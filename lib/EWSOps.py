'''
	Functions that return the string of XML for the desired EWS call
'''
import cgi

ExchangeVersion 		= "Exchange2010_SP2"
DistinguishedFolders 	= ["inbox", "sentitems", "deleteditems", "drafts", "outbox"]

def findItemsDistinguishedId(folderName = "msgfolderroot", maxEntries = 250, offset = 0, basePoint = "Beginning"):
	listFolders 	= open("./lib/EWS_Calls/finditem_distinguishedId.xml").read()
	listFolders 	= listFolders.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	listFolders 	= listFolders.replace("REPLACE_OFFSET", str(offset))
	listFolders 	= listFolders.replace("REPLACE_MAX_ENTRIES", str(maxEntries))
	listFolders 	= listFolders.replace("REPLACE_BASEPOINT", basePoint)
	listFolders 	= listFolders.replace("REPLACE_FOLDER_NAME", folderName)
	return listFolders

def findItemsFolderId(folderId, changeKey, maxEntries = 250, offset = 0, basePoint = "Beginning"):
	findItems 	= open("./lib/EWS_Calls/finditem_FolderId.xml").read()
	findItems 	= findItems.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	findItems 	= findItems.replace("REPLACE_OFFSET", str(offset))
	findItems 	= findItems.replace("REPLACE_MAX_ENTRIES", str(maxEntries))
	findItems 	= findItems.replace("REPLACE_BASEPOINT", basePoint)
	findItems 	= findItems.replace("REPLACE_PARENT_FOLDER_ID", folderId)
	findItems 	= findItems.replace("REPLACE_FOLDER_CHANGE_KEY", changeKey)
	return findItems

def findAllWithAttachmentsDistinguished(folderName = "msgfolderroot", maxEntries = 250, offset = 0, basePoint = "Beginning"):
	attachments 	= open("./lib/EWS_Calls/finditem_allWithAttachments_distinguishedId.xml").read()
	attachments 	= attachments.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	attachments 	= attachments.replace("REPLACE_OFFSET", str(offset))
	attachments 	= attachments.replace("REPLACE_MAX_ENTRIES", str(maxEntries))
	attachments 	= attachments.replace("REPLACE_BASEPOINT", basePoint)
	attachments 	= attachments.replace("REPLACE_FOLDER_NAME", folderName)
	return attachments

def findSubFoldersOfDistinguished(folderName = "msgfolderroot", maxEntries = 250, offset = 0, basePoint = "Beginning"):
	listFolders 	= open("./lib/EWS_Calls/findfolder_distinguishedId.xml").read()
	listFolders 	= listFolders.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	listFolders 	= listFolders.replace("REPLACE_OFFSET", str(offset))
	listFolders 	= listFolders.replace("REPLACE_MAX_ENTRIES", str(maxEntries))
	listFolders 	= listFolders.replace("REPLACE_BASEPOINT", basePoint)
	listFolders 	= listFolders.replace("REPLACE_PARENT_FOLDER_NAME", folderName)
	return listFolders

def findSubFoldersOfCustom(folderId, folderChangeKey, maxEntries = 250, offset = 0, basePoint = "Beginning"):
	listFolders 	= open("./lib/EWS_Calls/findfolder_folderId.xml").read()
	listFolders 	= listFolders.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	listFolders 	= listFolders.replace("REPLACE_OFFSET", str(offset))
	listFolders 	= listFolders.replace("REPLACE_MAX_ENTRIES", str(maxEntries))
	listFolders 	= listFolders.replace("REPLACE_BASEPOINT", basePoint)
	listFolders 	= listFolders.replace("REPLACE_PARENT_FOLDER_ID", folderId)
	listFolders 	= listFolders.replace("REPLACE_FOLDER_CHANGE_KEY", folderChangeKey)
	return listFolders

