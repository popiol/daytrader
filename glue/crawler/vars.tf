variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		temporary = bool
    })
}

variable "crawler_name" {
	type = string
}

variable "catalog_name" {
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
