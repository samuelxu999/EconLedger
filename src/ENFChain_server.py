'''
========================
ENFChain_server module
========================
Created on Dec.10, 2020
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide encapsulation of server API that handle and response client's request.
                  This can be used as microchain validator server.
'''
import sys
import time
import datetime
import json
import threading
import logging
from flask import Flask, jsonify
from flask import abort,make_response,request
from argparse import ArgumentParser

from network.nodes import *
from network.wallet import Wallet
from network.p2p import Kademlia_Server
from utils.utilities import FileUtil, TypesUtil, DatetimeUtil
from consensus.transaction import Transaction
from consensus.block import Block
from consensus.validator import Validator
from consensus.consensus import POE
from utils.service_api import SrvAPI
from randomness.randshare import RandShare, RandOP
from utils.ENFchain_RPC import swarm_utils

logger = logging.getLogger(__name__)

def build_tx(tx_json):
	'''
	Build a transaction that encapsulate a json style value
	'''
	## use validator's account
	sender = myblockchain.wallet.accounts[0]

	## input head information of a tx
	sender_address = sender['address']
	sender_private_key = sender['private_key']
	recipient_address = sender['address']

	## get time stamp
	time_stamp = time.time()

	## covert tx_json to string format
	tx_str = TypesUtil.json_to_string(tx_json)

	## construct a tx object
	mytransaction = Transaction(sender_address, sender_private_key, recipient_address, time_stamp, tx_str)

	## convert tx object to json format
	transaction_json = mytransaction.to_json()

	## sign transaction and  add signature 
	sign_data = mytransaction.sign('samuelxu999')
	transaction_json['signature']=TypesUtil.string_to_hex(sign_data)

	return transaction_json

# ================================= Instantiate the server =====================================
app = Flask(__name__)
#CORS(app)

#===================================== Validator RPC handler ===================================
@app.route('/test/consensus/run', methods=['POST'])
def consensus_run():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	json_data=json.loads(req_data)

	if(json_data=='{}'):
		abort(401, {'error': 'No node data'})

	myblockchain.runConsensus = json_data['consensus_run']

	return jsonify({'consensus_run': myblockchain.runConsensus}), 201


@app.route('/test/validator/getinfo', methods=['GET'])
def validator_info():
	response = myblockchain.get_info()
	return jsonify(response), 200

@app.route('/test/validator/status', methods=['GET'])
def validator_status():
	response = myblockchain.get_status()
	return jsonify(response), 200

# ================================ Transaction RPC handler==================================
@app.route('/test/transaction/query', methods=['GET'])
def query_transaction():
	## parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)

	tx_hash=json.loads(req_data)

	response = myblockchain.query_tx(tx_hash)

	return jsonify(response), 200

@app.route('/test/transaction/submit', methods=['POST'])
def submit_transaction():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)

	tx_json=json.loads(req_data)
	
	if(tx_json=='{}'):
		abort(401, {'error': 'No transaction data'})

	respose_json = {}

	## build transaction data
	transaction_json=build_tx(tx_json)

	## broadcast transaction to peer nodes
	SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), 
						transaction_json, '/test/transaction/verify')

	## return tx hash	
	return jsonify({'submit_transaction': transaction_json['hash']}), 201

@app.route('/test/enf_proof/submit', methods=['GET'])
def submit_enf_proof():
	start_time=time.time()

	## ------------ build enf_tx -------------------
	sender = myblockchain.wallet.accounts[0]
	sender_address = sender['address']
	sender_private_key = sender['private_key']
	## set recipient_address as default value: 0
	recipient_address = '0'
	time_stamp = time.time()

	## value comes from hash value to indicate address that ENF samples are saved on swarm network.
	json_value={}
	json_value['sender_address'] = sender_address
	json_value['swarm_hash'] = swarm_utils.recordENF(sender_address)
	## convert json_value to string to ensure consistency in tx verification.
	str_value = TypesUtil.json_to_string(json_value)

	mytransaction = Transaction(sender_address, sender_private_key, recipient_address, time_stamp, str_value)

	## sign transaction
	sign_data = mytransaction.sign('samuelxu999')

	## --------------------- send transaction --------------------------------------
	transaction_json = mytransaction.to_json()
	transaction_json['signature']=TypesUtil.string_to_hex(sign_data)

	## broadcast tx to peers
	SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), transaction_json, '/test/transaction/verify')
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_submit_tx.log', format(exec_time*1000, '.3f'))
	
	return jsonify({'submit_enf_proof': 'Succeed!'}), 201

