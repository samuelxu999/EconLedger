'''
========================
Test_Client module
========================
Created on Dec.10, 2020
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide encapsulation of client API that access to Web service.
                  Mainly used to test and demo
'''
import argparse
import sys
import time
import logging
import asyncio
import random

from network.wallet import Wallet
from network.nodes import *
from utils.utilities import TypesUtil, FileUtil
from utils.service_api import SrvAPI
from utils.db_adapter import DataManager
from utils.ENFchain_RPC import ENFchain_RPC
from utils.configuration import *
from randomness.randshare import RandShare

logger = logging.getLogger(__name__)

TX_TIMEOUT = 30
# ------------------------ Instantiate the ENFchain_RPC ----------------------------------
ENFchain_client = ENFchain_RPC(keystore="keystore", 
								keystore_net="keystore_net")


# ====================================== validator test ==================================
def Epoch_validator(target_address, txs_count, tx_size, phase_delay=BOUNDED_TIME):
	'''
	This test network latency for one epoch life time:
	'''
	## Define ls_time_exec to save executing time to log
	ls_time_exec=[]

	## S0: send test transactions
	ENFchain_client.launch_txs(txs_count, tx_size)

	time.sleep(phase_delay)

	## S1: commit enf proofs
	start_time=time.time()
	ENFchain_client.start_enf_submit(target_address, True)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	## S2: start mining 
	start_time=time.time()   
	ENFchain_client.start_mining(target_address, True)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	## S3: fix head of epoch 
	start_time=time.time()   
	ENFchain_client.check_head()
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	## S4: voting block to finalize chain
	start_time=time.time() 
	ENFchain_client.start_voting(target_address, True)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	logger.info("txs: {}    mining: {}    fix_head: {}    vote: {}\n".format(ls_time_exec[0],
										ls_time_exec[1], ls_time_exec[2], ls_time_exec[3]))
	## Prepare log messgae
	str_time_exec=" ".join(ls_time_exec)
	## Save to *.log file
	FileUtil.save_testlog('test_results', 'exec_time.log', str_time_exec)

def Epoch_randomshare(target_address, phase_delay=BOUNDED_TIME):
	'''
	This test network latency for one epoch life time:
	'''
	# Define ls_time_exec to save executing time to log
	ls_time_exec=[]

	# get peer node information
	peer_nodes = PeerNodes()
	peer_nodes.load_ByAddress()

	# 1) create shares
	logger.info("1) Create shares")
	start_time=time.time()
	# for peer_node in list(peer_nodes.get_nodelist()):
	# 	json_node = TypesUtil.string_to_json(peer_node)
	# 	ENFchain_client.create_randshare(json_node['node_url'])
	ENFchain_client.create_randshare(target_address, True)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	# 2) fetch shares
	logger.info("2) Fetch shares")
	start_time=time.time()
	# for peer_node in list(peer_nodes.get_nodelist()):
	# 	json_node = TypesUtil.string_to_json(peer_node)
	# 	ENFchain_client.cache_fetch_share(json_node['node_url'])
	ENFchain_client.fetch_randshare(target_address, True)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	# 3) verify received shares
	logger.info("3) Verify received shares")
	start_time=time.time()
	ENFchain_client.verify_randshare(target_address, True)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	# 4) retrive vote shares from peers and verify them. need --threaded
	logger.info("4) Retrive vote shares from peers and verify them")
	start_time=time.time()
	for peer_node in list(peer_nodes.get_nodelist()):
		json_node = TypesUtil.string_to_json(peer_node)
		# cache_vote_shares(json_node['node_url'])
		ENFchain_client.vote_randshare(json_node['node_url'])
	# calculate voted shares 
	verify_vote = RandShare.verify_vote_shares()
	logging.info("verify_vote: {}".format(verify_vote))
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	# 5) retrive shares from peers for secret recover process
	logger.info("5) Retrive shares from peers for secret recovery process")
	start_time=time.time()
	for peer_node in list(peer_nodes.get_nodelist()):
		json_node = TypesUtil.string_to_json(peer_node)
		ENFchain_client.cache_recovered_shares(json_node['node_url'])
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	# 6) recover secret of each peer
	logger.info("6) Recover shared secret of each peer at local")
	ls_secret=[]
	start_time=time.time()
	for peer_node in list(peer_nodes.get_nodelist()):
		json_node = TypesUtil.string_to_json(peer_node)
		ls_secret.append(ENFchain_client.recovered_shares(json_node['address']))
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))

	time.sleep(phase_delay)

	# 7) calculate new random
	logger.info("7) Calculate new random")
	start_time=time.time()
	ENFchain_client.new_random(ls_secret)
	exec_time=time.time()-start_time
	ls_time_exec.append(format(exec_time*1000, '.3f'))
	

	# Prepare log messgae
	str_time_exec=" ".join(ls_time_exec)
	logging.info("{}\n".format(str_time_exec))
	# Save to *.log file
	FileUtil.save_testlog('test_results', 'exec_time_randshare.log', str_time_exec)

