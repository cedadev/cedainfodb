from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from django.contrib.auth.decorators import login_required

import os
import sys
import tempfile
import LDAP
import subprocess
from operator import itemgetter

from models import *
from udbadmin.forms import *
import NISaccounts
import udb_ldap

def _unique(array):
    """Removes duplicates from given list and sorts results"""
        
    array = list(set(array))
    array.sort()
    return array
 
def _list_difference(list1, list2):
    """uses list1 as the reference, returns list of items not in list2"""
    
    diff_list = []
    for item in list1:
        if not item in list2:
            diff_list.append(item)
    return diff_list


@login_required()
def ldap_list_root_users(request):
    """
    Lists LDAP users that have root access
    """      
    
    info = []
             
    groupNames = LDAP.rootAccessGroupNameValues()

    LDAPRootAccessAccountIDs = []
    notInLDAP                = []     
   
    for name in groupNames:
    
        if not (name == 'NON-STAFF' or name == 'NON_STAFF' or name == 'EX-STAFF'):
            members = LDAP.attribute_members('rootAccessGroupName', name)
            
            for member in members:
                #
                # Check udb to see if user should have root access or not
                #            
                accountid = member['uid'][0]
               
                LDAPRootAccessAccountIDs.append(accountid)
                
                user = User.objects.get(accountid=accountid)  
                if user.hasDataset("vm_root"):
                    member['udbRootAccess'] = True
                else:
                    member['udbRootAccess'] = False                
                      
            info.append((name, members))
#
#      Check for any users in the userdb who are not in LDAP
#
    udjJoin  = Datasetjoin.objects.filter(datasetid="vm_root").filter(userkey__gt=0).filter(removed=0)            
            
    for entry in udjJoin:
        if entry.userkey.accountid not in LDAPRootAccessAccountIDs:
            notInLDAP.append(entry.userkey.accountid)
 
        
    return render_to_response ('ldap_list_root_users.html', locals())

@login_required()
def ldap_list_root_users2(request):

    myform = JasminUsersForm(request.GET)
    
    valid = myform.is_valid()
    
    all_users = []
    
    if myform.cleaned_data['show_ceda_users']:
        users = _get_ldap_root_users(base="ou=ceda,ou=People,o=hpc,dc=rl,dc=ac,dc=uk")
        all_users = all_users + users
    if myform.cleaned_data['show_jasmin_users']:
        users = _get_ldap_root_users(base="ou=jasmin,ou=People,o=hpc,dc=rl,dc=ac,dc=uk")
        all_users = all_users + users
#
#   Add information from userdb if available for this user
#
    for user in all_users:
        
        user['email'] = ''
        user['udb_user'] = None
        
        if user['uidnumber']:
            try:
                udb_user = User.objects.get(uid=user['uidnumber'])
                user['udb_user'] = udb_user 
                user['email'] = udb_user.emailaddress.lower()
            except:
                user['email'] =  _gt_stfc_email (user['uid'])
                
                
    all_users = sorted(all_users, key=itemgetter('email'))
             
    return render_to_response ('ldap_list_root_users2.html', locals())    

def _get_ldap_root_users (base="ou=ceda,ou=People,o=hpc,dc=rl,dc=ac,dc=uk"):
    """
    Returns details of root users from LDAP database for given base
    """
   
    out = subprocess.check_output(["ldapsearch", "-LLL",  "-x", "-H", "ldap://homer.esc.rl.ac.uk", 
                                   "-b", base, 
                                   "(&(!(rootAccessGroupName=NON-STAFF))(!(rootAccessGroupName=EX-STAFF))(rootAccessGroupName=*))",
                                   "uid", "uidnumber", "gecos", "cn"])

#    out = subprocess.check_output(["ldapsearch", "-LLL",  "-x", "-H", "ldap://homer.esc.rl.ac.uk", 
#                                   "-b", base, "uid", "uidnumber", "gecos", "cn"])
        
    users = []
    
    lines = out.splitlines()
          
    for n in range(len(lines)):
        if lines[n].startswith('dn:'): 
            user = {'uid': '', 'uidnumber': None, 'gecos': '', 'cn': ''}
            
            for m in range(1, 5): 
                
                if n+m >= len(lines):
                    break
                
                if lines[n+m].startswith('uid:'):
                    user['uid'] = lines[n+m].split()[1]

                if lines[n+m].startswith('uidNumber:'):
                    user['uidnumber'] = int(lines[n+m].split()[1])

                if lines[n+m].startswith('gecos:'):
                    gecos = lines[n+m].replace('gecos: ', '')
                    user['gecos'] = gecos

                if lines[n+m].startswith('cn:'):
                    cn = lines[n+m].replace('cn: ', '')
                    user['cn'] = cn 

            users.append(user)

    return users

def _gt_stfc_email (cn):
    """
    Returns stfc email for given common name (accountid), or None if not found
    """
    
    out = subprocess.check_output(["ldapsearch", "-LLL",  "-x", 
                                   "-h", "ralfed.cclrc.ac.uk", 
                                   "-b", "DC=fed,DC=cclrc,DC=ac,DC=uk", 
                                   "cn=%s" % cn])
    
    lines = out.splitlines()
          
    for line in lines:
        if line.startswith('mail: '):
            email = line.split()[1]
            return email

    return None
   
@login_required()
def list_jasmin_users(request, tag=''):
    """
    Lists LDAP users which have the given tag in the LDAP database
    """    
    
    tag = request.REQUEST.get('tagname', 'cluster:jasmin-login')
    
