from django.http import HttpResponse

from models import *
import udb_ldap


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
    Write nis group file entry for the given group
    '''    
    
    record = udb_ldap.dataset_group_string (dataset.datasetid)
                   
    return HttpResponse(record, content_type="text/plain")

       
    
def write_all_ldap_groups (request):
    '''
    Writes nis group file entries for all groups managed by the userdb
    '''
    record = udb_ldap.generate_all_nis_groups()
                 
    return HttpResponse(record, content_type="text/plain")
     

