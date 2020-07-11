resource "aws_lambda_function" "main" {
	filename = "lambda/${var.function_name}.zip"
	function_name = "${var.inp.app.id}_${var.function_name}"
	role = var.role
	handler = "${var.function_name}.lambda_handler"
	source_code_hash = filebase64sha256("lambda/${var.function_name}.zip")
	runtime = "python3.8"
	timeout = 900
	tags = var.inp.app

	dynamic "environment" {
		for_each = toset(length(var.env_vars) > 0 ? ["0"] : [])

		content {
			variables = var.env_vars
		}
	}
}

resource "aws_cloudwatch_event_rule" "main" {
	for_each = toset(var.crontab_entry != "" ? [var.crontab_entry] : [])
	name = aws_lambda_function.main.function_name
	schedule_expression = each.key
	tags = var.inp.app
}

resource "aws_cloudwatch_event_target" "get_quotes" {
	for_each = toset(var.crontab_entry != "" ? [var.crontab_entry] : [])
	target_id = aws_cloudwatch_event_rule.main[each.key].name
	rule = aws_cloudwatch_event_rule.main[each.key].name
	arn = aws_lambda_function.main.arn
	input = jsonencode(merge(var.inp, var.inp2))
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

resource "aws_api_gateway_rest_api" "main" {
	for_each = toset(var.rest_api ? ["0"] : [])
	name = aws_lambda_function.main.function_name
	tags = var.inp.app
}

resource "aws_api_gateway_resource" "main" {
	for_each = toset(var.rest_api ? ["0"] : [])
	rest_api_id = aws_api_gateway_rest_api.main["0"].id
	parent_id = aws_api_gateway_rest_api.main["0"].root_resource_id
	path_part = aws_lambda_function.main.function_name
}

resource "aws_api_gateway_method" "main" {
	for_each = toset(var.rest_api ? ["0"] : [])
	rest_api_id = aws_api_gateway_rest_api.main[0].id
	resource_id = aws_api_gateway_resource.main[0].id
	http_method = "GET"
	authorization = "NONE"
	request_parameters = {
		"method.request.querystring.job_name" = true
	}
}

resource "aws_api_gateway_integration" "main" {
	for_each = toset(var.rest_api ? ["0"] : [])
	rest_api_id = aws_api_gateway_rest_api.main["0"].id
	resource_id = aws_api_gateway_resource.main["0"].id
	http_method = aws_api_gateway_method.main["0"].http_method
	integration_http_method = "GET"
	type = "AWS_PROXY"
	uri = aws_lambda_function.main.invoke_arn
}

resource "aws_api_gateway_deployment" "main" {
	for_each = toset(var.rest_api ? ["0"] : [])
	depends_on = [aws_api_gateway_integration.main["0"]]
	rest_api_id = aws_api_gateway_rest_api.main["0"].id
	stage_name = "main"

	lifecycle {
		create_before_destroy = true
	}
}

resource "aws_lambda_permission" "main" {
	for_each = toset(var.rest_api ? ["0"] : [])
	statement_id = "AllowExecutionFromAPIGateway"
	action = "lambda:InvokeFunction"
	function_name = aws_lambda_function.main.function_name
	principal = "apigateway.amazonaws.com"
	source_arn = "arn:aws:execute-api:${var.inp.aws_region}:${var.inp.aws_user_id}:${aws_api_gateway_rest_api.main["0"].id}/*/${aws_api_gateway_method.main["0"].http_method}${aws_api_gateway_resource.main["0"].path}"
}
