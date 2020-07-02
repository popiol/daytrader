resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "main" {
    vpc_id = aws_vpc.main.id
    cidr_block = aws_vpc.main.cidr_block
    tags = var.inp.app
}

resource "aws_security_group" "main" {
    vpc_id = aws_vpc.main.id
    tags = var.inp.app

    dynamic "ingress" {
        for_each = toset(var.ingress)
        from_port = ingress.key[0]
        to_port = ingress.key[1]
        protocol = ingress.key[2]
        cidr_blocks = [ingress.key[3]]
    }

    dynamic "egress" {
        for_each = toset(var.egress)
        from_port = egress.key[0]
        to_port = egress.key[1]
        protocol = egress.key[2]
        cidr_blocks = [egress.key[3]]
    }
}

resource "aws_internet_gateway" "main" {
    vpc_id = aws_vpc.main.id
    tags = var.inp.app
}

resource "aws_route_table" "main" {
	vpc_id = aws_vpc.main.id
	tags = var.inp.app

    route {
		cidr_block = "0.0.0.0/0"
		gateway_id = aws_internet_gateway.main.id
	}
}
