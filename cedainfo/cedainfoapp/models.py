from django.db import models
# from django.contrib.gis.db import models
from datetime import datetime, timedelta
import os, sys
import subprocess
import string
import hashlib
import time
import socket
import re
import pwd, grp

from storageDXMLClient import SpotXMLReader
from fields import *  # custom MultiSelectField, MultiSelectFormField from http://djangosnippets.org/snippets/2753/

from sizefield.models import FileSizeField
from sizefield.templatetags.sizefieldtags import filesize

# needed for volume feed
from django.contrib.syndication.views import Feed

# Needed for BigInteger fix
from django.db.models.fields import IntegerField
from django.conf import settings

from django.contrib.auth.models import *

from django.core.validators import RegexValidator

# https://timmyomahony.com/blog/reversing-admin-urls-and-creating-admin-links-you-models/
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

class ProblemsMixin(object):

    problem_levels = {0: "INFO", 1: "WARN", 2: "PROBLEM", 3: "URGENT", 4: "CRITICAL"}
    problem_colours = {0: "green", 1: "black", 2: "orange", 3: "pink", 4: "red"}

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def problem_html(self, msg, level=0):
        return '<a href="%s">%s</a><font color="%s">[%s] %s</font>' % (self.get_admin_url(), self,
                                                                       self.problem_colours[level],
                                                                       self.problem_levels[level], msg)

# Create your models here.

# Tags to help in creation of SDDCS nodelist view
# Each tag can itself be tagged (hence tag attribute)
# class NodeListTag(models.Model):
#    name=models.CharField(max_length=126, help_text="name of this tag")
#    tag=models.ManyToManyField('self', null=True, blank=True, help_text="tag associated with this tag")
#    def __unicode__(self):
#        return u'%s' % self.name

# class NodeList(models.Model):
#    name = models.CharField(max_length=126)
#    def __unicode__(self):
#        return u'%s the nodelist' % self.name
#
# class HostList(models.Model):
#    nodelist = models.OneToOneField(NodeList)
#    def __unicode__(self):
#        return u'%s the hostlist' % self.nodelist.name
#
# class RackList(models.Model):
#    nodelist = models.OneToOneField(NodeList)
#    def __unicode__(self):
#        return u'%s the racklist' % self.nodelist.name


class FilseSetCreationError(Exception): pass


class Rack(models.Model):
    '''Physical rack in which physical servers are installed'''
    name = models.CharField(max_length=126, help_text="Name of Rack")
    room = models.CharField(max_length=126, help_text="Physical location of Rack")

    # tag = models.ManyToManyField(NodeListTag, null=True, blank=True, help_text="tag for nodelist")
    #    racklist = models.ForeignKey(RackList, null=True, blank=True, help_text="list this rack belongs to (only one)")
    def __unicode__(self):
        return u'%s' % self.name


class Host(models.Model):
    '''An identifiable machine having a distinct IP address'''
    hostname = models.CharField(max_length=512, help_text="Full hostname e.g. machine.badc.rl.ac.uk")
    ip_addr = models.IPAddressField(blank=True,
                                    help_text="IP Address")  # TODO check if admin allows no ip_addr field (otherwise default='0.0.0.0')
    serial_no = models.CharField(max_length=126, blank=True, help_text="Serial no (if physical machine)")
    po_no = models.CharField(max_length=126, blank=True, help_text="Purchase order no (if physical machine)")
    organization = models.CharField(max_length=512, blank=True,
                                    help_text="Organisation for which machine was purchased (if physical machine)")
    supplier = models.CharField(max_length=126, blank=True, help_text="Hardware supplier (if physical machine)")
    arrival_date = models.DateField(null=True, blank=True,
                                    help_text="Date host was installed (physical) / created (virtual)")
    planned_end_of_life = models.DateField(null=True, blank=True,
                                           help_text="Date foreseen for retirement of machine (if physical machine)")
    retired_on = models.DateField(null=True, blank=True,
                                  help_text="Date host was retired (leave blank if still in service)")
    mountpoints = models.CharField(max_length=512, blank=True,
                                   help_text="logical mount points: This is used to generate an auto mount script for the machine e.g. /badc(ro) mounts all filesets on /badc (read only). The default is read-write")
    ftpmountpoints = models.CharField(max_length=512, blank=True,
                                      help_text="logical ftp mount points: This is used to make a mount script that has chroot jailed mount points for ftp e.g. /badc(ro) mounts all the disks needed to mount all filesets on /badc (read only)")
    notes = models.TextField(blank=True, help_text="Additional notes")
    host_type = models.CharField(
            max_length=50,
            choices=(
                ("virtual_server", "virtual server"),
                ("hypervisor_server", "hypervisor server"),
                ("storage_server", "storage server"),
                ("workstation", "workstation"),
                ("server", "server"),
            ),
            default="server",
            help_text="Type of host"
    )
    os = models.CharField(max_length=512, blank=True, help_text="Operating system")
    capacity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                   help_text="Rough estimate in Tb only")  # just an estimate (cf Partition which uses bytes from df)
    rack = models.ForeignKey(Rack, blank=True, null=True,
                             help_text="Rack (if virtual machine, give that of hypervisor)")
    hypervisor = models.ForeignKey('self', blank=True, null=True,
                                   help_text="If host_type=virtual_server, give the name of the hypervisor which contains this one.")

    # tag = models.ManyToManyField(NodeListTag, null=True, blank=True, help_text="tag for nodelist")
    # hostlist = models.ManyToManyField(HostList, null=True, blank=True, help_text="list(s) this host belongs to")

    def __unicode__(self):
        return u'%s' % self.hostname

    def partitions(self):
        return Partition.objects.filter(host=self)

    class Meta:
        ordering = ['hostname']


