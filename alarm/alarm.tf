resource "aws_cloudwatch_metric_alarm" "main" {
    for_each = toset(var.error_logs)
    alarm_name = "${var.inp.app.id}${replace(each.key,"/","_")}"
    evaluation_periods = 1
    period = 3600
    datapoints_to_alarm = 1
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
