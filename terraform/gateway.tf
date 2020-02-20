resource "aws_internet_gateway" "gateway1" {
	vpc_id = aws_vpc.vpc1.id

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_internet_gateway.gateway1"
	}
}

resource "aws_route_table" "route1" {
	vpc_id = aws_vpc.vpc1.id
	
	route {
		cidr_block = "0.0.0.0/0"
		gateway_id = aws_internet_gateway.gateway1.id
	}

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_route_table.route1"
	}
}

resource "aws_route_table" "route2" {
	vpc_id = aws_vpc.vpc1.id
	
	route {
		cidr_block = "0.0.0.0/0"
		gateway_id = aws_nat_gateway.nat1.id
	}

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_route_table.route2"
	}
}

resource "aws_route_table_association" "route1_subnet1" {
	subnet_id = aws_subnet.subnet1.id
	route_table_id = aws_route_table.route1.id
}

resource "aws_route_table_association" "route2_subnet2" {
	subnet_id = aws_subnet.subnet2.id
	route_table_id = aws_route_table.route2.id
}

resource "aws_nat_gateway" "nat1" {
	allocation_id = aws_eip.ip1.id
	subnet_id = aws_subnet.subnet1.id

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_nat_gateway.nat1"
	}
}

resource "aws_eip" "ip1" {
	vpc = true

	tags = {
		App = var.app
		AppVer = var.app_ver
		AppStage = var.app_stage
		TerraformID = "aws_eip.ip1"
	}
}

