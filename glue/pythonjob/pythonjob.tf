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
