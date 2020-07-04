resource "aws_iam_instance_profile" "main" {
	role = var.ec2_role_name
}

resource "aws_batch_compute_environment" "main" {
	compute_environment_name = var.inp.app.id
	service_role = var.batch_role
	type = "UNMANAGED"
}

resource "aws_batch_job_queue" "main" {
	name = var.inp.app.id
	state = "ENABLED"
	priority = 1
	compute_environments = [aws_batch_compute_environment.main.arn]
}

resource "aws_cloudwatch_event_rule" "main" {
	name = "${var.inp.app.id}_batch_done"

	event_pattern = jsonencode({
		source = "aws.batch"
	})
}

resource "aws_ecr_repository" "ml" {
	name = "${var.inp.app.id}/ml"
}

module "test_train_init" {
	source = "./batchjob"
	job_name = "test_train_init"
	image_name = aws_ecr_repository.ml.name
	inp = var.inp
}
