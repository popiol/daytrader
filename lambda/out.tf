output "arn" {
    value = aws_lambda_function.main.arn
}

output "invoke_url" {
    value = var.rest_api ? aws_api_gateway_deployment.main[0].invoke_url : ""
}
