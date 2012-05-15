from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from django.contrib.auth.decorators import login_required

from dateutil.relativedelta import relativedelta

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


@login_required()
def home(request):
    user = request.user
    return render_to_response('home.html', locals())
    
@login_required()
def list_current_user_datasets(request, userkey):
    user = request.user

#
#      Remove any datasets requested
#
    if request.method == 'POST':
       for removeID in request.POST.getlist('remove'):
          udj = Datasetjoin.objects.get(id=removeID)
	  udj.removeDataset()
	  
    cedauser = User.objects.get(userkey=userkey)

    sort_headers = SortHeaders(request, DATASET_HEADERS)
    headers = list(sort_headers.headers())
    datasets=cedauser.datasetjoin_set.all().filter(removed__exact=0).order_by(sort_headers.get_order_by())

    return render_to_response('list_current_user_datasets.html', locals())

@login_required()
def list_removed_user_datasets(request, userkey):
    user = request.user
    
    cedauser = User.objects.get(userkey=userkey)

    sort_headers = SortHeaders(request, REMOVED_DATASET_HEADERS)
    headers = list(sort_headers.headers())
    datasets=cedauser.datasetjoin_set.all().filter(removed__exact=-1).order_by(sort_headers.get_order_by())

    return render_to_response('list_removed_user_datasets.html', locals())


@login_required()
def dataset_details(request, datasetid):
#
#    Displays dataset details read-only
#
   try:
      dataset = Dataset.objects.get(datasetid=datasetid)   
   except:
      return HttpResponse('not found')
      
   user = request.user   
   return render_to_response('dataset_details.html', locals())

@login_required()
def edit_user_dataset_join (request, id):

   user = request.user  
         
   try:
      udj = Datasetjoin.objects.get(id=id) 
      cedauser = udj.userkey
   except:
      return HttpResponse('id %s not found' % id)

   
   if request.method == 'POST':
      udj.research     = request.POST.get('research', '')      
      udj.extrainfo    = request.POST.get('extrainfo', '')      
      udj.grantref     = request.POST.get('grantref', '')
      udj.expiredate   = datetime.strptime(request.POST.get('expiredate'), '%d/%m/%Y')
      udj.endorseddate = datetime.strptime(request.POST.get('endorseddate'), '%d/%m/%Y')
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


@login_required()
def edit_dataset_request (request, id):
      
   user = request.user
      
   try:
      datasetRequest = Datasetrequest.objects.get(id=id) 
      cedauser = datasetRequest.userkey
   except:
      return HttpResponse('id %s not found' % id)

   
   if request.method == 'POST':
      datasetRequest.research     = request.POST.get('research', '')      
      datasetRequest.extrainfo    = request.POST.get('extrainfo', '')      
      datasetRequest.grantref     = request.POST.get('grantref', '')
      datasetRequest.requestdate  = datetime.strptime(request.POST.get('requestdate'), '%d/%m/%Y')
      datasetRequest.fundingtype  = request.POST.get('fundingtype', '')
      datasetRequest.openpub      = request.POST.get('openpub', '')
      datasetRequest.nercfunded   = int(request.POST.get('nercfunded', 0))         
      datasetRequest.openpub      = request.POST.get('openpub', '')

      changeendorsedby = request.POST.get('changeendorsedby', '')
      if changeendorsedby:
         datasetRequest.endorsedby = changeendorsedby
	             
      datasetRequest.save()
#
#          For some reason I need to re-read the values in order for the expiredate and endorseddate to show the correct values
#      
      datasetRequest = Datasetrequest.objects.get(id=id)    

   myform = DatasetRequestForm(initial={'fundingtype':datasetRequest.fundingtype, 'nercfunded':datasetRequest.nercfunded, 'openpub':datasetRequest.openpub})
   
   authorisors = SiteUser.objects.exclude(last_name__exact="").order_by('first_name') 

   return render_to_response('edit_dataset_request.html', locals())


@login_required()
def add_user_datasets(request, userkey):

   user        = request.user
   cedauser    = User.objects.get(userkey=userkey)
   
   authorisors = SiteUser.objects.exclude(last_name__exact="").order_by('first_name') 
   datasets = Dataset.objects.all()
      
   if request.method == 'POST':
     
      datasetid = request.POST.get('datasetid', '') 
      
      if datasetid:
	 dataset   = Dataset.objects.get(datasetid=datasetid)
	 expireDate = datetime.now() + relativedelta(months=dataset.defaultreglength)

	 endorsedby = request.POST.get('endorsedby', '')  

	 version = Datasetjoin.objects.getDatasetVersion(userkey, datasetid) 
	 udj = Datasetjoin(userkey=cedauser, datasetid=dataset, ver=version, endorsedby=endorsedby, expiredate=expireDate, endorseddate=datetime.now(timezone('Europe/London')))
	 udj.save()

         return redirect ('/udbadmin/udj/%s' % udj.id)
	 
   return render_to_response('add_user_dataset.html', locals())
