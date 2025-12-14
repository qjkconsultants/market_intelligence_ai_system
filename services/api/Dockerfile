FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir \
      "uvicorn[standard]==0.30.6" \
      "fastapi==0.115.8" \
      "pydantic==2.10.6" \
      "pydantic-settings==2.7.1" \
      "boto3==1.36.16" \
      "botocore==1.36.16" \
      "structlog==24.4.0" \
      "opentelemetry-api==1.29.0" \
      "opentelemetry-sdk==1.29.0" \
      "opentelemetry-exporter-otlp==1.29.0" \
      "opentelemetry-instrumentation-fastapi==0.50b0" \
      "opentelemetry-instrumentation-requests==0.50b0" \
      "opentelemetry-instrumentation-urllib3==0.50b0" \
      "opentelemetry-instrumentation-logging==0.50b0" \
      "prometheus-client==0.21.0" \
      "python-json-logger==2.0.7" \
      "python-jose[cryptography]==3.3.0" \
      "httpx==0.27.2"

COPY app /app/app

EXPOSE 8080

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
