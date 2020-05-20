output "access_policy" {
  value = {
    event_process_log = module.event_process_log.access_policy
    evant_table = module.evant_table.access_policy
  }
}

output "table_name" {
  value = {
    event_process_log = module.event_process_log.table_name
    evant_table = module.evant_table.table_name
  }
}
