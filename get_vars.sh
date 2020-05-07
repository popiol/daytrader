#!/bin/bash

export APP_VER=$CI_COMMIT_BRANCH

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

