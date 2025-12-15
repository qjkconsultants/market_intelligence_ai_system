import json
import boto3
import os
import uuid

s3 = boto3.client("s3")

OUT_BUCKET = os.environ["OUT_BUCKET"]

def handler(event, context):
    tenant_id = event["tenant_id"]
    upload_id = event["upload_id"]

    output_key = (
        f"tenant={tenant_id}/"
        f"upload_id={upload_id}/"
        f"extraction.json"
    )

    fake_textract = {
        "job_status": "SUCCEEDED",
        "pages": [
            {
                "page": 1,
                "text": "This is mocked extracted text for testing."
            }
        ]
    }

    s3.put_object(
        Bucket=OUT_BUCKET,
        Key=output_key,
        Body=json.dumps(fake_textract),
        ContentType="application/json"
    )

    return {
        "tenant_id": tenant_id,
        "upload_id": upload_id,
        "extraction_output_key": output_key
    }
