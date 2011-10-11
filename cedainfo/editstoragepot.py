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
    if fs.storage_pot == None or fs.storage_pot == '':
        print "fileset has no storage pot set"
        fs.storage_pot = "archive/spot-%s" % fs.id
        fs.save()         
    else: 
        fs.storage_pot = "archive/spot-%s" % fs.id
        print "fileset already has storage pot set"



