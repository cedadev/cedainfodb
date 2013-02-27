from operator import attrgetter

import os

from django.http import HttpResponse

from models import *
import udb_ldap

ADDITIONAL_LDAP_GROUP_FILE = "/home/badc/etc/infrastructure/accounts/ldap/ldap_additional_groups.txt"


def write_nis_group (request, datasetid=''):
    '''
     Write nis group file entry for the given group
    '''    
    
    record = udb_ldap.dataset_group_string (dataset.datasetid)
                   
    return HttpResponse(record, content_type="text/plain")


def write_all_nis_groups (request):
    '''
    Writes nis group file entries for all groups managed by the userdb
    '''
    record = udb_ldap.generate_all_nis_groups()
                 
    return HttpResponse(record, content_type="text/plain")
    


def write_ldap_group (request, datasetid=''):
    '''
    Write ldap entry for the given group
    '''    
    
    record = ''
    
    if datasetid == 'open':
       record = udb_ldap.ldap_open_group_record()
    elif datasetid in udb_ldap.ARCHIVE_ACCESS_GROUPS.keys():
       record = udb_ldap.ldap_archive_access_group_record(datasetid)
    else:
       dataset = Dataset.objects.get(datasetid=datasetid)
       
       if dataset.gid > 0:
           record = udb_ldap.ldap_group_record(datasetid)
                                 
    return HttpResponse(record, content_type="text/plain")

       
    
def write_all_ldap_groups (request):
    '''
    Writes ldap entries for all groups managed by the userdb
    '''

    datasets = Dataset.objects.all().filter(gid__gt=0).order_by('grp')

    record = ''
        
    for dataset in datasets:
        record = record + udb_ldap.ldap_group_record(dataset.datasetid)                
        record = record + '\n'
    

    for datasetid in udb_ldap.ARCHIVE_ACCESS_GROUPS.keys():
        record = record + udb_ldap.ldap_archive_access_group_record(datasetid)
        record = record + '\n'
        
    record = record + udb_ldap.ldap_open_group_record()

    if os.path.exists(ADDITIONAL_LDAP_GROUP_FILE):
        f = open(ADDITIONAL_LDAP_GROUP_FILE, "r")

        additional_groups = f.read()
        record = record + additional_groups    
        
    return HttpResponse(record, content_type="text/plain")
     

def write_ldap_user (request, accountid=''):
    '''
    Write ldap entry for the given user
    '''    
    record = udb_ldap.ldap_user_record(accountid)    

    return HttpResponse(record, content_type="text/plain")

           
def write_all_ldap_users (request):
    '''
    Writes ldap entries for all LDAP users
    '''


    record = ''
        
    users = udb_ldap.all_users(order_by="accountid")

#    users = udb_ldap.get_dataset_users("jasmin-login")
#    users.sort(key=attrgetter('accountid'))
        
    for user in users:
        record = record + udb_ldap.ldap_user_record(user.accountid) + '\n'
           
    return HttpResponse(record, content_type="text/plain")

