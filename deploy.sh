#!/bin/bash

CONFIG_DIR=/home/gitlab-runner

source $CONFIG_DIR/config.ini

envsubst < config.tfvars > config.tfvars.new

mv config.tfvars.new config.tfvars

envsubst < main.tf > main.tf.new

mv main.tf.new main.tf

terraform init

terraform apply -var-file=config.tfvars
