resource "aws_lambda_function" "l_hello_world" {
  filename      = "lambda/hello_world.zip"
  function_name = "${var.app_id}_hello_world"
  role          = aws_iam_role.lambdarole.arn
  handler       = "main.lambda_handler"

  source_code_hash = filebase64sha256("lambda/hello_world.zip")

  runtime = "python3.8"

  vpc_config {
    subnet_ids         = [aws_subnet.subnet1.id]
    security_group_ids = [aws_vpc.vpc1.default_security_group_id]
  }

  tags = {
    App = var.app
    AppVer = var.app_ver
    AppStage = var.app_stage
    TerraformID = "aws_lambda_function.l_hello_world"
  }
}

