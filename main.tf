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

data "aws_caller_identity" "current" {}

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

locals {
	common_inputs = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
		aws_user_id = data.aws_caller_identity.current.account_id
	})
} 

module "lambda_role" {
	source = "./role"
	role_name = "lambda"
	service = "lambda"
	attached_policies = ["AmazonEC2FullAccess"]
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
	inp = merge(local.common_inputs, {
		log_table = module.dynamodb.table_name.event_process_log
		event_table = module.dynamodb.table_name.event_table
	})
}

module "vpc" {
	source = "./vpc"
	inp = local.common_inputs
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
	attached_policies = ["AmazonEC2FullAccess","service-role/AmazonEC2ContainerServiceforEC2Role","EC2InstanceConnect"]
	custom_policies = [module.s3_quotes.access_policy]
	inp = var.inp
}

module "stop_instance" {
	source = "./lambda"
	function_name = "stop_instance"
	on_failure = [module.alerts.arn]
	role = module.lambda_role.role_arn
	inp = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
	})
}

module "batch_jobs" {
	source = "./batch_jobs"
	batch_role = module.batch_role.role_arn
	ec2_role_name = module.ec2_role.role_name
	stop_instance_function = module.stop_instance.arn
	sec_groups = module.vpc.security_groups
	subnets = module.vpc.subnets
	image_id = "ami-0dd9f78450fe3a3fa"
	inp = local.common_inputs
}

module "ec2_template_ml" {
	source = "./ec2"
	instance_name = "ml"
	role_name = module.ec2_role.role_name
	sec_groups = module.vpc.security_groups
	subnets = module.vpc.subnets
	inp = local.common_inputs
	tags = {batch_job = "ml"}
	user_data = base64encode(templatefile("${path.module}/ec2/files/ml_init.sh", {
		ECS_CLUSTER_NAME = module.batch_jobs.ecs_cluster_name
	}))
}
