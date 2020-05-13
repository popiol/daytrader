variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		temporary = bool
	})
}

variable "role" {
	type = string
}

variable "bucket_name" {
	type = string
}