#GET req
@app.route('/test/transaction/verify', methods=['POST'])
def verify_transaction():
	## 1) parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)

	## 2) load req_data to transaction_json(json) 
	transaction_json=json.loads(req_data)

	## 3) check if transaction_json is empty.	
	if(transaction_json=='{}'):
		abort(401, {'error': 'No transaction data'})

	## 4) calculate tx verify time.
	start_time=time.time()
	verify_data = myblockchain.on_receive(transaction_json, 0)
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_verify_tx.log', format(exec_time*1000, '.3f'))

	# if(verify_data==True):
	# 	## 5) forward unseen tx to peer nodes.
	# 	SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), transaction_json, '/test/transaction/verify')
	
	return jsonify({'verify_transaction': verify_data}), 201

#GET req
@app.route('/test/transaction/broadcast', methods=['POST'])
def broadcast_transaction():
	## 1) parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)

	## 2) load req_data to transaction_json(json)
	transaction_json=json.loads(req_data)

	## 3) check if transaction_json is empty.
	if(transaction_json=='{}'):
		abort(401, {'error': 'No transaction data'})

	## 4) broadcast transaction_json to peer nodes
	start_time=time.time()
	SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), transaction_json, '/test/transaction/verify')
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_broadcast_tx.log', format(exec_time*1000, '.3f'))

	return jsonify({'broadcast_transaction': 'Succeed!'}), 201

@app.route('/test/transactions/get', methods=['GET'])
def get_transactions():
    # Get transactions from transactions pool
    transactions = myblockchain.transactions

    response = {'transactions': transactions}
    return jsonify(response), 200

@app.route('/test/enf_proofs/get', methods=['GET'])
def get_enf_proofs():
    # Get enf_proofs from local pool
    enf_proofs = myblockchain.enf_proofs

    response = {'enf_proofs': enf_proofs}
    return jsonify(response), 200

@app.route('/test/chain/get', methods=['GET'])
def full_chain():
	json_blocks = myblockchain.load_chain()
	response = {
	    'chain': json_blocks,
	    'length': len(json_blocks),
	}
	return jsonify(response), 200

## ================================ Mining RPC handler==================================
@app.route('/test/chain/checkhead', methods=['GET'])
def check_head():
	myblockchain.fix_processed_head()

	return jsonify({'Reorganize processed_head': myblockchain.processed_head}), 200

@app.route('/test/mining', methods=['GET'])
def mine_block():
	start_time=time.time()
	new_block=myblockchain.mine_block()
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_mining.log', format(exec_time*1000, '.3f'))
	
	#broadcast proposed block
	if( (not Block.isEmptyBlock(new_block)) ):
		#broadcast new block to peer nodes
		#myblockchain.peer_nodes.load_ByAddress()
		SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), new_block, '/test/block/verify')

		response = {
			'message': "New Block Forged",
			'sender_address': new_block['sender_address'],
			'signature': new_block['signature'],
			'hash': new_block['hash'],
			'height': new_block['height'],
			'nonce': new_block['nonce'],
			'previous_hash': new_block['previous_hash'],
		}
	else:
		response = { 'message': "Empty Block Forged, not broadcast."}		
	
	return jsonify(response), 200

## ================================ Node RPC handler==================================
@app.route('/test/p2p/neighbors', methods=['GET'])
def p2p_neighbors():
	neighbors = my_p2p.get_neighbors()
	response = {'neighbors': neighbors}
	return jsonify(response), 200

@app.route('/test/p2p/peers', methods=['GET'])
def p2p_peers():
	peers = my_p2p.get_peers()
	response = {'peers': peers}
	return jsonify(response), 200

