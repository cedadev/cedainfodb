# Create your views here.

from django.db.models import Q
from django.http import HttpResponse
from cedainfo.cedainfoapp.models import *
from cedainfo.cedainfoapp.forms import *
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.context_processors import csrf

import re

import datetime
import time
import random

logging=settings.LOG

# use generic view list_detail.object_list for Hosts (see urls.py)

# host_list view: optionally includes subsetting (e.g. in_pool or not yet retired)
@login_required()
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
@login_required()
def host_detail(request, host_id):
    url=reverse('cedainfoapp.views.host_list',args=(None,))
    try:
       host = get_object_or_404(Host, pk=host_id)
       services = Service.objects.filter(host=host)
       history = HostHistory.objects.filter(host=host)
       return render_to_response('cedainfoapp/host_detail.html', {'host': host, 'services': services, 'history': history,'user':request.user})
    except:
       message="Unable to find host with id='%s'"%(host_id)
       return render_to_response('error.html',{'message':message,'url':url,'user':request.user})
       

# search by dataentity_id for DataEntity objects (their internal id field is distinct from the MOLES dataentity_id field which links them to the MOLES catalogue)
@login_required()
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
    return render_to_response('cedainfoapp/search_dataentity.html', {"results" : results, "query": query, "user": request.user})

# find a dataentity & go straight to it
# TODO : handle things better when we can't find it
@login_required()
def dataentity_find(request, dataentity_id):
    url=reverse('cedainfoapp.views.dataentity_search')
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

    return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form,'user':request.user} )

# Edit a dataentity
@login_required()
def dataentity_detail_form(request, id):
    url=reverse('cedainfoapp.views.dataentity_search')
    try:
       dataentity = DataEntity.objects.get(pk=id)
       if request.method == 'POST':
          form = DataEntityForm(request.POST, instance=dataentity)
          if form.is_valid():
	     form.save()
       else:
          form = DataEntityForm(instance=dataentity)
       return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form,'user':request.user} )
    except:
       message="Unable to find dataentity with id=%s"%(id)
       return render_to_response('error.html',{'message':message,'url':url,'user':request.user})


# Add a new dataentity
@login_required()
def dataentity_add(request, dataentity_id):
    if (dataentity_id==''):
        # blank id ...can't make a new dataentity object
       message="Unable to create dataentity with blank dataentity_id. Add a string to the end of the URL representing the id, e.g. .../dataentity/add/newid"
       return render_to_response('error.html',{'message':message, 'user': request.user})
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
        return render_to_response('cedainfoapp/edit_dataentity.html', {'dataentity': dataentity, 'form': form, 'user': request.user} )

@login_required()
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

@login_required()
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

@login_required()
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

    return render_to_response('cedainfoapp/services_view.html', {'user': request.user, 'rack': rack, 'all_racks': all_racks, 'hosts': hosts, 'services_by_host': services_by_host, 'vms_by_hypervisor': vms_by_hypervisor} )

@login_required()
def home(request):
    # Home page view
    return render_to_response('cedainfoapp/home.html', {'user': request.user})

@login_required()
def fileset_list(request):
    '''Barebones list of filesets'''
    o = request.GET.get('o', 'id') # default order is ascending id
    search = request.GET.get('search', '') # default order is ascending id
    qs = FileSet.objects.filter(logical_path__contains=search).order_by(o)
    # Use the object_list view.
    totalalloc=0
    totaldu=0
    totalnum=0
    for fs in qs:
        lastsize = fs.last_size()
        if lastsize: 
            totaldu += lastsize.size
            totalnum += lastsize.no_files
	totalalloc += fs.overall_final_size
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/fileset_list.html",
        template_object_name = "fileset",
        extra_context = {"totaldu" : totaldu, "totalalloc" : totalalloc, "totalnum" : totalnum}
    )

@login_required()
def underallocated_fs(request):
    qs = FileSet.objects.all()
    filesets = []
    # Use the object_list view.
    for fs in qs:
        lastsize = fs.last_size() 
        if lastsize and (lastsize.size > fs.overall_final_size): filesets.append(fs)
    return render_to_response('cedainfoapp/underallocated.html', 
           {'filesets': filesets,'user':request.user})  

