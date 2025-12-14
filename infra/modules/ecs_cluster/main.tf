resource "aws_ecs_cluster" "this" {
  name = "${var.name}-${var.environment}-cluster"
}
