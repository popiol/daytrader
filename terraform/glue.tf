resource "aws_glue_catalog_database" "quotes" {
	name = "${var.app_id}_quotes"
}

resource "aws_glue_crawler" "quotes" {
	database_name = aws_glue_catalog_database.quotes.name
	name = "quotes"
	table_prefix = "${var.app_id}_"
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
	for_each = fileset("scripts/", "*py")
	bucket = aws_s3_bucket.quotes.id
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

resource "aws_s3_bucket_object" "lib" {
	for_each = fileset("scripts/lib/", "*zip")
	bucket = aws_s3_bucket.quotes.id
	key	= "scripts/lib/${each.value}"
	source = "scripts/lib/${each.value}"
	etag = filemd5("scripts/lib/${each.value}")

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_s3_bucket_object.lib"
	}
}

resource "aws_glue_job" "html2csv" {
	name = "${var.app_id}_html2csv"
	role_arn = aws_iam_role.lambdarole.arn
	max_capacity = "0.0625"

	command {
		name = "pythonshell"
		script_location = "s3://${aws_s3_bucket.quotes.bucket}/scripts/html2csv.py"
		python_version = "3"
	}

	#default_arguments = {
	#	"--extra-py-files" = "s3://${aws_s3_bucket.quotes.bucket}/scripts/lib/lxml.zip"
	#}

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_glue_job.html2csv"
	}
}

