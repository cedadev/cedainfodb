#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
import sys
  
from udbadmin.models import *

DATASETID = "jasmin-login"

def run():
     
    udjs = Datasetjoin.objects.filter(datasetid=DATASETID).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []
    
    for udj in udjs:
       accountids.append(udj.userkey.accountid)
       
       
    accountids.sort()
    
    for accountid in accountids:
        print accountid   


