output "log_group_names" {
  value = keys(aws_cloudwatch_log_group.this)
}
