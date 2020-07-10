resource "aws_s3_bucket_object" "main" {
	bucket = var.inp.bucket_name
	key = "www/${var.file_name}"
	source = "${path.module}/${var.file_name}"
	etag = filemd5("${path.module}/${var.file_name}")
    acl = "public-read"
}
