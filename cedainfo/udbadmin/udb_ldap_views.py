'''
Django views for ldap information generated from userdb
'''

import tempfile
import subprocess
import psycopg2

from django.http import HttpResponse
from django.conf import settings


from models import Dataset

import udb_ldap
import update_check
import LDAP


def write_nis_group (request, datasetid):
    '''
     Write nis group file entry for the given group
    '''    
    
    record = udb_ldap.dataset_group_string (datasetid)
                   
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
     

def write_ldap_user (request, accountid=''):
    '''
    Write ldap entry for the given user
    '''    
    record = udb_ldap.ldap_user_record(accountid)    

    return HttpResponse(record, content_type="text/plain")

       

def ldap_group_ldiff (request):
    """
    Displays differences between current LDAP information for ceda groups and 
    the information generated from the userdb using the ldifdiff.pl program
    """
 
    ldif = LDAP.ldif_all_groups()                  
    udb_ldif = udb_ldap.ldif_all_groups()
             
    tmp_out = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/ldifdiff.pl"
    p1 = subprocess.Popen([script, "-k", "dn", "--sharedattrs", 
                          "memberUid", udb_ldif.name, ldif.name], stdout=tmp_out)
    p1.wait()
    
    tmp_out2 = open(tmp_out.name, 'r')
    out = tmp_out2.readlines()
    
    return HttpResponse(out, content_type="text/plain")
 
     
def ldap_group_diff (request):
    """
    Displays differences between current LDAP information for ceda groups and 
    the information generated from the userdb using the diff2html program
    """
    
    ldif = LDAP.ldif_all_groups()                  
    udb_ldif = udb_ldap.ldif_all_groups()
           
    tmp_out = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/diff2html"
    p1 = subprocess.Popen([script, ldif.name, udb_ldif.name], stdout=tmp_out)   
    p1.wait()

    tmp_out2 = open(tmp_out.name, 'r')
    out = tmp_out2.readlines()
    
    
    return HttpResponse(out, content_type="text/html")
    

def ldap_groups (request):
    """
    Print out all group information from the LDAP server
    """
    fh = LDAP.ldif_all_groups()            
  
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['LDIF group information from LDAP server\n\n'] + record
    
    return HttpResponse(record, content_type="text/plain")

def ldap_udb_groups (request):
    '''
    Writes ldap entries for all groups managed by the userdb
    '''

    fh = udb_ldap.ldif_all_groups() 
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Sorted LDIF group information from userdb\n\n'] + record
    return HttpResponse(record, content_type="text/plain")

def ldap_users (request):
    """
    Print out all user information from the current LDAP server
    """
    fh = LDAP.ldif_all_users()            
  
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Sorted LDIF user information from LDAP server\n\n'] + record
    
    return HttpResponse(record, content_type="text/plain")

def ldap_udb_users (request):
    '''
    Writes ldap entries for all LDAP users managed by the userdb
    '''

    fh = udb_ldap.ldif_all_users() 
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Sorted LDIF user information from userdb\n\n'] + record

    return HttpResponse(record, content_type="text/plain")

def ldap_user_diff (request):
    """
    Displays differences between current LDAP information for ceda users and 
    the information generated from the userdb using the diff2html program
    """
    
    ldif = LDAP.ldif_all_users()                  
    udb_ldif = udb_ldap.ldif_all_users()
           
    d = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/diff2html"
    p1 = subprocess.Popen([script, "-b", ldif.name, udb_ldif.name], stdout=d)   
    p1.wait()

    e = open(d.name, 'r')
    out = e.readlines()
    
    
    return HttpResponse(out, content_type="text/html")
    
def ldap_user_ldiff (request):
    """
    Displays differences between current LDAP information for ceda users and 
    the information generated from the userdb using the ldifdiff.pl program
    """
 
    ldif = LDAP.ldif_all_users()                  
    udb_ldif = udb_ldap.ldif_all_users()
             
    d = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/ldifdiff.pl"
    p1 = subprocess.Popen([script, "-k", "dn", "--sharedattrs", "memberUid", 
                           udb_ldif.name, ldif.name], stdout=d)
    p1.wait()
    
    e = open(d.name, 'r')
    out = e.readlines()
    
    return HttpResponse(out, content_type="text/plain")


def check_udb_for_updates (request):
    '''
    Check if any updates have been made to the userdb that may require the 
    jasmin/cems account and group information to be updated.
    '''
    
    label = request.GET.get('label', 'jasmin')

    if 'noreset' in request.GET:
        reset = False
    else:
        reset = True    

    dbconf = settings.DATABASES['userdb']
    connection = psycopg2.connect(dbname=dbconf['NAME'], 
                                  host=dbconf['HOST'],
                                  user=dbconf['USER'], 
                                  password=dbconf['PASSWORD'])
    
    user_updated  = update_check.user_updated(connection, name = 
                                              label + '_user', reset=reset)
    group_updated = update_check.group_updated(connection, name = 
                                               label + '_group', reset=reset)
    
    connection.close()
    
    msg = ''
       
    if user_updated:
        msg = msg + 'user_updated=True\n'
    else:
        msg = msg + 'user_updated=False\n'
          
    if group_updated:
        msg = msg + 'group_updated=True\n' 
    else:
        msg = msg + 'group_updated=False\n'
              
    return HttpResponse(msg, content_type="text/plain")
    
