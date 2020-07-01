resource "aws_batch_compute_environment" "main" {
	compute_environment_name = var.inp.app.id
	service_role = var.batch_role
	type = "MANAGED"
	security_group_ids = var.sec_groups
	subnets = var.subnets
	tags = var.inp.app
	
	compute_resources {
		instance_role = var.batch_role
		max_vcpus = 4
		min_vcpus = 1
		type = "EC2"

		instance_type = [
			"a1.medium",
			"t2.micro",
			"t2.small",
			"t2.medium",
			"t3.micro",
			"t3.small",
			"t3.medium",
			"a1.large",
			"c5.large"
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
	name = var.inp.app.id
}

module "test_train_init" {
	source = "./batchjob"
	job_name = "test_train_init"
	inp = var.inp
}
