'''
========================
Client_RPC module
========================
Created on August.10, 2022
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide encapsulation of client APIs that access to Microchain node.
                  Mainly used to client application
'''
import random
import time
import logging
import threading
import queue
import copy
import asyncio

from network.nodes import *
from utils.utilities import TypesUtil, FileUtil
from utils.service_api import SrvAPI, ReqThread, QueryThread
from utils.configuration import *

logger = logging.getLogger(__name__)

## ---------------------- Internal function and class -----------------------------
class TxsThread(threading.Thread):
	'''
	Threading class to handle multiple txs threads pool
	'''
	def __init__(self, argv):
		threading.Thread.__init__(self)
		self.argv = argv

	#The run() method is the entry point for a thread.
	def run(self):
		## set parameters based on argv
		node_url = self.argv[0]
		json_tx = self.argv[1]

		SrvAPI.POST('http://'+node_url+'/test/transaction/submit', json_tx)

## --------------------------------- Client_RPC ------------------------------------------
class Client_RPC(object):
	'''
	------------ A client instance of Client_RPC contains the following arguments: -------
	self.peer_nodes: 		peer nodes management	
	'''
	def __init__(self, bootstrap_address):
		## Query nodes from bootstrap_address
		self.nodes = SrvAPI.GET('http://'+bootstrap_address+'/test/p2p/neighbors')['neighbors']

	## =========================== client side REST API ==================================
	def query_neighbors(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/p2p/neighbors')
		return json_response

	def query_account(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/account/info')
		json_response['info']['node_url'] = target_address
		return json_response

	def query_validator(self, target_address):
		json_response = SrvAPI.GET('http://'+target_address+'/test/validator/getinfo')
		return json_response

	def query_tx_pool(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/transactions/get')
		transactions = json_response['transactions']		
		return transactions

	def query_tx(self, target_address, tx_hash):
		json_response=SrvAPI.GET('http://'+target_address+'/test/transaction/query', tx_hash)
		return json_response

	def query_blk(self, target_address, block_hash):
		json_response=SrvAPI.GET('http://'+target_address+'/test/block/query', block_hash)
		return json_response

	def query_ledger(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/chain/get')
		return json_response

	## --------------------- tx broadcast ----------------------
	def submit_tx(self, target_address, tx_json):
		json_response=SrvAPI.POST('http://'+target_address+'/test/transaction/submit', tx_json)
		return json_response

	def submit_txs(self, thread_num, tx_size):
		## Instantiate mypeer_nodes using deepcopy of self.peer_nodes
		list_nodes = self.nodes
		len_nodes = len(self.nodes)

		## Create thread pool
		threads_pool = []

		## 1) build tx_thread for each task
		for idx in range(thread_num):
			## random choose a peer node. 
			node_idx = random.randint(0,len_nodes-1)
			node_url = list_nodes[node_idx][0]+':818'+str(list_nodes[node_idx][1])[-1]

			## using random byte string for value of tx; value can be any bytes string.
			json_tx={}
			json_tx['data']=TypesUtil.string_to_hex(os.urandom(tx_size)) 

			## Create new threads for tx
			p_thread = TxsThread( [node_url, json_tx] )

			## append to threads pool
			threads_pool.append(p_thread)

			## The start() method starts a thread by calling the run method.
			p_thread.start()

		## 2) The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		logger.info('launch txs, number:{}, size: {}'.format(thread_num, tx_size))

	## --------------------- consensus functions ----------------------
	def exec_mining(self):
		headers = {'Content-Type' : 'application/json'}
		exec_nodes = []

		## Create thread pool
		threads_pool = []
		i=0
		for node in self.nodes:
			node_url = node[0]+':818'+str(node[1])[-1]
			api_url = 'http://' + node_url + '/test/mining'
			exec_nodes.append(node_url)

			i+=1
			# Create new threads
			p_thread = ReqThread(i, 0, [api_url, headers])

			# append to threads pool
			threads_pool.append(p_thread)

			# The start() method starts a thread by calling the run method.
			p_thread.start()


		# The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		logger.info('exec_mining by nodes:{}'.format(exec_nodes))

	def exec_check_head(self):
		headers = {'Content-Type' : 'application/json'}
		exec_nodes = []

		## Create thread pool
		threads_pool = []
		i=0
		for node in self.nodes:
			node_url = node[0]+':808'+str(node[1])[-1]
			api_url = 'http://' + node_url + '/test/chain/checkhead'
			exec_nodes.append(node_url)

			i+=1
			# Create new threads
			p_thread = ReqThread(i, 0, [api_url, headers])

			# append to threads pool
			threads_pool.append(p_thread)

			# The start() method starts a thread by calling the run method.
			p_thread.start()


		# The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		logger.info('exec_check_head by nodes:{}'.format(exec_nodes))

	def exec_voting(self):
		headers = {'Content-Type' : 'application/json'}
		exec_nodes = []

		## Create thread pool
		threads_pool = []
		i=0
		for node in self.nodes:
			node_url = node[0]+':818'+str(node[1])[-1]
			api_url = 'http://' + node_url + '/test/block/vote'
			exec_nodes.append(node_url)

			i+=1
			# Create new threads
			p_thread = ReqThread(i, 0, [api_url, headers])

			# append to threads pool
			threads_pool.append(p_thread)

			# The start() method starts a thread by calling the run method.
			p_thread.start()


		# The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		logger.info('exec_voting by nodes:{}'.format(exec_nodes))

	def start_consensus(self):
		headers = {'Content-Type' : 'application/json'}
		exec_nodes = []

		json_msg={}
		json_msg['consensus_run']=True

		## Create thread pool
		threads_pool = []
		i=0
		for node in self.nodes:
			node_url = node[0]+':818'+str(node[1])[-1]
			api_url = 'http://' + node_url + '/test/consensus/run'
			exec_nodes.append(node_url)

			i+=1
			# Create new threads
			p_thread = ReqThread(i, 1, [api_url, json_msg, headers])

			# append to threads pool
			threads_pool.append(p_thread)

			# The start() method starts a thread by calling the run method.
			p_thread.start()


		# The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		logger.info('start_consensus by nodes:{}'.format(exec_nodes))

	def query_validators(self):
		'''
		query all validators information and return a queue list
		'''
		## Create queue to save results
		ret_queue = queue.Queue()
		## Create thread pool
		threads_pool = []
		## Create a list to save status from validators
		json_status = []

		headers = {'Content-Type' : 'application/json'}

		## 1) For each node and assign querying task to a QueryThread
		for node in self.nodes:
			node_url = node[0]+':818'+str(node[1])[-1]
			api_url = 'http://' + node_url + '/test/validator/getinfo'
			node_address = node_url
			## Create new threads for tx
			p_thread = QueryThread( [ret_queue, node_address, api_url, headers] )

			## append to threads pool
			threads_pool.append(p_thread)

			## The start() method starts a thread by calling the run method.
			p_thread.start()

		# 2) The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		# 3) get all results from queue
		while not ret_queue.empty():
			## q_data is used to save json response from GET
			q_data = ret_queue.get()
			json_status.append(q_data)
			# json_status[q_data['address']]={}
			# json_status[q_data['address']]['consensus_run']=q_data['consensus_run']
			# json_status[q_data['address']]['consensus_status']=q_data['consensus_status']

		return json_status

	def query_validators_status(self):
		'''
		query all validators status and return a queue list
		'''
		## Create queue to save results
		ret_queue = queue.Queue()
		## Create thread pool
		threads_pool = []
		## Create a list to save status from validators
		json_status = []

		headers = {'Content-Type' : 'application/json'}

		## 1) For each node and assign querying task to a QueryThread
		for node in self.nodes:
			node_url = node[0]+':818'+str(node[1])[-1]
			api_url = 'http://' + node_url + '/test/validator/status'
			node_address = node_url
			## Create new threads for tx
			p_thread = QueryThread( [ret_queue, node_address, api_url, headers] )

			## append to threads pool
			threads_pool.append(p_thread)

			## The start() method starts a thread by calling the run method.
			p_thread.start()

		# 2) The join() waits for all threads to terminate.
		for p_thread in threads_pool:
			p_thread.join()

		# 3) get all results from queue
		while not ret_queue.empty():
			## q_data is used to save json response from GET
			q_data = ret_queue.get()
			json_status.append(q_data)
			# json_status[q_data['address']]={}
			# json_status[q_data['address']]['consensus_run']=q_data['consensus_run']
			# json_status[q_data['address']]['consensus_status']=q_data['consensus_status']

		return json_status