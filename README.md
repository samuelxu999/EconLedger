# EconLedger
Econledger project for development, deployment and evaluation.

The article "EconLedger: A Proof-of-ENF Consensus Based Lightweight Distributed Ledger for IoVT Networks" provide design ideas. Please refer to MDPI-Future Internet 2021, 13(10), 248; [https://doi.org/10.3390/fi13100248](https://doi.org/10.3390/fi13100248).

The overview of project organization are:

## src
The econledger prototype impelmentation by using python, which includs:

|   source   | Description |
|:----------:|-------------|
| consensus | transaction and block data structure and consensus algorithms |
| cryptolib | cryptography basis, like RAS, PVSS and VRF.|
| data | Sample ENF data for development and demo. |
| kademlia | a structured p2p protocol for node discovery. |
| network | identity (account and node) management and p2p wrapper of kademlia. |
| randomness | Epoch randomness protocol for committee election |
| rpcudp | provide udp handlers for rpc interfaces. |
| utils | utilities code to support functionality, like ledger database engine, service api and swarm interfaces, etc. |
| ENFChain_server.py | launch a flask server to run econledger node  |
| Test_client.py | provide test functions for client apps to interact with econledger node. |

## DOCKER
The econLedger docker image build and container deployment.

## config
The configuration files:

|   source   | Description |
|:----------:|-------------|
| static-nodes.json | static nodes for development and test. |
| swarm_server.json | swarm nodes of a private DDB netowrk used by Econledger. |

For swarm nodes deployment, please refer to: [swarm docker](https://github.com/samuelxu999/Blockchain_dev/tree/master/Swarm/DOCKER)


## config
The scripts for development and test:

|   source   | Description |
|:----------:|-------------|
| reset_all.sh | used for scalable test on distributed network, like update code and reset status of econledger nodes. |
| setup_localtest.sh | used for local test for development. |
| ssh_remote_expect.sh | work as underlying engine for reset_all.sh that remotely executes commands on distributed machine. |

## requirements.txt
List dependencies and required libs.