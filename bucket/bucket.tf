resource "aws_s3_bucket" "main" {
	bucket = "${var.inp.aws_user}.${replace(var.inp.app.id,"_","-")}-${var.bucket_name}"
	acl = "private"
	tags = var.inp.app
}

data "aws_iam_policy_document" "access" {
	statement {
		actions = [
			"s3:GetObject",
			"s3:PutObject",
			"s3:DeleteObject"
		]
		resources = [
			"${aws_s3_bucket.main.arn}/*"
		]
	}
}
