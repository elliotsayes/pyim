#!/usr/bin/python
# woo, python

# imports
import os.path
import cherrypy
import mimetypes
import urllib2
import socket
import json
import time # used for epoch
from cgi import escape

# project files
import dbHandler
import myCrypt
import serverInterface

# config
_listen_ip = "0.0.0.0"
_listen_port = 10002

_html_dir = "html/"
_css_dir = "css/"
_js_dir = "js/"
_img_dir = "img/"

# global variables
_user_dict = dict()

class MainApp(object):
    
    # CherryPy Configuration
    _cp_config = {'tools.encode.on': True, 
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on' : 'True',
                 }
    
    def authoriseUserLogin(self, username, passhash):
        error = serverInterface.report(username, passhash)
        return int(error[0]) # extract error code as int
    
    def sendPing(self, targetID, target_http_address, senderID):
		# Try pinging for connectivity 
		print "trying to ping " + targetID + " at " + target_http_address
		request_url = target_http_address + "ping?sender=" + senderID
		print request_url
		myRequest = urllib2.Request(request_url)
		try:
			myResponse = urllib2.urlopen(myRequest, timeout=2)
		except urllib2.URLError, e:
			print "Could not reach user " + targetID + " at " + target_http_address + " :("
			print e.args[0]
			return 0 # not connectable 
		except urllib2.HTTPError, e:
			print e.args[0]
			print "could not fing ping function"
			return 0 # not connectable
		except:
			print "an unknown error ocurred"
			return 0 # not connectable
		
		if myResponse.read() != "0":
			print "Invalid ping response from " + targetID + "!"
			return 0 # not connectable
		print "ping successful!"
		return 1 # connectable
	
    def html_escape(self, text):
		text_map = {
			"&": "&amp;",
			'"': "&quot;",
			"'": "&apos;",
			">": "&gt;",
			"<": "&lt;",
			"\n" : "<br />"
		}
		return "".join(text_map.get(c,c) for c in text)

	
    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "<h1>Error: 404</h1><h3>file not found</h3>"
        cherrypy.response.status = 404
        return Page
    
    # CSS serving
    @cherrypy.expose
    def css(self,fname):
        """ If they request some media, for example css files, set the content type of
        the response, read the file, and dump it out in the response."""
        cherrypy.response.headers['Content-Type'] = mimetypes.guess_type(fname)[0]
        f = open(_css_dir+fname,"r")
        data = f.read()
        f.close()
        return data
    
    # JS serving
    @cherrypy.expose
    def js(self,fname):
        cherrypy.response.headers['Content-Type'] = mimetypes.guess_type(fname)[0]
        f = open(_js_dir+fname,"r")
        data = f.read()
        f.close()
        return data
        
    # Image serving
    @cherrypy.expose
    def img(self,fname):
        cherrypy.response.headers['Content-Type'] = mimetypes.guess_type(fname)[0]
        f = open(_img_dir+fname,"r")
        data = f.read()
        f.close()
        return data
    
    # Login page (index)
    @cherrypy.expose
    def index(self):
        fileObject = open(_html_dir+"skeleton.html", "r")
        base_html = fileObject.read()
        
        # Setting HTML parameters and body
        page_title = "pyp2p: login"
        page_desc = "login page"
        css_path = _css_dir+"login.css"
        extra_head = ""
        fileObject = open(_html_dir+"login.html", "r")
        html_body = fileObject.read()
        fileObject.close()
        
        Page = base_html % (page_title, page_desc, css_path, extra_head, html_body) # Format HTML
        return Page
    
    # Client page
    @cherrypy.expose
    def client(self, username=None, password=None):
        
        # Set common parameters
        extra_head = ""
        fileObject = open(_html_dir+"skeleton.html", "r")
        base_html = fileObject.read()
        
        if (username == None and cherrypy.session.has_key('username') and cherrypy.session.has_key('password_hash')): # if there is no login attempt, but there is session info, check those first
            username = cherrypy.session['username']
            password_hash = cherrypy.session['password_hash']
            error = self.authoriseUserLogin(username,password_hash)
        elif (username != None and password != None): # if login is submitted, hash the password before checking
            password_hash = myCrypt.SHA256_serversalt_hex(password) # hash password for testing with server
            error = self.authoriseUserLogin(username,password_hash)
        else: # case for when no session OR submitted password
            error = -1
        
        #depending on authorisation, decide page content
        if (error == 0): # authorisation succeeded!
            # set session, used for and other messaging etc
            cherrypy.session['username'] = username
            cherrypy.session['password_hash'] = password_hash
            cherrypy.session['port'] = _listen_port
            #cherrypy.session['pubkey'] = #rsa public key
            cherrypy.session['enc'] = 0
            
            page_title = "IM Client"
            page_desc = "messaging client page"
            css_path = _css_dir+"client.css"
            # Load page content
            fileObject = open(_html_dir+"client.html", "r")
            html_body = fileObject.read()
            fileObject.close()            
        else:
            cherrypy.lib.sessions.expire() # clear any existing trash sessions
            page_title = "Login Error"
            page_desc = "error page"
            css_path = _css_dir+"error.css"
            # Load page content
            fileObject = open(_html_dir+"badlogin.html", "r")
            html_body = fileObject.read()
            fileObject.close()
        
        Page = base_html % (page_title, page_desc, css_path, extra_head, html_body) # Format HTML
        return Page
    
    @cherrypy.expose
    def logout(self):
        try:
            serverInterface.logoff(cherrypy.session['username'], cherrypy.session['password_hash'])
        except KeyError:
            print "<h3>session expired</h3>"
        cherrypy.lib.sessions.expire()
        return "<h3>logged out!<h3><button type=\"button\" onclick=\"javascript:window.close()\">Close</button>"    
    
    # API functions
    
    # listAPI - shows a list of APIs supported by this client
    @cherrypy.expose    
    def listAPI(self):
        output  = "/listAPI\r\n"
        output += "/ping [username]\r\n"
        output += "/receiveMessage [sender] [destination] [message] [stamp(opt)] [groupID(opt)] [encoding(opt)] [encryption(opt)] [hashing(opt)] [hash(opt)]\r\n"
        output += "Encoding 0\r\n"
        output += "Encryption 0 1\r\n"
        output += "Hashing 0"
        
        return output
    
    # ping - returns 0
    @cherrypy.expose
    def ping(self, sender):
        print sender + " pinged!"
        return str(0)
    
    # recieveMessage - called when another client sends a message to this client
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):
        try:
            encrypted_data = cherrypy.request.json # auto loads json
        except AttributeError, e:
            print "AttributeError: %s" % e.args[0]
            return str(1) # missing json (compulsory field)
        
        if(not encrypted_data.has_key("encryption") or encrypted_data["encryption"] == str(0)): #unencrypted
            raw_data = encrypted_data
        elif(encrypted_data["encryption"] == str(1)): #XOR
			raw_data = dict()
			for key,value in encrypted_data.items():
				raw_data[key] = myCrypt.XOR(value)
        else:
            return str(9) # unsupported standard
        
        if(raw_data.has_key("stamp")):
            storeTime = raw_data["stamp"]
        else:
            storeTime = time.time()
        
        try:
            dbHandler.saveMessage(raw_data["destination"], raw_data["sender"], storeTime, raw_data["sender"], raw_data["destination"], raw_data["message"])
        except TypeError, e:
            print e.args[0] + ", error receiving message"
            return str(1) # missing some compulsury json fields 
        
        print "successfully received message: " + raw_data["message"] + " from " + raw_data["sender"] + "!"
        return str(0)
        
    # acknowledge - called when another client wants to confirm they have received a message I sent
    # we can do whatever we like with this data
    @cherrypy.expose
    def acknowledge(self):
        return str(0)
    
    # JS Functions (local API)
    
    # Function called by javascript to get the messages in a particular table
    @cherrypy.expose
    def jsGetMessages(self, chatID=None, start_time=0):
        if(chatID==None or chatID==""):
            return "<h5>select a user to view messages</h5>" # insufficient arguments 
        elif(cherrypy.session.has_key('username')):
            try:
                messages = dbHandler.getMessages(cherrypy.session["username"], chatID, start_time)
            except:
                print "Error: getting messages from DB"
                return str(0)
            
            if (messages == None):
                return "<h5>" + chatID + "</h5><ul id=\"message_list\"><li>No messages found for user!</li></ul>"
            
            # build html
            output_html  = "<h5>" + chatID + "</h5>"
            output_html += "<ul id=\"message_list\">"
            for message in messages:
                if(message[1] == cherrypy.session["username"]):
                    message_class = "my_message"
                else:
                    message_class = "other_message"
                output_html += "<li class=\"" + message_class + "\"><span class=\"timestamp\">"
                output_html += "[" + time.strftime('%d/%m %X', time.localtime(message[0])) + "] </span>"
                output_html += "<span class=\"message_sender\">" + message[1] + ": </span>"
                output_html += "<span class=\"message_content\">" + self.html_escape(message[3]) + "</span>"
                output_html += "</li>"
            output_html += "</ul>"
            return output_html
        else:
            return str(-1) + "\r\nPlease log in again" # no login
    
    # Function called by javascript to maintain session with server
    @cherrypy.expose
    def jsAlive(self):
        print "keeping the session real"
        try:
            return serverInterface.report(cherrypy.session["username"], cherrypy.session["password_hash"])[0] # attempt to keep alive
        except:
            return str(-1) # session error
    
    # Function called by javascript to send a message
    @cherrypy.expose
    def jsSend(self, targetID=None, message=None):
        global _user_dict
        
        if(message==None or targetID==None):
            return str(-1) # insufficient arguments 
        elif(cherrypy.session.has_key("username")):
            print "attempting to send message: " + message + "\r\nto user: " + targetID
            
            if(_user_dict.has_key(targetID)):
                target_http_address = "http://" + _user_dict[targetID]["ip"] + ":" + _user_dict[targetID]["port"] + "/"
            else:
                return str(-5) + ", could not find user's IP" # user unknown
            
            # target_http_address = "http://127.0.0.1:10302/"
            
            if(_user_dict[targetID]["connectable"] != 1):
			    _user_dict[targetID]["connectable"] = self.sendPing(targetID, target_http_address, cherrypy.session["username"])
			    print "user " + targetID + " connectability is " + str(_user_dict[targetID]["connectable"])
				
            if(_user_dict[targetID]["connectable"] != 1):
                return str(-4) + ", could not ping target" # not connectable
            
            # Check target API for compatibility
            myRequest = urllib2.Request( target_http_address + "listAPI" )
            myResponse = urllib2.urlopen(myRequest)
            targetAPI = myResponse.read()
            if(targetAPI.find("/receiveMessage") < 0): # check if target client has not implemented /recieveMessage
                print "Wow! Client " + targetID + " has not even implemented /recieveMessage..."
                return str(-3) + ", client cannot receive message" # not implemented
            
            output_dict = { "sender" : cherrypy.session["username"] , "destination" : targetID, "message" : message, "encryption" : "0", "stamp" : time.time() }
            json_data = json.dumps(output_dict)
            myRequest = urllib2.Request( target_http_address + "receiveMessage", json_data, {'Content-Type':'application/json'})
            myResponse = urllib2.urlopen(myRequest)
            responseCode = myResponse.read()
            if(responseCode == "0"):
                print "message sent successfully!"
                dbHandler.saveMessage(cherrypy.session["username"], output_dict["destination"], output_dict["stamp"] , output_dict["sender"], output_dict["destination"], output_dict["message"]) # save message in db
            else:
				print "remote host rejected the message"
            return responseCode # return target's code
        else:
            return str(-2) # no login
    
    # Function called by javascript to get list of online users, returns HTML to display in friendslist
    @cherrypy.expose
    def jsGetUsers(self):
        global _user_dict
        
        try:
            raw_data = serverInterface.getList(cherrypy.session["username"], cherrypy.session["password_hash"]) # attempt to get users
        except KeyError:
            return str(-1) + "\r\nPlease log in again!" # session error
        
        if(raw_data[0] != "0"):
            return "server error: " + raw_data[0] # some kind of server error, return it
        
        try:
            head, csv_string = raw_data.split('\n', 1) # split message after first line to extract csv data
        except ValueError:
            return "<li>no one :(</li>" # no user list, instead return a sad message
        csv_list = csv_string.split('\r\n') # split into a list of csvs
        
        new_dict = dict()
        for row in csv_list:
            row_list = row.split(',')
            if(len(row_list) > 1):
                if(len(row_list) > 5):
                    public_key = row_list[5]
                else:
                    public_key = None
                new_dict[row_list[0]] = { "location" : row_list[1], "ip" : row_list[2], "port" : row_list[3], "last_seen" : row_list[4], "public_key" : public_key, "connectable" : -1 } # build updated user dictionary
        
        _user_dict = new_dict
        # print _user_dict
        
        output_html = ""
        for userID, userInfo in _user_dict.iteritems():
            if( userID != cherrypy.session["username"]):
                time_since_seen = int(time.time() - int(userInfo["last_seen"]))
                if(time_since_seen > 60):
                    image = "unknown.png" # last seen over 1 min ago!
                else:
                    image = "online.png" # last seen within the last minute
                if(False): # TODO
                    li_class = "new_message"
                else:
                    li_class = "no_message"
                output_html += "<a class=\"message_link\" href=\"javascript:setTarget(\'" + userID + "\')\" >"
                output_html += "<li class=\"" + li_class + "\" id=\"" + userID + " \">"
                output_html += "<span class=\"friendname\">[" + userInfo["location"] + "] " + userID + " </span>"
                output_html += "<img class=\"onlinestatus\" src=\"img/" + image + "\" /><br />"
                output_html += "<span class=\"lastseen\">Last seen: " + str(time_since_seen) + "s ago</span>"
                output_html += "</li></a>"
                output_html += "\n" #new line for readability
        
        return output_html
        
def runMainApp():
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), "/")

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': _listen_ip,
                            'server.socket_port': _listen_port,
                            'engine.autoreload.on': True,
                           })
    
    print "====================="
    print "| esay286 python IM |"
    print "====================="
    
    # Start the web server
    cherrypy.engine.start()

    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()
 
# Run the function to start everything
runMainApp()
