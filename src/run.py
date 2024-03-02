import time
import socket
import requests
import threading

import config
import endpoints
from endpoints import node, rest_api
from transaction import Transaction

from flask_cors import CORS
from argparse import ArgumentParser
from flask import Flask

# All nodes are aware of the ip and the port of the bootstrap
# node, in order to communicate with it when entering the network.
BOOTSTRAP_IP = config.BOOTSTRAP_IP
BOOTSTRAP_PORT = config.BOOTSTRAP_PORT

# Get the IP address of the device.
if config.LOCAL:
    IP_ADDR = BOOTSTRAP_IP
else:
    hostname = socket.gethostname()
    """ calls the gethostname() function from the socket module, 
    which returns the hostname of the machine where the Python 
    interpreter is currently executing. The hostname is a label 
    assigned to a device connected to a computer network that 
    is used to identify the device in various forms of 
    electronic communication. """
    IP_ADDR = socket.gethostbyname(hostname)
    """ takes the hostname obtained from the previous step and uses the 
    gethostbyname() function, also from the socket module, to convert this 
    hostname into its corresponding IPv4 address. This function queries the 
    DNS system (or the system's hosts file) to resolve the hostname to its IP address. 
    The resulting IP address is stored in the IPAddr variable. """


# Define the flask environment and register the blueprint with the endpoints.
app = Flask(__name__) # initializes a new Flask application from root path
app.register_blueprint(rest_api) # register a blueprint
""" Blueprints are a way to organize a group of related routes and other 
app functionalities. By splitting an application into blueprints, you can modularize 
your code, improve readability, and facilitate reuse across the application or even 
between different applications. """
CORS(app) # enables Cross-Origin Resource Sharing (CORS) for the entire Flask application
""" CORS is a security feature that allows or restricts resources on a web server to be 
requested from another domain. By default, web browsers enforce the same-origin policy, 
which prevents a web page from making requests to a different domain than the one that 
served the web page. Using CORS(app) from the Flask-CORS extension makes your Flask 
application accept requests from clients hosted on different origins (domains, schemes, 
or ports), which is essential for API services that are consumed by web applications 
hosted on different domains. """

""" When a Python file (script) is executed, Python sets the __name__ variable to "__main__" 
if the file is being run as the main program. If the file is imported as a module into another 
file, __name__ is set to the module's name. """

if __name__ == '__main__':
    # Define the argument parser.
    parser = ArgumentParser(description='Rest api of BlockChat.')

    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional_arguments')

    required.add_argument(
        '-p', type=int, help='port to listen on', required=True)
    required.add_argument(
        '-n', type=int, help='number of nodes in the blockchain', required=True)
    required.add_argument('-capacity', type=int,
                          help='block\'s capacity of transactions', required=True)
    optional.add_argument('-bootstrap', action='store_true',
                          help='set if the current node is the bootstrap')

    # Parse the given arguments.
    args = parser.parse_args()
    PORT = args.p
    endpoints.N = args.n
    node.CAPACITY = args.capacity
    IS_BOOTSTRAP = args.bootstrap
    endpoints.IS_BOOTSTRAP = IS_BOOTSTRAP

    if (IS_BOOTSTRAP):
        """
        The bootstrap node (id = 0):
            - registers itself in the ring.
            - creates the genesis block.
            - creates the first transaction and adds it in the genesis block.
            - adds the genesis block in the blockchain (no validation).
            - starts listening in the desired port.
        """
        node.id = 0
        node.register_node_to_ring(node.id, BOOTSTRAP_IP, BOOTSTRAP_PORT, node.wallet.public_key)

        # Defines the genesis block.
        gen_block = node.create_new_block(genesis=True)

        # Adds the first and only transaction in the genesis block.
        first_transaction = Transaction(sender_address="0", receiver_address=node.wallet.public_key, 
            amount=1000 * endpoints.N, message="", nonce=0)
        
        gen_block.add_transaction(first_transaction)
        gen_block.set_hash()
        node.update_balance(0, 1000 * endpoints.N, node.ring)
        node.wallet.transactions.append(first_transaction)
        node.send_counter += 1
        # Add the genesis block in the chain.
        node.chain.blocks.append(gen_block)

        # Listen in the specified address (ip:port)
        app.run(host=BOOTSTRAP_IP, port=BOOTSTRAP_PORT)
    else:
        """
        The rest nodes (id = 1, .., n-1):
            - communicate with the bootstrap node in order to register them.
            - starts listening in the desired port.
        """

        register_address = 'http://' + BOOTSTRAP_IP + \
            ':' + BOOTSTRAP_PORT + '/register_node'

        def thread_function():
            time.sleep(2)
            response = requests.post(
                register_address,
                data={'public_key': node.wallet.public_key,
                      'ip': IP_ADDR, 'port': PORT}
            )

            if response.status_code == 200:
                print("Node initialized")
            else:
                print("Node didnt initialize")
                print("Response: ", response.json())
                print("Exiting...")
                exit()
            node.id = response.json()['id']

        req = threading.Thread(target=thread_function, args=())
        """ A new thread object is created, with thread_function 
        set as the target function to be executed by the thread. 
        This allows the registration process to occur independently 
        of the main program flow, enabling the Flask server to 
        start without waiting for registration to complete. """
        req.start()

        # Listen in the specified address (ip:port)
        app.run(host=IP_ADDR, port=PORT)
        """ the Flask web server is started on the IP address (IPAddr) 
        and port number (port) specified. This server listens for incoming 
        HTTP requests """