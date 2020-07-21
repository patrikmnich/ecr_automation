#
#This connector allows running transaction with any ECR protocol for any test case (optionally)
#run specific protocol using arguments from parser to initialize ecr connection (scriptname.py -h to show all available argument in console)
#

import time
import sys
import datetime
import binascii
import argparse
import json

import PokladnaPRSK03 as prsk03

class ECRconnectorRS232:

    def open(self, port, speed):
        import serial

        self.ser = serial.Serial(rtscts=0)
        self.ser.port = port
        self.ser.baudrate = speed
        self.ser.open()
        #print ("[ecr_connector.py] Opening serial port on ", port)

    def close (self):
        self.ser.close()
        #print ("[ecr_connector.py] Closing connection")

    def read(self, buffer, timeout):
        data = self.ser.read(size=buffer)

        print ("[ecr_connector.py] received data: ", data)
        return data

    def write(self, message):
        self.ser.write(message)
        print ("[ecr_connector.py] sending message: ", message)

class ECRconnectorETH:

    def open(self, ip, port):
        import socket

        #open ip socket
        port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        #print ("[ecr_connector.py] Opening ECRcommunicator on: ",ip,port)

    def close(self):
        #close socket
        self.sock.close()
        #print ("[ecr_connector.py] Closing socket")

    def read(self, buffer, timeout):
        self.sock.settimeout(timeout)
        data = self.sock.recv(buffer)

        print ("[ecr_connector.py] received data: ", data)
        return data

    def write(self, message):
        self.sock.send(message)
        print ("[ecr_connector.py]  sending message: ", message)

if __name__ == "__main__":
    #create argument parser for ECR settings
    parser = argparse.ArgumentParser(description='Process settings for ECR initialization.')
    parser.add_argument('-c', '--interface',metavar=' Connection interface', help='Interface for communication (ETH, SERIAL)')
    parser.add_argument('-P', '--protocol', metavar='Protocol', help='ECR Protocol (PRSK03, PRTC02, etc.)')
    parser.add_argument('-p', '--port',metavar='Port', help='port for communication (COM1, COM2 for RS232 / port number for ETH)')
    parser.add_argument('-b', '--baudrate',metavar='Baudrate', help='RS232 connection speed')
    parser.add_argument('-r', '--parity',metavar='Parity', help='RS232 parity bit setting')
    parser.add_argument('-i', '--ip',metavar='IP adress', help='ETH IP adress')
    parser.add_argument('-n', '--close',metavar='close conn', help='Close socket after each connection (True/False)')
    parser.add_argument('-a', '--amount',metavar='Transaction amount', help='Transaction amount')
    parser.add_argument('-I', '--indentifier',metavar='Identifier', help='Transaction identifier')
    parser.add_argument('-T', '--transaction',metavar='Transaction type', help='Transaction type (SALE, VOID, RETURN)')
    #parser.add_argument('-', '--',metavar='', help='')
    
    args = vars(parser.parse_args())
    #print(args)

    if args['interface'] == 'SERIAL':
        connector = ECRconnectorRS232()
    elif args['interface'] == 'ETH':
        connector = ECRconnectorETH()
    else:
        print ("[ecr_connector.py] Invalid value of -c argument! Going to exit..")
        sys.exit()

    if args['protocol'] == 'PRSK03':
        ecr_protocol = prsk03
        ecr = prsk03.PRSK()

    connector.open(args['ip'], args['port'])

    #check amount
    transaction_amount = None
    if 'amount' in args:
        transaction_amount = args['amount']

    #check identifier
    identifier = None
    if 'indentifier' in args:
        identifier = args['indentifier']

    # check transaction type and initiate transaction
    if args['transaction'] == "SALE":
        pay_result = ecr.sale(connector, transaction_amount, identifier)
    elif args['transaction'] == "RETURN":
        pay_result = ecr.refund(connector, transaction_amount, identifier)
    elif args['transaction'] == "VOID":
        pay_result = ecr.void(connector, transaction_amount, '1')
    elif args['transaction'] == "SUBTOTALS":
        pay_result = ecr.subtotals(connector, identifier)
    elif args['transaction'] == "TOTALS":
        pay_result = ecr.totals(connector, identifier)
    else:
        print ("[ecr_connector.py] invalid transaction type")

    connector.close()
