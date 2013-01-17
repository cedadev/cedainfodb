from django.db import models
#from django.contrib.gis.db import models
from datetime import datetime, timedelta
import os, sys
import subprocess
import string
import hashlib
import time
import re
from storageDXMLClient import SpotXMLReader
from fields import * # custom MultiSelectField, MultiSelectFormField from http://djangosnippets.org/snippets/2753/

# needed for volume feed
from django.contrib.syndication.views import Feed

# Needed for BigInteger fix
from django.db.models.fields import IntegerField
from django.conf import settings

from django.contrib.auth.models import *

from django.core.validators import RegexValidator

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
    mountpoints = models.CharField(max_length=512,blank=True, help_text="logical mount points: This is used to generate an auto mount script for the machine e.g. /badc(ro) mounts all filesets on /badc (read only). The default is read-write")
    ftpmountpoints = models.CharField(max_length=512,blank=True, help_text="logical ftp mount points: This is used to make a mount script that has chroot jailed mount points for ftp e.g. /badc(ro) mounts all the disks needed to mount all filesets on /badc (read only)")
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

    def partitions(self):
        return Partition.objects.filter(host = self)

    class Meta:
       ordering = ['hostname']	

class Partition(models.Model):
    '''Filesystem equipped with standard directory structure for archive storage'''
    mountpoint = models.CharField(blank=True,max_length=1024, help_text="E.g. /disks/machineN", unique=True)
    host = models.ForeignKey(Host, blank=True, null=True, help_text="Host on which this partition resides")
    used_bytes = models.BigIntegerField(default=0, help_text="\"Used\" value from df, i.e. no. of bytes used. May be populated by script.")
    capacity_bytes = models.BigIntegerField(default=0, help_text="\"Available\" value from df, i.e. no. of bytes total. May be populated by script.")
    last_checked = models.DateTimeField(null=True, blank=True, help_text="Last time df was run against this partition & size values updated")
    status = models.CharField(max_length=50,       
              choices=(("Blank","Blank"),
                 ("Allocating","Allocating"),
                 ("Allocating_ps","Allocating_ps"),
                 ("Closed","Closed"),
                 ("Migrating","Migrating"),
                 ("Retired","Retired")) )

    def df(self):
        """Report disk usage.
           Return a dictionary with total, used, available. Sizes are reported
           in blocks of 1024 bytes."""
	   
	# skip if retired disk or non-existant   
	if self.status == 'Retired': return None   
	if not os.path.exists(self.mountpoint): return None   
        
	# do df
	output = subprocess.Popen(['/bin/df', '-B 1024', self.mountpoint],
                                 stdout=subprocess.PIPE).communicate()[0]
        lines = output.split('\n')
	if len(lines) == 3: dev, blocks_total, blocks_used, blocks_available, used, mount = lines[1].split()
	if len(lines) == 4: blocks_total, blocks_used, blocks_available, used, mount = lines[2].split()
        self.capacity_bytes = int(blocks_total)*1024
        self.used_bytes = int(blocks_used)*1024
	self.last_checked = datetime.now()
	self.save() 
              

    def exists(self):
        return os.path.ismount(self.mountpoint)  
    exists.boolean = True

    def list_allocated(self):
        # list allocation for admin interface
        s = ''

        allocs = FileSet.objects.filter(partition=self).order_by('-overall_final_size')
        if len(allocs) >0: s += 'Primary File Sets (biggest first): '
	for a in allocs:
	    s += '<a href="/admin/cedainfoapp/fileset/%s">%s</a> ' % (a.pk,a.logical_path)

        allocs = FileSet.objects.filter(secondary_partition=self).order_by('-overall_final_size')
        if len(allocs) >0: s += 'Secondary File Sets (biggest first): '
	for a in allocs:
	    s += '<a href="/admin/cedainfoapp/fileset/%s">%s</a> ' % (a.pk,a.logical_path)
	return s
    list_allocated.allow_tags = True
	
    def meter(self):
        # graphic meter for partition
        if self.capacity_bytes == 0: return "No capacity set"
        used = self.used_bytes
	current_allocated = self.allocated()
	current_secondary_allocated = self.secondary_allocated()
        alloc = current_allocated*100/self.capacity_bytes
        # Find the set of most recent FileSetSizeMeasurements for FileSets on this Partition
        filesetsum = self.used_by_filesets()
        secondaryfilesetsum = self.secondary_used_by_filesets()
        # Turn this into a percentage of capacity
        fssumpercent = filesetsum*100/self.capacity_bytes
	#work out units for capacity for axis (full axis is 110%)
	if self.capacity_bytes < 1000: unit="B"; scale= 1.0 
	elif  self.capacity_bytes < 1000000: unit="kB"; scale =  0.001
	elif  self.capacity_bytes < 1000000000: unit="MB";  scale =  0.000001
	elif  self.capacity_bytes < 1000000000000: unit="GB"; scale= 0.000000001
	elif  self.capacity_bytes < 1000000000000000: unit="TB";  scale = 0.000000000001
	else: unit="PB"; scale = 0.000000000000001
	googlechart = 'http://chart.googleapis.com/chart?cht=bhs&chco=0000ff|9999ff,00ff00|99ff99|aa1fff,ff0000,ffcccc&chs=300x80&chbh=16&chxt=y,x&chxl=0:|Allocated|Used&chma=5,10,5,5&chxtc=1,-100&chxs=1,,8|0,,9'
	googlechart += '&chd=t:%s,%s|%s,%s|%s,0|%s,0' % (filesetsum*scale, current_allocated*scale, secondaryfilesetsum*scale, current_secondary_allocated*scale, (used-filesetsum-secondaryfilesetsum)*scale,  (self.capacity_bytes-used)*scale)
	googlechart += '&chxr=1,0,%s&chds=0,%s' % (1.2*self.capacity_bytes*scale, 1.2*self.capacity_bytes*scale) # add data and axis range
        s = '<img src="%s">' % (googlechart,)
	return s
    meter.allow_tags = True

    def allocated(self):
        # find total allocated space
	total = 0
        allocs = FileSet.objects.filter(partition=self)
	for a in allocs: total += a.overall_final_size
	return total

    def secondary_allocated(self):
        # find total allocated space to secondary copies
	total = 0
        allocs = FileSet.objects.filter(secondary_partition=self)
	for a in allocs: total += a.overall_final_size
	return total
    
    def used_by_filesets(self):
        # find total allocated space used
        total = 0
        filesets = FileSet.objects.filter(partition=self)
        # for each fileset, find most recent FileSetSizeMeasurement
        for fs in filesets:
            fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')
	    if len(fssms) > 0: total += fssms[0].size 
        return total

    def secondary_used_by_filesets(self):
        # find total allocated space used by secondary copies
        total = 0
        filesets = FileSet.objects.filter(secondary_partition=self)
        # for each fileset, find most recent FileSetSizeMeasurement
        # NOTE: this is primary fileset measurement assumes copies are the same size
        for fs in filesets:
            fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')
	    if len(fssms) > 0: total += fssms[0].size 
        return total

    def use_summary(self):
        # find use info for total allocated space, etc,
	use = {'prime_alloc_used':0, 'second_alloc_used':0, 'unalloc_used':0, 'empty':0, 'prime_alloc': 0, 'second_alloc': 0, 'unallocated':0}
        prime_allocs = FileSet.objects.filter(partition=self)
        second_allocs = FileSet.objects.filter(secondary_partition=self)
	for a in prime_allocs: 
            use['prime_alloc'] += a.overall_final_size
            last_size = a.last_size()
            if last_size != None: use['prime_alloc_used'] += a.last_size().size
	for a in second_allocs: 
            use['second_alloc'] += a.overall_final_size
            last_size = a.last_size()
            if last_size != None: use['second_alloc_used'] += a.last_size().size
        use['unallocated'] = self.capacity_bytes - use['prime_alloc'] - use['second_alloc']
        use['unalloc_used'] = self.used_bytes - use['prime_alloc_used'] - use['second_alloc_used']
        use['empty'] = self.capacity_bytes - self.used_bytes
	return use



            
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
    tool = models.CharField(max_length=45, help_text="e.g. DMF /  / tape")
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
    logical_path = models.CharField(max_length=1024, blank=True, default='/badc/NNNN', help_text="e.g. /badc/acsoe", unique=True)
    overall_final_size = models.BigIntegerField(help_text="The allocation given to a fileset is an estimate of the final size on disk. If the dataset is going to grow indefinitely then estimate the size for 4 years ahead. Filesets can't be bigger than a single partition, but in order to aid disk managment they should no exceed 20% of the size of a partition.") # Additional data still expected (as yet uningested) in bytes
    notes = models.TextField(blank=True)
    partition = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to = {'status': 'Allocating'},help_text="Actual partition where this FileSet is physically stored")
    storage_pot_type = models.CharField(max_length=64, blank=True, default='archive', 
            help_text="The 'type' directory under which the data is held. This is archive for archive data and project_space for project space etc. DO NOT CHANGE AFTER SPOT CREATION", 
	    choices=(("archive","archive"),
                 ("project_spaces","project_spaces"),
                 ("group_workspace","group_workspace")) )
    storage_pot = models.CharField(max_length=1024, blank=True, default='', help_text="The directory under which the data is held")
    migrate_to = models.ForeignKey(Partition, blank=True, null=True,help_text="Target partition for migration", related_name='fileset_migrate_to_partition')
    secondary_partition = models.ForeignKey(Partition, blank=True, null=True, help_text="Target for secondary disk copy", related_name='fileset_secondary_partition')
    dmf_backup = models.BooleanField(default=False, help_text="Backup to DMF")
    sd_backup = models.BooleanField(default=False, help_text="Backup to Storage-D")
    complete = models.BooleanField(default=False, help_text="Is the fileset complete. If this is set then we are not anticipating the files to change, be deleted or added to.")
    complete_date = models.DateField(null=True, blank=True, help_text="Date when fileset was set to complete.")
    
    def __unicode__(self):
        return u'%s' % (self.logical_path,)
    # TODO custom save method (for when assigning a partition) : check that FileSet size

    def storage_path(self):
        return os.path.normpath(self.partition.mountpoint+'/'+self.storage_pot_type+'/'+self.storage_pot) 

    def secondary_storage_path(self):
        if self.secondary_partition: 
	    return os.path.normpath(self.secondary_partition.mountpoint+'/backup/'+self.storage_pot_type+'/'+self.storage_pot)
	else:
	    return None 

    def migrate_path(self):
        return os.path.normpath(self.migrate_to.mountpoint+'/'+self.storage_pot_type+'/'+self.storage_pot) 

    def make_spot(self):
        # create a storage pot and link
	if self.storage_pot_type == '': return # need a spot type 
        if self.storage_pot != '': return  #can't make a spot if it already exists in the db
        if self.logical_path_exists(): return #can't make a spot if logical path exists  
        if not self.partition: return #can't make a spot if no partition 

        #spot tail
        head, spottail = os.path.split(self.logical_path)
        if spottail == '': head, spottail = os.path.split(head)

        # icreate spot name 
        spotname = "spot-%s-%s" % (self.pk, spottail)

        self.storage_pot = spotname
        try:
            os.makedirs(self.storage_path())
        except:
            return ("os.makedirs(%s)" % self.storage_path(), sys.exc_value )
        try:
	    os.symlink(self.storage_path(), self.logical_path)
        except: 
            # remove spot dir that was make correctly, but is inconsistant because link not made
            os.rmdir(self.storage_path())
            return ("os.symlink(%s, %s) \n (removed spot dir for consistancy)" % (self.storage_path(),self.logical_path),sys.exc_value )
        self.save()

    def migrate_spot(self, do_audit=True):
        if self.storage_pot == '': raise "can't migrate a spot does not already exists in the db"
        if not self.partition: raise "can't migrate a spot if no partition"
        if not self.migrate_to: raise "can't migrate a spot if no migration partition" 
	if not os.path.islink(self.logical_path): raise "can't migrate a spot if logical path is not a link"
       
        # copy - exceptions raised if fail
	self._migration_copy()
		
	# delete link and remake link to new partition
	if os.readlink(self.logical_path) != self.migrate_path(): #may be tring again after failing
	    os.unlink(self.logical_path)
	    os.symlink(self.migrate_path(), self.logical_path)

	# copy again - exceptions raised if fail
	self._migration_copy()
		
	
	# verify and log - exceptions raised if fail
	if do_audit:
	    audit=Audit(fileset=self)
	    audit.start()   
	    audit.verify_copy()

	    # mark for deletion - write a file in the spot directory 
	    # showing the migration is complete with regard to the CEDA info tool  
            DOC = open(os.path.join(self.storage_path(),'MIGRATED.txt'), 'w')
	    DOC.write("""This storage directory has been migrated and can be deleted.
	
	            Migrated %s -> %s (%s)
	            Storage pot: %s/%s
	            Logical path: %s""" % (self.partition, self.migrate_to, 
		                           datetime.utcnow(), self.storage_pot_type, 
					   self.storage_pot, self.logical_path))

	# upgade fs with new partition info on success
	self.notes += '\nMigrated %s -> %s (%s) [do_audit=%s]' % (self.partition, 
	                             self.migrate_to, datetime.utcnow(), do_audit)
	self.partition = self.migrate_to
 	self.migrate_to = None
        self.save()
	
	
    def _migration_copy(self):	
        # copy - exception  copy is ok
	rsynccmd = 'rsync -av %s/ %s' % (self.storage_path(),self.migrate_path())
	print ">>> %s" %rsynccmd      
        subprocess.check_call(rsynccmd.split())

    def secondary_copy_command(self):	
        '''make an rsync command to create a secondary copy'''
	if not self.secondary_partition: return ''
        host = self.partition.host.hostname
	frompath = self.storage_path()
	topath = "badc@%s:%s" % (self.secondary_partition.host.hostname,self.secondary_storage_path())
	rsynccmd = 'ssh %s rsync -Puva --delete %s %s' % (host, frompath, topath)
	return rsynccmd


    def spot_display(self):
        if self.storage_pot: return "%s" % self.storage_pot
        else: return '<a href="/fileset/%s/makespot">Create Storage</a>' % self.pk
    spot_display.allow_tags = True
    spot_display.short_description = 'Storage pot'

    def spot_exists(self):
        if self.storage_pot == '':
            return False
        return os.path.exists(self.storage_path())    
    spot_exists.boolean = True

    def logical_path_exists(self):
        return os.path.exists(self.logical_path)
    logical_path_exists.boolean = True

    def logical_path_right(self):
        if not os.path.exists(self.logical_path): return False
	if not os.path.islink(self.logical_path): 
	    return False
	else:
	    linkpath = os.readlink(self.logical_path)
	    if linkpath == self.storage_path(): return True
	    else: return False

    def status(self):
        "return text showing fileset status"
        if not self.partition:
	    if self.migrate_to or self.storage_pot: return '<font color="#ff0000">Migrate to/Storage pot are set before partition?</font>'
            elif not self.logical_path_exists(): return '<font color="#bbbb00">New</font>'
	    elif os.path.islink(self.logical_path):
                linkpath = os.readlink(self.logical_path)
	        if linkpath[0:7] == '/disks/': return '<font color="#bbbb00">New (Can allocate from existing link)</font>'
	    else: return '<font color="#ff0000">Logical path exists</font>'
		
        else:
	    if not self.storage_pot and not self.logical_path_exists(): return '<font color="#bbbb00">Ready for storage creation</font>'
	    elif self.logical_path_right():
	        if self.migrate_to: return '<font color="#bbbb00">File set marked for migration</font>'
                else: return '<font color="#00bb00">Normal</font>'
	    else: return '<font color="#ff0000">Link error</font>'
    status.allow_tags = True

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
		linkbits = linkpath.split('/')
		if len(linkbits) != 5: raise "Not able to split %s into /disks/partition/spot_type/spotname" % linkpath
		junk, disks, partition, spottype, spotname = linkbits 
		mountpoint = '/disks/%s' % partition
		self.partition = Partition.objects.get(mountpoint=mountpoint)
	        self.storage_pot = spotname
		self.notes += 'allocated from pre-existing links to /disks/'
		self.save()
		return		 
		    
        else:
            if self.storage_pot_type == 'project_spaces': partitions = Partition.objects.filter(status='Allocating_ps')
            else: partitions = Partition.objects.filter(status='Allocating')
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
	    self.notes += '\nAllocated partition %s (%s)' % (self.partition, datetime.utcnow())
            self.save()
            
    def backup_summary(self):
        # get a text summary of storaged backup status
        reader = SpotXMLReader(self.storage_pot)
        return reader.getSpotSummary()
    backup_summary.short_description = 'backup'
    backup_summary.allow_tags = True

