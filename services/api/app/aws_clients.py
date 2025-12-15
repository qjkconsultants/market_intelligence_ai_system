from __future__ import annotations
import boto3
from botocore.config import Config
from .settings import settings

def dynamodb_resource():
    return boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        endpoint_url=settings.ddb_endpoint_url,  # 🔑 REQUIRED
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )

def s3_client():
    # For MinIO we pass explicit credentials & endpoint_url.
    session = boto3.session.Session(
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region
    )
    return session.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4", retries={"max_attempts": 10, "mode": "standard"})
    )


def stepfunctions_client():
    session = boto3.session.Session(region_name=settings.aws_region)
    return session.client(
        "stepfunctions",
        config=Config(retries={"max_attempts": 10, "mode": "standard"})
    )
