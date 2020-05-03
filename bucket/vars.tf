variable "bucket_name" {
	type = string
}

variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
        user = string
    })
}
