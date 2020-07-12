resource "aws_glue_crawler" "main" {
	database_name = var.catalog_name
	name = "${var.inp.app.id}_${var.crawler_name}"
	table_prefix = "${var.crawler_name}_"
	role = var.role
	classifiers = var.classifiers
	tags = var.inp.app

	s3_target {
		path = var.s3_path
	}	
}