@login_required()
def audit_totals(request):
    # view total volume of all analyses audits
    audits = Audit.objects.filter(auditstate="analysed")
    total_files = 0
    total_volume = 0
    naudits = 0
    for a in audits:
        total_files += a.total_files
        total_volume += a.total_volume
        naudits +=1

    return render_to_response('cedainfoapp/audit_totals.html', 
           {'total_files': total_files,'total_volume':total_volume, "naudits":naudits})  

@login_required()
def audit_trace(request, path):
    # trace a path through audits
    filesets = FileSet.objects.all().order_by('-logical_path')

    audits = []
    for fs in filesets:     
        if fs.logical_path == path[0:len(fs.logical_path)]: break
 
    
    fsaudits = Audit.objects.filter(auditstate="analysed", fileset=fs).order_by('starttime')
    rel_path = path[len(fs.logical_path)+1:]
    for a in fsaudits:
        audits.append(a)
        a.loglines = []
        LOG = open(a.logfile)
        while 1:
            line = LOG.readline()
            if line == '': break
            if line[0:len(rel_path)] == rel_path: a.loglines.append(line.strip())
         

    return render_to_response('cedainfoapp/audit_trace.html', 
           {'audits': audits, 'path':path, 'rel_path':rel_path})  

def next_audit(request):
    # make a new audit to do next via a remote service - for parallelising on Lotus
    # pick an audit to do: 
    # 1) any fileset that has no privious audit
    # 2) any fileset that has oldest audit
    filesets = FileSet.objects.filter(storage_pot_type='archive', storage_pot__isnull=False).exclude(storage_pot='')
    fileset_to_audit = None
    oldest_audit = datetime.datetime.utcnow()
    for f in filesets:
        last_audit = f.last_audit()
        # if no audit done before then use this one
	if last_audit == None:
            fileset_to_audit = f
            break    
        # skip if last audit not an analysed state then skip
        if last_audit.auditstate != 'analysed' and last_audit.auditstate != 'copy verified':    
            print "Ignore - last audit not 'analysed' or 'copy verified' state.  state=%s" % last_audit.auditstate 
            continue
        # see if this is the oldest audit
	if last_audit.starttime < oldest_audit:
	    oldest_audit = last_audit.starttime
	    fileset_to_audit = f
 
    if fileset_to_audit:
        audit=Audit(fileset=fileset_to_audit, auditstate='started', starttime = datetime.datetime.utcnow())
        audit.save()
        # wait a ramdom time and then check there are no other started audits for this fileset 
        # this is to solve a race condition 
        time.sleep(0.1*random.randint(1,100)) 
        started_audits = Audit.objects.filter(fileset=fileset_to_audit, auditstate='started') 
        if len(started_audits) != 1:  
            audit.delete() 
            audit=None        
    else: audit=None 

    return render_to_response('cedainfoapp/next_audit.txt', {'audit': audit})  

def upload_audit_results(request, id):
    # upload audit results from lotus job
    audit = get_object_or_404(Audit, pk=id)
    fileset = audit.fileset
    error = request.POST['error']
    if error =='1': 
        audit.auditstate='error'
        audit.endtime = datetime.datetime.utcnow()
        audit.save()
        return render_to_response('cedainfoapp/next_audit.txt', {'audit': audit})  

    checkm = request.POST['checkm']
    audit.auditstate='finished'
    audit.endtime = datetime.datetime.utcnow()
    # make checkm directory for spot is missing
    if not os.path.exists('%s/%s' %(settings.CHECKM_DIR, fileset.storage_pot)): 
	os.mkdir('%s/%s' %(settings.CHECKM_DIR, fileset.storage_pot))
    audit.logfile ='%s/%s/checkm.%s.%s.log' % (settings.CHECKM_DIR, fileset.storage_pot,
	        fileset.storage_pot, time.strftime('%Y%m%d-%H%M'))     
    audit.save()
    LOG = open(audit.logfile, 'w')
    LOG.write(checkm)
    LOG.close() 

    audit.analyse()    

    return render_to_response('cedainfoapp/next_audit.txt', {'audit': audit})  



