resource "aws_batch_job_definition" "main" {
    name = "${var.inp.app.id}_${var.job_name}"
    type = "container"
    container_properties = jsonencode({
        command = ["python", "${var.job_name}.py"]
        image = "${var.inp.aws_user_id}.dkr.ecr.${var.inp.aws_region}.amazonaws.com/${var.image_name}"
        memory = 1500
        vcpus = 1.5
        environment = [
            {
                name = "BUCKET_NAME"
                value = var.inp.bucket_name
            }
        ]
    })
}
