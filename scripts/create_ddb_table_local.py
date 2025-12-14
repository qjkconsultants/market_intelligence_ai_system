import os
import boto3

TABLE = os.getenv("DDB_TABLE_NAME", "DocumentIngestion")
REGION = os.getenv("AWS_REGION", "ap-southeast-2")
ENDPOINT = os.getenv("DDB_ENDPOINT_URL", "http://localhost:8000")

ddb = boto3.client(
    "dynamodb",
    region_name=REGION,
    endpoint_url=ENDPOINT,
    aws_access_key_id="local",
    aws_secret_access_key="local",
)

existing = ddb.list_tables()["TableNames"]
if TABLE in existing:
    print(f"Table already exists: {TABLE}")
    raise SystemExit(0)

ddb.create_table(
    TableName=TABLE,
    BillingMode="PAY_PER_REQUEST",
    KeySchema=[
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"},
    ],
    AttributeDefinitions=[
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
    ],
)
print("Creating table...")
ddb.get_waiter("table_exists").wait(TableName=TABLE)
print(f"Created table {TABLE}")
