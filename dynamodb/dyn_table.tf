resource "aws_dynamodb_table" "main" {
	name = "${var.inp.app.id}_${var.table_name}"
	billing_mode = "PAY_PER_REQUEST"
	hash_key = var.keys[0]
	range_key = length(var.keys) > 1 ? var.keys[1] : ""
	
	dynamic "attribute" {
		for_each = toset(var.keys)

		content {
			name = attribute.key
			type = "S"
		}
	}
	
	tags = var.inp.app
}

data "aws_iam_policy_document" "access" {
	policy_id = "${var.inp.app.id}_${var.table_name}_tb"

	statement {
		actions = [
			"dynamodb:GetItem",
			"dynamodb:Scan",
			"dynamodb:Query",
			"dynamodb:BatchGetItem",
			"dynamodb:BatchWriteItem",
			"dynamodb:DeleteItem",
			"dynamodb:PutItem",
			"dynamodb:UpdateItem",
			"dynamodb:DescribeTable",
			"dynamodb:DeleteTable",
			"dynamodb:CreateTable"
		]
		resources = [
			"${aws_dynamodb_table.main.arn}"
		]
	}
}
