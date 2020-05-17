variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		bucket_name = string
		alert_topic = string
    })
}

variable "script_name" {
	type = string
}

variable "role" {
	type = string
}
