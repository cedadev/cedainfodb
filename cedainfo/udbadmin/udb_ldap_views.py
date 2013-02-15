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
        
    return HttpResponse(record, content_type="text/plain")
     

