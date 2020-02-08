#!/bin/bash

if [ -z "$1" ]; then
	echo "Missing argument"
	echo "Usage: $(basename -- $0) <branch_name>"
	exit 1
fi

branch_name=$1
branch_name=`echo $branch_name | sed "s/origin\///"`

echo "Add & commit"

git add .
git commit -am "Auto commit `date '+%Y-%m-%d %H:%M:%S'`"

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

echo \
"app_id=\"$app_id\"
app=\"$app\"
app_ver=\"$app_ver\"
app_stage=\"$stage\"
" > config.ini

echo "Pull"

git pull

echo "Add tags to terraform"

cd terraform

python ../lifecycle/add_tags.py

echo "Zip lambda functions"

cd lambda
funcs=`ls -d1 */ | sed "s/\/$//" | tr '\n' ' '`

for func in $funcs
do
	cd $func
	zip -r ../$func.zip .
	cd ..
done

cd ..

echo "Init terraform"

rm terraform.tfstate*
terraform init

echo "Import from AWS to terraform"

aws_ids=`aws resourcegroupstaggingapi get-resources --tag-filters Key=App,Values=$app,Key=AppVer,Values=$app_ver --output text | grep RESOURCETAGMAPPINGLIST | cut -d$'\t' -f 2 | rev | cut -d '/' -f 1 | cut -d ':' -f 1 | rev | tr "\n" "|" | sed "s/^|//"`

terr_ids=`aws resourcegroupstaggingapi get-resources --tag-filters Key=App,Values=$app,Key=AppVer,Values=$app_ver --output text | grep TerraformID | rev | cut -d$'\t' -f 1 | rev | tr "\n" "|" | sed "s/|$//"`

role_ids=`aws iam list-roles --path-prefix /$app/$app_ver/ --output text | grep ROLES | rev | cut -d$'\t' -f 1 | rev | tr '\n' ' '`
role_terr_ids=''
for role_id in $role_ids
do
	terr_id=`aws iam list-role-tags --role-name $role_id | sed -z "s/\",\n/\", /g" | grep TerraformID | rev | cut -d ':' -f 1 | rev | cut -d '"' -f 2`
	role_terr_ids="$role_terr_ids|$terr_id"
done

rule_ids=`aws resourcegroupstaggingapi get-resources --tag-filters Key=App,Values=$app,Key=AppVer,Values=$app_ver --output text | grep RESOURCETAGMAPPINGLIST | grep ":rule/" | cut -d$'\t' -f 2 | rev | cut -d '/' -f 1 | cut -d ':' -f 1 | rev | tr "\n" " "`
target_ids=''
target_terr_ids=''
for rule_id in $rule_ids
do
	target_ids="$target_ids|$rule_id/$rule_id"
	terr_id=`echo $rule_id | sed "s/^${app_id}_//"`
	target_terr_ids="$target_terr_ids|aws_cloudwatch_event_target.$terr_id"
done

echo "Target ID's: $target_ids"
echo "Target terraform ID's: $target_terr_ids"

role_ids=`echo $role_ids | tr "\n" "|" | sed "s/|$//"`
aws_ids="${aws_ids}${role_ids}"
terr_ids=`echo "${terr_ids}${role_terr_ids}" | sed "s/^|\||$//g"`
aws_ids="${aws_ids}${target_ids}"
terr_ids="${terr_ids}${target_terr_ids}"

echo "AWS ID's: $aws_ids"
echo "Terraform ID's: $terr_ids"

python ../lifecycle/import_resources.py "$aws_ids" "$terr_ids"

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

