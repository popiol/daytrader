module "event_process_log" {
	source = "./dynamodb"
	table_name = "event_process_log"
	keys = ["obj_key"]
	inp = var.inp
}

module "event_table" {
	source = "./dynamodb"
	table_name = "events"
	keys = ["comp_code", "quote_dt"]
	inp = var.inp
}
