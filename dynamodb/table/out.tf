output "access_policy" {
  value = data.aws_iam_policy_document.access.json
}

output "table_name" {
  value = aws_dynamodb_table.main.name
}
