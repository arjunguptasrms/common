#Copyright Jon Berg , turtlemeat.com

import socket
import random
import time
import string,cgi
import os 
import re 
#from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import BaseServer ,ThreadingMixIn
#from OpenSSL import SSL
import json
import ConfigParser
import threading

Config = ConfigParser.ConfigParser()
queryFileName = "queryJson.json"
postFileName = "postJson.json"
getFileName = "getJson.json"
f400 = '400.json'
f403 = '403.json'
f400_3 = '400_3.json'
f400_21 = '400_21.json'
f400_46 = '400_46.json'
f400_40 = '400_40.json'
f400_6 = '400_6.json'
f400_invalid_request = '400_invalid_request.json'
f400_invalid_client = '400_invalid_client.json'
f400_unauthorized_client = '400_unauthorized_client.json'
f400_unsupported_grant_type = '400_unsupported_grant_type.json'
f403_21 = '403_21.json'
f403_26 = '403_26.json'
f403_400 = '403_400.json'
f401 = '401.json'
f500 = '500_1.json'
#g_number = 918212849675

g_number = '918230001250'
imsi_number =  '405878230003003'
#imsi_number =  '405874800001250'
imsi_number2 =  '405874800001250'
imsi_number3 =  '405878230003003'
#imsi_number2 = '405878230001307'

g_user = "stuser10"
temp_user = 100
final_g_user = "stuser10" + str(temp_user)
glb_number = 818230010000

getTokenFileName = "token.json"
getPath = "/sdc/v1/profiles?userId="
getPath_refresh = "/sdc/v1/profiles"
sdcgetSSOTokenExpiryPath = "/sdc/v2/common/token?access_token"
#sdcgetSSOTokenExpiryPath = "/sdc/v2/token?access_token"
postPath = "/sdc/v1/profiles/token"
postPath_1 = "/sdc/v1/profiles/token?device_id="
postValPath = "/sdc/v2/token"
getRedirect = "/iam"
getPermission = "permission-management/v1/permissions"
codeList = []
code2TokenDict = {}
tokenList = []
token2impu = {}
impulist =[]
impuCount=0
impufile = open('impuist.txt', 'r')
for eachline in impufile:
	impulist.append(eachline)
	impuCount = impuCount+1
totalImpus = impuCount
print 'Total impus is:'+ str(totalImpus)
#    Name = ConfigSectionMap("ResponsetoSendBack")['errorcode']
def subscriberNo(userId):
	matchstr=userId
	print "user id is "
	print matchstr
	users={

			"e2euser166": '918230001250',
			"e2euser167": '918230001251',
			"e2euser168": '918230001252',
			"e2euser169": '918230001253',
			"e2euser170": '918230001254',
			"e2euser171": '918230001255',
			"e2euser1":   '918230001250',
			"e2euser2":   '918230001251',
			"e2euser3":   '918230001252',
			"stuser01":   '918230001253',
			"stuser02":   '918230001254',
			"stuser03":   '918230001255',
			"stuser04":   '918230001250',
			"stuser05":   '918230001251',
			"stuser06":   '918230001252',
			"1250": '918230001250',
			"1251": '918230001251',
			"1252": '918230001252',
			"1253": '918230001253',
			"1254": '918230001254',
			"1255": '918230001255',
			"1256": '918230001256',
			"1307": '918230001307',
			"1308": '918230001308',
			"1309": '918230001309',
			"1310": '918230001310',
			"1311": '918230001311',
			"1312": '918230001312',
			"1313": '918230001313',
			"1314": '918230001314',
			"1315": '918230001315',
			"1316": '918230001316',
			"1317": '918230001317',
			"1318": '918230001318',
            "818230003003": '818230003003',
            "818230003040": '818230003040',
            "818230003049": '818230003049',
            "818230003051": '818230003051'
	}
	random_subscriber=['918230001250', '918230001251', '918230001252', '918230001253', '918230001254', '918230001255', '918230001256' ]

	for key in users:
	    #if re.search(r'matchstr$' , key)
	     if key.endswith(matchstr):
		 #print 'matched users  impus is:'+ str(key)
			return users[key]	

    #print 'not matched users  '
	return random.choice(random_subscriber)


def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

class SecureHTTPServer(HTTPServer):
    def __init__(self, server_address, HandlerClass):
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        #server.pem's location (containing the server private key and
        #the server certificate).
        fpem = 'server.pem'
        ctx.use_privatekey_file (fpem)
        ctx.use_certificate_file(fpem)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,self.socket_type))
        self.server_bind()
        self.server_activate()
        global mycount
        mycount  = totalImpus-1

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	address_family = socket.AF_INET6

