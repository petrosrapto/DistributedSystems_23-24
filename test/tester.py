import os
import requests
import socket
import pickle
import sys
import time

from argparse import ArgumentParser
from texttable import Texttable

# Add config file in our path.
sys.path.insert(0, '../src')
import config

# Get the IP address of the device
if config.LOCAL:
    IPAddr = '127.0.0.1'
else:
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)

total_time = 0
num_transactions = 0

def start_transactions():
    """This function makes the transactions in a given text file"""

    global total_time
    global num_transactions
    address = 'http://' + IPAddr + ':' + str(port) + '/api/create_transaction'
    with open(input_file, 'r') as f:
        for line in f:
            # Get the info of the transaction.
            line = line.replace('\n','').split(" ", 1)
            receiver_id = int(line[0][2])

            if (receiver_id > num_clients) :
                receiver_id -= 5
            if (receiver_id == id) :
                if (id == 4) :
                    receiver_id = 3
                else :
                    receiver_id += 1

            message = line[1]
            transaction = {'receiver': receiver_id, 'amount': 0, 'message': message}
    
            print('\nSending message \'%s\' to the node with id %d ...' % (message, receiver_id))
    
            # Send the current transaction.
            try:
                start_time = time.time()
                response = requests.post(address, data=transaction)
                end_time = time.time() - start_time
                message = response.json()["message"]
                if response.status_code == 200:
                    total_time += end_time
                    num_transactions += 1
                    print("\n" + message + '\n')
                elif response.status_code == 400:
                    print("Error: " + message + '\n')
            except:
                exit("\nNode is not active. Try again later.\n")

    input("\nWhen all transactions in the network are over, press Enter to continue...\n")

    try:
        address = 'http://' + IPAddr + ':' + str(port) + '/api/get_my_transactions'
        response = requests.get(address)
        data = pickle.loads(response._content)
    except:
        exit("\nSomething went wrong while receiving your transactions.\n")

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t',  # text
                          't',  
                          't',  
                          't',
                          't',
                          't']) 
    table.set_cols_align(["c", "c", "c", "c", "c", "c"])
    headers = ["Sender ID", "Receiver ID", "BCC\'s sent", "Message", "Validator", "Status"]

    rows = []
    rows.append(headers)
    rows.extend(data)
    table.add_rows(rows)
    print(table.draw() + "\n")

    try:
        address = 'http://' + IPAddr + ':' + str(port) + '/api/get_balance'
        response = requests.get(address).json()
        message = str(response['message'])
        print("Current Balance: " + message + " BCCs\n")
    except:
        exit("\nSomething went wrong while receiving your balance.\n")

    try:
        address = 'http://' + IPAddr + ':' + str(port) + '/api/get_metrics'
        response = requests.get(address).json()
        num_blocks = str(response['num_blocks'])
        capacity = str(response['capacity'])
        transactions1 = (float(num_transactions))
        time1 = (float(total_time))
        blocks1 = (float(num_blocks))
    
        print("Total transactions: " + str(num_transactions))
        print("Total blocks (without genesis): " + str(int(num_blocks) - 1))
        print("Total time: " + str(total_time))
        print("Capacity: " + capacity)
        print("Node Stake: " + str(nstake))
        if (int(total_time) == 0) or (int(num_blocks) == 0):
            print("Error: time or blocks are 0")
        else:
            throughput = transactions1/time1
            block_time = time1/blocks1
            print("Throughput (transactions/time): " + str(throughput))
            print("Block Time: " + str(block_time) + "\n")

    except:
        exit("\nSomething went wrong while receiving the blockchain metrics.\n")

def get_id():
    address = 'http://' + IPAddr + ':' + str(port) + '/api/get_id'
    response = requests.get(address).json()
    message = response['message']
    return message

def get_stake():
    address = 'http://' + IPAddr + ':' + str(port) + '/api/get_stake'
    response = requests.get(address).json()
    message = response['message']
    return message

if __name__ == "__main__":
    # Define the argument parser.
    parser = ArgumentParser(
        description='Makes the transactions listed in a text file.')

    required = parser.add_argument_group('required arguments')
    
    required.add_argument(
        '-input', help='Path to the directory of the transactions. Each text file contains one transaction per line in the following format:\nid[#] message, e.g. id8 The Universe!', required=True)
    
    required.add_argument(
        '-p', type=int, help='Port that the api is listening on', required=True)
    
    required.add_argument(
        '-c', type=int, help='Number of clients (5 or 10)', required=True)

    # Parse the given arguments.
    args = parser.parse_args()
    input_dir = args.input
    port = args.p
    num_clients = (args.c)-1

    input("\n Press Enter to start the transactions...\n")

    # Find the corresponding transaction file.
    id = get_id()
    nstake = get_stake()

    input_file = os.path.join(input_dir, 'trans' + str(id) + '.txt')

    print('Reading %s ...' % input_file)

    start_transactions()
