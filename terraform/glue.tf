resource "aws_glue_catalog_database" "quotes" {
  name = "${var.app_id}_quotes"
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

