resource "aws_iam_instance_profile" "main" {
    name = "${var.inp.app.id}_${var.instance_name}"
	role = var.role_name
}

resource "aws_launch_template" "main" {
    name = "${var.inp.app.id}_${var.instance_name}"
    image_id = "ami-0fdb9f8a87f3ff6c4"
    instance_type = "t3a.small"
    instance_initiated_shutdown_behavior = "terminate"
    user_data = var.user_data
    
    iam_instance_profile {
        arn = aws_iam_instance_profile.main.arn
    }
    
    network_interfaces {
        associate_public_ip_address = true
        subnet_id = var.subnets[0]
        security_groups = var.sec_groups
    }
    
    tag_specifications {
        resource_type = "instance"
        tags = merge(var.inp.app, var.tags)
    }
}
