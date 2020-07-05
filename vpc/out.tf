output "id" {
  value = aws_vpc.main.id
}

output "security_groups" {
  value = [aws_default_security_group.main.id]
}

output "subnets" {
  value = [aws_subnet.main.id]
}
