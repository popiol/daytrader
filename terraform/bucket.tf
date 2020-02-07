resource "aws_s3_bucket" "quotes_bucket" {
  bucket = replace()"-quotes"
  acl    = "private"

  tags = {
    App = var.app
    AppVer = var.app_ver
    AppStage = var.app_stage
    TerraformID = "aws_s3_bucket.quotes_bucket"
  }
}

