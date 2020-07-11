locals {
	content_type_map = {
		html = "text/html; charset=UTF-8"
		js = "application/javascript; charset=UTF-8"
	}
}

resource "aws_s3_bucket_object" "main" {
	bucket = var.inp.bucket_name
	key = "www/${var.file_name}"
	content = templatefile("${path.module}/${var.file_name}", var.vars)
	etag = filemd5("${path.module}/${var.file_name}")
    acl = "public-read"
	content_type = local.content_type_map[split(".", var.file_name)[1]]
}
