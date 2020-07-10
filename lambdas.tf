module "lambda_role" {
	source = "./role"
	role_name = "lambda"
	service = "lambda"
	attached_policies = ["AmazonEC2FullAccess", "CloudWatchLogsReadOnlyAccess", "AmazonS3FullAccess", "AmazonSNSFullAccess"]
	inp = var.inp
}

module "get_quotes" {
	source = "./lambda"
	function_name = "get_quotes"
	crontab_entry = "cron(31 12-21 ? * 2-6 *)"
	on_failure = [module.alerts.arn]
	role = module.lambda_role.role_arn
	inp = local.common_inputs
}

module "get_sample_quotes" {
	source = "./lambda"
	function_name = "get_sample_quotes"
	on_failure = [module.alerts.arn]
	role = module.lambda_role.role_arn
	inp = local.common_inputs
	env_vars = {
		app_id = var.inp.app.id
	}
	rest_api = true
}
