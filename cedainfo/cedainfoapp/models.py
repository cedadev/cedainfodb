from django.db import models
from datetime import datetime
import os, sys
import subprocess
import string

# Needed for BigInteger fix
from django.db.models.fields import IntegerField
from django.conf import settings

# BigInteger fix as per http://www.mattwaite.com/posts/2009/mar/10/django-and-really-big-numbers/
class BigIntegerField(IntegerField):
    empty_strings_allowed=False
    def get_internal_type(self):
        return "BigIntegerField"    
    def db_type(self):
        return 'bigint' # Will this work with non-postgres?

# Create your models here.

# Tags to help in creation of SDDCS nodelist view
# Each tag can itself be tagged (hence tag attribute)
#class NodeListTag(models.Model):
#    name=models.CharField(max_length=126, help_text="name of this tag")
#    tag=models.ManyToManyField('self', null=True, blank=True, help_text="tag associated with this tag")
#    def __unicode__(self):
#        return u'%s' % self.name

class NodeList(models.Model):
    name = models.CharField(max_length=126)
    def __unicode__(self):
        return u'%s the nodelist' % self.name

class HostList(models.Model):
    nodelist = models.OneToOneField(NodeList)
    def __unicode__(self):
        return u'%s the hostlist' % self.nodelist.name

class RackList(models.Model):
    nodelist = models.OneToOneField(NodeList)
    def __unicode__(self):
        return u'%s the racklist' % self.nodelist.name
        

class Rack(models.Model):
    '''Physical rack in which physical servers are installed'''
    name = models.CharField(max_length=126, help_text="Name of Rack")
    room = models.CharField(max_length=126, help_text="Physical location of Rack")
    #tag = models.ManyToManyField(NodeListTag, null=True, blank=True, help_text="tag for nodelist")
    racklist = models.ForeignKey(RackList, null=True, blank=True, help_text="list this rack belongs to (only one)")
    def __unicode__(self):
        return u'%s' % self.name

class Host(models.Model):
    '''An identifiable machine having a distinct IP address'''
    hostname = models.CharField(max_length=512, help_text="Full hostname e.g. machine.badc.rl.ac.uk")
    ip_addr = models.IPAddressField(blank=True, help_text="IP Address") # TODO check if admin allows no ip_addr field (otherwise default='0.0.0.0')
    serial_no = models.CharField(max_length=126,blank=True, help_text="Serial no (if physical machine)")
    po_no = models.CharField(max_length=126,blank=True, help_text="Purchase order no (if physical machine)")
    organization = models.CharField(max_length=512,blank=True, help_text="Organisation for which machine was purchased (if physical machine)")
    supplier = models.CharField(max_length=126,blank=True, help_text="Hardware supplier (if physical machine)")
    arrival_date = models.DateField(null=True,blank=True, help_text="Date host was installed (physical) / created (virtual)")
    planned_end_of_life = models.DateField(null=True,blank=True, help_text="Date foreseen for retirement of machine (if physical machine)")
    retired_on = models.DateField(null=True,blank=True, help_text="Date host was retired (leave blank if still in service)")
    notes = models.TextField(blank=True, help_text="Additional notes")
    host_type = models.CharField(
        max_length=50,
        choices=(
            ("virtual_server","virtual server"),
            ("hypervisor_server","hypervisor server"),
            ("storage_server", "storage server"),
            ("workstation", "workstation"),
            ("server", "server"),
        ),
        default="server",
        help_text="Type of host"
    )
    os = models.CharField(max_length=512, blank=True, help_text="Operating system")
    capacity = models.DecimalField(max_digits=6, decimal_places=2,null=True,blank=True, help_text="Rough estimate in Tb only") # just an estimate (cf Partition which uses bytes from df)
    rack = models.ForeignKey(Rack, blank=True, null=True, help_text="Rack (if virtual machine, give that of hypervisor)")
    hypervisor = models.ForeignKey('self', blank=True, null=True, help_text="If host_type=virtual_server, give the name of the hypervisor which contains this one.")
    #tag = models.ManyToManyField(NodeListTag, null=True, blank=True, help_text="tag for nodelist")
    hostlist = models.ManyToManyField(HostList, null=True, blank=True, help_text="list(s) this host belongs to")
    def __unicode__(self):
        return u'%s' % self.hostname


