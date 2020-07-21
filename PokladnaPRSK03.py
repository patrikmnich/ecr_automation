from ecr_connector import *
    
class PRSK(object):

    STX = b"\x02"
    ETX = b'\x03'
    
    def lrc(self, data, bad=0):
        lrc = 0
        #print ("[PokladnaPRSK03.py] calculating lrc from: ",data)
        for d in data:
            #lrc ^= ord(d)
            lrc ^= d
            if bad != 0:
                lrc += 1
        #print("lrc: ",bytes([lrc]))
        return bytes([lrc])

    def parseMsg(self, data):
        if data == b'':
            print ("[PokladnaPRSK03.py] empty response data")
            return False
        #calculate response lrc
        calclrc = self.lrc(data[1:-1])
        resplrc = bytes([data[-1]])
        #print ("[PokladnaPRSK03.py] calculated lrc: " +  + "    response lrc: " + str(resplrc))
        if calclrc != resplrc:
            print("wrong lrc! calculated lrc: ", str(calclrc) + "expected: ", str(resplrc))
            connector.write(b'\x15')
            print ("[PokladnaPRSK03.py] Sending NAK")
            return False

        if data[:1] != PRSK.STX:
            print ("[PokladnaPRSK03.py] No STX")
            return False

        if data[len(data)-2:-1] != PRSK.ETX:
            print ("[PokladnaPRSK03.py] No ETX")
            return False
        
        data = data[1:-2]
        data = data.decode("utf-8")

        #splitlines = data.replace('\x1c',"\n").replace('\x02',"<STX>\n").replace('\x03',"\n<ETX>\n")
        #print ("[PokladnaPRSK03.py] split text:\n",splitlines)
        
        data = data.split("\x1c")
        print ("[PokladnaPRSK03.py] Data: ", data)
        
        result = {}
        result['ecr_result'] = data[0]
        for field in data:
            if field[0] == "R":
                result["response_code"] = field[1:]
                #print ("[PokladnaPRSK03.py] result[response_code]: ",result["response_code"])
            if field[0] == "P":
                result["cvm"] = field[1:]
                #print ("[PokladnaPRSK03.py] result[cvm]: ",result["cvm"])
            if field[0] == "n":
                result["totals"] = field[1:]
                #print ("[PokladnaPRSK03.py] result[totals]: ",result["totals"])
                #result["response_message"] = data[]
                #result["AID"] = data["Q"]
                #result["PAN"] = data[]
                #result["Date"] = data[]
            
        return result

    def sale(self, connector, amount, identifier = None):
        #create message
        #amount
        message_body = b'S' + amount.encode()
        
        return self.transaction(connector, message_body, identifier)

    def void(self, connector, amount, identifier = None):
        #create message
        #amount
        message_body = b'C' + amount.encode()
        
        return self.transaction(connector, message_body, identifier)
    
    def refund(self, connector, amount, identifier = None):
        #create message
        #amount
        message_body = b'R' + amount.encode()
        
        return self.transaction(connector, message_body, identifier)
        
    def subtotals(self, connector, identifier = None):
        #create message
        #amount
        message_body = b't'
        
        return self.transaction(connector, message_body, identifier)
        
    def totals(self, connector, identifier = None):
        #create message
        #amount
        message_body = b'T'
        
        return self.transaction(connector, message_body, identifier)

    def transaction(self, connector, message_body, identifier):
        #STX

        message = PRSK.STX
        message += message_body
        
        if identifier:
            #add Identifier with field separator to the message
            message += b'\x1CI' + identifier.encode()
            #print ("[PokladnaPRSK03.py] Identifier: ", identifier)

        #ETX
        message += PRSK.ETX
        
        #calculate and add lrc
        lrc = self.lrc(message[1:])
        message += lrc
        
        #send message
        connector.write(message)
        
        #wait for ACK
        resp = connector.read(1, 5)
        if resp == b'\x06':
            print ("[PokladnaPRSK03.py] ACK received")
        else:
            return False
    
        resp = b''
        print ("[PokladnaPRSK03.py] Waiting for response..")
        resp = connector.read(4096, 60)

        #print ("[PokladnaPRSK03.py] lrc OK!")
        parse_result = self.parseMsg(resp)
        if parse_result == False:
            print ("[PokladnaPRSK03.py] Sending NAK")
            return False

        connector.write(b'\x06')
        print ("[PokladnaPRSK03.py] Sending ACK")
        return parse_result

