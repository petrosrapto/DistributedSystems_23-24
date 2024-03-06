import requests
import pickle
import os

from PyInquirer import style_from_dict, Token, prompt
from PyInquirer import Validator, ValidationError
from argparse import ArgumentParser
from texttable import Texttable
from time import sleep

# Get the IP address of the device
try:
    from run import IP_ADDR
except:
    print("Node's backend is not running")
    print("Start the backend and then try connecting to CLI")
    print("Exiting...")
    quit()

style = style_from_dict({
    Token.QuestionMark: '#E91E63 bold',
    Token.Selected: '#673AB7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#2196f3 bold',
    Token.Question: '',
})

class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))

class PositiveNumberValidator(Validator):
    def validate(self, document):
        try:
            if int(document.text) < 0:
                raise ValidationError(
                    message="You gave negative number, try again",
                    cursor_position=len(document.text))
        except ValueError:
            raise ValidationError(
                message='Please enter a non-negative integer',
                cursor_position=len(document.text))

def HomeOrExit():
    HomeOrExit_q = [
        {
            'type': 'list',
            'name': 'option',
            'message': 'What do you want to do?',
            'choices': ['Home', 'Exit'],
            'filter': lambda val: val.lower()
        }]
    HomeOrExit_a = prompt(HomeOrExit_q)['option']
    return HomeOrExit_a


