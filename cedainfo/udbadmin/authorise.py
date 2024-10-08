from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from django.contrib.auth.decorators import login_required


from datetime import datetime
from dateutil.relativedelta import relativedelta
import os, sys
import smtplib

from subprocess import *

from .models import *

def _add_user_to_jasmin_mailinglist (email, name):
#
#   Adds the given user details to the jasmin-users mailing list by
#   sending an email command
#

    FROM = "support@ceda.ac.uk"
    TO   = ("listserv@jiscmail.ac.uk", "andrew.harwood@stfc.ac.uk") 
    cmd = "add jasmin-users %s %s" % (email, name)

    message = """\
From: %s
To: %s
Subject: Adding %s (%s ) to jasmin-users mailing list

%s

    """ % (FROM, ",".join(TO), email, name, cmd)

    server = smtplib.SMTP("localhost")
    server.sendmail(FROM, TO, message)
    server.quit()


@login_required()
def authorise_datasets(request, userkey):

    
   if request.method == 'POST':

     if request.POST.get('remove_datasets', ''):
       for removeID in request.POST.getlist('remove'):
          udj = Datasetjoin.objects.get(id=removeID)
          udj.removeDataset()
     else:
     
        authorisorName = request.POST.get('name', '')
        expireMonths   = int(request.POST.get('expiremonths', 0))
        emailuser      = request.POST.get('emailuser', 'no')

        datasetsAdded = 0
        datasetsRejected = 0
        
        msg_sent = False
        added_to_jasmin_email_list = False
        msg_status = 0
        mailmsg = ''

        changes = 0
        manualProcessingRequired = 0
        uid_update = False
        
        infoString = []

        for name in list(request.POST.keys()):
   #
   #             Process any form parameters associated with requests
   #     
           if name.startswith('id_'):
              changes += 1
   #
   #                   Extract the request identifier number from the parameter value and make a datasetRequest object
   #
              value = request.POST.get(name)
              requestID = name.split('_')[1]
              datasetRequest = Datasetrequest.objects.get(id=requestID)

              if value == "accept":

                 dataset = Dataset.objects.get(datasetid=datasetRequest.datasetid)

                 if expireMonths == -1:
                     expireDate = datetime.strptime('01/01/2099', '%d/%m/%Y')   

                 elif expireMonths == 0:
                    userExpireDate = request.POST.get('userexpiredate', '')
                    
                    if userExpireDate:
                       try:
                          expireDate = datetime.strptime(userExpireDate, '%d/%m/%Y')
                       except:
                          return HttpResponse ("Invalid date string: '%s'. Use format 'dd/mm/yyyy'" % userExpireDate)   
                    else:
                       expireDate = datetime.now() + relativedelta(months=dataset.defaultreglength)
                       
                 else:
                    expireDate = datetime.now() + relativedelta(months=expireMonths)

                 datasetRequest.accept(expireDate=expireDate, endorsedby=authorisorName)

                 datasetsAdded += 1
#
#                If this is for jasmin-login, add to the jasmin-users mailing list
#                 
                 if dataset.datasetid == "jasmin-login" or \
                    dataset.datasetid == "cems-login" or \
                    dataset.datasetid == "commercial-login":
    
                    uid_update = True
    
                    datasetRequest.userkey.jasminaccountid = datasetRequest.userkey.accountid
                    datasetRequest.userkey.save()
 
                    uid = _add_uid(datasetRequest.userkey)
                     
                    try:
                        email = datasetRequest.userkey.emailaddress
                        name = datasetRequest.userkey.othernames + ' ' + \
                            datasetRequest.userkey.surname
                        _add_user_to_jasmin_mailinglist (email, name)
                        added_to_jasmin_email_list = True
                    except:
                        pass                     

                         
                 if dataset.manual_processing_required():
                     manualProcessingRequired += 1
                    
                 infoString.append ('Accepted %s' % datasetRequest.datasetid)

              elif value == "reject":
                 datasetsRejected += 1
                 datasetRequest.reject()
                 infoString.append ('Rejected %s' % datasetRequest.datasetid)
              elif value == "junk":
                 datasetRequest.junk()
                 infoString.append ('Junked %s' % datasetRequest.datasetid)              
              else:
                 pass      

        if changes == 0:
           return HttpResponse ("No updates requested")
   #
   #        If any datasets have been added then email user if requested
   #

        if datasetsAdded:
#
#                   Don't send email if all of the datasets are ones that require manual intervention 
#                   
           if emailuser.lower() == "yes" and (datasetsAdded > manualProcessingRequired):

       ##        userkey = 1  # Just for testing, so all messages go to Andrew rather than the user!
               userkey = datasetRequest.userkey
               msg_sent = True
               cmd = "/usr/local/cedainfodb/releases/current/cedainfo/udbadmin/scripts/new_datasets_notification/new_datasets_msg.py"
               m = Popen([cmd, "-send", "%s" % userkey])
               m.wait()
               msg_status = m.returncode

               mailmsg = Popen([cmd, "%s" % userkey], stdout=PIPE).communicate()[0] 

        return render (request, 'authorise_datasets_response.html', locals())
      
   
   try:
      cedauser = User.objects.get(userkey=userkey)
   except:
      return HttpResponse ("No user found with userkey %s" % userkey)

   datasets=cedauser.datasetjoin_set.all().filter(removed__exact=0).order_by('datasetid')
   removed_datasets=cedauser.datasetjoin_set.all().filter(removed__exact=-1).order_by('datasetid')

   requests = cedauser.datasetRequests(status='pending')
   
   request_history = cedauser.datasetRequests().order_by('-requestdate')   
#
#  Construct string containing authorisers name and store in a dictionary keyed on datasetid
#   
   authstring = {}
   
   for r in request_history:
       authstring[r.datasetid] = get_dataset_authoriser_string(r.datasetid)

   for r in datasets:
       authstring[r.datasetid] = get_dataset_authoriser_string(r.datasetid)

   for r in removed_datasets:
       authstring[r.datasetid] = get_dataset_authoriser_string(r.datasetid)
   

   authorisors = SiteUser.objects.all()

   user = request.user
   return render (request, 'authorise_datasets.html', locals())

def get_dataset_authoriser_string (datasetid):
#
#   Returns a list of dataset authorisers for the given datasetid. These are returned
#   as a string suitable for inserting into a tool-tip
#
    
    authoriser_string = ''
    
    try:
    
        priv = Privilege.objects.filter(datasetid=datasetid, type='authorise')


        if len(priv)==1:
            authoriser_string = 'Authoriser: '
        else:
            authoriser_string = '%s Authorisers: ' % len(priv)
        
        for p in priv:
            authoriser_string = authoriser_string + p.userkey.displayName() + ', '

        authoriser_string = authoriser_string.rstrip(', ')

    except:
        pass


    return authoriser_string

      
def _add_uid(user):
    '''
        Adds uid number to users details if not already defined
    '''
        
    if not user.uid:
        uid = _get_next_free_uid()
        if uid > 0:
            user.uid = uid
            user.save()
            
        return uid
    else:
        return user.uid
    
