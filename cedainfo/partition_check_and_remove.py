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
            self.LOG = open("%s.log" % filename, 'w')
            self.state['current_partition_index'] = 0
            self.state['current_fileset']=None
            self.state['run_start'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.LOG.write("==== started: %s\n" % self.state['run_start'])
            self.state['partitions_todo'] = []
            for p in Partition.objects.filter(status='Migrating').order_by('-capacity_bytes','mountpoint'): 
                self.state['partitions_todo'].append(p.pk)
            print self.state['partitions_todo']
            print self.state['current_partition_index']
            self.partition = Partition.objects.get(pk=self.state['partitions_todo'][self.state['current_partition_index']])
            self.write_runfile()
            
        else: 
            f = open(filename)
            self.state = pickle.load(f)
            self.LOG = open("%s.log" % filename, 'a')
            if self.state['current_partition_index'] >= len(self.state['partitions_todo']):
                raise Exception("Old runfile says its finished") 
            self.partition = None
            self.state['reload'] =  time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.partition = Partition.objects.get(pk=self.state['partitions_todo'][self.state['current_partition_index']])            
            self.write_runfile()
            
    def write_runfile(self):
        output = open(self.filename, 'wb')
        pickle.dump(self.state, output)
        output.close()

    def log(self,msg):
        self.LOG.write("%s\n" % msg)
        self.LOG.flush()
        

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
           try: 
               self.check_partition()
           except: 
               pass
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
                self.log("** %s no matching fileset- skip" % s)
                continue
            if len(filesets)>1:
                self.log("** %s more than 1 matching fileset- skip" %s)
                continue
            print filesets
            fileset = filesets[0]
            new_spotpath = fileset. storage_path()
            self.log("old path %s was migrated to %s" % (old_spotpath, new_spotpath))
            if old_spotpath == new_spotpath:
                self.log("** %s old and new the same - skip" %s)
                continue

            # latest size measurements
            size = fileset.last_size()
            self.log("%s" %size)
            if size != None: lastfiles = size.no_files
            else: 
                self.log("** %s no file size measurement - skip" %s)
                continue

            # storage-d backup size
            #backup= fileset.backup_summary()
            #self.LOG.write("%s\n" %backup)

            # crude storage-d size finder via screen scrape... 
            url = 'http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_Summary_XML.php?%s' % s
            import urllib2
            f = urllib2.urlopen(url)
            backup = f.read()
            m = re.search('<total_volume>(.*)</total_volume><total_file_count>(.*)</total_file_count>', backup)
            try:
                backupsize, backupfiles =  int(m.group(1)), int(m.group(2))
            except:
                backupsize, backupfiles = 0, 0
            if backupfiles >= 0.95*size.no_files: print "OK -- ",backupfiles, size.no_files
            else: print " *** ",backupfiles, size.no_files 

            # skip if no backup         
            if backupfiles >= 0.95*size.no_files: print "**** backup with more files done ****"
            #elif backupfiles > 0: print "++++ some backup done ++++"
            else: 
                self.log("** %s no backup suffience on storage-D  (storage-d:%s, measured:%s)- skip" %(s,backupfiles, size.no_files))
                continue 

            self.check_del(old_spotpath, new_spotpath)
            
            # record that a fileset has been checked
            self.state['filesets_checked'] += 1 
            self.write_runfile()

        # record that a partition has been checked
        self.state['partitions_checked'] += 1 
        self.write_runfile()

            

    def check_del(self, old, new):
        # check files are ok to remove         
        # if all files are checked and ok return True 

        # check file present?
        # use a MIGRATED.txt file to see if this dir and it's subdirectories have been checked
        if os.path.exists(os.path.join(old, 'MIGRATED.txt')): 
            self.log("already migrated - has a MIGRATED.txt file (skip): %s" % old)
            return True

        # if can't write in the dir then skip this one because it will not be possible to record it as checked.
        if not os.access(old, os.W_OK):
            self.log("Can't write to this dir (skip): %s" % old)
            return False

        files = os.listdir(old)
        nfiles = len(files)

        for f in files:
            oldpath = os.path.join(old, f)
            newpath = os.path.join(new, f)
            self.state['files_checked'] += 1 
            
            # cmip5 frequenty updated files
            if f[0:5] == "COPY_" or f==".ftpaccess" or f==".mnj_wrk":
                    self.state['files_deleted'] += 1 
                    self.log("IGNORE: %s " % oldpath)
                    nfiles -= 1
                    continue

            if not os.path.lexists(newpath):
                self.log("MISSING: %s" % newpath)
                continue

            if os.path.islink(oldpath): 
                if os.path.islink(newpath): 
                    self.state['links_deleted'] += 1 
                    self.log("RMLINK: %s" % oldpath)
                    nfiles -= 1

            elif os.path.isdir(oldpath): 
                
                if self.check_del(oldpath, newpath):
                    self.state['dirs_deleted'] += 1 
                    self.log("RMDIR: %s" % oldpath)
                    nfiles -= 1
                    self.write_runfile()

            elif os.path.isfile(oldpath): 
                same = filecmp.cmp(oldpath, newpath)        
                if same: 
                    self.state['files_deleted'] += 1 
                    self.state['vol_deleted'] += os.path.getsize(oldpath)
                    self.log("DEL: %s" % oldpath)
                    nfiles -= 1
                else: 
                    self.log("MODIFIED: %s" % oldpath)
                   

            else: 
                self.log("IREGULAR FILE: %s" % oldpath)
                continue 
            
        # write MIGRATED.txt file to this dir and it's subdirectories have been checked
        if nfiles ==0: 
            M = open(os.path.join(old, 'MIGRATED.txt'),'w')
            M.close()
            return True
        else: return False


if __name__=="__main__":
    
    filename = sys.argv[1]
    T = TidyRun(filename)
    T.write_runfile()
    T.run()



	
	 
 
