#!/usr/bin/python
import Crypto.Hash.MD5
import Crypto.Hash.SHA256 
import Crypto.Hash.SHA512

_XOR_KEY = 0b01101001
_SHA256_SERVER_SALT = "COMPSYS302-2015"
_AES256_KEY = '491d2a0b5008b43c546df27a'


def XOR(string):
	outstring = str()
	for char in string:
		outstring += chr(ord(char) ^ _XOR_KEY)
	return outstring

def MD5_hex(string, salt=""): # salt argument is optional (hashing code 1)
    hash = Crypto.Hash.MD5.new()
    hash.update(string + salt)
    return hash.hexdigest()
    
def SHA256_hex(string, salt=""): # salt argument is optional (hashing code 1)
    hash = Crypto.Hash.SHA256.new()
    hash.update(string)
    return hash.hexdigest()
    
def SHA256_serversalt_hex(string): # uses server's salt automatically
    hash = Crypto.Hash.SHA256.new()
    hash.update(string + _SHA256_SERVER_SALT)
    return hash.hexdigest()
    
def SHA512_hex(string, salt=""): # salt argument is optional (hashing code 1)
    hash = Crypto.Hash.SHA512.new()
    hash.update(string)
    return hash.hexdigest()
