variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
    })
}

variable "error_logs" {
	type = list(string)
}

variable "targets" {
	type = list(string)
}
