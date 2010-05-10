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
    name = models.CharField(max_length=126)
    room = models.CharField(max_length=126)
    def __unicode__(self):
	return self.name

class Host(models.Model):
    hostname = models.CharField(max_length=512)
    ip_addr = models.IPAddressField(blank=True)
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
    capacity = models.DecimalField(max_digits=6, decimal_places=2,null=True,blank=True) # just an estimate (cf Partition which uses bytes from df)
    rack = models.ForeignKey(Rack, blank=True, null=True)
    hypervisor = models.ForeignKey('self', blank=True, null=True)
    def __unicode__(self):
        return self.hostname

class Partition(models.Model):
    # individual filesystem equipped with standard directory structure for archive storage
    mountpoint = models.CharField(blank=True,max_length=1024)
    host = models.ForeignKey(Host, blank=True, null=True) # implies partition can only exist on StorageHost (not PhysicalHost or VirtualHost)
    used_bytes = BigIntegerField(null=True, blank=True) # "Used" in df-speak, i.e. no. of bytes used (mutable & constantly updated from df)
    capacity_bytes = BigIntegerField(null=True, blank=True) # "Size" in df-speak, i.e. physical size of partition
    primary_use = models.TextField(blank=True)
    special = models.CharField(max_length=1024,blank=True)
    type = models.CharField(max_length=512, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    def __unicode__(self):
	return self.mountpoint

class CurationCategory(models.Model):
    category = models.CharField(max_length=5)
    description = models.CharField(max_length=1024)
    def __unicode__(self):
	return self.category

class BackupPolicy(models.Model):
    tool = models.CharField(max_length=45)
    frequency = models.CharField(max_length=45)
    type = models.CharField(max_length=45)
    policy_version = models.IntegerField()
    def __unicode__(self):
	return self.tool

class AccessStatus(models.Model):
    status = models.CharField(max_length=45)
    comment = models.CharField(max_length=1024)
    def __unicode__(self):
        return self.status

class DataEntity(models.Model):
    dataentity_id = models.CharField(max_length=255, unique=True)
    friendly_name = models.CharField(max_length=1024, blank=True)
    symbolic_name = models.CharField(max_length=1024, blank=True)
    logical_path = models.CharField(max_length=1024, blank=True)
    monthly_growth = BigIntegerField(null=True, blank=True) # monthly growth in bytes
    still_expected = BigIntegerField(null=True, blank=True) # Additional data still expected (as yet uningested) in bytes
    curation_category = models.ForeignKey(CurationCategory, null=True, blank=True)
    notes = models.TextField(blank=True)
    availability_priority = models.BooleanField(default=False)
    availability_failover = models.BooleanField(default=False)
    backup_destination = models.CharField(max_length=1024, blank=True)
    current_backup_policy = models.ForeignKey(BackupPolicy, null=True, blank=True)
    recipes_expression = models.CharField(max_length=1024, blank=True)
    recipes_explanation = models.TextField(blank=True)
    access_status = models.ForeignKey(AccessStatus)
    db_match = models.IntegerField(null=True, blank=True) # id match to "dataset" in old storage db
    def __unicode__(self):
	return '%s (%s)' % (self.dataentity_id, self.symbolic_name)

class TopLevelDir(models.Model):
    # top-level dir on a partition of a nas box, e.g. /disks/foo1/archive/<dataentity symbolic name>
    # expansion example would be /disks/foo1/archive/.<dataentity symbolic name>_expansion1
    partition = models.ForeignKey(Partition, null=True, blank=True) # allow to be temporarily null (until db built 1st time)
    mounted_location = models.CharField(max_length=1024)
    badc_symlink_name = models.CharField(max_length=1024, blank=True)
    neodc_symlink_name = models.CharField(max_length=1024,blank=True)
    dataentity = models.ForeignKey(DataEntity, null=True, blank=True)
    expansion_no = models.IntegerField(null=True, blank=True) # convention: 0 (or null) if this is the only topleveldir. 1,2,3, otherwise
    dataset_type = models.CharField(max_length=512,blank=True)
    notes = models.TextField(blank=True)
    size = BigIntegerField(null=True,blank=True) # 
    no_files = BigIntegerField(null=True,blank=True)
    last_modified = models.DateTimeField(null=True,blank=True)
    status_last_checked = models.DateTimeField(null=True,blank=True)
    special = models.CharField(max_length=1024,blank=True)
    def __unicode__(self):
        expansion_label = 'primary'
	if self.expansion_no != 0:
	    expansion_label = 'expansion_%d' % expansion_no
	return '%s|%s|%s' % (self.dataentity.symbolic_name, expansion_label, self.mounted_location )

class Role(models.Model):
    role = models.CharField(max_length=45)
    comment = models.TextField(blank=True)
    def __unicode__(self):
	return self.role

class Person(models.Model):
    name = models.CharField(max_length=1024)
    email = models.EmailField()
    username = models.CharField(max_length=45)
    def __unicode__(self):
	return self.name

class DataEntityContact(models.Model):
    role = models.ForeignKey(Role)
    person = models.ForeignKey(Person)
    data_entity = models.ForeignKey(DataEntity)
    def __unicode__(self):
	return '%s|%s|%s' % (self.role, self.person, self.data_entity)

class Allocation(models.Model):
    # allocation of a topleveldir (for a primary or expansion dir) to a partition
    # example
    # "this particular topleveldir is to be moved to this parition via migration or be received there via ingest"
    # The same topleveldir can have multiple entries in this table because of migrations, i.e. can be scheduled to move to another partition on a given date
    top_level_dir = models.ForeignKey(TopLevelDir)
    partition = models.ForeignKey(Partition)
    allocated_space = BigIntegerField() # maximum over the entire period that this allocation represents
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    notes = models.TextField(blank=True)
    def __unicode__(self):
	return '%s|%s' % (self.top_level_dir, self.partition)

class Service(models.Model):
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
	return self.name

class HostHistory(models.Model):
    host = models.ForeignKey(Host)
    date = models.DateField()
    history_desc = models.TextField()
    admin_contact = models.ForeignKey(Person)
    def __unicode__(self):
	return '%s|%s' % (self.host, self.date)

class DataEntityBackupLog(models.Model):
    data_entity = models.ForeignKey(DataEntity)
    subdirectory = models.CharField(max_length=2048)
    backup_policy = models.ForeignKey(BackupPolicy)
    date = models.DateTimeField()
    success = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    def __unicode__(self):
	return '%s|%s' % (self.data_entity, self.date)	
	
class ServiceBackupLog(models.Model):
    service = models.ForeignKey(Service)
    backup_policy = models.ForeignKey(BackupPolicy)
    date = models.DateTimeField()
    success = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    def __unicode__(self):
	return '%s|%s' % (self.service, self.date)	
	
class DataEntitySizeMeasurement(models.Model):
    # entry giving measured size of dataset on given date
    dataentity = models.ForeignKey(DataEntity)
    date = models.DateTimeField(default=datetime.now )
    size = BigIntegerField() # in bytes

# Notes from Dan

# Allocations:
# Start with data entity. DE has a log over time of its current size. Data Scientits provides either a monthly growth rate, or a still_expected amount ...describes the DE size requirements.
# Create an allocation (of a dataentity to a partition) ...manually for now. Thought process : look at remaining space & remaining time available for that machine, based on its expectied retirement date. 
# Based on info for DE described above, calculate whether or not, over that given period, there will be sufficient space to accommodate that dataentity. If so, allocation is for now until retirement date of the machine. For each partition, calculate how quickly it will fill up based on the above calculation. This will give a priority order : pick the best.

# When that allocation has been implemented, update the topleveldirs table to reflect what has been implemented (Allocation is more of a planning tool).