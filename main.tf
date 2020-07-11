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

locals {
	common_inputs = merge(var.inp, {
		bucket_name = module.s3_quotes.bucket_name
		alert_topic = module.alerts.arn
		aws_user_id = data.aws_caller_identity.current.account_id
	})
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

module "vpc" {
	source = "./vpc"
	inp = local.common_inputs
}

module "ec2_role" {
	source = "./role"
	role_name = "ec2"
	service = "ec2"
	attached_policies = ["AmazonEC2FullAccess", "service-role/AmazonEC2ContainerServiceforEC2Role", "EC2InstanceConnect", "AmazonS3FullAccess"]
	inp = var.inp
}
