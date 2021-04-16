
import sys
import socket


name = sys.argv[1]
(hostname, aliaslist, ipaddrlist) = socket.gethostbyname_ex(name)
print (hostname, aliaslist, ipaddrlist)

        
