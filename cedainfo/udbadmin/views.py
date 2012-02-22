from django.http import HttpResponse
from django.shortcuts import *
from udbadmin.models import *
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

   try:
      dataset = Dataset.objects.get(datasetid=datasetid)   
   except:
      return HttpResponse('not found')
      
   return render_to_response('dataset_details.html', locals())
