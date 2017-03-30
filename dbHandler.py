#!/usr/bin/python

import sqlite3

# Basic database functions
def dbConnect(db):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    return connection, cursor

def dbFinish(db_connection):
    db_connection.commit()
    db_connection.close()

# Code to deal with databasing interface
_messages_db_prefix = "messages_"
_messages_db_suffix = ".sqlite"

def getMessages(ownerID, chatID, startTime):
    try:
        myConnectionData = dbConnect(_messages_db_prefix + ownerID + _messages_db_suffix)
        try:
            myConnectionData[1].execute("SELECT time, sender, recipient, message from " + chatID + " WHERE time>=?;", str(startTime))
            messages = myConnectionData[1].fetchall()
        except sqlite3.Error, e:
            print "sqlite error: \r\n%s\r\n(no history for " %e.args[0] + chatID + ")"
            messages = None
        dbFinish(myConnectionData[0])
        return messages
            
    except sqlite3.Error, e: 
        print "sqlite3 critical error:\r\n%s" % e.args[0]
        # if(myConnectionData[0]):
            # myConnectionData[0].close # end any zombie connections
        return None
    
def saveMessage(ownerID, chatID, epochTime, senderID, recipientID, message):
    try:
        myConnectionData = dbConnect(_messages_db_prefix + ownerID + _messages_db_suffix)
        myConnectionData[1].execute("CREATE TABLE IF NOT EXISTS " + chatID + " ( "
                                  + "time INTEGER," 
                                  + "sender TEXT,"
                                  + "recipient TEXT,"
                                  + "message TEXT );") # make sure the table for this user exists, create it if it doesn't
        saveData = [epochTime, senderID, recipientID, message]
        myConnectionData[1].execute("INSERT into " + chatID + " VALUES(?, ?, ?, ?)", saveData) # write in message
        dbFinish(myConnectionData[0])
        return 0
    
    except sqlite3.Error, e: 
        print "sqlite3 critical error:\r\n%s" % e.args[0]
        # if(myConnectionData):
            # myConnectionData[0].close # end any zombie connections
        return 1