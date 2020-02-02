#!/bin/bash

if [ -z $1 ]; then
	echo "Missing branch name"
	exit 1
fi

branch_name=$1
branch_name=`echo $branch_name | sed "s/origin\///"`

echo "Checkout $branch_name"

git checkout deleted/$branch_name

if [ $? -gt 0 ]; then
	res=1
	if [[ $branch_name == */* ]]; then
		branch_name=`echo $branch_name | sed "s/^.*\///"`
		echo "Checkout $branch_name"
		git checkout deleted/$branch_name
		res=$?
	fi
	if [ $res -gt 0 ]; then
		branch_name="dev/$branch_name"
		echo "Checkout $branch_name"
		git checkout deleted/$branch_name
	fi
fi

if [ $? -gt 0 ]; then
	echo "Incorrect branch name"
	exit 1
fi

echo "Rename"

git branch -m $branch_name

echo "Undelete remote branch"

git push origin :deleted/$branch_name $branch_name

echo "Push"

git push origin -u $branch_name


