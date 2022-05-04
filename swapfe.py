#!/bin/env python3

import threading
import subprocess
import requests
import platform
import shutil
import time
import hashlib
import psutil
import sys
import webbrowser

from threading import Thread

from flask import Flask, request, json, render_template, Response

from os import path, mkdir
from os.path import expanduser
from decimal import Decimal

from bs4 import BeautifulSoup

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt




app = Flask(__name__)



def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, relative_path)
    

SwapFormFile = resource_path('templates/swapform.html')
StandardHTMLFile = resource_path('templates/standard.html')
TimerHTMLFile = resource_path('templates/timer.html')
DashboardTMLFile = resource_path('templates/dashboard.html')
home_dir = expanduser("~")
SwapCmd = path.join(path.abspath(home_dir),'AtomicSwaps', 'swap', 'swap')
SwapDBdir = path.join(path.abspath(home_dir),'AtomicSwaps', 'swap')
sys_platform = platform.system()
PreStepOneMessage = False
SwapID = ''
SwapResumes = 0

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return



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

        SwapCMD = [SwapCmd, "--data-base-dir", SwapDBdir, 'withdraw-btc', '--address', BTCAddress]
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

@app.route('/listsellerform')
def sellerform():
    return render_template('listsellerform.html')    

@app.route('/listsellers', methods=['POST', 'GET'])
def listsellers():
         
    try: 
        rendezvous = request.form['multiaddress']
    except Exception as e:
        return Response(str(e), mimetype='text/html')
    return Response(GetSellers(rendezvous), mimetype='text/html')


def format_btc(Price):
    OneBTC = 100000000
    BTC = Decimal(Price) / Decimal(OneBTC)
    return(f"{BTC : .8f}")
    
def render_sellers_html(SellerData):
    StandardHTML = open(DashboardTMLFile, "r")
    html_output = StandardHTML.read()

    html_table = ''
    for row in SellerData:
        html_table = html_table + '<tr scope="row">\n'
        for d in row:
            html_table = html_table + "<td>%s</td>\n" % d
        html_table = html_table + '</tr>\n'
    html_table = html_table + '</tbody>\n</table>'
    html_output = html_output + html_table + '<br><br><br><br><div class="footer"><p>swapfe v0.0.1</p></div>'
    return html_output

