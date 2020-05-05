resource "aws_glue_job" "main" {
	name = "${var.inp.app.id}_${var.script_name}"
	role_arn = var.role
	max_capacity = "0.0625"
	tags = var.inp.app

	command {
		name = "pythonshell"
		script_location = "s3://${var.bucket_name}/scripts/${var.script_name}.py"
		python_version = "3"
	}
}

resource "aws_s3_bucket_object" "script" {
	bucket = var.bucket_name
	key = "/scripts/${var.script_name}.py"
	source = "${path.module}/${var.script_name}.py"
	etag = filemd5("${path.module}/${var.script_name}.py")
	tags = var.inp.app
}
