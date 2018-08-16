# ExchangeRelayX
Version 1.0.0. This tool is a PoC to demonstrate the ability of an attacker to perform an SMB or HTTP based NTLM relay attack to the EWS endpoint on an on-premise Microsoft Exchange server to compromise the mailbox of the victim. This tool provides the attacker with an OWA looking interface, with access to the user's mailbox and contacts.

# Background
Released at Defcon26. View the background on the tool, the core issues being exploited, and a recorded demo here: https://www.quickbreach.io/one-click-to-owa/

# Installation
	pip install -r requirements.txt

# Usage
	./exchangeRelayx.py -t https://mail.quickbreach.com

# Features
- Raw XML Access to the EWS server, so you can send requests to functions and features that were not pre-programmed in exchangeRelayx
- Add redirecting rules to the victim's email for backdooring
- Download all attachments of the user, inbox and sent
- Search the global address book tied to Active Directory
- Send emails, with attachments, as the victim - the emails will not be stored in the user's sent folder

# Program Structure
The application breaks apart into the owaServer, the relay servers, and the HTTPAttack client (exchangePlugin) that is created for each new relayed connection. 

## owaServer
The owaServer is a flask based webserver that listens on http://127.0.0.1:8000 by default. This web server serves up static HTML files of index.html, OWA.html, and ComposeEmail.html - and everything else is loaded from JSON requests (from EWS.js) to the owaServer endpoints. When a request is made to the owaServer, the owaServer will generate the appropriate EWS call and input it to the shared-memory dictionary that is used by both the owaServer and the exchangePlugin. Once the exchangePlugin recieves the request, it will send it off to Exchange and then load the response into the same shared-memory dictionary. Finally, when the owaServer gets the response from the dict, it parses the data and returns the results. You will notice that the file-download functionality is not that of a standard website, and that's due to the asynchronous nature of the app. 

## relay servers
The relay servers are standard impacket HTTP and SMB based NTLM relay servers, and they will create a new exchangePlugin instance for each newly relayed connection

## exchangePlugin
The exchangePlugin is, in a nutshell, the actual HTTPClient making and recieving the requests from the EWS server. All exchangePlugin's are passed the same shared-memory dictionary upon initialization, and they use this dictionary for interprocess communication. This allows the requests from the owaServer to be passed back to the appropriate user's relayed connection - which gives more flexibility for for multi-victim managing.

# Roadmap
This tool was built and tested against Exchange 2013 on a Server 2012 R2 system, so I would bet that adjustments will need to be made for other environments. Some goals for the next few iterations of the tool are:

0. Detect and handle the various types of Exchange 
1. Incorporate the ExpandDL and FindPeople functions in EWS
2. Add the ability to download the emails of the user themselves, rather than just the attachments
3. Include a form to remove any added redirecting rules, currently it is manual through the Raw XML interface with the UpdateInboxRules function

Pull requests are greatly appreciated
