import json
import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")
OUT_BUCKET = os.environ.get("OUT_BUCKET")  # could be same bucket as docs

def handler(event, context):
    tenant_id = event["tenant_id"]
    upload_id = event["upload_id"]
    ddb_item = event["ddb_item"]

    # Extract the key from DynamoDB (DynamoDB JSON format)
    object_key = ddb_item["object_key"]["S"]
    domain_id = ddb_item.get("domain_id", {}).get("S", "")
    content_type = ddb_item.get("content_type", {}).get("S", "")

    # Where we store extracted output
    extraction_output_key = (
        f"tenant={tenant_id}/upload_id={upload_id}/extracted/textract.json"
    )

    # Mock payload shaped like “document extraction”
    payload = {
        "mock": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "tenant_id": tenant_id,
            "upload_id": upload_id,
            "domain_id": domain_id,
            "bucket": OUT_BUCKET,
            "object_key": object_key,
            "content_type": content_type,
        },
        "textract_style": {
            "Blocks": [
                {"BlockType": "PAGE", "Id": "p1"},
                {"BlockType": "LINE", "Text": "Hello from mock extractor", "Page": 1},
                {"BlockType": "LINE", "Text": f"ObjectKey={object_key}", "Page": 1},
            ]
        }
    }

    s3.put_object(
        Bucket=OUT_BUCKET,
        Key=extraction_output_key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )

    return {"extraction_output_key": extraction_output_key}
