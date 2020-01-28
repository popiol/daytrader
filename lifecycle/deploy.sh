#!/bin/bash

if [ -z "$1" ]; then
	echo "Missing argument"
	echo "Usage: $(basename -- $0) <branch_name>"
	exit 1
fi

branch_name=$1
aws_user="$(basename -- $branch_name)"
stage="$(basename -- $(dirname $branch_name))"

if [ "$aws_user" = "master" ]; then
	stage="prod"
fi

if [ "$aws_user" = "release" ]; then
	stage="test"
fi

if [ -z "$stage" ]; then
	stage="dev"
fi

echo "Stage $stage"
echo "AWS user $aws_user"

echo "Checkout"

git checkout $branch_name

echo "Pull"

git pull

echo "Apply Terraform"

cd terraform

terraform apply

