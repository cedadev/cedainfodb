import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import FileSet, Partition, Audit


def usage():
    print "Cron script to du audit next fileset"
    print "Usage: %s <N>" % sys.argv[0]
    print " N= number of audits to do"
    print

def pick_audit():
    # pick an audit to do: 
    filesets = FileSet.objects.filter(storage_pot_type='archive', storage_pot__isnull=False)
    fileset_to_audit = None
    oldest_audit = datetime.datetime.utcnow()
    for f in filesets:
        last_audit = f.last_audit()
        # if no audit done before then use this one
	if last_audit == None:
	    return f    
        # skip if last audit not an analysed state then skip
        if last_audit.auditstate != 'analysed':    
            print "Ignore - audit got an error" 
            continue
        # see if this is the oldest audit
        print  last_audit.starttime , oldest_audit, last_audit.starttime < oldest_audit
	if last_audit.starttime < oldest_audit:
	    oldest_audit = last_audit.starttime
	    fileset_to_audit = f
    return fileset_to_audit	        
            	  	
def do_audit(f):
    print "Doing audit of fileset: %s ... " % f 
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

