#!/bin/bash

just_clean="0"

if [ -z $1 ]; then
	just_clean="1"
fi

if [[ "$just_clean" != "1" && "$1" == *master ]]; then
	echo "You cannot delete master branch"
	exit 1
fi

if [ "$just_clean" != "1" ]; then

branch_name=$1
branch_name=`echo $branch_name | sed "s/origin\///"`

echo "Add & commit"

git add .
git commit -am "Auto-commit `date '+%Y-%m-%d %H:%M:%S'`"

echo "Checkout $branch_name"

git checkout $branch_name

if [ $? -gt 0 ]; then
	res=1
	if [[ $branch_name == */* ]]; then
		branch_name=`echo $branch_name | sed "s/^.*\///"`
		echo "Checkout $branch_name"
		git checkout $branch_name
		res=$?
	fi
	if [ $res -gt 0 ]; then
		branch_name="dev/$branch_name"
		echo "Checkout $branch_name"
		git checkout $branch_name
	fi
fi

if [ $? -gt 0 ]; then
	echo "Incorrect branch name"
	exit 1
fi

echo "Rename"

git branch -m deleted/$branch_name

echo "Delete remote branch"

git push origin :$branch_name deleted/$branch_name

echo "Push"

git push origin -u deleted/$branch_name

fi

git branch -r | grep origin/deleted | sed 's/origin\///' | while read del_branch
do
	git checkout $del_branch
	delete_dt=`git show | grep Date | head -n 1 | sed 's/Date:   \| [^ ]*$//g' | sed 's/^\|$/"/g' | xargs date '+%s' -d`
	ref_dt=`date '+%s' -d 'now - 1 month'`
	if [ "$delete_dt" -le "$ref_dt" ]; then
		echo "Remove $del_branch"
		git checkout master
		git branch -d $del_branch
		git push origin --delete $del_branch
	else
		echo "Do not delete $del_branch: $(( (delete_dt - ref_dt)/86400 )) days left"
	fi
done

