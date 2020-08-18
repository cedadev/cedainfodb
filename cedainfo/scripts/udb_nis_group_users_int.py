#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
import sys
  
from udbadmin.models import *
import NISaccounts

DATASETID = "metop_iasi"

def run():

    intPasswd = NISaccounts.getIntPasswdFile()
    
    udjs = Datasetjoin.objects.filter(datasetid=DATASETID).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []
    
    for udj in udjs:
       accountids.append(udj.userkey.accountid)
       
       
    accountids = list(set(accountids))
    accountids.sort()
        

    group = NISaccounts.getIntGroupFile()
    
    
    for user in group[DATASETID].users:
       if user not in accountids:
          accountids.append(user)
          
          
    accountids = list(set(accountids))
    accountids.sort()

          
    for accountid in accountids:
        if accountid in list(intPasswd.keys()):
           sys.stdout.write( "%s," % accountid)
   
    print() 
    
    
#    print 'Users in NIS group, but not set in userdb: '
#        
#    for user in group[DATASETID].users:
#        print user
    
    
    
    
  