# migration allocation don by hand at the moment

    #def allocate_m(self):
    #    # find partion for migration
    #    if self.storage_pot == '': return  #can't migrate a spot does not already exists in the db
    #    if not self.partition: return #can't migrate a spot if no partition 
    #    if self.migrate_to: return #already got a migration partition 

#	partitions = Partition.objects.filter(status='Allocating')
#        # find the fullest partition which can accomidate the file set
#	allocated_partition = None
#	fullest_space = 10e40
#	for p in partitions:
#	    partition_free_space = 0.95 * p.capacity_bytes - p.allocated()
#            # if this partition could accommidate file set...
#	    if partition_free_space > self.overall_final_size:
#		# ... and its the fullest so far  
#		if partition_free_space < fullest_space:
#		    allocated_partition = p
#		    fullest_space = partition_free_space
#		
#        self.migrate_to = allocated_partition
#	self.notes += '\nAllocated migration partition %s (%s)' % (self.migrate_to, datetime.now())
#        self.save()
    
    def du(self):
        '''Report disk usage of FileSet by creating as FileSetSizeMeasurement.'''
        if self.spot_exists():
            # find volume using du
            output = subprocess.Popen(['/usr/bin/du', '-sk', '--apparent', self.storage_path()],stdout=subprocess.PIPE).communicate()[0]
            lines = output.split('\n')
            if len(lines) == 2: size, path = lines[0].split()

            # find number of files
            p1 = Popen(["find", self.storage_path(), "-type", "f"], stdout=PIPE)
            p2 = Popen(["wc", "-l"], stdin=p1.stdout, stdout=PIPE)
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            nfiles = p2.communicate()[0]

            fssm = FileSetSizeMeasurement(fileset=self, date=datetime.now(), size=int(size)*1024, no_files=int(nfiles))
            fssm.save() 
        return      

    def dataentity(self):
	des = DataEntity.objects.order_by("-logical_path")
	for de in des:
            if de.logical_path == '': return None #skip if getting to DE with no logical path set
	    if de.logical_path == self.logical_path[0:len(de.logical_path)]:
	        return de
	return None	

    def responsible(self):
	des = DataEntity.objects.order_by("-logical_path")
	for de in des:
            if de.logical_path == '': return None #skip if getting to DE with no logical path set
	    if de.logical_path == self.logical_path[0:len(de.logical_path)]:
	        return de.responsible_officer
	return None	

    def links(self):
        # links to actions for filesets
        s = '<a href="/fileset/%s/du">du</a> <a href="http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_Summary.php?%s">storageD</a>' % (self.pk,self.storage_pot)
        return s
    links.allow_tags = True
    
    def last_size(self):
        # display most recent FileSetSizeMeasurement
        try:
            fssm = FileSetSizeMeasurement.objects.filter(fileset=self).order_by('-date')[0]
            return fssm
        except:
            return None
    last_size.allow_tags = True

    def last_audit(self, state='finished'):
        # display most recent audit
        try:
            audit = Audit.objects.filter(fileset=self, auditstate=state).order_by('-starttime')[0]
            return audit
        except:
            return None
    last_size.allow_tags = True
        

