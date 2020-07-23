locals {
	rules = {
		rule1 = {
			prefix = "data/"
			expiration = 90
		}
		rule2 = {
			prefix = "logs/"
			expiration = 60
		}
	}
}

resource "aws_s3_bucket" "main" {
	bucket = "${var.inp.aws_user}.${replace(var.inp.app.id,"_","-")}-${var.bucket_name}"
	acl = "private"
	tags = var.inp.app
	force_destroy = var.inp.temporary

	dynamic "lifecycle_rule" {
		for_each = local.rules
		content {
			prefix = lifecycle_rule.value["prefix"]
			expiration {
				days = lifecycle_rule.value["expiration"]
			}
		}
	}

	dynamic "lifecycle_rule" {
		for_each = toset(var.archived_paths)

		content {
			id = "archive${replace(lifecycle_rule.key,"/","_")}"
			enabled = true
			prefix = lifecycle_rule.key

			transition {
				days = 30
				storage_class = "STANDARD_IA"
			}

			transition {
				days = 360
				storage_class = "GLACIER"
			}
		}
	}
}

data "aws_iam_policy_document" "access" {
	policy_id = "${var.inp.app.id}_${var.bucket_name}_s3"

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

	statement {
		actions = [
			"s3:ListBucket"
		]
		resources = [
			"${aws_s3_bucket.main.arn}"
		]
	}
}
