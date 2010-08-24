from django.db import models
from datetime import datetime

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
    
class Rack(models.Model):
    '''Physical rack in which physical servers are installed'''
    name = models.CharField(max_length=126)
    room = models.CharField(max_length=126)
    def __unicode__(self):
        return u'%s' % self.name

class Host(models.Model):
    '''An identifiable machine having a distinct IP address'''
    hostname = models.CharField(max_length=512)
    ip_addr = models.IPAddressField(blank=True) # TODO check if admin allows no ip_addr field (otherwise default='0.0.0.0')
    serial_no = models.CharField(max_length=126,blank=True)
    po_no = models.CharField(max_length=126,blank=True)
    organization = models.CharField(max_length=512,blank=True)
    supplier = models.CharField(max_length=126,blank=True)
    arrival_date = models.DateField(null=True,blank=True)
    planned_end_of_life = models.DateField(null=True,blank=True)
    retired_on = models.DateField(null=True,blank=True)
    notes = models.TextField(blank=True)
    host_type = models.CharField(
        max_length=50,
        choices=(
            ("virtual_server","virtual server"),
            ("hypervisor_server","hypervisor server"),
            ("storage_server", "storage server"),
            ("workstation", "workstation"),
            ("server", "server"),
        ),
        default="server"
    )
    os = models.CharField(max_length=512, blank=True)
    capacity = models.DecimalField(max_digits=6, decimal_places=2,null=True,blank=True, help_text="Rough estimate in Tb only") # just an estimate (cf Partition which uses bytes from df)
    rack = models.ForeignKey(Rack, blank=True, null=True)
    hypervisor = models.ForeignKey('self', blank=True, null=True, help_text="If host_type=virtual_server, give the name of the hypervisor which contains this one.")
    def __unicode__(self):
        return u'%s' % self.hostname

class PartitionPool(models.Model):
    '''Container for paritions that are grouped together, often associated with a particular FileSetCollection'''
    purpose = models.CharField(
        max_length=50, 
        help_text="Single or general purpose partition pool",
        choices=(
            ("general","general"),
            ("single","single"),
        ),
        default="general"
       )
    def __unicode__(self):
        return u'%d : %s' % (self.id, self.purpose) 

class Partition(models.Model):
    '''Filesystem equipped with standard directory structure for archive storage'''
    mountpoint = models.CharField(blank=True,max_length=1024, help_text="E.g. /disks/machineN", unique=True)
    host = models.ForeignKey(Host, blank=True, null=True, help_text="Host on which this partition resides")
    used_bytes = BigIntegerField(default=0, help_text="\"Used\" value from df, i.e. no. of bytes used. May be populated by script.")
    capacity_bytes = BigIntegerField(default=0, help_text="\"Available\" value from df, i.e. no. of bytes total. May be populated by script.")
    last_checked = models.DateTimeField(null=True, blank=True, help_text="Last time df was run against this partition & size values updated")
    partition_pool = models.ForeignKey(PartitionPool, null=True, blank=True, help_text="Unique pool that this partition belongs to.")
    expansion_no = models.IntegerField(help_text="0 for primary, 1 to N for expansion number", default=0)
    def __unicode__(self):
        tb_remaining = (self.capacity_bytes - self.used_bytes) / (1024**4)
        return u'%s (%d %s)' % (self.mountpoint, tb_remaining, 'Tb free')
    __unicode__.allow_tags = True # seem to need this in order to use __unicode__ as one of the fields in list_display in the admin view (see http://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display)

class CurationCategory(models.Model):
    '''Category indicating whether CEDA is the primary or secondary archive (or other status) for a dataset'''
    category = models.CharField(max_length=5)
    description = models.CharField(max_length=1024)
    def __unicode__(self):
        return u"%s : %s" % (self.category, self.description) 

class BackupPolicy(models.Model):
    '''Backup policy'''
    tool = models.CharField(max_length=45, help_text="DMF / rsync / tape")
    destination = models.CharField(max_length=1024, blank=True, help_text="Path made up of e.g. dmf:/path_within_dmf, rsync:/path_to_nas_box, tape:/tape_number")
    frequency = models.CharField(max_length=45, help_text="Daily, weekly, monthly...")
    type = models.CharField(max_length=45, help_text="Full, incremental, versioned")
    policy_version = models.IntegerField(help_text="Policy version number")
    def __unicode__(self):
        return u"%s %s %s %s" % (self.tool, self.frequency, self.type, self.policy_version)