@app.route('/test/account/info', methods=['GET'])
def account_info():
	base_account = myblockchain.wallet.accounts[0]
	json_info = {}
	json_info['address'] = base_account['address']
	json_info['public_key'] = base_account['public_key']
	response = {'info': json_info}
	return jsonify(response), 200

@app.route('/test/nodes/get', methods=['GET'])
def get_nodes():
	myblockchain.peer_nodes.load_ByAddress()
	nodes = myblockchain.peer_nodes.nodes
	response = {'nodes': nodes}
	return jsonify(response), 200

@app.route('/test/nodes/add', methods=['POST'])
def add_node():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	json_node=json.loads(req_data)

	if(json_node=='{}'):
		abort(401, {'error': 'No node data'})

	myblockchain.peer_nodes.register_node(json_node['address'], json_node['public_key'], json_node['node_url'])
	myblockchain.peer_nodes.load_ByAddress()
	myrandshare.peer_nodes.load_ByAddress()
	return jsonify({'add peer node': json_node['address']}), 201

@app.route('/test/nodes/remove', methods=['POST'])
def remove_node():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	json_node=json.loads(req_data)
	
	if(json_node=='{}'):
		abort(401, {'error': 'No node data'})
		
	myblockchain.peer_nodes.remove_node(json_node['address'])
	myblockchain.peer_nodes.load_ByAddress()
	myrandshare.peer_nodes.load_ByAddress()
	return jsonify({'remove peer node': json_node['address']}), 201

## ================================ Block RPC handler==================================
@app.route('/test/block/query', methods=['GET'])
def query_block():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)

	block_hash=json.loads(req_data)

	response = myblockchain.query_block(block_hash)

	return jsonify(response), 200

@app.route('/test/block/verify', methods=['POST'])
def verify_block():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	block_data=json.loads(req_data)
	
	if(block_data=='{}'):
		abort(401, {'error': 'No block data'})

	start_time=time.time()
	verify_result = myblockchain.on_receive(block_data, 1)
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_verify_block.log', format(exec_time*1000, '.3f'))

	return jsonify({'verify_block': verify_result}), 201

## ================================ Vote RPC handler==================================
@app.route('/test/block/vote', methods=['GET'])
def vote_block():
	json_block = myblockchain.processed_head

	ret_msg = "Not valid for voting epoch"
	# if( (json_block['height'] % EPOCH_SIZE) == 0):
	if( (json_block['height'] % myblockchain.block_epoch) == 0):
		vote_data = myblockchain.vote_checkpoint(json_block)	
		SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), vote_data, '/test/vote/verify')
		ret_msg = vote_data

	return jsonify({'Vote block': ret_msg}), 201

@app.route('/test/vote/verify', methods=['POST'])
def verify_vote():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	vote_data=json.loads(req_data)
	
	if(vote_data=='{}'):
		abort(401, {'error': 'No vote data'})

	start_time=time.time()
	verify_result = myblockchain.on_receive(vote_data, 2)
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_verify_vote.log', format(exec_time*1000, '.3f'))

	# print('verify_vote:', verify_result)

	return jsonify({'verify_vote': verify_result}), 201

#GET req
@app.route('/test/vote/broadcast', methods=['POST'])
def broadcast_vote():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	vote_data=json.loads(req_data)

	if(vote_data=='{}'):
		abort(401, {'error': 'No vote data'})

	# broadcast transaction to peer nodes
	#myblockchain.peer_nodes.load_ByAddress()
	SrvAPI.broadcast_POST(myblockchain.peer_nodes.get_nodelist(), vote_data, '/test/vote/verify')

	return jsonify({'broadcast_vote': 'Succeed!'}), 201

# ====================================== Random share RPC handler==================================
@app.route('/test/randshare/create', methods=['GET'])
def create_randshare():

	start_time=time.time()
	# create new shares
	json_shares=myrandshare.create_shares()
	# save new shares into local file
	RandShare.save_sharesInfo(json_shares)
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_create_shares.log', format(exec_time*1000, '.3f'))

	return jsonify({'create_randshare': 'Succeed!'}), 201

