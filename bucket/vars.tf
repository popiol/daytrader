variable "bucket_name" {
	type = string
}

variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
        aws_user = string
        temporary = bool
    })
}

variable "archived_paths" {
    type = list(string)
}
