# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


if __name__=="__main__":

    logical_path = sys.argv[1]
    filesets = FileSet.objects.filter(logical_path = logical_path)
    fs = filesets[0] 
    print "found fileset %s" % fs

    migration_part = sys.argv[2]
    migration_part = Partition.objects.filter(mountpoint = migration_part ) 
    migration_part = migration_part[0]

    print "seting migration partition to %s" % migration_part

    fs.migrate_to = migration_part
    fs.save()        


