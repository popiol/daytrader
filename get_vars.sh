#!/bin/bash

if [ -z "$1" ]; then
	export APP_VER=$CI_COMMIT_BRANCH
elif [ "$1" != "source" ]; then
	echo "Invalid parameter: $1"
	echo "Usage: $(basename -- $0) [source]"
	exit 1
else
	export APP_VER=$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME
fi

if [[ "$APP_VER" == "master" || "$APP_VER" == "$CI_DEFAULT_BRANCH" ]]; then
	export TEMP_DEPLOY="false"
else
	export TEMP_DEPLOY="true"
fi

envsubst < config.tfvars > config.tfvars.new
mv config.tfvars.new config.tfvars

envsubst < main.tf > main.tf.new
mv main.tf.new main.tf

cd lambda
dirs=`ls -d1 */ | sed "s/\/$//" | tr '\n' ' '`
for dir in $dirs
do
	cd $dir
	zip -r ../$dir.zip .
	cd ..
done
cd ..

