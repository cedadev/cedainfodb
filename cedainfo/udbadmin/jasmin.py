from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from django.contrib.auth.decorators import login_required

import os
import sys
import tempfile

from models import *
import NISaccounts


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
    datasets = Dataset.objects.all().filter(datasetid__startswith='gws_')
   
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
                     
           if not user.accountid in dataset.linux_users:
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
      
     


ARCHIVE_ACCESS_GROUPS = {"cmip5_research":[],

                         "esacat1": ["aatsr_multimission"],                         
                         "ecmwf": ["era", "ecmwfop"],
                         "ukmo" : ["surface"],
                         "eurosat": ["metop_iasi"],
                         "open": [],
}


def group_members_ext(datasetid):
    """
    Returns list of accountids that should be able to access the given group
    on the external NIS server.
    """
    udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []
    
    for udj in udjs:
       if  udj.userkey.isExtNISUser():
           accountids.append(udj.userkey.accountid)
              
    return _unique(accountids)

def group_members_int(datasetid):
    """
    Returns list of accountids that should be able to access the given group
    on the internal NIS server.
    """
 
    udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []
    
    for udj in udjs:
       if  udj.userkey.isIntNISUser():
           accountids.append(udj.userkey.accountid)
              
    return _unique(accountids)

def group_members(datasetid, server='external'):
    """
    Returns list of accountids that should be able to access the given group
    on the internal NIS server.
    """
 
    udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)
    
    accountids = []

    if server == 'external':    
        for udj in udjs:
           if  udj.userkey.isExtNISUser():
               accountids.append(udj.userkey.accountid)
    else:        
        for udj in udjs:
           if  udj.userkey.isIntNISUser():
               accountids.append(udj.userkey.accountid)
                  
    return _unique(accountids)

def get_nis_group_entries(server='external'):
    
    nis_groups = []

    if server == 'external':
       groupFile = NISaccounts.getExtGroupFile()   
    else:
       groupFile = NISaccounts.getIntGroupFile()   

    for accessGroup in ARCHIVE_ACCESS_GROUPS.keys():
        group_info = {}
        group_info['uid'] = 999
        group_info['name'] = accessGroup
               
        accounts = []
        
        for datasetid in ARCHIVE_ACCESS_GROUPS[accessGroup]:
            accounts = accounts + group_members(datasetid, server=server)
#
#             Sort and remove any duplicates
#
        accounts = _unique(accounts)
        group_info['accounts']      = ['badc', 'prototype'] +accounts        
        group_info['accountString'] = ",".join(group_info['accounts']) 

        group_info['nisAccounts'] = groupFile[accessGroup].users 
        group_info['nisAccountsString'] = ",".join(groupFile[accessGroup].users)
        
        group_info['diff1'] = _list_difference(group_info['accounts'] , group_info['nisAccounts'])
        group_info['diff2'] = _list_difference(group_info['nisAccounts'], group_info['accounts'])

        group_info['datasets'] = ARCHIVE_ACCESS_GROUPS[accessGroup]
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


          
        
        


