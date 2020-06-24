resource "aws_glue_catalog_database" "quotes" {
	name = "${var.inp.app.id}_quotes"
}

module "html2csv" {
	source = "./pythonjob"
	script_name = "html2csv"
	role = var.role
	inp = var.inp
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
	s3_path = "s3://${var.inp.bucket_name}/csv"
	role = var.role
	inp = var.inp
}

module "clean_quotes" {
	source = "./pythonjob"
	script_name = "clean_quotes"
	role = var.role
	inp = var.inp
}

module "crawler_quotes" {
	source = "./crawler"
	catalog_name = aws_glue_catalog_database.quotes.name
	crawler_name = "quotes"
	classifiers = [aws_glue_classifier.csv.name]
	s3_path = "s3://${var.inp.bucket_name}/csv_clean"
	role = var.role
	inp = var.inp
}

module "events" {
	source = "./pythonjob"
	script_name = "events"
	role = var.role
	inp = var.inp
	extra-py-files = ["glue_utils.py"]
}

module "discretize" {
	source = "./pythonjob"
	script_name = "discretize"
	role = var.role
	inp = var.inp
	extra-py-files = ["glue_utils.py"]
}

module "clear_events" {
	source = "./pythonjob"
	script_name = "clear_events"
	role = var.role
	inp = var.inp
}

module "pricech_model" {
	source = "./pythonjob"
	script_name = "pricech_model"
	role = var.role
	inp = var.inp
	extra-py-files = ["glue_utils.py"]
}
