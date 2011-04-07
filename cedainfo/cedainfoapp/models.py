from django.db import models
from datetime import datetime
import os
import subprocess

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
        s = '<img src="https://chart.googleapis.com/chart?chs=150x50&cht=gom&chco=99FF99,999900,FF0000&chd=t:%s|%s&chls=3|3,5,5|15|10">' % (used, alloc)
	return s
    meter.allow_tags = True

    def allocated(self):
        # find total allocated space
	total = 0
        allocs = FileSet.objects.filter(partition=self)
	for a in allocs: total += a.overall_final_size
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
    logical_path = models.CharField(max_length=1024, blank=True, default='unallocated', help_text="Initially unallocated, indicating not belonging to FileSetCollection. Then set by save method of FileSetCollectionRelation to hold path within FSCR.")
    overall_final_size = BigIntegerField(help_text="Overall final size in bytes. Estimate from data scientist.") # Additional data still expected (as yet uningested) in bytes
    notes = models.TextField(blank=True)
    partition = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to = {'status': 'Allocating'},help_text="Actual partition where this FileSet is physically stored")
    storage_pot = models.CharField(max_length=1024, blank=True, default='unallocated', help_text="dd")
    migrate_to = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to = {'status': 'Allocating'},help_text="Target partition for migration", related_name='fileset_migrate_to_partition')

    def __unicode__(self):
        return u'%s' % (self.logical_path,)
    # TODO custom save method (for when assigning a partition) : check that FileSet size

    def storage_path(self):
        return os.path.normpath(self.partition.mountpoint+'/'+self.storage_pot+'/'+self.logical_path) 

    def spot_path(self): 
        return os.path.normpath(self.partition.mountpoint+'/'+self.storage_pot) 
    
    def make_spot(self):
        if self.partition:
	    if not os.path.exists(self.spot_path()): 
	        # make spot path
		# os.mkdir(self.spot_path())
		return "os.mkdir(%s)" %self.spot_path()

    def spot_exists(self):
        return os.path.exists(self.spot_path())    
    spot_exists.boolean = True

    def logical_path_exists(self):
        return os.path.exists(self.logical_path)
    logical_path_exists.boolean = True

    def status(self):
        s= "spot exists:%s (%s), " % (os.path.exists(self.spot_path()),self.spot_path())    
        s += "logical path exists:%s (%s), " % (os.path.exists(self.logical_path),self.logical_path)    
        return s

       

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

        