class Partition(models.Model):
    '''Filesystem equipped with standard directory structure for archive storage'''
    mountpoint = models.CharField(blank=True,max_length=1024, help_text="E.g. /disks/machineN", unique=True)
    host = models.ForeignKey(Host, blank=True, null=True, help_text="Host on which this partition resides")
    used_bytes = BigIntegerField(default=0, help_text="\"Used\" value from df, i.e. no. of bytes used. May be populated by script.")
    capacity_bytes = BigIntegerField(default=0, help_text="\"Available\" value from df, i.e. no. of bytes total. May be populated by script.")
    last_checked = models.DateTimeField(null=True, blank=True, help_text="Last time df was run against this partition & size values updated")
    status = models.CharField(max_length=50,       
              choices=(("Blank","Blank"),
                 ("Allocating","Allocating"),
                 ("Closed","Closed"),
                 ("Migrating","Migrating"),
                 ("Retired","Retired")) )

    def df(self):
        """Report disk usage.
           Return a dictionary with total, used, available. Sizes are reported
           in blocks of 1024 bytes."""
        if os.path.ismount(self.mountpoint):
            output = subprocess.Popen(['/bin/df', '-B 1024', self.mountpoint],
                                     stdout=subprocess.PIPE).communicate()[0]
            lines = output.split('\n')
	    if len(lines) == 3: dev, blocks_total, blocks_used, blocks_available, used, mount = lines[1].split()
	    if len(lines) == 4: blocks_total, blocks_used, blocks_available, used, mount = lines[2].split()
            self.capacity_bytes = int(blocks_total)*1024
            self.used_bytes = int(blocks_used)*1024
	    self.last_checked = datetime.now()
	    self.save() 
        return      

    def exists(self):
        return os.path.ismount(self.mountpoint)  
    exists.boolean = True

    def list_allocated(self):
        # list allocation for admin interface
        s = ''
        allocs = FileSet.objects.filter(partition=self)
	for a in allocs:
	    s += '<a href="/admin/cedainfoapp/fileset/%s">%s</a> ' % (a.pk,a.logical_path)
	return s
    list_allocated.allow_tags = True
	
    def meter(self):
        # meter for 
        if self.capacity_bytes == 0: return "No capacity set"
        used = self.used_bytes*100/self.capacity_bytes
        alloc = self.allocated()*100/self.capacity_bytes
        # Find the set of most recent FileSetSizeMeasurements for FileSets on this Partition
        filesetsum = 0
        filesets = FileSet.objects.filter(partition=self)
        for fs in filesets:
            try:
                fssm = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')[0]
                filesetsum += fssm.size
            except:
                filesetsum += 0
        # Turn this into a percentage of capacity
        filesetsum = filesetsum*100/self.capacity_bytes
        #s = '<img src="https://chart.googleapis.com/chart?chs=150x50&cht=gom&chco=99FF99,999900,FF0000&chd=t:%s|%s&chls=3|3,5,5|15|10"> %s%% Used, %s%% Allocated ' % (used, alloc,used, alloc)
        s = '<img src="http://chart.googleapis.com/chart?chxt=y&cht=bhs&chd=t:%s,%s,%s&chco=FF0000|00FF00|0000FF&chls=1.0&chs=200x100&chxl=0:|SumOfFileSets|Allocated|UsedCapacity&chm=N*f0*%%,000000,0,-1,11" alt="U:%s%% A:%s%% F:%s%%" title="U:%s%% A:%s%% F:%s%%">' % (used, alloc, filesetsum,used, alloc, filesetsum,used, alloc, filesetsum)
        return s
    meter.allow_tags = True

    def allocated(self):
        # find total allocated space
	total = 0
        allocs = FileSet.objects.filter(partition=self)
	for a in allocs: total += a.overall_final_size
	return total
    
    def used_by_filesets(self):
        # find total allocated space
        total = 0
        filesets = FileSet.objects.filter(partition=self)
        # for each fileset, find most recent FileSetSizeMeasurement
        
        for fs in filesets:
            fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')[0]
            total += fssms.size 
        return total
            
    def links(self):
        # links to actions for partions
	s = '<a href="/partition/%s/df">update df</a> ' % (self.pk,)
	return s
    links.allow_tags = True

    def __unicode__(self):
        tb_remaining = (self.capacity_bytes - self.used_bytes) / (1024**4)
        return u'%s (%d %s)' % (self.mountpoint, tb_remaining, 'Tb free')
    __unicode__.allow_tags = True # seem to need this in order to use __unicode__ as one of the fields in list_display in the admin view (see http://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display)


