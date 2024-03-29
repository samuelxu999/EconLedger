'''
========================
ENFchain_RPC module
========================
Created on Jan.21, 2021
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide encapsulation of client APIs that access to ENFchain_server node.
                  Mainly used to client test and demo
'''
import random
import time
import logging
import threading
import copy
import asyncio

from network.wallet import Wallet
from network.nodes import *
from consensus.transaction import Transaction
from consensus.block import Block
from consensus.consensus import POE
from utils.utilities import TypesUtil, FileUtil
from utils.service_api import SrvAPI
from utils.Swarm_RPC import Swarm_RPC
from utils.db_adapter import DataManager
from utils.configuration import *
from randomness.randshare import RandShare, RandOP

logger = logging.getLogger(__name__)


## --------------------------------- swarm_utils class ------------------------------------------
class swarm_utils(object):
	## ----------- class variables ----------------
	## Load ENF samples database for test
	ENF_data = FileUtil.csv_read("./data/one_day_enf.csv")

	##  ----------- class functions ---------------
	@staticmethod
	def getSwarmhash(samples_id, samples_head, samples_size, is_random=False):
		if(is_random==True):
			head_pos = random.randint(0,7200) 
		else:
			head_pos = samples_head 

		ls_ENF = TypesUtil.np2list(swarm_utils.ENF_data[head_pos:(head_pos+samples_size), 1]) 

		## ******************** upload ENF samples **********************
		## build json ENF data for transaction
		tx_json = {}

		json_ENF={}
		json_ENF['id']=samples_id
		json_ENF['enf']=ls_ENF
		tx_data = TypesUtil.json_to_string(json_ENF)  

		## save ENF data in transaction
		tx_json['data']=tx_data
		# print(tx_json)

		## random choose a swarm server
		target_address = Swarm_RPC.get_service_address()
		post_ret = Swarm_RPC.upload_data(target_address, tx_json)	

		return post_ret['data']

	@staticmethod
	def recordENF(samples_id):
		'''
		Record ENF sample to swarm network and retrun swarm hash (reference). 
		'''
		## use random ENF data for test
		head_pos = random.randint(0,7200) 
		samples_size = 60
		ls_ENF = TypesUtil.np2list(swarm_utils.ENF_data[head_pos:(head_pos+samples_size), 1]) 

		## ******************** upload ENF samples **********************
		## build json ENF data for transaction
		tx_json = {}

		json_ENF={}
		json_ENF['id']=samples_id
		json_ENF['enf']=ls_ENF
		tx_data = TypesUtil.json_to_string(json_ENF)  

		## save ENF data in transaction
		tx_json['data']=tx_data
		# print(tx_json)

		## random choose a swarm server
		target_address = Swarm_RPC.get_service_address()
		post_ret = Swarm_RPC.upload_data(target_address, tx_json)	

		return post_ret['data']

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