@login_required()    
def partition_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    partfilter = request.GET.get('filter', None) # default order is ascending id
    partitions = Partition.objects.order_by(o)
    filtered_partitions = []
    # list overfilled partitions
    if partfilter == 'overfill': 
        for p in partitions:
            if 100.0* p.used_bytes/(p.capacity_bytes+1) > 98.0 and p.status != 'Retired' : 
                filtered_partitions.append(p)
                p.used_copy = p.use_summary() 
    # list overallocated partitions
    elif partfilter == 'overalloc': 
        for p in partitions:
            allocated = p.allocated() + p.secondary_allocated()
            if 100.0* allocated/(p.capacity_bytes+1) > 85.0 and p.status != 'Retired' :filtered_partitions.append(p)
    # list unalloced files on partition
    elif partfilter == 'unalloc': 
        for p in partitions:
            unalloc = p.used_bytes - p.used_by_filesets() + p.secondary_used_by_filesets()
            if 100.0* unalloc/(p.capacity_bytes+1) > 15.0 and p.status != 'Retired' :filtered_partitions.append(p)
    else: filtered_partitions = partitions
           
    # Use the object_list view.
    return render_to_response('cedainfoapp/partition_list.html', {'partitions': filtered_partitions,'user': request.user})    

@login_required()    
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


    return render_to_response('cedainfoapp/nodelist_view.txt', {'hostlist_list': hostlist_list, 'racklist_list': racklist_list,'user':request.user}, mimetype="text/plain")  

@login_required()
def partition_vis(request, id):
    part = Partition.objects.get(pk=id)
    filesets = FileSet.objects.filter(partition=part)
    unalloc = part.capacity_bytes
    for f in filesets:
        alloc = f.overall_final_size*100/part.capacity_bytes
        #f.vis = '|' * alloc
        f.vis = alloc
        size = f.last_size().size
        f.allocused = min(f.overall_final_size, size)
        f.allocfree = max(f.overall_final_size-size, 0)
        f.overalloc = max(size-f.overall_final_size, 0)
        f.totalsize = max(f.overall_final_size, f.overall_final_size+f.overalloc)
        unalloc -= f.totalsize
    return render_to_response('cedainfoapp/partition_vis.html', 
               {'part': part, 'filesets': filesets, 'unalloc':unalloc})  

    
# do df for a partition and redirect back to partitions list
@login_required()
def df(request, id):
    part = Partition.objects.get(pk=id)
    part.df()
    return redirect(request.META['HTTP_REFERER'])

# do du for a fileset and redirect back to fileset list
@login_required()
def du(request, id):
    fileset = FileSet.objects.get(pk=id)
    fileset.du()
    return redirect(request.META['HTTP_REFERER'])

@login_required()
def markcomplete(request, id):
    fileset = FileSet.objects.get(pk=id)
    confirm = request.GET.get('confirm', None) 
    if confirm != None:
        fileset.complete=True
	fileset.complete_date = datetime.datetime.now()
	fileset.save()
	return redirect('/admin/cedainfoapp/fileset/%s' %id)
    else:
        return render_to_response('cedainfoapp/fileset_markcomplete.html', {'fileset': fileset,'user':request.user})  
 

# do allocation of a fileset to a partition
@login_required() 
def allocate(request, id):
    fs = FileSet.objects.get(pk=id)
    fs.allocate()
    return redirect(request.META['HTTP_REFERER'])

# create storage pot and link archive 
@login_required()
def makespot(request, id):
    fs = FileSet.objects.get(pk=id)
    error = fs.make_spot()
    if error: 
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])
        
