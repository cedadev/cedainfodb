# Create your views here.

from django.db.models import Q
from cedainfo.cedainfoapp.models import *
from cedainfo.cedainfoapp.forms import *
#from cedainfo.cedainfoapp.custom_widgets import TinyMCE
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.core.urlresolvers import reverse

import datetime


# use generic view list_detail.object_list for Hosts (see urls.py)

# host_list view: optionally includes subsetting (e.g. in_pool or not yet retired)
def host_list(request, subset=None):
    # define the queryset, using the subset if available
    if (subset == 'in_pool'):
        hosts = Host.objects.filter(in_pool=True)
    elif (subset == 'not_retired'):
	hosts = Host.objects.filter(planned_end_of_life__gt=datetime.date.today() )
    else:
        hosts = Host.objects.all()
    return render_to_response('cedainfoapp/host_list.html', {'host_list': hosts, 'subset': subset}, )


# host_detail view: includes details of host, plus services and history entries for that host
def host_detail(request, host_id):
    url=reverse('cedainfo.cedainfoapp.views.host_list',args=(None,))
    try:
       host = get_object_or_404(Host, pk=host_id)
       services = HostService.objects.filter(host=host)
       history = HostHistory.objects.filter(host=host)
       return render_to_response('cedainfoapp/host_detail.html', {'host': host, 'services': services, 'history': history})
    except:
       message="Unable to find host with id='%s'"%(host_id)
       return render_to_response('error.html',{'message':message,'url':url})
       

# search by dataentity_id for DataEntity objects (their internal id field is distinct from the MOLES dataentity_id field which links them to the MOLES catalogue)
def dataentity_search(request):
    query = request.GET.get('q', '')
    if query:
        qset = (
	    Q(dataentity_id__icontains=query)
	)
	results = DataEntity.objects.filter(qset).distinct()
    else:
        results = []
    return render_to_response('cedainfoapp/search_dataentity.html', {"results" : results, "query": query})

# find a dataentity & go straight to it
# TODO : handle things better when we can't find it
def dataentity_find(request, dataentity_id):
    url=reverse('cedainfo.cedainfoapp.views.dataentity_search')
    if dataentity_id:
        try:
            dataentity = DataEntity.objects.get(dataentity_id=dataentity_id)
	    form = DataEntityForm(instance=dataentity)
            if form.is_valid():
	        form.save()
        except:
            message="Unable to find dataentity '%s'"%(dataentity_id)
            return render_to_response('error.html',{'message':message,'url':url})
    else:
        dataentity = None
	form = None
        message="Unable to find dataentity %s"%(dataentity_id)
        return render_to_response('error.html',{'message':message,'url':url})

    return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form} )

# Edit a dataentity
def dataentity_detail_form(request, id):
    url=reverse('cedainfo.cedainfoapp.views.dataentity_search')
    try:
       dataentity = DataEntity.objects.get(pk=id)
       if request.method == 'POST':
          form = DataEntityForm(request.POST, instance=dataentity)
          if form.is_valid():
	     form.save()
       else:
          form = DataEntityForm(instance=dataentity)
       return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form} )
    except:
       message="Unable to find dataentity with id=%s"%(id)
       return render_to_response('error.html',{'message':message,'url':url})


# Add a new dataentity
def dataentity_add(request, dataentity_id):
    dataentity = DataEntity(dataentity_id=dataentity_id, access_status=AccessStatus.objects.get(pk=2) ) # TODO : add defaults / dummy values...
    dataentity.save()
    if request.method == 'POST':
        form = DataEntityForm(request.POST, instance=dataentity)
        if form.is_valid():
	    form.save()
    else:
        form = DataEntityForm(instance=dataentity)
    return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form} )

# Show slots by rack
def slots_by_rack(request, rack_id):
    rack = Rack.objects.get(pk=rack_id)
    slots = Slot.objects.filter(parent_rack = rack)
    return render_to_response('cedainfoapp/slots_by_rack.html', {'rack': rack, 'slots': slots} )    
	
# Dan's pre-made database views, recreated here...

# original name : datasets_with_responsible_names
# New model has DataEntity, Person, Role and DataEntityAdministrator
# ... Need to list each combination of [person & role] associated with a data entity
def dataentity_with_dataentity_administrators(request, dataentity_id):
    # find this data entity
    dataentity = DataEntity.objects.get(pk=dataentity_id)
    # find the list of data entity administrator intances for this data entity
    # for each of these, we should be able to find the person and role
    dataentity_administrators = DataEntityAdministrator.objects.filter(data_entity=dataentity_id)
    return render_to_response('cedainfoapp/dataentity_with_dataentity_administrators.html', {'dataentity': dataentity, 'dataentity_administrators': dataentity_administrators, })

def dataentities_with_dataentity_administrators(request):
    # find all dataentities
    dataentities = DataEntity.objects.all()
    # for each dataentity, find the list of data entity administrator intances for this data entity
    dataentity_list = []
    for dataentity in dataentities:
	# for each of these, append an additional attribute which is a queryset representing the deas for this de
	dataentity.deas = DataEntityAdministrator.objects.filter(data_entity=dataentity.dataentity_id)
	dataentity_list.append(dataentity)
		
    return render_to_response('cedainfoapp/dataentities_with_dataentity_administrators.html', {'dataentities': dataentity_list} )