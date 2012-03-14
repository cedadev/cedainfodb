from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from subprocess import *

from models import *


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

	infoString = []

	for name in request.POST.keys():
   #
   #             Process any form parameters associated with requests
   #     
           if name.startswith('id_'):
   #
   #                   Extract the request identifier number from the parameter value and make a datasetRequest object
   #
	      value = request.POST.get(name)
	      requestID = name.split('_')[1]
	      datasetRequest = Datasetrequest.objects.get(id=requestID)

	      if value == "accept":

		 dataset = Dataset.objects.get(datasetid=datasetRequest.datasetid)

        	 if expireMonths == 0:
	            expireDate = datetime.now() + relativedelta(months=dataset.defaultreglength)
		 else:
	            expireDate = datetime.now() + relativedelta(months=expireMonths)

		 datasetRequest.accept(expireDate=expireDate, endorsedby=authorisorName)

		 datasetsAdded += 1
		 infoString.append ('Accepted %s' % datasetRequest.datasetid)

	      elif value == "reject":
		 datasetRequest.reject()
		 infoString.append ('Rejected %s' % datasetRequest.datasetid)
	      elif value == "junk":
		 datasetRequest.junk()
		 infoString.append ('Junked %s' % datasetRequest.datasetid)	      
	      else:
		 pass      

   #
   #        If any datasets have been added then email user if requested
   #

	if datasetsAdded and emailuser.lower() == "yes":

   ##        userkey = 1  # Just for testing, so all messages go to Andrew rather than the user!
	   userkey = datasetRequest.userkey

	   if datasetRequest.datasetid.datacentre.lower() == "neodc":
	      cmd = "/home/badc/software/infrastructure/useradmin/bin/new_datasets_msg_neodc"
	      Popen([cmd, "-send", "%s" % userkey])
              mailmsg = Popen([cmd, "%s" % userkey], stdout=PIPE).communicate()[0] 
	   else:
	      cmd = "/home/badc/software/infrastructure/useradmin/bin/new_datasets_msg"
              Popen([cmd, "-send", "%s" % userkey])
              mailmsg = Popen([cmd, "%s" % userkey], stdout=PIPE).communicate()[0] 

	return render_to_response ('authorise_datasets_response.html', locals())
      
   
   try:
      user = User.objects.get(userkey=userkey)
   except:
      return HttpResponse ("No user found with userkey %s" % userkey)

   datasets=user.datasetjoin_set.all().filter(removed__exact=0).order_by('datasetid')
   removed_datasets=user.datasetjoin_set.all().filter(removed__exact=-1).order_by('datasetid')

   requests = user.datasetRequests(status='pending')

   authorisors = SiteUser.objects.all()

   return render_to_response('authorise_datasets.html', locals())

      
 