def checkpoint_netInfo(target_address, isDisplay=False):
	# get validators information in net.
	validator_info = ENFchain_client.validator_getinfo(target_address, True)

	fininalized_count = {}
	justifized_count = {}
	processed_count = {}

	## -------------  Calculate all checkpoints count -------------------
	for validator in validator_info:
		# Calculate finalized checkpoint count
		if validator['highest_finalized_checkpoint'] not in fininalized_count:
			fininalized_count[validator['highest_finalized_checkpoint']] = 0
		fininalized_count[validator['highest_finalized_checkpoint']] += 1
		
		# Calculate justified checkpoint count
		if validator['highest_justified_checkpoint'] not in justifized_count:
			justifized_count[validator['highest_justified_checkpoint']] = 0
		justifized_count[validator['highest_justified_checkpoint']] += 1

		# Calculate processed checkpoint count
		if validator['processed_head'] not in processed_count:
			processed_count[validator['processed_head']] = 0
		processed_count[validator['processed_head']] += 1

	if(isDisplay):
		logger.info("")
		logger.info("Finalized checkpoints: {}\n".format(fininalized_count))
		logger.info("Justified checkpoints: {}\n".format(justifized_count))
		logger.info("Processed checkpoints: {}\n".format(processed_count))

	## -------------- search finalized checkpoint with maximum count -------------
	checkpoint = ''
	max_acount = 0
	for _item, _value in fininalized_count.items():
		if(_value > max_acount):
			max_acount = _value
			checkpoint = _item	
	finalized_checkpoint = [checkpoint, max_acount]
	if(isDisplay):
		logger.info("Finalized checkpoint: {}    count: {}\n".format(finalized_checkpoint[0],
															   finalized_checkpoint[1]))

	## --------------- search finalized checkpoint with maximum count -------------
	checkpoint = ''
	max_acount = 0
	for _item, _value in justifized_count.items():
		if(_value > max_acount):
			max_acount = _value
			checkpoint = _item	
	justified_checkpoint = [checkpoint, max_acount]
	if(isDisplay):
		logger.info("Justified checkpoint: {}    count: {}\n".format(justified_checkpoint[0],
															   justified_checkpoint[1]))

	## -----------------search finalized checkpoint with maximum count -------------
	checkpoint = ''
	max_acount = 0
	for _item, _value in processed_count.items():
		if(_value > max_acount):
			max_acount = _value
			checkpoint = _item	
	processed_checkpoint = [checkpoint, max_acount]
	if(isDisplay):
		logger.info("Processed checkpoint: {}    count: {}\n".format(processed_checkpoint[0],
															   processed_checkpoint[1]))

	## build json date for return.
	json_checkpoints={}
	json_checkpoints['finalized_checkpoint'] = finalized_checkpoint
	json_checkpoints['justified_checkpoint'] = justified_checkpoint
	json_checkpoints['processed_checkpoint'] = processed_checkpoint

	return json_checkpoints

def disp_chaindata(target_address, isDisplay=False):
	json_response = ENFchain_client.get_chain(target_address)
	chain_data = json_response['chain']
	chain_length = json_response['length']
	logger.info('Chain length: {}'.format(chain_length))

	if( isDisplay ):
		# only list latest 10 blocks
		if(chain_length>10):
			for block in chain_data[-10:]:
				logger.info("{}\n".format(block))
		else:
			for block in chain_data:
				logger.info("{}\n".format(block))