# create storage pot and link archive
@login_required() 
def storagesummary(request):
    parts = Partition.objects.all()
    sumtable = [{'status':'Blank',      'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                {'status':'Allocating', 'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
                {'status':'Allocating_ps', 'npart':0, 'used':0, 'allocated':0, 'allocused':0, 'sec_allocated':0, 'sec_allocused':0, 'capacity':0},
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
	sumtable[6]["npart"] += 1
	sumtable[6]["used"] += part.used_bytes
	sumtable[6]["allocated"] += part.allocated()
	sumtable[6]["allocused"] += part.used_by_filesets()
	sumtable[6]["sec_allocated"] += part.secondary_allocated()
	sumtable[6]["sec_allocused"] += part.secondary_used_by_filesets()
	sumtable[6]["capacity"] += part.capacity_bytes
 
    return render_to_response('cedainfoapp/sumtable.html', {'sumtable':sumtable, 'user':request.user})  

# needs to be public to interact with scripts.
def storaged_spotlist(request):
#    filesets = FileSet.objects.filter(logical_path__startswith='/badc')
    withpath = request.GET.get('withpath', None) 
    filesets = FileSet.objects.filter(sd_backup=True, storage_pot__isnull=False ).exclude(storage_pot='')
    if withpath != None: return render_to_response('cedainfoapp/storage-d_spotlist_withpath.html', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  
    else: return render_to_response('cedainfoapp/storage-d_spotlist.html', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  

#
# Provide 'external' access to simple list of spots for use by e-science. Login is disabled for this view. If any access protection is required then it can be added to the apache configuration file.
#
def storaged_spotlist_public(request):
    filesets = FileSet.objects.filter(sd_backup=True, storage_pot__isnull=False ).exclude(storage_pot='')
    
    output = ''
    
    for fs in filesets:
        output += fs.storage_pot + '\n'
           
    return HttpResponse(output, content_type="text/plain")


@login_required()
def detailed_spotlist(request):
    '''detailed table of spots including latest FSSM for each one'''
    filesets = FileSet.objects.filter(sd_backup=True, storage_pot__isnull=False ).exclude(storage_pot='')
    for fs in filesets:
        # find FSSMs for this fs ordered by date
        fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')
        if (len(fssms) > 0):
            fs.latest_size = fssms[len(fssms)-1]
        else:
            fs.latest_suze = 0
    return render_to_response('cedainfoapp/detailed_spotlist.html', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  
    
# make list of rsync commands for makeing a secondary copies
# needs to be open for automation
#
def make_secondary_copies(request):
    filesets = FileSet.objects.filter(secondary_partition__isnull=False).exclude(storage_pot='')
    return render_to_response('cedainfoapp/make_secondary_copies.txt', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  

# make list of download stats configuration
# needs to be open for automation
#
def download_conf(request):
    filesets = FileSet.objects.all().exclude(storage_pot='')
    return render_to_response('cedainfoapp/download_conf.txt', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  

# make list filesets for depositserver
# needs to be open for automation
#
def complete_filesets(request):
    filesets = FileSet.objects.all()
    return render_to_response('cedainfoapp/complete.txt', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  

# make list filesets for access stats
# needs to be open for automation
#
def spotlist(request):
    filesets = FileSet.objects.all()
    return render_to_response('cedainfoapp/spotlist.txt', {'filesets':filesets,'user':request.user}, mimetype="text/plain")  

# make a fileset from simple web request.
# if the path already exists then split the spot
def make_fileset(request):
    path = request.GET.get('path', None)
    size = request.GET.get('size', None)
    if path==None: 
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':'no path specified','user':request.user})   
    if size==None: 
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':'no size specified','user':request.user})  
    # find parent fileset 
    filesets = FileSet.objects.all()
    parent = None    
    #find fileset to break
    for f in filesets:
         if f.logical_path == path[0:len(f.logical_path)]:
	     if parent == None:
	         parent = f
	     elif len(parent.logical_path) < len(f.logical_path):
	         parent = f	      
	     print f, parent
    
    # if no break found exit
    if parent == None: 
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':'no parent fileset found','user':request.user})  

    # Find size
    if size[-1].upper() == 'K': size = int(size[0:-1])*1024
    elif size[-1].upper() == 'M': size = int(size[0:-1])*1024*1024
    elif size[-1].upper() == 'G': size = int(size[0:-1])*1024*1024*1024
    elif size[-1].upper() == 'T': size = int(size[0:-1])*1024*1024*1024*1024
    else: size = int(size)
    
    # if the path does not exist but its perent directory exists then this is a 
    # request for a new fileset.
    if not os.path.exists(path) and os.path.isdir(os.path.dirname(path)):
        new_fs = FileSet(logical_path=path, overall_final_size=size)
        new_fs.save()
        new_fs.allocate()
        print new_fs.make_spot()
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':'made new fileset','user':request.user})  
        
    # if break point is an existing directory        
    elif os.path.isdir(path) and not os.path.islink(path):     
        # make new fileset with same partition and a low size (to be changed latter)
        new_fs = FileSet(partition=parent.partition, 
             logical_path=path, overall_final_size=size)
        new_fs.save() 
        #spot tail
        head, spottail = os.path.split(new_fs.logical_path)
        if spottail == '': head, spottail = os.path.split(head)
        # icreate spot name 
        spotname = "spot-%s-split-%s" % (new_fs.pk, spottail)
        new_fs.storage_pot = spotname
        new_fs.save() 
    
        # rename the break dir as the spot
        print "rename %s to %s" % (path, new_fs.storage_path())
        os.rename(path, new_fs.storage_path())

        # make new link
        print "symlink %s to %s" % (new_fs.storage_path(), new_fs.logical_path)
        os.symlink(new_fs.storage_path(), new_fs.logical_path)
        
        # change the parent fileset size 
        parent.overall_final_size = max(0,parent.overall_final_size-size)
        parent.save()

        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':'split fileset','user':request.user})  

    else:
        return render_to_response('cedainfoapp/spotcreationerror.html', {'error':'fileset creat error','user':request.user})  

    
 	
# create ftp mount script for a host - chroot jail mounting
# REDUNDANT CAN REMMOVE?
@login_required() 
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
	'user':request.user,
        'ftpmount_partitions':ftpmount_partitions,
	'mountlinks': mountlinks,
	 }, mimetype="text/plain")  

# create auto mount script for a host
@login_required() 
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
	'user':request.user,
        'automount_partitions':automount_partitions,
	 }, mimetype="text/plain")

# approve an existing gwsrequest
@login_required()
def reject_gwsrequest(request, id):
    gwsrequest = GWSRequest.objects.get(pk=id)
    error = gwsrequest.reject()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])
     
# approve an existing gwsrequest
@login_required()
def approve_gwsrequest(request, id):
    gwsrequest = GWSRequest.objects.get(pk=id)
    error = gwsrequest.approve()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])

