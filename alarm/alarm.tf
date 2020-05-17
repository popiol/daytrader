resource "aws_cloudwatch_metric_alarm" "main" {
    foreach = toset(var.error_logs)
    alarm_name = "${var.inp.app.id}_${replace(each.key,"/","-")}"
    evaluation_periods = "24"
    period = "3600"
    comparison_operator = "GreaterThanThreshold"
    metric_name = "IncomingLogEvents"
    namespace = "AWS/Logs"
    statistic = "Sum"
    threshold = 0
    dimensions = {
        LogGroupName = each.key
    }
    alarm_actions = var.targets
    tags = var.inp.app
}
