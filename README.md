# Daytrader

The project meant to download and process stock market quotes, analyse it and generate automated investment decisions. 

The tools used in the project:
* Gitlab CI/CD
* Terraform
* Docker
* AWS Batch
* AWS ECS
* AWS Glue
* AWS Lambda
* AWS S3

Deployment:
* Every commit triggers the Gitlab CI/CD script, which does the following:
  * executes terraform files to set up all needed AWS services
  * builds the docker image for the ML model processing (training/validation/prediction)
  * pushes the docker image to the AWS ECR repository
  * runs unit tests 
* The script creates separate environment for each Git branch and deletes it when the branch is removed

Input data:
* The data is downloaded by a Lambda function triggered every 1 hour during the stock exchange session
* The data stored in an S3 bucket
* The data is processed by sequence of jobs ran within an AWS Glue workflow
* The AWS Glue jobs clean the data, transform it into the JSON format and store in DynamoDB

ML model processing:
* There are separate AWS Batch jobs for training, validation and prediction
* Each job runs on the same Docker image but executes a different python script
* The model is stored in an S3 bucket
* There are several versions of the model: production model, development model, working model, initial model
