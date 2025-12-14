# Document Ingestion Scaffold (FastAPI + DynamoDB + Commercial Observability)

This scaffold gives you a **production-shaped** local environment that mirrors the AWS design:
- FastAPI API service (stateless, structured logs, metrics, traces)
- DynamoDB (local) for metadata (tenant/domain/upload lifecycle)
- MinIO (local) as S3-compatible object store (so your API can issue presigned URLs now)
- OpenTelemetry Collector to receive traces/metrics from the app (prints them to logs)

> Goal: you can develop and test the ingestion pattern **without any AWS costs**, then later deploy the same API container to ECS.

---

## 1) Start the stack

From this folder:

```bash
docker compose up --build
```

Wait until containers are healthy.

---

## 2) Create the DynamoDB table (local)

In a second terminal:

```bash
export DDB_TABLE_NAME=DocumentIngestion
export AWS_REGION=ap-southeast-2
export DDB_ENDPOINT_URL=http://localhost:8000
python scripts/create_ddb_table_local.py
```

---

## 3) Smoke test FastAPI

Health check:

```bash
curl -s http://localhost:8080/health | jq .
```

---

## 4) Test upload init (presigned URL flow)

Call `uploads/init`:

```bash
curl -s -X POST http://localhost:8080/v1/uploads/init \
  -H "Content-Type: application/json" \
  -H "x-request-id: req-demo-001" \
  -d '{
    "tenant_id":"tenantA",
    "domain_id":"contracts",
    "filename":"sample.pdf",
    "content_type":"application/pdf",
    "size_bytes":12345
  }' | jq .
```

Copy the `presigned_url` and upload a file with it:

```bash
URL="<paste presigned_url here>"
curl -X PUT "$URL" -H "Content-Type: application/pdf" --data-binary @/path/to/sample.pdf
```

Then mark complete:

```bash
curl -s -X POST http://localhost:8080/v1/uploads/complete \
  -H "Content-Type: application/json" \
  -H "x-request-id: req-demo-002" \
  -d '{
    "tenant_id":"tenantA",
    "upload_id":"<paste upload_id here>"
  }' | jq .
```

---

## 5) Observability (what to look at)

### Structured logs
The API container prints **JSON logs**. Each upload has:
- tenant_id
- domain_id
- upload_id
- request_id
- trace_id

View:
```bash
docker logs -f doc-ingestion-api
```

### Traces & metrics
The app sends OTLP traces/metrics to the collector, and the collector prints them.

View:
```bash
docker logs -f otel-collector
```

Prometheus scrape endpoint (collector metrics):
- http://localhost:8888/metrics

---

## 6) Why this architecture supports 1000 docs/min

- API is stateless and lightweight
- Clients upload **directly to object storage** via presigned URLs
- DynamoDB is the metadata write path (scales horizontally)
- Processing is async (queue + workers later)

This prevents your API from becoming the throughput bottleneck.

---

## 7) Next steps (Phase 2)
1) Add an SQS-compatible queue for local dev (or Redis) + a worker service
2) Add idempotency keys and conditional writes in DynamoDB
3) Add auth (JWT) and tenant/domain authorization
4) When ready, deploy to AWS:
   - Terraform apply
   - Push image to ECR
   - ECS service + ALB
   - CloudWatch Logs + X-Ray/OTel



## Production hardening additions (v0.2.0)
- JWT Auth middleware (toggle with AUTH_ENABLED)
- RBAC domain checks (RBAC_POLICY_JSON)
- Presigned GET download endpoint with authz
- Optional Step Functions trigger on /v1/uploads/complete (ENABLE_STEP_FUNCTIONS + STEP_FUNCTION_ARN)
- Updated OTel collector config to use debug exporter (logging exporter deprecated)
