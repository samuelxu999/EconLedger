'''
========================
consensus.py
========================
Created on Dec.10, 2020
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide consensus algorithm implementation.
@Reference: 
'''

from enum import Enum

from merklelib import MerkleTree, jsonify as merkle_jsonify

from utils.configuration import *
from utils.utilities import TypesUtil, FuncUtil
from consensus.transaction import Transaction
from utils.Swarm_RPC import Swarm_RPC
from consensus.ENF_consensus import ENFUtil

class POE():
	''' 
	Proof-of-ENF consenses mechanism
	'''
	@staticmethod
	def proof_of_enf(commit_enf_proofs, validator_id):
		"""
		Proof of ENF algorithm
		@ commit_enf_proofs: 	commited enf_proofs list when new block is generated
		@ validator_id: 		the address of validator 
		"""
		## 1) query ENF samples from swarm nodes given commit_enf_proofs.
		ENF_samples = Swarm_RPC.get_ENFsamples(commit_enf_proofs)

		## For byzantine tolerant: 3f+1, at least 4 samples points are required. 
		if(len(ENF_samples)<4):
			return False
		
		## 2) calculate ENF score for each node 
		ls_ENF_score = []
		for ENF_id in range(len(ENF_samples)):
			# print(sample_data['enf'])
			sorted_ENF_sqr_dist=ENFUtil.sort_ENF_sqr_dist(ENF_samples, ENF_id)
			ENF_score = ENFUtil.ENF_score(sorted_ENF_sqr_dist)
			ls_ENF_score.append([ENF_id, ENF_score])

		## 3) get sorted ENF score 
		sorted_score = sorted(ls_ENF_score, key=lambda x:x[1])
		# print(sorted_score)

		winner_id = ENF_samples[sorted_score[0][0]][2]
		# print("winner: {}    sender: {}   result: {}".format(winner_id, validator_id,
		# 													validator_id==winner_id))

		## 4) return if validator_id has proposed the least score among all nodes
		return validator_id==winner_id
