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


class Partition(models.Model):
    '''Filesystem equipped with standard directory structure for archive storage'''
    mountpoint = models.CharField(blank=True,max_length=1024, help_text="E.g. /disks/machineN", unique=True)
    host = models.CharField(blank=True,max_length=1024, help_text="Host on which this partition resides")
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
	    s += '<a href="/admin/allocator/fileset/%s">%s</a> ' % (a.pk,a.logical_path)
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
	s = '<a href="/allocator/partition/%s/df">update df</a> ' % (self.pk,)
	return s
    links.allow_tags = True

    def __unicode__(self):
        tb_remaining = (self.capacity_bytes - self.used_bytes) / (1024**4)
        return u'%s (%d %s)' % (self.mountpoint, tb_remaining, 'Tb free')
    __unicode__.allow_tags = True # seem to need this in order to use __unicode__ as one of the fields in list_display in the admin view (see http://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display)


class FileSet(models.Model):
    ''' subtree of archive directory hierarchy.
    Collection of all filesets taken together should exactly represent 
    all files in the archive. Must never span multiple filesystems.'''
    logical_path = models.CharField(max_length=1024, blank=True, default='unallocated', help_text="Initially unallocated, indicating not belonging to FileSetCollection. Then set by save method of FileSetCollectionRelation to hold path within FSCR.")
    overall_final_size = BigIntegerField(help_text="Overall final size in bytes. Estimate from data scientist.") # Additional data still expected (as yet uningested) in bytes
    notes = models.TextField(blank=True)
    partition = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to = {'status': 'Allocating'},help_text="Actual partition where this FileSet is physically stored")
    storage_pot = models.CharField(max_length=1024, blank=True, default='unallocated', help_text="dd")

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
    
class FileSetSizeMeasurement(models.Model):
    '''Date-stampted size measurement of a FileSet'''
    fileset = models.ForeignKey(FileSet, help_text="FileSet that was measured")
    date = models.DateTimeField(default=datetime.now, help_text="Date and time of measurement")
    size = BigIntegerField(help_text="Size in bytes") # in bytes
    no_files = BigIntegerField(null=True, blank=True, help_text="Number of files") 
    def __unicode__(self):
        return u'%s|%s' % (self.date, self.fileset)

