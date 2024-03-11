import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA

class Wallet:
    """
    The wallet of a node in the network.

    Attributes:
        private_key (int): the private key of the node.
        public_key (int): the public key of the node (also serves as the node's address).
        transactions (list of lists): a list of lists that contains the transactions of the node
                             as list (transaction, validator, status)
                             When a transaction is validated and is relevant to the current node,
                             its added to the wallet as [transaction, "None", "Unconfirmed"]
                             When a transaction is added to the blockchain, the transactions
                             alter to [transaction, validator, "Confirmed"]
        parent_node (reference): pointer to the parent node
    """

    def __init__(self, node):
        """Inits a Wallet - called only inside Node init"""
        # Generate a private key of key length of 1024 bits.
        key = RSA.generate(1024)

        self.private_key = key.exportKey().decode('ISO-8859-1')
        # Generate the public key from the above private key.
        self.public_key = key.publickey().exportKey().decode('ISO-8859-1')
        self.transactions = []
        self.parent_node = node

    def __str__(self):
        """Returns a string representation of a Wallet object."""
        return str(self.__class__) + ": " + str(self.__dict__)

    def get_balance(self):
        """Returns the total balance of the wallet"""
        return self.parent_node.ID_to_balance(self.parent_node.id, self.parent_node.softState_ring)
    
    def get_stake(self):
        """Returns the stake of the wallet"""
        return self.parent_node.ID_to_stake(self.parent_node.id, self.parent_node.softState_ring)