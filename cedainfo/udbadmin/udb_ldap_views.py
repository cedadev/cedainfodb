'''
Django views for ldap information generated from userdb
'''

import tempfile
import subprocess
import psycopg2
import os
from datetime import datetime
from operator import itemgetter

from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import *

from .models import Dataset
from .models import User

from . import udb_ldap
from . import update_check
from . import LDAP

def user_has_ldap_write_access(user):
    '''Indicates if logged in user is allowed to write to ldap server'''

    if user:
        if user.groups.filter(name='update_ldap_server').count() > 0:
            return True
 
    return False

@login_required()
def write_nis_group (request, datasetid):
    '''
     Write nis group file entry for the given group
    '''    
    
    record = udb_ldap.dataset_group_string (datasetid)
                   
    return HttpResponse(record, content_type="text/plain")
#
# Don't add login_required here as this is called from storm
# by a cron job 
#
def write_all_nis_groups (request):
    '''
    Writes nis group file entries for all groups managed by the userdb
    '''
    record = udb_ldap.generate_all_nis_groups()
                 
    return HttpResponse(record, content_type="text/plain")
    
@login_required()
def write_ldap_group (request, datasetid=''):
    '''
    Write ldap entry for the given group
    '''    
    
    record = ''
    
    if datasetid == 'open':
        record = udb_ldap.ldap_open_group_record()
    elif datasetid in list(udb_ldap.ARCHIVE_ACCESS_GROUPS.keys()):
        record = udb_ldap.ldap_archive_access_group_record(datasetid)
    else:
        dataset = Dataset.objects.get(datasetid=datasetid)
       
        if dataset.gid > 0:
            record = udb_ldap.ldap_group_record(datasetid)
                                 
    return HttpResponse(record, content_type="text/plain")
     
@login_required()
def write_ldap_user (request, accountid=''):
    '''
    Write ldap entry for the given user
    '''    
    record = udb_ldap.ldap_user_record(accountid)    

    return HttpResponse(record, content_type="text/plain")
 
@login_required()
def ldap_group_ldiff (request):
    """
    Displays differences between current LDAP information for ceda groups and 
    the information generated from the userdb using the ldifdiff.pl program.
    You can then send the commands to the LDAP server to update it.
    """

    server = settings.LDAP_WRITE_URL
 
    if request.method == 'POST':
        if not user_has_ldap_write_access(request.user):   
            return redirect('/udbadmin/ldap/accessdenied')

        ldif = request.POST.get('ldif', '') 
        
        if ldif:
#
#           Need to remove \r as otherwise ldap modify does not recognise
#           the '-' separator
#
            ldif = ldif.replace('\r', '')
            output = LDAP.ldif_write(ldif, server=server)

    else:
        stringout = udb_ldap.ldif_all_group_updates (server=server,select_groups=udb_ldap.userdb_managed_ldap_groups(), add_additions_file=False)
#       server_ldif = LDAP.ldif_all_groups(filter_scarf_users=True, server=server)                  
#       udb_ldif = udb_ldap.ldif_all_groups()
#                   
#       tmp_out = tempfile.NamedTemporaryFile()
#       script = settings.PROJECT_DIR + "/udbadmin/ldifdiff.pl"
#       p1 = subprocess.Popen([script, "-k", "dn", "--sharedattrs", 
#                               "memberUid", udb_ldif.name, server_ldif.name], stdout=tmp_out)
#       p1.wait()
#       
#       tmp_out2 = open(tmp_out.name, 'r')
#       diffoutput = tmp_out2.readlines()
#
#        stringout = ""
#
#        for i in range(len(diffoutput)):
#            stringout += diffoutput[i]
        
 
 
    return render_to_response('ldap_update_groups.html', locals())   
 
@login_required()     
def ldap_group_diff (request):
    """
    Displays differences between current LDAP information for ceda groups and 
    the information generated from the userdb using the diff2html program
    """
    
    ldif = LDAP.ldif_all_groups(filter_scarf_users=True, select_groups=udb_ldap.userdb_managed_ldap_groups())                  
    udb_ldif = udb_ldap.ldif_all_groups(add_additions_file=False)
           
    tmp_out = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/diff2html"
    p1 = subprocess.Popen([script, ldif.name, udb_ldif.name], stdout=tmp_out)   
    p1.wait()

    tmp_out2 = open(tmp_out.name, 'r')
    out = tmp_out2.readlines()
    
    
    return HttpResponse(out, content_type="text/html")
    
@login_required()
def ldap_groups (request):
    """
    Print out all group information from the LDAP server
    """
    fh = LDAP.ldif_all_groups(filter_scarf_users=False)            
  
    e = open(fh.name, 'r')
    record = e.readlines()
    header = 'LDIF group information from LDAP server %s\n\n' % settings.LDAP_URL
    record = [header] + record
    
    return HttpResponse(record, content_type="text/plain")

