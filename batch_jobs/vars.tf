variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		aws_user_id = string
		bucket_name = string
		alert_topic = string
		temporary = bool
	})
}

variable "batch_role" {
	type = string
}

variable "ec2_role_name" {
	type = string
}

variable "ec2_role" {
	type = string
}

variable "stop_instance_function" {
	type = string
}
