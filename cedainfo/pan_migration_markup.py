# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


# script to list a prioritiesd set of partitions to migrage to panasas 

if __name__=="__main__":

    # set up list of panasas volumes to allocate to 
    partitions = Partition.objects.exclude(status='retired').exclude(mountpoint__startswith='/datacentre')
    
    for p in partitions:
    
        filesets = FileSet.objects.filter(partition=p, storage_pot_type = 'archive')
	

        p.score = 0
	if len(filesets) >0:
	    p.score = 1
	    
	    allocated = p.allocated()
	    capacity = p.capacity_bytes
	    used_bytes = p.used_bytes
	    
	    p.newcapacity = allocated * 1.3 /(1024*1024*1024*1024)
	    
            overfull = (used_bytes  > 0.99 * capacity)
	    if overfull: p.score += 2
	    overalloc = (allocated > capacity)
	    if overalloc: p.score += 1
	    
	    cmip5 =  False
	    neodc = False

            for fs in filesets: 
		if fs.logical_path[0:11] == '/badc/cmip5': cmip5=True
		if fs.logical_path[0:7] == '/neodc/': neodc=True
			    
	    if cmip5: p.score += 1
	    if neodc: p.score += 1

	if p.mountpoint == '/disks/damp1': p.score = 0
	if p.mountpoint == '/disks/willow1': p.score += 2
	if p.mountpoint == '/disks/willow2': p.score += 2
	if p.mountpoint == '/disks/caucasus1': p.score += 1
	if p.mountpoint == '/disks/caucasus2': p.score += 1
	
    sorted_partitions = sorted(partitions, key=lambda x: (x.score, x.mountpoint), reverse=True)
    
    
    pannumber = 5
    # print Pananas volumes to make
    print "# Pananas volumes to make"
    for p in sorted_partitions:
        if p.score >0 : 
	    print  '/datacentre/archvol/pan%s %2.2f TB' % (pannumber, p.newcapacity)
            pannumber += 1
    print
    print 

    # print Pananas copy operations
    print "# Pananas copy operations"
    pannumber = 5
    for p in sorted_partitions:
        if p.score >0 : 
	    print  '%s:%s/archive /datacentre/archvol/pan%s/archive ' % (p.host.hostname, p.mountpoint, pannumber)
            pannumber += 1
	    
    
    
    
    
    
    
