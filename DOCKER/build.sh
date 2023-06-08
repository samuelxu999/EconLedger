#!/bin/bash

## read from arguments
OPERATION=$1
IMAGE_NAME=$2

## local variable
src_folder="../src"
app_folder="./app"
config_folder="../config"

## ------------------- pre-preparation ----------
## new app folders to save temp files from src
if [ ! -d "$app_folder" ]
then
	mkdir $app_folder
fi
## copy server and client code to localtest folder
cp $src_folder/ENFChain_server.py $app_folder/
cp $src_folder/Test_client.py $app_folder/

## copy libs to localtest folder
cp -r $src_folder/cryptolib $app_folder/
cp -r $src_folder/network $app_folder/
cp -r $src_folder/consensus $app_folder/
cp -r $src_folder/randomness $app_folder/
cp -r $src_folder/utils $app_folder/
cp -r $src_folder/kademlia $app_folder/
cp -r $src_folder/rpcudp $app_folder/

## copy swarm_server.json 
cp $config_folder/swarm_server.json $app_folder/

# ## copy data
# cp -r $src_folder/data $app_folder/

## copy requirements.txt 
cp ../requirements.txt ./

## ------------------- execute docker build ----------
## Check image name
if [[ "" == $2 ]]; then
	IMAGE_NAME="ecoledger_node"
	#echo "Use default image $IMAGE_NAME ...!"
fi

## Liat all image
if [[ "list" == $OPERATION ]]; then
	echo "List image $IMAGE_NAME ...!"
	docker image ls $IMAGE_NAME
	#docker image ls

## Make image
elif [[ "make" == $OPERATION ]]; then
	echo "Start make $IMAGE_NAME ...!"
	docker build -t $IMAGE_NAME .

## Clean image given IMAGE_NAME
elif [[ "clean" == $OPERATION ]]; then
	echo "Remove $IMAGE_NAME ...!"
	docker image rm -f $IMAGE_NAME

else
	echo "Usage $0 cmd[list|make|clean|] image_name"
fi

## ------------------- post-preparation ----------
rm -rf $app_folder
rm -rf ./requirements.txt

