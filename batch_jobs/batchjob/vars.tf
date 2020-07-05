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

variable "job_name" {
	type = string
}

variable "image_name" {
	type = string
}

variable "launch_template" {
	type = string
}
