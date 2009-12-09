from django.db import models

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

class HostTag(models.Model):
    tag = models.CharField(max_length=126)
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return self.tag	

class Host(models.Model):
    hostname = models.CharField(max_length=512)
    ip_addr = models.IPAddressField(blank=True)
    serial_no = models.CharField(max_length=126,blank=True)
    retired = models.BooleanField()
    po_no = models.CharField(max_length=126,blank=True)
    organization = models.CharField(max_length=512,blank=True)
    height = models.IntegerField(null=True,blank=True)
    supplier = models.CharField(max_length=126,blank=True)
    arrival_date = models.DateField(null=True,blank=True)
    planned_end_of_life = models.DateField(null=True,blank=True)
    retirement = models.CharField(max_length=126,blank=True)
    notes = models.TextField(blank=True)
    capacity = models.DecimalField(max_digits=6, decimal_places=2,null=True,blank=True)
    tags = models.ManyToManyField(HostTag, blank=True)
    def __unicode__(self):
        return self.hostname

class Rack(models.Model):
    name = models.CharField(max_length=126)
    building = models.CharField(max_length=126)
    room = models.CharField(max_length=126)
    size = models.IntegerField()
    notes = models.TextField(blank=True)
    def __unicode__(self):
	return self.name

class Slot(models.Model):
    position = models.IntegerField()
    occupant = models.ForeignKey(Host, null=True, blank=True)
    parent_rack = models.ForeignKey(Rack)
    def __unicode__(self):
        return '%s|%s' % (self.position, self.parent_rack)


class Partition(models.Model):
    mountpoint = models.CharField(blank=True,max_length=1024)
    host = models.ForeignKey(Host, blank=True, null=True)
    size = BigIntegerField(null=True, blank=True)
    capacity = BigIntegerField(null=True, blank=True)
    primary_use = models.TextField(blank=True)
    special = models.CharField(max_length=1024,blank=True)
    used = BigIntegerField(null=True, blank=True)
    type = models.CharField(max_length=512, blank=True)
    avail = BigIntegerField(null=True, blank=True)
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
    dataentity_id = models.CharField(max_length=1024, unique=True)
    friendly_name = models.CharField(max_length=1024, blank=True)
    symbolic_name = models.CharField(max_length=1024, blank=True)
    logical_path = models.CharField(max_length=1024, blank=True)
    current_size = BigIntegerField(null=True, blank=True)
    yearly_growth = BigIntegerField(null=True, blank=True)
    final_size = BigIntegerField(null=True, blank=True)
    curation_category = models.ForeignKey(CurationCategory, null=True, blank=True)
    notes = models.TextField(blank=True)
    availability_priority = models.BooleanField(null=True, blank=True)
    availability_failover = models.BooleanField(null=True, blank=True)
    backup_destination = models.CharField(max_length=1024, blank=True)
    current_backup_policy = models.ForeignKey(BackupPolicy, null=True, blank=True)
    recipes_expression = models.CharField(max_length=1024, blank=True)
    recipes_explanation = models.TextField(blank=True)
    access_status = models.ForeignKey(AccessStatus)
    db_match = models.IntegerField(null=True, blank=True) # match to "dataset" in old storage db
    def __unicode__(self):
	return self.dataentity_id

class TopLevelDir(models.Model):
    partition = models.ForeignKey(Partition)
    mounted_location = models.CharField(max_length=1024)
    badc_symlink_name = models.CharField(max_length=1024, blank=True)
    neodc_symlink_name = models.CharField(max_length=1024,blank=True)
    dataentity = models.ForeignKey(DataEntity, null=True, blank=True)
    expansion_no = models.IntegerField(null=True, blank=True)
    expansion_location = models.CharField(max_length=1024, blank=True)
    dataset_type = models.CharField(max_length=512,blank=True)
    notes = models.TextField(blank=True)
    size = BigIntegerField(null=True,blank=True)
    no_files = BigIntegerField(null=True,blank=True)
    no_dirs = BigIntegerField(null=True,blank=True)
    last_modified = models.DateTimeField(null=True,blank=True)
    status_last_checked = models.DateTimeField(null=True,blank=True)
    special = models.CharField(max_length=1024,blank=True)
    def __unicode__(self):
	return self.mounted_location

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

class DataEntityAdministrator(models.Model):
    role = models.ForeignKey(Role)
    person = models.ForeignKey(Person)
    data_entity = models.ForeignKey(DataEntity)
    def __unicode__(self):
	return '%s|%s|%s' % (self.role, self.person, self.data_entity)

class Allocation(models.Model):
    top_level_dir = models.ForeignKey(TopLevelDir)
    data_entity = models.ForeignKey(DataEntity)
    allocated_space = BigIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    proposed = models.BooleanField()
    expansion_no = models.IntegerField()
    notes = models.TextField(blank=True)
    def __unicode__(self):
	return self.top_level_dir

class HostService(models.Model):
    host = models.ForeignKey(Host)
    service_type = models.CharField(max_length=512)
    details = models.TextField()
    port = models.IntegerField(null=True, blank=True)
    def __unicode__(self):
	return self.details

class HostHistory(models.Model):
    host = models.ForeignKey(Host)
    date = models.DateField()
    history_desc = models.TextField()
    admin_contact = models.ForeignKey(Person)
    def __unicode__(self):
	return '%s|%s' % (self.host, self.date)

class DataEntityBackupLog(models.Model):
    data_entity = models.ForeignKey(DataEntity)
    backup_policy = models.ForeignKey(BackupPolicy)
    date = models.DateTimeField()
    success = models.BooleanField()
    comment = models.TextField(blank=True)
    subdirectory = models.CharField(max_length=2048)
    def __unicode__(self):
	return '%s|%s' % (self.data_entity, self.date)	
	
class ServiceBackupLog(models.Model):
    service = models.ForeignKey(HostService)
    backup_policy = models.ForeignKey(BackupPolicy)
    date = models.DateTimeField()
    success = models.BooleanField()
    comment = models.TextField(blank=True)
    def __unicode__(self):
	return '%s|%s' % (self.data_entity, self.date)	
	