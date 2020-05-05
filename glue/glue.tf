resource "aws_glue_catalog_database" "quotes" {
	name = "${var.inp.app.id}_quotes"
}

resource "aws_glue_classifier" "csv" {
	name = "${var.inp.app.id}_csv"

	csv_classifier {
		allow_single_column = false
		contains_header = "PRESENT"
		delimiter = ","
		disable_value_trimming = false
		quote_symbol = "\""
	}
}

module "crawler_in_quotes" {
	source = "./crawler"
	catalog_name = aws_glue_catalog_database.quotes.name
	crawler_name = "in_quotes"
	classifiers = [aws_glue_classifier.csv.name]
	s3_path = "s3://${var.bucket_name}/csv"
	role = var.role
	inp = var.inp
}

module "html2csv" {
	source = "./pythonjob"
	script_name = "html2csv"
	bucket_name = var.bucket_name
	role = var.role
	inp = var.inp
}

module "crawler_quotes" {
	source = "./crawler"
	catalog_name = aws_glue_catalog_database.quotes.name
	crawler_name = "quotes"
	classifiers = [aws_glue_classifier.csv.name]
	s3_path = "s3://${var.bucket_name}/csv_clean"
	role = var.role
	inp = var.inp
}

module "clean_quotes" {
	source = "./pythonjob"
	script_name = "clean_quotes"
	bucket_name = var.bucket_name
	role = var.role
	inp = var.inp
}
