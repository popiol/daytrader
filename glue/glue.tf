resource "aws_glue_catalog_database" "quotes" {
	name = "${var.inp.app.id}_quotes"
}

resource "aws_glue_classifier" "csv" {
	name = "${var.inp.app.id}_in_quotes"

	csv_classifier {
		allow_single_column    = false
		contains_header        = "PRESENT"
		delimiter              = ","
		disable_value_trimming = false
		quote_symbol           = "\""
	}
}

module "crawler_in_quotes" {
	source = "crawler"
	catalog_name = aws_glue_catalog_database.quotes.name
	crawler_name = "in_quotes"
	classifiers = [aws_glue_classifier.csv.name]
	s3_path = "s3://${var.bucket_name}/csv"
	role = var.role
	inp = var.inp
}

resource "aws_s3_bucket_object" "scripts" {
	for_each = fileset("scripts/", "*py")
	bucket = var.bucket_name
	key	= "scripts/${each.value}"
	source = "scripts/${each.value}"
	etag = filemd5("scripts/${each.value}")
	tags = var.tags
}

module "html2csv" {
	source = "pythonjob"
	script_name = "html2csv"
	role = var.role
	inp = var.inp
}

module "crawler_in_quotes" {
	source = "crawler"
	catalog_name = aws_glue_catalog_database.quotes.name
	crawler_name = "quotes"
	classifiers = [aws_glue_classifier.csv.name]
	s3_path = "s3://${var.bucket_name}/csv_clean"
	role = var.role
	inp = var.inp
}

module "clean_quotes" {
	source = "pythonjob"
	script_name = "clean_quotes"
	role = var.role
	inp = var.inp
}
