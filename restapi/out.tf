output "invoke_url" {
    value = "${aws_api_gateway_deployment.main.invoke_url}${aws_api_gateway_resource.main.path}"
}
