variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
        aws_user = string
    })
}

variable "table_name" {
    type = string
}

variable "keys" {
    type = list(string)
}
