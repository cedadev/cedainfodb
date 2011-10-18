# Create your views here.

from django.db.models import Q
from cedainfo.cedainfoapp.models import *
from cedainfo.cedainfoapp.forms import *
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.core.urlresolvers import reverse
import re

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
    search = request.GET.get('search', '') # default order is ascending id
    qs = FileSet.objects.filter(logical_path__contains=search).order_by(o)
    # Use the object_list view.
    totalalloc=0
    totaldu=0
    for fs in qs:
        lastsize = fs.last_size()
        if lastsize: totaldu += lastsize.size
	totalalloc += fs.overall_final_size
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/fileset_list.html",
        template_object_name = "fileset",
        extra_context = {"totaldu" : totaldu, "totalalloc" : totalalloc}
    )

def underallocated_fs(request):
    qs = FileSet.objects.all()
    filesets = []
    # Use the object_list view.
    for fs in qs:
        lastsize = fs.last_size() 
        if lastsize and (lastsize.size > fs.overall_final_size): filesets.append(fs)
    return render_to_response('cedainfoapp/underallocated.html', 
           {'filesets': filesets})  

    
def partition_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    partfilter = request.GET.get('filter', None) # default order is ascending id
    partitions = Partition.objects.order_by(o)
    filtered_partitions = []
    # list overfilled partitions
    if partfilter == 'overfill': 
        for p in partitions:
            if 100.0* p.used_bytes/(p.capacity_bytes+1) > 98.0 and p.status != 'Retired' :filtered_partitions.append(p)
    # list overallocated partitions
    elif partfilter == 'overalloc': 
        for p in partitions:
            allocated = p.allocated() + p.secondary_allocated()
            if 100.0* allocated/(p.capacity_bytes+1) > 99.0 and p.status != 'Retired' :filtered_partitions.append(p)
    # list unalloced files on partition
    elif partfilter == 'unalloc': 
        for p in partitions:
            unalloc = p.used_bytes - p.used_by_filesets() + p.secondary_used_by_filesets()
            if 100.0* unalloc/(p.capacity_bytes+1) > 1.0 and p.status != 'Retired' :filtered_partitions.append(p)
    else: filtered_partitions = partitions
           
    # Use the object_list view.
    return render_to_response('cedainfoapp/partition_list.html', {'partitions': filtered_partitions,})    

    
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

def partition_vis(request, id):
    part = Partition.objects.get(pk=id)
    filesets = FileSet.objects.filter(partition=part)
    for f in filesets:
        alloc = f.overall_final_size*100/part.capacity_bytes
        #f.vis = '|' * alloc
        f.vis = alloc
        f.size = f.current_size()
    return render_to_response('cedainfoapp/partition_vis.html', 
               {'part': part, 'filesets': filesets})  

    
# do df for a partition and redirect back to partitions list
def df(request, id):
    part = Partition.objects.get(pk=id)
    part.df()
    return redirect(request.META['HTTP_REFERER'])

# do du for a fileset and redirect back to fileset list
def du(request, id):
    fileset = FileSet.objects.get(pk=id)
    fileset.du()
    return redirect(request.META['HTTP_REFERER'])

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
        return redirect(request.META['HTTP_REFERER'])
        