class Partition(models.Model, ProblemsMixin):
    '''Filesystem equipped with standard directory structure for archive storage'''
    mountpoint = models.CharField(blank=True, max_length=1024, help_text="E.g. /disks/machineN", unique=True)
    host = models.ForeignKey(Host, blank=True, null=True, help_text="Host on which this partition resides")
    used_bytes = models.BigIntegerField(default=0,
                                        help_text="\"Used\" value from df, i.e. no. of bytes used. May be populated by script.")
    capacity_bytes = models.BigIntegerField(default=0,
                                            help_text="\"Available\" value from df, i.e. no. of bytes total. May be populated by script.")
    last_checked = models.DateTimeField(null=True, blank=True,
                                        help_text="Last time df was run against this partition & size values updated")
    status = models.CharField(max_length=50,
                              choices=(("Blank", "Blank"),
                                       ("Allocating", "Allocating"),
                                       ("Allocating_tape", "Allocating_tape"),
                                       ("Closed", "Closed"),
                                       ("Migrating", "Migrating"),
                                       ("Retired", "Retired")))
    notes = models.TextField(blank=True)

    def df(self):
        """Report disk usage.
           Return a dictionary with total, used, available. Sizes are reported
           in blocks of 1024 bytes."""

        # skip if retired disk or non-existant
        if self.status == 'Retired': return None
        if not os.path.exists(self.mountpoint): return None

        # do df
        output = subprocess.Popen(['/usr/local/bin/pan_df', '-B 1024', self.mountpoint],
                                  stdout=subprocess.PIPE).communicate()[0]
        lines = output.split('\n')
        if len(lines) == 3: dev, blocks_total, blocks_used, blocks_available, used, mount = lines[1].split()
        if len(lines) == 4: blocks_total, blocks_used, blocks_available, used, mount = lines[2].split()
        self.capacity_bytes = int(blocks_total) * 1024
        self.used_bytes = int(blocks_used) * 1024
        self.last_checked = datetime.utcnow()
        self.save()

    def exists(self):
        return os.path.ismount(self.mountpoint)

    exists.boolean = True

    def list_allocated(self):
        # list allocation for admin interface
        s = ''

        allocs = FileSet.objects.filter(partition=self).order_by('-overall_final_size')
        if len(allocs) > 0: s += 'Primary File Sets (biggest first): '
        for a in allocs:
            s += '<a href="/admin/cedainfoapp/fileset/%s">%s</a> ' % (a.pk, a.logical_path)

        allocs = FileSet.objects.filter(secondary_partition=self).order_by('-overall_final_size')
        if len(allocs) > 0: s += 'Secondary File Sets (biggest first): '
        for a in allocs:
            s += '<a href="/admin/cedainfoapp/fileset/%s">%s</a> ' % (a.pk, a.logical_path)
        return s

    list_allocated.allow_tags = True

    def meter(self):
        # graphic meter for partition
        if self.capacity_bytes == 0: return "No capacity set"
        used = self.used_bytes
        current_allocated = self.allocated()
        current_secondary_allocated = self.secondary_allocated()
        alloc = current_allocated * 100 / self.capacity_bytes
        # Find the set of most recent FileSetSizeMeasurements for FileSets on this Partition
        filesetsum = self.used_by_filesets()
        secondaryfilesetsum = self.secondary_used_by_filesets()
        # Turn this into a percentage of capacity
        fssumpercent = filesetsum * 100 / self.capacity_bytes
        # work out units for capacity for axis (full axis is 110%)
        if self.capacity_bytes < 1000:
            unit = "B"; scale = 1.0
        elif self.capacity_bytes < 1000000:
            unit = "kB"; scale = 0.001
        elif self.capacity_bytes < 1000000000:
            unit = "MB";  scale = 0.000001
        elif self.capacity_bytes < 1000000000000:
            unit = "GB"; scale = 0.000000001
        elif self.capacity_bytes < 1000000000000000:
            unit = "TB";  scale = 0.000000000001
        else:
            unit = "PB"; scale = 0.000000000000001
        googlechart = 'http://chart.googleapis.com/chart?cht=bhs&chco=0000ff|9999ff,00ff00|99ff99|aa1fff,ff0000,ffcccc&chs=300x80&chbh=16&chxt=y,x&chxl=0:|Allocated|Used&chma=5,10,5,5&chxtc=1,-100&chxs=1,,8|0,,9'
        googlechart += '&chd=t:%s,%s|%s,%s|%s,0|%s,0' % (
        filesetsum * scale, current_allocated * scale, secondaryfilesetsum * scale, current_secondary_allocated * scale,
        (used - filesetsum - secondaryfilesetsum) * scale, (self.capacity_bytes - used) * scale)
        googlechart += '&chxr=1,0,%s&chds=0,%s' % (
        1.2 * self.capacity_bytes * scale, 1.2 * self.capacity_bytes * scale)  # add data and axis range
        s = '<img src="%s">' % (googlechart,)
        return s

    meter.allow_tags = True

    def text_meter(self):
        # text meter for partition
        if self.capacity_bytes == 0:
            return "No capacity set"
        used = self.used_bytes
        cap = self.capacity_bytes
        #current_allocated = self.allocated()
        #current_secondary_allocated = self.secondary_allocated()
        #alloc = current_allocated * 100 / self.capacity_bytes
        # Find the set of most recent FileSetSizeMeasurements for FileSets on this Partition
        #filesetsum = self.used_by_filesets()
        #secondaryfilesetsum = self.secondary_used_by_filesets()
        # Turn this into a percentage of capacity
        #fssumpercent = filesetsum * 100 / self.capacity_bytes
        # work out units for capacity for axis (full axis is 110%)
        if self.capacity_bytes < 1000:
            unit = "B"; scale = 1.0
        elif self.capacity_bytes < 1000000:
            unit = "kB"; scale = 0.001
        elif self.capacity_bytes < 1000000000:
            unit = "MB";  scale = 0.000001
        elif self.capacity_bytes < 1000000000000:
            unit = "GB"; scale = 0.000000001
        elif self.capacity_bytes < 1000000000000000:
            unit = "TB";  scale = 0.000000000001
        else:
            unit = "PB"; scale = 0.000000000000001
        return "%5.2f%s used of %5.2f%s (%2.2f%%)" % (used * scale, unit, cap * scale, unit, 100.0 * used/cap)

    text_meter.allow_tags = True

    def allocated(self):
        # find total allocated space
        total = 0
        allocs = FileSet.objects.filter(partition=self)
        for a in allocs: total += a.overall_final_size
        return total

    def disk_allocated(self):
        # find total allocated space allowing for tape only filesets
        total = 0
        allocs = FileSet.objects.filter(partition=self)
        for a in allocs:
            if a.primary_on_tape:
                alloc_size = max(a.last_vol(), 0.05 * a.overall_final_size)
            else:
                alloc_size = a.overall_final_size
            total += alloc_size
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
        use = {'prime_alloc_used': 0, 'second_alloc_used': 0, 'unalloc_used': 0, 'empty': 0, 'prime_alloc': 0,
               'second_alloc': 0, 'unallocated': 0}
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

    @staticmethod
    def problems():
        partitions = Partition.objects.exclude(status="Retired")
        msgs = []
        # list overfilled partitions
        for p in partitions:
            if 100.0 * p.used_bytes/(p.capacity_bytes+1) > 99.99:
                msgs.append(p.problem_html("Partition Full", 4))
            elif 100.0 * p.used_bytes/(p.capacity_bytes+1) > 99.0:
                msgs.append(p.problem_html("Partition over filled", 3))
        # list overallocated partitions
        for p in partitions:
            allocated = p.allocated() + p.secondary_allocated()
            if 100.0 * allocated/(p.capacity_bytes+1) > 87.0:
                msgs.append(p.problem_html("Partition overallocated", 2))
        return msgs

    def __unicode__(self):
        tb_remaining = (self.capacity_bytes - self.used_bytes) / (1024 ** 4)
        return u'%s (%d %s)' % (self.mountpoint, tb_remaining, 'Tb free')

    __unicode__.allow_tags = True    # seem to need this in order to use __unicode__ as one of the fields
                                     # in list_display in the admin view (see
                                     # http://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display)


class CurationCategory(models.Model):
    '''Category indicating whether CEDA is the primary or secondary archive (or other status) for a dataset'''
    category = models.CharField(max_length=5, help_text="Curation category label")
    description = models.CharField(max_length=1024, help_text="Longer description")

    def __unicode__(self):
        return u"%s : %s" % (self.category, self.description)


class BackupPolicy(models.Model):
    '''Backup policy'''
    tool = models.CharField(max_length=45, help_text="e.g. DMF / tape")
    destination = models.CharField(max_length=1024, blank=True,
                                   help_text="Path made up of e.g. dmf:/path_within_dmf, rsync:/path_to_nas_box, tape:/tape_number")
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

    class Meta:
        ordering = ["name"]


