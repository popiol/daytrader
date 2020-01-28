#!/bin/bash

if [ -z "$1" ]; then
	echo "Missing argument."
	echo "Usage: $(basename -- $0) <new_repo_url>"
	exit 1
fi

repo_url=$1

git clone $repo_url

if [ $? -gt 0 ]; then
	echo "Invalid repo URL"
	exit 1
fi

repo_name="$(basename -- $repo_url)"
repo_name="${repo_name%.*}"

echo "Repo name: $repo_name"

cd $repo_name

git config credential.helper store

echo "Add upstream repo"

git remote add upstream https://github.com/popiol/aws_template.git

echo "Fetch upstream"

git fetch upstream

echo "Checkout master"

git checkout master

echo "Reset to upstream"

git reset --hard upstream/master

echo "Remove upstream"

git remote rm upstream

echo "Clear README.md file"

echo "# $repo_name" > README.md

echo "Add"

git add .

echo "Commit"

git commit -am "Fork aws_template"

echo "Push"

git push -fu origin master

