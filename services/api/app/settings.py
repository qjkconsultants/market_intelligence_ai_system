from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    service_name: str = Field(default="doc-ingestion-api", alias="SERVICE_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Auth / RBAC ---
    auth_enabled: bool = Field(default=False, alias="AUTH_ENABLED")
    jwt_issuer: str = Field(default="", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="", alias="JWT_AUDIENCE")
    jwks_url: str = Field(default="", alias="JWKS_URL")
    tenant_claim: str = Field(default="tenant_id", alias="TENANT_CLAIM")
    groups_claim: str = Field(default="cognito:groups", alias="GROUPS_CLAIM")
    roles_claim: str = Field(default="roles", alias="ROLES_CLAIM")
    # JSON string mapping role/group -> list of domains allowed. Use "*" for all.
    rbac_policy_json: str = Field(
        default='{"ADMIN":["*"]}',
        alias="RBAC_POLICY_JSON",
        description="JSON mapping of roles/groups to allowed domain_ids."
    )

    # --- Step Functions ---
    enable_step_functions: bool = Field(default=False, alias="ENABLE_STEP_FUNCTIONS")
    step_function_arn: str = Field(default="", alias="STEP_FUNCTION_ARN")

    # DynamoDB
    ddb_table_name: str = Field(default="DocumentIngestion", alias="DDB_TABLE_NAME")
    aws_region: str = Field(default="ap-southeast-2", alias="AWS_REGION")
    ddb_endpoint_url: str | None = Field(default=None, alias="DDB_ENDPOINT_URL")

    # S3-compatible storage
    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_bucket_name: str = Field(default="docs", alias="S3_BUCKET_NAME")
    s3_access_key: str = Field(default="minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin", alias="S3_SECRET_KEY")
    s3_region: str = Field(default="ap-southeast-2", alias="S3_REGION")
    s3_use_ssl: bool = Field(default=False, alias="S3_USE_SSL")
    s3_public_endpoint: str | None = Field(default=None, alias="S3_PUBLIC_ENDPOINT")

    presign_expires_seconds: int = Field(default=900, alias="PRESIGN_EXPIRES_SECONDS")
    max_upload_size_bytes: int = Field(default=50 * 1024 * 1024, alias="MAX_UPLOAD_SIZE_BYTES")

settings = Settings()
