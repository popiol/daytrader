resource "aws_batch_job_definition" "main" {
    name = "${var.inp.app.id}_${var.job_name}"
    type = "container"
    container_properties = jsonencode(local.container)
}

locals {
    container = {
        command = ["python", "${var.job_name}.py"]
        image = "${var.inp.aws_user}.dkr.ecr.${var.inp.aws_region}.amazonaws.com/${var.inp.app.id}/${var.job_name}"
        memory = 2048
        vcpus = 2
        environment = [
            {
                name = "BUCKET_NAME"
                value = var.inp.bucket_name
            }
        ]
    }
}
