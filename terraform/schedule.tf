resource "aws_cloudwatch_event_rule" "get_quotes" {
	name = "${var.app_id}_get_quotes"
	schedule_expression = "cron(31 14-23 ? * 2-6 *)"

  tags = {
    App = var.app
    AppVer = var.app_ver
    AppStage = var.app_stage
    TerraformID = "aws_cloudwatch_event_rule.get_quotes"
  }
}

resource "aws_cloudwatch_event_target" "get_quotes" {
	target_id = "${var.app_id}_get_quotes"
	rule = aws_cloudwatch_event_rule.get_quotes.name
	arn = aws_lambda_function.l_get_quotes.arn
}

