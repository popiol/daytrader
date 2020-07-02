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
	archived_paths = ["html/","csv/","csv_clean/","csv_rejected/"]
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
	custom_policies = [
		module.s3_quotes.access_policy,
		module.alerts.publish_policy
	]
	inp = var.inp
}

module "get_quotes" {
	source = "./lambda"
	function_name = "get_quotes"
	crontab_entry = "cron(31 12-21 ? * 2-6 *)"
	on_failure = [module.alerts.arn]
	role = module.lambda_role.role_arn
	inp = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
	})
}

module "dynamodb" {
	source = "./dynamodb"
	inp = var.inp
}

module "glue_role" {
	source = "./role"
	role_name = "glue"
	service = "glue"
	custom_policies = [
		module.s3_quotes.access_policy,
		module.alerts.publish_policy,
		module.dynamodb.access_policy.event_process_log,
		module.dynamodb.access_policy.event_table
	]
	attached_policies = ["service-role/AWSGlueServiceRole"]
	inp = var.inp
}

module "etl" {
	source = "./glue"
	role = module.glue_role.role_arn
	inp = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
		log_table = module.dynamodb.table_name.event_process_log
		event_table = module.dynamodb.table_name.event_table
	})
}

module "glue_error_alert" {
	source = "./alarm"
	error_logs = ["/aws-glue/python-jobs/error"]
	targets = [module.alerts.arn]
	inp = var.inp
}

module "vpc" {
	source = "./vpc"
	inp = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
	})
}

module "batch_role" {
	source = "./role"
	role_name = "batch"
	service = "batch"
	attached_policies = ["service-role/AWSBatchServiceRole"]
	inp = var.inp
}

module "ec2_role" {
	source = "./role"
	role_name = "ec2"
	service = "ec2"
	attached_policies = ["AmazonEC2FullAccess","service-role/AmazonEC2ContainerServiceforEC2Role"]
	inp = var.inp
}

module "batch_jobs" {
	source = "./batch_jobs"
	batch_role = module.batch_role.role_arn
	ec2_role = module.ec2_role.role_arn
	ec2_role_name = module.ec2_role.role_name
	sec_groups = module.vpc.security_groups
	subnets = module.vpc.subnets
	inp = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
	})
}