@login_required()
def ldap_groups_filtered (request):
    """
    Print out all group information from the LDAP server, filtered to show only groups controlled by ceda
    """
    fh = LDAP.ldif_all_groups(filter_scarf_users=True, select_groups=udb_ldap.userdb_managed_ldap_groups())            
  
    e = open(fh.name, 'r')
    record = e.readlines()
    header = 'LDIF group information from LDAP server %s filtered to show only groups controlled by CEDA \n\n' % settings.LDAP_URL
    record = [header] + record
    
    return HttpResponse(record, content_type="text/plain")

@login_required()
def ldap_udb_groups (request):
    '''
    Writes ldap entries for all groups managed by the userdb
    '''

    fh = udb_ldap.ldif_all_groups(add_additions_file=False) 
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Sorted LDIF group information from userdb\n\n'] + record
    return HttpResponse(record, content_type="text/plain")

@login_required()
def ldap_users (request):
    """
    Print out all user information from the current LDAP server
    """
    fh = LDAP.ldif_all_users(filter_root_users=False)            
  
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Sorted LDIF user information from LDAP server\n\n'] + record
    
    return HttpResponse(record, content_type="text/plain")

@login_required()
def ldap_user (request, uid):
    """
    Print out user information from the current LDAP server
    for the given uid
    """
 
    if int(uid) <=0:
        return HttpResponse('No UID set for user')

    fh  = LDAP.ldif_user(uid=uid)            
     
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Information from current LDAP server for uid: %s\n\n' % uid] + record
    
    return HttpResponse(record, content_type="text/plain")

@login_required()
def ldap_udb_user (request, userkey):
    '''
    Writes LDAP information for given user in userdb
    '''
    try:
        user    = User.objects.get(userkey=userkey)
    except:
        return HttpResponse('Error reading details from database for UserKey %s' % userkey)
    
    record = udb_ldap.ldap_user_record(user.accountid)

    body = record.split('\n')[1:]
    dn = record.split('\n')[0]

    output = 'Information from user database\n\n' + dn + '\n'.join(sorted(body))

    return HttpResponse(output, content_type="text/plain")

@login_required()
def ldap_udb_users (request):
    '''
    Writes ldap entries for all LDAP users managed by the userdb
    '''

    fh = udb_ldap.ldif_all_users() 
    e = open(fh.name, 'r')
    record = e.readlines()
    record = ['Sorted LDIF user information from userdb\n\n'] + record

    return HttpResponse(record, content_type="text/plain")

@login_required()
def ldap_udb_user_diff (request, userkey):
    '''
    Shows difference between ldap information from current server
    and ldap information from udb for single user.
    '''
    try:
        user    = User.objects.get(userkey=userkey)
    except:
        return HttpResponse('Error reading details from database for UserKey %s' % userkey)

    if user.uid <=0:
        return HttpResponse('No UID set for user')

    record = udb_ldap.ldap_user_record(user.accountid)
#
#   Sort the records, but leave the 'dn' at the top
#
    body = record.split('\n')[1:]
    dn = record.split('\n')[0]
    udb_output = dn + '\n'.join(sorted(body)) + '\n\n'
#
#   Write results to temporary file
#
    udb_file = tempfile.NamedTemporaryFile(delete=False)
    udb_file.write(udb_output)
    udb_file.close()
    udb_file = open(udb_file.name, 'r')

    ldif_fh  = LDAP.ldif_user(uid=user.uid)            
     
    d = tempfile.NamedTemporaryFile()
##    script = settings.PROJECT_DIR + "/udbadmin/diff2html"
    script = "/usr/bin/diff"
    p1 = subprocess.Popen([script, ldif_fh.name, udb_file.name], stdout=d)   
    p1.wait()

    os.remove(udb_file.name)

    e = open(d.name, 'r')
    output = e.readlines()

    return HttpResponse(output, content_type="text/plain")

@login_required()
def ldap_udb_user_ldif (request, userkey):
    '''
    Shows difference between ldap information from current server
    and ldap information from udb for single user.
    '''
    try:
        user    = User.objects.get(userkey=userkey)
    except:
        return HttpResponse('Error reading details from database for UserKey %s' % userkey)

    if user.uid <=0:
        return HttpResponse('No UID set for user')

    record = udb_ldap.ldap_user_record(user.accountid)
#
#   Sort the records, but leave the 'dn' at the top
#
    body = record.split('\n')[1:]
    dn = record.split('\n')[0]
    udb_output = dn + '\n'.join(sorted(body)) + '\n\n'
#
#   Write results to temporary file
#
    udb_file = tempfile.NamedTemporaryFile(delete=False)
    udb_file.write(udb_output)
    udb_file.close()
    udb_file = open(udb_file.name, 'r')

    ldif  = LDAP.ldif_user(uid=user.uid)            

    d = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/ldifdiff.pl"
    p1 = subprocess.Popen([script, "-k", "dn", "--sharedattrs", "description", "--sharedattrs", "objectClass",
                        udb_file.name, ldif.name], stdout=d)
    p1.wait()