class VolFeed(Feed):
    # RSS feed to be used by the CEDA site.
    title = "CEDA data volume summary"
    link = "/latest/volumes"
    description = "Lastest volume summary for CEDA data."

    def items(self): return [1]

    def item_title(self, item): return "Volume summary"

    def item_description(self, item):
         
        d= ''
        table = {}
        filesets = FileSet.objects.all().order_by('logical_path')
    
        toplevel = ''
        vol, nfiles = 0,0
        for f in filesets:
            slashcount = f.logical_path.count('/')
            if slashcount == 4: 
                table[toplevel] = (vol,nfiles)
                vol, nfiles = 0,0
                toplevel = f.logical_path

            size  = f.last_size()
            if size: 
                vol=vol+size.size
                nfiles = nfiles+size.no_files   
        lines = table.items()

        d += "Top 10 largest datasets\n"
        lines.sort( key=lambda a:a[1][0], reverse=True )
        i=0
        for topfs, size in lines:
            d += "%s | %2.2f TB | %s\n" % (topfs, size[0]/1.0e12, size[1])
            i+=1
            if i >9: break

        d += "\nTop 10 datasets with most files\n"
        lines.sort( key=lambda a:a[1][1], reverse=True )
        i=0
        for topfs, size in lines:
            d += "%s | %2.2f TB | %s\n" % (topfs, size[0]/1.0e12, size[1])
            i+=1
            if i >9: break

        return d


    def item_link(self, item): 
        return "link"
        
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

    friendly_name.alphabetic_filter = True
    
    
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

    def summary(self):
       '''Returns a summary string extracted from the start of the full description text'''
           
       SummaryLength = 60
       summary = self.description.strip()
       summary = ' '.join(summary.split())
       
       if len(summary) > SummaryLength:
          summary = summary[0:SummaryLength-1] + '...'
    
       return summary

    def documentationLink (self):
    
       return self.documentation
       	  	       
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
    size = models.BigIntegerField(help_text="Size in bytes") # in bytes
    no_files = models.BigIntegerField(null=True, blank=True, help_text="Number of files") 
    def __unicode__(self):
        if self.size > 2000000000000: size =self.size/(1024*1024*1024*1024); unit = "TB"
        if self.size > 2000000000: size =self.size/(1024*1024*1024); unit = "GB"
        if self.size > 2000000: size =self.size/(1024*1024); unit = "MB"
        elif self.size > 2000:    size =self.size/(1024); unit = "kB"
	else:                     size = self.size; unit= "B"

        if self.no_files > 2000000: no_files =self.no_files/(1000*1000); funit = "Mfiles"
	else:                     no_files = self.no_files; funit= "files"
	
        return u'%s %s; %s %s (%s)' % (size, unit, no_files, funit, self.date.strftime("%Y-%m-%d %H:%M"))