class AccessStatus(models.Model):
    '''Degree to which access to a DataEntity is restricted'''
    status = models.CharField(max_length=45)
    comment = models.CharField(max_length=1024)
    def __unicode__(self):
        return u"%s : %s" % (self.status, self.comment)

class Person(models.Model):
    '''Person with some role'''
    name = models.CharField(max_length=1024)
    email = models.EmailField()
    username = models.CharField(max_length=45)
    def __unicode__(self):
        return u'%s' % self.name

class FileSet(models.Model):
    '''Non-overlapping subtree of archive directory hierarchy.
    Collection of all filesets taken together should exactly represent 
    all files in the archive. Must never span multiple filesystems.'''
    label = models.CharField(max_length=1024, blank=True, help_text="Arbitrary label for this FileSet")
    current_size = BigIntegerField(default=0, help_text="Initial or current size, e.g. by using du on directory")
    monthly_growth = BigIntegerField(null=True, blank=True, help_text="Monthly growth in bytes (estimated by data scientist)") # monthly growth in bytes
    overall_final_size = BigIntegerField(null=True, blank=True, help_text="Overall final size in bytes. Estimate from data scientist.") # Additional data still expected (as yet uningested) in bytes
    notes = models.TextField(blank=True)
    current_backup_policy = models.ForeignKey(BackupPolicy, null=True, blank=True, help_text="Current policy which is intended to be applied to this dataset (look in backup log for record of what actually got applied)")
    partition = models.ForeignKey(Partition, blank=True, null=True, help_text="Actual partition where this FileSet is physically stored")
    def __unicode__(self):
        return u'%s : %s' % (self.id, self.label)
    # TODO custom save method (for when assigning a partition) : check that FileSet size

class FileSetCollection(models.Model):
    '''Group of fileSets handled together'''
    fileset = models.ManyToManyField(FileSet, through='FileSetCollectionRelation')
    logical_path = models.CharField(max_length=1024, help_text="Logical path to the root of this FileSetCollection. Omit trailing slash.")
    partitionpool = models.ForeignKey(PartitionPool, help_text="PartitionPool to which this FileSetCollection is allocated. Must be provided if any of the FileSets in the FileSetCollection are primary.", null=True, blank=True)
    # TODO : should really have monthly_growth / still_expected size estimates for files in the top level of the FileSetCollection (e.g. ancillary files), but for now will assume they are trivial in size (compared to FileSets)
    def __unicode__(self):
        return u'%d : %s' % (self.id, self.logical_path)

class FileSetCollectionRelation(models.Model):
    '''Documents the relationship of a fileSet with a FileSetCollection.
       A FileSet's relationship with a FileSetCollection can be:
        - primary : this is where the data are actually stored
        - secondary : symlink to the physical instance of the FileSet (and e.g. would be skipped in backups)
    '''
    fileset = models.ForeignKey(FileSet)
    fileset_collection = models.ForeignKey(FileSetCollection)
    logical_path = models.CharField(max_length=1024, blank=True, help_text="Location, relative to the FileSetCollection root, of this FileSet (NB: not the directory in which this resides). Omit leading and trailing slash.")
    is_primary = models.BooleanField(default='True', help_text="Whether or not the presence of this FileSet in this FileSetCollection represents where the FileSet is physically stored [True] (or whether it is just a symlink [False])")
    def __unicode__(self):
        return u'%s' % (self.logical_path)
    #TODO Need a custom save method where to impose uniqueness constraint : a given FileSet can only have ONE FileSetCollectionMembership that is primary (i.e. can only be stored physically in one place).       

