import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from audit.models import *
from cedainfoapp.models import *

def usage():
    print "Migration script for filesets"
    print "Usage: %s" % sys.argv[0]
    print



if __name__=="__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"
    
    filesets = FileSet.objects.all()
    for f in filesets:
         if f.migrate_to:
	    print "MIGRATING %s" % (f.logical_path) 
	    print "     %s -> %s" % (f.partition, f.migrate_to) 
	    f.migrate_spot()
 

