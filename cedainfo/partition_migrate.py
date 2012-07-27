# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


# usage: partition_migrate.py <from_partition> <to_partition>
# mark a whole partition for migration to a new one
# both partition need to exist in the data base
# No auditing is done on the datasets


if __name__=="__main__":
    
    from_partition, to_partition = sys.argv[1:3]
    
    print from_partition, to_partition
    
    from_partition = Partition.objects.filter(mountpoint=from_partition)[0]
    to_partition = Partition.objects.filter(mountpoint=to_partition)[0]
    
    print from_partition, to_partition
    
    filesets = FileSet.objects.filter(partition=from_partition, storage_pot_type = 'archive')
    
    from_partition.status = 'Migrating'
    from_partition.save()
    to_partition.status = 'Closed'
    to_partition.save()

    	
    for fs in filesets:
        print " - Marking %s for migration to %s" % (fs, to_partition)
	fs.migrate_to = to_partition
        fs.save()
        fs.migrate_spot(do_audit=False)
	
	 
 
