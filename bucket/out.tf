output "access_policy" {
  value = data.aws_iam_policy_document.access.json
}

output "bucket_name" {
  value = aws_s3_bucket.main.bucket
}
