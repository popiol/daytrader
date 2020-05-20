output "access_policy" {
  value = data.aws_iam_policy_document.access.json
}

output "table_name" {
  value = var.table_name
}
