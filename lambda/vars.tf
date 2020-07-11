variable "function_name" {
	type = string
}

variable "crontab_entry" {
	type = string
	default = ""
}

variable "on_failure" {
	type = list(string)
}

variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		aws_user_id = string
		bucket_name = string
		alert_topic = string
	})
}

variable "inp2" {
	type = map(string)
	default = {}
}

variable "env_vars" {
	type = map(string)
	default = {}
}

variable "role" {
	type = string
}
