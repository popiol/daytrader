variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
	})
}

variable "role" {
	type = string
}

variable "bucket_name" {
	type = string
}
