resource "aws_sns_topic" "main" {
	name = "${var.inp.app.id}_${var.topic}"
}

resource "aws_sns_topic_subscription" "main" {
    for_each = toset(var.subscribe)
	topic_arn = aws_sns_topic.main.arn
	protocol  = each.key.protocol
	endpoint  = each.key.endpoint
}
