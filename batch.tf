module "batch_role" {
	source = "./role"
	role_name = "batch"
	service = "batch"
	attached_policies = ["service-role/AWSBatchServiceRole"]
	inp = var.inp
}

resource "aws_iam_instance_profile" "batch" {
	role = module.ec2_role.role_name
}

resource "aws_batch_compute_environment" "main" {
	compute_environment_name = var.inp.app.id
	service_role = module.batch_role.role_arn
	type = "MANAGED"

	compute_resources {
		instance_role = aws_iam_instance_profile.batch.arn
		max_vcpus = 2
		min_vcpus = 0
		desired_vcpus = 0
		security_group_ids = module.vpc.security_groups
		subnets = module.vpc.subnets
		type = "EC2"
		instance_type = [
			"c4.large",
		]
		image_id = "ami-0dd9f78450fe3a3fa"
		ec2_key_pair = "popiolkey4"
		tags = var.inp.app
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
	image_name = aws_ecr_repository.ml.name
	inp = local.common_inputs
}

module "batch_train_init" {
	source = "./batchjob"
	job_name = "train_init"
	image_name = aws_ecr_repository.ml.name
	inp = local.common_inputs
}

module "test_test_model" {
	source = "./batchjob"
	job_name = "test_test_model"
	image_name = aws_ecr_repository.ml.name
	inp = local.common_inputs
}

module "batch_test_model" {
	source = "./batchjob"
	job_name = "test_model"
	image_name = aws_ecr_repository.ml.name
	inp = local.common_inputs
}
