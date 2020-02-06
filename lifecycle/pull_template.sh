#!/bin/bash

echo "Add & commit"

git add .
git commit -am "Auto commit `date '+%Y-%m-%d %H:%M:%S'`"

echo "Add upstream repo"

git remote add upstream https://github.com/popiol/aws_template.git

echo "Checkout master"

git checkout master

echo "Pull"

git pull

echo "Fetch upstream"

git fetch upstream

echo "Reset lifecycle scripts"

git checkout upstream/master -- lifecycle

echo "Remove upstream"

git remote rm upstream

echo "Add"

git add .

echo "Commit"

git commit -am "Pull aws_template changes"

echo "Push"

git push -fu origin master

