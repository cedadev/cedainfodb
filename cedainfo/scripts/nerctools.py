
#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
import sys
import os
import struct

from django.core.management import setup_environ
from django.conf import settings

sys.path.append('/pyEnv/ve/cedainfo/cedainfo')

import settings as dbsettings
import tempfile
import os
import subprocess

setup_environ(dbsettings)




from udbadmin.models import *
from django.db.models import Q

DATASETID = "jasmin-login"

def run():
     
    udjs = Datasetjoin.objects.filter(Q (datasetid='jasmin-login') | Q(datasetid='cems-login')).filter(removed=0)
    
    
    for udj in udjs:
    
        print(udj.userkey.userkey)

        if udj.userkey.userkey == 1:
            print('AAAAAAA')
            continue
        
        nerctools = Datasetjoin.objects.filter(userkey=udj.userkey).filter(datasetid='nerctools')

        if udj.userkey == 1:
            print('ZZZ', udj.userkey)
    
        if len(nerctools) <= 0:
            print('Add nerctools to ', udj.userkey)

        else:
            print('already got nerctools')    

    
      
    
    
#    accountids = []
#    
#    for udj in udjs:
#       accountids.append(udj.userkey.accountid)
#       
#       
#    accountids.sort()
#    
#    for accountid in accountids:
#        print accountid   


