#!/usr/bin/env bash
set -e

# =========================
# USAGE CHECK
# =========================
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-pdf>"
  echo "Example:"
  echo "  $0 /path/to/document.pdf"
  exit 1
fi

FILE_PATH="$1"

if [ ! -f "$FILE_PATH" ]; then
  echo "❌ File not found: $FILE_PATH"
  exit 1
fi

# =========================
# CONFIGURATION
# =========================
API_BASE_URL="http://localhost:8080"
DDB_ENDPOINT="http://localhost:8000"
AWS_REGION="ap-southeast-2"
TENANT_HEADER="tenant-finance"
TENANT_ID="tenant-finance"
DOMAIN_ID="accounts"
CONTENT_TYPE="application/pdf"

REQUEST_ID_INIT="req-$(uuidgen)"
REQUEST_ID_COMPLETE="req-$(uuidgen)"

# =========================
# FILE METADATA
# =========================
FILENAME=$(basename "$FILE_PATH")
FILE_SIZE=$(stat -f%z "$FILE_PATH")

echo "📄 Document:"
echo "  Path : $FILE_PATH"
echo "  Name : $FILENAME"
echo "  Size : $FILE_SIZE bytes"
echo ""

# =========================
# STEP 1: INITIATE UPLOAD
# =========================
echo "➡️  Initiating upload..."

INIT_RESPONSE=$(curl -s -X POST "$API_BASE_URL/v1/uploads/init" \
  -H "Content-Type: application/json" \
  -H "x-request-id: $REQUEST_ID_INIT" \
  -H "x-tenant-id: $TENANT_HEADER" \
  -d "{
    \"tenant_id\": \"$TENANT_ID\",
    \"domain_id\": \"$DOMAIN_ID\",
    \"filename\": \"$FILENAME\",
    \"content_type\": \"$CONTENT_TYPE\",
    \"size_bytes\": $FILE_SIZE
  }")

echo "$INIT_RESPONSE" | jq .

UPLOAD_ID=$(echo "$INIT_RESPONSE" | jq -r '.upload_id')
PRESIGNED_URL=$(echo "$INIT_RESPONSE" | jq -r '.presigned_url')

if [ "$UPLOAD_ID" = "null" ] || [ "$PRESIGNED_URL" = "null" ]; then
  echo "❌ Failed to initiate upload"
  exit 1
fi

echo ""
echo "Upload ID: $UPLOAD_ID"
echo ""

# =========================
# STEP 2: UPLOAD TO S3 / MINIO
# =========================
echo "⬆️  Uploading document to object storage..."

curl -s -X PUT "$PRESIGNED_URL" \_
