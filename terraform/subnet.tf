resource "aws_subnet" "subnet1" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = "172.16.10.0/24"
  availability_zone = "${data.aws_region.current.name}a"
}
