locals {
    scraper_function_s3_bucket      = "stack-half-full-bucket"
    scraper_function_s3_arn         = "arn:aws:s3:::${local.scraper_function_s3_bucket}"
    scraper_function_file_name      = "imdb_scraper"
    scraper_function_handler        = "${local.scraper_function_file_name}.handler"
    scraper_function_layer_name     = "imdb_scraper_libraries_layer"
    scraper_function_role_name      = "${local.scraper_function_file_name}-role"
    scraper_function_policy_name    = "${local.scraper_function_file_name}-policy"
    common_tags = {
        "project"     = "stack-half-full"
        "environment" = "test"
    }
}

resource "aws_lambda_function" "scraper_lambda_function" {
    s3_bucket       = local.scraper_function_s3_bucket
    s3_key          = local.scraper_function_file_name
    handler         = local.scraper_function_handler
    runtime         = "python3.7"
    timeout         = 15
    layers          = [aws_lambda_layer_version.scraper_lambda_function_layer.arn]
    role            = aws_iam_role.scraper_lambda_function_role.arn
    tags            = merge(local.common_tags, tomap({"Name" = local.scraper_function_file_name}))
}

resource "aws_lambda_layer_version" "scraper_lambda_function_layer" {
    s3_bucket           = local.scraper_function_s3_bucket
    s3_key              = local.scraper_function_file_name
    layer_name          = local.scraper_function_layer_name
    compatible_runtimes = ["python3.7"]
    description         = "Libraries used by the scraper function"
}


# IAM
resource "aws_iam_role" "scraper_lambda_function_role" {
    name        = local.scraper_function_role_name
    tags        = merge(local.common_tags, tomap({"Name" = local.scraper_function_file_name}))

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
        {
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
            Service = "lambda.amazonaws.com"
            }
        },
        ]
    })
}
data "aws_iam_policy_document" "scraper_lambda_function_policy_document" {
    policy_id = local.scraper_function_policy_name
    
    statement {
        actions = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogStreams",
            "cloudwatch:GetMetricData",
            "cloudwatch:ListMetrics",
            "cloudwatch:PutMetricData",
            "ec2:CreateNetworkInterface",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DeleteNetworkInterface",
            "ec2:AssignPrivateIpAddresses",
            "ec2:UnassignPrivateIpAddresses"
        ]
        resources = ["*"]
    }

    statement {
        actions = [
            "s3:GetObject",
            "s3:GetObjectVersion",
            "s3:ListBucket",
            "s3:PutObject"
        ]
        resources = [local.scraper_function_s3_arn.arn]
    }
}
resource "aws_iam_policy" "scraper_lambda_function_policy" {
    name         = local.scraper_function_policy_name
    policy       = data.aws_iam_policy_document.scraper_lambda_function_policy_document.json
}
resource "aws_iam_role_policy_attachment" "scraper_role_policy_attachment" {
    role         = aws_iam_role.scraper_lambda_function_role.name
    policy_arn   = aws_iam_policy.scraper_lambda_function_policy.arn
}
