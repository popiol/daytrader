resource "aws_glue_workflow" "quotes" {
	name = "${var.inp.app.id}_quotes"
}

resource "aws_glue_trigger" "start" {
	name = "${var.inp.app.id}_start"
	type = "SCHEDULED"
	schedule = "cron(0 6 ? * 7 *)"
	workflow_name = aws_glue_workflow.quotes.name

	actions {
		job_name = module.html2csv.job_name
	}
}

resource "aws_glue_trigger" "html2csv" {
	name = "${var.inp.app.id}_html2csv"
	type = "CONDITIONAL"
	workflow_name = aws_glue_workflow.quotes.name

	predicate {
		conditions {
			job_name = module.html2csv.job_name
			state = "SUCCEEDED"
		}
	}

	actions {
		crawler_name = module.crawler_in_quotes.crawler_name
	}
}

resource "aws_glue_trigger" "crawler_in_quotes" {
	name = "${var.inp.app.id}_crawler_in_quotes"
	type = "CONDITIONAL"
	workflow_name = aws_glue_workflow.quotes.name

	predicate {
		conditions {
			crawler_name = module.crawler_in_quotes.crawler_name
			crawl_state = "SUCCEEDED"
		}
	}

	actions {
		job_name = module.clean_quotes.job_name
	}
}

resource "aws_glue_trigger" "clean_quotes" {
	name = "${var.inp.app.id}_clean_quotes"
	type = "CONDITIONAL"
	workflow_name = aws_glue_workflow.quotes.name

	predicate {
		conditions {
			job_name = module.clean_quotes.job_name
			state = "SUCCEEDED"
		}
	}

	actions {
		crawler_name = module.crawler_quotes.crawler_name
	}
}

resource "aws_glue_trigger" "discretize" {
	name = "${var.inp.app.id}_discretize"
	type = "CONDITIONAL"
	workflow_name = aws_glue_workflow.quotes.name

	predicate {
		conditions {
			crawler_name = module.crawler_quotes.crawler_name
			crawl_state = "SUCCEEDED"
		}
	}

	actions {
		job_name = module.discretize.job_name
	}
}

resource "aws_glue_trigger" "pricech_model" {
	name = "${var.inp.app.id}_pricech_model"
	type = "CONDITIONAL"
	workflow_name = aws_glue_workflow.quotes.name

	predicate {
		conditions {
			job_name = module.discretize.job_name
			state = "SUCCEEDED"
		}
	}

	actions {
		job_name = module.pricech_model.job_name
	}
}

resource "aws_glue_trigger" "start_events" {
	name = "${var.inp.app.id}_start_events"
	type = "SCHEDULED"
	schedule = "cron(*/5 * ? * * *)"

	actions {
		job_name = module.events.job_name
	}
}
