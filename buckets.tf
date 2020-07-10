module "s3_quotes" {
	source = "./bucket"
	bucket_name = "quotes"
	archived_paths = ["html/","csv/","csv_clean/","csv_rejected/"]
	inp = var.inp
}
