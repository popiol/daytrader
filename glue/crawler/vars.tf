variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
    })
}

variable "crawler_name" {
	type = string
}

variable "classifiers" {
	type = list(string)
}

variable "s3_path" {
	type = string
}

variable "role" {
	type = string
}
