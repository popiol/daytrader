resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
    tags = var.inp.app
}

resource "aws_subnet" "main" {
    vpc_id = aws_vpc.main.id
    cidr_block = aws_vpc.main.cidr_block
    map_public_ip_on_launch = true
    tags = var.inp.app
}

resource "aws_default_security_group" "main" {
    vpc_id = aws_vpc.main.id
    tags = var.inp.app

    dynamic "ingress" {
        for_each = toset(var.ingress)

        content {
            from_port = ingress.key[0]
            to_port = ingress.key[1]
            protocol = ingress.key[2]
            cidr_blocks = [ingress.key[3]]
        }
    }

    dynamic "egress" {
        for_each = toset(var.egress)

        content {
            from_port = egress.key[0]
            to_port = egress.key[1]
            protocol = egress.key[2]
            cidr_blocks = [egress.key[3]]
        }
    }
}

resource "aws_internet_gateway" "main" {
    vpc_id = aws_vpc.main.id
    tags = var.inp.app
}

resource "aws_default_route_table" "main" {
    default_route_table_id = aws_vpc.main.default_route_table_id
    tags = var.inp.app

    route {
		cidr_block = "0.0.0.0/0"
		gateway_id = aws_internet_gateway.main.id
	}
}

