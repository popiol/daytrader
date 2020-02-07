resource "aws_s3_bucket" "quotes_bucket" {
  bucket = "popiol.${var.app_id}_quotes"
  acl    = "private"
}

