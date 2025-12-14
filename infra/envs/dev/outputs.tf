output "vpc_id" { value = module.vpc.vpc_id }

output "docs_bucket_name" { value = module.s3_docs.bucket_name }

output "ecs_cluster_name" { value = module.ecs_cluster.cluster_name }

output "api_task_role_arn"    { value = module.iam.api_task_role_arn }
output "worker_task_role_arn" { value = module.iam.worker_task_role_arn }
output "ecs_execution_role_arn" { value = module.iam.ecs_task_execution_role_arn }

output "alb_sg_id" { value = module.security_groups.alb_sg_id }
output "ecs_sg_id" { value = module.security_groups.ecs_tasks_sg_id }
