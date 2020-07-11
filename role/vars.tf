variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		temporary = bool
    })
}

variable "role_name" {
	type = string
}

variable "service" {
	type = string
}

variable "attached_policies" {
	type = list(string)
    default = []
}
