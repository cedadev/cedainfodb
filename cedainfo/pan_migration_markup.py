# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


# script to list a prioritiesd set of partitions to migrage 

if __name__=="__main__":

    # set up list of panasas volumes to allocate to 
    partitions = Partition.objects.exclude(status='retired').exclude(mountpoint__startswith='/datacentre')
    
    for p in partitions:
    
        print "====> Partition %s" % p
        filesets = FileSet.objects.filter(storage_pot_type = 'archive')
	
        for fs in filesets: 
             print " -- Fileset %s" % fs
	


