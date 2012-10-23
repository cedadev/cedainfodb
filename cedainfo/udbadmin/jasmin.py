from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from django.contrib.auth.decorators import login_required

import os
import tempfile

import passwd

from models import *
import NISaccounts

@login_required()
def check_linux_groups(request):
#
#      Checks userdb groups that should correspond with groups on the external NIS server
#

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
      