class CurationCategory(models.Model):
    '''Category indicating whether CEDA is the primary or secondary archive (or other status) for a dataset'''
    category = models.CharField(max_length=5, help_text="Curation category label")
    description = models.CharField(max_length=1024, help_text="Longer description")
    def __unicode__(self):
        return u"%s : %s" % (self.category, self.description) 

class BackupPolicy(models.Model):
    '''Backup policy'''
    tool = models.CharField(max_length=45, help_text="e.g. DMF / rsync / tape")
    destination = models.CharField(max_length=1024, blank=True, help_text="Path made up of e.g. dmf:/path_within_dmf, rsync:/path_to_nas_box, tape:/tape_number")
    frequency = models.CharField(max_length=45, help_text="Daily, weekly, monthly...")
    type = models.CharField(max_length=45, help_text="Full, incremental, versioned")
    policy_version = models.IntegerField(help_text="Policy version number")
    def __unicode__(self):
        return u"%s %s %s %s" % (self.tool, self.frequency, self.type, self.policy_version)

class AccessStatus(models.Model):
    '''Degree to which access to a DataEntity is restricted'''
    status = models.CharField(max_length=45, help_text="Status label")
    comment = models.CharField(max_length=1024, help_text="Comment describing this status")
    def __unicode__(self):
        return u"%s : %s" % (self.status, self.comment)

class Person(models.Model):
    '''Person with some role'''
    name = models.CharField(max_length=1024, help_text="Firstname Lastname")
    email = models.EmailField(help_text="Email address")
    username = models.CharField(max_length=45, help_text="System username")
    def __unicode__(self):
        return u'%s' % self.name

