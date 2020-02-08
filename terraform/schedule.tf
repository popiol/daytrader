resource "aws_cloudwatch_event_rule" "get_quotes" {
	name = "${var.app_id}_get_quotes"
	schedule_expression = "cron(31 14-23 * * 1-5 *)"
}

resource "aws_cloudwatch_event_target" "get_quotes" {
	rule = aws_cloudwatch_event_rule.get_quotes.name
	arn = aws_lambda_function.l_get_quotes.arn
}

