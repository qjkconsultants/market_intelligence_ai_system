from __future__ import annotations

import json
import uuid
import structlog
from fastapi import FastAPI, HTTPException, Request
from starlette.responses import JSONResponse

from .settings import settings
from .observability import configure_structured_logging, configure_opentelemetry, instrument_fastapi
from .middleware import ObservabilityMiddleware
from .auth_middleware import AuthMiddleware
from .auth import authorize_domain_access
from .models import UploadInitRequest, UploadInitResponse, UploadCompleteRequest, DownloadResponse
from .s3_storage import S3Storage
from .ddb import DdbRepository
from . import metrics
from .aws_clients import stepfunctions_client
from opentelemetry import trace

log = structlog.get_logger()

def create_app() -> FastAPI:
    # ---- Logging + tracing ----
    configure_structured_logging(settings.service_name, settings.log_level)
    configure_opentelemetry(settings.service_name)

    app = FastAPI(title="Document Ingestion API", version="0.2.0")

    # OTel instrumentation first so trace context exists
    instrument_fastapi(app)

    # Auth middleware (PROD: validate JWT; DEV: injects local identity)
    app.add_middleware(AuthMiddleware)

    # Our middleware enriches logs/metrics with request_id/trace_id
    app.add_middleware(ObservabilityMiddleware)

    storage = S3Storage()
    repo = DdbRepository()
    sfn = stepfunctions_client()

    @app.on_event("startup")
    async def startup():
        # Dev convenience. In production you normally create buckets via Terraform.
        storage.ensure_bucket()
        log.info("startup_complete", service=settings.service_name, env=settings.app_env)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.service_name, "env": settings.app_env}

    @app.post("/v1/uploads/init", response_model=UploadInitResponse)
    async def upload_init(req: UploadInitRequest, request: Request):
        # ---- Identity & authorization ----
        auth = getattr(request.state, "auth", None)
        if not auth:
            raise HTTPException(status_code=401, detail="unauthorized")

        # Production safety: do not trust tenant_id from the body.
        # We keep it in the request schema for now, but we enforce it matches the token.
        if req.tenant_id != auth.tenant_id:
            raise HTTPException(status_code=403, detail="tenant mismatch")

        try:
            authorize_domain_access(req.domain_id, roles=auth.roles, groups=auth.groups)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

        # ---- Validation ----
        if req.size_bytes > settings.max_upload_size_bytes:
            raise HTTPException(status_code=413, detail=f"File too large. Max {settings.max_upload_size_bytes} bytes.")

        upload_id = str(uuid.uuid4())
        object_key = storage.build_object_key(auth.tenant_id, req.domain_id, upload_id, req.filename)

        presigned_url = storage.create_presigned_put_url(
            object_key=object_key,
            expires_seconds=settings.presign_expires_seconds,
        )

        # Trace id (from current span)
        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span else None
        trace_id = format(span_ctx.trace_id, "032x") if span_ctx and span_ctx.trace_id else None

        request_id = request.headers.get("x-request-id", "unknown")

        # ---- Metadata record ----
        repo.put_upload_record(
            tenant_id=auth.tenant_id,
            upload_id=upload_id,
            domain_id=req.domain_id,
            object_key=object_key,
            content_type=req.content_type,
            size_bytes=req.size_bytes,
            request_id=request_id,
            trace_id=trace_id or "",
            created_by_user_id=auth.user_id,
            created_by_roles=auth.roles,
            created_by_groups=auth.groups,
            classification="internal",
            access_policy={"mode": "domain-rbac", "domain_id": req.domain_id},
        )

        metrics.uploads_initiated_total.add(1, {"tenant_id": auth.tenant_id, "domain_id": req.domain_id})

        log.info(
            "upload_initiated",
            tenant_id=auth.tenant_id,
            domain_id=req.domain_id,
            upload_id=upload_id,
            object_key=object_key,
            content_type=req.content_type,
            size_bytes=req.size_bytes,
            request_id=request_id,
            trace_id=trace_id,
            user_id=auth.user_id,
        )

        return UploadInitResponse(
            upload_id=upload_id,
            object_key=object_key,
            bucket=settings.s3_bucket_name,
            presigned_url=presigned_url,
            expires_in_seconds=settings.presign_expires_seconds,
        )

    @app.post("/v1/uploads/complete")
    async def upload_complete(req: UploadCompleteRequest, request: Request):
        auth = getattr(request.state, "auth", None)
        if not auth:
            raise HTTPException(status_code=401, detail="unauthorized")
        if req.tenant_id != auth.tenant_id:
            raise HTTPException(status_code=403, detail="tenant mismatch")

        # Trace ids for correlation (API -> workflow -> workers)
        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span else None
        trace_id = format(span_ctx.trace_id, "032x") if span_ctx and span_ctx.trace_id else None
        request_id = request.headers.get("x-request-id", "unknown")

        # Mark as queued in metadata (source of truth)
        repo.update_status(
            tenant_id=auth.tenant_id,
            upload_id=req.upload_id,
            status="QUEUED",
            request_id=request_id,
            trace_id=trace_id or "",
        )

        # Start Step Functions orchestration (production path).
        execution_arn = None
        if settings.enable_step_functions and settings.step_function_arn:
            # Input should be minimal and include only pointers (never the document bytes).
            inp = {
                "tenant_id": auth.tenant_id,
                "upload_id": req.upload_id,
                "request_id": request_id,
                "trace_id": trace_id,
                "started_by_user_id": auth.user_id,
            }
            resp = sfn.start_execution(
                stateMachineArn=settings.step_function_arn,
                name=req.upload_id,
                input=json.dumps(inp),
            )
            execution_arn = resp.get("executionArn")
            if execution_arn:
                repo.attach_workflow(auth.tenant_id, req.upload_id, execution_arn)

        metrics.uploads_completed_total.add(1, {"tenant_id": auth.tenant_id})

        log.info(
            "upload_completed",
            tenant_id=auth.tenant_id,
            upload_id=req.upload_id,
            request_id=request_id,
            trace_id=trace_id,
            user_id=auth.user_id,
            stepfn_execution_arn=execution_arn,
        )

        return {"status": "queued", "upload_id": req.upload_id, "workflow_execution_arn": execution_arn}

    @app.get("/v1/uploads/{upload_id}/download", response_model=DownloadResponse)
    async def download(upload_id: str, request: Request):
        """Generate a short-lived presigned GET URL after authorization checks.

        This is the production-safe way to let users download documents:
          - The API checks tenant + RBAC rules using metadata.
          - The API returns a short-lived URL to object storage.
        """
        auth = getattr(request.state, "auth", None)
        if not auth:
            raise HTTPException(status_code=401, detail="unauthorized")

        item = repo.get_upload(auth.tenant_id, upload_id)
        if not item:
            raise HTTPException(status_code=404, detail="not found")

        domain_id = item.get("domain_id", "")
        try:
            authorize_domain_access(domain_id, roles=auth.roles, groups=auth.groups)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

        object_key = item["object_key"]
        presigned = storage.create_presigned_get_url(object_key=object_key, expires_seconds=settings.presign_expires_seconds)

        return DownloadResponse(
            upload_id=upload_id,
            bucket=settings.s3_bucket_name,
            object_key=object_key,
            presigned_url=presigned,
            expires_in_seconds=settings.presign_expires_seconds,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
        return JSONResponse(status_code=500, content={"error": "internal_server_error"})

    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8080)