class FileSet(models.Model):
    ''' subtree of archive directory hierarchy.
    Collection of all filesets taken together should exactly represent 
    all files in the archive. Must never span multiple filesystems.'''
    logical_path = models.CharField(max_length=1024, blank=True, default='/badc/NNNN', help_text="e.g. /badc/acsoe")
    overall_final_size = BigIntegerField(help_text="The allocation given to a fileset is an estimate of the final size on disk. If the dataset is going to grow indefinitely then estimate the size for 4 years ahead. Filesets can't be bigger than a single partition, but in order to aid disk managment they should no exceed 20% of the size of a partition.") # Additional data still expected (as yet uningested) in bytes
    notes = models.TextField(blank=True)
    partition = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to = {'status': 'Allocating'},help_text="Actual partition where this FileSet is physically stored")
    storage_pot = models.CharField(max_length=1024, blank=True, default='', help_text="dd")
    migrate_to = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to = {'status': 'Allocating'},help_text="Target partition for migration", related_name='fileset_migrate_to_partition')
    secondary_partition = models.ForeignKey(Partition, blank=True, null=True, help_text="Target for secondary disk copy", related_name='fileset_secondary_partition')
    dmf_backup = models.BooleanField(default=False, help_text="Backup to DMF")
    sd_backup = models.BooleanField(default=False, help_text="Backup to Storage-D")

    def __unicode__(self):
        return u'%s' % (self.logical_path,)
    # TODO custom save method (for when assigning a partition) : check that FileSet size

    def storage_path(self):
        return os.path.normpath(self.partition.mountpoint+'/'+self.storage_pot) 

    def make_spot(self, prefix='archive'):
        # create a storage pot and link 
        if self.storage_pot != '': return  #can't make a spot if it already exists in the db
        if self.logical_path_exists(): return #can't make a spot if logical path exists  
        if not self.partition: return #can't make a spot if no partition 

        spotname = "%s/spot-%s" % (prefix,self.pk)
        self.storage_pot = spotname
        try:
            os.makedirs(self.storage_path())
        except:
            return ("os.makedirs(%s)" % self.storage_path(), sys.exc_value )
        try:
	    os.symlink(self.storage_path(), self.logical_path)
        except: 
            return ("os.symlink(%s, %s)" % (self.storage_path(),self.logical_path),sys.exc_value )
        self.save()

    def spot_display(self):
        if self.storage_pot: return "%s" % self.storage_pot
        else: return '<a href="/fileset/%s/makespot">Create Storage</a>' % self.pk
    spot_display.allow_tags = True
    spot_display.short_description = 'Storage pot'

    def spot_exists(self):
        return os.path.exists(self.storage_path())    
    spot_exists.boolean = True

    def logical_path_exists(self):
        return os.path.exists(self.logical_path)
    logical_path_exists.boolean = True

    def partition_display(self):
        if self.partition: return "Partition Set" 
        else: return '<a href="/fileset/%s/allocate">Allocate</a>' % self.pk
    partition_display.allow_tags = True
    partition_display.short_description = 'Allocate Partition'
    
    def allocate(self):
        # find partion for this fileset
        if self.partition: return # return if already allocated
	
        # if its already a link to a '/disks/'
	if os.path.islink(self.logical_path): 
            # get storage path
            linkpath = os.readlink(self.logical_path)
	    if linkpath[0:7] == '/disks/': # look like it is already allocated
	        # find mount point
	        p = linkpath
	        oldspot = ''
	        while 1: 
                    head, tail = os.path.split(p)
	            oldspot = os.path.join(tail, oldspot) 	
	            if os.path.ismount(head): 
		        self.partition = Partition.objects.get(mountpoint=head)
			self.storage_pot = oldspot
			self.notes += 'allocated from pre-existing links to /disks/'
			self.save()
			return		 
	            p = head
		    
        else:
	    partitions = Partition.objects.filter(status='Allocating')
            # find the fullest partition which can accomidate the file set
	    allocated_partition = None
	    fullest_space = 10e40
	    for p in partitions:
	        partition_free_space = 0.95 * p.capacity_bytes - p.allocated()
		# if this partition could accommidate file set...
		if partition_free_space > self.overall_final_size:
		    # ... and its the fullest so far  
		    if partition_free_space < fullest_space:
		        allocated_partition = p
			fullest_space = partition_free_space
		
            self.partition = allocated_partition
	    self.notes += 'Allocated by algorythum'
            self.save()
    
    def du(self):
        '''Report disk usage of FileSet by creating as FileSetSizeMeasurement.'''
        if self.spot_exists() and os.path.ismount(self.partition.mountpoint):
            output = subprocess.Popen(['/bin/du', '-sk', self.storage_path()],stdout=subprocess.PIPE).communicate()[0]
            lines = output.split('\n')
            if len(lines) == 2: size, path = lines[0].split()
            fssm = FileSetSizeMeasurement(fileset=self, date=datetime.now(), size=int(size)*1024)
            fssm.save() 
        return      

    def links(self):
        # links to actions for filesets
        s = '<a href="/fileset/%s/du">du</a> ' % (self.pk,)
        return s
    links.allow_tags = True
    
    # TODO...
    #def size_history(self):
    #    # display graph of size history for fileset
    #    fssms = FileSetSizeMeasurements.filter(fileset=self).order_by('date')
    #    size_values = fssms.values_list('size', flat=True)
    #    size_values = map(str, size_values)
    #    size_values = string.join(size_values,',')
        
    #    date_values = fssms.values_list('date', flat=True)
    #    date_values = map(datetime.toordinal, date_values)
    #    date_values = string.join(date_values,',')
        
        #if self.capacity_bytes == 0: return "No measurements"
        #used = self.used_bytes*100/self.capacity_bytes
        #alloc = self.allocated()*100/self.capacity_bytes
    #    s = '<img src="https://chart.googleapis.com/chart?chs=150x50&cht=gom&chco=99FF99,999900,FF0000&chd=t:|&chls=3#|3,5,5|15|10">'
    #    return s
    #size_history.allow_tags = True
        
class DataEntity(models.Model):
    '''Collection of data treated together. Has corresponding MOLES DataEntity record.'''
    dataentity_id = models.CharField(help_text="MOLES data entity id", max_length=255, unique=True)
    friendly_name = models.CharField(max_length=1024, blank=True, help_text="Longer name (possibly incl spaces, braces)")
    symbolic_name = models.CharField(max_length=1024, blank=True, help_text="Short abbreviation to be used for directory names etc")
    logical_path = models.CharField(max_length=1024, blank=True, help_text="Top level of location within archive")
    curation_category = models.ForeignKey(CurationCategory, null=True, blank=True, help_text="Curation catagory : choose from list")
    notes = models.TextField(blank=True, help_text="Additional notes")
    availability_priority = models.BooleanField(default=False, help_text="Priority dataset : use highest spec hardware")
    availability_failover = models.BooleanField(default=False, help_text="Whether or not this dataset requires redundant copies for rapid failover (different from recovery from backup)")
    access_status = models.ForeignKey(AccessStatus, help_text="Security applied to dataset")
    recipes_expression = models.CharField(max_length=1024, blank=True)
    recipes_explanation = models.TextField(blank=True, help_text="Verbal explanation of registration process. Can be HTML snippet. To be used in dataset index to explain to user steps required to gain access to dataset.")
    db_match = models.IntegerField(null=True, blank=True, help_text="Admin use only : please ignore") # id match to "dataset" in old storage db
    responsible_officer = models.ForeignKey(Person, blank=True, null=True, help_text="CEDA person acting as contact for this dataset")
    last_reviewed = models.DateField(null=True, blank=True, help_text="Date of last dataset review")
    review_status = models.CharField(
        max_length=50,
        choices=(
            ("to be reviewed","to be reviewed"),
            ("in review","in review"),
            ("reviewed but issues", "reviewed but issues"),
            ("passed", "passed"),
        ),
        default="to be reviewed",
        help_text="Remember to set date of next review if \"to be reviewed\""
    )
    next_review = models.DateField(null=True, blank=True, help_text="Date of next dataset review")
    def __unicode__(self):
        return u'%s (%s)' % (self.dataentity_id, self.symbolic_name)

