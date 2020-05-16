resource "aws_cloudformation_stack" "main" {
	name = replace("${var.inp.app.id}-${var.topic}","_","-")
	template_body = templatefile("${path.module}/sns.json", {
		topic = replace(replace("${var.inp.app.id}${var.topic}","_",""),"-","")
		display_name  = "Daytrader Alerts"
		subscribe = jsonencode(var.subscribe)
	})
	tags = var.inp.app
}

data "aws_iam_policy_document" "publish" {
	policy_id = "${var.inp.app.id}_${var.bucket_name}_sns"

	statement {
		actions = [
			"sns:Publish"
		]
		resources = [
			aws_cloudformation_stack.main.outputs["ARN"]
		]
	}
}
