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
}

module "get_sample_quotes_api" {
	source = "./restapi"
	api_name = module.get_sample_quotes.name
	lambda_function = module.get_sample_quotes.arn
	lambda_invoke_arn = module.get_sample_quotes.invoke_arn
	query_params = ["method.request.querystring.job_name"]
	inp = local.common_inputs
}