class Service(models.Model):
    '''Software-based service'''
    #host = models.ManyToManyField(Host, help_text="Host machine on which service is deployed", null=True, blank=True)
    host = models.ForeignKey(Host, help_text="Host machine on which service is deployed", null=True, blank=True)
    name = models.CharField(max_length=512, help_text="Name of service")
    active = models.BooleanField(default=False, help_text="Is this service active or has it been decomissioned?")
    description = models.TextField(blank=True, help_text="Longer description if needed")
    documentation = models.URLField(verify_exists=False, blank=True, help_text="URL to documentation for service in opman")
    externally_visible = models.BooleanField(default=False, help_text="Whether or not this service is visible outside the RAL firewall")
    deployment_type = models.CharField(max_length=50,       
        choices=(
        ("failover","failover"),
            ("loadbalanced","loadbalanced"),
            ("simple","simple")
        ),
        default="simple",
        help_text="Type of deployment"
    )
    dependencies = models.ManyToManyField('self', blank=True, null=True, help_text="Other services that this one depends on")
    availability_tolerance = models.CharField(max_length=50,
        choices=(
        ("immediate","must be restored ASAP"),
        ("24 hours","must be restored within 24 hours of failure"),
        ("1 workingday","must be restored within 1 working day of failure"),
        ("3 workingdays","must be restored within 3 working days of failure"),
        ("1 week","must be restored within 1 week of failure"),
        ("2 weeks","must be restored within 2 weeks of failure"),
        ("1 month","must be restored within 1 month of failure"),
        ("disposable","disposable"),
        ),
        default="disposable",
        help_text="How tolerant of unavailability we should be for this service"
    )
    requester = models.ForeignKey(Person, null=True, blank=True, related_name='service_requester', help_text="CEDA Person requesting deployment")
    installer = models.ForeignKey(Person, null=True, blank=True, related_name='service_installer', help_text="CEDA Person installing the service")
    software_contact = models.ForeignKey(Person, null=True, blank=True, related_name='service_software_contact', help_text="CEDA or 3rd party contact who is responsible for the software component used for the service")
    def __unicode__(self):
        theHost = ''
        if self.host is not None:
            theHost = self.host
        return u'%s (%s)' % (self.name, theHost)

class HostHistory(models.Model):
    '''Entries detailing history of changes to a Host'''
    host = models.ForeignKey(Host, help_text="Host name")
    date = models.DateField(help_text="Event date")
    history_desc = models.TextField(help_text="Details of event / noteworthy item in host's history")
    admin_contact = models.ForeignKey(Person, help_text="CEDA Person reporting this event")
    def __unicode__(self):
        return u'%s|%s' % (self.host, self.date)

    
class ServiceBackupLog(models.Model):
    '''Backup history for a Service'''
    service = models.ForeignKey(Service, help_text="Service being backed up")
    backup_policy = models.ForeignKey(BackupPolicy, help_text="Backup policy implemented for this backup event")
    date = models.DateTimeField(help_text="Date and time of backup")
    success = models.BooleanField(default=False, help_text="Success (True) or Failure (False) of backup event")
    comment = models.TextField(blank=True, help_text="Additional comment(s)")
    def __unicode__(self):
        return u'%s|%s' % (self.service, self.date)  
    
class FileSetSizeMeasurement(models.Model):
    '''Date-stampted size measurement of a FileSet'''
    fileset = models.ForeignKey(FileSet, help_text="FileSet that was measured")
    date = models.DateTimeField(default=datetime.now, help_text="Date and time of measurement")
    size = BigIntegerField(help_text="Size in bytes") # in bytes
    no_files = BigIntegerField(null=True, blank=True, help_text="Number of files") 
    def __unicode__(self):
        return u'%s|%s' % (self.date, self.fileset)

        
