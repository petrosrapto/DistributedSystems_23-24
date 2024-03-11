import pickle
from node import Node
from copy import deepcopy

from flask import Blueprint, jsonify, request
import traceback
###########################################################
################## INITIALIZATIONS ########################
###########################################################


# Define the node object of the current node.
node = Node()
# Define the number of nodes in the network.
N = 0
# Define a Blueprint for the api endpoints.
rest_api = Blueprint('rest_api', __name__)


###########################################################
################## API/API COMMUNICATION ##################
###########################################################


@rest_api.route('/get_block', methods=['POST'])
def get_block():
    '''Endpoint that gets an incoming block, validates it and adds it in the
        blockchain.

        Input:
            new_block: the incoming block in pickle format.
        Returns:
            message: the outcome of the procedure.
    '''

    try:
        new_block = pickle.loads(request.get_data())
        (validation, changed_ring) = node.validate_block(new_block)
        if validation:
            # If the block is valid:
            # - Add block to the current blockchain.
            # - Remove the new_block's transactions from the unconfirmed_blocks of the node.
            node.chain_lock.acquire()
            node.add_block_to_chain(new_block, changed_ring)
            node.chain_lock.release()
            node.filter_transactions(new_block)
            node.checkOutOfOrderBlocks()
            return jsonify({'message': "OK"})
        # what happens when a block is rejected?
        elif new_block.previous_hash != node.chain.blocks[-1].current_hash:
            # received out of order 
            node.outOfOrderBlocks.append(new_block)
        else:
            return jsonify({'mesage': "Block rejected."}), 400
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500

@rest_api.route('/validate_transaction', methods=['POST'])
def validate_transaction():
    '''Endpoint that gets an incoming transaction and valdiates it.
       Input:
            new_transaction: the incoming transaction in pickle format.
       Returns:
            message: the outcome of the procedure.

       Note: Each validated transaction is added to the transactions pool,
       from where blocks are shaped, gathering many transactions together.
       If the transaction is validated, the softState is changed.
    '''
    try:
        new_transaction = pickle.loads(request.get_data())
        (validation, changed_ring) = node.validate_transaction(new_transaction)
        if validation:
            node.add_transaction_to_pool(new_transaction)
            node.softState_ring = changed_ring
            # if the current node is the receiver or the sendera added to its wallet
            if (new_transaction.receiver_address == node.wallet.public_key or \
                new_transaction.sender_address == node.wallet.public_key):
                node.wallet.transactions.append([new_transaction, "None", "Unconfirmed"])
            return jsonify({'message': "OK"}), 200
        else:
            return jsonify({'message': "The transaction is invalid"}), 400
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500

@rest_api.route('/register_node', methods=['POST'])
def register_node():
    '''Endpoint that registers a new node in the network.
        It is called only in the bootstrap node.

        Input:
            public_key: the public key of node to enter.
            ip: the ip of the node to enter.
            port: the port of the node to enter.

        Returns:
            id: the id that the new node is assigned.
    '''
    try:

        if (not IS_BOOTSTRAP):
            return jsonify({'message': "Node isnt bootstrap"}), 401
        elif (len(node.chainState_ring) == N):
            return jsonify({'message': "System is full, exactly N nodes are running"}), 401

        # Get the arguments
        node_key = request.form.get('public_key')
        node_ip = request.form.get('ip')
        node_port = request.form.get('port')
        node_id = len(node.chainState_ring)

        # Add node in the list of registered nodes.
        node.register_node_to_ring(
            id=node_id, ip=node_ip, port=node_port, public_key=node_key) 
        # When all nodes are registered, the bootstrap node sends them:
        # - the ring
        # - the current chain
        # - a transaction of their first BCCs
        if (node_id == N - 1):
            # update the soft state of the bootstrap node
            node.softState_ring = deepcopy(node.chainState_ring) 
            for ring_node in node.chainState_ring:
                if ring_node["id"] != node.id: # dont send to myself
                    node.share_ring(ring_node)
                    node.share_chain(ring_node)
            for ring_node in node.chainState_ring:
                if ring_node["id"] != node.id:
                    node.create_transaction(
                        receiver=ring_node['public_key'],
                        amount=1000
                    )
        return jsonify({'message': "OK", 'id': node_id}), 200
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500


@rest_api.route('/get_ring', methods=['POST'])
def get_ring():
    '''Endpoint that gets a ring (information about other nodes).
        Input:
            ring: the ring in pickle format.
        Returns:
            message: the outcome of the procedure.
    '''
    try:
        node.chainState_ring = pickle.loads(request.get_data())
        # Update the id of the node based on the given ring.
        for ring_node in node.chainState_ring:
            if ring_node['public_key'] == node.wallet.public_key:
                node.id = ring_node['id']
        return jsonify({'message': "OK"})
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500


