#!/bin/bash

if [ -z "$1" ]; then
	echo "Missing argument"
	echo "Usage: $(basename -- $0) <branch_name>"
	exit 1
fi

branch_name=$1
branch_name=`echo $branch_name | sed "s/origin\///"`

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

echo "Calc params"

app_ver="$(basename -- $branch_name)"
stage="$(basename -- $(dirname $branch_name))"

if [ "$app_ver" = "master" ]; then
	stage="prod"
fi

if [ "$app_ver" = "release" ]; then
	stage="test"
fi

if [ -z "$stage" ]; then
	stage="dev"
fi

repo_name=`git remote -v | head -n 1 | sed 's/^.*\/\| [^ ]*$//g'`
repo_name="${repo_name%.*}"
app=$repo_name
app_id="${repo_name}_${app_ver}"

echo "Stage: $stage"
echo "App ver: $app_ver"
echo "App: $app"
echo "App ID: $app_id"

echo "/
aws_id=\"$aws_id\"
app=\"$app\"
app_ver=\"$app_ver\"
app_stage=\"$stage\"
" > config.ini

echo "Pull"

git pull

echo "Add tags to terraform"

cd terraform

python ../lifecycle/add_tags.py

echo "Import from AWS to terraform"

aws_ids=`aws resourcegroupstaggingapi get-resources --tag-filters Key=App,Values=$app,Key=AppVer,Values=$app_ver --output text | grep RESOURCETAGMAPPINGLIST | cut -d$'\t' -f 2 | rev | cut -d '/' -f 1 | cut -d ':' -f 1 | rev | tr "\n" "|"`

terr_ids=`aws resourcegroupstaggingapi get-resources --tag-filters Key=App,Values=$app,Key=AppVer,Values=$app_ver --output text | grep TerraformID | rev | cut -d$'\t' -f 1 | rev | tr "\n" "|"`

echo "AWS ID's: $aws_ids"
echo "Terraform ID's: $terr_ids"

python ../lifecycle/import_resources.py $aws_ids $terr_ids

if [ $? -gt 0 ]; then
	exit 1
fi

echo "Apply Terraform"

terraform apply -var-file="../config.ini" -auto-approve

echo "Git add"

cd ..

git add .

echo "Git commit"

git commit -am 'Terraform auto tagging'

echo "Git push"

git push

