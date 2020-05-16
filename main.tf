terraform {
	backend "s3" {
		bucket = "${STATEFILE_BUCKET}"
		key = "${APP_NAME}/${APP_VER}/tfstate"
		region = "${AWS_REGION}"
	}
}

provider "aws" {
	region = var.inp.aws_region
}

module "s3_quotes" {
	source = "./bucket"
	bucket_name = "quotes"
	archived_paths = ["/html","/csv"]
	inp = var.inp
}

module "alerts" {
	source = "./sns"
	topic = "alerts"
	subscribe = [{
		Protocol = "email"
		Endpoint = var.inp.notify_email_addr
	}]
	inp = var.inp
}

module "lambda_role" {
	source = "./role"
	role_name = "lambda"
	service = "lambda"
	custom_policies = [module.s3_quotes.access_policy]
	inp = var.inp
}

module "get_quotes" {
	source = "./lambda"
	function_name = "get_quotes"
	crontab_entry = "cron(31 12-21 ? * 2-6 *)"
	role = module.lambda_role.role_arn
	inp = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		sns_arn = module.alerts.arn
	})
}

module "glue_role" {
	source = "./role"
	role_name = "glue"
	service = "glue"
	custom_policies = [module.s3_quotes.access_policy]
	attached_policies = ["AWSGlueServiceRole"]
	inp = var.inp
}

module "etl" {
	source = "./glue"
	bucket_name = module.s3_quotes.bucket_name
	role = module.glue_role.role_arn
	inp = var.inp
}