# convert an existing gwsrequest into a gws
@login_required()
def convert_gwsrequest(request, id):
    gwsrequest = GWSRequest.objects.get(pk=id)
    error = gwsrequest.convert()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])
        
# create an update request for a GWS
@login_required
def create_gws_update_request(request, id):
	gws = GWS.objects.get(pk=id)
	reqid = gws.create_update_request()
	if reqid:
		return redirect('/admin/cedainfoapp/gwsrequest/%i' % reqid)
	else:
		return render_to_response('error.html', {'error':error,'user':request.user})
        
# convert an existing vmrequest into a vm 
@login_required()
def reject_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.reject()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])

# convert an existing vmrequest into a vm 
@login_required()
def approve_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.approve()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])

# convert an existing vmrequest into a vm 
@login_required()
def convert_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.convert()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])
        
# create an update request for a VM
@login_required()
def create_vm_update_request(request, id):
	vm = VM.objects.get(pk=id)
	reqid = vm.create_update_request()
	if reqid:
		return redirect('/admin/cedainfoapp/vmrequest/%i' % reqid)
	else:
		return render_to_response('error.html', {'error':error,'user':request.user})
        
# list of GWSs presented for external viewers
@login_required()    
def gwsrequest_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id

    filter = {}
    if request.method=='POST': # if form was submitted
        form = GWSRequestListFilterForm(request.POST, initial={'request_status':'ceda approved'}, )
        filter['request_status'] = request.POST['request_status']
        items = GWSRequest.objects.filter(request_status__exact=filter['request_status']).order_by(o)
    else:   # provide a blank form
        form = GWSRequestListFilterForm(initial={'request_status':'ceda approved'}, )
        items = GWSRequest.objects.order_by(o)
        
    c = RequestContext(request, {
        'form': form,
        'items': items,
    })        
    c.update(csrf(request))
    return render_to_response('cedainfoapp/gwsrequest_list.html', c)

@login_required()
def gwsrequest_detail(request, id):
    item = get_object_or_404(GWSRequest, pk=id)
    form = GWSRequestDetailForm(instance=item)
    c = RequestContext(request, {
        'item': item,
        'form': form,
    }) 
    return render_to_response('cedainfoapp/gwsrequest_detail.html', c)
        
# list of VMRequests presented for external viewers
@login_required()  
def vmrequest_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    
    filter = {}
    if request.method=='POST': # if form was submitted
        form = VMRequestListFilterForm(request.POST, initial={'request_status':'ceda approved'}, )
        filter['request_status'] = request.POST['request_status']
        items = VMRequest.objects.filter(request_status__exact=filter['request_status']).order_by(o)
    else:   # provide a blank form
        form = VMRequestListFilterForm(initial={'request_status':'ceda approved'}, )
        items = VMRequest.objects.order_by(o)
        
    c = RequestContext(request, {
        'form': form,
        'items': items,
    })        
    c.update(csrf(request))
    return render_to_response('cedainfoapp/vmrequest_list.html', c)

@login_required()
def vmrequest_detail(request, id):
    item = get_object_or_404(VMRequest, pk=id)
    form = VMRequestDetailForm(instance=item)
    c = RequestContext(request, {
        'item': item,
        'form': form,
    }) 
    return render_to_response('cedainfoapp/vmrequest_detail.html', c)

