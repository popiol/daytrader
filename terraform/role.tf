resource "aws_iam_role" "lambdarole" {
	name = "${var.app_id}_role"
	path = "/${var.app}/${var.app_ver}/"

	assume_role_policy = <<EOF
{
	"Statement": [
		{
			"Action": "sts:AssumeRole",
			"Principal": {
				"Service": [
					"lambda.amazonaws.com",
					"glue.amazonaws.com"
				]
			},
			"Effect": "Allow",
			"Sid": ""
		}
	]
}
EOF

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_iam_role.lambdarole"
	}
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
	role = aws_iam_role.lambdarole.name
	policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "glue_policy_attachment" {
	role = aws_iam_role.lambdarole.name
	policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "s3_access" {
	name = "${var.app_id}_s3_access"
	role = aws_iam_role.lambdarole.id
	policy = data.aws_iam_policy_document.s3_access_doc.json
}

data "aws_iam_policy_document" "s3_access_doc" {
	statement {
		actions = [
			"s3:GetObject",
			"s3:PutObject",
			"s3:DeleteObject"
		]
		resources = [
			"${aws_s3_bucket.quotes.arn}/*"
		]
	}
}

