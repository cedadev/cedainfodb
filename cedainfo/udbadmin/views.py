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

KEY_HEADERS = (
  ('Userkey', 'userkey'),
  ('AccountID', 'accountid'),
  ('Start date', 'startdate'),
  ('Email', 'emailaddress'),
  ('Public key', 'public_key')
)

@login_required()
def home(request):
    user = request.user
    return render_to_response('home.html', locals())

@login_required()
def user_edit_by_accountid(request, accountid):
    """Provides a simple redirect to allow user details page to be specified directly by accountid. 
       You can do this by adding '?accountid=' to the admin page, but you end up with an extra page
       of 'results' in between."""
   
    try:    
        cedauser = User.objects.get(accountid=accountid)
    except:
       return HttpResponse('Accountid: %s not found' % accountid)
    
    return redirect ('/admin/udbadmin/user/%s' % cedauser.userkey)


def user_account_details(request, userkey):
 
    cedauser = User.objects.get(userkey=userkey)
  
    record = 'accountid: ' + cedauser.accountid + '\n'
    record += 'surname: ' + cedauser.surname + '\n'
  
    record = \
"""accountid: %s
surname: %s
    """ % (cedauser.accountid, cedauser.surname)
      
    return HttpResponse(record, content_type="text/plain")



@login_required()
def list_keys(request):
    user = request.user

    cedausers = User.objects.exclude(public_key__exact='a').exclude(public_key__exact='b')


    sort_headers = SortHeaders(request, KEY_HEADERS)
    headers = list(sort_headers.headers())
    cedausers = User.objects.exclude(public_key__exact=' ').exclude(public_key__exact='').order_by(sort_headers.get_order_by())
    
    return render_to_response('list_keys.html', locals())

    
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
   datasets = Dataset.objects.exclude(datasetid__startswith='msf')
      
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


@login_required()
def list_users_for_dataset(request, datasetid):
    user = request.user

    try:
       dataset = Dataset.objects.get(datasetid=datasetid)   
#       udjs = Datasetjoin.objects.filter(datasetid=datasetid)
       recs  = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0).order_by('-userkey')      

#       print users[0]
#       recs = []
       
#       for u in users:
#          print u['userkey']
#          print userKey
#          cedaUser = User.objects.get(userkey=userKey)
#	  mydict = {'user': cedaUser}
#	  recs.append(userKey)
	  
    except:
       return HttpResponse('dataset not found')

    return render_to_response('list_users_for_dataset.html', locals())

@login_required()
def list_accounts_for_dataset(request, datasetid):
    user = request.user

    try:
       dataset = Dataset.objects.get(datasetid=datasetid)   
       recs  = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0)      	  
    except:
       return HttpResponse('dataset not found')


    accounts = []
    
    for rec in recs:
        accounts.append(rec.userkey.accountid)
        
    accounts = list(set(accounts))
    accounts.sort()        
        
    return render_to_response('list_accounts_for_dataset.html', locals())


@login_required()
def list_users_email_for_dataset(request, datasetid):
    user = request.user

    try:
       dataset = Dataset.objects.get(datasetid=datasetid)   
       recs  = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0).values('userkey__emailaddress').distinct()
       
    except:
       return HttpResponse('Not found')
       
    return render_to_response('list_users_email_for_dataset.html', locals())
