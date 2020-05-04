resource "aws_glue_workflow" "quotes" {
  name = "${var.app.id}_quotes"
}

resource "aws_glue_trigger" "start" {
  name          = "start"
  type          = "SCHEDULED"
  workflow_name = aws_glue_workflow.quotes.name

  actions {
    job_name = module.html2csv.job_name
  }
}

resource "aws_glue_trigger" "html2csv" {
  name          = "html2csv"
  type          = "CONDITIONAL"
  workflow_name = aws_glue_workflow.quotes.name

  predicate {
    conditions {
      job_name = module.html2csv.job_name
      state    = "SUCCEEDED"
    }
  }

  actions {
    crawler_name = module.crawler_in_quotes.crawler_name
  }
}

resource "aws_glue_trigger" "crawler_in_quotes" {
  name          = "crawler_in_quotes"
  type          = "CONDITIONAL"
  workflow_name = aws_glue_workflow.quotes.name

  predicate {
    conditions {
      job_name = module.crawler_in_quotes.crawler_name
      state    = "SUCCEEDED"
    }
  }

  actions {
    job_name = module.clean_quotes.job_name
  }
}

resource "aws_glue_trigger" "clean_quotes" {
  name          = "clean_quotes"
  type          = "CONDITIONAL"
  workflow_name = aws_glue_workflow.quotes.name

  predicate {
    conditions {
      job_name = module.clean_quotes.job_name
      state    = "SUCCEEDED"
    }
  }

  actions {
    crawler_name = module.crawler_quotes.crawler_name
  }
}
