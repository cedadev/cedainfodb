#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
#  Reads a list of accountids piped into standard input and prints out the 
#  associated email address
#
import sys
import socket

#from udbadmin.models import User
#from cedainfoapp.models import *


try: 
     name = '00 un'
     address = socket.gethostbyname(name)
     print ('Pass', name, address)
except:
     print ('Fail', name)
     
#def run():
#
#    vms = VM.objects.all()
#    
#    for vm in vms:
#        if vm.status == 'active':
#            name = vm.name
#            name = name.replace('legacy:', '')
#  
#            try:
#                address = socket.gethostbyname(name)
#                print ('Pass', name)
#            except:
#                print ('Fail', name)