# create storage pot and link archive 
def storagesummary(request):
    parts = Partition.objects.all()
    sumtable = [{'status':'Blank',      'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                {'status':'Allocating', 'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
		{'status':'Closed',     'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                {'status':'Migrating',  'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                {'status':'Retired',    'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                {'status':'Total',      'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                ]
    index = {}
    for i in range(len(sumtable)): index[sumtable[i]['status']] = i
      
    for part in parts:
        i = index[part.status]
	sumtable[i]["npart"] += 1
	sumtable[i]["used"] += part.used_bytes
	sumtable[i]["allocated"] += part.allocated()
	sumtable[i]["allocused"] += part.used_by_filesets()
	sumtable[i]["sec_allocated"] += part.secondary_allocated()
	sumtable[i]["sec_allocused"] += part.secondary_used_by_filesets()
	sumtable[i]["capacity"] += part.capacity_bytes
	sumtable[5]["npart"] += 1
	sumtable[5]["used"] += part.used_bytes
	sumtable[5]["allocated"] += part.allocated()
	sumtable[5]["allocused"] += part.used_by_filesets()
	sumtable[5]["sec_allocated"] += part.secondary_allocated()
	sumtable[5]["sec_allocused"] += part.secondary_used_by_filesets()
	sumtable[5]["capacity"] += part.capacity_bytes
 
    return render_to_response('cedainfoapp/sumtable.html', {'sumtable':sumtable})  
        
# make list of rsync commands for makeing a secondary copies
def make_secondary_copies(request):
    filesets = FileSet.objects.all()
    output = ''
    for f in filesets:
         rsynccmd = f.secondary_copy_command()
	 if rsynccmd: output = "%s%s\n" % (output,rsynccmd)	
    return render_to_response('cedainfoapp/make_secondary_copies.txt', {'cmds':output}, mimetype="text/plain")  
	
# create ftp mount script for a host - chroot jail mounting 
def ftpmount_script(request, host):
    host = Host.objects.get(hostname=host)
    mounts = host.ftpmountpoints
    if mounts == None: mounts = []
    else: mounts = mounts.split()
    ftpmount_partitions = set()
    filesets = []
    mountlinks = []
    
    # ftpmounts
    for mount in mounts:
	rw = True
	path = mount
        if mount[-4:] == "(ro)": 
	    rw = False
	    path = mount[:-4]
	
        filesets = FileSet.objects.filter(logical_path__startswith=path)
	for fs in filesets:
	    partition = fs.partition.mountpoint
	    ftpmount_partitions.add((partition,rw,fs.partition.host))
	    
	primefileset = FileSet.objects.filter(logical_path=path)
	primefileset = primefileset.all()[0]
	
	mountlinks.append((path, primefileset.storage_path())) 
	    
    # remove ro partition mounts if rw one exists
    discard_list = []
    for part, rw, parthost in ftpmount_partitions:
        if rw == True: discard_list.append((part,False,parthost) )   
    for part in discard_list: ftpmount_partitions.discard(part)    

	
    return render_to_response('cedainfoapp/ftpmountscript.html', {'host':host, 
        'filesets':filesets,
        'ftpmount_partitions':ftpmount_partitions,
	'mountlinks': mountlinks,
	 }, mimetype="text/plain")  

# create auto mount script for a host 
def automount_script(request, host):
    host = Host.objects.get(hostname=host)
    mounts = host.mountpoints
    if mounts == None: mounts = []
    else: mounts = mounts.split()
    automount_partitions = set()
    filesets = []
    
    # automounts
    for mount in mounts:
	rw = True
	path = mount
        if mount[-4:] == "(ro)": 
	    rw = False
	    path = mount[:-4]

	rw = True
	path = mount
        if mount[-4:] == "(ro)": 
	    rw = False
	    path = mount[:-4]
		
        filesets = FileSet.objects.filter(logical_path__startswith=path)
	for fs in filesets:
	    partition = fs.partition.mountpoint
	    if partition[:7] == "/disks/": 
	        partition = partition[7:] # remove disks
	    else: continue # can't deal with automount things that are not in disks 
	    automount_partitions.add((partition,rw,fs.partition.host))

    # remove ro partition mounts if rw one exists
    discard_list = []
    for part, rw, host in automount_partitions:
        if rw == True: discard_list.append((part,False,host))    
    for p in discard_list: automount_partitions.discard(p)    
           
    return render_to_response('cedainfoapp/mountscript.html', {'host':host, 
        'filesets':filesets,
        'automount_partitions':automount_partitions,
	 }, mimetype="text/plain")  
