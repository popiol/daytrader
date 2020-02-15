resource "aws_lambda_function" "l_get_quotes" {
	filename = "lambda/get_quotes.zip"
	function_name = "${var.app_id}_get_quotes"
	role = aws_iam_role.lambdarole.arn
	handler = "main.lambda_handler"
	source_code_hash = filebase64sha256("lambda/get_quotes.zip")
	runtime = "python3.8"
	timeout = 300

	vpc_config {
		subnet_ids = [
			aws_subnet.subnet1.id,
			aws_subnet.subnet2.id
		]
		security_group_ids = [aws_security_group.security1.id]
	}

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_lambda_function.l_get_quotes"
	}
}

