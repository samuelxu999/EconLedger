'''
========================
app_server module
========================
Created on June.8, 2023
@author: Xu Ronghua
@Email:  rxu22@binghamton.edu
@TaskDescription: This module provide application server side api
'''

import sys
import logging
import random

from flask import Flask, render_template
from flask import request
from argparse import ArgumentParser
from utils.utilities import TypesUtil
from utils.Client_RPC import Client_RPC

logger = logging.getLogger(__name__)

# ================================= Instantiate the server =====================================
app = Flask(__name__)

#===================================== Web App handler ===================================
@app.route('/')
def info():
    ## query information of neighbors
    target_address = args.bootstrapnode
    neighbors = Client_instace.query_neighbors(target_address)['neighbors']

    ls_peers = []

    for node in neighbors:
        node_info={}
        node_info['url']="{}:81{}".format(node[0], str(node[1])[-2:])

        ## get account address
        _account = Client_instace.query_account(node_info['url'])['info']
        node_info['account']=str(_account['address'])

        ## get validator information
        _validator = Client_instace.query_validator(node_info['url'])
        node_info['node_id']=str(_validator['node_id'])

        ## update reputation information
        node_info['reputation']=str( random.randint(0,10))

        ls_peers.append(node_info)


    return render_template('info.html', posts = [ls_peers, len(ls_peers)])

@app.route('/validator', methods=['GET', 'POST'])
def validator():
    ret_posts = ['NULL']
    ## get params from request
    if request.method == 'POST':
        node_url = request.form.get('node_url')
        ret_posts[0]=node_url
        
        if(ret_posts[0]==''):
            ret_posts[0]='NULL'
        else:
            try:
                ## get validator information
                _validator = Client_instace.query_validator(node_url)

                ret_posts.append(_validator)

                ## get vote list
                ls_vote = []
                for source, value in _validator['vote_count'].items():
                    for target, vote in value.items():
                        ls_vote.append([source, target, vote])

                ret_posts.append(ls_vote)
            except Exception as e:
                ret_posts[0] = 'Fail'
                ret_posts.append(str(e))

    return render_template('validator.html', posts = ret_posts)

@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    ret_posts = ['NULL']
    ## get params from request
    if request.method == 'POST':
        tx_hash = request.form.get('tx_hash')

        if(tx_hash!=""):
            ret_posts[0]=tx_hash
        
            ## random choose a node for target_address
            list_nodes = Client_instace.nodes
            len_nodes = len(list_nodes)
            node_idx = random.randint(0,len_nodes-1)
            target_address = list_nodes[node_idx][0]+':818'+str(list_nodes[node_idx][1])[-1]

            ret_posts.append(target_address)

            ## get transaction information
            ret_tx = Client_instace.query_tx(target_address, tx_hash)

            ret_posts.append(len(ret_tx))
            if(len(ret_tx)!=0):
                ret_posts.append([ret_tx[0][3], TypesUtil.string_to_json(ret_tx[0][2])])

    return render_template('transaction.html', posts = ret_posts)

@app.route('/block', methods=['GET', 'POST'])
def block():
    ret_posts = ['NULL']
    ## get params from request
    if request.method == 'POST':
        block_hash = request.form.get('block_hash')

        if(block_hash!=""):
            ret_posts[0]=block_hash
        
            ## random choose a node for target_address
            list_nodes = Client_instace.nodes
            len_nodes = len(list_nodes)
            node_idx = random.randint(0,len_nodes-1)
            target_address = list_nodes[node_idx][0]+':818'+str(list_nodes[node_idx][1])[-1]

            ret_posts.append(target_address)

            ## get block information
            json_block = Client_instace.query_blk(target_address, block_hash)

            # print(json_block['enf_proofs'])

            ret_posts.append(json_block)

    return render_template('block.html', posts = ret_posts)

def define_and_get_arguments(args=sys.argv[1:]):
    parser = ArgumentParser(description="Run microchain websocket server.")

    parser.add_argument("--debug", action="store_true", 
                        help="if set, debug model will be used.")

    parser.add_argument("--threaded", action="store_true", 
                        help="if set, support threading request.")

    parser.add_argument('-p', '--port', default=8188, type=int, 
                        help="port to listen on.")

    parser.add_argument("--bootstrapnode", default='127.0.0.1:8180', type=str, 
                        help="bootstrap node address format[ip:port] to join the network.")

    args = parser.parse_args()

    return args

## ****************************** Main function ***********************************
if __name__ == '__main__':
    FORMAT = "%(asctime)s %(levelname)s %(filename)s(l:%(lineno)d) - %(message)s"
    # FORMAT = "%(asctime)s %(levelname)s | %(message)s"
    LOG_LEVEL = logging.INFO
    logging.basicConfig(format=FORMAT, level=LOG_LEVEL)

    ## get arguments
    args = define_and_get_arguments()

    ## initialize Client_RPC instance
    Client_instace = Client_RPC(args.bootstrapnode)

    ## -------------------------------- run app server ----------------------------------------
    app.run(host='0.0.0.0', port=args.port, debug=args.debug, threaded=args.threaded)


