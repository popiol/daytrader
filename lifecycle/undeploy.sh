#!/bin/bash

source lifecycle/deploy.sh

echo "Destroy"

terraform destroy -var-file="../config.ini" -auto-approve