#
#       Read the output and convert into a string
#    
    e = open(d.name, 'r')
    out = e.readlines()
    stringout = ""

    for i in range(len(out)):
        stringout += out[i]
   
    os.remove(udb_file.name)

##    return render_to_response('ldap_update_user.html', locals())
    return HttpResponse(stringout, content_type="text/plain")

@login_required()
def udp_ldap_new_members(request):

    udb_users = udb_ldap.all_jasmin_cems_users(order_by="accountid")

    ldap_accounts = LDAP.all_member_accountids()

    new_users = []

    for udb_user in udb_users:
        if udb_user.accountid not in ldap_accounts:
            new_users.append(udb_user)

    return render_to_response('list_new_jasmin_users.html', locals())   

@login_required()
def ldap_user_diff (request):
    """
    Displays differences between current LDAP information for ceda users and 
    the information generated from the userdb using the diff2html program
    """
    
    ldif = LDAP.ldif_all_users(filter_root_users=True)                  
    udb_ldif = udb_ldap.ldif_all_users(write_root_access=False)
           
    d = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/diff2html"
    p1 = subprocess.Popen([script, "-b", ldif.name, udb_ldif.name], stdout=d)   
    p1.wait()

    e = open(d.name, 'r')
    out = e.readlines()
    
    
    return HttpResponse(out, content_type="text/html")
    
@login_required()
def ldap_user_ldiff (request):
    """
    Displays differences between current LDAP information for ceda users and 
    the information generated from the userdb using the ldifdiff.pl program
    """

    server = settings.LDAP_WRITE_URL

    if request.method == 'POST':

        if not user_has_ldap_write_access(request.user):   
            return redirect('/udbadmin/ldap/accessdenied')
        
        ldif = request.POST.get('ldif', '') 
        output = LDAP.ldif_write(ldif, server=server)

    else:
        stringout = udb_ldap.ldif_all_user_updates (server=server)   

    return render_to_response('ldap_update_users.html', locals())   

@login_required()
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

@login_required()
def display_nis_external_passwd (request):
    '''Displays entries that should go in external nis passwd file.
       There may be other users to be added which are not in the user database, so
       this output should not be used without checking it.'''

    EXTERNAL_LOGIN_DATASET =  "system-login"
    CUTOFFDATE = datetime.strptime('01/07/2013', '%d/%m/%Y')

    users = User.objects.all().order_by('accountid')

    output  = ''

    for user in users:
        if user.uid != 0:
 
            if user.hasDataset(EXTERNAL_LOGIN_DATASET) or user.isJasminCemsUser():
                output = output + udb_ldap.user_passwd_file_entry(user) + '\n'
            else:
                if (user.accountid == 'mkochan' or \
                    user.accountid == 'myoshioka' or \
                    user.accountid == 'rtorres' or \
                    user.accountid == 'tjnightingale' or \
                    user.accountid == 'pwhitfield'):

                     output = output + udb_ldap.user_passwd_file_entry(user, overide_shell='/sbin/nologin') + '\n'
#
#               Add any users removed after we started using the LDAP system, but make sure
#               their shell is set to 'nologin'. 
#
                udjs = user.removedDatasets()

                for udj in udjs:
 
                    if (udj.datasetid.datasetid == EXTERNAL_LOGIN_DATASET and \
                       udj.removeddate > CUTOFFDATE):
                            output = output + udb_ldap.user_passwd_file_entry(user, overide_shell='/sbin/nologin') + '\n'


    return HttpResponse(output,content_type="text/plain")

@login_required()
def display_nis_internal_passwd (request):
    '''Displays entries that should go in internal nis passwd file.
       There may be other users to be added which are not in the user database, so
       this output should not be used without checking it.'''

    users = User.objects.all().order_by('accountid')

    output  = ''

    for user in users:
        if user.uid != 0:
 
            if user.hasDataset("vm_access_ceda_internal"):
                output = output + udb_ldap.user_passwd_file_entry(user) + '\n'

    return HttpResponse(output,content_type="text/plain")


@login_required()
def ldap_user_groups (request, userkey):

    try:
        user    = User.objects.get(userkey=userkey)
    except:
        return HttpResponse('Error reading details from database for UserKey %s' % userkey)
 
    if user.uid <=0:
        return HttpResponse('No UID set for user')

    groups = LDAP.member_groups(user.accountid)
    groups = sorted(groups, key=itemgetter('cn'))

    return render_to_response ('list_ldap_user_groups.html', locals()) 

@login_required()
@user_passes_test(user_has_ldap_write_access, login_url='/udbadmin/ldap/accessdenied')
def write_to_ldap_server(request):
        
    server = settings.LDAP_WRITE_URL

    if request.method == 'POST':
     
        ldif = request.POST.get('ldif', '') 
      
        if ldif:
            output = LDAP.ldif_write(ldif)
#           return HttpResponse(out, content_type="text/html")
 
    return render(request, 'write_to_ldap_server.html', locals())