def client():
    print('Initializing node\'s CLI...\n')
    sleep(2)
    print("Node\'s CLI initialized!\n")
    while True:
        print("----------------------------------------------------------------------")
        method_q = [
            {
                'type': 'list',
                'name': 'method',
                'message': 'What would you like to do?',
                'choices': ['New transaction', 'Update Stake', 'View last transactions', 'Show balance and stake', 'Help', 'Exit'],
                'filter': lambda val: val.lower()
            }]
        method_a = prompt(method_q, style=style)["method"]
        os.system('cls||clear')
        if method_a == 'new transaction':
            print("New transaction!")
            print(
                "----------------------------------------------------------------------")
            print("Keep in mind that you will be charged 3%% extra fee according to the")
            print("amount of BCCs you want to send plus 1BCC for each sent message character")
            transaction_q = [
                {
                    'type': 'input',
                    'name': 'receiver',
                    'message': 'Receiver (type receiver\'s id):',
                    'validate': PositiveNumberValidator,
                    'filter': lambda val: int(val)
                },
                {
                    'type': 'input',
                    'name': 'amount',
                    'message': 'Amount of BCC\'s to send (put 0 otherwise):',
                    'validate': PositiveNumberValidator, # the amount can be 0
                    'filter': lambda val: int(val)
                },
                {
                    'type': 'input',
                    'name': 'message',
                    'message': 'Message to send (optional):',
                    # No 'validate' key here, allowing for any input including empty strings
            }]
            transaction_a = prompt(transaction_q, style=style)
            if transaction_a["amount"] == 0 and transaction_a.get("message", "") == "":
                print("You cant create a transaction with zero BCCs transferred and empty message, aborting...\n")
                continue
            print("\nConfirmation:")
            confirmation_message = 'Do you confirm the below?\n' + 'Receiver node: ' + str(transaction_a["receiver"]) + '\n' + 'Amount of BCCs: ' + str(transaction_a["amount"]) + '\n'
            """ .get() safely access the "message" key in the 
            transaction_a dictionary. It defaults to an 
            empty string ("") if the key does not exist. """
            if transaction_a.get("message", "") != "":
                confirmation_message += 'Message: ' + transaction_a["message"] + '\n'
            confirmation_q = [
                {
                    'type': 'confirm',
                    'name': 'confirm',
                    'message': confirmation_message,
                    'default': False
                }
            ]
            confirmation_a = prompt(confirmation_q)["confirm"]
            if confirmation_a:
                address = 'http://' + IP_ADDR + ':' + \
                    str(PORT) + '/api/create_transaction'
                try:
                    response = requests.post(
                        address, data=transaction_a).json()
                    message = response["message"]
                    print("\n" + message + '\n')
                    if "balance" in response:
                        balance = response["balance"]
                        print("----------------------------------")
                        print("Your current balance is: " +
                                str(balance) + " BCCs")
                        print("Keep in mind that the balance isn't updated until")
                        print("the transactions sent are inserted to a block and")
                        print("added to the blockchain")
                        print("----------------------------------\n")
                except:
                    print("\nNode is not active. Try again later.\n")
                if HomeOrExit() == 'exit':
                    break
                else:
                    os.system('cls||clear')
            else:
                print("\nTransaction aborted.")

        elif method_a == 'update stake':
            print("Update stake")
            print(
                "----------------------------------------------------------------------")
            print("Give the additional amount that will be held from your balance as stake")
            print("If you give negative amount then that amount will be freed from stake and added to your balance")
            transaction_q = [
                {
                    'type': 'input',
                    'name': 'amount',
                    'message': 'Amount of BCC\'s to be (+)held/(-)freed from balance to stake:',
                    'validate': NumberValidator, 
                    'filter': lambda val: int(val)
                }]
            transaction_a = prompt(transaction_q, style=style)
            print("\nConfirmation:")
            if transaction_a["amount"] > 0:
                confirmation_message = str(transaction_a["amount"]) + ' additional BCCs will be held from your balance as stake' 
            else:
                confirmation_message = str(abs(transaction_a["amount"])) + ' BCCs will be freed from stake and added to your balance' 

            confirmation_q = [
                {
                    'type': 'confirm',
                    'name': 'confirm',
                    'message': confirmation_message,
                    'default': False
                }
            ]
            confirmation_a = prompt(confirmation_q)["confirm"]
            if confirmation_a:
                address = 'http://' + IP_ADDR + ':' + \
                    str(PORT) + '/api/create_transaction'
                try:
                    transaction_a["stake"] = "true"
                    response = requests.post(
                        address, data=transaction_a).json()
                    message = response["message"]
                    print("\n" + message + '\n')
                    if "balance" and "stake" in response:
                        balance = response["balance"]
                        print("----------------------------------")
                        print("Your current balance is: " +
                                str(balance) + " BCCs")
                        stake = response["stake"]
                        print("Your current stake is: " +
                                str(stake) + " BCCs")
                        print("Keep in mind that the balance and stake arent updated until")
                        print("the transactions sent are inserted to a block and")
                        print("added to the blockchain")
                        print("----------------------------------\n")
                except:
                    print("\nNode is not active. Try again later.\n")
                if HomeOrExit() == 'exit':
                    break
                else:
                    os.system('cls||clear')
            else:
                print("\nTransaction aborted.")

        elif method_a == 'view last transactions':
            print("Last transactions (last valid block in the blockchain)")
            print(
                "----------------------------------------------------------------------\n")
            address = 'http://' + IP_ADDR + ':' + \
                str(PORT) + '/api/view_block'
            try:
                response = requests.get(address)
                data = pickle.loads(response._content)
                table = Texttable()
                table.set_deco(Texttable.HEADER)
                table.set_cols_dtype(['t',  # text
                                      't',  # text
                                      't',  # text
                                      't',  # text
                                      't'])  # text
                table.set_cols_align(["c", "c", "c", "c", "c"])
                headers = ["Sender ID", "Receiver ID",
                           "BCC\'s sent", "Message", "Validator ID"]
                
                # BCCs sent does not include fees
                rows = []
                rows.append(headers)
                rows.extend(data)
                table.add_rows(rows)
                print(table.draw() + "\n")
            except:
                print("Node is not active. Try again later.\n")
            if HomeOrExit() == 'exit':
                break
            else:
                os.system('cls||clear')
        elif method_a == 'show balance and stake':
            print("Your balance and stake")
            print(
                "----------------------------------------------------------------------\n")
            try:
                address = 'http://' + IP_ADDR + ':' + str(PORT) + '/api/get_balance'
                response = requests.get(address).json()
                message = str(response['message'])
                print("Your balance: " + message + ' BCCs\n')
                address = 'http://' + IP_ADDR + ':' + str(PORT) + '/api/get_stake'
                response = requests.get(address).json()
                message = str(response['message'])
                print("Your stake: " + message + ' BCCs\n')
            except:
                print("Node is not active. Try again later.\n")
            if HomeOrExit() == 'exit':
                break
            else:
                os.system('cls||clear')
        elif method_a == 'help':
            print("Help")
            print(
                "----------------------------------------------------------------------")
            print("You have the following options:")
            print("- New transaction: Creates a new transaction. You are asked for the")
            print("  id of the receiver node, the amount of BCCs and the message you want")
            print("  to send. You will be charged extra 3%% fee according to the amount")
            print("  you sent and 1BCC for each character of the message.")
            print("  You cant send only BCC's or only a message or both.")
            print("- Update stake: Update the stake of the current node. Positive amount ")
            print("  means that BCCs will be held from the balance and transformed into stake.")
            print("  Negative amount frees BCCs from stake and adds them to balance")
            print("- View last transactions: Prints the transactions of the last validated")
            print("  block of the BlockChat blockchain.")
            print("- Show balance and stake: Prints the current balance and stake of your wallet.")
            print("- Help: Prints usage information about the options.\n")

            if HomeOrExit() == 'exit':
                break
            else:
                os.system('cls||clear')

        else:
            break


if __name__ == "__main__":
    # Define the argument parser.
    parser = ArgumentParser(description='CLI client of BlockChat.')
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        '-p', type=int, help='port to listen on', required=True)

    # Parse the given arguments.
    args = parser.parse_args()
    PORT = args.p

    # Call the client function.
    client()
