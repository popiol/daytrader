output "arn" {
    value = aws_lambda_function.main.arn
}

output "name" {
    value = aws_lambda_function.main.function_name
}

output "invoke_arn" {
    value = aws_lambda_function.main.invoke_arn
}
