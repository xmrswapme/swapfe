# swapfe 
Atomic Swap web interface front end with realtime reporting for *Bitcoin* to *Monero* atomic swaps. 

## Atomic Swap CLI
Developed by the Comit-Network, their command line interface (SWAP CLI) allows atomic swaps between the Bitcoin and Monero blockchain. You can download the Atomic Swap CLI to get started at the links below. 

Latest Release Version (0.8.3):
[Linux Swap CLI](https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Linux_x86_64.tar)
[Windows Swap CLI](https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Windows_x86_64.zip)
[OS X Swap CLI](https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Darwin_x86_64.tar)

We suggest exploring the various command line options that you may need to use aside from **swapfe**. We would appreciate it if you could provide us with feedback when **swapfe** is not providing details for various commands - as some have not been tested. This will enable us to build a complete GUI for the surrouding swap cli. 

## Swapfe Web Interface
**swapfe** is a GUI web interface to the comit-network swap command. It processes the json output of the swap CLI and interprets it producing a user interface within your web browser. It does this by starting its own "webserver" (flask), automatically opens your webbrowser to the specified address, and allows you to interact with the swap CLI. 

Currently, the first screen is the swapform. This is a UI for conducting a swap. It uses a known database of Market Makers (Atomic Swap Providers) from our [xmrswap.me](https://xmrswap.me) server. This database is checked against current swap providers and determines if they are online or not. You can use the **swapfe** web interface to choose an Atomic Swap Provider, or if you know another one that is not in the database, feel free to use that one as well. 

### Conducting a swap

**swapfe** will spin up a webserver and automatically open the webbrowser to the swapform page as seen below.

![swapform](https://i.imgur.com/Rhsjgxn.png)

From here you can choose a Seller Address from the table on the page, or enter your own seller address into **1**. Next enter an unusued *Bitcoin* change address into **2**. Finally input the *Monero* address you wish to receive the funds to in **3**. Press submit, **ONLY ONCE**, as it will begin running the command and will display the output of swap CLI on the page it redirects you to. 

The redirected page is continuously updated with the results of the swap in realtime. Please leave this page open until the swap finishes successfully or with an error. If a swap is currently live, do not close or go to a different page, as you will not be able to see the progress of the live swap.

**Note**: All progress of the swap can also be seen in JSON format within the terminal where you ran **swapfe**. This is used for debugging purposes and will be needed for other use cases when they arise. 

**Note 2**: NO DATA IS SENT TO OUR SERVERS. This is a local only webserver that is only accessible by you. We do pull in the Seller Database from our server, but nothing is sent to our servers. NO LOGGING OF ANY KIND OTHER THAN WHAT YOU SEE IN YOUR LOCAL BROWSER AND IN THE CONSOLE. 

### Successful Swap
Here are the results of the Live Swap page on a fully completed swap. Click on the image to see it in full scale. 

<a href="https://i.imgur.com/e2bJIqO.png"><img src="https://i.imgur.com/e2bJIqO.png" /></a>

As you can see, it provides a nice format with which to see the realtime progress of the active swap. Once your swap completes, you may navigate away from the page.

### Failed or Incomplete Swap
The most common occurence when a swap fails is the ability to withdraw your funds from the local *Bitcoin* wallet that SWAP CLI uses. We provide an interface to allow the withdraw of your transferred BTC back to your private wallet. 

One aspect of a failed swap is that generally you can conduct a new swap using the existing *Bitcoin* funds with a new provider. Our interface handles this option as well. But, if you are just fed up and want your *Bitcoin* in a safe place and would rather not conduct a new swap you can use this form to do that. The following screenshot shows the Withdraw interface.

![Withdraw](https://i.imgur.com/6kRc9za.png)

Click submit **ONLY ONCE** and it will redirect you to a new page telling you the status of your withdraw.

### Swap History
Another feature of **swapfe** is the ability to view the output of the history database from the Swap CLI database. A screenshot of the history can be seen below.

![Swap History](https://i.imgur.com/D91VzhO.png)

The swap cli database is very primative as of now and just displays the SWAP ID and the state the swap finished in. As you can see we conducted three successful swaps. 

### Find Providers
We have interpreted the output of the swap command when listing sellers for an arbritary rendezvousd point. It pulls in the price, min, max qty and the seller address to a formatted table and displays it within the web browser. The seller form and results can be seen in the following screenshots:

![Seller Form](https://i.imgur.com/zCy4th5.png)

![Rendezvous Results](https://i.imgur.com/Tfom7MR.png)


#### Testing

We have successfully tested this on various error responses and completed swaps. It **MUST** be pointed out that not all use cases have arose in our testing. This is why we need more people to test this interface so we can properly interpret the JSON results so they may be provided within the interface and appropriate responses can be implemented. 

What you can do if the interface fails to provide you with a status that is acceptable is to provide us with the JSON output in the console you ran **swapfe** from. This will allow us to code an interpreter to the JSON output and be able to handle it within the UI. 

## Installing and Running
Until we are able to get *setuptools* working correctly and distribute this as a pip package or even better a standalone bundle (with an .exe for Windows users), the following installation instructions have to suffice for the time being.

### Install
Simply clone this git repo using your favorite method. Using the git CLI you can simply do the following:

`git clone https://github.com/xmrswapme/swapfe`

### Dependencies
* Python 3 or higher
* Flask
* psutils
* xmr-btc-swap SWAP CLI

**swapfe** requires two extra dependencies to be able to run correclty. These are **Flask** and **psutils**. Issue the following comands in your console to install these requried packages. 

`pip install Flask`
`pip install psutils`

You must download the Swap CLI from Comit-network and install it in the directory where **swapfe** resides. For \*NIX users you can download that by issuing the following command in your console:

`wget -q -O- https://github.com/comit-network/xmr-btc-swap/releases/download/0.8.3/swap_0.8.3_Linux_x86_64.tar | tar x`

### Running
Once you've installed the required depencies you can then run **swapfe**. Simply run the following in your console window:

`$ python swapfe.py`
or
`$ ./swapfe.py`

It will spin up a webserver and open your default webbrowser to the location that provides the swap interface. 

By default the **swapfe** interface uses a tor-socks5 port of 9050. If you have the tor socks running on a different port, we currently don't have support for that. If you know how to read Python you can change that in the code.

If you are not running a tor instance on your machine **swapfe** will use the clearnet. This is by design of the Comit-network which defaults to tor and falls back to the clearnet if tor is not avaiable. 

## Use Case Scenarios
What is nice about the way we designed a UI to the swap CLI is that it is able to run as a standalone webserver. This is particular useful for any third-parties that want to be a custodian for Atomic Swaps.

Of course, it must be said that being a third party that wishes to conduct atomic swaps on users behalf goes against the whole ideology of an atomic swap not needing a trusted third party. Nevertheless, exposure to Monero/Bitcoin atomic swaps is necessary and if people are willing to forgoe the primary reason behind them and enlist trust in a third party using our (or anyone else's) software; then so be it. So long as the network of atomic swap providers and users increases, we fully support the use of the software.

### Apache & Nginx
Because this is a Flask app one can ultimately use it with **wsgi** and the apache/nginx **wsgi** module. A little work needs to be done first. For one, if you are going to be a third party providing atomic swaps, then you need to edit the code to issue a unique `--data-base-dir <uniqueID>` with every instance. You will need to build in an interface to handle an internal swapID, separate from the one the SWAP CLI provides, for each users case - so that you may conduct withdraws/refunds and the like from the appropriate wallet. Finally, you will need to create a **wsgi** startup file with the necessary SSL requirements and options.

We plan on providing this use case in future releases as we see the benefit of expanding the network. However, at this time, you will need to edit the code to make this work on you or your party's behalf.

### Other uses
Because this is a local and standalone webserver, a user can run this on a machine on their local network and connect to it from their phone or their tablet and run a swap through there. Hell. You can run a swap while you do the dishes or laundry. It's a use case, although we suggest using your computer. 
