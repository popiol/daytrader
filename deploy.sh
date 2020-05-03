#!/bin/bash

if [ -z $1 ]; then
    echo "Branch not specified"
    exit 1
else
    branch=$1
fi

export APP_VER=$branch

envsubst < config.tfvars > config.tfvars.new
mv config.tfvars.new config.tfvars

envsubst < main.tf > main.tf.new
mv main.tf.new main.tf

terraform init
terraform apply -var-file=config.tfvars
