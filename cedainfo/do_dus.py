import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *

def usage():
    print "Cron script to du all filesets"
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
        fssm = FileSetSizeMeasurement.objects.filter(fileset=f).order_by('-date')
	if len(fssm) == 0:
            print "Doing du of fileset: %s ... [FIRST TIME] " % f 
            f.du()
	    print "            ... Done"
	    continue
	
	lastdu = fssm[0].date
	if datetime.now() - lastdu > timedelta(days=10): 
            print "Doing du of fileset: %s ... " % f 
            f.du()
	    print "            ... Done"
	else: 
	    print "      SKIPPIG %s (done in last 10 days)" % f
 

