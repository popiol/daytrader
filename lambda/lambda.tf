resource "aws_lambda_function" "main" {
	filename = "lambda/${var.function_name}.zip"
	function_name = "${var.inp.app.id}_${var.function_name}"
	role = var.role
	handler = "main.lambda_handler"
	source_code_hash = filebase64sha256("lambda/${var.function_name}.zip")
	runtime = "python3.8"
	timeout = 900
	tags = var.inp.app
}

resource "aws_cloudwatch_event_rule" "main" {
	name = aws_lambda_function.main.function_name
	schedule_expression = var.crontab_entry
	tags = var.inp.app
}

resource "aws_cloudwatch_event_target" "get_quotes" {
	target_id = aws_cloudwatch_event_rule.main.name
	rule = aws_cloudwatch_event_rule.main.name
	arn = aws_lambda_function.main.arn
	input = jsonencode(var.inp)
}

resource "aws_lambda_function_event_invoke_config" "main" {
	foreach = toset(var.on_failure)
	function_name = aws_lambda_function.main.function_name

	destination_config {
		on_failure {
			destination = each.key
		}
	}
}
