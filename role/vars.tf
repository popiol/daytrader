variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
    })
}

variable "attached" {
	type = list(string)
    default = []
}

variable "custom" {
	type = list(string)
    default = []
}
