resource "aws_glue_job" "main" {
	name = "${var.inp.app.id}_${var.script_name}"
	role_arn = var.role
	max_capacity = "0.0625"
	tags = var.inp.app

	command {
		name = "pythonshell"
		script_location = "s3://${var.inp.bucket_name}/scripts/${var.script_name}.py"
		python_version = "3"
	}

	default_arguments = {
		for key, val in local.job_args : "--${key}" => trim(jsonencode(val), "\"")
	}
}

locals {
	job_args = merge(var.inp, {
		extra-py-files = join(",", var.extra-py-files)
	})
}

resource "aws_s3_bucket_object" "script" {
	bucket = var.inp.bucket_name
	key = "/scripts/${var.script_name}.py"
	source = "${path.module}/${var.script_name}.py"
	etag = filemd5("${path.module}/${var.script_name}.py")
	tags = var.inp.app
}

resource "aws_s3_bucket_object" "extra-py-files" {
	for_each = toset(var.extra-py-files)
	bucket = var.inp.bucket_name
	key = "/scripts/${split("/","${each.key}")[4]}"
	source = "${path.module}/${split("/","${each.key}")[4]}"
	etag = filemd5("${path.module}/${split("/","${each.key}")[4]}")
	tags = var.inp.app
}
