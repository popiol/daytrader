output "ecs_cluster_name" {
    value = split("/", aws_batch_compute_environment.main.ecs_cluster_arn)[1]
}
