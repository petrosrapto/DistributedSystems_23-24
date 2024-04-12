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

1. A rest api that implements the functionality of BlockChat and is placed in `src` directory.
2. A cli client placed in `src/tester.py`.
3. A web app in `webapp` directory.

## Setup/Usage

- Install all necessary requirements

    `pip install -r requirements.txt`

- Setup BlockChat backend by running the rest api of n nodes.

    ```
    $ python src/run.py --help
    usage: run.py [-h] -p P -n N -capacity CAPACITY [-bootstrap]

    Rest api of blockchat.

    optional arguments:
      -h, --help          show this help message and exit

    required arguments:
      -p P                port to listen on
      -n N                number of nodes in the blockchain
      -capacity CAPACITY  capacity of a block

    optional_arguments:
      -bootstrap          set if the current node is the bootstrap
    ```
    
    > **_NOTE:_** The file `src/config.py` should contain the ip address of the bootstrap node and the variable LOCAL should change in case of running in a remote server. In addition, each execution of the code above represents a node in the system. You have to execute the code N times, where N is the number of nodes you will use for the system as specified while setting up the bootstrap node (which can only be set **once**).

- Run a CLI client:

     ```
     $ python src/client.py --help

    usage: client.py [-h] -p P

    CLI client of blockchat.

    optional arguments:
      -h, --help  show this help message and exit

    required arguments:
      -p P        port to listen on
    ```

    > **_NOTE:_** Each execution of the code above represents a CLI client for the corresponding node at the specified port P.


## Technologies used

1. The rest api is written in Python 3.6 using the following libraries: 
    - Flask
    - Flask-Cors
    - pycryptodome
    - requests
    - PyInquirer
2. The webapp is developed using Django 3.0.4 and Python 3.6

## Evaluation of the system

We evaluate the performance and the scalability of BlockChat by running the system in [okeanos](https://okeanos-knossos.grnet.gr/home/) and perform from each node 100 transcations to the system. The transactions are placed in `/test/transactions` and the scipt for executing them in `test/tester.py`. 

## Project Structure

- `src/`: Source code of the rest backend and cli client.
- `test/`: Files regarding the evaluation of the system.
- `webapp/`: Files about the web app.

## Contributors

Developed by

<p align="center">
    <a href="https://github.com/petrosrapto"> <img src="etc/petrosrapto.png" width="10%"></a>  <a href="https://github.com/kostis25"><img src="etc/kostis25.png" width="10%"></a>  <a href="https://github.com/GrigoriosTsenos"><img src="etc/GrigoriosTsenos.png" width="10%"></a>
<p>
    
as a semester project for the Distributed Systems course 2023-2024 of ECE NTUA.