def count_vote_size(target_address):
	# get validators information from a validator.
	validator_info = ENFchain_client.validator_getinfo(target_address, False)[0]
	if(validator_info['vote_count']!={}):
		hf_block = validator_info['highest_finalized_checkpoint']
		voter_db = DataManager(CHAIN_DATA_DIR, VOTER_DATA)
		voter_name = 'voter_' + hf_block['sender_address']
		ls_votes = voter_db.select_block(voter_name)
		if(len(ls_votes)>0):
			vote_str = TypesUtil.json_to_string(ls_votes[0]) 
			logger.info('Vote size: {} Bytes'.format(len( vote_str.encode('utf-8') )))

def validator_getStatus():
	## Instantiate the PeerNodes and load all nodes information
	peer_nodes = PeerNodes()
	peer_nodes.load_ByAddress()
	
	ls_nodes = list(peer_nodes.get_nodelist())
	json_status = SrvAPI.get_statusConsensus(ls_nodes)
	unconditional_nodes = []
	for node in ls_nodes:
		json_node = TypesUtil.string_to_json(node)
		node_status = json_status[json_node['address']]
		if(node_status['consensus_status']!=4):
			unconditional_nodes.append(node)
		logger.info("{}    status: {}".format(json_node['address'], node_status))

	logger.info("Non-syn node: {}".format(unconditional_nodes))

## evaluation on how long to commit tx on ledger.
def commit_tx_evaluate(target_address, tx_thread, tx_size):
	tx_time = 0.0

	# logger.info("launch txs ...\n") 
	# ENFchain_client.launch_txs(tx_thread, tx_size)

	## using random byte string for value of tx; value can be any bytes string.
	json_tx={}
	json_tx['data']=TypesUtil.string_to_hex(os.urandom(tx_size)) 

	## submit tx and get tx_hash
	tx_hash = ENFchain_client.submit_transaction(target_address, json_tx)['submit_transaction']
	commit_block =''

	time.sleep(2)

	logger.info("wait until tx:{} is committed...\n".format(tx_hash))
	start_time=time.time()
	while(True):
		list_tx = ENFchain_client.query_transaction(target_address, tx_hash)

		if(list_tx[0][3]!='0'):
			commit_block = list_tx[0][3]
			break

		time.sleep(0.5)
		tx_time +=0.5
		if(tx_time>=TX_TIMEOUT):
			logger.info("Timeout, tx commit fail.") 
			break

	exec_time=time.time()-start_time
	logger.info("tx is committed in block {}, time: {:.3f}\n".format(commit_block, exec_time, '.3f')) 
	FileUtil.save_testlog('test_results', 'exec_tx_commit.log', format(exec_time, '.3f'))


def define_and_get_arguments(args=sys.argv[1:]):
	parser = argparse.ArgumentParser(
	    description="Run websocket client."
	)
	parser.add_argument("--test_func", type=int, default=2, help="test function: \
															0: set peer nodes \
															1: validator test \
															2: single step test \
															3: randshare test")
	parser.add_argument("--op_status", type=int, default=0, help="test case type.")
	parser.add_argument("--test_round", type=int, default=1, help="test evaluation round")
	parser.add_argument("--samples_head", type=int, default=0, help="Start point of ENF samples data for node.")
	parser.add_argument("--samples_size", type=int, default=60, help="Size of ENF samples list from node.")
	parser.add_argument("--wait_interval", type=int, default=1, help="break time between step.")
	parser.add_argument("--target_address", type=str, default="0.0.0.0:8180", 
						help="Test target address - ip:port.")
	parser.add_argument("--data", type=str, default="", 
						help="Input date for test.")
	parser.add_argument("--tx_thread", type=int, default=1, help="Number of threads for txs.")
	parser.add_argument("--tx_size", type=int, default=128, help="Size of each tx.")
	args = parser.parse_args(args=args)
	return args

