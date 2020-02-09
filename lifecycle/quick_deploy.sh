#!/bin/bash

cd terraform

terraform apply -var-file="../config.ini" -auto-approve

