provider "aws" {
  profile = "terraform"
  region  = "ap-southeast-2"
}


module "vpc" {
  source             = "../../modules/vpc"
  name               = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
}

module "kms" {
  source      = "../../modules/kms"
  name        = var.project_name
  environment = var.environment
}

module "s3_docs" {
  source      = "../../modules/s3_docs"
  name        = var.project_name
  environment = var.environment
  kms_key_arn = module.kms.kms_key_arn
}

module "ecr" {
  source      = "../../modules/ecr"
  name        = var.project_name
  environment = var.environment
  repos       = ["doc-ingestion-api", "doc-ingestion-worker"]
}

module "cloudwatch_logs" {
  source            = "../../modules/cloudwatch_logs"
  name              = var.project_name
  environment       = var.environment
  retention_in_days = var.log_retention_days
  log_groups = [
    "/ecs/doc-ingestion-api",
    "/ecs/doc-ingestion-worker"
  ]
}

module "ecs_cluster" {
  source      = "../../modules/ecs_cluster"
  name        = var.project_name
  environment = var.environment
}

module "security_groups" {
  source      = "../../modules/security_groups"
  name        = var.project_name
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
}

module "iam" {
  source      = "../../modules/iam"
  name        = var.project_name
  environment = var.environment

  docs_bucket_arn = module.s3_docs.bucket_arn
  kms_key_arn     = module.kms.kms_key_arn
}

module "step_functions" {
  source = "../../step_functions"

  project_name     = var.project_name
  environment      = var.environment
  ddb_table_name = var.ddb_table_name
  docs_bucket_name = module.s3_docs.bucket_name
}
