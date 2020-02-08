resource "aws_network_interface" "network1" {
	subnet_id   = aws_subnet.subnet1.id

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_network_interface.network1"
	}
}

