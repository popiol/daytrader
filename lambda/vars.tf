variable "function_name" {
	type = string
}

variable "crontab_entry" {
	type = string
}

variable "on_failure" {
	type = list(string)
}

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
