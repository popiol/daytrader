resource "aws_iam_instance_profile" "main" {
	role = var.ec2_role_name
}

resource "aws_batch_compute_environment" "main" {
	compute_environment_name = var.inp.app.id
	service_role = var.batch_role
	type = "MANAGED"

	compute_resources {
		instance_role = var.ec2_role
		max_vcpus = 2
		min_vcpus = 0
		desired_vcpus = 0
		security_group_ids = var.sec_groups
		subnets = var.subnets
		type = "EC2"
		launch_template {
			launch_template_id = var.launch_template
		}
		instance_type = [
			"a1.large",
		]
	}
}

resource "aws_batch_job_queue" "main" {
	name = var.inp.app.id
	state = "ENABLED"
	priority = 1
	compute_environments = [aws_batch_compute_environment.main.arn]
}

#resource "aws_cloudwatch_event_rule" "main" {
#	name = "${var.inp.app.id}_batch_done"
#
#	event_pattern = jsonencode({
#		detail = {
#			status = ["FAILED", "SUCCEEDED"]
#		}
#		source = ["aws.batch"]
#	})
#}

#resource "aws_cloudwatch_event_target" "main" {
#	rule = aws_cloudwatch_event_rule.main.name
#	target_id = aws_cloudwatch_event_rule.main.name
#	arn = var.stop_instance_function
#	input = jsonencode(var.inp)
#}

resource "aws_ecr_repository" "ml" {
	name = "${var.inp.app.id}/ml"
}

module "test_train_init" {
	source = "./batchjob"
	job_name = "test_train_init"
	image_name = aws_ecr_repository.ml.name
	inp = var.inp
}
