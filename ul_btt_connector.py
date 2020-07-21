import argparse
import socket
import time
import binascii

class BTTConnectorLow:

    def read(self, buffer, timeout):
        self.sock.settimeout(timeout)
        data = self.sock.recv(buffer)
        return data

    def write(self, message):
        self.sock.send(message)

class BTTConnector:

    def open(self, ip, port):

        port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def close(self):
        #close socket
        self.sock.close()
        
    def select_card(self, profile_name):
        # tlv EA
        # tlv DF01 A100
        # tlv DF03 Path
        #tlv = TLV(['DF01', 'A100'], ['DF03', profile_name])
        
        profile_name_encoded = binascii.hexlify(profile_name.encode())
        print('profile_name_encoded:', profile_name_encoded)
        
        tlv_request = b''
        tlv_request += b'DF0102A100'
        tlv_request += b'DF03' + '{:02x}'.format(len(profile_name)).encode() + profile_name_encoded
        
        # concat
        #print('request length', len(tlv_request))
        tlv_request = b'EA' + '{:02x}'.format(int(len(tlv_request)/2)).encode() + tlv_request

        tlv_request = '{:04x}'.format(int(len(tlv_request)/2)).encode() + tlv_request

        tlv_decoded = binascii.unhexlify(tlv_request)
        tlv_decoded = bytes(tlv_decoded)
        print("Select card")
        print('tlv_request:', tlv_request)
        self.sock.send(tlv_decoded)
        
        response = self.sock.recv(4096)
        print('Select card response: ', response)

    def start_simulation(self):
        tlv_request = b''
        tlv_request += b'DF0102B100'
        #tlv_request = b'EA' + '{:x}'.format(len(tlv_request)).encode() + tlv_request
        tlv_request = b'0007EA05' + tlv_request
        print('tlv_request:', tlv_request)
        print("Start simulation")

        tlv_decoded = binascii.unhexlify(tlv_request)
        tlv_decoded = bytes(tlv_decoded)
        #print('tlv_decoded:', tlv_decoded)

        bytes_sent = self.sock.send(tlv_decoded)
        #print('bytes_sent', bytes_sent)

        response = self.sock.recv(4096)
        print('Start simulation response: ', response)

    def stop_simulation(self):
        tlv_request = b''
        tlv_request += b'DF0102C100'
        #tlv_request = b'EA' + '{:x}'.format(len(tlv_request)).encode() + tlv_request
        tlv_request = b'0007EA05' + tlv_request
        print('tlv_request:', tlv_request)
        print("Stop simulation")

        tlv_decoded = binascii.unhexlify(tlv_request)
        tlv_decoded = bytes(tlv_decoded)
        #print('tlv_decoded:', tlv_decoded)

        bytes_sent = self.sock.send(tlv_decoded)
        #print('bytes_sent', bytes_sent)

        response = self.sock.recv(4096)
        print('Stop simulation response: ', response)

#if __name__ == "__main__":
#    parser = argparse.ArgumentParser(description='Process settings for ECR initialization.')
#    parser.add_argument('-p', '--port',metavar='Port', help='port number')
#    parser.add_argument('-i', '--ip',metavar='IP adress', help='IP adress')
#    parser.add_argument('-c', '--card',metavar='Card', help='Card profile')
#    
#    args = vars(parser.parse_args())
#    #print(args)
#    
#    BTT = BTTConnector()
#    BTT.open(args['ip'], args['port'])
#    BTT.select_card(args['card'])
#    BTT.start_simulation()
#    time.sleep(20)
#    BTT.stop_simulation()
#    #BTT.stop_simulation()
#    #BTT.close()
