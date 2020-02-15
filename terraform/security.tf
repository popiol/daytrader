resource "aws_security_group" "security1" {
  name = "${var.app_id}_security1"
  vpc_id = aws_vpc.vpc1.id

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
