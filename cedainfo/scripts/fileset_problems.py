import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib


from cedainfoapp.models import *


def audit_problems():
    audits = Audit.objects.filter(auditstate='corrupt')
    for a in audits:
        print_msg(a, "Audit detected corruption")

    audits = Audit.objects.filter(auditstate='error')
    for a in audits:
        print_msg(a, "Audit detected error")

    time_threshold = datetime.now() - timedelta(days=5)
    audits = Audit.objects.filter(auditstate='started', starttime__lt=time_threshold)
    for a in audits:
        print_msg(a, "Audit started but not finished")

def partition_problems():
    partitions = Partition.objects.exclude(status="Retired")
    # list overfilled partitions
    for p in partitions:
        if 100.0* p.used_bytes/(p.capacity_bytes+1) > 98.0: 
            print_msg(p, "Partition over filled")
    # list overallocated partitions
    for p in partitions:
        allocated = p.allocated() + p.secondary_allocated()
        if 100.0* allocated/(p.capacity_bytes+1) > 87.0:
            print_msg(p, "Partition overallocated")

def fileset_problems():
    
    # Look at filesets for over allocation
    filesets = FileSet.objects.all()
    msg = ''
    today = datetime.now()

    for f in filesets:
        fssms = FileSetSizeMeasurement.objects.filter(fileset=f).order_by('-date')
        first_time = (len(fssms) == 0) 
        
        if not first_time:
            last_fssm = fssms[0]

            too_many_files =  last_fssm.no_files > 5000000
            too_big = f.overall_final_size > 30000000000000
            over_alloc = last_fssm.size > f.overall_final_size

            changing = False # assume static and look for changes
            npoints=0
            for fssm in fssms[1:]:                    # loop over fileset measurements from second to last...
                if datetime.now() - fssm.date > timedelta(days=120): break  # only look in past 120 days
                npoints +=1         # number of points within 120 days
                if fssm.size != last_fssm.size or fssm.no_files != last_fssm.no_files:
                    changing =True
            if npoints <2: changing = True    # if we have one or less points in the 120 days then assume changing.
   
            if len(fssms) < 10 and not f.sd_backup: print_msg(f, "Newish and not marked for backup.")
        else: 
            print_msg(f, "Not measured yet")

        if too_many_files: print_msg(f, "Too Many files %s")
        if too_big: print_msg(f, "Too Big")
        if over_alloc: print_msg(f, "Over allocation")

        if f.sd_backup:
            backup_processed =  f.sd_backup_process_log()[-13:-5]
            if backup_processed[:3] == "Not": print_msg(f, "Not processed for backup yet")
            else:
                date = datetime(int(backup_processed[:4]), int(backup_processed[4:6]), int(backup_processed[6:8]))
                if today - date > timedelta(days=10):
                    print_msg(f, "Not backed up for over 10 days")        
    
def print_msg(obj, msg):
    url = "http://cedadb.ceda.ac.uk/admin/cedainfoapp/"
    #print obj._meta
    #print dir(obj._meta)
    obj_type = obj._meta.object_name.lower()
    url += "%s/%s" % (obj_type, obj.pk)
    print "%s [%s] %s" % (url, msg, obj)

def run ():
    fileset_problems()
    audit_problems()
    partition_problems()    
