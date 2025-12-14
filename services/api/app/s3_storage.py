from __future__ import annotations

import boto3
from botocore.config import Config

from .settings import settings


class S3Storage:
    """
    S3 abstraction supporting:
    - Internal endpoint (Docker / AWS)
    - Public endpoint (browser / curl via presigned URLs)
    """

    def __init__(self):
        self._internal_client = self._create_client(
            endpoint_url=settings.s3_endpoint_url
        )
        self._public_client = self._create_client(
            endpoint_url=settings.s3_public_endpoint or settings.s3_endpoint_url
        )

    def _create_client(self, endpoint_url: str | None):
        return boto3.client(
            "s3",
            region_name=settings.s3_region,
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            use_ssl=settings.s3_use_ssl,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 5, "mode": "standard"},
                s3={"addressing_style": "path"},  # REQUIRED for MinIO
            ),
        )

    # --------------------------------------------------
    # Bucket
    # --------------------------------------------------
    def ensure_bucket(self) -> None:
        try:
            self._internal_client.head_bucket(
                Bucket=settings.s3_bucket_name
            )
        except Exception:
            self._internal_client.create_bucket(
                Bucket=settings.s3_bucket_name
            )

    # --------------------------------------------------
    # Object key
    # --------------------------------------------------
    def build_object_key(
        self,
        tenant_id: str,
        domain_id: str,
        upload_id: str,
        filename: str,
    ) -> str:
        safe_filename = filename.replace("/", "_")
        return (
            f"tenant={tenant_id}/"
            f"domain={domain_id}/"
            f"upload_id={upload_id}/"
            f"{safe_filename}"
        )

    # --------------------------------------------------
    # Presigned URLs
    # --------------------------------------------------
    def create_presigned_put_url(
        self,
        object_key: str,
        expires_seconds: int,
    ) -> str:
        return self._public_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": object_key,
            },
            ExpiresIn=expires_seconds,
            HttpMethod="PUT",
        )


    def create_presigned_get_url(
        self,
        object_key: str,
        expires_seconds: int,
    ) -> str:
        return self._public_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": object_key,
            },
            ExpiresIn=expires_seconds,
            HttpMethod="GET",
        )
