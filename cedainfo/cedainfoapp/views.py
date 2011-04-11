# Create your views here.

from django.db.models import Q
from cedainfo.cedainfoapp.models import *
from cedainfo.cedainfoapp.forms import *
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.core.urlresolvers import reverse

import datetime

logging=settings.LOG

# use generic view list_detail.object_list for Hosts (see urls.py)

# host_list view: optionally includes subsetting (e.g. in_pool or not yet retired)
def host_list(request, subset=None):
    o = request.GET.get('o', 'id') # default order is ascending id
    # define the queryset, using the subset if available
    if (subset == 'active'):
	    qs = Host.objects.filter(retired_on=None).order_by(o)
    else:
        qs = Host.objects.all().order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/host_list.html",
        template_object_name = "host",
    )    

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
    if (dataentity_id==''):
        # blank id ...can't make a new dataentity object
       message="Unable to create dataentity with blank dataentity_id. Add a string to the end of the URL representing the id, e.g. .../dataentity/add/newid"
       return render_to_response('error.html',{'message':message})
    else:  
        # make a new dataentity using this new id
        dataentity = DataEntity(dataentity_id=dataentity_id, access_status=AccessStatus.objects.get(pk=2) ) # TODO : add defaults / dummy values...
        dataentity.save()
        if request.method == 'POST':
            form = DataEntityForm(request.POST, instance=dataentity)
            if form.is_valid():
                form.save()
        else:
            form = DataEntityForm(instance=dataentity)
        return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form} )

def dataentity_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    qs = DataEntity.objects.order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/dataentity_list.html",
        template_object_name = "dataentity",
    )    

def dataentities_for_review(request):
    o = request.GET.get('o', 'next_review') # default order is ascending next_review (date)
    qs = DataEntity.objects.filter(review_status="to be reviewed").order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/dataentity_list.html",
        template_object_name = "dataentity",
    )    

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

def home(request):
    # Home page view
    return render_to_response('cedainfoapp/home.html', )

def fileset_list(request):
    '''Barebones list of filesets'''
    o = request.GET.get('o', 'id') # default order is ascending id
    qs = FileSet.objects.order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/fileset_list.html",
        template_object_name = "fileset",
    )


    
def partition_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    qs = Partition.objects.order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/partition_list.html",
        template_object_name = "partition",
    )
    
def nodelist(request):
    hostlist_list = HostList.objects.all()
    for hostlist in hostlist_list:
        # pre-populate list with its members
        hostlist.members = Host.objects.filter(hostlist=hostlist)
        hostlist.memberlist = Host.objects.filter(hostlist=hostlist).values_list('hostname', flat=True)
        # Generate string containing members
        mylist = []
        for member in hostlist.memberlist:
            mylist.append(member)
        hostlist.memberstring = (" ").join(mylist)
        
    racklist_list = RackList.objects.all()
    for racklist in racklist_list:
        # pre-populate list with its members
        racklist.members = Rack.objects.filter(racklist=racklist)
        racklist.memberlist = Rack.objects.filter(racklist=racklist).values_list('name', flat=True)
        # Generate string containing members
        mylist = []
        for member in racklist.memberlist:
            mylist.append("$%s" % member)
        racklist.memberstring = (" ").join(mylist)


    return render_to_response('cedainfoapp/nodelist_view.txt', {'hostlist_list': hostlist_list, 'racklist_list': racklist_list}, mimetype="text/plain")  


    
# do df for a partition and redirect back to partitions list
def df(request, id):
    part = Partition.objects.get(pk=id)
    part.df()
    return redirect('/admin/cedainfoapp/partition')

# do allocation of a fileset to a partition 
def allocate(request, id):
    fs = FileSet.objects.get(pk=id)
    fs.allocate()
    return redirect(request.META['HTTP_REFERER'])

# create storage pot and link archive 
def makespot(request, id):
    fs = FileSet.objects.get(pk=id)
    error = fs.make_spot()
    if error: 
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':error})  
    else:
        return redirect('/admin/cedainfoapp/fileset')