class DataEntity(models.Model):
    '''Collection of FileSets treated together as a data set. Has corresponding MOLES DataEntity record.'''
    dataentity_id = models.CharField(help_text="MOLES data entity id", max_length=255, unique=True)
    friendly_name = models.CharField(max_length=1024, blank=True)
    symbolic_name = models.CharField(max_length=1024, blank=True)
    logical_path = models.CharField(max_length=1024, blank=True)
    fileset = models.ManyToManyField(FileSet, null=True)
    curation_category = models.ForeignKey(CurationCategory, null=True, blank=True, help_text="Curation catagory : choose from list")
    notes = models.TextField(blank=True)
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
    host = models.ManyToManyField(Host)
    name = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    externally_visible = models.BooleanField(default=False)
    deployment_type = models.CharField(max_length=50,       
        choices=(
        ("failover","failover"),
            ("loadbalanced","loadbalanced"),
            ("simple","simple")
        ),
        default="simple"
    )
    dependencies = models.ManyToManyField('self', blank=True)
    availability_tolerance = models.CharField(max_length=50,
        choices=(
        ("disposable","disposable"),
        ("immediate","must be restored ASAP"),
        ("24 hours","must be restored within 24 hours of failure"),
        ("1 workingday","must be restored within 1 working day of failure"),
        ),
        default="disposable"
    )
    requester = models.ForeignKey(Person, null=True, blank=True, related_name='service_requester')
    installer = models.ForeignKey(Person, null=True, blank=True, related_name='service_installer')
    software_contact = models.ForeignKey(Person, null=True, blank=True, related_name='service_software_contact')
    def __unicode__(self):
        return u'%s' % self.name

class HostHistory(models.Model):
    '''Entries detailing history of changes to a Host'''
    host = models.ForeignKey(Host)
    date = models.DateField()
    history_desc = models.TextField()
    admin_contact = models.ForeignKey(Person)
    def __unicode__(self):
        return u'%s|%s' % (self.host, self.date)

class FileSetBackupLog(models.Model):
    '''Backup history for a FileSet'''
    fileset = models.ForeignKey(FileSet)
    subdirectory = models.CharField(max_length=2048)
    backup_policy = models.ForeignKey(BackupPolicy)
    date = models.DateTimeField()
    success = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return u'%s|%s' % (self.data_entity, self.date)  
    
class ServiceBackupLog(models.Model):
    '''Backup history for a Service'''
    service = models.ForeignKey(Service)
    backup_policy = models.ForeignKey(BackupPolicy)
    date = models.DateTimeField()
    success = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return u'%s|%s' % (self.service, self.date)  
    
class FileSetSizeMeasurement(models.Model):
    '''Date-stampted size measurement of a FileSet'''
    fileset = models.ForeignKey(FileSet)
    date = models.DateTimeField(default=datetime.now )
    size = BigIntegerField() # in bytes
    def __unicode__(self):
        return u'%s|%s' % (self.date, self.fileset)

class FileSetAllocationPlan(models.Model):
    '''Future plan of allocation of a particular FileSet to a Partition
    Most common use case = migrating between partitions, e.g. if one partition has run
    out of space for a given fileset.
    '''
    fileset = models.ForeignKey(FileSet, help_text="FileSet to allocate to a Parition")
    partition = models.ForeignKey(Partition, help_text="Proposed Partition for allocation")
    allocated_space = BigIntegerField(help_text="Estimate of volume required (bytes)") # maximum over the entire period that this allocation represents
    start_date = models.DateTimeField(help_text="Proposed start date for this allocation. SHould be after Host.arrival_date for that partition")
    end_date = models.DateTimeField(help_text="Proposed end date for this allocation. Should be before Host.planned_end_of_life for that partition")
    notes = models.TextField(blank=True)
    def __unicode__(self):
        return u'%s|%s' % (self.fileset, self.partition)
        
# Notes from Dan

# Allocations:
# Start with data entity. DE has a log over time of its current size. Data Scientits provides either a monthly growth rate, or a still_expected amount ...describes the DE size requirements.
# Create an allocation (of a dataentity to a partition) ...manually for now. Thought process : look at remaining space & remaining time available for that machine, based on its expectied retirement date. 
# Based on info for DE described above, calculate whether or not, over that given period, there will be sufficient space to accommodate that dataentity. If so, allocation is for now until retirement date of the machine. For each partition, calculate how quickly it will fill up based on the above calculation. This will give a priority order : pick the best.

# When that allocation has been implemented, update the topleveldirs table to reflect what has been implemented (Allocation is more of a planning tool).