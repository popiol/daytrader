module "glue_role" {
	source = "./role"
	role_name = "glue"
	service = "glue"
	custom_policies = [
		module.s3_quotes.access_policy,
		module.alerts.publish_policy,
		module.event_process_log.access_policy,
		module.event_table.access_policy
	]
	attached_policies = ["service-role/AWSGlueServiceRole", "AWSBatchFullAccess"]
	inp = var.inp
}

locals {
    glue_inputs = merge(local.common_inputs, {
		log_table = module.event_process_log.table_name
		event_table = module.event_table.table_name
	})
}

resource "aws_glue_catalog_database" "quotes" {
	name = "${var.inp.app.id}_quotes"
}

module "html2csv" {
	source = "./pythonjob"
	script_name = "html2csv"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
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
	role = module.glue_role.role_arn
	inp = local.glue_inputs
}

module "clean_quotes" {
	source = "./pythonjob"
	script_name = "clean_quotes"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
}

module "crawler_quotes" {
	source = "./crawler"
	catalog_name = aws_glue_catalog_database.quotes.name
	crawler_name = "quotes"
	classifiers = [aws_glue_classifier.csv.name]
	s3_path = "s3://${var.bucket_name}/csv_clean"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
}

module "events" {
	source = "./pythonjob"
	script_name = "events"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
	inp2 = {"repeat"=1}
	extra-py-files = ["glue_utils.py"]
}

module "discretize" {
	source = "./pythonjob"
	script_name = "discretize"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
	extra-py-files = ["glue_utils.py"]
}

module "clear_events" {
	source = "./pythonjob"
	script_name = "clear_events"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
}

module "pricech_model" {
	source = "./pythonjob"
	script_name = "pricech_model"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
	extra-py-files = ["glue_utils.py"]
}

module "glue_train_init" {
	source = "./pythonjob"
	script_name = "train_init"
	role = module.glue_role.role_arn
	inp = local.glue_inputs
	extra-py-files = ["glue_utils.py"]
}