class Audit(models.Model):
    '''A record of inspecting a fileset'''
    fileset = models.ForeignKey(FileSet, help_text="FileSet which this audit related to at time of creation", on_delete=models.SET_NULL, null=True, blank=True)
    starttime = models.DateTimeField(null=True, blank=True, )
    endtime = models.DateTimeField(null=True, blank=True, )
    auditstate = models.CharField(max_length=50,       
        choices=(
            ("not started","not started"),
            ("started","started"),
            ("finished","finished"),
            ("copy verified","copy verified"),
            ("analysed","analysed"),
            ("error","error"),
        ),
        default="not started",
        help_text="state of this audit"
    )
    corrupted_files = models.IntegerField(default=0)
    new_files = models.IntegerField(default=0)
    deleted_files = models.IntegerField(default=0)
    modified_files = models.IntegerField(default=0)
    unchanges_files = models.IntegerField(default=0)
    logfile = models.CharField(max_length=255, default='')
           
    def __unicode__(self):
        return 'Audit of %s started %s  [[%s]]' % (self.fileset, self.starttime, self.auditstate)
        
    def start(self):
        
	# find the last finished audit of this fileset for comparison
        prev_audit = self.fileset.last_audit('analysed') 

	print "**** %s" % prev_audit    
	    
 	self.starttime = datetime.now()
	self.auditstate = 'started'
	self.save()
	try: 
	    self.checkm_log()
	except:
	    self.endtime = datetime.now()
	    self.auditstate = 'error'
	    self.save()
	    raise "Error when creating checkm log" 
	    
	self.endtime = datetime.now()
	self.auditstate = 'finished'
	self.save()
	
	if prev_audit: 
	    result = self.compare(prev_audit)
	    print result
	    self.corrupted_files = len(result['corrupt'])
	    self.modified_files = result['modified']
	    self.new_files = result['new']
	    self.deleted_files = result['deleted']
	    self.unchanges_files = result['unchanged']

	self.auditstate = 'analysed'
	self.save()
	       
    def compare(self, prev_audit):
        # open current and previous log files
	CLOG = open(self.logfile)
	PLOG = open(prev_audit.logfile)
	
	# read top lines from the checkm files
	cline = CLOG.readline()
	pline = PLOG.readline()
	# Flags to indicate end of file
	cend = False
	pend = False
	# lists for tallies 
	corrupt = []
	modified = 0
	new = 0
	deleted = 0
	unchanged = 0
	
	while 1:
	    # The lists are sorted so we go down the two lists together. 
	    # If we find a name on the current list that was not on the last list this is a new file.
	    # If we find a name on the last list that was not on the current list this is a deleeted file.
	    # If the names are the same then we need to look for changes.
	    
	    if cline == '': cend = True
	    if pline == '': pend = True
	                
	    # stop if end of both files
	    if pend and cend: break           
	    
	    # ignore lines with # at the start
	    if not cend and cline[0] =='#': 
	        cline = CLOG.readline()
		continue
	    if not pend and pline[0] =='#': 
	        pline = PLOG.readline()
		continue
	    
	    # if the lines are the same move both logs on 
	    if cline == pline: 
	        unchanged = unchanged + 1
	        cline = CLOG.readline()
	        pline = PLOG.readline()
		continue

            # if current log ended then files have been deleted
	    if cend: 
	        deleted = deleted + 1
	        pline = PLOG.readline()
		continue

            # if previous log ended then files have been added
	    if pend: 
	        new = new + 1
	        cline = CLOG.readline()
		continue
		
	    # split the lines into components. (At this point we know both lines exist)
	    (cfilename, calgorithm, cdigest, csize, cmodtime) = cline.split('|')  	
	    (pfilename, palgorithm, pdigest, psize, pmodtime) = pline.split('|')  	

            # if current file is differnt and less than the previous one then
	    # a new file has been added
	    if cfilename < pfilename: 
	        new = new + 1
	        cline = CLOG.readline()
		continue

            # if current file is differnt and greater than the previous one 
	    # then a file has been deleted. 
	    if cfilename > pfilename: 
	        deleted = deleted + 1
	        pline = PLOG.readline()
		continue

            # at this point we know the log lines are for the same file, but are different in some 
	    # other way
	    
	    # if the modified time has changed then the file has been modified
	    if cmodtime != pmodtime: 
	        modified = modified + 1
	        cline = CLOG.readline()
	        pline = PLOG.readline()
		continue

	    # if content has changed this is corrupt
	    if cdigest != pdigest: 
	        corrupt.append(cline)
	        cline = CLOG.readline()
	        pline = PLOG.readline()
		continue
	        
	return {'corrupt':corrupt, 'modified':modified, 'new':new, 'deleted':deleted, 'unchanged':unchanged}
            		
	
	
    def checkm_log(self):
        print "Writing checkm log for this audit..."
	fileset = self.fileset
	if fileset == None: raise "Can't make log for audit with no fileset"
        # make checkm directory for spot is missing
        if not os.path.exists('%s/%s' %(settings.CHECKM_DIR, fileset.storage_pot)): 
	    os.mkdir('%s/%s' %(settings.CHECKM_DIR, fileset.storage_pot))
	self.logfile ='%s/%s/checkm.%s.%s.log' % (settings.CHECKM_DIR, fileset.storage_pot,
	            fileset.storage_pot, time.strftime('%Y%m%d-%H%M'))     
        LOG = open(self.logfile, 'w')
	LOG.write('#%checkm_0.7\n')
	LOG.write('# manifest file for %s\n' % fileset.logical_path)
	LOG.write('# scaning path %s\n' % fileset.storage_path())
	LOG.write('# generated %s\n' % datetime.utcnow())
	LOG.write('# audit ID: %s\n' % self.id)
	LOG.write('# \n')
	LOG.write('# Filename|Algorithm|Digest|Length | ModTime\n')
        self._checkm_log(fileset.storage_path(), fileset.storage_path(), LOG)
	LOG.close()
        print "      ... Done"
	
    def _checkm_log(self, directory, storage_path, LOG):
	# recursive function to make checkm log file
        reldir = directory[len(storage_path)+1:]
        names = os.listdir(directory)
        # look for diectories and recurse
	names.sort()
	for n in names:
            path = os.path.join(directory,n)    
            if os.path.isdir(path) and not os.path.islink(path):
                self._checkm_log(path, storage_path, LOG)
        # for each file 
        for n in names:
            path = os.path.join(directory,n)     
            relpath = os.path.join(reldir,n)                     
            # if path is reg file
            if os.path.isfile(path): 
	        size = os.path.getsize(path)
		mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%dT%H:%M:%SZ')
                F=open(path)
                m=hashlib.md5()
                while 1:
                    buf= F.read(1024*1024)
                    m.update(buf)
                    if buf=="": break
                LOG.write("%s|md5|%s|%s|%s\n" % (relpath,m.hexdigest(),size,mtime))

    def verify_copy(self):	
        # verify that a migrated copy has the same files as this audit.
	# Added files are OK. 
        print "Verifying checkm log against migrated files ..."
        LOG = open(self.logfile)
	while 1:
	    line = LOG.readline()
	    if line == '': break
	    if line[0] == '#': continue
	    relpath,alg,checksum,size,modtime = line.split('|')
	    checksum = checksum.strip()
	    newpath = os.path.join(self.fileset.migrate_path(), relpath)
            if not os.path.exists(newpath): raise "File not there %s" % newpath
            if not os.path.isfile(newpath): raise "Not regular file %s" % newpath
	     
            F=open(newpath)
            m=hashlib.md5()
            while 1:
                buf= F.read(1024*1024)
                m.update(buf)
                if buf=="": break
	    if m.hexdigest() != checksum: raise "checksums do not match %s" % newpath
	self.auditstate = 'copy verified'
	self.save()
        print "      ... Done"
	
    
