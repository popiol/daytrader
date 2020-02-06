#!/bin/bash

source lifecycle/deploy.sh

echo "Destroy"

cd terraform

terraform destroy -var-file="../config.ini" -auto-approve