# toggle operational status of a VM 
@login_required()
def change_status(request, id):
    vm = VM.objects.get(pk=id)
    error = vm.change_status()
    if error: 
        return render_to_response('error.html', {'error':error,'user':request.user})  
    else:
        return redirect(request.META['HTTP_REFERER'])
        
# list of actual GWSs presented for external viewers
@login_required()    
def gws_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id

    filter = {}
    if request.method=='POST': # if form was submitted
        form = GWSListFilterForm(request.POST, initial={'status':'active'}, )
        filter['status'] = request.POST['status']
        filter['path'] = request.POST['path']
        items = GWS.objects.filter(status__exact=filter['status'], path__exact=filter['path']).order_by(o)

    else:   # provide a blank form
        form = GWSListFilterForm(initial={'status':'active'}, )
        items = GWS.objects.order_by(o)
        
    total_volume = 0
    for i in items:
        total_volume += i.requested_volume
        
    c = RequestContext(request, {
        'form': form,
        'items': items,
        'total_volume': total_volume,
    })        
    c.update(csrf(request))
    return render_to_response('cedainfoapp/gws_list.html', c)

# GWS dashboard
#@login_required()    
def gws_dashboard(request):

	items = GWS.objects.all()
	c = RequestContext(request, {
		'items': items,
	})        
	c.update(csrf(request))
	return render_to_response('cedainfoapp/gws_dashboard.html', c)
	
# do du for a gws and redirect back to gws list
@login_required()
def gwsdu(request, id):
    gws = GWS.objects.get(pk=id)
    gws.du()
    return redirect(request.META['HTTP_REFERER'])

# do df for a gws and redirect back to gws list
@login_required()
def gwsdf(request, id):
    gws = GWS.objects.get(pk=id)
    gws.pan_df()
    return redirect(request.META['HTTP_REFERER'])
    
# GWS Manager list, for digestion by Elastic Tape system
# needs to be public to interact with scripts.
def gws_list_etexport(request):

    gwss = GWS.objects.all()
    return render_to_response('cedainfoapp/gws_list_etexport.html', {'items':gwss}, mimetype="text/plain")      

#
# The following 'txt' views provide a simple text dump of selected tables. These are intended to be called
# using 'curl' or 'wget' from the command line rather than via a browser. Fields are separated by a tab
# character, which allows them to be simply cut up using the 'cut' command. The list of vms was requested by
# Peter Chiu. I added the host list for good measure (actually, I implemented it by mistake!). 
#
# Note that they should not require a django login - curl or wget can't get past this. Instead, any
# security required should be added via the apache configuration for the site.
#
# Andrew 06/09/13
#
def txt_host_list (request):

    o = request.GET.get('o', 'id') # default order is ascending id
    subset = request.GET.get('subset', None) # default order is ascending id

    # define the queryset, using the subset if available
    if (subset == 'active'):
	    hosts = Host.objects.filter(retired_on=None).order_by(o)
    else:
        hosts = Host.objects.all().order_by(o)
 
    output = ''

    fields = ("hostname", 
                     "ip_addr", \
                     "serial_no",\
                     "po_no", \
                     "organization",\
                     "supplier", \
                     "arrival_date",\
                     "planned_end_of_life",\
                     "retired_on",\
                     "mountpoints",\
                     "ftpmountpoints",\
                     "host_type",\
                     "os",\
                     "capacity")
 

    for field in fields:
        output += field + '\t'
    output += '\n'

    for host in hosts:
        for field in fields:
            output += str(getattr(host, field))
            output += '\t'
  
        output += '\n'
    
    return HttpResponse(output, content_type="text/plain")


def txt_vms_list (request):

    vms = VM.objects.all().order_by('name')
 
    output = ''

    fields = ("name", \
              "type",\
              "operation_type", \
              "internal_requester",\
              "date_required",\
              "cpu_required", \
              "memory_required", \
              "disk_space_required", \
              "disk_activity_required", \
              "network_required", \
              "os_required", \
              "other_info", \
              "patch_responsible",\
              "status", \
              "created",\
              "end_of_life",\
              "retired",\
              "timestamp")

    for field in fields:
        output += field + '\t'
    output += '\n'

    for vm in vms:
        for field in fields:
            output += str(getattr(vm, field))
            output += '\t'
  
        output += '\n'

    return HttpResponse(output, content_type="text/plain")
