resource "aws_kms_key" "this" {
  description             = "KMS key for ${var.name}-${var.environment}"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "${var.name}-${var.environment}-kms"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.name}-${var.environment}-kms"
  target_key_id = aws_kms_key.this.key_id
}
