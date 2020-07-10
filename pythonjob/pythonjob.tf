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
	job_args = merge(merge(var.inp, var.inp2), length(var.extra-py-files)>0 ? {
		extra-py-files = join(",", [for x in var.extra-py-files : "s3://${var.inp.bucket_name}/scripts/${x}"])
	} : {})
}

resource "aws_s3_bucket_object" "script" {
	bucket = var.inp.bucket_name
	key = "/scripts/${var.script_name}.py"
	source = "${path.module}/${var.script_name}.py"
	etag = filemd5("${path.module}/${var.script_name}.py")
}

resource "aws_s3_bucket_object" "extra-py-files" {
	for_each = toset(var.extra-py-files)
	bucket = var.inp.bucket_name
	key = "scripts/${each.key}"
	source = "${path.module}/${each.key}"
	etag = filemd5("${path.module}/${each.key}")
}
