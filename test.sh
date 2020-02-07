#!/bin/bash

role_ids=`aws iam list-roles --path-prefix /daytrader/master/ --output text | grep ROLES | rev | cut -d$'\t' -f 1 | rev | tr '\n' ' '` # | sed -z "s/\(^\||\)|/\1/g" | tr '|' '\n'`

echo "Id's: $role_ids"

for role_id in $role_ids
do
	echo "Id: $role_id"
done


