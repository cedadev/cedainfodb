# script to look at storage state
# Sam Pepler 2012-09-14

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import *


if __name__=="__main__":

    # script to tidy
    script=''

    partitions = Partition.objects.filter(status='Closed')
    for p in partitions:
        if p.mountpoint=='/disks/drizzle2': continue
        if p.mountpoint=='/disks/drizzle1': continue
        print(("************** %s **********" % p))
        filesets = FileSet.objects.filter(partition=p)
        for fs in filesets:
            # for each fileset check spot and link exists
            spot_path = fs.storage_path()
            if not os.path.isdir(spot_path): print(("   FILESET ERROR -> %s is not a directory" % spot_path))
            if not os.path.islink(fs.logical_path): print(("   FILESET ERROR -> %s is not a link" % fs.logical_path))
            elif os.readlink(fs.logical_path) != spot_path: print(("   FILESET ERROR  %s does not link to %s" % (fs.logical_path, spot_path)))
 
           # print "    -> contains fileset %s" % fs

        # check out stuff in archive directory
        archive_path = "%s/archive" % p.mountpoint        
        if os.path.exists(archive_path): 
            spots = os.listdir(archive_path)
            #print spots
            if '.checksums' in spots: spots.remove('.checksums')
            if '.summary' in spots: spots.remove('.summary')

            for fs in filesets:
                if fs.storage_pot in spots: spots.remove(fs.storage_pot)
            if len(spots)>0: print(("ODD spots> ", spots)) 
            
            for s in spots: 
                dupfilesets = FileSet.objects.filter(storage_pot=s)
                if len(dupfilesets) == 0: print((" !! %s not found elsewhere!" % s))
                for dup in dupfilesets:
                    print((" ==  %s looks like dup of %s (%s)" % (s, dup, dup.storage_path())))
                    print("To remove dup run:")
                    print(("rm -rf %s/archive/%s" %(p.mountpoint, s)))
                    # if migrate.txt file and on pan then its definitly safe to delete
                    if os.path.exists("%s/archive/%s/MIGRATED.txt" %(p.mountpoint, s)) and p.mountpoint[0:12] == '/datacentre/': script += "rm -rf %s/archive/%s\n" %(p.mountpoint, s)
                          
                    
    print('\n\n\n\n\n')
    print(script)

