resource "aws_iam_instance_profile" "main" {
    name = "${var.inp.app.id}_${var.instance_name}"
	role = var.role_name
}

resource "aws_launch_template" "main" {
    name = "${var.inp.app.id}_${var.instance_name}"
    image_id = "ami-0466acdbae3d9cc42"
    instance_type = "t3a.small"
    vpc_security_group_ids = var.sec_groups
    instance_initiated_shutdown_behavior = "terminate"

    iam_instance_profile {
        arn = aws_iam_instance_profile.main.arn
    }
    
    network_interfaces {
        associate_public_ip_address = false
        subnet_id = var.subnets[0]
    }
    
    tag_specifications {
        resource_type = "instance"
        tags = var.inp.app
    }
}
