import json
from time import time
from Crypto.Hash import SHA256

class Block:
    """
    A block in the blockchain.

    Attributes:
        index (int): the sequence number of the block.
        timestamp (float): timestamp of the creation of the block.
        transactions (list): list of all the transactions in the block.
        validator (int): public key of the node that validated the block
        previous_hash (hash object): hash of the previous block in the blockchain.
        current_hash (hash object): hash of the block.
    """

    def __init__(self, index, previous_hash, validator=None):
        """Inits a Block"""
        self.index = index
        self.timestamp = time()
        self.transactions = []
        self.validator = validator
        self.previous_hash = previous_hash
        self.current_hash = None

    def __str__(self):
        """Returns a string representation of a Block object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    def __eq__(self, other):
        """Overrides the default method for comparing Block objects.

        Two blocks are equal if their current_hash is equal.
        """

        return self.current_hash == other.current_hash

    def get_hash(self):
        """Computes the current hash of the block."""

        # We should compute current hash without using the
        # field self.current_hash.
        block_list = [self.index, self.timestamp, [
            tr.transaction_id for tr in self.transactions], self.validator, self.previous_hash]
        
        block_dump = json.dumps(block_list.__str__())
        return SHA256.new(block_dump.encode("ISO-8859-2")).hexdigest()

    def set_hash(self):
        """Sets current hash of the block."""
        self.current_hash = self.get_hash()

    def add_transaction(self, transaction):
        """Adds a new transaction in the block."""
        self.transactions.append(transaction)