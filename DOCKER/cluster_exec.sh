#!/bin/bash

## ============= Run cluster by launching multiple containerized econledger nodes given args ==============
OPERATION=$1

## Start cluster
if  [ "start" == "$OPERATION" ] ; then
	echo "Start a bootstrap node"
	./service_run.sh start econledger-bootstrap x86 31180 8180
	sleep 5

	echo "Start four validators"
	./service_run.sh start econledger-node1 x86 31181 8181 0.0.0.0:31180
	./service_run.sh start econledger-node2 x86 31182 8182 0.0.0.0:31180
	./service_run.sh start econledger-node3 x86 31183 8183 0.0.0.0:31180
	./service_run.sh start econledger-node4 x86 31184 8184 0.0.0.0:31180

## Stop cluster
elif [ "stop" == "$OPERATION" ] ; then
	echo "Stop cluster"
	./docker_exec.sh econledger-bootstrap docker "rm -rf nodedata"
	./service_run.sh stop econledger-bootstrap
	./service_run.sh stop econledger-node1
	./service_run.sh stop econledger-node2
	./service_run.sh stop econledger-node3
	./service_run.sh stop econledger-node4

## Remove volumes
elif [ "remove" == "$OPERATION" ] ; then
	echo "Remove volumes"
	docker volume rm econledger-bootstrap
	docker volume rm econledger-node1
	docker volume rm econledger-node2
	docker volume rm econledger-node3
	docker volume rm econledger-node4

## show cluster
elif [ "show" == "$OPERATION" ] ; then
	echo "Show cluster"
	./service_run.sh show | grep econledger-

## Show usage
else
	echo "Usage $0 -operation(start|stop|show)"
fi