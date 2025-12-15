aws_region  = "ap-southeast-2"
project_name = "doc-ingestion"
environment  = "dev"
ddb_table_name = "DocumentIngestion"
vpc_cidr = "10.0.0.0/16"

availability_zones = ["ap-southeast-2a", "ap-southeast-2b"]
public_subnets     = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnets    = ["10.0.11.0/24", "10.0.12.0/24"]

log_retention_days = 7
