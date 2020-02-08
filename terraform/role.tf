resource "aws_iam_role" "lambdarole" {
	name = "${var.app_id}_role"
	path = "/${var.app}/${var.app_ver}/"

	assume_role_policy = <<EOF
{
	"Statement": [
		{
			"Action": "sts:AssumeRole",
			"Principal": {
				"Service": "lambda.amazonaws.com"
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

