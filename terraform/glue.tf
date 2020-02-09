resource "aws_glue_catalog_database" "quotes" {
	name = "${var.app_id}_quotes"
	prefix = "${var.app_id}_"
}

resource "aws_glue_crawler" "quotes" {
	database_name = aws_glue_catalog_database.quotes.name
	name = "quotes"
	role = aws_iam_role.lambdarole.arn

	s3_target {
		path = "s3://${aws_s3_bucket.quotes.bucket}"
	}

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_glue_crawler.quotes"
	}
}

resource "aws_s3_bucket_object" "scripts" {
	for_each = fileset("scripts/", "*")
	bucket = "s3://${aws_s3_bucket.quotes.bucket}"
	key	= "scripts/${each.value}"
	source = "scripts/${each.value}"
	etag = filemd5("scripts/${each.value}")

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_s3_bucket_object.scripts"
	}
}

resource "aws_glue_job" "html2csv" {
	name = "${var.app_id}_html2csv"
	role_arn = "${aws_iam_role.lambdarole.arn}"

	command {
		script_location = "s3://${aws_s3_bucket.quotes.bucket}/scripts/html2csv.py"
	}

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_glue_job.html2csv"
	}
}

