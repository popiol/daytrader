variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		bucket_name = string
		alert_topic = string
		temporary = bool
	})
}

variable "instance_name" {
	type = string
}

variable "role_name" {
	type = string
}

variable "sec_groups" {
	type = list(string)
}

variable "subnets" {
	type = list(string)
}

variable "user_data" {
	type = string
	default = ""
}

variable "tags" {
	type = map(string)
	default = {}
}
