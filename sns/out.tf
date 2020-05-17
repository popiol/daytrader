output "arn" {
  value = aws_cloudformation_stack.main.outputs["ARN"]
}

output "publish_policy" {
  value = data.aws_iam_policy_document.publish.json
}
