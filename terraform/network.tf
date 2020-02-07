resource "aws_network_interface" "network1" {
  subnet_id   = aws_subnet.subnet1.id
}

