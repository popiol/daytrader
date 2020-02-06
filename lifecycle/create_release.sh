#!/bin/bash

branch_name=release

echo "Add & commit"

git add .
git commit -am 'Auto commit `date "+%Y-%m-%d %H:%M:%S"`'

echo "Checkout master"

git checkout master

echo "Pull"

git pull

echo "Checkout new branch"

git checkout -b $branch_name master

echo "Push"

git push -u origin $branch_name