def GetSellers(rendezvous):

    SellerData = []

    SwapCMD = [SwapCmd,"--data-base-dir", SwapDBdir,'-j', 'list-sellers', '--rendezvous-point', rendezvous, '--tor-socks5-port', '9050']
    proc = subprocess.Popen(SwapCMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    for line in iter(proc.stdout.readline, ''):
        print(line)
        try:
            jsonOBJ = json.loads(line)
        except Exception as e:
            print(str(e))
            continue
        if 'status' in jsonOBJ:
            if "Unreachable" == jsonOBJ['status']:
                continue
            if 'Online' in jsonOBJ['status']:
                SellerInfo = []
                try:
                    SellerInfo.append(format_btc(jsonOBJ['status']['Online']['price']))
                    SellerInfo.append(format_btc(jsonOBJ['status']['Online']['min_quantity']))
                    SellerInfo.append(format_btc(jsonOBJ['status']['Online']['max_quantity']))
                    SellerInfo.append(jsonOBJ['multiaddr'])
                    SellerData.append(SellerInfo)
                except Exception as e:
                    print(str(e))
                    yield str(e)
                    break
            else:
                continue
        else:
            continue
    html_output = render_sellers_html(SellerData)
    yield html_output

@app.route('/resume')
def resume():
        
    def inner():
        ResumeSwapHTMLFile = resource_path("templates/resumeswap.html")
        SwapHistoryHTML = open(ResumeSwapHTMLFile, "r")
        html_output = SwapHistoryHTML.read()
        SwapHistoryHTML.flush()
        SwapHistoryHTML.close()
        SwapCMD = [SwapCmd,"--data-base-dir", SwapDBdir, 'history']
        proc = subprocess.Popen(SwapCMD, stdout=subprocess.PIPE, universal_newlines=True)
        swaplines = '<h1>Swap History</h1><pre>'
        for line in iter(proc.stdout.readline,''):
            swaplines = swaplines + line 
    
        yield html_output + swaplines + '<br>\n' 

    return Response(inner(), mimetype='text/html')

@app.route('/resumeswap', methods=['POST', 'GET'])
def resume_swap():
    try: 
        global SwapID
        SwapID = request.form['swapid']
    except Exception as e:
        return Response(str(e), mimetype='text/html')
    return Response(ResumeSwap(False), mimetype='text/html')
         
@app.route('/history')
def SwapHistory():
    
    def inner():
        SwapHistoryHTML = open(StandardHTMLFile, "r")
        html_output = SwapHistoryHTML.read()
        SwapHistoryHTML.flush()
        SwapHistoryHTML.close()
        SwapCMD = [SwapCmd,"--data-base-dir", SwapDBdir, 'history']
        proc = subprocess.Popen(SwapCMD, stdout=subprocess.PIPE, universal_newlines=True)
        swaplines = '<h1>Swap History</h1><pre>'
        for line in iter(proc.stdout.readline,''):
            swaplines = swaplines + line 
    
        yield html_output + swaplines + '<br>\n' 

    return Response(inner(), mimetype='text/html')
    
@app.route('/swapform')
def showSwapForm():
    return render_template('swapform.html')

def GetQRcmd():
    if sys_platform == "Windows":
        return path.join(path.abspath(home_dir),'AtomicSwaps', 'swap', 'qrcode.exe')
    else:
        if shutil.which('qrencode') is not None:
            return 'qrencode'
        else:
            return ''


def PreStepOne(html_body, PreStepOneMessage, Message):
    
    if PreStepOneMessage:
        html_output = Message
    else:
        html_output =  html_body + Message
        
    yield html_output

def SwapPriceTable(Price, MinAmount, MaxAmount):
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
    return html_price_table

def SwapAmtTable(NewBalance, SwappableAmt):
    html_swap_table = '''
                       <table class="table table-striped custom-table">
                          <thead>
                            <tr>
                              <th scope="col">Balance</th>
                              <th scope="col">Swappable Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                         <tr scope="row">
                                  <td>%s</td>
                                  <td>%s</td>
                                  
                              </tr>

                          </tbody>
                      </table>
                      ''' % (NewBalance, SwappableAmt)

    return html_swap_table

def ResumeSwap(auto):
    global SwapResumes
    SwapResumes += 1


    if not auto:
        HTML = open(StandardHTMLFile, "r")
        html_output = HTML.read()
        HTML.close()
        yield html_output
        
    timer_file = open(TimerHTMLFile, "r")
    timer_html = timer_file.read()
    timer_file.flush()
    timer_file.close()
    
    yield timer_html + "<br>"
    time.sleep(5)
    
    SwapCMD = [SwapCmd, "--data-base-dir", SwapDBdir, "-j", "resume", "--swap-id",  SwapID, "--tor-socks5-port", "9050"]
    proc = subprocess.Popen(SwapCMD, stderr=subprocess.PIPE, universal_newlines=True)
    for line in iter(proc.stderr.readline,''):
        time.sleep(1)
        global PreStepOneMessage
        PreStepOneMessage = True
        print(line)        
        html_gen = SwapConditionals(line, proc)
        try: 
            html_output = next(html_gen)
        except: 
            pass
        yield html_output + '<br/>\n'
    
def SwapConditionals(line, proc):
    
    def error_message(line, html_error, SwapCmd):
        html_error = html_error + "<br><h2>You can either: Issue the command:</h2> <p><strong>swap withdraw-btc --address <your_btc_address></strong></p><br><p><strong>Or use the Withdraw Link on this page</strong></p><br><h2>Or:</h2> <p><strong>Start a new Atomic Swap with another Provider as this one seems to have problems. The funds in your bitcoin wallet will automatically be used to begin a new swap.</strong></p>"
        p1 = subprocess.Popen([SwapCmd,"--data-base-dir", SwapDBdir, "balance"], stdout=subprocess.PIPE)
        templine = p1.communicate()
        temp = templine[0].decode('utf-8')
        html_error = html_error + "<h2>" + temp + "</h2>\n"
        yield html_error

    global PreStepOneMessage
    global SwapResumes
    
    WaitingMessage = '<h2>Please be patient. This can take a while....</h2>' + '<p>Go buy some more BTC so you can swap it for XMR again once this finishes.</p>\n'
    DonutMessage = '<h2>Please be patient. This can take a while....</h2>\n' + '<p>Go grab a coffee and a donut and watch your crypto ticker for 13-30 minutes.</p>\n'
    
    StandardHTML = open(StandardHTMLFile, "r")
    html_body = StandardHTML.read()
    StandardHTML.flush()
    StandardHTML.close()
    
    QRPath = path.join('static', 'img', 'qrcodes')
    
    
    
    try:
        jsonOBJ = json.loads(line.rstrip())
        Message = jsonOBJ['fields']['message'].rstrip()
        Level = jsonOBJ['level']
        #print(Message)
        #print(Level)
        #print(step)
    except Exception as e:
        print(str(e))
        if "Error: Failed to complete swap" in line:
            #print(line)
            kill(proc.pid)
            yield '<h2>Will try to resume swap.</h2>'
            if SwapResumes > 1:
                yield '<h2>Already tried to resume swap once. Manual intervention is needed. Please consult the swap CLI.</h2>'
            else:
                if SwapID:
                    ResumeSwap(True)
                else:
                    yield '<p>No SWAPID found. Cannot resume.</p>'
        elif "Error:" in line:
            #print(line)
            html_error = "<h2>" + line + "</h2>\n"
            yield html_error
        elif  "Caused by:" in line:
            #print(line)
            html_error = "<h1>" + line + "<h1>"
            yield html_error
        elif line != '\n':
            #print(line)
            html_error = "<p>" + line + "<p>" + "<br><h2>Your funds are safe.</h2>\n"
            html_error_gen = error_message(line, html_error, SwapCmd)
            try:
                html_error = next(html_error_gen)
            except:
                pass
            kill(proc.pid)
            yield html_error
        else:
            yield ' '
        
        
    # output any warning message to the web interface
    if Level == "WARN":
        html_output = '<p>' + Message + '</p>'
        yield html_output
    
    # download monero-wallet-rpc
    if 'Downloading' in jsonOBJ['fields']['message']:
        html_output = PreStepOne(html_body, PreStepOneMessage, Message)
        PreStepOneMessage = True
        yield next(html_output)
        
        
    
    # if sqlite is not used, let them know about migrating        
    if 'migrate' in jsonOBJ['fields']['message']:
        html_output = PreStepOne(html_body, PreStepOneMessage, Message)
        PreStepOneMessage = True;
        yield next(html_output)
         
    
    # Just a way to get started parsing the messages
    # really should be something more concrete
    if 'Connected' in Message or 'connect' in Message:
        try:
            html_pre_step = PreStepOne(html_body, PreStepOneMessage, Message)
        except Exception as e:
            print("ERROR: STEP 1 (Connection issues)")
            yield str(e) + '<br/>\n'
            
    elif 'quote' in Message:
        try:
            html_price_table = SwapPriceTable(jsonOBJ['fields']['price'],
                                              jsonOBJ['fields']['minimum_amount'],
                                              jsonOBJ['fields']['maximum_amount'])
            
            html_output = '<p>%s</p>' % Message  + html_price_table + '\n'
        except Exception as e:
            print("ERROR: STEP 2 (receiving quote")
            print(str(e))
            yield str(e)  + '<br/>\n'
            
    # Show Deposit Address and QR code to begin swap
    elif "deposit_address" in jsonOBJ['fields']:
        try:
            BTCDepositAddy = jsonOBJ['fields']['deposit_address']
            #print("BTC Deposity Address: %s" % BTCDepositAddy)
            qrhash= hashlib.sha256(str(BTCDepositAddy).encode("utf-8") ).hexdigest()
            qrfile = qrhash + ".png"
            qrcmd = GetQRcmd()
            if qrcmd:
                subprocess.Popen([qrcmd, '-o', path.join(resource_path(QRPath),qrfile), '-s', '6','-t', 'PNG', BTCDepositAddy], universal_newlines=True)
                image_html = '<img src="'   + path.join(QRPath,qrfile) +'"/><br>\n'
                cancel_html = '<p>If you would like to cancel this active swap, do not deposit BTC in the above address and click the following link: </p><a href=/cancel?pid=%s>Cancel Swap</a><br>Otherwise, proceed with the deposit.' % proc.pid
                html_output = '<p>%s</p>\n' % Message +  '<p>Bitcoin Depoist Address: %s</p><br>\n' % BTCDepositAddy  + image_html + '<br>\n' + cancel_html
            else:
                cancel_html = '<p>If you would like to cancel this active swap, do not deposit BTC in the above address and click the following link: </p><a href=/cancel?pid=%s>Cancel Swap</a><br>Otherwise, proceed with the deposit.' % proc.pid
                html_output = '<p>%s</p>\n' % Message + '<p>Bitcoin Depoist Address: %s</p><br>\n' % BTCDepositAddy + '<p>No QR code program available... use address</p><br>\n' + cancel_html
        except Exception as e:
            print(line)
            yield str(e)
            
            
    # Bitcoin received in internal wallet 
    elif 'new_balance' in jsonOBJ['fields']:
        try:
            html_swap_table = SwapAmtTable(jsonOBJ['fields']['new_balance'], jsonOBJ['fields']['max_giveable'])
            html_output = '<p>%s</p>\n' % Message + html_swap_table + "<p>Conducting a swap for Swappable Amount...</p>\n"
        except Exception as e:
            print(line)
            yield str(e)
            
    # This means the swap has started
    elif 'fees' in jsonOBJ['fields']:
        Fees = jsonOBJ['fields']['fees']
        SwapAmt = jsonOBJ['fields']['amount']
        html_output = '<p>%s</p>' % Message + '<p>BTC Swap Amount: %s</p>' % SwapAmt + '<p>Fees: %s</p>\n' % Fees
        
    elif 'swap_id' in jsonOBJ['fields']:
        try:
            SwapID = jsonOBJ['fields']['swap_id']
            print(SwapID)
            html_output = '<p>%s</p>\n' % Message + '<h1>Swap ID: %s</h1>' % SwapID  + '<h2>PLEASE COPY OR WRITE DOWN YOUR SWAP ID</h2>'
        except Exception as e: 
            yield str(e)
            
    elif 'txid' in jsonOBJ['fields']:
        # This is where Bob Publishes his Bitcoin Transaction
        if 'kind' in jsonOBJ['fields']:
            html_output = '<p>%s</p>\n' % Message + '<p>Bitcoin TxID: %s</p>\n' % jsonOBJ['fields']['txid']
            
        # Alice Locked and Published Monero lock TxID 
        elif 'target_confirmations' in jsonOBJ['fields']:
            MoneroTxID = jsonOBJ['fields']['txid']
            TargetToConfirm = jsonOBJ['fields']['target_confirmations']
            html_output = '<p>%s</p>\n' % Message + '<p>Alices Monero TxID: %s</p>\n' % MoneroTxID  + '<p>Needed Confirmations: %s</p>\n' % TargetToConfirm  + WaitingMessage
            
        # Print no. of Monero Confirmations
        elif 'seen_confirmations' in jsonOBJ['fields']:
            MoneroTxID = jsonOBJ['fields']['txid']
            Confirmations = jsonOBJ['fields']['seen_confirmations']
            print("XMR TxID: %s" % MoneroTxID)
            print("Confirmations: %s" % Confirmations)
            html_output = '<p>%s</p>\n' % Message + '<p>Confirmations: %s</p>\n' % Confirmations
        
        # Success  
        elif 'monero_receive_address' in jsonOBJ['fields']:
            print(Message)
            MoneroAddy = jsonOBJ['fields']['monero_receive_address']
            XMRFinalityTxID = jsonOBJ['fields']['txid']
            html_output = '<p>%s</p>\n' % Message + '<p>XMR Receive Address: %s</p>\n' % MoneroAddy  + '<p>Finality TxID: %s</p>\n<h2>SUCCESS!</h2>' % XMRFinalityTxID
            
        # Handle any messages not in tx conditionals 
        else:
            print(Message)
            html_output = '<p>%s</p>\n' % Message
            
    # Right after swap has begun
    elif 'Waiting for Alice' in Message:
        print(Message)
        html_output = '<p>%s</p>\n' % Message + DonutMessage
        
    # print any message not caught in main conditionals    
    else:
        print("Not Caught")
        html_output = '<p>%s</p>\n' % Message
    try: 
        html_output = next(html_pre_step)
    except:
        pass
    #return return_val
    yield html_output
    #return

@app.route('/swap',methods=['POST','GET'])
def index():
    

    def inner(btcAddy, xmrAddy, seller):
        SwapCMD = [SwapCmd, "--data-base-dir", SwapDBdir, "-j", "buy-xmr", "--change-address",  btcAddy, "--receive-address", xmrAddy,"--seller",  seller, "--tor-socks5-port", "9050"]
        proc = subprocess.Popen(SwapCMD, stderr=subprocess.PIPE, universal_newlines=True)

        for line in iter(proc.stderr.readline,''):
            time.sleep(1)
            print(line)
            html_gen = SwapConditionals(line, proc)
            try: 
                html_output = next(html_gen)
            except Exception as e:
                print("ERROR with Generator: %s" % str(e))
                pass
            yield html_output + '<br/>\n'
            

    try:
        seller = request.form['multiaddress'].rstrip().lstrip()
        btcAddy = request.form['btc'].rstrip().lstrip()
        xmrAddy = request.form['xmr'].rstrip().lstrip()
        return Response(inner(btcAddy,xmrAddy,seller), mimetype='text/html')  # text/html is required for most browsers to show th$
    except Exception as e:
        print(str(e))
        return Response(str(e), mimetype='text/html')


@app.route('/cancel', methods=['GET'])
def CancelSwap():
    StandardHTML = open(StandardHTMLFile, "r")
    html_body = StandardHTML.read()
    StandardHTML.flush()
    StandardHTML.close()
    query_parameters = request.args
    
    swap_process_pid = query_parameters.get('pid')
    kill(int(swap_process_pid))
    html_output = html_body + '<br><h1>Swap Cancelled!</h1>\n'
    return html_output



def get_latest_platform_release():
    GhBaseURL = "https://github.com/"
    SwapCLIURL = 'https://github.com/comit-network/xmr-btc-swap/releases'

    req = requests.get(SwapCLIURL)
    HTML = req.text
        
    soup = BeautifulSoup(HTML, features="html.parser")
    ahref_blocks = soup.find_all('a', {"rel" : "nofollow"})
    
    sys_platform = platform.system()
    
    for link in ahref_blocks:
        if 'swap_' in link['href']:
            if ''.join([sys_platform, "_x86"]) in link['href']:
                print(''.join([GhBaseURL,link['href']]))
                return ''.join([GhBaseURL,link['href']])
            

def get_swap(url,target_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(target_path, 'wb') as f:
            f.write(response.raw.read())    


def get_swap_cli(url):
    
    if path.isdir(path.join(path.abspath(home_dir), "AtomicSwaps")):
        print("Atomic Swaps Directory Exists!")
    else:
        print("Creating space for Comit-Network swap CLI")
        mkdir(path.join(path.abspath(home_dir), "AtomicSwaps"))
    
    if sys_platform == "Windows":
        print("Downloading Comit-Network swap CLI...")

        get_swap(url, resource_path('swap_0.8.3.zip'))
        shutil.unpack_archive(resource_path('swap_0.8.3.zip'), path.join(path.abspath(home_dir), 'AtomicSwaps','swap'))
    else:
        print("Downloading Comit-Network swap CLI...")

        get_swap(url, resource_path('swap_0.8.3.tar'))
        shutil.unpack_archive(resource_path('swap_0.8.3.tar'), path.join(path.abspath(home_dir), 'AtomicSwaps', 'swap'))

    print("Done.")

def DownloadSwap(window):
    
    
    if path.isfile(path.join(path.abspath(home_dir),"AtomicSwaps","swap", "swap")) or path.isfile(path.join(path.abspath(home_dir),"AtomicSwaps","swap", "swap.exe")):
        print("Swap CLI installed.")
        SwapCmd = path.join(path.abspath(home_dir),"AtomicSwaps","swap", "swap")        
        p1 = subprocess.Popen([SwapCmd, "--version"], stdout=subprocess.PIPE)
        templine = p1.communicate()
        version = templine[0].decode('utf-8').split(' ')[-1].replace('.', '')
        print("Installed Version: %s" % version)
        print("Checking for new version...")
        url = get_latest_platform_release()
        latest_version = url.split('/')[-1]
        latest_version = latest_version.split('_')[1]
        latest_version = latest_version.replace('swap_', '').replace('.', '')
        print("Latest Version: %s" % latest_version)
        if latest_version > version or "preview" in latest_version:
            print("New Version found... Getting...")
            get_swap_cli(url)
        
        
    else:
        print("No version found. Retrieving...")
        url = get_latest_platform_release()
        get_swap_cli(url)

    # This is to get the QRCode binary for Windows. Pyinstaller had permission issues in temp folder. 
    # Seeing if this works. 
    if sys_platform == "Windows":
        print("Downloading QRCode executable...")
        get_swap("https://xmrswap.me/pkgs/qrcode.exe",path.join(path.abspath(home_dir),'AtomicSwaps', 'swap', 'qrcode.exe'))
    
    return window.close()

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(400, 300)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # create label
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(0, 0, 400, 300))
        self.label.setMinimumSize(QtCore.QSize(400, 300))
        self.label.setMaximumSize(QtCore.QSize(400, 300))
        self.label.setObjectName("Loading")

        # frameless window
        MainWindow.setWindowFlags(Qt.FramelessWindowHint)
        

        # add label to main window
        MainWindow.setCentralWidget(self.centralwidget)

        # set qmovie as label
        self.movie = QMovie(resource_path("static/img/loading.gif"))
        self.label.setMovie(self.movie)
        self.movie.start()
        
        

def LoadingAtomicApp():
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    window.show()
    
    #window.close()
    dlthrd = threading.Thread(target=DownloadSwap, args=(window,))
    dlthrd.start()
    #y = threading.Thread(target=app.exec_())
    #y.start()
    app.exec_()
    
def LoadBrowser():
    time.sleep(2)
    webbrowser.open("http://0.0.0.0:3333/swapform")
    

if __name__ == "__main__":

            
    qtthread = threading.Thread(target=LoadingAtomicApp())
    qtthread.start()
    
    wbthread = threading.Thread(target=LoadBrowser)
    wbthread.start()
    app.run(debug=True, port=3333, host='0.0.0.0', use_reloader=False)
    
    print("Done.")
    
