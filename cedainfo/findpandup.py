# script to remove files from partitions that have been migrated
# Sam Pepler 2013-01-02

# This script finds duplicate spot data on panasis storage.
# This is to enable a tidy up of things that have been copied during migration, but were migrated to a differnent 
# bit of the panasis storage.





import getopt, sys, pickle
import os, errno, re, time

from django.core.management import setup_environ
import settings
setup_environ(settings)
import filecmp

from cedainfoapp.models import *


if __name__=="__main__":
    
    # for each pan partition...
    pans = []
    archvols = ('/datacentre/archvol', '/datacentre/archvol2')
    for a in archvols:
        pan_dirs = os.listdir(a)
        for p in pan_dirs:
            pans.append(os.path.join(a, p))

    for p in pans:
        #print p
        # for each (potential) spotname
        archivename = os.path.join(p, 'archive')
        if not os.path.exists(archivename): continue
        spots = os.listdir(archivename)
        for spotname in spots:
            filesets = FileSet.objects.filter(storage_pot=spotname, storage_pot_type = 'archive')
            pan_spotpath = os.path.join( archivename, spotname)
            if len(filesets)==0: 
                print "** %s no matching fileset- why is it here - remove?\n" % pan_spotpath
                continue
            if len(filesets)>1:
                #print "** %s more than 1 matching fileset- skip" %spotname
                continue
            fileset = filesets[0]
            current_spotpath = fileset.storage_path()
            if fileset.partition.mountpoint[0:12] != '/datacentre/':
                #print "** current storage is not panasas - %s" % current_spotpath
                continue
            if pan_spotpath == current_spotpath:
                #print "** %s pan spot and current spot are the same - skip" %spotname
                continue

            print "------- %s redundent? (current spot %s)" % (pan_spotpath, current_spotpath)
            os.system('ls -l %s' % fileset.logical_path)
            print  


    



	
	 
 