if __name__ == "__main__":
	FORMAT = "%(asctime)s %(levelname)s | %(message)s"
	LOG_LEVEL = logging.INFO
	logging.basicConfig(format=FORMAT, level=LOG_LEVEL)

	ENFchain_RPC_logger = logging.getLogger("ENFchain_RPC")
	ENFchain_RPC_logger.setLevel(logging.INFO)

	## get arguments
	args = define_and_get_arguments()

	## set parameters
	target_address = args.target_address
	test_func = args.test_func
	op_status = args.op_status
	wait_interval = args.wait_interval
	test_run = args.test_round
	samples_head = args.samples_head
	samples_size = args.samples_size
	tx_thread = args.tx_thread
	tx_size = args.tx_size

	## |------------------------ test function type -----------------------------|
	## | 0:set peer nodes | 1:round test | 2:single step test | 3:randshare test |
	## |-------------------------------------------------------------------------|

	if(test_func == 0):
		if(op_status == 1):
			neighbors = ENFchain_client.get_neighbors(target_address)
			logger.info(neighbors)
		elif(op_status == 2):
			peers = ENFchain_client.get_peers(target_address)
			logger.info(peers)
		elif(op_status == 3):
			tasks = [ENFchain_client.get_peers_info(target_address)]
			loop = asyncio.get_event_loop()
			done, pending = loop.run_until_complete(asyncio.wait(tasks))
			for future in done:
				logger.info(future.result())
			loop.close()
		else:
			# display peering nodes
			json_response=ENFchain_client.get_nodes(target_address)
			nodes = json_response['nodes']
			logger.info('Consensus nodes:')
			for node in nodes:
				logger.info(node)
	elif(test_func == 1):
		for x in range(test_run):
			logger.info("Test run:{}".format(x+1))
			if(op_status == 0):
				Epoch_validator(target_address, tx_thread, tx_size, 3)
				time.sleep(wait_interval)
			else:
				commit_tx_evaluate(target_address, tx_thread, tx_thread)
				# time.sleep(wait_interval*random.randint(1, 5))

		# get checkpoint after execution
		json_checkpoints = checkpoint_netInfo(target_address, False)
		for _item, _value in json_checkpoints.items():
			logger.info("{}: {}    {}".format(_item, _value[0], _value[1]))

	elif(test_func == 2):
		if(op_status == 100):
			ENFchain_client.send_enf_tx(target_address, samples_head, samples_size, True)
		elif(op_status == 101):
			## build dummy json_tx for test.
			json_tx={}
			json_tx['name']='Samuel'
			json_tx['age']=28
			## call submit tx API
			ret_msg = ENFchain_client.submit_transaction(target_address, json_tx)
			logger.info(ret_msg)
		elif(op_status == 102):
			ENFchain_client.launch_txs(tx_thread, tx_size)
		elif(op_status == 11):
			ENFchain_client.start_enf_submit(target_address, True)
		elif(op_status == 12):
			ENFchain_client.start_mining(target_address, True)
		elif(op_status == 13):
			ENFchain_client.check_head()
		elif(op_status == 14):
			ENFchain_client.start_voting(target_address, True)
		elif(op_status == 200):
			enf_proofs = ENFchain_client.get_enf_proofs(target_address)
			logger.info(enf_proofs)
		elif(op_status == 201):
			transactions = ENFchain_client.get_transactions(target_address)
			logger.info(transactions)
		elif(op_status == 210):
			tx_hash = args.data
			list_tx = ENFchain_client.query_transaction(target_address, tx_hash)
			for tx in list_tx:
				tx_size=len( tx[2].encode('utf-8'))
				logger.info("{}, committed in block:{}, size:{}.\n".format(TypesUtil.string_to_json(tx[2]),
																tx[3], tx_size))
		elif(op_status == 211):
			block_hash = args.data
			json_block = ENFchain_client.query_block(target_address, block_hash)
			if(json_block!={}):
				block_size = len( TypesUtil.json_to_string(json_block).encode('utf-8'))
				tx_count = len(json_block['transactions'])
				enf_proof_count = len(json_block['enf_proofs'])
				logger.info("{}, size:{}, tx_count:{}, enf_proof_count:{}".format(json_block, 
														block_size, tx_count, enf_proof_count))
		elif(op_status == 212):
			count_vote_size(target_address)
		elif(op_status == 22):
			disp_chaindata(target_address, True)
		elif(op_status == 9):
			ENFchain_client.run_consensus(target_address, True, True)
		elif(op_status == 90):
			validator_getStatus()
		else:
			json_checkpoints = checkpoint_netInfo(target_address, False)
			for _item, _value in json_checkpoints.items():
				logger.info("{}: {}    {}".format(_item, _value[0], _value[1])) 
	else:
		for x in range(test_run):
			logger.info("Test run:{}".format(x+1))
			Epoch_randomshare(target_address)
			time.sleep(wait_interval)
