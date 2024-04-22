<p align="center">
    <br>
    <img src="etc/logo.png" alt="Blockchat" width="400"/>
    <br>
<p>

<h3 align="center">
A blockchain system for messaging and money transfer
</h3>


## About the project

BlockChat is a distributed system designed for secure and reliable exchange of messages and cryptocurrency transactions. Utilizing blockchain technology, BlockChat ensures safe peer-to-peer interactions without the need for a central authority. It utilizes cryptography techniques for transaction verification and the Proof-of-Stake (PoS) algorithm for consensus. <br>
Each user has a wallet with a private key for sending BCCs and messages, and a public key for receiving them. New transactions are broadcast across the network and validated by all nodes. The PoS algorithm indicates which node will be the validator, who will gather the transactions up to that point, add them to a block, validate the block and broadcast it to the network in order to be added to the blockchain. Validators receive transaction fees as a reward for their service.


## Deliverables

1. A REST API that implements the functionality of BlockChat and is placed in `src` directory.
2. A CLI client placed in `src/client.py`.
3. A report going over the system's architecture and the results of the required experiments.

## Setup and Usage

- Install all necessary requirements

    `pip install -r requirements.txt`

- For each of the N nodes, setup a BlockChat backend by running run.py. Make sure to designate one, and *only* one, of the nodes as the **bootstrap** node by using the `-bootstrap` argument:

    ```
    $ python src/run.py [-h] -p P -n N -capacity CAPACITY [-bootstrap]
    
    optional arguments:
      -h, --help          show the help message and exit

    required arguments:
      -p P                port to listen on
      -n N                number of nodes in the blockchain
      -capacity CAPACITY  capacity of a block

    optional_arguments:
      -bootstrap          set if the current node is the bootstrap
    ```

    > **_NOTE:_** The bootstrap node should be the first to be initialized. Nodes won't get initialized before the bootstrap has started running and won't connect to the network.

    > **_NOTE:_** Argument `-p` should be unique for each node, while arguments `-n` and `-capacity` should remain consistent. Arguments `bootstrap`, `-n` and `-capacity` can be specified only ***once*** and can't be changed after the bootstrap node has started running.
    
    > **_NOTE:_** The file `src/config.py` should contain the ip address of the bootstrap node and the variable LOCAL should change in case of running in a remote server.

- For each node, you can now open another terminal and run the client:

     ```
     $ python src/client.py [-h] -p P

    optional arguments:
      -h, --help  show the help message and exit

    required arguments:
      -p P        port of the node
    ```

    > **_NOTE:_** Each execution of the code above represents a CLI client for the node corresponding to the specified port P.


## Technologies used

1. The REST API is written in Python 3.6 using the following libraries: 
    - Flask
    - Flask-Cors
    - pycryptodome
    - requests
    - PyInquirer

## Evaluation of the system

We evaluate the performance and the scalability of BlockChat by running the system in [okeanos](https://okeanos-knossos.grnet.gr/home/) and perform from each node 100 transactions to the system. The transactions are placed in `/test/transactions` and the script for executing them in `test/tester.py`. The results of the evaluation can be seen in the report.

## Project Structure

- `src/`: Source code of the REST backend and CLI client.
- `test/`: Files regarding the evaluation of the system.

## Contributors

Developed by

<p align="center">
    <a href="https://github.com/petrosrapto"> <img src="etc/petrosrapto.png" width="10%"></a>  <a href="https://github.com/kostis25"><img src="etc/kostis25.png" width="10%"></a>  <a href="https://github.com/GrigoriosTsenos"><img src="etc/GrigoriosTsenos.png" width="10%"></a>
<p>
    
as a semester project for the Distributed Systems course 2023-2024 of ECE NTUA.
