variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		notify_email_addr = string
    })
}

variable "subscribe" {
	type = list(object({
		protocol = string
		endpoint = string
	}))
}
