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
    """This function makes the transactions of the text file"""

    global total_time
    global num_transactions
    address = 'http://' + IPAddr + ':' + str(port) + '/api/create_transaction'
    with open(input_file, 'r') as f:
        for line in f:
            # Get the info of the transaction.
            line = line.split()
            receiver_id = int(line[0][2])
          
            if (receiver_id > num_clients) :
              receiver_id -= 5
            if (receiver_id == id) :
              if (id == 4) :
                receiver_id = 3
              else :
                receiver_id += 1
          
            message = line[1:]
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
                print("\n" + message + '\n')  #Both are called message?
            except:
                exit("\nNode is not active. Try again later.\n")

    input("\nWhen all transactions in the network are over, press Enter to get your final balance ...\n")

    try:
        address = 'http://' + IPAddr + ':' + \
            str(port) + '/api/get_my_transactions'
        response = requests.get(address)
        data = pickle.loads(response._content)
    except:
        exit("\nSomething went wrong while receiving your transactions.\n")

    transactions = []
    balance = 0
    for tr in data:
        if tr[0] == IPAddr:
            transactions.append(['Send', "Me", tr[1], tr[2], tr[3], ((0.03*int(tr[2])) + len(tr[3]))])
            balance -= int(tr[2])
        elif tr[1] == IPAddr:
            transactions.append(['Receive', tr[0], "Me", tr[1], tr[2], tr[3], ((0.03*int(tr[2])) + len(tr[3]))])
            balance += int(tr[2])
        else:
            exit('Error while deciphering your transactions.')

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t', 
                          't', 
                          't', 
                          't', 
                          't', # text
                          'a']) # automatic (try to use the most appropriate datatype)
    table.set_cols_align(["c", "c", "c", "c", "c", "c"]) #column centered
    headers = ["Type", "From", "To", "Amount", "Message", "Cost"]
    rows = []
    rows.append(headers)
    rows.extend(transactions)
    table.add_rows(rows)
    print(table.draw() + "\n")

    try:
        address = 'http://' + IPAddr + ':' + str(port) + '/api/get_balance'
        response = requests.get(address).json()
        message = response['message']
        balance = str(response['balance'])
        print('\n' + message + ' ' + balance + '\n')
        print("The balance calculated based on the transactions in the table above is: " +
              str(balance) + " BCCs\n")
    except:
        exit("\nSomething went wrong while receiving your balance.\n")

    try:
        address = 'http://' + IPAddr + ':' + str(port) + '/api/get_metrics'
        response = requests.get(address).json()
        num_blocks = response['num_blocks'] - 1
        capacity = response['capacity']
        with open('./results', 'a') as f:
            f.write('Total transactions: %d\n' %num_transactions)
            f.write('Total blocks (without genesis): %d\n' %num_blocks)
            f.write('Total time: %f\n' %total_time)
            f.write('Capacity: %d\n' %capacity)
            f.write('Node Stake: %s\n' %nstake)
            f.write('Throughput (transactions/time): %f\n' %(float(num_transactions)/total_time))
            f.write('Block Time: %f\n' %(total_time/float(num_blocks)))
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