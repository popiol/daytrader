resource "aws_api_gateway_rest_api" "main" {
	name = aws_lambda_function.main.function_name
	tags = var.inp.app
}

resource "aws_api_gateway_resource" "main" {
	rest_api_id = aws_api_gateway_rest_api.main.id
	parent_id = aws_api_gateway_rest_api.main.root_resource_id
	path_part = aws_lambda_function.main.function_name
}

resource "aws_api_gateway_method" "main" {
	rest_api_id = aws_api_gateway_rest_api.main[0].id
	resource_id = aws_api_gateway_resource.main[0].id
	http_method = "GET"
	authorization = "NONE"
	request_parameters = {for x in var.query_params : x => true}
}

resource "aws_api_gateway_integration" "main" {
	rest_api_id = aws_api_gateway_rest_api.main.id
	resource_id = aws_api_gateway_resource.main.id
	http_method = aws_api_gateway_method.main.http_method
	integration_http_method = "POST"
	type = "AWS_PROXY"
	uri = aws_lambda_function.main.invoke_arn
}

resource "aws_api_gateway_deployment" "main" {
	depends_on = [aws_api_gateway_integration.main]
	rest_api_id = aws_api_gateway_rest_api.main.id
	stage_name = "main"

	lifecycle {
		create_before_destroy = true
	}
}

resource "aws_lambda_permission" "main" {
	statement_id = "AllowExecutionFromAPIGateway"
	action = "lambda:InvokeFunction"
	function_name = aws_lambda_function.main.function_name
	principal = "apigateway.amazonaws.com"
	source_arn = "arn:aws:execute-api:${var.inp.aws_region}:${var.inp.aws_user_id}:${aws_api_gateway_rest_api.main.id}/*/${aws_api_gateway_method.main.http_method}${aws_api_gateway_resource.main.path}"
}

resource "aws_api_gateway_stage" "main" {
	stage_name = aws_api_gateway_deployment.main.stage_name
	rest_api_id = aws_api_gateway_rest_api.main.id
	deployment_id = aws_api_gateway_deployment.main.id
}

resource "aws_api_gateway_method_response" "main" {
    rest_api_id = aws_api_gateway_rest_api.main.id
    resource_id = aws_api_gateway_resource.main.id
    http_method = aws_api_gateway_method.main.http_method
    status_code = "200"
    response_parameters = {
        "method.response.header.Access-Control-Allow-Origin" = true
    }
    depends_on = [aws_api_gateway_method.main]
}
