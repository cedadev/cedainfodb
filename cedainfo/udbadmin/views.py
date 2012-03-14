from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from datetime import *
from pytz import *

from udbadmin.models import *
from udbadmin.forms import *
from udbadmin.SortHeaders import SortHeaders

#
# sort table headers: djangosnippets.org/snippets/308
#

DATASET_HEADERS = (
    ('Dataset', 'datasetid'),
    ('Version', 'ver'),
    ('Endorsed', 'endorseddate'),
    ('Expires',  'expiredate'),
    ('Endorsed by', 'endorsedby'),
    ('NERC?', 'nercfunded'),
    ('Research', 'research'),
)

REMOVED_DATASET_HEADERS = ( 
    ('Dataset', 'datasetid'),
    ('Version', 'ver'),
    ('Endorsed', 'endorseddate'),
    ('Expires',  'expiredate'),
    ('Removed', 'removeddate'),
    ('Endorsed by', 'endorsedby'),
    ('NERC?', 'nercfunded'),
    ('Research', 'research'),
)


def home(request):
    return render_to_response('home.html', locals())
    
def list_current_user_datasets(request, userkey):

#
#      Remove any datasets requested
#
    if request.method == 'POST':
       for removeID in request.POST.getlist('remove'):
          udj = Datasetjoin.objects.get(id=removeID)
	  udj.removeDataset()
	  
    user = User.objects.get(userkey=userkey)

    sort_headers = SortHeaders(request, DATASET_HEADERS)
    headers = list(sort_headers.headers())
    datasets=user.datasetjoin_set.all().filter(removed__exact=0).order_by(sort_headers.get_order_by())

    return render_to_response('list_current_user_datasets.html', locals())

def list_removed_user_datasets(request, userkey):

    user = User.objects.get(userkey=userkey)

    sort_headers = SortHeaders(request, REMOVED_DATASET_HEADERS)
    headers = list(sort_headers.headers())
    datasets=user.datasetjoin_set.all().filter(removed__exact=-1).order_by(sort_headers.get_order_by())

    return render_to_response('list_removed_user_datasets.html', locals())


def dataset_details(request, datasetid):
#
#    Displays dataset details read-only
#
   try:
      dataset = Dataset.objects.get(datasetid=datasetid)   
   except:
      return HttpResponse('not found')
      
   return render_to_response('dataset_details.html', locals())


def edit_user_dataset_join (request, id):

   try:
      udj = Datasetjoin.objects.get(id=id) 
      user = udj.userkey
   except:
      return HttpResponse('id %s not found' % id)

   
   if request.method == 'POST':
      udj.research     = request.POST.get('research', '')      
      udj.extrainfo    = request.POST.get('extrainfo', '')      
      udj.grantref     = request.POST.get('grantref', '')
      udj.expiredate   = request.POST.get('expiredate', '')
      udj.endorseddate = request.POST.get('endorseddate', '')
      udj.fundingtype  = request.POST.get('fundingtype', '')
      udj.openpub      = request.POST.get('openpub', '')
      udj.nercfunded   = int(request.POST.get('nercfunded', 0))         
      udj.openpub      = request.POST.get('openpub', '')

      changeendorsedby = request.POST.get('changeendorsedby', '')
      if changeendorsedby:
         udj.endorsedby = changeendorsedby

      if udj.removed == 0 and request.POST.get('removed') == "-1":
         udj.removeDataset()
      if udj.removed == -1 and request.POST.get('removed') == '0':
         udj.removed = 0
	 udj.removeddate = None
	             
      udj.save()
#
#          For some reason I need to re-read the values in order for the expiredate and endorseddate to show the correct values
#      
      udj = Datasetjoin.objects.get(id=id)    

   myform = UdjForm(initial={'fundingtype':udj.fundingtype, 'nercfunded':udj.nercfunded, 'openpub':udj.openpub, 'removed': udj.removed})
   
   authorisors = SiteUser.objects.exclude(last_name__exact="").order_by('first_name') 

   return render_to_response('edit_user_dataset_join.html', locals())

