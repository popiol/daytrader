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

variable "file_name" {
	type = string
}

variable "vars" {
	type = map(string)
	default = {}
}
