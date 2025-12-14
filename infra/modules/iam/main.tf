data "aws_iam_policy_document" "ecs_task_execution_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.name}-${var.environment}-ecs-task-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_exec_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn  = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# API task role (app permissions) - minimal for Phase 1
resource "aws_iam_role" "api_task" {
  name               = "${var.name}-${var.environment}-api-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume.json
}

data "aws_iam_policy_document" "api_task_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:ListBucketMultipartUploads",
      "s3:ListBucket"
    ]
    resources = [
      var.docs_bucket_arn,
      "${var.docs_bucket_arn}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = ["kms:Encrypt", "kms:GenerateDataKey"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_policy" "api_task" {
  name   = "${var.name}-${var.environment}-api-task-policy"
  policy = data.aws_iam_policy_document.api_task_policy.json
}

resource "aws_iam_role_policy_attachment" "api_task_attach" {
  role      = aws_iam_role.api_task.name
  policy_arn = aws_iam_policy.api_task.arn
}

# Worker task role (minimal for Phase 1)
resource "aws_iam_role" "worker_task" {
  name               = "${var.name}-${var.environment}-worker-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume.json
}

data "aws_iam_policy_document" "worker_task_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      var.docs_bucket_arn,
      "${var.docs_bucket_arn}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_policy" "worker_task" {
  name   = "${var.name}-${var.environment}-worker-task-policy"
  policy = data.aws_iam_policy_document.worker_task_policy.json
}

resource "aws_iam_role_policy_attachment" "worker_task_attach" {
  role      = aws_iam_role.worker_task.name
  policy_arn = aws_iam_policy.worker_task.arn
}
