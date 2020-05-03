resource "aws_iam_role" "main" {
	name = "${var.inp.app.id}_${var.name}"
	assume_role_policy = data.aws_iam_policy_document.main.json
}

data "aws_iam_policy_document" "main" {
	statement {
		actions = [
			"sts:AssumeRole"
		]
		principals {
			type = "Service"
			identifiers = [
				"${var.service}.amazonaws.com"
			]
		}
	}
}

resource "aws_iam_role_policy_attachment" "main" {
    for_each = toset(var.attached)
	role = aws_iam_role.main.name
	policy_arn = "arn:aws:iam::aws:policy/service-role/${each.key}"
}

resource "aws_iam_role_policy" "main" {
    for_each = toset(var.custom)
	name = aws_iam_role.main.name
	role = aws_iam_role.main.id
	policy = each.key
}
