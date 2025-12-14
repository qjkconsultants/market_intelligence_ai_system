# For ALB later (public inbound 443)
resource "aws_security_group" "alb" {
  name        = "${var.name}-${var.environment}-alb-sg"
  description = "ALB security group"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# For ECS tasks (private, no inbound yet)
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.name}-${var.environment}-ecs-sg"
  description = "ECS tasks security group"
  vpc_id      = var.vpc_id

  # No ingress by default (we'll allow ALB->ECS later)
  egress {
    description = "HTTPS outbound"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
