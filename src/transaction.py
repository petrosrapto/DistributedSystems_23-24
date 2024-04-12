import json
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss

class Transaction:
    """
    A BlockChat transaction in the blockchain

    Attributes:
        sender_address (int): the public key of the sender's wallet.
        receiver_address (int): the public key of the receiver's wallet.
        amount (int): the sent amount of BCCs 
                      it DOES NOT include fees and message costs
        message (string): the sent message, defaults to empty string "" 
        nonce (int): counter of transactions made by the sender
        transaction_id (int): hash of the transaction.
        TTL (int): (Time-To-Live) is the index of the last block of the node's chain when the transaction
                    is created. If the transaction remain unconfirmed in the network more than a limit (compare the TTL
                    with the index of the last block of the current chain) the transaction is rejected
        signature (int): signature that verifies that the owner of the wallet created the transaction.
    """

    def __init__(self, sender_address, receiver_address, amount, message, nonce, TTL):
        """Inits a Transaction"""
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount 
        self.message = message
        self.nonce = nonce
        self.TTL = TTL
        self.transaction_id = self.get_hash()
        self.signature = None

    def __str__(self):
        """Returns a string representation of a Transaction object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    def __eq__(self, other):
        """Overrides the default method for comparing Transaction objects.
        Two transactions are equal if their current_hash is equal.
        """
        return self.transaction_id == other.transaction_id

    def to_list(self):
        """Converts a Transaction object into to list."""
        return [self.sender_address, self.receiver_address, self.amount, self.message]

    def get_hash(self):
        """Computes the hash of the transaction."""
        # Serialize the transaction into a JSON string

        transaction_list = [self.sender_address, 
            self.receiver_address, self.amount, self.message, self.nonce]

        serialized_transaction = json.dumps(transaction_list, sort_keys=True)
        # Hash the serialized transaction including the data
        return SHA256.new(serialized_transaction.encode("ISO-8859-2")).hexdigest()

    def sign_transaction(self, private_key):
        """Sign the current transaction with the given private key."""
        transaction_hash = SHA256.new()
        transaction_hash.update(bytes.fromhex(self.transaction_id))

        key = RSA.importKey(private_key.encode("ISO-8859-1"))
        self.signature = pss.new(key).sign(transaction_hash).hex()

    def verify_signature(self):
        """Verifies the signature of a transaction."""
        transaction_hash = SHA256.new()
        transaction_hash.update(bytes.fromhex(self.transaction_id))
        key = RSA.importKey(self.sender_address.encode('ISO-8859-1'))
        try:
            pss.new(key).verify(transaction_hash, bytes.fromhex(self.signature))
            return True
        except (ValueError, TypeError):
            return False
