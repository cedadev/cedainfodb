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
    if (subset == 'active'):
	    hosts = Host.objects.filter(retired_on=None)
    else:
        hosts = Host.objects.all()
    return render_to_response('cedainfoapp/host_list.html', {'host_list': hosts, 'subset': subset}, )


# host_detail view: includes details of host, plus services and history entries for that host
def host_detail(request, host_id):
    url=reverse('cedainfo.cedainfoapp.views.host_list',args=(None,))
    try:
       host = get_object_or_404(Host, pk=host_id)
       services = Service.objects.filter(host=host)
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
	    Q(dataentity_id__icontains=query) |
	    Q(symbolic_name__icontains=query) |
            Q(friendly_name__icontains=query) |
            Q(logical_path__icontains=query)
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

# Dan's pre-made database views, recreated here...

# original name : datasets_with_responsible_names
# New model has DataEntity, Person, Role and DataEntityContact
# ... Need to list each combination of [person & role] associated with a data entity
def dataentity_with_dataentity_contacts(request, dataentity_id):
    # find this data entity
    dataentity = DataEntity.objects.get(pk=dataentity_id)
    # find the list of data entity contact intances for this data entity
    # for each of these, we should be able to find the person and role
    dataentity_contacts = DataEntityContact.objects.filter(data_entity=dataentity_id)
    return render_to_response('cedainfoapp/dataentity_with_dataentity_contacts.html', {'dataentity': dataentity, 'dataentity_contacts': dataentity_contacts, })

def dataentities_with_dataentity_contacts(request):
    # find all dataentities
    dataentities = DataEntity.objects.all()
    # for each dataentity, find the list of data entity administrator intances for this data entity
    dataentity_list = []
    for dataentity in dataentities:
	# for each of these, append an additional attribute which is a queryset representing the deas for this de
	dataentity.deas = DataEntityContact.objects.filter(data_entity=dataentity.dataentity_id)
	dataentity_list.append(dataentity)
		
    return render_to_response('cedainfoapp/dataentities_with_dataentity_contacts.html', {'dataentities': dataentity_list} )

def services_by_rack(request, rack_id):
    # show a rack, show hosts within rack, show virtual hosts within hypervisor hosts, services within hosts ...sort of deployment diagram
    # Create a data structure to hold hierarchical structure:
    # rack
    #   host
    #     [virtualhost]
    #        service
    layout = {}
    rack = Rack.objects.get(pk=rack_id)
    all_racks = Rack.objects.all()
    # Find list of physical hosts belonging to this rack
    hosts = Host.objects.filter(rack=rack).filter(hypervisor=None)
    services_by_host = {}
    vms_by_hypervisor = {}
    for host in hosts:
        services_by_host[host] = Service.objects.filter(host=host)
        # Make a list of any vms that are on this physical host
        vms_by_hypervisor[host] = Host.objects.filter(hypervisor=host)
        # Loop through child vms that we've found
        for vm in vms_by_hypervisor[host]:
            # look for services that belong to this vm
            services_by_host[vm] = Service.objects.filter(host=vm)

    return render_to_response('cedainfoapp/services_view.html', {'rack': rack, 'all_racks': all_racks, 'hosts': hosts, 'services_by_host': services_by_host, 'vms_by_hypervisor': vms_by_hypervisor} )
    