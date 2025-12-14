from __future__ import annotations
import time
from typing import Any, Dict, Optional
from botocore.exceptions import ClientError
from .aws_clients import dynamodb_resource
from .settings import settings

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

class DdbRepository:
    def __init__(self):
        self._ddb = dynamodb_resource()
        self._table = self._ddb.Table(settings.ddb_table_name)

    def put_upload_record(
        self,
        tenant_id: str,
        upload_id: str,
        domain_id: str,
        object_key: str,
        content_type: str,
        size_bytes: int,
        request_id: str,
        trace_id: str,
        created_by_user_id: str,
        created_by_roles: list[str] | None = None,
        created_by_groups: list[str] | None = None,
        classification: str = "internal",
        access_policy: Optional[Dict[str, Any]] = None,
    ) -> None:
        pk = f"TENANT#{tenant_id}"
        sk = f"UPLOAD#{upload_id}"
        now = _now_iso()

        item: Dict[str, Any] = {
            "PK": pk,
            "SK": sk,
            "tenant_id": tenant_id,
            "domain_id": domain_id,
            "upload_id": upload_id,
            "object_key": object_key,
            "content_type": content_type,
            "size_bytes": int(size_bytes),
            "status": "INITIATED",
            "classification": classification,
            "access_policy": access_policy or {"mode": "domain-rbac"},
            "created_by": {
                "user_id": created_by_user_id,
                "roles": created_by_roles or [],
                "groups": created_by_groups or [],
            },
            "created_at": now,
            "updated_at": now,
            "request_id": request_id,
            "trace_id": trace_id,
            "workflow": None,
            "error_code": None,
            "error_message": None,
        }
        self._table.put_item(Item=item)

    def get_upload(self, tenant_id: str, upload_id: str) -> Optional[Dict[str, Any]]:
        pk = f"TENANT#{tenant_id}"
        sk = f"UPLOAD#{upload_id}"
        resp = self._table.get_item(Key={"PK": pk, "SK": sk})
        return resp.get("Item")

    def attach_workflow(self, tenant_id: str, upload_id: str, execution_arn: str) -> None:
        pk = f"TENANT#{tenant_id}"
        sk = f"UPLOAD#{upload_id}"
        now = _now_iso()
        self._table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET workflow = :w, updated_at = :u",
            ExpressionAttributeValues={
                ":w": {"engine": "step-functions", "execution_arn": execution_arn, "started_at": now},
                ":u": now,
            },
        )

    def update_status(
        self,
        tenant_id: str,
        upload_id: str,
        status: str,
        request_id: str,
        trace_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        pk = f"TENANT#{tenant_id}"
        sk = f"UPLOAD#{upload_id}"
        now = _now_iso()

        expr = "SET #st = :s, updated_at = :u, request_id = :r, trace_id = :t, error_code = :ec, error_message = :em"
        names = {"#st": "status"}
        values = {
            ":s": status,
            ":u": now,
            ":r": request_id,
            ":t": trace_id,
            ":ec": error_code,
            ":em": error_message,
        }
        self._table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=expr,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
        )