@rest_api.route('/get_chain', methods=['POST'])
def get_chain():
    '''Endpoint that gets a blockchain.

        Input:
            chain: the blockchain in pickle format.
        Returns:
            message: the outcome of the procedure.
    '''
    try:
        got_chain = pickle.loads(request.get_data())
        (validation, ring) = node.validate_chain(got_chain)
        if validation and len(node.chain.blocks) == 0:
            node.chain = got_chain
            # init soft and chain state
            node.chainState_ring = ring
            node.softState_ring = ring 
            # clear the transaction pool
            node.transaction_pool_lock.acquire()
            node.transaction_pool.clear()
            node.transaction_pool_lock.release()
            return jsonify({'message': "OK"}), 200
        return jsonify({'message': "Chain rejected"}), 400
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500

@rest_api.route('/send_chain', methods=['GET'])
def send_chain():
    '''Endpoint that sends a blockchain.

        Returns:
            the blockchain of the node in pickle format.
    '''
    try:
        return pickle.dumps(node.chain)
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500
    

##############################################################
################## CLIENT/API COMMUNICATION ##################
##############################################################


@rest_api.route('/api/create_transaction', methods=['POST'])
def create_transaction():
    '''Endpoint that creates a new transaction.

        Input:
            receiver: the id of the receiver node.
            amount: the amount of BCCs to send.
            message: the message to send
        Returns:
            message: the outcome of the procedure.
    '''

    # Get the arguments.
    # Assuming 'stake' is submitted as a string, like "true" 
    # Defaults to 'false'
    if request.form.get('stake', 'false') == 'true':
        receiver_public_key = "0"
        message = ""
    else:
        receiver_id = int(request.form.get('receiver'))
        receiver_public_key = node.ID_to_key(receiver_id)
        message = request.form.get('message')
    amount = int(request.form.get('amount'))
    
    if (receiver_public_key and receiver_public_key != node.wallet.public_key):
        if node.create_transaction(receiver_public_key, amount, message):
            return jsonify({'message': 'The transaction was created successfully.', 'balance': node.wallet.get_balance(), 'stake': node.wallet.get_stake()}), 200
        else:
            return jsonify({'message': 'Not enough BCCs.', 'balance': node.wallet.get_balance(), 'stake': node.wallet.get_stake()}), 400
    else:
        return jsonify({'message': 'Transaction failed. Wrong receiver id.'}), 400


@rest_api.route('/api/get_balance', methods=['GET'])
def get_balance():
    '''Endpoint that returns the current balance of the node.

        Returns:
            message: the current balance.
    '''
    try:
        return jsonify({'message': node.wallet.get_balance()}), 200
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500

@rest_api.route('/api/get_stake', methods=['GET'])
def get_stake():
    '''Endpoint that returns the current stake of the node.

        Returns:
            message: the current stake.
    '''
    try:
        return jsonify({'message': node.wallet.get_stake()}), 200
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500

@rest_api.route('/api/view_block', methods=['GET'])
def view_block():
    '''Endpoint that returns the transactions of the last confirmed block.

        Returns:
            a formatted list of transactions in pickle format.
    '''
    try:
        transactions_list = [tr.to_list() for tr in node.chain.blocks[-1].transactions]
        modified_transactions_list = [
            [
                node.key_to_ID(sender_address), 
                "--" if receiver_address == "0" else node.key_to_ID(receiver_address), 
                amount, 
                "stake update" if receiver_address == "0" else message, 
                node.key_to_ID(node.chain.blocks[-1].validator)
            ] 
            for sender_address, receiver_address, amount, message in transactions_list
        ]
        return pickle.dumps(modified_transactions_list)
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500


@rest_api.route('/api/get_my_transactions', methods=['GET'])
def get_my_transactions():
    '''Endpoint that returns all the transactions of a node (as a sender or receiver).
        Returns:
            a formatted list of transactions in pickle format.
    '''
    try:
        wallet_transactions_list = [tr[0].to_list() for tr in node.wallet.transactions]
        modified_transactions_list = [
            [
                node.key_to_ID(sender_address), 
                "--" if receiver_address == "0" else node.key_to_ID(receiver_address), 
                amount, 
                "stake update" if receiver_address == "0" else message, 
            ] 
            for (sender_address, receiver_address, amount, message) in wallet_transactions_list
        ]
        for modified_transaction, original_transaction in zip(modified_transactions_list, node.wallet.transactions):
            validator, status = original_transaction[1], original_transaction[2]
            # Append the validator and status to the modified transaction list
            validator = validator if validator == "None" else node.key_to_ID(validator)
            modified_transaction.append(validator)
            modified_transaction.append(status)
        return pickle.dumps(modified_transactions_list)
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500


@rest_api.route('/api/get_id', methods=['GET'])
def get_id():
    '''Endpoint that returns the id of the node.

        Returns:
            message: the id of the node.
    '''
    try:
        return jsonify({'message': node.id}), 200
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500
    
@rest_api.route('/api/get_metrics', methods=['GET'])
def get_metrics():
    '''Endpoint that returns some useful parameters of the network.

        Returns:
            num_blocks: total number of blocks.
            capacity: the capacity of each block.
    '''
    try:
        return jsonify({'num_blocks': len(node.chain.blocks), 'capacity': node.CAPACITY})
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        traceback_string = "".join(tb_str)
        print(traceback_string)
        return jsonify({'message': f"{e}"}), 500