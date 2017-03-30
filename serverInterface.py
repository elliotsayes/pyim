#!/usr/bin/python
import urllib2
import json

_listen_port = 10002
_uni_wireless = False
_server_address = "andrewchenuoa.pythonanywhere.com"
_server_http_address = "http://" + _server_address + "/"

def getPublicIPInfo(): # returns list 
    # testCon = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # testCon.connect(("www.google.com",0))
    # myIP = testCon.getsockname()[0]
    # if(myIP == "0.0.0.0" or myIP == "127.0.0.1" or myIP[0:6] == "192.168" or myIP[0:2] == "10."): # private network
    myIP = json.load(urllib2.urlopen('http://jsonip.com'))['ip'] # get from WWW
    if _uni_wireless:
        location = 1 # uni wireless
    elif(myIP[0:7] == "130.216"):
        location = 0 # uni desktops
    else:
        location = 2 # rest of the internet
    return location, myIP

def report(username, passhash):
    print "Reporting user " + username + " to server..."
    server_request = ( _server_http_address + "report?username=" + username
                                                  + "&password=" + passhash
                                                  + "&location=" + str(getPublicIPInfo()[0])
                                                  + "&ip=" + getPublicIPInfo()[1]
                                                  + "&port=" + str(_listen_port)
                                                  #+ "&pubkey="
                                                  + "&enc=" + str(0) )
    print "Server request: " + server_request
    myRequest = urllib2.Request(server_request)
    myResponse = urllib2.urlopen(myRequest);
    return str(myResponse.read())

def getList(username, passhash):
    print "Getting new online list from server.."
    server_request = ( _server_http_address + "getList?username=" + username
                                                   + "&password=" + passhash
                                                   + "&enc=" + str(0) )
    print "Server request: " + server_request
    myRequest = urllib2.Request(server_request)
    myResponse = urllib2.urlopen(myRequest);
    return str(myResponse.read())
    
def logoff(username, passhash):
    print "Logging off user " + username + ". Goodnight!"
    server_request = ( _server_http_address + "logoff?username=" + username
                                                   + "&password=" + passhash
                                                   + "&enc=" + str(0) )
    print "Server request: " + server_request
    myRequest = urllib2.Request(server_request)
    myResponse = urllib2.urlopen(myRequest);
    return str(myResponse.read())