#class SpatioTemp(models.Model):
#    '''spatiotemporal coverage of a file'''
#    file = models.ForeignKey(File)
#    geom = models.GeometryField(null=True, blank=True)
#    start_time = models.DateTimeField(null=True, blank=True)
#    end_time = models.DateTimeField(null=True, blank=True)
#    vert_extent_lower = models.IntegerField(null=True, blank=True)
#    vert_extend_upper = models.IntegerField(null=True, blank=True)
#    objects = models.GeoManager()
#    def __unicode__(self):
#        return 'spatiotemp for file %s' % self.file

class GWSRequest(models.Model):
    '''Request for a Group Workspace
       Captures all information about requirements for GWS and if converted is copied to a GWS instance (new or updated)'''
    class Meta:
        verbose_name_plural = 'group workspace requests'
    
    gws_name = models.CharField(
        # name doesn't need to be unique here : there might be several requests but it's the one that's approved that gets copied.
        max_length=16,
        validators=[
            RegexValidator( 
                regex=settings.GWS_NAME_REGEX,
                message=u"Invalid name : this string will be used as a unix group name so must match the pattern %s" % settings.GWS_NAME_REGEX.pattern,
                )
            ]
        , help_text='short string to be used as name for group workspace, also used for corresponsing unix group name. Must match pattern %s' % settings.GWS_NAME_REGEX.pattern
        )
    path = models.CharField(max_length=2048, help_text='storage path to this group workspace excluding GWS name', default='/group_workspaces/jasmin_or_cems/')
    internal_requester = models.ForeignKey(User, help_text='CEDA person sponsoring the request')
    gws_manager = models.CharField(max_length=1024, help_text='External person who will manage the GWS during its lifetime')
    description = models.TextField(null=True, blank=True, help_text='Text description of proposed GWS')
    requested_volume = models.BigIntegerField(help_text="In bytes, but can be enetered using integer<space>suffix e.g. '200 Tb'")
    backup_requirement = models.CharField(max_length=127, choices=settings.GWS_BACKUP_CHOICES, default='no backup')
    related_url = models.URLField(verify_exists=False, blank=True, help_text='Link to further info relevant to this GWS')
    expiry_date = models.DateField(default = datetime.now()+timedelta(days=2*365), help_text="date after which GWS will be deleted") # approx 2 years from now
    request_type = models.CharField(max_length=127, choices=settings.GWS_REQUEST_TYPE_CHOICES, default='new', help_text='type of request')
    request_status = models.CharField(max_length=127, choices=settings.GWS_REQUEST_STATUS_CHOICES, default='pending', help_text='status of this request')
    gws = models.ForeignKey('GWS', blank=True, null=True, on_delete=models.SET_NULL, help_text='GWS to which this request pertains')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')
    
    def __unicode__(self):
        return u'%s' % self.gws_name
        
    # Actions : 
    # reject
    #   - following CEDA review, reject a request (can later be deleted)
    # approve
    #   - following CEDA review, approve a request (puts it into list for SCD to see)
    # convert
    #   - make a GWS out of a GWSRequest (new)
    #   - update an existing GWS out of a GWSRequest (update)
    
    def reject(self):
        '''Review process : reject a request'''
        if self.request_status == 'ceda pending':
            self.request_status = 'ceda rejected'
            # disassociate it from any gws
            self.gws = None
            self.save()
            
        else:
            raise Exception("Can't reject a request unless status = 'ceda pending'")
            
    def approve(self):
        '''Review process : approve a request'''
        if self.request_status == 'ceda pending':
            self.request_status = 'ceda approved'
            # disassociate it from any gws
            self.save()
        else:
            raise Exception("Can't approve a request unless status = 'ceda pending'")        

    def convert(self):
        '''Set the status to under construction. If no associated GWS, make one and associate this request with it. Else update an existing GWS. In both cases, copy existing fields to overwrite attributes of GWS.'''
        
        # Approving a new request (first time)
        if self.request_type == 'new' and (self.gws is None or self.gws == ''):
            # make a new gws object, copying attributes from request           
            gws = GWS.objects.create(
                name = self.gws_name,
                path = self.path,
                status = 'active',
                internal_requester = self.internal_requester,
                gws_manager = self.gws_manager,
                description = self.description,
                requested_volume = self.requested_volume,
                backup_requirement = self.backup_requirement,
                related_url = self.related_url,
                expiry_date = self.expiry_date,
            )
            self.gws = gws
            # update the request status
            self.request_status = 'completed'
            self.save()        

        elif self.request_type == 'update':
            if self.gws is None or self.gws == '':
                raise Exception("Can't do update request : no GWS associated")
            else:
                gws = self.gws
                # update the existing associated gws
                #self.gws.name = self.gws_name #DISABLED : presumably this never needs to change, once created.
                gws.path = self.path
                #gws.status = 'approved' #DISABLED : don't need to update this
                gws.internal_requester = self.internal_requester
                gws.gws_manager = self.gws_manager
                gws.description = self.description
                gws.requested_volume = self.requested_volume
                gws.backup_requirement = self.backup_requirement
                gws.related_url = self.related_url
                gws.expiry_date = self.expiry_date
                gws.status = 'active'
                gws.forceSave()
                self.gws = gws
                # update the request status
                self.request_status = 'completed'
                self.save()
                
        elif self.request_type == 'remove':
            if self.gws is None or self.gws == '':
                raise Exception("Can't do remove request : no GWS associated")
            else:
                self.gws.delete()
                self.delete()
        else:
            raise Exception("Must set request status to update if updating an existing GWS")

            
    def action_links(self):
        if self.request_status == 'ceda pending':
            return u'<a href="/gwsrequest/%i/approve">approve</a> <a href="/gwsrequest/%i/reject">reject</a>' % (self.id, self.id)
        elif self.request_status == 'ceda approved':
            return u'<a href="/gwsrequest/%i/convert">convert</a>' % self.id
        else:
            return u'n/a'
    action_links.allow_tags = True
    action_links.short_description = 'actions'
    
    def gws_link(self):
        return u'<a href="/admin/cedainfoapp/gws/%i">%s%s</a>' % (self.gws.id, self.gws.path, self.gws.name)
    gws_link.allow_tags = True
    gws_link.short_description = 'GWS'
    

