resource "aws_lambda_function" "l_get_quotes" {
  filename      = "lambda/get_quotes.zip"
  function_name = "${var.app_id}_get_quotes"
  role          = aws_iam_role.lambdarole.arn
  handler       = "main.lambda_handler"

  source_code_hash = filebase64sha256("lambda/get_quotes.zip")

  runtime = "python3.8"

  vpc_config {
    subnet_ids         = [aws_subnet.subnet1.id]
    security_group_ids = [aws_vpc.vpc1.default_security_group_id]
  }
}

