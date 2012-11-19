# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno, re

from django.core.management import setup_environ
import settings
setup_environ(settings)
import filecmp

from cedainfoapp.models import *


# usage: partition_migrate.py <from_partition> <to_partition>
# mark a whole partition for migration to a new one
# both partition need to exist in the data base
# No auditing is done on the datasets


def check_del(old, new):
    files = os.listdir(old)
    for f in files:
        oldpath = os.path.join(old, f)
        newpath = os.path.join(new, f)
        if os.path.islink(oldpath): continue
        elif os.path.isdir(oldpath): check_del(oldpath, newpath)
        elif os.path.isfile(oldpath): 
             pass
             print "cf %s to %s" % (oldpath, newpath)
             print filecmp.cmp(oldpath, newpath)        
        else: continue 
            
    # remove empty dir
    for f in files:
        oldpath = os.path.join(old, f)
        newpath = os.path.join(new, f)
        if os.path.islink(oldpath): continue
        elif os.path.isdir(oldpath):
             nfiles =  len(os.listdir(oldpath))
             if nfiles == 0: print "os.rmdir(%s)" % oldpath 
        else: continue 




if __name__=="__main__":
    
    partition = sys.argv[1]
    
    print partition
    
    partition = Partition.objects.filter(mountpoint=partition)[0]
    
    print partition
    old_archivedir = os.path.join(partition.mountpoint,'archive')
    spots = os.listdir(old_archivedir)

    print spots
    
    for s in spots:
        filesets = FileSet.objects.filter(storage_pot=s, storage_pot_type = 'archive')
        old_spotpath = os.path.join( old_archivedir, s)
        if len(filesets)==0: 
            print "** %s no matching fileset- skip" %s
            continue
        if len(filesets)>1:
            print "** %s more than 1 matching fileset- skip" %s
            continue
        print filesets
        fileset = filesets[0]
        new_spotpath = fileset. storage_path()
        print "old path %s was migrated to %s" % (old_spotpath, new_spotpath)
        if old_spotpath == new_spotpat:
            print "** %s old and new the same - skip" %s
            continue

        # latest size measurements
        size = fileset.last_size()
        print size
        

        # crude storage-d size finder via screen scrape... 
        url = 'http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_Summary.php?%s' % s
        import urllib2
        f = urllib2.urlopen(url)
        for i in range(7): f.readline()
        backup = f.readline()
        backup = backup.split('<td')
        m = re.search('>(\d*)</a></td>', backup[3])
        backupfiles = m.group(1)
        if backupfiles !='': backupfiles = int(backupfiles)
        else: backupfiles = 0 
        print backupfiles, size.no_files

        # skip if no backup         
        if backupfiles == size.no_files: print "**** exactly the right size backup ****"
        elif backupfiles > 0: print "++++ some backup done ++++"
        else: 
            print "no backup done - skip"
            continue 

        check_del(old_spotpath, new_spotpath)
        

    #from_partition.status = 'Migrating'

	
	 
 
