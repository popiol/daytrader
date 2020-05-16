resource "aws_cloudformation_stack" "main" {
	name = "${var.inp.app.id}_${var.topic}"
	template_body = templatefile("${path.module}/sns.json", {
		topic = "${var.inp.app.id}_${var.topic}"
		display_name  = "Daytrader Alerts"
		subscribe = jsonencode(var.subscribe)
	})
	tags = var.inp.app
}
