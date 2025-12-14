from __future__ import annotations
from pydantic import BaseModel, Field, constr

class UploadInitRequest(BaseModel):
    tenant_id: constr(min_length=1) = Field(..., description="Tenant identifier")
    domain_id: constr(min_length=1) = Field(..., description="Domain / document category identifier")
    filename: constr(min_length=1) = Field(..., description="Original file name")
    content_type: constr(min_length=1) = Field(..., description="MIME type, e.g. application/pdf")
    size_bytes: int = Field(..., ge=1, description="File size in bytes (client declared)")

class UploadInitResponse(BaseModel):
    upload_id: str
    object_key: str
    bucket: str
    presigned_url: str
    expires_in_seconds: int

class UploadCompleteRequest(BaseModel):
    tenant_id: constr(min_length=1)
    upload_id: constr(min_length=1)


class DownloadResponse(BaseModel):
    upload_id: str
    bucket: str
    object_key: str
    presigned_url: str
    expires_in_seconds: int
