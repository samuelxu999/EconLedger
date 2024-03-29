'''
========================
block.py
========================
Created on Dev.10, 2020
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide block data struct and functions implementation.
@Reference: 
'''

from collections import OrderedDict

from merklelib import MerkleTree, jsonify as merkle_jsonify

from utils.utilities import TypesUtil, FuncUtil
from cryptolib.crypto_rsa import Crypto_RSA
from utils.configuration import *
from consensus.transaction import Transaction

class Block(object):
	"""One node (roundrobin) adds a new block to the blockchain every
	BLOCK_PROPOSAL_TIME iterations.

	Args:
	    parent: 		parent block
	    transactions: 	committed transactions in new block.
	    nonce: 			nonce proof to meet difficult level.
	"""

	def __init__(self, parent=None, merkle_root=0, transactions=[], enf_proofs=[], nonce = 0):
		"""A block contains the following arguments:

		self.hash: 			hash of the block
		self.height: 		height of the block (genesis = 0)
		self.previous_hash: hash of the parent block
		self.transactions: 	transactions list
		self.merkle_root: 	merkle tree root (hash) of transactions.
		self.enf_proofs: 	enf proof list
		"""
		# If we are genesis block, set initial values
		if not parent:
			self.height = 0
			self.previous_hash = 0
		else:
			self.height = parent.height+1
			self.previous_hash = parent.hash
		
		self.merkle_root = merkle_root
		self.transactions = transactions
		self.enf_proofs = enf_proofs
		self.nonce = nonce

		block = {'height': self.height,
			'previous_hash': self.previous_hash,
			'transactions': self.transactions,
			'merkle_root': self.merkle_root,
			'enf_proofs': self.enf_proofs,
			'nonce': self.nonce}
		# calculate hash of block 
		self.hash = TypesUtil.hash_json(block)
		return

	def to_dict(self):
		"""
		Output dict block data structure. 
		"""
		order_dict = OrderedDict()
		order_dict['hash'] = self.hash
		order_dict['height'] = self.height
		order_dict['previous_hash'] = self.previous_hash
		order_dict['transactions'] = self.transactions
		order_dict['merkle_root'] = self.merkle_root
		order_dict['enf_proofs'] = self.enf_proofs
		order_dict['nonce'] = self.nonce
		return order_dict
    
	def to_json(self):
		"""
		Output dict block data structure. 
		"""
		return {'hash': self.hash,
				'height': self.height,
				'previous_hash': self.previous_hash,
				'transactions': self.transactions,
				'merkle_root': self.merkle_root,
				'enf_proofs': self.enf_proofs,
				'nonce': self.nonce }

	def print_data(self):
		print('Block information:')
		print('    hash:',self.hash)
		print('    height:',self.height)
		print('    previous_hash:',self.previous_hash)
		print('    transactions:',self.transactions)
		print('    merkle_root:',self.merkle_root)
		print('    enf_proofs:',self.enf_proofs)
		print('    nonce:',self.nonce)

	def sign(self, sender_private_key, sk_pw):
		'''
		Sign block by using sender's private key and password
		'''
		try:
			private_key_byte = TypesUtil.hex_to_string(sender_private_key)
			private_key = Crypto_RSA.load_private_key(private_key_byte, sk_pw)

			# generate hashed json_block
			hash_data = TypesUtil.hash_json(self.to_json(),'sha1')
			sign_value = Crypto_RSA.sign(private_key, hash_data)
		except:
			sign_value=''
		return sign_value

	def verify(self, sender_public_key, signature):
		"""
		Verify block signature by using sender's public key
		"""
		try:
			public_key_byte = TypesUtil.hex_to_string(sender_public_key)
			publick_key = Crypto_RSA.load_public_key(public_key_byte)

			# generate hashed json_block
			hash_data = TypesUtil.hash_json(self.to_json(),'sha1')
			verify_sign=Crypto_RSA.verify(publick_key,signature,hash_data)
		except:
			verify_sign=False
		return verify_sign

	def get_epoch(self, epoch_size=EPOCH_SIZE):
		"""
		return the epoch height
		"""
		return(self.height // epoch_size)

	@staticmethod
	def json_to_block(block_json):
		"""
		Output block object given json block data structure. 
		"""
		block = Block()
		block.hash = block_json['hash']
		block.height = block_json['height']
		block.previous_hash = block_json['previous_hash']
		block.transactions = block_json['transactions']
		block.merkle_root = block_json['merkle_root']
		block.enf_proofs = block_json['enf_proofs']
		block.nonce = block_json['nonce']
		return block

	@staticmethod
	def isEmptyBlock(block_json):
		"""
		check if block_json is empty block. 
		"""
		if( (block_json['height'] >0) and block_json['nonce']==0):
			return True
		return False
