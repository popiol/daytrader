variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		bucket_name = string
		alert_topic = string
		log_table = string
		event_table = string
		temporary = bool
	})
}

variable "batch_role" {
	type = string
}

variable "ec2_role" {
	type = string
}

variable "sec_groups" {
	type = list(string)
}

variable "subnets" {
	type = list(string)
}
