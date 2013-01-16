# script to monitor the partition_check_and_remove.py script
# Sam Pepler 2013-01-16

import sys, pickle


if __name__=="__main__":
    filename = sys.argv[1]
    f = open(filename)
    state = pickle.load(f)
    print "------------------------"
    print "Run stated: %s (restarted: %s)" % (state['run_start'],state['reload'])
    print "files checked: %s" % (state['files_checked'],)
    print state

#'links_deleted', 'dirs_deleted', 'partitions_checked', 'files_deleted', , 
#'', 'vol_deleted', 'filesets_checked', 'files_checked'

	
	 
 