def findAllWithAttachmentsCustom(folderId, folderChangeKey,  maxEntries = 250, offset = 0, basePoint = "Beginning"):
	attachments 	= open("./lib/EWS_Calls/finditem_allWithAttachments_FolderId.xml").read()
	attachments 	= attachments.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	attachments 	= attachments.replace("REPLACE_OFFSET", str(offset))
	attachments 	= attachments.replace("REPLACE_MAX_ENTRIES", str(maxEntries))
	attachments 	= attachments.replace("REPLACE_BASEPOINT", basePoint)
	attachments 	= attachments.replace("REPLACE_PARENT_FOLDER_ID", folderId)
	attachments 	= attachments.replace("REPLACE_FOLDER_CHANGE_KEY", folderChangeKey)
	return attachments

def getEmailAttachmentIds(keyMap):
	# 	keyMap = [{"ItemId" : "ads9f0sadnf..", "ChangeKey" : "adsfdsafdsa..."}, {"ItemId" : "ads9f0sadnf..", "ChangeKey" : "adsfdsafdsa..."}]
	itemStuff 		= open('./lib/EWS_Calls/getEmailAttachmentIds.xml').read()

	itemIds 		= ""
	for x in keyMap:
		itemIds += '''<t:ItemId Id="'''+x['ItemId']+'''" ChangeKey="'''+x['ChangeKey']+'''" />\n'''

	itemStuff 		= itemStuff.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	itemStuff 		= itemStuff.replace("REPLACE_ITEM_IDS", itemIds)

	return itemStuff
def downloadEmailAttachment(attachmentID):
	itemStuff 		= open('./lib/EWS_Calls/downloadAttachment.xml').read()
	itemStuff 		= itemStuff.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	itemStuff 		= itemStuff.replace("REPLACE_ATTACHMENT_ID", attachmentID)
	return itemStuff
def addRedirectRule(ruleName, targetEmail):
	addRule 	= open("./lib/EWS_Calls/addRedirectRule.xml").read()
	addRule 	= addRule.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	addRule 	= addRule.replace("REPLACE_DISPLAY_NAME", ruleName)
	addRule 	= addRule.replace("REPLACE_TARGET_EMAIL", targetEmail)
	return addRule


# For sending an email, but avoid saving a copy in the "sent" folder 
def sendEmail_Secret(to_recipients = [], cc_recipients = [], bcc_recipients = [], subject = "", htmlBody = ""):
	sendEmail_Secret 	= open('./lib/EWS_Calls/createitem_sendEmailSecret.xml').read()
	htmlBody 			= cgi.escape(htmlBody).encode("ascii", 'xmlcharrefreplace')	#REPLACE_HTML_BODY

	# Basics
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_SUBJECT", subject)
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_HTML_BODY", htmlBody)

	# Tos
	to_recipients_data = "<t:ToRecipients>"
	for person in to_recipients:
		to_recipients_data += "<t:Mailbox><t:EmailAddress>"+person+"</t:EmailAddress></t:Mailbox>"
	to_recipients_data += '''</t:ToRecipients>'''
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_TO_RECIPIENTS", to_recipients_data)

	# Ccs
	cc_recipients_data = '''<t:CcRecipients>'''
	for person in cc_recipients:
		cc_recipients_data += "<t:Mailbox><t:EmailAddress>"+person+"</t:EmailAddress></t:Mailbox>"
	cc_recipients_data += '''</t:CcRecipients>'''
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_CC_RECIPIENTS", cc_recipients_data)


	# Bccs
	bcc_recipients_data = '''<t:BccRecipients>'''
	for person in bcc_recipients:
		bcc_recipients_data += "<t:Mailbox><t:EmailAddress>"+person+"</t:EmailAddress></t:Mailbox>"
	bcc_recipients_data += '''</t:BccRecipients>'''
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_BCC_RECIPIENTS", bcc_recipients_data)
	
	# Return the request
	return sendEmail_Secret

