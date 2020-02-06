#!/bin/bash

current_branch=`git branch | grep '*' | cut -d ' ' -f 2`

echo "Add & commit"

git add .
git commit -am "Auto commit `date '+%Y-%m-%d %H:%M:%S'`"

git branch -r | grep -v HEAD | grep -v /deleted/ | sed "s/^[^o]*origin\///" | while read branch_name
do
	echo "Checkout $branch_name"

	git checkout $branch_name

	echo "Pull"

	git pull

	echo "Git push"

	git push
done

echo "Back to $current_branch"

git checkout $current_branch