class GWS(models.Model):

    class Meta:
        verbose_name_plural = 'group workspaces'
     
    name = name = models.CharField(
        max_length=16,
        unique=True,
        validators=[
            RegexValidator( 
                regex=settings.GWS_NAME_REGEX,
                message=u"Invalid name : this string will be used as a unix group name so must match the pattern %s" % settings.GWS_NAME_REGEX.pattern,
                )
            ]
        , help_text='short string to be used as name for group workspace, also used for corresponsing unix group name. Must match pattern %s' % settings.GWS_NAME_REGEX.pattern
        )

    # Fields populated from GWS request
    path = models.CharField(max_length=2048, help_text='storage path to this group workspace excluding GWS name')
    internal_requester = models.ForeignKey(User, help_text='CEDA person sponsoring the GWS')
    gws_manager = models.CharField(max_length=1024, help_text='External person who will manage the GWS during its lifetime')
    description = models.TextField(null=True, blank=True, help_text='Text description of GWS')
    requested_volume = models.BigIntegerField(help_text="In bytes, but can be enetered using integer<space>suffix e.g. '200 Tb'")
    backup_requirement = models.CharField(max_length=127, choices=settings.GWS_BACKUP_CHOICES, default='no backup')
    related_url = models.URLField(verify_exists=False, blank=True, help_text='Link to further info relevant to this GWS')
    expiry_date = models.DateField(help_text='Date after which GWS will be deleted')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')
    
    # Fields specific to GWS
    last_reviewed = models.DateTimeField(null=True, blank=True, help_text='date of last review')
    review_notes = models.TextField(blank=True, help_text='notes from reviews (append)')
    status = models.CharField(max_length=127, choices=settings.GWS_STATUS_CHOICES, default='active', help_text='status of GWS')

    
    def get_current_gwsrequest(self):
        '''Find the most recent GWSRequest which has this GWS as FK'''
        try:
            gws =  GWSRequest.objects.filter(gws=self, request_status='approved').order_by('-timestamp')[0]
            return gws
        except:
            return None
            
    def volume(self):
        if self.get_current_gwsrequest():
            return self.get_current_gwsrequest().requested_volume
        else:
            return None
    
    def __unicode__(self):
        if self.path:
            path = self.path
        else:
            path = ''
        return u'%s(%s)' % (self.name, path)
        
    def create_update_request(self):
        '''Create a new gwsrequest based on this gws pre-populated with values ready for editing & approval'''
        req = GWSRequest.objects.create(
            gws_name = self.name,
            path = self.path,
            internal_requester = self.internal_requester, 
            gws_manager = self.gws_manager,
            description = self.description,
            requested_volume = self.requested_volume,
            backup_requirement = self.backup_requirement,
            related_url = self.related_url,
            expiry_date = self.expiry_date,
            request_type = 'update',
            request_status = 'pending',
            gws = self,
        )
        return req.id

		
    def update_link(self):
		return u'<a href="/gws/%i/update">update</a>' % self.id
    update_link.allow_tags = True

    def save(self, *args, **kwargs):
        # Custom save method : will only save an instance if there is no PK, i.e. if the model is a new instance
        # Logic : If you want to change a request, you can't, you need to make a new one & have that approved.
        if self.pk is None:
            super(GWS, self).save(*args, **kwargs)
        else:
            raise Exception("Unable to save changes to existing GWS : create an update request & get it approved")
            
    def forceSave(self, *args, **kwargs):
        # OK, sometimes we need to update individual fields (e.g. "approved")"
        super(GWS, self).save(*args, **kwargs)  
   
