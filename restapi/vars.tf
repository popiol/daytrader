variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		aws_user_id = string
		bucket_name = string
		alert_topic = string
		temporary = string
	})
}

variable "lambda_function" {
	type = string
}
