variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		bucket_name = string
		alert_topic = string
		event_process_log = string
		event_table = string
	})
}

variable "role" {
	type = string
}