class VMRequest(models.Model):
    vm_name = models.CharField(max_length=127, help_text="proposed fully-qualified host name") # TODO : need regex
    type = models.CharField(max_length=16, choices=settings.VM_TYPE_CHOICES, help_text="Type of VM, see REF") # TODO update REF
    operation_type = models.CharField(max_length=127, choices=settings.VM_OP_TYPE_CHOICES, help_text="Operation type of VM (dev, test, production, ...)")
    internal_requester = models.ForeignKey(User, help_text="CEDA person sponsoring the request", related_name='vmrequest_internal_requester_user')
    description = models.TextField(help_text="")
    date_required = models.DateField()
    cpu_required = models.CharField(max_length=127, choices=settings.VM_CPU_REQUIRED_CHOICES)
    memory_required = models.CharField(max_length=127, choices=settings.VM_MEM_REQUIRED_CHOICES)
    disk_space_required = models.CharField(max_length=127, choices=settings.VM_DISK_SPACE_REQUIRED_CHOICES)
    disk_activity_required = models.CharField(max_length=127, choices=settings.VM_DISK_ACTIVITY_REQUIRED_CHOICES)
    mountpoints_required = MultiSelectField(max_length=2048, choices=settings.MOUNT_CHOICES)
    network_required = models.CharField(max_length=127, choices=settings.VM_NETWORK_ACTIVITY_REQUIRED_CHOICES)
    os_required = models.CharField(max_length=127, choices=settings.VM_OS_REQUIRED_CHOICES, default='rhel6')
    other_info = models.TextField(blank=True)
    patch_responsible = models.ForeignKey(User, related_name='vmrequest_patch_responsible_user',
        limit_choices_to = {'id__in': settings.ADMIN_USERS_PATCH_RESPONSIBLE},
    )
    root_users = models.ManyToManyField(User, related_name='vmrequest_root_users_user')
    request_type = models.CharField(max_length=127, choices=settings.VM_REQUEST_TYPE_CHOICES, default='new')
    request_status = models.CharField(max_length=127, choices=settings.VM_REQUEST_STATUS_CHOICES, default='pending')
    vm = models.ForeignKey('VM', blank=True, null=True, on_delete=models.SET_NULL, help_text='VM to which this request pertains')
    end_of_life = models.DateField(default = datetime.now()+timedelta(days=3*365)) # approx 3 years from now
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')
    
    def __unicode__(self):
        return u'%s' % self.vm_name
        
    def action_links(self):
        if self.request_status == 'ceda pending':
            return u'<a href="/vmrequest/%i/approve">approve</a> <a href="/vmrequest/%i/reject">reject</a>' % (self.id, self.id)
        elif self.request_status == 'ceda approved':
            return u'<a href="/vmrequest/%i/convert">convert</a>' % self.id
        else:
            return u'n/a'
    action_links.allow_tags = True
    action_links.short_description = 'actions'
    
    def reject(self):
        '''Review process : reject a request'''
        if self.request_status == 'ceda pending':
            self.request_status = 'ceda rejected'
            # disassociate it from any gws
            self.vm = None
            self.save()
            
        else:
            raise Exception("Can't reject a request unless status = 'ceda pending'")
            
    def approve(self):
        '''Review process : approve a request'''
        if self.request_status == 'ceda pending':
            self.request_status = 'ceda approved'
            # disassociate it from any gws
            self.save()
        else:
            raise Exception("Can't approve a request unless status = 'ceda pending'")        

    def convert(self):
        '''Set the status to completed. If no associated VM, make one and associate this request with it. Else update an existing VM. In both cases, copy existing fields to overwrite attributes of VM.'''
        
        # Approving a new request (first time)
        if self.request_type == 'new': #and (self.vm is None or self.vm == ''):
            # make a new gws object, copying attributes from request           
            vm =VM.objects.create(
                name = self.vm_name,
                internal_requester = self.internal_requester,
                description = self.description,
                date_required = self.date_required,
                type = self.type,
                operation_type = self.operation_type,
                cpu_required = self.cpu_required, 
                memory_required = self.memory_required, 
                disk_space_required = self.disk_space_required,
                disk_activity_required = self.disk_activity_required,
                mountpoints_required = self.mountpoints_required,
                network_required = self.network_required,
                os_required = self.os_required,
                patch_responsible = self.patch_responsible,
                status = 'created',
                end_of_life = self.end_of_life,
            )
            # root_users is a ManyToManyField, so need to copy outside of create()
            vm.root_users = self.root_users.all()
            vm.forceSave()
            
            self.vm = vm
            # update the request status
            self.request_status = 'completed'
            self.save()        

        elif self.request_type == 'update':
            if self.vm is None or self.vm == '':
                raise Exception("Can't do update request : no VM associated")
            else:
                vm = self.vm
                print self.vm
                # update the existing associated vm
                vm.name = self.vm_name
                vm.internal_requester = self.internal_requester
                vm.description = self.description
                vm.date_required = self.date_required
                vm.type = self.type
                vm.operation_type = self.operation_type
                vm.cpu_required = self.cpu_required
                vm.memory_required = self.memory_required
                vm.disk_space_required = self.disk_space_required
                vm.disk_activity_required = self.disk_activity_required
                vm.mountpoints_required = self.mountpoints_required
                vm.network_required = self.network_required
                vm.os_required = self.os_required
                vm.patch_responsible = self.patch_responsible
                vm.status = 'created'
                vm.end_of_life = self.end_of_life
                vm.root_users = self.root_users.all()
                vm.forceSave()
                
                # update the request status
                self.request_status = 'completed'
                self.save()
                
        elif self.request_type == 'remove':
            if self.vm is None or self.vm == '':
                raise Exception("Can't do update request : no VM associated")
            else:
                self.vm.delete()
                self.delete()
                
        else:
            raise Exception("Must set request status to update if updating an existing VM")
            
    def vm_link(self):
        return u'<a href="/admin/cedainfoapp/vm/%i">%s</a>' % (self.vm.id, self.vm.name)
    vm_link.allow_tags = True
    vm_link.short_description = 'VM'
            
