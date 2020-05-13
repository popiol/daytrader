variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		temporary = bool
    })
}

variable "script_name" {
	type = string
}

variable "bucket_name" {
	type = string
}

variable "role" {
	type = string
}
