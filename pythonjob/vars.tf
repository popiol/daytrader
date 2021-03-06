variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		bucket_name = string
		alert_topic = string
		log_table = string
		event_table = string
		temporary = bool
    })
}

variable "inp2" {
	type = map(string)
	default = {}
}

variable "extra-py-files" {
	type = list(string)
	default = []
}

variable "script_name" {
	type = string
}

variable "role" {
	type = string
}
