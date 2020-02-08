resource "aws_s3_bucket" "quotes" {
	bucket = "popiol.${replace(var.app_id,"_","-")}-quotes"
	acl    = "private"

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_s3_bucket.quotes"
	}
}

