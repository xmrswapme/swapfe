#!/bin/env python3

import subprocess
from flask import Flask, request, json, render_template, Response
import time
import hashlib
import psutil
import os
import webbrowser
from numpy.compat.py3k import os_fspath
#import requests
#import platform
app = Flask(__name__)


SwapFormFile = os.path.join('templates', 'swapform.html')
StandardHTMLFile = os.path.join('templates', 'standard.html')
SwapCmd = os.path.abspath('swap')

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    print("process killed!")


@app.route('/withdrawform')
def withDrawForm():
    return render_template('withdrawform.html')

@app.route('/withdraw',methods=['POST','GET'])
def withdraw():
    def inner(BTCAddress):
        StandardHTML = open(StandardHTMLFile, "r")
        html_output = StandardHTML.read()

        SwapCMD = [SwapCmd, 'withdraw-btc', '--address', BTCAddress]
        proc = subprocess.Popen(SwapCMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        TotalOutput = ' '
        for line in iter(proc.stdout.readline, ''):
            TotalOutput = TotalOutput + line
        for line in iter(proc.stderr.readline, ''):
            TotalOutput = TotalOutput + line
        yield html_output + '<p>' + TotalOutput + '</p>'
            
    try: 
        BTCAddress = request.form['btc']
    except Exception as e:
        return Response(str(e), mimetype='text/html')

    return Response(inner(BTCAddress), mimetype='text/html')  # text/html is required for most browsers to show th$

    
@app.route('/history')
def SwapHistory():
    
    def inner():
        SwapHistoryHTML = open(StandardHTMLFile, "r")
        html_output = SwapHistoryHTML.read()
        SwapHistoryHTML.flush()
        SwapHistoryHTML.close()
        SwapCMD = [SwapCmd, 'history']
        proc = subprocess.Popen(SwapCMD, stdout=subprocess.PIPE, universal_newlines=True)
        swaplines = '<h1>Swap History</h1><pre>'
        for line in iter(proc.stdout.readline,''):
            swaplines = swaplines + line 

        
        print(swaplines)   
        print(''.join([html_output,swaplines, '</pre>']))
            
        yield html_output + swaplines + '<br>\n'

    return Response(inner(), mimetype='text/html')
    
@app.route('/swapform')
def showSignUp():
    return render_template('swapform.html')



@app.route('/swap',methods=['POST','GET'])
def index():
    
    def error_message(line, html_error, SwapCmd):
        html_error = html_error + "<br><h2>Your funds are safe.</h2>\n<h2>You can either: Issue the command:</h2> <p><strong>swap withdraw-btc --address <your_btc_address></strong></p><h2>Or:</h2> <p><strong>Start a new Atomic Swap with another Provider as this one seems to have problems. The funds in your bitcoin wallet will automatically be used to begin a new swap.</strong></p>"
        p1 = subprocess.Popen([SwapCmd, "balance"], stdout=subprocess.PIPE)
        templine = p1.communicate()
        temp = templine[0].decode('utf-8')
        html_error = html_error + "<h2>" + temp + "</h2>\n"
        return html_error

    def inner(btcAddy, xmrAddy, seller):
        QRPath = os.path.join('static', 'img', 'qrcodes')
        SwapCMD = [SwapCmd, "-j", "buy-xmr", "--change-address",  btcAddy, "--receive-address", xmrAddy,
        "--seller",  seller, "--tor-socks5-port", "9050"]
        proc = subprocess.Popen(SwapCMD, stderr=subprocess.PIPE, universal_newlines=True)
        StandardHTML = open(StandardHTMLFile, "r")
        html_body = StandardHTML.read()
        StandardHTML.flush()
        StandardHTML.close()
        step = 1
        for line in iter(proc.stderr.readline,''):
            time.sleep(1)
            try:
                jsonOBJ = json.loads(line.rstrip())
                Message = jsonOBJ['fields']['message'].rstrip()
                Level = jsonOBJ['level']
            except Exception as e:
                print(str(e))
                if "Error:" in line:
                    print(line)
                    html_error = "<h2>" + line + "</h2>\n"
                    continue
                elif  "Caused by:" in line:
                    print(line)
                    html_error = html_error + "<h1>" + line + "<h1>"
                    continue
                elif line != '\n':
                    print(line)
                    html_error = html_error + "<p>" + line + "<p>" + "<br><h2>Your funds are safe.</h2>\n"
                    html_error = error_message(line, html_error, SwapCmd)
                    kill(proc.pid)
                    yield html_error + "<br/>\n"
                    break
                else:
                    continue
            if Level == "WARN":
                html_output = '<p>' + Message + '</p>'
                yield html_output + "\n"
                continue
            
            if step == 1:
                try:
                    ConnectionMessage = jsonOBJ['fields']['message']
                    html_output =  html_body + ConnectionMessage
                    print(ConnectionMessage) 
                    step += 1
                except Exception as e:
                    print("ERROR: STEP 1 (Connection issues)")
                    yield str(e) + '<br/>\n'
            elif step == 2:
                try:
                    Price = jsonOBJ['fields']['price']
                    MinAmount = jsonOBJ['fields']['minimum_amount']
                    MaxAmount = jsonOBJ['fields']['maximum_amount']
                    print("Price: %s" % Price.replace(" BTC", ''))
                    print("Minimum: %s" % MinAmount.replace(" BTC", ''))
                    print("Maximum: %s" % MaxAmount.replace(" BTC", ''))
                    html_price_table = '''
                       <table class="table table-striped custom-table">
                          <thead>
                            <tr>
                              <th scope="col">Price</th>
                              <th scope="col">Minimum</th>
                              <th scope="col">Maximum</th>
                            </tr>
                          </thead>
                          <tbody>
                              <tr scope="row">
                                  <td>%s</td>
                                  <td>%s</td>
                                  <td>%s</td>
                              </tr>

                          </tbody>
                      </table>
                      ''' % (Price, MinAmount, MaxAmount)
                    html_output = '<p>' + Message + '</p>' + html_price_table + '\n'
                    step += 1
                except Exception as e:
                    print(line)
                    print("ERROR: STEP 2 (receiving quote")
                    print(e)
                    yield str(e)  + '<br/>\n'
                    
            elif "deposit_address" in jsonOBJ['fields']:
                try:
                    BTCDepositAddy = jsonOBJ['fields']['deposit_address']
                    print("BTC Deposity Address: %s" % BTCDepositAddy)
                    hash = hashlib.sha256(str(BTCDepositAddy).encode("utf-8") ).hexdigest()
                    qrfile = hash + ".png"
                    qrproc = subprocess.Popen(['qrencode', '-o', os.path.join(QRPath,qrfile), '-s', '6','-t', 'PNG32', BTCDepositAddy], universal_newlines=True)
                    image_html = '<img src="'   + os.path.join(QRPath,qrfile) +'"/><br>\n'
                    html_output = '<p>' + Message + '</p>\n' + '<p>Bitcoin Depoist Address:    ' + BTCDepositAddy + '</p><br>\n' + image_html + '<br>\n' 
                    step += 1
                    #kill(proc.pid)
                except:
                    print(line)
                    yield str(e) 
            elif 'new_balance' in jsonOBJ['fields']:
                try:
                    NewBalance = jsonOBJ['fields']['new_balance']
                    SwappableAmt = jsonOBJ['fields']['max_giveable']
                    print("New Balance: %s" % NewBalance)
                    html_swap_table = '''
                       <table class="table table-striped custom-table">
                          <thead>
                            <tr>
                              <th scope="col">Balance</th>
                              <th scope="col">Swappable Amount</th>
                            </tr>
                          </thead>
                          <tbody>
               url = 'https://pypi.python.org/packages/source/x/xlrd/xlrd-0.9.4.tar.gz'
target_path = 'xlrd-0.9.4.tar.gz'

response = requests.get(url, stream=True)
if response.status_code == 200:
    with open(target_path, 'wb') as f:
        f.write(response.raw.read())               <tr scope="row">
                                  <td>%s</td>
                                  <td>%s</td>
                                  
                              </tr>

                          </tbody>
                      </table>
                      ''' % (NewBalance, SwappableAmt)

                    html_output = '<p>' + Message + '</p>\n' + html_swap_table + "<p>Conducting a swap for Swappable Amount...</p>\n"
                    step += 1
                except Exception as e:
                    print(line)
                    yield str(e)
            # This means the swap has started
            elif 'swap_id' in jsonOBJ['fields']:
                try:
                    print("Swap has started: ", end=' ')
                    Fees = jsonOBJ['fields']['fees']
                    SwapID = jsonOBJ['fields']['swap_id']
                    SwapAmt = jsonOBJ['fields']['amount']
                    print(SwapID)
                    print("Swap Amount: %s" % SwapAmt)
                    html_output = '<p>' + Message + '</p>\n' + '<p>Swapping: ' + SwapAmt + '</p>' + '<h1>Swap ID: ' + SwapID + '</h1>' + '<h2>PLEASE COPY OR WRITE DOWN YOUR SWAP ID</h2>'
                    step += 1
                except Exception as e: 
                    yield str(e)
            elif 'txid' in jsonOBJ['fields']:
                # This is where Bob Publishes his Bitcoin Transaction
                if 'kind' in jsonOBJ['fields']:
                    BitcoinTxID = jsonOBJ['fields']['txid']
                    print(Message)
                    print("TxID: %s" % BitcoinTxID)
                    html_output = '<p>' + Message + '</p>\n' + '<p>Bitcoin TxID: ' + BitcoinTxID + '</p>\n'
                elif 'target_confirmations' in jsonOBJ['fields']:
                    MoneroTxID = jsonOBJ['fields']['txid']
                    TargetToConfirm = jsonOBJ['fields']['target_confirmations']
                    html_output = '<p>' + Message + '</p>\n' + '<p>Alices Monero TxID: ' + MoneroTxID + '</p>\n' + '<p>Needed Confirmations: ' + TargetToConfirm + '</p>\n' + '<h2>Please be patient. This can take a while....</h2>' + '<p>Go buy some more BTC so you can swap it for XMR again once this finishes.</p>\n'
                elif 'seen_confirmations' in jsonOBJ['fields']:
                    MoneroTxID = jsonOBJ['fields']['txid']
                    Confirmations = jsonOBJ['fields']['seen_confirmations']
                    print("XMR TxID: %s" % MoneroTxID)
                    print("Confirmations: %s" % Confirmations)
                    html_output = '<p>' + Message + '</p>' + '<p>Confirmations: ' + Confirmations + '</p>\n'
                elif 'monero_receive_address' in jsonOBJ['fields']:
                    print(Message)
                    MoneroAddy = jsonOBJ['fields']['monero_receive_address']
                    XMRFinalityTxID = jsonOBJ['fields']['txid']
                    html_output = '<p>' + Message + '</p>\n' + '<p>XMR Receive Address: ' + MoneroAddy + '</p>\n' + '<p>Finality TxID: ' + XMRFinalityTxID + '</p>\n' + '<h2>SUCCESS!</h2>'
                else:
                    print(Message)
                    html_output = '<p>' + Message + '</p>\n'
            elif 'Waiting for Alice' in Message:
                print(Message)
                html_output = '<p>' + Message + '</p>\n' + '<h2>Please be patient. This can take a while....</h2>\n' + '<p>Go grab a coffee and a donut and watch your crypto ticker for 13-30 minutes.</p>\n'
   
            print(line)        
            yield html_output.rstrip() + '<br/>\n'

    try:
        seller = request.form['multiaddress']
        btcAddy = request.form['btc']
        xmrAddy = request.form['xmr']
        return Response(inner(btcAddy,xmrAddy,seller), mimetype='text/html')  # text/html is required for most browsers to show th$
    except Exception as e:
        print(str(e))
        return Response(str(e), mimetype='text/html')

'''
def get_swap(url,target_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(target_path, 'wb') as f:
            f.write(response.raw.read())    

def DownloadSwap():
    sys_platform = platform.system()
    
    if sys_platform == "Windows":
        url = "https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Windows_x86_64.zip"
        target_path = 'swap_0.8.3.zip'
    elif sys_platform == "Linux":
        url = "https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Linux_x86_64.tar"
        target_path = 'swap_0.8.3.tar'
    else:
        url = "https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Darwin_x86_64.tar"
        target_path = 'swap_0.8.3.tar'
        
    
    get_swap(url, target_path)
'''
    
if __name__ == "__main__":
#    DownloadSwap()
    webbrowser.open("http://127.0.0.1:3333/swapform")
    app.run(debug=True, port=3333, host='0.0.0.0')
    
