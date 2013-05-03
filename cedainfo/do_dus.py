import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import FileSet, Partition


def usage():
    print "Cron script to du all filesets"
    print "Usage: %s" % sys.argv[0]
    print



def do_dus():
    # do a file set measurement for all the filesets which have not had it done in the last 10 days
    filesets = FileSet.objects.all()
    for f in filesets:
        fssm = f.last_size() 
	if fssm == None:
            print "Doing du of fileset: %s ... [FIRST TIME] " % f 
            f.du()
	    print "            ... Done"
	    continue
	
	if datetime.now() - fssm.date > timedelta(days=10): 
            print "Doing du of fileset: %s ... " % f 
            f.du()
	    print "            ... Done"
	else: 
	    print "SKIPP:%s " % f,

def do_dfs():
    # do df for all partitions
    partitions = Partition.objects.all()
    for p in partitions:
        print "Doing df of partition: %s " % p
        p.df()

def notify():
    # do a file set measurement for all the filesets which have not had it done in the last 10 days
    filesets = FileSet.objects.all()
    for f in filesets:
        fssm = f.last_size() 
	if fssm == None: continue
 	
	# if over allocated...
	if f.overall_final_size < fssm.size:
	    print "%s over size" %f 
	    responsible = f.responsible()
	    if responsible == None: continue
	    email = responsible.email
	    subject = "Alocation reached for %s" % (f.logical_path,)
	    msg = """The Allocation for %s has been reached. 
	    Please review the allocation (http://cedadb.badc.rl.ac.uk/admin/cedainfoapp/fileset/%s)
	    """ % (f.logical_path, f.pk)
            server = smtplib.SMTP('localhost')
            server.sendmail('sam.pepler@stfc.ac.uk', (email,), msg)
            server.quit()


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
    
 
    # do file set measurements
    do_dus()
    # do dfs
    #do_dfs()
    #
    notify()
    
