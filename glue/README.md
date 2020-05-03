Creates the ETL workflow:

1. Transform HTML table to CSV
  * input: /html
  * output: /csv
  * partition field: date
  
1. Clean CSV
  * input: /csv
  * output: /csv_clean
  * rejected: /csv_rejected