# request for share from peers
@app.route('/test/randshare/fetch', methods=['POST'])
def fetch_randshare():
	# parse data from request.data
	req_data=TypesUtil.bytes_to_string(request.data)
	json_node=json.loads(req_data)

	if(json_node=='{}'):
		abort(401, {'error': 'No node data'})

	response = myrandshare.fetch_randomshares(json_node)
	return jsonify(response), 200

# request for share from peers and cache to local
@app.route('/test/randshare/cachefetched', methods=['GET'])
def cachefetched_randshare():
	myrandshare.set_cmd(1)
	return jsonify({'cachefetched_randshare': 'Succeed!'}), 200

# verify share and proof 
@app.route('/test/randshare/verify', methods=['GET'])
def verify_randshare():
	start_time=time.time()
	myrandshare.verify_randomshare()
	exec_time=time.time()-start_time
	FileUtil.save_testlog('test_results', 'exec_verify_shares.log', format(exec_time*1000, '.3f'))
	return jsonify({'verify_randshare': 'Succeed!'}), 200

@app.route('/test/randshare/recovered', methods=['GET'])
def recovered_randshare():
	response = myrandshare.recovered_randomshare()
	return jsonify(response), 200

# request for vote shares from peers
@app.route('/test/randshare/fetchvote', methods=['GET'])
def fetch_vote_randshare():
	response = myrandshare.fetch_vote_randonshare()
	return jsonify(response), 200

# retrive vote shares from peers and locally cache for verify vote 
@app.route('/test/randshare/cachevote', methods=['GET'])
def cache_vote_randshare():
	myrandshare.set_cmd(2)
	return jsonify({'vote_randshare': 'Succeed!'}), 200

def disp_randomshare(json_shares):
	''' randshare function'''	
	logger.info("poly_secrets:")
	poly_secrets = json_shares['poly_secrets']
	if poly_secrets:
	    for poly_secret in poly_secrets:
	        logger.info('    {}'.format(poly_secret))

	logger.info("node_shares:")
	node_shares = json_shares['node_shares']
	nodes = myrandshare.peer_nodes.get_nodelist()
	if node_shares:
		shares=[]
		for node in nodes:
			json_node = TypesUtil.string_to_json(node)
			shares.append(node_shares[json_node['address']])
			logger.info('    {}: {}'.format(json_node['address'], node_shares[json_node['address']]))
	
	# get poly_commits
	poly_commits = myrandshare.poly_commits(poly_secrets)
	logger.info("poly_commitments:")
	if poly_commits:
		for poly_commit in poly_commits:
			logger.info('    {}'.format(poly_commit))

	# get share_proofs
	share_proofs = myrandshare.share_proofs(shares)
	logger.info("share_proofs:")
	share_proofs.sort(key=lambda tup: tup[0])
	if share_proofs:
		for share_proof in share_proofs:
			logger.info('    {}'.format(share_proof))

## ================================ Private functions ==================================
def new_account():
	## Instantiate the Wallet
	mywallet = Wallet()

	## load accounts
	mywallet.load_accounts()

	## new account
	mywallet.create_account('samuelxu999')

	if(len(mywallet.accounts)!=0):
		account = mywallet.accounts[0]
		print(TypesUtil.hex_to_string(account['public_key']))
		print(len(account['address']))

	#list account address
	print(mywallet.list_address())

def static_node():
	## add static node from json.
	static_nodes = StaticNodes()
	static_nodes.load_node()

	## load test node information from local 'static-nodes.json'
	json_nodes = FileUtil.JSON_load('static-nodes.json')

	## case 2) add all nodes
	for (node_name, node_data) in json_nodes.items():
		# print("Name: " + node_name)
		# print("Data: " + str(node_data))
		if( node_data !={}):
			static_nodes.register_node(node_name, node_data['address'], node_data['ip'])

	## save node test
	static_nodes.save_node()

	# reload static_nodes buffer for print
	reload_nodes = static_nodes.nodes
	#print(reload_nodes)

	print('List loaded static nodes:')
	for node in list(reload_nodes):
	    #json_node = TypesUtil.string_to_json(node)
	    json_node = node
	    print(json_node['node_name'] + '    ' + json_node['node_address'] + '    ' + json_node['node_url'])	

