import json
import argparse
import threading
import time
import pandas as pd
import ecr_connector
import ul_btt_connector as btt
import PokladnaPRSK03 as prsk03

btt_stop = False

def run_btt(btt_ip, btt_port, btt_card_profile):
            # check transaction type and initiate transaction + btt
            
                time.sleep(5)
                btt_connector = btt.BTTConnector()
                btt_connector.open(btt_ip, btt_port)
                btt_connector.select_card(btt_card_profile)
                btt_connector.start_simulation()
                time.sleep(5)
                btt_connector.stop_simulation()

def run_file(sourcefile, writer):
    # read file
    with open(sourcefile) as json_file:
        tests = json.load(json_file)

        tx_data = []

            #print ("[test_runner.py] net " + tests['network']['ip'] + tests['network']['port'])
    # parse json
    for t in tests['Cases']:
            #print ([test_runner.py] 'Test name: ' + t['test_name'])
            #print ([test_runner.py] 'Amount: ' + t['ecr_amount'])
            #print ([test_runner.py] 'Transaction type: ' + t['transaction_type'])
            #print ([test_runner.py] 'Host: ' + t['host'])
            #print ([test_runner.py] '')
    # execute test_case
            if tests['network']['interface'] == 'SERIAL':
                connector = ecr_connector.ECRconnectorRS232()
                connector.open(tests['network']['com'], tests['network']['speed'])
            elif tests['network']['interface'] == 'ETH':
                connector = ecr_connector.ECRconnectorETH()
                connector.open(tests['network']['ip'], tests['network']['port'])
            else:
                print ("[test_runner.py] Invalid value of -c argument!")
                break

            if t['protocol'] == 'PRSK03':
                ecr_protocol = prsk03
                ecr = prsk03.PRSK()
            else:
                print ("[test_runner.py] Invalid protocol!")
                break

            #check identifier
            if not 'ecr_identifier' in t:
                identifier = None
            else:
                identifier = t['ecr_identifier']

            if 'btt_card_profile' in t:
                btt_thread = threading.Thread(target=run_btt, args=(tests['network']['btt_ip'], tests['network']['btt_port'], t['btt_card_profile'],))
                btt_thread.start()

            if t['transaction_type'] == "SALE":
                pay_result = ecr.sale(connector, t['ecr_amount'], identifier)
            elif t['transaction_type'] == "RETURN":
                pay_result = ecr.refund(connector, t['ecr_amount'], identifier)
            elif t['transaction_type'] == "VOID":
                pay_result = ecr.void(connector, t['ecr_amount'], identifier)
            elif t['transaction_type'] == "SUBTOTALS":
                pay_result = ecr.subtotals(connector, identifier)
            elif t['transaction_type'] == "TOTALS":
                pay_result = ecr.totals(connector, identifier)
            else:
                print ("[test_runner.py] invalid transaction type")
                break

            if 'btt_card_profile' in t:
                btt_stop = True
                btt_thread.join()
            
            if pay_result == False:
                print ("[test_runner.py] error")
                break
            
            temp_data = ["N/A", "N/A", "N/A", "N/A", "N/A"]
            incorrect_result = ecr_incorrect_result = cvm_not_match = totals_not_match = False

            temp_data[0] = (t["transaction_type"])

            #print ("[test_runner.py] Pay result", pay_result)
            if "expected_result" in t:
                if "response_code" in pay_result:
                    temp_data[3] = (pay_result["response_code"])
                    if (pay_result["response_code"] == t['expected_result']):
                        print ("[test_runner.py] Expected results match!!")
                    else:
                        print ("[test_runner.py] Results do not match!")
                        incorrect_result = True

            if "ecr_amount" in t:
                temp_data[1] = (t["ecr_amount"])

            if "expected_ecr_result" in t:
                if (pay_result["ecr_result"] == t['expected_ecr_result']):
                    print ("[test_runner.py] Expected ecr results match!!")
                else:
                    ecr_incorrect_result = True
                    print ("[test_runner.py] ECR results do not match!")

            if "expected_cvm" in t:
                if "cvm" not in pay_result:
                    print ("[test_runner.py] NO CVM")
                else:
                    temp_data[2] = (pay_result["cvm"])
                    if pay_result["cvm"] == t['expected_cvm']:
                        print ("[test_runner.py] Result CVM value", pay_result['cvm'])
                        print ("[test_runner.py] CVM match!")
                    else:
                        cvm_not_match = True
                        print ("[test_runner.py] CVM does not match!")

            if "expected_totals" in t:
                if pay_result["totals"] == t['expected_totals']:
                    print ("[test_runner.py] Totals", pay_result['totals'])
                    print ("[test_runner.py] Totals match!")
                else:
                    totals_not_match = True
                    print ("[test_runner.py] Totals do not match!")
                    print ("[test_runner.py] Expected totals :" + t['expected_totals'] + " vs. POS totals: " + pay_result['totals'])

            if incorrect_result or cvm_not_match or ecr_incorrect_result or totals_not_match:
                temp_data[4] = "NOK"
            else:
                temp_data[4] = "OK"

            #update tx data
            tx_data.append(temp_data)
            print (tx_data)
            print (" ")
            connector.close()

    #create excel file
    df = pd.DataFrame(tx_data, columns=['Transaction type', 'Amount', 'CVM', 'Response code','Result'])
    df = df.style.applymap(color_negative_red, subset=['Result'])
    df.to_excel(writer, sheet_name=tests['meta']['case_name'])

def color_negative_red(value):
    if value == "OK":
        color = 'green'
    elif value == "NOK":
        color = 'red'
    else:
        color = 'black'
    
    return 'color: %s' % color

if __name__ == "__main__":
    runnerparser = argparse.ArgumentParser(description='Manager for running test scripts.')
    runnerparser.add_argument('-f', '--sourcefile',metavar='Source file', help='File for loading config and running tests')
    runner = vars(runnerparser.parse_args())
    writer = pd.ExcelWriter('./output.xlsx', engine='xlsxwriter')
    run_file(runner["sourcefile"], writer)
    writer.save()
    print("XLS FILE CREATED")