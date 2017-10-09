from operator import itemgetter
from dateutil.relativedelta import relativedelta

from django.http import HttpResponse
from django.shortcuts import *
from django.contrib.auth.models import User as SiteUser
from django.contrib.auth.decorators import login_required

from udbadmin.models import *
from udbadmin.forms import *
from udbadmin.SortHeaders import SortHeaders
import LDAP
import json
import public_keys

import udb_ldap
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
  ('UID', 'uid'),
  ('Start date', 'startdate'),
  ('Email', 'emailaddress'),
  ('Key length', 'length'),
  ('Public key', 'public_key')
)

DATASET_USERS_HEADERS = (
  ('Userkey', 'userkey'),
  ('AccountID', 'userkey__accountid'),
  ('First name', 'userkey__othernames'),
  ('Surname', 'userkey__surname'),
  ('Email', 'userkey__emailaddress'),
  ('Institute', 'userkey__addresskey__institutekey__name'),
  ('Endorsed', 'endorseddate'),
  ('Expires', 'expiredate'),
  ('Research', 'research')
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


def user_account_details(request, accountid):

    cedauser = User.objects.get(accountid=accountid)


    record = 'accountid: %s' + cedauser.accountid + '\n'
    record += 'surname: ' + cedauser.surname + '\n'

    record = \
"""accountid: %s
surname: %s
    """ % (cedauser.accountid, cedauser.surname)

    return HttpResponse(record, content_type="text/plain")

def user_getemail(request, accountid):
    """Function to return a users email address from accountid"""
    cedauser = User.objects.get(accountid=accountid)
    record = {'accountid': cedauser.accountid, 'email': cedauser.emailaddress}
    return HttpResponse(json.dumps(record), content_type="application/json")

@login_required()
def list_keys(request):
    user = request.user

    sort_headers = SortHeaders(request, KEY_HEADERS)
    headers = list(sort_headers.headers())
##    users = User.objects.filter(uid__gt=0).order_by(sort_headers.get_order_by()) 
    
    if sort_headers.get_order_by() != 'length':       
        users = User.objects.exclude(public_key__exact=' ').exclude(public_key__exact='').order_by(sort_headers.get_order_by())
    else:
    	users = User.objects.exclude(public_key__exact=' ').exclude(public_key__exact='')

##    users = udb_ldap.all_users()
#
#      Get public keys for all members in ldap database
#    
    ldap_member_details = LDAP.all_member_details()
    ldap_public_keys = {}
    
    for member in ldap_member_details:
        accountid = member[1]['uid'][0]
        key = member[1]['sshPublicKey'][0]
        ldap_public_keys[accountid] = key

    cedausers = []
    warning_count = 0
    
    for user in users:
        if not user.isJasminCemsUser():
            continue
    
        ldap_public_key = ''
        public_key_differs = False
         
        if user.accountid in ldap_public_keys:
            ldap_public_key = ldap_public_keys[user.accountid]

                  
            if public_keys.public_keys_differ(ldap_public_key, user.public_key):
                warning_count = warning_count + 1
                public_key_differs = True

        length = public_keys.check_public_key(user.public_key)
	
        userhash = {'cedauser': user, 
                    'ldap_public_key': ldap_public_key, 
		    'key_length': length, 
                    'public_key_differs': public_key_differs, 
                    'diag_udb_key': public_keys.prepare_key_for_diff(user.public_key), 
                    'diag_ldap_key': public_keys.prepare_key_for_diff(ldap_public_key)}
                     
        cedausers.append(userhash)
	
    if sort_headers.get_order_by() == 'length':          
        cedausers = sorted(cedausers, key=itemgetter('key_length'))
     
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
   
   authorisers = get_dataset_authorisers(dataset.datasetid)
   viewers = get_dataset_viewers(dataset.datasetid)
      
   return render_to_response('dataset_details.html', locals())


def get_dataset_authorisers (datasetid):
#
#   Returns a list of dataset authorisers for the given datasetid. Authorisers are returned as a list
#   of User objects. If no authoriser is found then "badc" user is added (as this is the default 
#   authoriser)
#
    authorisers = []

    try:
    	
	priv = Privilege.objects.filter(datasetid=datasetid, type='authorise')

	for p in priv:
            authorisers.append(p.userkey)

	if not authorisers:
            authorisers.append(User.objects.get(userkey=-1))
    except:
        pass
			
    return authorisers

def get_dataset_viewers (datasetid):
#
#   Returns a list of users authorised to view membership for the given datasetid. Viewers are returned as a list
#   of User objects. 
#
    viewers = []

    try:
    	
	priv = Privilege.objects.filter(datasetid=datasetid, type='viewusers')

	for p in priv:
            viewers.append(p.userkey)
    except:
        pass
			
    return viewers




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
   datasets = Dataset.objects.exclude(datasetid__startswith='msf').exclude(authtype='jasmin-portal')
      
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
       sort_headers = SortHeaders(request, DATASET_USERS_HEADERS)
       headers = list(sort_headers.headers())

       dataset = Dataset.objects.get(datasetid=datasetid)   
#       udjs = Datasetjoin.objects.filter(datasetid=datasetid)
       recs  = Datasetjoin.objects.filter(datasetid=datasetid).filter(userkey__gt=0).filter(removed=0).order_by(sort_headers.get_order_by())      


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
