#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
import sys
  
from udbadmin.models import *
import udbadmin.jasmin as jasmin

ARCHIVE_ACCESS_GROUPS = {"ecmwf": ["era", "ecmwfop"],
                         "ukmo" : [],
                         "esacat1": ["aatsr_multimission"],
}




def group_members_ext(datasetid):

    udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []
    
    for udj in udjs:
       if  udj.userkey.isExtNISUser():
           accountids.append(udj.userkey.accountid)
              
    accountids = list(set(accountids))
    accountids.sort()
    return accountids

def group_members_int(datasetid):

    udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []
    
    for udj in udjs:
       if  udj.userkey.isIntNISUser():
           accountids.append(udj.userkey.accountid)
              
    accountids = list(set(accountids))
    accountids.sort()
    return accountids
     

def run():

    ext_nis_groups = []
    
    for accessGroup in ARCHIVE_ACCESS_GROUPS.keys():
        group_info = {}
        group_info['uid'] = 999
        group_info['name'] = accessGroup
        
        
        ext_accounts = []
        
        for datasetid in ARCHIVE_ACCESS_GROUPS[accessGroup]:
            ext_accounts = ext_accounts + group_members_ext(datasetid)

        ext_accounts = list(set(ext_accounts))
        ext_accounts.sort()

        group_info['accounts'] = ext_accounts        
        group_info['accountString'] = ",".join(ext_accounts) 

        ext_nis_groups.append(group_info)        

    
   
  
    for info in ext_nis_groups:
       print info['name'], info['uid']
       
       for member in info['accounts']:
          print '   ', member

