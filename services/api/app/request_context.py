from __future__ import annotations
import contextvars
from dataclasses import dataclass
from typing import Optional

_request_id = contextvars.ContextVar("request_id", default=None)
_trace_id = contextvars.ContextVar("trace_id", default=None)
_tenant_id = contextvars.ContextVar("tenant_id", default=None)
_upload_id = contextvars.ContextVar("upload_id", default=None)

def set_request_id(v: str | None) -> None: _request_id.set(v)
def get_request_id() -> str | None: return _request_id.get()

def set_trace_id(v: str | None) -> None: _trace_id.set(v)
def get_trace_id() -> str | None: return _trace_id.get()

def set_tenant_id(v: str | None) -> None: _tenant_id.set(v)
def get_tenant_id() -> str | None: return _tenant_id.get()

def set_upload_id(v: str | None) -> None: _upload_id.set(v)
def get_upload_id() -> str | None: return _upload_id.get()
