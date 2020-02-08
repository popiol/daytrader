#!/bin/bash

versions="master"
for i in "$@"
do
	i=`basename $i`
	versions=${versions} $i
done

echo "Versions to skip: $versions"

repo_name=`git remote -v | head -n 1 | sed 's/^.*\/\| [^ ]*$//g'`
repo_name="${repo_name%.*}"
app=$repo_name
#app_id="${repo_name}_${app_ver}"

echo "App: $app"

nremoved=1
nitems_prev=0

while [ $nremoved -gt 0 ]
do

aws_ids=`aws resourcegroupstaggingapi get-resources --tag-filters Key=App,Values=$app --output text | grep "RESOURCETAGMAPPINGLIST\|AppVer" | sed -z "s/\nTAGS//g"`
role_ids=`aws iam list-roles --path-prefix /$app/ --output text | grep ROLES`

for ver in $versions
do
	aws_ids=`echo "$aws_ids" | grep -v $'AppVer\t$ver'`
	role_ids=`echo "$role_ids" | grep -v '/$app/$ver/'`
done

aws_ids=`echo "$aws_ids" | cut -d$'\t' -f 2 | rev | cut -d ':' -f 1 | rev | tr "\n" " " | sed "s/ $//"`
role_ids=`echo "$role_ids" | rev | cut -d$'\t' -f 1 | rev | tr "\n" " " | sed "s/ $//"`

echo ""
echo "AWS ID's: $aws_ids"
echo "Role ID's: $role_ids"
echo ""

nitems=0
nremoved=0

for id in $aws_ids
do
	nitems=$((nitems+1))
	type=`echo $id | cut -d '/' -f 1`
	id=`echo $id | cut -d '/' -f 2`
	echo aws ec2 delete-$type --$type-id $id
	aws ec2 delete-$type --$type-id $id
	if [ $? -eq 0 ]; then
		nremoved=$((nremoved+1))
	fi
done

for id in $role_ids
do
	nitems=$((nitems+1))
	policies=`aws iam list-attached-role-policies --role-name $id --output text | grep ATTACHEDPOLICIES | cut -d$'\t' -f 2 | tr '\n' ' '`
	for policy in $policies
	do
		echo aws iam detach-role-policy --role-name $id --policy-arn $policy
		aws iam detach-role-policy --role-name $id --policy-arn $policy
	done
	echo aws iam delete-role --role-name $id
	aws iam delete-role --role-name $id
	if [ $? -eq 0 ]; then
		nremoved=$((nremoved+1))
	fi
done

if [ $nitems_prev -gt 0 ]; then
	nremoved=$((nitems_prev-nitems))
fi
nitems_prev=$nitems

echo ""
echo "Items to removed: $nitems"
echo "Items removed: $nremoved"
echo ""

done

