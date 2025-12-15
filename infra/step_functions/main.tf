locals {
  name = "${var.project_name}-${var.environment}"
}

# ---------------------------
# Lambda IAM role
# ---------------------------
resource "aws_iam_role" "mock_lambda" {
  name = "${local.name}-mock-extract-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.mock_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_s3" {
  name = "${local.name}-lambda-s3-write"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:PutObject"]
      Resource = "arn:aws:s3:::${var.docs_bucket_name}/*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.mock_lambda.name
  policy_arn = aws_iam_policy.lambda_s3.arn
}

# ---------------------------
# Lambda function
# ---------------------------
data "archive_file" "mock_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_mock_extract.py"
  output_path = "${path.module}/mock_extract.zip"
}

resource "aws_lambda_function" "mock_extract" {
  function_name = "${local.name}-mock-extract"
  role          = aws_iam_role.mock_lambda.arn
  handler       = "lambda_mock_extract.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.mock_zip.output_path
  source_code_hash = data.archive_file.mock_zip.output_base64sha256

  environment {
    variables = {
      OUT_BUCKET = var.docs_bucket_name
    }
  }
}

# ---------------------------
# Step Function IAM role
# ---------------------------
resource "aws_iam_role" "stepfn" {
  name = "${local.name}-stepfn"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = { Service = "states.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "stepfn_policy" {
  name = "${local.name}-stepfn-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.mock_extract.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "stepfn_attach" {
  role       = aws_iam_role.stepfn.name
  policy_arn = aws_iam_policy.stepfn_policy.arn
}

# ---------------------------
# Step Function
# ---------------------------
locals {
  definition = templatefile("${path.module}/stepfn.asl.json", {
    DDB_TABLE_NAME          = var.ddb_table_name
    MOCK_EXTRACT_LAMBDA_ARN = aws_lambda_function.mock_extract.arn
  })
}

resource "aws_sfn_state_machine" "ingestion" {
  name       = "${local.name}-ingestion-v1"
  role_arn  = aws_iam_role.stepfn.arn
  definition = local.definition
}
