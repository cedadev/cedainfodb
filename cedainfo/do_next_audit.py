import getopt, sys
import os, errno
import datetime
from datetime import timedelta
import smtplib

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import FileSet, Partition, Audit


def usage():
    print "Cron script to du audit next fileset"
    print "Usage: %s" % sys.argv[0]
    print



def pick_audit():
    # pick an audit to do: 
    # 1) any fileset that has no privious audit
    # 2) any fileset that has 
    filesets = FileSet.objects.all()
    fileset_to_audit = None
    oldest_audit = datetime.datetime.now()
    for f in filesets:
        last_audit = f.last_audit() 
        
	if last_audit == None:
	    print 'Last Audit: %s' % last_audit
	    return f
        
	if last_audit.starttime < oldest_audit: 
	    # don't start one for a fileset that's already going
	    if last_audit.auditstate == "started":
	        print " --- Already started" 
	        continue
	    oldest_audit = last_audit.starttime
	    fileset_to_audit = f

    return fileset_to_audit	    
    
            	  	
def do_audit(f):

    print "Doing audit of fileset: %s ... [FIRST TIME] " % f 

    audit=Audit(fileset=f)
    audit.start()
    print "            ... Done"




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
    
    fileset = pick_audit()
    print fileset 
    # do audit
    if fileset != None: do_audit(fileset)
