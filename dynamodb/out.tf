output "access_policy" {
  value = {
    event_process_log = module.event_process_log.access_policy
    evant_table = module.event_table.access_policy
  }
}

output "table_name" {
  value = {
    event_process_log = module.event_process_log.table_name
    evant_table = module.event_table.table_name
  }
}
