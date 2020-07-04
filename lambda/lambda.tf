resource "aws_lambda_function" "main" {
	filename = "lambda/${var.function_name}.zip"
	function_name = "${var.inp.app.id}_${var.function_name}"
	role = var.role
	handler = "${var.function_name}.lambda_handler"
	source_code_hash = filebase64sha256("lambda/${var.function_name}.zip")
	runtime = "python3.8"
	timeout = 900
	tags = var.inp.app
}

resource "aws_cloudwatch_event_rule" "main" {
	for_each = toset(var.crontab_entry ? [var.crontab_entry] : [])
	name = aws_lambda_function.main.function_name
	schedule_expression = each.key
	tags = var.inp.app
}

resource "aws_cloudwatch_event_target" "get_quotes" {
	for_each = toset(var.crontab_entry ? [var.crontab_entry] : [])
	target_id = aws_cloudwatch_event_rule.main[each.key].name
	rule = aws_cloudwatch_event_rule.main[each.key].name
	arn = aws_lambda_function.main.arn
	input = jsonencode(var.inp)
}

resource "aws_lambda_function_event_invoke_config" "main" {
	for_each = toset(var.on_failure)
	function_name = aws_lambda_function.main.function_name

	destination_config {
		on_failure {
			destination = each.key
		}
	}
}