def define_and_get_arguments(args=sys.argv[1:]):
	parser = ArgumentParser(description="Run microchain websocket server.")

	parser.add_argument("--test_func", type=int, default=0, 
						help="Execute test function: 0-run_validator, \
													1-new_account(), \
													2-static_node()")

	parser.add_argument('-p', '--port', default=8180, type=int, 
						help="port to listen on.")
	parser.add_argument('-rp', '--rpc_port', default=31180, type=int, 
							help="rpc_port to listen on.")
	parser.add_argument('--blockepoch', default=2, type=int, 
						help="Block proposal round epoch size.")
	parser.add_argument('--pauseepoch', default=2, type=int, 
						help="Checkpoint epoch size for pending consensus and synchronization.")
	parser.add_argument('--phasedelay', default=3, type=int, 
						help="Delay time between operations of consensus protocol.")
	parser.add_argument("--debug", action="store_true", 
						help="if set, debug model will be used.")
	parser.add_argument("--threaded", action="store_true", 
						help="if set, support threading request.")
	parser.add_argument("--firstnode", action="store_true", 
						help="if set, bootstrap as first node of network.")
	parser.add_argument("--bootstrapnode", default='128.226.88.210:31180', type=str, 
						help="bootstrap node address format[ip:port] to join the network.")
	parser.add_argument('--save_state', default=600, type=int, 
							help="frequency for save_state_regularly.")
	parser.add_argument('--refresh_neighbors', default=600, type=int, 
							help="frequency for refresh_neighbors_regularly.")
	args = parser.parse_args()

	return args

if __name__ == '__main__':
	# FORMAT = "%(asctime)s %(levelname)s %(filename)s(l:%(lineno)d) - %(message)s"
	FORMAT = "%(asctime)s %(levelname)s | %(message)s"
	LOG_LEVEL = logging.INFO
	logging.basicConfig(format=FORMAT, level=LOG_LEVEL)

	# get arguments
	args = define_and_get_arguments()

	## if debug mode, show debug information.
	if(args.debug):
		kademlia_logger = logging.getLogger("kademlia")
		kademlia_logger.setLevel(logging.DEBUG)
		p2p_logger = logging.getLogger("p2p")
		p2p_logger.setLevel(logging.DEBUG)
		# randshare_logger = logging.getLogger("randshare")
		# randshare_logger.setLevel(logging.DEBUG)

	if(args.test_func==1):
		new_account()
	elif(args.test_func==2):
		static_node()
	else:
		## ---------------------- Instantiate the Wallet ---------------------------
		mywallet = Wallet()

		## load accounts
		mywallet.load_accounts()

		if(len(mywallet.accounts)==0): 
			mywallet.create_account('samuelxu999')

		## ------------------------ Instantiate the Validator ----------------------------------
		myblockchain = Validator(port=args.port, 
								bootstrapnode=args.bootstrapnode,
								block_epoch=args.blockepoch,
								pause_epoch=args.pauseepoch,
								phase_delay=args.phasedelay,
								frequency_peers=args.refresh_neighbors)

		myblockchain.print_config()

		## -------------------------- Instantiate RandShare -------------------------------------
		myrandshare = RandShare()
		# json_sharesInfo=RandShare.load_sharesInfo()
		# # display random shares
		# disp_randomshare(json_sharesInfo)

		## ------------------------ Instantiate p2p server as thread ------------------------------
		base_account = myblockchain.wallet.accounts[0]
		my_p2p = Kademlia_Server(rpc_port=args.rpc_port, bootstrapnode=args.bootstrapnode,
								freq_loop=[args.save_state, args.refresh_neighbors], 
								node_id=base_account['address'], ksize=20, alpha=3)
		
		## bind my_p2p.run() to a thread.daemon
		p2p_thread = threading.Thread(target=my_p2p.run, args=(args.firstnode,))
		p2p_thread.daemon = True		
		p2p_thread.start()

		## -------------------------------- run app server ----------------------------------------
		app.run(host='0.0.0.0', port=args.port, debug=args.debug, threaded=args.threaded)