class VM(models.Model):
    name = models.CharField(max_length=127, help_text="fully-qualified host name", unique=True) # TODO : need regex
    type = models.CharField(max_length=16, choices=settings.VM_TYPE_CHOICES, help_text="Type of VM, see REF") # TODO update REF
    operation_type = models.CharField(max_length=127, choices=settings.VM_OP_TYPE_CHOICES, help_text="Operation type of VM (dev, test, production, ...)")
    internal_requester = models.ForeignKey(User, help_text="CEDA person sponsoring the request", related_name='vm_internal_requester_user')
    description = models.TextField(help_text="")
    date_required = models.DateField()
    cpu_required = models.CharField(max_length=127)
    memory_required = models.CharField(max_length=127)
    disk_space_required = models.CharField(max_length=127, choices=settings.VM_DISK_SPACE_REQUIRED_CHOICES)
    disk_activity_required = models.CharField(max_length=127, choices=settings.VM_DISK_ACTIVITY_REQUIRED_CHOICES)
    mountpoints_required = MultiSelectField(max_length=2048, choices=settings.MOUNT_CHOICES)
    network_required = models.CharField(max_length=127, choices=settings.VM_NETWORK_ACTIVITY_REQUIRED_CHOICES)
    os_required = models.CharField(max_length=127, choices=settings.VM_OS_REQUIRED_CHOICES, default='rhel6')
    other_info = models.TextField(blank=True)
    patch_responsible = models.ForeignKey(User, related_name='vm_patch_responsible_user',
        limit_choices_to = {'id__in': settings.ADMIN_USERS_PATCH_RESPONSIBLE},
    )
    root_users = models.ManyToManyField(User, related_name='vm_root_users_user')
    status = models.CharField(max_length=127, choices=settings.VM_STATUS_CHOICES, default='active')
    created = models.DateField(auto_now_add=True)
    end_of_life = models.DateField(default = datetime.now()+timedelta(days=3*365)) # 3 years from now
    retired = models.DateField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')
    
    def __unicode__(self):
        return u'%s' % self.name
        
    def save(self, *args, **kwargs):
        # Custom save method : will only save an instance if there is no PK, i.e. if the model is a new instance
        # Logic : If you want to change a request, you can't, you need to make a new one & have that approved.
        if self.pk is None:
            super(VM, self).save(*args, **kwargs)
        else:
            raise Exception("Unable to save changes to existing VM : create an update request & get it approved")
            
    def forceSave(self, *args, **kwargs):
        # OK, sometimes we need to update individual fields (e.g. "approved")"
        super(VM, self).save(*args, **kwargs)
        
    def create_update_request(self):
        '''Create a new gwsrequest based on this gws pre-populated with values ready for editing & approval'''
        req = VMRequest.objects.create(
            vm_name = self.name,
            internal_requester = self.internal_requester,
            description = self.description,
            date_required = self.date_required,
            type = self.type,
            operation_type = self.operation_type,
            cpu_required = self.cpu_required, 
            memory_required = self.memory_required, 
            disk_space_required = self.disk_space_required,
            disk_activity_required = self.disk_activity_required,
            mountpoints_required = self.mountpoints_required,
            network_required = self.network_required,
            os_required = self.os_required,
            patch_responsible = self.patch_responsible,
            request_status = 'update',
            end_of_life = self.end_of_life,
        )
        req.root_users = self.root_users.all()
        req.save()
        return req.id
        
    		
    def update_link(self):
		return u'<a href="/vm/%i/update">update</a>' % self.id
    update_link.allow_tags = True
    
    def change_status(self):
        '''Toggle a VM as inuse / deprecated / retired'''
        if self.status == 'deprecated':
            self.status = 'created'
        elif self.status == 'created':
            self.status = 'inuse'
        elif self.status == 'inuse':
            self.status = 'deprecated'
        elif self.status == 'deprecated':
            self.status = 'retired'
        else:
            raise Exception("Unrecognised status to use for VM")
        self.forceSave()
        
    def action_links(self):
        return u'<a href="/vm/%i/changestatus">change status</a>' % (self.id,)
    action_links.allow_tags = True
    action_links.short_description = 'actions'
    
