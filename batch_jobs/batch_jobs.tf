resource "aws_iam_instance_profile" "main" {
	role = var.ec2_role_name
}

resource "aws_batch_compute_environment" "main" {
	compute_environment_name = var.inp.app.id
	service_role = var.batch_role
	type = "MANAGED"
	
	compute_resources {
		instance_role = aws_iam_instance_profile.main.arn
		max_vcpus = 4
		min_vcpus = 0
		desired_vcpus = 0
		type = "EC2"
		security_group_ids = var.sec_groups
		subnets = var.subnets
		tags = var.inp.app
		
		instance_type = [
			"a1.medium",
			"a1.large"
		]
	}
}

resource "aws_batch_job_queue" "main" {
	name = var.inp.app.id
	state = "ENABLED"
	priority = 1
	compute_environments = [aws_batch_compute_environment.main.arn]
}

resource "aws_ecr_repository" "ml" {
	name = "${var.inp.app.id}/ml"
}

module "test_train_init" {
	source = "./batchjob"
	job_name = "test_train_init"
	inp = var.inp
}
