import requests
import pickle
import numpy as np

from copy import deepcopy
from collections import deque
from threading import Lock, Thread

from blockchain import Blockchain
from block import Block
from wallet import Wallet
from transaction import Transaction

class Node:
    """
    A node in the network.

    Attributes:
        id (int): the id of the node.
        chain (Blockchain): the blockchain that the node has.
        wallet (Wallet): the wallet of the node.
        chainState_ring (list): list of information about other nodes
                                (id, ip, port, public_key, balance, stake, nonces).
                                nonces is a list where the nonces seen are kept.
                                The balances, stakes, nonces are the ones up until the 
                                last block of the chain, so they are valid but not 100% 
                                up to date
        softState_ring (list):  same with chainState_ring but the balances, stakes, nonces
                                include the ones from the chainState with the additional 
                                state's change enforced by the validated transactions
                                of the transaction pool (which are not yet added to the blockchain).
                                That means that the softState is NOT valid (added to the chain)
                                but 100% up to date
        lock (Lock): a lock in order to provide mutual exclution for chain/transaction_pool.
        outOfOrderBlocks (deque): A queue that contains the block that received out of order
        transaction_pool (deque): A queue that contains all the validated 
                                transactions waiting to be inserted to a block
        send_counter (int):     a counter that holds how many transactions were made
                                by the current node as sender
        CAPACITY(int):          the number of transaction in a block
    """

    def __init__(self):
        """Inits a Node."""
        self.id = None
        self.chain = Blockchain()
        self.wallet = self.generate_wallet() 
        self.chainState_ring = []
        self.softState_ring = []
        self.chain_lock = Lock()
        self.transaction_pool_lock = Lock()
        self.transaction_pool = deque()
        self.outOfOrderBlocks = deque()
        self.send_counter = 0

    def __str__(self):
        """Returns a string representation of a Node object."""
        return str(self.__class__) + ": " + str(self.__dict__)

    def generate_wallet(self):
        return Wallet(self) # pass my pointer 

    def create_new_block(self, genesis=False):
        """Creates a new block for the blockchain."""
        if genesis:
            # Here, the genesis block is created.
            new_idx = 0
            previous_hash = 1
            validator = 0
            return Block(new_idx, previous_hash, validator)
        else:
            new_block = Block(self.chain.blocks[-1].index + 1, self.chain.blocks[-1].current_hash, self.ID_to_key(self.id))
            self.add_transactions_to_block(new_block)
            new_block.set_hash()
            return new_block
        

    def register_node_to_ring(self, id, ip, port, public_key):
        """Registers a new node in the ring.

        This method is called only in the bootstrap node.
        """

        self.chainState_ring.append(
            {
                'id': id,
                'ip': ip,
                'port': port,
                'public_key': public_key,
                'balance': 0, # default value
                'stake': 1, # default value
                'nonces': []
            })

    @staticmethod
    def ID_to_balance(id, ring):
        # search for the first occurrence that matches your condition 
        # and return its balance. If no matching condition is found, 
        # it will return None
        return next((ring_node['balance'] for ring_node in ring if ring_node['id'] == id), None)
   
    @staticmethod
    def ID_to_stake(id, ring):
        return next((ring_node['stake'] for ring_node in ring if ring_node['id'] == id), None)


    @staticmethod
    def update_balance(id, change, ring):
        for ring_node in ring:
            if ring_node['id'] == id:
                ring_node['balance'] += change
                break

    @staticmethod
    def update_nonces(id, nonce, ring):
        for ring_node in ring:
            if ring_node['id'] == id:
                ring_node['nonces'].append(nonce)
                break  

    @staticmethod
    def update_stake(id, change, ring):
        for ring_node in ring:
            if ring_node['id'] == id:
                ring_node['stake'] += change
                break

    @staticmethod
    def ID_to_nonces(id, ring):
        return next((ring_node['nonces'] for ring_node in ring if ring_node['id'] == id), None)

    def key_to_ID(self, address):
        return next((ring_node['id'] for ring_node in self.chainState_ring if ring_node['public_key'] == address), 0)

    def IP_to_ID(self, address):
        return next((ring_node['id'] for ring_node in self.chainState_ring if ring_node['ip'] == address), None)
    
    def ID_to_IP(self, id):
        return next((ring_node['ip'] for ring_node in self.chainState_ring if ring_node['id'] == id), None)

    def ID_to_port(self, id):
        return next((ring_node['port'] for ring_node in self.chainState_ring if ring_node['id'] == id), None)

    def ID_to_key(self, id):
        return next((ring_node['public_key'] for ring_node in self.chainState_ring if ring_node['id'] == id), None)

    @staticmethod
    def totalChargedAmount(amount, message, stake=False):
        if stake: # we have stake transaction, we dont have a fee
            return amount
        else: # we have regular transaction
            """ extra 3% fee and 1BCC for each message's character """
            return 1.03*amount + len(message)
    
    def create_transaction(self, receiver, amount, message=""):
        """Creates a new transaction.

        receiver: The public_key of the receiver
        
        This method creates a new transaction
        Returns true if the transaction was created
        False otherwise

        stake argument determines if the transaction is a stake update
        """

        transaction = Transaction(
            sender_address=self.wallet.public_key,
            receiver_address=receiver,
            amount=amount,
            message=message,
            nonce=self.send_counter,
            TTL=self.chain.blocks[-1].index
        )

        # Sign the transaction
        transaction.sign_transaction(self.wallet.private_key)

        # validate the transaction (balance, amount)
        if not self.validate_transaction(transaction)[0]:
            return False

        self.send_counter += 1 # increase send counter
        # Broadcast the transaction to the whole network.
        self.broadcast_transaction(transaction)
            
        return True

    def add_transactions_to_block(self, block):
        """Add transactions to the block.

           This method adds transactions in the block
           transaction_pool_lock is already acquired
        """
        self.transaction_pool_lock.acquire()
        for i in range(self.CAPACITY):
            block.add_transaction(self.transaction_pool.popleft())
        self.transaction_pool_lock.release()
        return block

    def broadcast_transaction(self, transaction):
        """Broadcasts a transaction to the whole network.

        This is called each time a new transaction is created. In order to
        send the transaction simultaneously, each request is sent by a
        different thread. If all nodes accept the transaction, the node adds
        it in the current block. the transaction is send back to the sender as well
        """

        """ we should NOT wait for all nodes to validate the transaction """

        def thread_func(node, endpoint):
            address = 'http://' + node['ip'] + ':' + node['port']
            requests.post(address + endpoint, data=pickle.dumps(transaction))

        threads = []
        for node in self.chainState_ring:
            thread = Thread(target=thread_func, args=(
                node, '/validate_transaction'))
            threads.append(thread)
            thread.start()

        for tr in threads:
            tr.join()

        return True

    def validate_transaction(self, transaction, ring=None, validator=None, block=None):
        """Validates an incoming transaction.

        if not ring is given as argument, the node's softState_ring 
        is checked, otherwise the argument-ring

        we use softState_ring to validate a transaction cause we want
        to check the transactions not added to a block yet

        that helps us validate a block full of transactions
        where a temporary ring must be kept and according
        to that the validate transaction must be called

        The validation consists of:
        - verification of the signature.
        - check that the sender has enough balance
        - check if the nonce is seen

        Returns the tuple (validation, changed_ring)
        in other words, if the transaction is valid, and how 
        the given ring will be if the transaction is applied
        """

        if not transaction.verify_signature():
            return (False, None)

        ring = ring if ring is not None else self.softState_ring
        validator_id = validator if validator is not None else self.find_validator()
        block = block if block is not None else self.chain.blocks[-1]
        # if the block is given check its index, otherwise chain the last block of the chain
        if block.index-transaction.TTL > self.TTL_LIMIT: 
            return (False, None) # reject transaction as old one

        # negative amounts are accepted only for stake transactions
        if transaction.amount < 0:
            if transaction.receiver_address != "0":
                return (False, None)
            # if the stakes update (amount) is greater than the actual stake
            if self.ID_to_stake(self.key_to_ID(transaction.sender_address), ring) < abs(transaction.amount):
                return (False, None)
        else:
            if self.ID_to_balance(self.key_to_ID(transaction.sender_address), ring) < self.totalChargedAmount(transaction.amount, transaction.message, transaction.receiver_address == "0"):
                return (False, None)

        if transaction.nonce in self.ID_to_nonces(self.key_to_ID(transaction.sender_address), ring):
            return (False, None)

        temp_ring = deepcopy(ring)
        sender_id = self.key_to_ID(transaction.sender_address) 
        self.update_balance(sender_id, -self.totalChargedAmount(transaction.amount, transaction.message, transaction.receiver_address == "0"), temp_ring)
        self.update_nonces(sender_id, transaction.nonce, temp_ring)
        if transaction.receiver_address == "0": #stake transaction
            self.update_stake(sender_id, transaction.amount, temp_ring)
        else: # regular transaction
            receiver_id = self.key_to_ID(transaction.receiver_address)
            self.update_balance(receiver_id, transaction.amount, temp_ring)
            self.update_balance(validator_id, transaction.amount*0.03+len(transaction.message), temp_ring)
        return (True, temp_ring)

    def add_transaction_to_pool(self, transaction):
        """Appends a transaction to the pool

            If there are enough transactions >= CAPACITY
            then a block can be formed, call mine_block()
        """
        self.transaction_pool_lock.acquire()
        self.transaction_pool.append(transaction)
        if len(self.transaction_pool) >= self.CAPACITY:
            self.transaction_pool_lock.release()
            self.mint_block()
        else:
            self.transaction_pool_lock.release()

    def find_validator(self, block=None, ring=None, chain=None):
        """ Finds the validator of the block according 
            to the hash of the previous block 
            Implements Proof Of stake Algorithm

            we use chainState_ring cause the validator can be found based
            on the (up to) last block of the chain
        """

        ring = ring if ring is not None else self.chainState_ring
        chain = chain if chain is not None else self.chain
        hash = block.previous_hash if block is not None else chain.blocks[-1].current_hash
        """ find_validator is called in two cases:
            a) when a block is ready to be mined at the end of the chain
                -> then we must check the current hash of the last block to determine the seed
            b) when a block is being validated 
                -> then we must check the previous hashS of the block being validated (the current
                hash of the previous block)
        """

        total_stakes = 0
        for ring_node in ring:
            total_stakes += ring_node['stake']
        if total_stakes == 0:
            return None

        # Create a sorted list of (cumulative_probability, node_id) tuples
        cumulative_probabilities = []
        cumulative_probability = 0.0
        for ring_node in ring:
            cumulative_probability += ring_node["stake"] / total_stakes
            cumulative_probabilities.append((cumulative_probability, ring_node["id"]))

        # Draw a random number and find the corresponding node
        # Use the hash of the last block as a seed
        rng = np.random.default_rng(seed=int(hash, 16))  
        rand = rng.random()
        return next(node_id for cum_prob, node_id in cumulative_probabilities if rand <= cum_prob)

    def mint_block(self):
        """Implements the proof-of-stake.

        This methods implements the proof of stake algorithm.
        if the calling node isnt the validator false is returned
        otherwise the block is mined and broadcasted, true is returned
        """

        validator = self.find_validator()

        if (validator != self.id):
            return False

        mined_block = self.create_new_block()
        self.broadcast_block(mined_block)
        return True

    def broadcast_block(self, block):
        """
        Broadcasts a validated block in the whole network.

        This method is called each time a new block is mined. 
        The miner that mined the block does not wait for explicit 
        validation from other nodes, he adds the block to his blockchain 
        immediately upon successful mining.
        miner broadcasts it to himself as well

        when we are about to send a block we dont need to validate it,
        cause the transactions were validated while they were being received
        """

        def thread_func(node):
            address = 'http://' + node['ip'] + ':' + node['port']
            requests.post(address + '/get_block', data=pickle.dumps(block))

        threads = []
        for node in self.chainState_ring:
            thread = Thread(target=thread_func, args=(node,))
            threads.append(thread)
            thread.start()

        for tr in threads:
            tr.join()

    def validate_block(self, block, chain=None, ring=None):
        """Validates an incoming block.

            The validation consists of:
            - check that current hash is valid.
            - validate the previous hash.
            - validate all transactions of the block

            its not enough to validate each transaction separately
            we must make sure that the costs all together can be afforded

            if not ring is given as argument, the node's ring 
            is checked, otherwise the argument-ring
            same with chain

            the block is validated based on the chainState_ring

            that helps us validate a blockchain full of blocks
            where a temporary ring must be kept and according
            to that the validate block must be called

            returns tuple (boolean, ring)
            true if the block is validated, false otherwise
            'ring' is the ring if the changes of the block 
            is applied to the current state (self.ring)
        """

        ring = ring if ring is not None else self.chainState_ring
        chain = chain if chain is not None else self.chain

        if block.current_hash != block.get_hash(): 
            return (False, None)
        if block.previous_hash != chain.blocks[-1].current_hash:
            return (False, None)
        if self.find_validator(block, ring, chain) != self.key_to_ID(block.validator):
            return (False, None)
        
        temp_ring = deepcopy(ring)
        for transaction in block.transactions:
            (validation, temp_ring) = self.validate_transaction(transaction, temp_ring, validator=self.key_to_ID(block.validator), block=block)
            if validation == False:
                return (False, None)
        return (True, temp_ring)

    def add_block_to_chain(self, block, new_ring):
        """ Adds a block at the end of the chain
            alters the chainState_ring but 
                   the softState_ring as well.
            Everytime a block is added to the chain
            of the current node, the softState becomes
            identical to the chainState. However, if 
            after filter_transactions() transactions remain 
            in the transaction pool, they must get validated
            again and the softState must adjust accordingly  
        """

        # If the node is the recipient or the sender of the transaction,
        # it adds the transaction in its wallet.
        for tr in block.transactions:
            if (tr.receiver_address == self.wallet.public_key or \
                tr.sender_address == self.wallet.public_key):
                for w_tr in self.wallet.transactions:
                    if w_tr[0] == tr:
                        w_tr[1] = block.validator
                        w_tr[2] = "Confirmed"
                        break
                    
        self.chain.blocks.append(block)
        self.chainState_ring = deepcopy(new_ring)
        self.softState_ring = deepcopy(new_ring)

    def filter_transactions(self, mined_block):
        """ When a block is got, validated and added to the chain,
            we must remove its transactions from the transaction pool.
            Additionally, if transactions remain in the transaction pool,
            we should change the softState accordingly
        """
        self.transaction_pool_lock.acquire()
        try:
            
            # Remove transactions that are in the mined block
            self.transaction_pool = deque(
                tr for tr in self.transaction_pool if tr not in mined_block.transactions
            )
            # MUST VALIDATE THE TRANSACTIONS REMAINED IN THE TRANSACTION POOL
            # AND CHANGE THE SOFT STATE
            transactions_to_remove = [] # list to collect transactions that need to be removed
            for tr in self.transaction_pool:
                (validation, changed_ring) = self.validate_transaction(tr)
                # if the transaction is not valid yet remove it
                # check if the transaction is old, if it is remove it
                if validation == True and mined_block.index-tr.TTL <= self.TTL_LIMIT: 
                    self.softState_ring = changed_ring
                else: # not valid or old, remove it
                    transactions_to_remove.append(tr)

            # Remove the transactions that are invalid or too old
            for tr in transactions_to_remove:
                self.transaction_pool.remove(tr)
        finally:
            #pass
            self.transaction_pool_lock.release()

    def checkOutOfOrderBlocks(self):
        """ When a block is got, validated and added to the chain,
            and after the transaction filtering, we must check the 
            deque that contained out of order blocks if now the blocks
            can get in order. If there is the next block in the queue, 
            remove it and send it again to myself
        """
        # Use a list to track blocks to be removed
        blocks_to_remove = []
        for outOfOrderBlock in self.outOfOrderBlocks:
            if outOfOrderBlock.previous_hash == self.chain.blocks[-1].current_hash:
                blocks_to_remove.append(outOfOrderBlock)
                address = 'http://' + self.ID_to_IP(self.id) + ':' + self.ID_to_port(self.id)
                requests.post(address + '/get_block', data=pickle.dumps(outOfOrderBlock))
                break
        
        # Remove the identified blocks
        for block in blocks_to_remove:
            self.outOfOrderBlocks.remove(block)

    def share_ring(self, ring_node):
        """Shares the node's ring (neighbor nodes) to a specific node.

        This function is called for every newcoming node in the blockchain.
        """

        address = 'http://' + ring_node['ip'] + ':' + ring_node['port']
        requests.post(address + '/get_ring',
                      data=pickle.dumps(self.chainState_ring))

    def validate_chain(self, chain):
        """Validates all the blocks of a chain.

        This function is called every time a node receives a chain after
        a conflict.

        Note: validate_chain() calls validate_block() it calls validate_transaction()
        the validate_chain will work only for nodes that have zero knowledge about the 
        block chain, otherwise they should clear the nonces lists and etc.

        returns tuple (boolean, ring)
        true if the chain is validated, false otherwise
        'ring' is the ring if the changes of the chain
        is applied to the initial state (self.ring)
        """
        temp_ring = deepcopy(self.chainState_ring)
        for ring_node in temp_ring:
            ring_node['balance'] = 0
            ring_node['nonces'] = []
            ring_node['stake'] = 1
        blocks = chain.blocks
        for i in range(len(blocks)):
            if i == 0:
                if (blocks[i].previous_hash != 1 or
                    blocks[i].current_hash != blocks[i].get_hash() or 
                    blocks[i].transactions[0].sender_address != "0" or 
                    blocks[i].transactions[0].receiver_address != self.ID_to_key(0) or
                    blocks[i].transactions[0].amount != 1000 * len(temp_ring) or
                    blocks[i].transactions[0].message != "" or 
                    blocks[i].transactions[0].nonce != 0):
                    return (False, None)
                self.update_balance(0, 1000 * len(temp_ring), temp_ring)
                self.update_nonces(0, 0, temp_ring)
            else:
                (validation, temp_ring) = self.validate_block(blocks[i], temp_ring)
                if not validation:  
                    return (False, None)
        return (True, temp_ring)

    def share_chain(self, ring_node):
        """Shares the node's current blockchain to a specific node.

        This function is called whenever there is a conflict and the node is
        asked to send its chain by the ring_node.
        """
        address = 'http://' + ring_node['ip'] + ':' + ring_node['port']
        requests.post(address + '/get_chain', data=pickle.dumps(self.chain))

    def stake(self, amount):
        """ updates the stake of the current node 
            stake updates are transactions with 0 as the receiver address 
            if amount is positive, coins from the account's balance is held
            otherwise coins from the account's stake is freed
        """
        self.create_transaction(self, "0", amount, message="")