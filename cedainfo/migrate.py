import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *

def usage():
    print "Migration script for filesets"
    print "Usage: %s" % sys.argv[0]
    print



if __name__=="__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:p:n")
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    fileset=''
    partition='' 
    do_audit = True   
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-f", "--fileset"):
            fileset = a 
        elif o in ("-p", "--partition"):
            partition = a 
        elif o in ("-n", "--noaudit"):
            do_audit = False 
        else:
            assert False, "unhandled option"

    # select filesets to migrate
    filesets = FileSet.objects.filter(migrate_to__isnull=False)
    if partition: filesets = filesets.filter(partition__mountpoint=partition)
    if fileset: filesets = filesets.filter(logical_path=fileset)
    
    
    print "filessets to migrate: %s" % filesets

    for fs in filesets:
        print "MIGRATING %s" % (fs.logical_path) 
        print "     %s -> %s" % (fs.partition, fs.migrate_to) 
        fs.migrate_spot(do_audit=do_audit)
 