class FileSet(models.Model, ProblemsMixin):
    ''' subtree of archive directory hierarchy.
    Collection of all filesets taken together should exactly represent 
    all files in the archive. Must never span multiple filesystems.'''
    logical_path = models.CharField(max_length=1024, blank=True, default='/badc/NNNN', help_text="e.g. /badc/acsoe",
                                    unique=True)
    overall_final_size = models.BigIntegerField(
        help_text="The allocation given to a fileset is an estimate of the final size on disk. If the dataset is going to grow indefinitely then estimate the size for 4 years ahead. Filesets can't be bigger than a single partition, but in order to aid disk managment they should no exceed 20% of the size of a partition.")  # Additional data still expected (as yet uningested) in bytes
    notes = models.TextField(blank=True)
    partition = models.ForeignKey(Partition, blank=True, null=True, limit_choices_to={'status': 'Allocating'},
                                  help_text="Actual partition where this FileSet is physically stored")
    storage_pot_type = models.CharField(max_length=64, blank=True, default='archive',
                                        help_text="The 'type' directory under which the data is held. This is archive for archive data and project_space for project space etc. DO NOT CHANGE AFTER SPOT CREATION",
                                        choices=(("archive", "archive"),
                                                 ("project_spaces", "project_spaces"),
                                                 ("group_workspace", "group_workspace")))
    storage_pot = models.CharField(max_length=1024, blank=True, default='',
                                   help_text="The directory under which the data is held")
    migrate_to = models.ForeignKey(Partition, blank=True, null=True, help_text="Target partition for migration",
                                   related_name='fileset_migrate_to_partition')
    secondary_partition = models.ForeignKey(Partition, blank=True, null=True,
                                            help_text="Target for secondary disk copy",
                                            related_name='fileset_secondary_partition')
    dmf_backup = models.BooleanField(default=False, help_text="Backup to DMF")
    sd_backup = models.BooleanField(default=False, help_text="Backup to Storage-D")
    complete = models.BooleanField(default=False,
                                   help_text="Is the fileset complete. If this is set then we are not anticipating the files to change, be deleted or added to.")
    complete_date = models.DateField(null=True, blank=True, help_text="Date when fileset was set to complete.")
    primary_on_tape = models.BooleanField(default=False, help_text="Primary media storage on tape.")

    def __unicode__(self):
        return u'%s' % (self.logical_path,)

    # TODO custom save method (for when assigning a partition) : check that FileSet size

    def storage_path(self):
        return os.path.normpath(self.partition.mountpoint + '/' + self.storage_pot_type + '/' + self.storage_pot)

    def secondary_storage_path(self):
        if self.secondary_partition:
            return os.path.normpath(
                self.secondary_partition.mountpoint + '/backup/' + self.storage_pot_type + '/' + self.storage_pot)
        else:
            return None

    def migrate_path(self):
        return os.path.normpath(self.migrate_to.mountpoint + '/' + self.storage_pot_type + '/' + self.storage_pot)

    def migrate_spot(self, do_audit=True):
        assert self.storage_pot != '', "can't migrate a spot does not already exists in the db"
        assert self.partition, "can't migrate a spot if no partition"
        assert self.migrate_to, "can't migrate a spot if no migration partition"
        assert os.path.islink(self.logical_path), "can't migrate a spot if logical path is not a link"

        # copy - exceptions raised if fail
        self._migration_copy()

        # delete link and remake link to new partition
        if os.readlink(self.logical_path) != self.migrate_path():  # may be tring again after failing
            os.unlink(self.logical_path)
            os.symlink(self.migrate_path(), self.logical_path)

        # copy again - exceptions raised if fail
        self._migration_copy()

        # verify and log - exceptions raised if fail
        if do_audit:
            audit = Audit(fileset=self)
            audit.start()
            audit.verify_copy()

            # mark for deletion - write a file in the spot directory
            # showing the migration is complete with regard to the CEDA info tool
            DOC = open(os.path.join(self.storage_path(), 'MIGRATED.txt'), 'w')
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
        rsynccmd = 'rsync -av %s/ %s' % (self.storage_path(), self.migrate_path())
        print ">>> %s" % rsynccmd
        subprocess.check_call(rsynccmd.split())

    def secondary_copy_command(self):
        '''make an rsync command to create a secondary copy'''
        if not self.secondary_partition: return ''
        host = self.partition.host.hostname
        frompath = self.storage_path()
        topath = "badc@%s:%s" % (self.secondary_partition.host.hostname, self.secondary_storage_path())
        rsynccmd = 'ssh %s rsync -Puva --delete %s %s' % (host, frompath, topath)
        return rsynccmd

    def spot_exists(self):
        if self.storage_pot == '':
            return False
        return os.path.exists(self.storage_path())

    spot_exists.boolean = True

    def logical_path_exists(self):
        return os.path.exists(self.logical_path)

    logical_path_exists.boolean = True

    def logical_path_right(self):
        if not os.path.exists(self.logical_path):
            return False
        if not os.path.islink(self.logical_path):
            return False
        else:
            linkpath = os.readlink(self.logical_path)
            if linkpath == self.storage_path():
                return True
            else:
                return False

    def status(self):
        "return text showing fileset status"
        if not self.partition:
            if self.migrate_to or self.storage_pot:
                return '<font color="#ff0000">Migrate to/Storage pot are set before partition?</font>'
            elif not self.logical_path_exists():
                return '<font color="#bbbb00">New</font>'
            elif os.path.islink(self.logical_path):
                linkpath = os.readlink(self.logical_path)
                if linkpath[
                   0:7] == '/disks/': return '<font color="#bbbb00">New (Can allocate from existing link)</font>'
            else:
                return '<font color="#ff0000">Logical path exists</font>'

        else:
            if not self.storage_pot and not self.logical_path_exists():
                return '<font color="#bbbb00">Ready for storage creation</font>'
            elif self.logical_path_right():
                if self.migrate_to:
                    return '<font color="#bbbb00">File set marked for migration</font>'
                else:
                    return '<font color="#00bb00">Normal</font>'
            else:
                return '<font color="#ff0000">Link error</font>'

    status.allow_tags = True

    def make_fileset(self, path, size, on_tape=False):
        """make a fileset including makeing spot directoies and seting allocations."""
        filesets = FileSet.objects.filter(logical_path=path)
        assert not os.path.exists(path), "Logical path already exists."
        assert len(filesets) == 0, "File set with same logical path already exists."
        assert os.path.isdir(os.path.dirname(path)), "Parent directory does not exist."

        # select partitions to search for space
        partitions = Partition.objects.filter(status='Allocating')
        fill_factor = 0.8

        # find the fullest partition which can accomidate the file set
        allocated_partition = None
        fullest_space = 10e40
        for p in partitions:
            print p, p.allocated(), p.disk_allocated()
            partition_free_space = fill_factor * p.capacity_bytes - p.disk_allocated()
            # if this partition could accommidate file set...
            if partition_free_space > size:
                # ... and its the fullest so far
                if partition_free_space < fullest_space:
                    allocated_partition = p
                    fullest_space = partition_free_space
                    print ">>>>>>> ", p, allocated_partition, fullest_space, partition_free_space

        if allocated_partition is None:
            raise FilseSetCreationError("Can't find a partition to allocate this to.")

        # create a fileset in the database
        self.logical_path = path
        self.overall_final_size = size
        self.partition = allocated_partition
        self.notes += '\nAllocated partition %s (%s)' % (self.partition, datetime.utcnow())
        self.save()

        # create the spot name. This uses the fileset id and last directory name in the path.
        head, spottail = os.path.split(path)
        if spottail == '': head, spottail = os.path.split(head)
        spotname = "spot-%s-%s" % (self.pk, spottail)
        self.storage_pot = spotname

        try:
            os.makedirs(self.storage_path())
        except:
            self.delete()
            raise FilseSetCreationError("Can't make storage pot directory")
        try:
            # change the group ownership to be the same as the parent path.
            gid = os.stat(os.path.dirname(path)).st_gid
            os.chown(self.storage_path(), -1, gid)
        except:
            os.rmdir(self.storage_path())
            self.delete()
            raise FilseSetCreationError("Can't chown the storage pot directory (removed spot dir for consistancy)")
        try:
            os.symlink(self.storage_path(), self.logical_path)
        except:
            # remove spot dir that was make correctly, but is inconsistant because link not made
            os.rmdir(self.storage_path())
            self.delete()
            raise FilseSetCreationError("Can't make link (removed spot dir for consistancy)")
        self.save()

    # split a fileset in two. 
    def split_fileset(self, path, size):
        # find path is in scope of this fileset
        if path == self.logical_path: raise FilseSetCreationError("Can't split: path identical to current fileset")
        if self.logical_path != path[0:len(self.logical_path)]: raise FilseSetCreationError(
            "Can't split: path not contained in current fileset")

        # if check break point is an existing directory        
        if not os.path.isdir(path): raise FilseSetCreationError("Can only split on a directory.")
        if os.path.islink(path): raise FilseSetCreationError("Can't split on a symlink.")

        # make new fileset with same partition.
        new_fs = FileSet(partition=self.partition,
                         logical_path=path, overall_final_size=size,
                         notes="Split from %s on %s" % (self, datetime.utcnow()),
                         secondary_partition=self.secondary_partition,
                         sd_backup=self.sd_backup)
        new_fs.save()
        # spot tail
        head, spottail = os.path.split(new_fs.logical_path)
        if spottail == '': head, spottail = os.path.split(head)
        # create spot name 
        spotname = "spot-%s-%s" % (new_fs.pk, spottail)
        new_fs.storage_pot = spotname
        new_fs.save()

        # rename the break dir as the spot
        os.rename(path, new_fs.storage_path())

        # make new link
        os.symlink(new_fs.storage_path(), new_fs.logical_path)

        # change the parent fileset size 
        self.overall_final_size = max(0, self.overall_final_size - size)
        self.notes += "\nSplit at %s on %s." % (new_fs.logical_path, datetime.utcnow())
        self.save()
        return new_fs

    def backup_summary(self):
        # get a text summary of storaged backup status
        reader = SpotXMLReader(self.storage_pot)
        return reader.getSpotSummary()

    backup_summary.short_description = 'backup'
    backup_summary.allow_tags = True

    # crude storage-d size finder via screen scrape...
    def backup_summary2(self):
        url = 'http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_Summary_XML.php?fileset=%s;level=top' % self.storage_pot
        import urllib2
        f = urllib2.urlopen(url)
        backup = f.read()
        m = re.search(
            '<total_volume>(.+)</total_volume><total_file_count>(.*)</total_file_count><aggregation_count>(.*)</aggregation_count><first_file>(.*)</first_file><last_updated>(.*)</last_updated>',
            backup)
        if m:
            backupsize, backupfiles, nagg, firstfiletime, lastupdated = (int(m.group(1)),
                                                                         int(m.group(2)), int(m.group(3)), m.group(4),
                                                                         m.group(5))
        else:
            backupsize, backupfiles, nagg, firstfiletime, lastupdated = 0, 0, 0, '--', '--'
        return "%s files, %s bytes last stored %s" % (backupfiles, backupsize, lastupdated)

    def sd_backup_process_log(self):
        """find last time processed for storage-D..."""
        SDLOG = open('/datacentre/stats/storaged/lastprocessing-latest-RT.txt')
        while 1:
            line = SDLOG.readline()
            if line == '':
                break
            if line.find(self.storage_pot) != -1:
                return line
        return 'Not in log'

    @staticmethod
    def problems():
        """find fileset problems"""
        # Look at filesets for over allocation
        filesets = FileSet.objects.all()
        msgs = []
        today = datetime.now()

        for f in filesets:
            fssms = FileSetSizeMeasurement.objects.filter(fileset=f).order_by('-date')
            first_time = (len(fssms) == 0)

            if not first_time:
                last_fssm = fssms[0]
                too_many_files = last_fssm.no_files > 5000000
                too_big = f.overall_final_size > 40000000000000
                over_alloc = last_fssm.size > f.overall_final_size

                changing = False     # assume static and look for changes
                npoints = 0
                for fssm in fssms[1:]:                    # loop over fileset measurements from second to last...
                    if datetime.now() - fssm.date > timedelta(days=120):
                        break  # only look in past 120 days
                    npoints += 1         # number of points within 120 days
                    if fssm.size != last_fssm.size or fssm.no_files != last_fssm.no_files:
                        changing = True
                if npoints < 2:
                    changing = True    # if we have one or less points in the 120 days then assume changing.

                if len(fssms) < 10 and not f.sd_backup:
                    msgs.append(f.problem_html("Newish and not marked for backup.", 1))
            else:
                msgs.append(f.problem_html("Not measured yet", 1))
                continue

            if too_many_files:
                msgs.append(f.problem_html("Too Many files", 1))
            if too_big:
                msgs.append(f.problem_html("Too Big", 1))
            if over_alloc:
                msgs.append(f.problem_html("Over allocation", 2))

            if f.sd_backup:
                backup_processed = f.sd_backup_process_log()[-13:-5]
                if backup_processed[:3] == "Not":
                    msgs.append(f.problem_html("Not processed for backup yet", 1))
                else:
                    date = datetime(int(backup_processed[:4]), int(backup_processed[4:6]), int(backup_processed[6:8]))
                    if today - date > timedelta(days=10):
                        msgs.append(f.problem_html("Not backed up for over 10 days", 2))

            if not f.partition:
                msgs.append(f.problem_html("Fileset without partition", 4))

            if not f.storage_pot:
                msgs.append(f.problem_html("Fileset without storage pot", 4))
            if not f.logical_path_right():
                msgs.append(f.problem_html("Fileset with bad logical path", 4))
            if f.migrate_to:
                msgs.append(f.problem_html("Fileset marked for migration to %s" % f.migrate_to, 3))

        return msgs

    # migration allocation don by hand at the moment

    # def allocate_m(self):
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
        """Report disk usage of FileSet by creating as FileSetSizeMeasurement."""
        if self.spot_exists():
            # find volume using du
            output = subprocess.Popen(['/usr/bin/du', '-sk', '--apparent', self.storage_path()],
                                      stdout=subprocess.PIPE).communicate()[0]
            # output = subprocess.Popen(['/usr/bin/du', '-sk', self.storage_path()],stdout=subprocess.PIPE).communicate()[0]
            lines = output.split('\n')
            if len(lines) == 2:
                size, path = lines[0].split()

            # find number of files
            p1 = subprocess.Popen(["find", self.storage_path(), "-type", "f"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            nfiles = p2.communicate()[0]

            fssm = FileSetSizeMeasurement(fileset=self, date=datetime.utcnow(),
                                          size=int(size) * 1024, alloc=self.overall_final_size, no_files=int(nfiles))
            fssm.save()
        return

    def dataentity(self):
        des = DataEntity.objects.order_by("-logical_path")
        for de in des:
            if de.logical_path == '': return None  # skip if getting to DE with no logical path set
            if de.logical_path == self.logical_path[0:len(de.logical_path)]:
                return de
        return None

    def responsible(self):
        des = DataEntity.objects.order_by("-logical_path")
        for de in des:
            if de.logical_path == '': return None  # skip if getting to DE with no logical path set
            if de.logical_path == self.logical_path[0:len(de.logical_path)]:
                return de.responsible_officer
        return None

    def links(self):
        # links to actions for filesets
        s = '<a href="/fileset/%s/du">du</a> <a href="http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_Summary.php?%s">storageD</a>' % (
        self.pk, self.storage_pot)
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

    def last_vol(self):
        # display most recent FileSetSizeMeasurement
        try:
            fssm = FileSetSizeMeasurement.objects.filter(fileset=self).order_by('-date')[0]
            return fssm.size
        except:
            return 0

    def last_audit(self):
        # display most recent audit
        audit = Audit.objects.filter(fileset=self)
        if len(audit) == 0:
            return None
        else:
            audit = audit.order_by('-starttime')[0]
            return audit

    last_size.allow_tags = True


class VolFeed(Feed):
    # RSS feed to be used by the CEDA site.
    title = "CEDA data volume summary"
    link = "/latest/volumes"
    description = "Lastest volume summary for CEDA data."

    def items(self):
        return [1]

    def item_title(self, item):
        return "Volume summary"

    def item_description(self, item):

        d = ''
        table = {}
        filesets = FileSet.objects.all().order_by('logical_path')

        toplevel = ''
        vol, nfiles = 0, 0
        for f in filesets:
            slashcount = f.logical_path.count('/')
            if slashcount == 2:
                table[toplevel] = (vol, nfiles)
                vol, nfiles = 0, 0
                toplevel = f.logical_path

            size = f.last_size()
            if size:
                vol = vol + size.size
                nfiles = nfiles + size.no_files
        lines = table.items()

        d += "Top 10 largest datasets\n"
        lines.sort(key=lambda a: a[1][0], reverse=True)
        i = 0
        for topfs, size in lines:
            d += "%s | %2.2f TB | %s\n" % (topfs, size[0] / 1.0e12, size[1])
            i += 1
            if i > 9: break

        d += "\nTop 10 datasets with most files\n"
        lines.sort(key=lambda a: a[1][1], reverse=True)
        i = 0
        for topfs, size in lines:
            d += "%s | %2.2f TB | %s\n" % (topfs, size[0] / 1.0e12, size[1])
            i += 1
            if i > 9: break

        return d

    def item_link(self, item):
        return "link"

    def item_pubdate(self, item):
        return datetime.now()


class DataEntity(models.Model):
    '''Collection of data treated together. Has corresponding MOLES DataEntity record.'''
    dataentity_id = models.CharField(help_text="MOLES data entity id", max_length=255, unique=True)
    friendly_name = models.CharField(max_length=1024, blank=True,
                                     help_text="Longer name (possibly incl spaces, braces)")
    symbolic_name = models.CharField(max_length=1024, blank=True,
                                     help_text="Short abbreviation to be used for directory names etc")
    logical_path = models.CharField(max_length=1024, blank=True, help_text="Top level of location within archive")
    curation_category = models.ForeignKey(CurationCategory, null=True, blank=True,
                                          help_text="Curation catagory : choose from list")
    notes = models.TextField(blank=True, help_text="Additional notes")
    availability_priority = models.BooleanField(default=False, help_text="Priority dataset : use highest spec hardware")
    availability_failover = models.BooleanField(default=False,
                                                help_text="Whether or not this dataset requires redundant copies for rapid failover (different from recovery from backup)")
    access_status = models.ForeignKey(AccessStatus, help_text="Security applied to dataset")
    recipes_expression = models.CharField(max_length=1024, blank=True)
    recipes_explanation = models.TextField(blank=True,
                                           help_text="Verbal explanation of registration process. Can be HTML snippet. To be used in dataset index to explain to user steps required to gain access to dataset.")
    db_match = models.IntegerField(null=True, blank=True,
                                   help_text="Admin use only : please ignore")  # id match to "dataset" in old storage db
    responsible_officer = models.ForeignKey(Person, blank=True, null=True,
                                            help_text="CEDA person acting as contact for this dataset")
    last_reviewed = models.DateField(null=True, blank=True, help_text="Date of last dataset review")
    review_status = models.CharField(
            max_length=50,
            choices=(
                ("to be reviewed", "to be reviewed"),
                ("in review", "in review"),
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
    # host = models.ManyToManyField(Host, help_text="Host machine on which service is deployed", null=True, blank=True)
    host = models.ForeignKey(Host, help_text="Host machine on which service is deployed", null=True, blank=True)
    name = models.CharField(max_length=512, help_text="Name of service")
    active = models.BooleanField(default=False, help_text="Is this service active or has it been decomissioned?")
    description = models.TextField(blank=True, help_text="Longer description if needed")
    documentation = models.URLField(verify_exists=False, blank=True,
                                    help_text="URL to documentation for service in opman")
    externally_visible = models.BooleanField(default=False,
                                             help_text="Whether or not this service is visible outside the RAL firewall")
    deployment_type = models.CharField(max_length=50,
                                       choices=(
                                           ("failover", "failover"),
                                           ("loadbalanced", "loadbalanced"),
                                           ("simple", "simple")
                                       ),
                                       default="simple",
                                       help_text="Type of deployment"
                                       )
    dependencies = models.ManyToManyField('self', blank=True, null=True,
                                          help_text="Other services that this one depends on")
    availability_tolerance = models.CharField(max_length=50,
                                              choices=(
                                                  ("immediate", "must be restored ASAP"),
                                                  ("24 hours", "must be restored within 24 hours of failure"),
                                                  ("1 workingday", "must be restored within 1 working day of failure"),
                                                  (
                                                  "3 workingdays", "must be restored within 3 working days of failure"),
                                                  ("1 week", "must be restored within 1 week of failure"),
                                                  ("2 weeks", "must be restored within 2 weeks of failure"),
                                                  ("1 month", "must be restored within 1 month of failure"),
                                                  ("disposable", "disposable"),
                                              ),
                                              default="disposable",
                                              help_text="How tolerant of unavailability we should be for this service"
                                              )
    requester = models.ForeignKey(Person, null=True, blank=True, related_name='service_requester',
                                  help_text="CEDA Person requesting deployment")
    installer = models.ForeignKey(Person, null=True, blank=True, related_name='service_installer',
                                  help_text="CEDA Person installing the service")
    software_contact = models.ForeignKey(Person, null=True, blank=True, related_name='service_software_contact',
                                         help_text="CEDA or 3rd party contact who is responsible for the software component used for the service")

    def __unicode__(self):
        the_host = ''
        if self.host is not None:
            the_host = self.host
        return u'%s (%s)' % (self.name, the_host)

    def summary(self):
        '''Returns a summary string extracted from the start of the full description text'''

        SummaryLength = 60
        summary = self.description.strip()
        summary = ' '.join(summary.split())

        if len(summary) > SummaryLength:
            summary = summary[0:SummaryLength - 1] + '...'

        return summary

    def documentationLink(self):

        return self.documentation


class HostHistory(models.Model):
    """Entries detailing history of changes to a Host"""
    host = models.ForeignKey(Host, help_text="Host name")
    date = models.DateField(help_text="Event date")
    history_desc = models.TextField(help_text="Details of event / noteworthy item in host's history")
    admin_contact = models.ForeignKey(Person, help_text="CEDA Person reporting this event")

    def __unicode__(self):
        return u'%s|%s' % (self.host, self.date)


class ServiceBackupLog(models.Model):
    """Backup history for a Service"""
    service = models.ForeignKey(Service, help_text="Service being backed up")
    backup_policy = models.ForeignKey(BackupPolicy, help_text="Backup policy implemented for this backup event")
    date = models.DateTimeField(help_text="Date and time of backup")
    success = models.BooleanField(default=False, help_text="Success (True) or Failure (False) of backup event")
    comment = models.TextField(blank=True, help_text="Additional comment(s)")

    def __unicode__(self):
        return u'%s|%s' % (self.service, self.date)


class FileSetSizeMeasurement(models.Model):
    """Date-stampted size measurement of a FileSet"""
    fileset = models.ForeignKey(FileSet, help_text="FileSet that was measured")
    date = models.DateTimeField(default=datetime.now, help_text="Date and time of measurement")
    size = models.BigIntegerField(help_text="Size in bytes")  # in bytes
    alloc = models.BigIntegerField(help_text="Allocatoion Size in bytes")  # in bytes
    no_files = models.BigIntegerField(null=True, blank=True, help_text="Number of files")

    def __unicode__(self):
        if self.size > 2000000000000:
            size = self.size / 1000000000000
            unit = "TB"
        elif self.size > 2000000000:
            size = self.size / 1000000000
            unit = "GB"
        elif self.size > 2000000:
            size = self.size / 1000000
            unit = "MB"
        elif self.size > 2000:
            size = self.size / 1000
            unit = "kB"
        else:
            size = self.size
            unit = "B"

        if self.no_files > 2000000:
            no_files = self.no_files / 1000000
            funit = "Mfiles"
        else:
            no_files = self.no_files
            funit = "files"

        return u'%s %s; %s %s (%s)' % (size, unit, no_files, funit, self.date.strftime("%Y-%m-%d %H:%M"))


class Audit(models.Model, ProblemsMixin):
    """A record of inspecting a fileset"""
    fileset = models.ForeignKey(FileSet, help_text="FileSet which this audit related to at time of creation",
                                on_delete=models.SET_NULL, null=True, blank=True)
    starttime = models.DateTimeField(null=True, blank=True, )
    endtime = models.DateTimeField(null=True, blank=True, )
    auditstate = models.CharField(max_length=50,
                                  choices=(
                                      ("not started", "not started"),
                                      ("started", "started"),
                                      ("finished", "finished"),
                                      ("copy verified", "copy verified"),
                                      ("analysed", "analysed"),
                                      ("error", "error"),
                                      ("corruption", "corruption"),
                                  ),
                                  default="not started",
                                  help_text="state of this audit"
                                  )
    total_files = models.IntegerField(default=0)
    total_volume = FileSizeField(default='0')
    corrupted_files = models.IntegerField(default=0)
    new_files = models.IntegerField(default=0)
    deleted_files = models.IntegerField(default=0)
    modified_files = models.IntegerField(default=0)
    unchanges_files = models.IntegerField(default=0)
    logfile = models.CharField(max_length=255, default='')

    def __unicode__(self):
        return 'Audit of %s started %s  [[%s]]' % (self.fileset, self.starttime, self.auditstate)

    def fileset_link(self):
        return '<a href="/admin/cedainfoapp/fileset/%s">%s</a>' % (self.fileset.pk, self.fileset)

    fileset_link.allow_tags = True
    fileset_link.short_description = "Fileset"

    def start(self):
        self.starttime = datetime.utcnow()
        self.auditstate = 'started'
        self.save()
        try:
            self.checkm_log()
        except Exception, e:
            self.endtime = datetime.utcnow()
            self.auditstate = 'error'
            self.save()
            raise e

        self.endtime = datetime.utcnow()
        self.auditstate = 'finished'
        self.save()

        # analyse the result
        self.analyse()

    def prev_audit(self):
        # return privious audit
        audit = Audit.objects.filter(fileset=self.fileset, starttime__lt=self.starttime).order_by('-starttime')
        if len(audit) == 0:
            return None
        else:
            audit = audit[0]
            return audit

    def analyse(self):
        # count number and volume
        self.totals()

        # find the last finished audit of this fileset for comparison
        prev_audit = self.prev_audit()
        if prev_audit and prev_audit.auditstate == 'analysed':
            result = self.compare(prev_audit)
            self.corrupted_files = len(result['corrupt'])
            self.modified_files = result['modified']
            self.new_files = result['new']
            self.deleted_files = result['deleted']
            self.unchanges_files = result['unchanged']

        if self.corrupted_files != 0:
            self.auditstate = 'corruption'
        else:
            self.auditstate = 'analysed'
        self.save()

    def totals(self):
        # record number and size totals for audit.
        # open log file
        LOG = open(self.logfile)

        # lists for tallies
        total_files = 0
        total_volume = 0

        while 1:
            line = LOG.readline()
            if line == '':
                break
            line = line.strip()
            if line == '':
                continue
            if line[0] == '#':
                continue

            (filename, algorithm, digest, size, modtime) = line.split('|')
            total_files += 1
            total_volume += int(size)

        self.total_files = total_files
        self.total_volume = total_volume
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

            if cline == '':
                cend = True
            if pline == '':
                pend = True

            # stop if end of both files
            if pend and cend:
                break

            # ignore lines with # at the start
            if not cend and cline[0] == '#':
                cline = CLOG.readline()
                continue
            if not pend and pline[0] == '#':
                pline = PLOG.readline()
                continue

            # if the lines are the same move both logs on
            if cline == pline:
                unchanged += 1
                cline = CLOG.readline()
                pline = PLOG.readline()
                continue

            # if current log ended then files have been deleted
            if cend:
                deleted += 1
                pline = PLOG.readline()
                continue

            # if previous log ended then files have been added
            if pend:
                new += 1
                cline = CLOG.readline()
                continue

            # split the lines into components. (At this point we know both lines exist)
            (cfilename, calgorithm, cdigest, csize, cmodtime) = cline.split('|')
            (pfilename, palgorithm, pdigest, psize, pmodtime) = pline.split('|')

            # if current file is differnt and less than the previous one then
            # a new file has been added
            if cfilename < pfilename:
                new += 1
                cline = CLOG.readline()
                continue

            # if current file is differnt and greater than the previous one 
            # then a file has been deleted.
            if cfilename > pfilename:
                deleted += 1
                pline = PLOG.readline()
                continue

            # at this point we know the log lines are for the same file, but are different in some 
            # other way

            # if the modified time has changed then the file has been modified
            if cmodtime != pmodtime:
                modified += 1
                cline = CLOG.readline()
                pline = PLOG.readline()
                continue

            # if content has changed this is corrupt
            if cdigest != pdigest:
                corrupt.append(cline)
                cline = CLOG.readline()
                pline = PLOG.readline()
                continue

        return {'corrupt': corrupt, 'modified': modified, 'new': new, 'deleted': deleted, 'unchanged': unchanged}

    def checkm_log(self):
        print "Writing checkm log for this audit..."
        fileset = self.fileset
        if fileset is None:
            raise Exception("Can't make log for audit with no fileset")
        # make checkm directory for spot is missing
        if not os.path.exists('%s/%s' % (settings.CHECKM_DIR, fileset.storage_pot)):
            os.mkdir('%s/%s' % (settings.CHECKM_DIR, fileset.storage_pot))
        self.logfile = '%s/%s/checkm.%s.%s.log' % (settings.CHECKM_DIR, fileset.storage_pot,
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
        reldir = directory[len(storage_path) + 1:]
        names = os.listdir(directory)
        # look for diectories and recurse
        names.sort()
        for n in names:
            path = os.path.join(directory, n)
            if os.path.isdir(path) and not os.path.islink(path):
                self._checkm_log(path, storage_path, LOG)
        # for each file 
        for n in names:
            path = os.path.join(directory, n)
            relpath = os.path.join(reldir, n)
            # if path is reg file
            if os.path.isfile(path) and not os.path.islink(path):
                size = os.path.getsize(path)
                mtime = datetime.utcfromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%dT%H:%M:%SZ')
                F = open(path)
                m = hashlib.md5()
                while 1:
                    buf = F.read(1024 * 1024)
                    m.update(buf)
                    if buf == "": break
                LOG.write("%s|md5|%s|%s|%s\n" % (relpath, m.hexdigest(), size, mtime))

    def verify_copy(self):
        # verify that a migrated copy has the same files as this audit.
        # Added files are OK.
        print "Verifying checkm log against migrated files ..."
        LOG = open(self.logfile)
        while 1:
            line = LOG.readline()
            if line == '':
                break
            if line[0] == '#':
                continue
            relpath, alg, checksum, size, modtime = line.split('|')
            checksum = checksum.strip()
            newpath = os.path.join(self.fileset.migrate_path(), relpath)
            if not os.path.exists(newpath):
                raise "File not there %s" % newpath
            if not os.path.isfile(newpath):
                raise "Not regular file %s" % newpath

            F = open(newpath)
            m = hashlib.md5()
            while 1:
                buf = F.read(1024 * 1024)
                m.update(buf)
                if buf == "": break
            if m.hexdigest() != checksum: raise "checksums do not match %s" % newpath
        self.auditstate = 'copy verified'
        self.save()
        print "      ... Done"

    @staticmethod
    def problems():
        msgs = []
        audits = Audit.objects.filter(auditstate='corruption')
        for a in audits:
            msgs.append(a.problem_html("Audit detected corruption", 3))

        audits = Audit.objects.filter(auditstate='error')
        for a in audits:
            msgs.append(a.problem_html("Audit detected error", 2))

        time_threshold = datetime.now() - timedelta(days=5)
        audits = Audit.objects.filter(auditstate='started', starttime__lt=time_threshold)
        for a in audits:
            msgs.append(a.problem_html("Audit started but not finished", 1))
        return msgs

# class SpatioTemp(models.Model):
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
        ordering = ['gws_name']

    gws_name = models.CharField(
            # name doesn't need to be unique here : there might be several requests but it's the one that's approved that gets copied.
            max_length=16,
            validators=[
                RegexValidator(
                        regex=settings.GWS_NAME_REGEX,
                        message=u"Invalid name : this string will be used as a unix group name so must match the pattern %s" % settings.GWS_NAME_REGEX.pattern,
                )
            ]
            ,
            help_text='short string to be used as name for group workspace, also used for corresponsing unix group name. Must match pattern %s' % settings.GWS_NAME_REGEX.pattern
    )
    path = models.CharField(max_length=2048, help_text='storage path to this group workspace excluding GWS name',
                            choices=settings.GWS_PATH_CHOICES)
    internal_requester = models.ForeignKey(User, help_text='CEDA person sponsoring the request')
    gws_manager = models.CharField(max_length=1024,
                                   help_text='External person who will manage the GWS during its lifetime')
    gws_manager_email = models.EmailField(help_text="Email address")
    gws_manager_username = models.CharField(max_length=45, help_text="System username")
    description = models.TextField(null=True, blank=True, help_text='Text description of proposed GWS')
    requested_volume = FileSizeField(help_text="In bytes, but can be enetered using suffix e.g. '200TB'", default='0')
    # et_quota uses requested_volume as default unless other value specified: doesn't have to be the same)
    et_quota = FileSizeField(help_text="Elastic Tape quota. In bytes, but can be entered using suffix e.g. '200TB'",
                             default='0')
    backup_requirement = models.CharField(max_length=127, choices=settings.GWS_BACKUP_CHOICES, default='no backup')
    related_url = models.URLField(verify_exists=False, blank=True,
                                  help_text='Link to further info relevant to this GWS')
    expiry_date = models.DateField(default=datetime.now() + timedelta(days=2 * 365),
                                   help_text="date after which GWS will be deleted")  # approx 2 years from now
    request_type = models.CharField(max_length=127, choices=settings.GWS_REQUEST_TYPE_CHOICES, default='new',
                                    help_text='type of request')
    request_status = models.CharField(max_length=127, choices=settings.GWS_REQUEST_STATUS_CHOICES, default='pending',
                                      help_text='status of this request')
    gws = models.ForeignKey('GWS', blank=True, null=True, on_delete=models.SET_NULL,
                            help_text='GWS to which this request pertains')
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
                    name=self.gws_name,
                    path=self.path,
                    status='active',
                    internal_requester=self.internal_requester,
                    gws_manager=self.gws_manager,
                    gws_manager_email=self.gws_manager_email,
                    gws_manager_username=self.gws_manager_username,
                    description=self.description,
                    requested_volume=self.requested_volume,
                    et_quota=self.et_quota,
                    backup_requirement=self.backup_requirement,
                    related_url=self.related_url,
                    expiry_date=self.expiry_date,
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
                # self.gws.name = self.gws_name #DISABLED : presumably this never needs to change, once created.
                gws.path = self.path
                # gws.status = 'approved' #DISABLED : don't need to update this
                gws.internal_requester = self.internal_requester
                gws.gws_manager = self.gws_manager
                gws.gws_manager_email = self.gws_manager_email
                gws.gws_manager_username = self.gws_manager_username
                gws.description = self.description
                gws.requested_volume = self.requested_volume
                gws.et_quota = self.et_quota
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
            return u'<a href="/gwsrequest/%i/approve">approve</a> <a href="/gwsrequest/%i/reject">reject</a>' % (
            self.id, self.id)
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

    def volume_filesize(self):
        return filesize(self.requested_volume)

    volume_filesize.short_description = 'volume'

    def et_quota_filesize(self):
        return filesize(self.et_quota)

    et_quota_filesize.short_description = 'et_quota'


class GWS(models.Model):
    class Meta:
        verbose_name_plural = 'group workspaces'
        ordering = ['name']

    name = models.CharField(
            max_length=16,
            unique=True,
            validators=[
                RegexValidator(
                        regex=settings.GWS_NAME_REGEX,
                        message=u"Invalid name : this string will be used as a unix group name so must match the pattern %s" % settings.GWS_NAME_REGEX.pattern,
                )
            ]
            ,
            help_text='short string to be used as name for group workspace, also used for corresponsing unix group name. Must match pattern %s' % settings.GWS_NAME_REGEX.pattern
    )

    # Fields populated from GWS request
    path = models.CharField(max_length=2048, help_text='storage path to this group workspace excluding GWS name',
                            choices=settings.GWS_PATH_CHOICES)
    internal_requester = models.ForeignKey(User, help_text='CEDA person sponsoring the GWS')
    gws_manager = models.CharField(max_length=1024,
                                   help_text='External person who will manage the GWS during its lifetime')
    gws_manager_email = models.EmailField(help_text="Email address")
    gws_manager_username = models.CharField(max_length=45, help_text="System username")
    # et_quota uses requested_volume as default unless other value specified: doesn't have to be the same)
    et_quota = FileSizeField(help_text="In bytes, but can be entered using suffix e.g. '200TB'", default='0')

    description = models.TextField(null=True, blank=True, help_text='Text description of GWS')
    requested_volume = FileSizeField(help_text="In bytes, but can be entered using suffix e.g. '200TB'", default='0')
    backup_requirement = models.CharField(max_length=127, choices=settings.GWS_BACKUP_CHOICES, default='no backup')
    related_url = models.URLField(verify_exists=False, blank=True,
                                  help_text='Link to further info relevant to this GWS')
    expiry_date = models.DateField(help_text='Date after which GWS will be deleted')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')

    # Fields specific to GWS
    last_reviewed = models.DateTimeField(null=True, blank=True, help_text='date of last review')
    review_notes = models.TextField(blank=True, help_text='notes from reviews (append)')
    status = models.CharField(max_length=127, choices=settings.GWS_STATUS_CHOICES, default='active',
                              help_text='status of GWS')
    et_used = FileSizeField(help_text="In bytes, but can be entered using suffix e.g. '200TB'", default='0')

    def get_current_gwsrequest(self):
        '''Find the most recent GWSRequest which has this GWS as FK'''
        try:
            gws = GWSRequest.objects.filter(gws=self, request_status='approved').order_by('-timestamp')[0]
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
                gws_name=self.name,
                path=self.path,
                internal_requester=self.internal_requester,
                gws_manager=self.gws_manager,
                gws_manager_email=self.gws_manager_email,
                gws_manager_username=self.gws_manager_username,
                description=self.description,
                requested_volume=self.requested_volume,
                et_quota=self.et_quota,
                backup_requirement=self.backup_requirement,
                related_url=self.related_url,
                expiry_date=self.expiry_date,
                request_type='update',
                request_status='pending',
                gws=self,
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

    def requested_volume_filesize(self):
        return filesize(self.requested_volume)

    requested_volume_filesize.short_description = 'volume'

    def used_volume(self):
        if self.last_size() is not None:
            return self.last_size().size
        else:
            return 0

    def used_volume_filesize(self):
        return filesize(self.last_size().size)
        # return filesize(self.used_volume)

    used_volume_filesize.short_description = 'used'

    def et_quota_filesize(self):
        return filesize(self.et_quota)

    et_quota_filesize.short_description = 'ET quota'

    def et_used_filesize(self):
        return filesize(self.et_used)

    et_used_filesize.short_description = 'ET used'

    def df(self):
        '''Report disk usage of GWS by creating a GWSSizeMeasurement.'''
        gws_dir = os.path.join(self.path, self.name)
        if os.path.isdir(gws_dir):
            # find volume using du
            output = subprocess.Popen(['/usr/bin/df', '-k', gws_dir], stdout=subprocess.PIPE).communicate()[0]
            lines = output.split('\n')
            if len(lines) == 3:
                (fs, blocks, used, available, use, mounted) = lines[1].split()
            size = int(used) * 1024
            print "used %s, size %s" % (used, size)

            # find number of files
            p1 = subprocess.Popen(["find", gws_dir, "-type", "f"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            nfiles = p2.communicate()[0]

            gwssm = GWSSizeMeasurement(gws=self, date=datetime.utcnow(), size=size, no_files=int(nfiles))
            gwssm.save()
            self.used_volume = size
            self.forceSave()
        return

    def pan_df(self):
        '''Report disk usage of GWS by creating a GWSSizeMeasurement.'''
        gws_dir = os.path.join(self.path, self.name)
        if os.path.isdir(gws_dir):
            # find volume using pan_df
            output = subprocess.Popen(['/usr/local/bin/pan_df', '-k', gws_dir], stdout=subprocess.PIPE).communicate()[0]
            lines = output.split('\n')
            if len(lines) == 4:
                (blocks, used, available, use, mounted) = lines[2].split()
            size = int(used) * 1024

            gwssm = GWSSizeMeasurement(gws=self, date=datetime.utcnow(), size=size)
            gwssm.save()
            self.used_volume = size
            self.forceSave()
        return

    def last_size(self):
        """Return most recent GWSSetSizeMeasurement"""
        gwssms = GWSSizeMeasurement.objects.filter(gws=self).order_by('-date')
        if len(gwssms) > 0:
            return gwssms[0]
        else:
            return None

    last_size.allow_tags = True

    def action_links(self):
        return u'<a href="/gws/%i/df">df</a>' % self.id

    action_links.allow_tags = True
    action_links.short_description = 'actions'


class GWSSizeMeasurement(models.Model):
    '''Date-stampted size measurement of a GWS'''
    gws = models.ForeignKey('GWS', help_text="GWS that was measured")
    date = models.DateTimeField(default=datetime.now, help_text="Date and time of measurement")
    size = models.BigIntegerField(help_text="Size in bytes")  # in bytes
    no_files = models.BigIntegerField(null=True, blank=True, help_text="Number of files")

    def __unicode__(self):
        if self.no_files > 2000000:
            no_files = self.no_files / (1000 * 1000)
            funit = "Mfiles"
        else:
            no_files = self.no_files
            funit = "files"
        return u'%s %s %s %s' % (filesize(self.size), self.no_files, funit, self.date.strftime("%Y-%m-%d %H:%M"))


class VMRequest(models.Model):
    vm_name = models.CharField(max_length=127, help_text="proposed fully-qualified host name")  # TODO : need regex
    type = models.CharField(max_length=16, choices=settings.VM_TYPE_CHOICES,
                            help_text="Type of VM, see REF")  # TODO update REF
    operation_type = models.CharField(max_length=127, choices=settings.VM_OP_TYPE_CHOICES,
                                      help_text="Operation type of VM (dev, test, production, ...)")
    internal_requester = models.ForeignKey(User, help_text="CEDA person sponsoring the request",
                                           related_name='vmrequest_internal_requester_user')
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
                                          limit_choices_to={'id__in': settings.ADMIN_USERS_PATCH_RESPONSIBLE},
                                          )
    root_users = models.ManyToManyField(User, related_name='vmrequest_root_users_user')
    request_type = models.CharField(max_length=127, choices=settings.VM_REQUEST_TYPE_CHOICES, default='new')
    request_status = models.CharField(max_length=127, choices=settings.VM_REQUEST_STATUS_CHOICES, default='pending')
    vm = models.ForeignKey('VM', blank=True, null=True, on_delete=models.SET_NULL,
                           help_text='VM to which this request pertains')
    end_of_life = models.DateField(default=datetime.now() + timedelta(days=3 * 365))  # approx 3 years from now
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')

    # Set default ordering
    class Meta:
        ordering = ['vm_name']

    def __unicode__(self):
        return u'%s' % self.vm_name

    def action_links(self):
        if self.request_status == 'ceda pending':
            return u'<a href="/vmrequest/%i/approve">approve</a> <a href="/vmrequest/%i/reject">reject</a>' % (
            self.id, self.id)
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
        if self.request_type == 'new':  # and (self.vm is None or self.vm == ''):
            # make a new gws object, copying attributes from request           
            vm = VM.objects.create(
                    name=self.vm_name,
                    internal_requester=self.internal_requester,
                    description=self.description,
                    date_required=self.date_required,
                    type=self.type,
                    operation_type=self.operation_type,
                    cpu_required=self.cpu_required,
                    memory_required=self.memory_required,
                    disk_space_required=self.disk_space_required,
                    disk_activity_required=self.disk_activity_required,
                    mountpoints_required=self.mountpoints_required,
                    network_required=self.network_required,
                    os_required=self.os_required,
                    patch_responsible=self.patch_responsible,
                    status='created',
                    end_of_life=self.end_of_life,
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

    def coloured_vm_name(self):
        '''Colour the vm name if no dns entry found'''

        try:
            address = socket.gethostbyname(self.vm_name)
            return self.vm_name
        except:
            return ('<span style="color:red;">%s</span>' % self.vm_name)

    coloured_vm_name.short_description = 'VM name'
    coloured_vm_name.allow_tags = True


class VM(models.Model):
    name = models.CharField(max_length=127, help_text="fully-qualified host name", unique=True)  # TODO : need regex
    type = models.CharField(max_length=16, choices=settings.VM_TYPE_CHOICES,
                            help_text="Type of VM, see REF")  # TODO update REF
    operation_type = models.CharField(max_length=127, choices=settings.VM_OP_TYPE_CHOICES,
                                      help_text="Operation type of VM (dev, test, production, ...)")
    internal_requester = models.ForeignKey(User, help_text="CEDA person sponsoring the request",
                                           related_name='vm_internal_requester_user')
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
    patch_responsible = models.ForeignKey(User, related_name='vm_patch_responsible_user',
                                          limit_choices_to={'id__in': settings.ADMIN_USERS_PATCH_RESPONSIBLE},
                                          )
    root_users = models.ManyToManyField(User, related_name='vm_root_users_user')
    status = models.CharField(max_length=127, choices=settings.VM_STATUS_CHOICES, default='active')
    created = models.DateField(auto_now_add=True)
    end_of_life = models.DateField(default=datetime.now() + timedelta(days=3 * 365))  # 3 years from now
    retired = models.DateField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False, help_text='time last modified')

    # Set default ordering
    class Meta:
        ordering = ['name']

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
                vm_name=self.name,
                internal_requester=self.internal_requester,
                description=self.description,
                date_required=self.date_required,
                type=self.type,
                operation_type=self.operation_type,
                cpu_required=self.cpu_required,
                memory_required=self.memory_required,
                disk_space_required=self.disk_space_required,
                disk_activity_required=self.disk_activity_required,
                mountpoints_required=self.mountpoints_required,
                network_required=self.network_required,
                os_required=self.os_required,
                patch_responsible=self.patch_responsible,
                request_status='ceda pending',
                request_type='update',
                end_of_life=self.end_of_life,
                vm=self,
        )
        req.root_users = self.root_users.all()
        req.save()
        return req.id

    def update_link(self):
        return u'<a href="/vm/%i/update">update</a>' % self.id

    update_link.allow_tags = True

    def change_status(self):
        '''Cycle thro the available VM_STATUS_CHOICES (created / inuse / deprecated / retired)'''
        status_options = settings.VM_STATUS_CHOICES
        current_index = 0
        for i in status_options:
            # lookup position of current status value in tuple
            if (self.status == i[0]):
                break
            current_index += 1
        # select the next entry from the tuple
        try:
            self.status = status_options[current_index + 1][0]
        except IndexError:
            self.status = status_options[0][0]
        self.forceSave()

    def action_links(self):
        return u'<a href="/vm/%i/changestatus">change status</a>' % (self.id,)

    action_links.allow_tags = True
    action_links.short_description = 'actions'

    def coloured_vm_name(self):
        '''Colour the vm name if no dns entry found. Remove legacy prefix before checking'''
        try:
            address = socket.gethostbyname(self.name.replace('legacy:', ''))
            return self.name
        except:
            return ('<span style="color:red;">%s</span>' % self.name)

    coloured_vm_name.short_description = 'VM name'
    coloured_vm_name.allow_tags = True


class ServiceKeyword(models.Model):
    keyword = models.CharField(max_length=30)

    def __unicode__(self):  # __unicode__ on Python 2
        return self.keyword

    class Meta:
        ordering = ('keyword',)


class NewService(models.Model):
    '''Software-based service'''
    # host = models.ManyToManyField(Host, help_text="Host machine on which service is deployed", null=True, blank=True)
    host = models.ForeignKey(VM, help_text="Host machine on which service is deployed", null=True, blank=True)
    name = models.CharField(max_length=512, help_text="Name of service")

    status = models.CharField(
            max_length=50,
            choices=(
                ("pre-production", "Pre-production"),
                ("production", "Production"),
                ("decomissioned", "Decomissioned"),
                ("other", "Other (e.g. temporarily offline)")
            ),
            default="to be reviewed"
    )

    description = models.TextField(blank=True, help_text="Longer description if needed")
    documentation = models.URLField(verify_exists=False, blank=True,
                                    help_text="URL to documentation for service in opman")
    ##    externally_visible = models.BooleanField(default=False, help_text="Whether or not this service is visible outside the RAL firewall")

    visibility = models.CharField(
            max_length=50,
            choices=(
                ("public", "Public"),
                ("internal", "Internal only"),
                ("restricted", "Restricted external access"),
            ),
            default="public",
            help_text="Intended visibility when operational"
    )

    service_manager = models.ForeignKey(Person, null=True, blank=True, related_name='software_manager',
                                        help_text="CEDA person who looks after this service")

    owner = models.ForeignKey(Person, null=True, blank=True, related_name='owner', help_text="Owner of this service")

    last_reviewed = models.DateField(null=True, blank=True, help_text="Date of last review")
    review_status = models.CharField(
        max_length=50,
        choices=(
            ("to be reviewed","To be reviewed"),
            ("passed", "Passed"),
            ("passed with issues", "Passed with issues"),
            ("failed", "Failed"),
            ("failed with minor issues", "Failed with minor issues"),

        ),
        default="to be reviewed"
    )

    review_info = models.TextField(blank=True,
                                   help_text="Information from reviews. Please date and put most recent information at the top.")

    keywords = models.ManyToManyField(ServiceKeyword, blank=True, null=True,
                                      help_text="Select any keywords that apply to this service")

    ports = models.CharField(max_length=100, blank=True, help_text='External open ports required by this service')

    class Meta:
        verbose_name = "Service"

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
            summary = summary[0:SummaryLength - 1] + '...'

        return summary

    def documentationLink(self):

        return self.documentation