class MyHandler(BaseHTTPRequestHandler):
	def setup(self):
		self.connection = self.request
		self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
		self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
	
	def do_POST(self):
		path = self.path
		print "this is post path ", path
		if "notificationSubscription" in path:
			resp_json = '{"subscriptionId" : "'+ glb_number +'"}'
        		self.send_response(201,"Created")
			self.send_header('Content-type',"application/json")
			self.send_header('Connection','close')
			self.send_header ("Content-Length", len(resp_json))
			self.end_headers()
			self.wfile.write(resp_json)

	
	def do_PUT(self):
		self.send_response(200)
		self.send_header('Connection',  'close')
		self.send_header ("Content-Length", 0)
		self.end_headers()


	def do_GET(self):
		print threading.currentThread().getName()
		try:
			path = self.path
			#print path
			paths = path.split('?')
			authcode = self.headers.get('Authorization')
			Config.read("config.cfg")
			['config.cfg']
			Config.sections()
			['Others', 'ResponsetoSendBack', 'HeaderCheck', 'BodyCheck']
			flag = 1
			Name = ConfigSectionMap("ResponsetoSendBack")['errorcode']
			subName = ConfigSectionMap("ResponsetoSendBack")['suberrorcode']
			Authorization = ConfigSectionMap("HeaderCheck")['authorization']
			RedirectPath = ConfigSectionMap("Others")['path']


			if sdcgetSSOTokenExpiryPath in path :
				#print 'sdcgetSSOTokenExpiryPath---->'
				#print 'Authorization from request---->'+authcode
				paths[1] = paths[1].replace('access_token=','');
				tmpToken = paths[1].split('&')[0]
				deviceId = paths[1].split('&')[1]
				deviceId = deviceId.replace('device_id=','')
				#print 'paths in Get is:'
				#print paths
				#print 'token in Get is:'+tmpToken
				#print 'deviceId in Get is:'+deviceId
				f = open(getTokenFileName,"r")
				getFileContent = f.read();
				getFileContent = getFileContent.replace('5454b6511ea75a08918fb4e52f35a03064109c599b665b91b70b9e3cb44c46a5',str(tmpToken))
				global temp_user
				temp_user = temp_user+1
				final_g_user = "stuser" + str(temp_user)
				getFileContent = getFileContent.replace('666e8a5032787edfb6e499f6b5df6067',str(final_g_user))
				self.send_response(200)
				self.send_header('Content-type',	'application/json;charset=UTF-8')
				self.send_header('Connection',	'close')
				self.send_header ("Content-Length", len(getFileContent))
				self.end_headers()
				#print getFileContent
				self.wfile.write(getFileContent)
				f.close()



#deviceId
			if (getPath in path or getPath_refresh in path):
				#print "arjun gupta ******"
				#print path
				userIdPath = path.split("=")[1]
				#print "userIdPath", userIdPath
				f = open(getFileName,"r")
				global glb_number
				getFileContent = f.read();
				glb_number = glb_number +1 
				#deviceId = path.split('=')[2]
				imsi_number = str(40587) + str(glb_number)
			 	deviceId = "urn%3Auuid%3Aa0e1dddf-6d6a-39fa-89a9-a635595-ff" + str(glb_number)[7:]
				getFileContent = getFileContent.replace('urn%3Auuid%3Aa0e1dddf-6d6a-39fa-89a9-a635595-ff10161',str(deviceId))
				getFileContent = getFileContent.replace('818230010161',str(glb_number))
				getFileContent = getFileContent.replace('40587818230010161',str(imsi_number))
				getFileContent = getFileContent.replace('52e824f3a01a7bc63cb4a9bb13e010161',userIdPath)
				#print getFileContent
				self.send_response(200)
				self.send_header('Content-type',	'application/json;charset=UTF-8')
				self.send_header('Connection',	'close')
				self.send_header ("Content-Length", len(getFileContent))
				self.end_headers()
				self.wfile.write(getFileContent)
				f.close()
		except IOError:
			self.send_error(404,'File Not Found: %s' % self.path)

class HTTPServerV6(HTTPServer):
	address_family = socket.AF_INET6
	global mycount
	mycount  = totalImpus-1





def main():
	try:
		server = ThreadedHTTPServer(('', 8866), MyHandler)
		print 'started httpserver...'
		server.serve_forever()
	except KeyboardInterrupt:
		print '^C received, shutting down server'
		server.socket.close()

if __name__ == '__main__':
	main()


