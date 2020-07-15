resource "aws_batch_job_definition" "main" {
    name = "${var.inp.app.id}_${var.job_name}"
    type = "container"
    container_properties = jsonencode({
        command = ["python", "${var.job_name}.py"]
        image = "${var.inp.aws_user_id}.dkr.ecr.${var.inp.aws_region}.amazonaws.com/${var.image_name}"
        memory = 1500
        vcpus = 2
        environment = [
            {name = "bucket_name", value = var.inp.bucket_name},
            {name = "event_table_name", value = var.inp.event_table},
            {name = "temporary", value = var.inp.temporary ? "1" : "0"}
        ]
    })
}
