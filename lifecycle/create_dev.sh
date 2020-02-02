#!/bin/bash

if [ -z $1 ]; then
	echo "Missing argument."
	echo "Usage: $(basename -- $0) <dev_branch_name>"
	exit 1
fi

branch_name=$1
branch_name=`echo $branch_name | sed "s/^.*\///g"`
branch_name=dev/$branch_name

echo "Checkout master"

git checkout master

echo "Pull"

git pull

echo "Checkout new branch"

git checkout -b $branch_name master

echo "Push"

git push -u origin $branch_name