# For sending an email with an attachment, but avoid saving a copy in the "sent" folder
def sendEmail_SecretAttachment(to_recipients = [], cc_recipients = [], bcc_recipients = [], subject = "", htmlBody = "", attachmentName = "", attachmentBase64Content = ""):

	sendEmail_Secret 	= open('./lib/EWS_Calls/createitem_sendEmailSecretWithAttachment.xml').read()
	htmlBody 			= cgi.escape(htmlBody).encode("ascii", 'xmlcharrefreplace')	#REPLACE_HTML_BODY

	# Basics
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_SUBJECT", subject)
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_HTML_BODY", htmlBody)


	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_ATTACHMENT_NAME", attachmentName)
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_ATTACHMENT_BASE64_CONTENT", attachmentBase64Content)

	# Tos
	to_recipients_data = "<t:ToRecipients>"
	for person in to_recipients:
		to_recipients_data += "<t:Mailbox><t:EmailAddress>"+person+"</t:EmailAddress></t:Mailbox>"
	to_recipients_data += '''</t:ToRecipients>'''
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_TO_RECIPIENTS", to_recipients_data)

	# Ccs
	cc_recipients_data = '''<t:CcRecipients>'''
	for person in cc_recipients:
		cc_recipients_data += "<t:Mailbox><t:EmailAddress>"+person+"</t:EmailAddress></t:Mailbox>"
	cc_recipients_data += '''</t:CcRecipients>'''
	sendEmail_Secret 	= sendEmail_Secret.replace("REPLACE_CC_RECIPIENTS", cc_recipients_data)


	# Bccs
	bcc_recipients_data = '''<t:BccRecipients>'''
	for person in bcc_recipients:
		bcc_recipients_data += "<t:Mailbox><t:EmailAddress>"+person+"</t:EmailAddress></t:Mailbox>"
	bcc_recipients_data += '''</t:BccRecipients>'''
	sendEmail_Secret 	 = sendEmail_Secret.replace("REPLACE_BCC_RECIPIENTS", bcc_recipients_data)


	
	# Return the request
	return sendEmail_Secret

# [GetItems]
# Use this to get the content of emails, etc
# keyMap = a list of dictionaries
# 	keyMap = [{"ItemId" : "ads9f0sadnf..", "ChangeKey" : "adsfdsafdsa..."}, {"ItemId" : "ads9f0sadnf..", "ChangeKey" : "adsfdsafdsa..."}]
def getItems(keyMap):
	itemStuff 		= open('./lib/EWS_Calls/getitem.xml').read()

	itemIds 		= ""
	for x in keyMap:
		itemIds += '''<t:ItemId Id="'''+x['ItemId']+'''" ChangeKey="'''+x['ChangeKey']+'''" />\n'''

	itemStuff 		= itemStuff.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	itemStuff 		= itemStuff.replace("REPLACE_ITEM_IDS", itemIds)

	return itemStuff

# [ResolveNames]
# 	This will return the first 100 results that start with the "startsWith" string.
# 	ie. startsWith = "am"
#	results:
#				Amanda.Hugandkiss
#				Amiright.guys
#				etc
def searchAddressBook(queryString):
	getBook 	= open("./lib/EWS_Calls/resolveNames.xml").read()
	getBook 	= getBook.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	getBook 	= getBook.replace("REPLACE_QUERY_STRING", queryString)
	return getBook


#<<Future dev stuff>>#

# [ExpandDL]
# 	This will return the list of emails that belong to the given distrobution group email.
# 	If you can find the "everyone" distrobution group, then you can get the info for every
# 	
def getGroupMembers(groupEmail):
	getMembers 	= open('/EWS_Calls/expandDL.xml').read()
	getMembers 	= getMembers.replace("REPLACE_EXCHANGE_VERSION", ExchangeVersion)
	getMembers 	= getMembers.replace("REPLACE_GROUP_EMAIL", groupEmail)
	return getMembers
