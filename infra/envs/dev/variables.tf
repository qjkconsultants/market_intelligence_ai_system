variable "aws_region" { type = string }

variable "project_name" { type = string }
variable "environment"  { type = string }

variable "vpc_cidr" { type = string }

variable "availability_zones" { type = list(string) }
variable "public_subnets"     { type = list(string) }
variable "private_subnets"    { type = list(string) }

variable "log_retention_days" { type = number }
variable "ddb_table_name" {
  type        = string
  description = "DynamoDB table name for document ingestion metadata"
}
