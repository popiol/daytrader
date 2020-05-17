variable "inp" {
	type = object({
		app = map(string)
		aws_region = string
		aws_user = string
		temporary = bool
		notify_email_addr = string
	})
}
