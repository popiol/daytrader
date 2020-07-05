resource "aws_iam_role" "main" {
	name = "${var.inp.app.id}_${var.role_name}"
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
    for_each = toset(var.attached_policies)
	role = aws_iam_role.main.name
	policy_arn = "arn:aws:iam::aws:policy/${each.key}"
}

resource "aws_iam_role_policy" "main" {
    for_each = toset(var.custom_policies)
	name = jsondecode(each.key)["Id"]
	role = aws_iam_role.main.id
	policy = each.key
}
