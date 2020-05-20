output "access_policy" {
  value = {for x in module[*]: x => module[x].access_policy}
}

output "table_name" {
  value = {for x in module[*]: x => module[x].table_name}
}
