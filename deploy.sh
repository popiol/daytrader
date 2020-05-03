#!/bin/bash

if [ -z $1 ]; then
    echo "Branch not specified"
    exit 1
else
    branch=$1
fi

export APP_VER=$branch

CONFIG_DIR=/home/gitlab-runner

#source $CONFIG_DIR/config.ini

echo APP_NAME=$APP_NAME
echo APP_VER=$APP_VER
echo AWS_USER=$AWS_USER
echo AWS_REGION=$AWS_REGION
echo STATEFILE_BUCKET=$STATEFILE_BUCKET
ls -ltr

envsubst < config.tfvars > config.tfvars.new

mv config.tfvars.new config.tfvars

envsubst < main.tf > main.tf.new

mv main.tf.new main.tf

terraform init

terraform apply -var-file=config.tfvars
