import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from audit.models import *
from cedainfoapp.models import *



if __name__=="__main__":

    breakpath = sys.argv[1]

    filesets = FileSet.objects.all()
    fs_to_break = None
    
    #find fileset to break
    for f in filesets:
         if f.logical_path == breakpath[0:len(f.logical_path)]:
	     if fs_to_break == None:
	         fs_to_break = f
	     elif len(fs_to_break.logical_path) < len(f.logical_path):
	         fs_to_break = f	      
	     print f, fs_to_break
	 
 
    # if no break found exit
    if fs_to_break == None: 
        raise "No fileset found to break for path %s" % breakpath
    
    # if break point is not an existing directory exit
    if not os.path.isdir(breakpath) or os.path.islink(breakpath): 
        raise "path needs to be a plain directory (%s)" % breakpath
    
    # make new fileset with same partition and a low size (to be changed latter)
    new_fs = FileSet(partition=fs_to_break.partition, 
             logical_path=breakpath, overall_final_size=1024*1024)
    new_fs.save() 
    spotname = "archive/spot-%s" % new_fs.pk
    new_fs.storage_pot = spotname
    # if spot exists?
    if os.path.exists(new_fs.storage_path()) : 
        raise "storage dir already exists? (%s)" % str(new_fs.storage_path())
    new_fs.save() 
    
    # rename the break dir as the spot
    os.rename(breakpath, new_fs.storage_path())

    # make new link
    os.symlink(new_fs.storage_path(), new_fs.logical_path)

     
