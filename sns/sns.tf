data "template_file" "main" {
	template = file("${path.module}/sns.json")
	
	vars {
		topic = "${var.inp.app.id}_${var.topic}"
		display_name  = "Daytrader"
		subscribe = jsonencode(var.subscribe)
	}
}

resource "aws_cloudformation_stack" "main" {
	name = "${var.inp.app.id}_${var.topic}"
	template_body = data.template_file.main.rendered
	tags = var.inp.app
}
