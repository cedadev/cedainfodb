# script to remove files from partitions that have been migrated
# Sam Pepler 2012-11-19

# This script goes through all data on partitions marked as migrating. 
# It checks that the spots it can see in the archive directory.
# If a spot has one matching fileset and that primary fileset is on a diffent partion then
# it checks to see if a storage-d backup exists.
# If the backup exists it checks all files in the fileset to see if they are the same as the
# current one. If they are the same then the file is removed. 

# If the script is stopped it records the partition and fileset so that restart is from 
# where it left off. Logging is done to trace what has happened and a summary of 
# volume and number of files is recorded. 

# A runfile is used to record the config and status of a run. 
# This file is updated at the end of each fileset to be restartable.  



import getopt, sys, pickle
import os, errno, re, time

from django.core.management import setup_environ
import settings
setup_environ(settings)
import filecmp

from cedainfoapp.models import *


class TidyRun:


    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(filename):
            # make new run
            self.state = {'files_deleted':0, 'links_deleted':0, 'dirs_deleted':0, 'files_checked':0, 'vol_deleted':0, 
                     'filesets_checked':0, 'partitions_checked':0}
            self.LOG = open("%s.log" % filename, 'a')
            self.state['current_partition_index'] = 0
            self.state['current_fileset']=None
            self.state['run_start'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.LOG.write("==== started: %s\n" % self.state['run_start'])
            self.state['partitions_todo'] = []
            for p in Partition.objects.filter(status='Migrating').order_by('mountpoint'): 
                self.state['partitions_todo'].append(p.pk)
            self.partition = Partition.objects.get(pk=self.state['partitions_todo'][self.state['current_partition_index']])
            self.write_runfile()
            
        else: 
            f = open(filename)
            self.state = pickle.load(f)
            self.LOG = open("%s.log" % filename, 'a')
            self.state['reload'] =  time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.partition = Partition.objects.get(pk=self.state['partitions_todo'][self.state['current_partition_index']])            
            self.write_runfile()
            
    def write_runfile(self):
        output = open(self.filename, 'wb')
        pickle.dump(self.state, output)
        output.close()

    def next_partition(self):
        self.partition = Partition.objects.get(pk=self.state['partitions_todo'][self.state['current_partition_index']])
        self.state['current_partition_index'] = self.state['current_partition_index'] + 1
        if self.state['current_partition_index'] >= len(self.state['partitions_todo']): 
            self.partition = None
        else:    
            self.partition = Partition.objects.get(pk=self.state['partitions_todo'][self.state['current_partition_index']])
        self.write_runfile()
    
    def run(self):
        while 1:
           self.check_partition()
           self.next_partition()
           if self.partition == None: return
    
    def check_partition(self):
        partition  = self.partition
        old_archivedir = os.path.join(partition.mountpoint,'archive')
        spots = os.listdir(old_archivedir)

        print spots

        for s in spots:
            filesets = FileSet.objects.filter(storage_pot=s, storage_pot_type = 'archive')
            old_spotpath = os.path.join( old_archivedir, s)
            if len(filesets)==0: 
                self.LOG.write("** %s no matching fileset- skip\n" %s)
                continue
            if len(filesets)>1:
                self.LOG.write("** %s more than 1 matching fileset- skip\n" %s)
                continue
            print filesets
            fileset = filesets[0]
            new_spotpath = fileset. storage_path()
            self.LOG.write("old path %s was migrated to %s\n" % (old_spotpath, new_spotpath))
            if old_spotpath == new_spotpath:
                self.LOG.write("** %s old and new the same - skip\n" %s)
                continue

            # latest size measurements
            size = fileset.last_size()
            self.LOG.write("%s\n" %size)
        

            # storage-d backup size
            #backup= fileset.backup_summary()
            #self.LOG.write("%s\n" %backup)

            # crude storage-d size finder via screen scrape... 
            #url = 'http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_Summary.php?%s' % s
            #import urllib2
            #f = urllib2.urlopen(url)
            #for i in range(7): f.readline()
            #backup = f.readline()
            #backup = backup.split('<td')
            #m = re.search('>(\d*)</a></td>', backup[3])
            #backupfiles = m.group(1)
            #if backupfiles !='': backupfiles = int(backupfiles)
            #else: backupfiles = 0 
            #print backupfiles, size.no_files

            # skip if no backup         
            #if backupfiles == size.no_files: print "**** exactly the right size backup ****"
            #elif backupfiles > 0: print "++++ some backup done ++++"
            #else: 
            #    print "no backup done - skip"
            #    continue 

            #check_del(old_spotpath, new_spotpath)
        


    def check_del(self, old, new):
        files = os.listdir(old)
        for f in files:
            oldpath = os.path.join(old, f)
            newpath = os.path.join(new, f)
            self.status['files_checked'] += 1 

            if os.path.islink(oldpath): 
                if os.path.islink(newpath): 
                    #os.unlink(oldpath)
                    self.status['links_deleted'] += 1 
                    self.LOG.write("RMLINK: %s\n" % oldpath)

            elif os.path.isdir(oldpath): 
                check_del(oldpath, newpath)
                nfiles =  len(os.listdir(oldpath))
                if nfiles == 0: 
                    #os.rmdir(oldpath)
                    self.status['dirs_deleted'] += 1 
                    self.LOG.write("RMDIR: %s\n" % oldpath)

            elif os.path.isfile(oldpath): 
                same = filecmp.cmp(oldpath, newpath)        
                if same: 
                    #os.unlink(oldpath)
                    self.status['files_deleted'] += 1 
                    self.LOG.write("DEL: %s\n" % oldpath)

            else: 
                self.LOG.write("IREGULAR FILE: %s\n" % oldpath)
                continue 
            


if __name__=="__main__":
    

    T = TidyRun('/tmp/samsrun')

    T.write_runfile()

   
    T.run()



	
	 
 
