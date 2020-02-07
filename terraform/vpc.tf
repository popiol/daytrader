resource "aws_vpc" "vpc1" {
  cidr_block = "172.16.0.0/16"

  tags = {
    App = var.app
    AppVer = var.app_ver
    AppStage = var.app_stage
    TerraformID = "aws_vpc.vpc1"
  }
}

