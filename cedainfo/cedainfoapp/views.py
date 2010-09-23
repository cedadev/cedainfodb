# Create your views here.

from django.db.models import Q
from cedainfo.cedainfoapp.models import *
from cedainfo.cedainfoapp.forms import *
#from cedainfo.cedainfoapp.custom_widgets import TinyMCE
from django.shortcuts import render_to_response, get_object_or_404
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

def dataentity_fileset_view(request):
    '''Complete list of dataentities and their component filesets'''
    de_list = DataEntity.objects.all()
    # build a dictionary of these de objects, containing their filesets
    de_dict = dict()
    for de in de_list:
        fs_list = de.fileset.all()
        de_dict[ de ] = fs_list
    return render_to_response('cedainfoapp/dataentity_fileset_list.html', {'de_dict': de_dict} )

def filesetcollection_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    qs = FileSetCollection.objects.order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/filesetcollection_list.html",
        template_object_name = "filesetcollection",
    )
    
def filesetcollection_list_extended(request):
    '''Full view of filesetcollections, meant to be functional replacement for table on Dan's volume planning Wiki page
       http://proj.badc.rl.ac.uk/badc/wiki/VolumePlanning'''
    # Columns:
    # FileSetCollection (loosely one-to-one with DataEntity (via logical_path) )
    # For each Partition in PartitionPool associated with this FileSetCollection:
    #   Partition
    #   Partition.Host.arrival_date
    #   Parition.capacity_bytes
    #   Parition.Host.planned_end_of_life
    #   FileSetCollection total current size (sum of most recent primary FSSMs for this fileset)
    #   FileSet.monthly_growth (TODO ...group by partition)
    #   FileSet.overall_total_size (TODO ...group by partition)
    #   contact (...needs to come from DataEntity(filter=same logical path as fileset).responsible_officer
    #   Derived field : FSC won't drow too big before end of machine warranty period
    #   Derived field : Escess / Deficit

    o = request.GET.get('o', 'id') # default order is ascending id
    fsc_list = FileSetCollection.objects.order_by(o)
    fsc_count = 0
    my_fsc_list = []
    for fsc in fsc_list:
        # add some dynamic attributes to make things easier in the template
        fsc.partitions = Partition.objects.filter(partition_pool=fsc.partitionpool)
        for partition in fsc.partitions:
            partition.filesets = FileSet.objects.filter(partition=partition)
        fscr_list = FileSetCollectionRelation.objects.filter(fileset_collection=fsc)
        fsc.size_all_filesets_incl_nonprimary_sum = 0
        fsc.size_all_filesets_primaryonly_sum = 0
        fsc.num_filesets_unallocated = 0
        for fscr in fscr_list:
            try:
                fssm = FileSetSizeMeasurement.objects.filter(fileset=fscr.fileset).order_by('-date')
                if fssm != None:
                    size = fssm[0].size
                else:
                    size = 0
            except:
                size = 0 # NB sets size to zero if no measurement found.
            fsc.size_all_filesets_incl_nonprimary_sum += size
            if fscr.is_primary:
                fsc.size_all_filesets_primaryonly_sum += size
            fsc_count += 1
            # filesets that belong to this filesetcollection (have an fscr) but no partition allocated
            if (fscr.fileset.partition is None) or (fscr.fileset.partition == ''):
                fsc.num_filesets_unallocated += 1

        my_fsc_list.append(fsc)

    return render_to_response('cedainfoapp/filesetcollection_list_extended.html', 
        {
            'filesetcollection_list': my_fsc_list,
        }
    )
    


# Show total storage requirements for a FileSetCollection, calculated with and without non-primary FileSet members.
def filesetcollection_view(request, id):
    # Get this FileSetCollection
    fsc = FileSetCollection.objects.get(pk=id)
    # Get the FileSetCollectionMemberships associated with this FileSetCollection
    # These will be the fileset's we're interested in
    fscr_list = FileSetCollectionRelation.objects.filter(fileset_collection=fsc)

    # Use dynamic atributes to aggregate sizes of all filesets within filesetcollection
    # ...with and without non-primary filesets
    fsc.size_all_filesets_incl_nonprimary_sum = 0
    fsc.size_all_filesets_primaryonly_sum = 0
    fsc_count=0
    for fscr in fscr_list:
        try:
            fssm = FileSetSizeMeasurement.objects.filter(fileset=fscr.fileset).order_by('-date')
            if fssm != None:
                size = fssm[0].size
            else:
                size = 0
        except:
            size = 0 # NB sets size to zero if no measurement found.
        fscr_list[fsc_count].fileset.current_size = size #???
        fsc.size_all_filesets_incl_nonprimary_sum += size
        if fscr.is_primary:
            fsc.size_all_filesets_primaryonly_sum += size
        fsc_count += 1
    
    return render_to_response('cedainfoapp/filesetcollection_view.html', {'fsc': fsc, 'fscr_list': fscr_list} )

def partitionpool_list(request):
    o = request.GET.get('o', 'id') # default order is ascending id
    qs = PartitionPool.objects.order_by(o)
    # Use the object_list view.
    return list_detail.object_list(
        request,
        queryset = qs,
        template_name = "cedainfoapp/partitionpool_list.html",
        template_object_name = "partitionpool",
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

#### Methods to setup filesetcollections

def filesetcollection_setup(request):
# Workflow for setting up new FileSetCollection

    return render_to_response('cedainfoapp/filesetcollection_setup.html', )

from fsc_manager import *

def filesetcollection_link_fsc_partition(request):
    
    #Choose or create a filesetcollection to link with a ParitionPool
    form = None
    disabled = None
    status = None
    if request.method=='POST':
        # Must have come from a form submission ...process the form
        form = FileSetCollectionLinkForm(request.POST)
        if form.is_valid():
            fsc = form.cleaned_data['filesetcollection']
            logging.debug("Got fsc from form : %s" % fsc)
            if fsc.partitionpool is not None:
                if Partition.objects.filter(partition_pool=fsc.partitionpool).count() < 1:
                    # Parition pool has no partitions
                    status = "Selected PartitionPool has no Partitions associated with it : please try again"
                else:
                    try:
                        tool = fsc_partition_linker(fsc.logical_path)
                        logging.info("About to link filesetcollection to partitionpool")
                        tool.link_fsc_to_partitions()
                        status = "Done"
                    except:
                        status = "Error"
            else:
                # No partitionpool attached to this FSC
                status = "Selected FileSetCollection has no ParitionPool : please try again"
    else:
        # First time loading page is via GET, from a link
        form = FileSetCollectionLinkForm()

    return render_to_response('cedainfoapp/filesetcollection_link.html', {'form': form, 'status': status})

def filesetcollection_make_filesets(request):
    '''Parse a CSV File to define filesets & their estimated sizes'''
    status = None
    fs_made = []
    if request.method == 'POST':
        form = FileSetMakerForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # do something
                logging.info("Setting up tool for making FileSets")
                fsc = form.cleaned_data['filesetcollection']
                logging.info("Got FileSetCollection %s from form" % fsc)
                file = form.cleaned_data['file']
                logging.info("Got File %s from form" % file)
                tool = filesetmaker(fsc.logical_path)
                logging.info("Made tool")
                fs_made = tool.make_filesets_from_csv( file )
                logging.info("Made FileSets")
                status = 'success : %d filesets made' % len(fs_made)
            except:
                status = "Error"
    else:
        form = FileSetMakerForm()

    return render_to_response('cedainfoapp/filesetcollection_make_filesets.html', {'form': form, 'status': status, 'fs_made': fs_made})