## --------------------------------- ENFchain_RPC ------------------------------------------
class ENFchain_RPC(object):
	'''
	------------ A client instance of ENFchain_RPC contains the following arguments: -------
	self.wallet: 			local wallet account management
	self.wallet_net: 		network wallet accounts management, for test purpose
	self.peer_nodes: 		peer nodes management	
	'''
	def __init__(self, 	keystore="keystore", 
						keystore_net="keystore_net"):
		## Instantiate the local wallet and load all accounts information
		self.wallet = Wallet(keystore)
		self.wallet.load_accounts()

		## Instantiate the net wallet and load all accounts information
		self.wallet_net = Wallet(keystore_net)
		self.wallet_net.load_accounts()

		## Instantiate the PeerNodes and load all nodes information
		self.peer_nodes = PeerNodes()
		self.peer_nodes.load_ByAddress()

	# =========================== client side REST API ==================================
	def run_consensus(self, target_address, exec_consensus, isBroadcast=False):
		json_msg={}
		json_msg['consensus_run']=exec_consensus

		if(not isBroadcast):
			json_response=SrvAPI.POST('http://'+target_address+'/test/consensus/run', json_msg)
			json_response = {'run_consensus': target_address, 'status': json_msg['consensus_run']}
		else:
			SrvAPI.broadcast_POST(self.peer_nodes.get_nodelist(), json_msg, '/test/consensus/run', True)
			json_response = {'run_consensus': 'broadcast', 'status': json_msg['consensus_run']}
		logger.info(json_response)

	def validator_getinfo(self, target_address, isBroadcast=False):
		info_list = []
		if(not isBroadcast):
			json_response = SrvAPI.GET('http://'+target_address+'/test/validator/getinfo')
			info_list.append(json_response)
		else:
			for node in self.peer_nodes.get_nodelist():
				json_node = TypesUtil.string_to_json(node)
				json_response = SrvAPI.GET('http://'+json_node['node_url']+'/test/validator/getinfo')
				info_list.append(json_response)
		return info_list

	def launch_txs(self, thread_num, tx_size):
		## Instantiate mypeer_nodes using deepcopy of self.peer_nodes
		mypeer_nodes = copy.deepcopy(self.peer_nodes)
		list_nodes = list(mypeer_nodes.get_nodelist())
		len_nodes = len(list_nodes)

		## Create thread pool
		threads_pool = []

		## 1) build tx_thread for each task
		for idx in range(thread_num):
			## random choose a peer node. 
			node_idx = random.randint(0,len_nodes-1)
			node_url = TypesUtil.string_to_json(list_nodes[node_idx])['node_url']

			## using random byte string for value of tx; value can be any bytes string.
			json_tx={}
			# json_tx['id']= TypesUtil.string_to_json(list_nodes[node_idx])['address']
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

	def send_enf_tx(self, target_address, samples_head, samples_size, isBroadcast=False):
		##----------------- build test transaction --------------------
		sender = self.wallet.accounts[0]
		sender_address = sender['address']
		sender_private_key = sender['private_key']
		## set recipient_address as default value: 0
		recipient_address = '0'
		time_stamp = time.time()

		## value comes from hash value to indicate address that ENF samples are saved on swarm network.
		json_value={}
		json_value['sender_address'] = sender_address
		json_value['data_ref'] = swarm_utils.getSwarmhash(sender_address, samples_head, samples_size)
		## convert json_value to string to ensure consistency in tx verification.
		str_value = TypesUtil.json_to_string(json_value)

		mytransaction = Transaction(sender_address, sender_private_key, recipient_address, time_stamp, str_value)

		## sign transaction
		sign_data = mytransaction.sign('samuelxu999')

		## --------------------- send transaction --------------------------------------
		transaction_json = mytransaction.to_json()
		transaction_json['signature']=TypesUtil.string_to_hex(sign_data)
		# print(transaction_json)
		if(not isBroadcast):
			json_response=SrvAPI.POST('http://'+target_address+'/test/transaction/verify', 
										transaction_json)
		else:
			json_response=SrvAPI.POST('http://'+target_address+'/test/transaction/broadcast', 
										transaction_json)
		logger.info(json_response)

	def get_transactions(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/transactions/get')
		transactions = json_response['transactions']
		return transactions

	def get_enf_proofs(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/enf_proofs/get')
		json_enf_proofs = json_response['enf_proofs']
		return json_enf_proofs

	def query_transaction(self, target_address, tx_hash):
		json_response=SrvAPI.GET('http://'+target_address+'/test/transaction/query', tx_hash)
		return json_response

	def query_block(self, target_address, block_hash):
		json_response=SrvAPI.GET('http://'+target_address+'/test/block/query', block_hash)
		return json_response

	def submit_transaction(self, target_address, tx_json):
		json_response=SrvAPI.POST('http://'+target_address+'/test/transaction/submit', tx_json)
		return json_response

	def start_enf_submit(self, target_address, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.GET('http://'+target_address+'/test/enf_proof/submit')
		else:
			SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/enf_proof/submit', True)
			json_response = {'start_enf_submit': 'broadcast'}

		logger.info(json_response)

	def start_mining(self, target_address, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.GET('http://'+target_address+'/test/mining')
		else:
			SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/mining', True)
			json_response = {'start mining': 'broadcast'}

		logger.info(json_response)

	def start_voting(self, target_address, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.GET('http://'+target_address+'/test/block/vote')
		else:
			SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/block/vote', True)
			json_response = {'verify_vote': 'broadcast'}
		logger.info(json_response)

	def get_neighbors(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/p2p/neighbors')
		return json_response

	def get_peers(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/p2p/peers')
		return json_response

	async def get_account(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/account/info')
		json_response['info']['node_url'] = target_address
		return json_response

	async def get_peers_info(self, target_address):
		## get p2p peers
		live_peers = self.get_peers(target_address)['peers']
		# print(live_peers)

		## set address list for each peer
		ls_peers = [peer[1]+":818"+str(peer[2])[-1] for peer in live_peers ]
		# print(ls_peers)	

		## async call get_account to query each peer's info
		cos = list(map(self.get_account, ls_peers))
		gathered = await asyncio.gather(*cos)
		info_peers = [node['info'] for node in gathered if node is not None]	

		return info_peers

	def get_nodes(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/nodes/get')
		return json_response

	def add_node(self, target_address, json_node, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.POST('http://'+target_address+'/test/nodes/add', json_node)
			logger.info(json_response)
		else:
			for target_node in target_address:
				try:
					SrvAPI.POST('http://'+target_node+'/test/nodes/add', json_node)
				except:
					logger.info("access {} failed.".format(target_node))
					pass

	def remove_node(self, target_address, json_node, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.POST('http://'+target_address+'/test/nodes/remove', json_node)
			logger.info(json_response)
		else:
			for target_node in target_address:
				try:
					SrvAPI.POST('http://'+target_node+'/test/nodes/remove', json_node)
				except:
					logger.info("access {} failed.".format(target_node))
					pass

	def get_chain(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/chain/get')
		return json_response

	def check_head(self):
		SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/chain/checkhead')
		json_response = {'Reorganize processed_head': 'broadcast'}

	## ================================ randomshare client API =================================
	def create_randshare(self, target_address, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.GET('http://'+target_address+'/test/randshare/create')
		else:
			SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/randshare/create', True)
			json_response = {'broadcast_create_randshare': 'Succeed!'}
		return json_response

	def fetch_randshare(self, target_address, isBroadcast=False):
		if(not isBroadcast):
			# get host address
			json_node={}
			json_node['address'] = self.wallet.accounts[0]['address']
			json_response=SrvAPI.POST('http://'+target_address+'/test/randshare/fetch', json_node)
		else:
			SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/randshare/cachefetched', True)
			json_response = {'broadcast fetch_randshare': 'Succeed!'}
		return json_response

	def verify_randshare(self, target_address, isBroadcast=False):
		if(not isBroadcast):
			json_response=SrvAPI.GET('http://'+target_address+'/test/randshare/verify')
		else:
			SrvAPI.broadcast_GET(self.peer_nodes.get_nodelist(), '/test/randshare/verify', True)
			json_response = {'broadcast verify_randshare': 'Succeed!'}
		return json_response

	def recovered_randshare(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/randshare/recovered')
		return json_response

	def fetchvote_randshare(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/randshare/fetchvote')
		return json_response

	def vote_randshare(self, target_address):
		json_response=SrvAPI.GET('http://'+target_address+'/test/randshare/cachevote')
		return json_response

	# ====================================== Random share test ==================================
	## request for share from peers and cache to local
	def cache_fetch_share(self, target_address):
		# read cached randshare
		host_shares=RandShare.load_sharesInfo(RandOP.RandDistribute)
		if( host_shares == None):
			host_shares = {}
		fetch_share=self.fetch_randshare(target_address)
		# logging.info(fetch_share)
		for (node_name, share_data) in fetch_share.items():
			host_shares[node_name]=share_data
		# update host shares 
		RandShare.save_sharesInfo(host_shares, RandOP.RandDistribute)

	## request for recovered shares from peers and cache to local 
	def cache_recovered_shares(self, target_address):
		# read cached randshare
		recovered_shares=RandShare.load_sharesInfo(RandOP.RandRecovered)
		if( recovered_shares == None):
			recovered_shares = {}
		host_recovered_shares=self.recovered_randshare(target_address)
		for (node_name, share_data) in host_recovered_shares.items():
			recovered_shares[node_name]=share_data
		# update host shares 
		RandShare.save_sharesInfo(recovered_shares, RandOP.RandRecovered)

	# request for vote shares from peers and cache to local 
	def cache_vote_shares(self, target_address):
		# read cached randshare
		vote_shares=RandShare.load_sharesInfo(RandOP.RandVote)
		if( vote_shares == None):
			vote_shares = {}
		host_vote_shares=fetchvote_randshare(target_address)
		# logging.info(host_vote_shares)
		for (node_name, share_data) in host_vote_shares.items():
			vote_shares[node_name]=share_data
		# update host shares 
		RandShare.save_sharesInfo(vote_shares, RandOP.RandVote)

	# test recovered shares
	def recovered_shares(self, host_address):		
		# read cached randshare
		recovered_shares=RandShare.load_sharesInfo(RandOP.RandRecovered)
		if( recovered_shares == None):
			recovered_shares = {}
		# print(recovered_shares)

		## Instantiate mypeer_nodes using deepcopy of self.peer_nodes
		peer_nodes = copy.deepcopy(self.peer_nodes)
		peer_nodes.load_ByAddress(host_address)
		json_nodes = TypesUtil.string_to_json(list(peer_nodes.get_nodelist())[0])
		# get public numbers given peer's pk
		public_numbers = RandShare.get_public_numbers(json_nodes['public_key'])

		# get shares information
		shares = recovered_shares[host_address]
		# print(shares)
		# instantiate RandShare to verify share proof.
		myrandshare = RandShare(daemon=False)
		myrandshare.p = public_numbers.n

		secret=myrandshare.recover_secret(shares)
		# print('secret recovered from node shares:', secret)
		return secret

	# test new random generator
	def new_random(self, ls_secret):
		# get host account information
		json_nodes=self.wallet.accounts[0]
		# get public numbers given pk
		public_numbers = RandShare.get_public_numbers(json_nodes['public_key'])

		# instantiate RandShare to verify share proof.
		myrandshare = RandShare(daemon=False)
		myrandshare.p = public_numbers.n

		# calculate new random number
		random_secret = myrandshare.calculate_random(ls_secret)

		logger.info("New random secret: {}".format(random_secret))
