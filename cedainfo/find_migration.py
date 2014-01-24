# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


if __name__=="__main__":


    migration_part = sys.argv[1]
    migration_part = Partition.objects.filter(mountpoint = migration_part ) 
    migration_part = migration_part[0]

    print "using migration partition: %s" % migration_part



    
    margin=0.85

    for part in Partition.objects.filter(status='Closed', mountpoint__startswith='/datacentre'):
        alloc = part.allocated()
        if margin* part.capacity_bytes < alloc:
            print part
            migration_size=alloc - margin*part.capacity_bytes
            filesets = FileSet.objects.filter(partition=part).order_by('overall_final_size')
            fs_list = []
            fs_list_size = 0 
            if len(filesets) == 1: 
                print "don't move filesets on their own: %s" % filesets[0]
                continue
            for fs in filesets:
                fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')
                if len(fssms) > 0:
                    fs_size= fssms[0].size
                    fs_number = fssms[0].no_files 
                if fs_size > 3000000000000: continue # don't move filesets currently bigger than 3TB 
                if fs.overall_final_size > 10000000000000: continue # don't move filesets bigger than 1TB 
                if fs_number > 50000: continue # don't move filesets bigger than 50000 files 
                if fs_list_size < migration_size: 
                    fs_list.append(fs)
                    fs_list_size += fs.overall_final_size
                else:  
                    break
            
            if len(fs_list) ==0:
                print  "no good moves"
                continue 
        #    print "best move: %s" % fs_list
            best = fs_list[-1]
            print "%4.2f TB (need to move %4.2f TB) " % (fs_list_size*1e-12, migration_size*1e-12)
            print "best start with %s (%4.2f TB)"   % (best, best.overall_final_size*1e-12)
            ans = raw_input("Mark for migration? (y/n)> ")
            if ans == 'y':
                print "Marked %s to migrate to %s" % (best, migration_part)
                best.migrate_to = migration_part
                best.save()        