#    if request.method == 'POST':
#        tag = request.POST.get('tagname', '')  
#    else:
#        tag = 'cluster:jasmin-login'
           
    users = LDAP.tag_members(tag)
    
    for user in users:
       accountID = user['uid'][0]
       groups = LDAP.member_groups(accountID)
       groups = sorted(groups, key=itemgetter('cn'))
       user['groups'] = groups
       
#       try:
#           udbuser = User.objects.get(accountid=accountID)
#           user['udbuser'] = udbuser
#       except:
#           user['udbuser'] = None

    myform = LDAPuserForm(initial={'tagname':tag},)
           
    return render_to_response ('list_jasmin_users.html', locals())
   
@login_required()
def ldap_group_details(request, group=''):
    """
    Lists details of the given group in the LDAP database
    """    
    
    details = LDAP.group_details(group)
          
    return render_to_response ('ldap_group_details.html', locals())

   
@login_required()
def ldap_user_details(request, accountid=''):
    """
    Lists details of the given user in the LDAP database
    """    
    
    details = LDAP.member_details(accountid)
          
    return render_to_response ('ldap_user_details.html', locals())

@login_required()
def ldap_list_groups(request):
    """
    Lists all groups in the LDAP database
    """    
    
    groupsInfo = LDAP.ceda_groups()
          
    return render_to_response ('ldap_list_groups.html', locals())
    
@login_required()
def check_linux_groups(request):
    """
      Checks userdb groups that should correspond with groups on the external NIS server
    """

#
#   Get NIS group file, as returned by the 'passwdfile' module
#
    group = NISaccounts.getExtGroupFile()
#
#   Get all datasets that should correspond with NIS groups. Currently this is just any
#   datasetid that starts with 'gws_' ('group workspace'), but it might need to be changed
#   to use another method.
#    
#    datasets = Dataset.objects.all().filter(datasetid__startswith='gws_')
    datasets = Dataset.objects.all().filter(gid__gt=0)
   
    for dataset in datasets:
            
        dataset.users               = []  
        dataset.usersNotInGroupFile = []
        dataset.usersNotInUserdb    = []
#
#       Get any users for this dataset from NIS
#    
        try:
            dataset.linux_users = group[dataset.grp].users
        except:
            dataset.linux_users = []
#
#       Get any registrations for this dataset from the userdb
#
        recs = Datasetjoin.objects.filter(datasetid=dataset.datasetid).filter(userkey__gt=0).filter(removed=0)
                          
        for rec in recs:
           user = User.objects.get(userkey=rec.userkey.userkey)
           dataset.users.append(user)
                 
           if (user.isJasminCemsUser() or user.hasDataset("system-login")) and (not user.accountid in dataset.linux_users):
              dataset.usersNotInGroupFile.append(user)
 #
 #      Now check that each member of the group in the NIS file also has a registration
 #      in the userdb. Store details of any users which are not found
 #
        for entry in dataset.linux_users:
            if entry:
                found = False

                for user in dataset.users:
                   if user.accountid == entry:
                      found = True
                      break

                if not found:                   
                   dataset.usersNotInUserdb.append(entry)

           
    return render_to_response ('check_linux_groups.html', locals())
     
def group_members(datasetid, server='external'):
    """
    Returns list of accountids that should be able to access the given group
    on the given NIS server.
    """
 
    udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []

    if server == 'external':  
      
        for udj in udjs:
           if udb_ldap.is_ldap_user(udj.userkey):
#           if NISaccounts.isExtNISUser(udj.userkey):
               accountids.append(udj.userkey.accountid)
    else:        
        for udj in udjs:
           if NISaccounts.isIntNISUser(udj.userkey):
               accountids.append(udj.userkey.accountid)
                  
    return _unique(accountids)

def get_nis_group_entries(server='external'):
    
    nis_groups = []

    if server == 'external':
       groupFile = NISaccounts.getExtGroupFile()   
    else:
       groupFile = NISaccounts.getIntGroupFile()   

    for accessGroup in udb_ldap.ARCHIVE_ACCESS_GROUPS.keys():
        if not accessGroup in groupFile:
            continue    
 
        group_info = {}
        group_info['uid'] = 999
        group_info['name'] = accessGroup
               
        accounts = []
        
        for datasetid in udb_ldap.ARCHIVE_ACCESS_GROUPS[accessGroup]["datasets"]:
            accounts = accounts + group_members(datasetid, server=server)
#
#             Sort and remove any duplicates
#
        accounts = _unique(accounts)
#
#              Add any known general users
#
        if server == 'external':
            group_info['accounts']      = ['badc', 'prototype', 'cwps'] + accounts        
        else:
            group_info['accounts']      = ['badc', 'prototype', 'cwps'] + accounts        
        
        group_info['accountString'] = ",".join(group_info['accounts']) 

        group_info['nisAccounts'] = groupFile[accessGroup].users 
        group_info['nisAccountsString'] = ",".join(groupFile[accessGroup].users)
        
        group_info['diff1'] = _list_difference(group_info['accounts'] , group_info['nisAccounts'])
        group_info['diff2'] = _list_difference(group_info['nisAccounts'], group_info['accounts'])

        group_info['datasets'] = udb_ldap.ARCHIVE_ACCESS_GROUPS[accessGroup]["datasets"]
        nis_groups.append(group_info)   
             
    return nis_groups

@login_required()
def nis_group_entries(request, server='external'):
    """
    
    """     
        
    ext_nis_groups = get_nis_group_entries(server='external')
    int_nis_groups = get_nis_group_entries(server='internal')

    group = NISaccounts.getExtGroupFile()
        
    return render_to_response ('nis_group_entries.html', locals())


          
        
        


