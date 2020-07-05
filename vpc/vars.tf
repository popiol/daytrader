variable "inp" {
	type = object({
        app = map(string)
        aws_region = string
		aws_user = string
		bucket_name = string
		alert_topic = string
		temporary = bool
	})
}

variable "ingress" {
	type = list(list(string))
	default = [["22", "22", "tcp", "0.0.0.0/0"]]
}

variable "egress" {
	type = list(list(string))
	default = [["0", "0", "-1", "0.0.0.0/0"]]
}
