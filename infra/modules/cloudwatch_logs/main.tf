resource "aws_cloudwatch_log_group" "this" {
  for_each          = toset(var.log_groups)
  name              = each.value
  retention_in_days = var.retention_in_days

  tags = {
    Environment = var.environment
    Project     = var.name
  }
}
