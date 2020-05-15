variable "topic" {
	type = string
}

variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
    })
}

variable "subscribe" {
	type = list(object({
		protocol = string
		endpoint = string
	}))
}
