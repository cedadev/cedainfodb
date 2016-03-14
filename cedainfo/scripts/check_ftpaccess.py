#
# Report on any storage directory that does not contain an ftpaccess
# file. The ftp server needs a file in each linked directory in order
# to allow access to files within that directory. 
#
# Unless the argument "update" is added, no updates will actually be made.
#
import os
import sys
import filecmp
import shutil
import subprocess

import psycopg2


FILE = '.ftpaccess'

doit = False

if len(sys.argv) > 1:
    if sys.argv[1] == "update":
        doit = True

if doit:
   print "Updates will be made"
else:
   print "Demo run only. No changes will be made"
  

def find_nearest_ftpaccess_file (start_dirname):
    '''
    Returns the location of the 'nearest' ftpaccess file to the given
    location. Returns an empty string if nothing is found.
    '''   
    dirname = start_dirname 
    dirname = dirname.rstrip('/')
    dirname = os.path.dirname(dirname) 

    while True:
    
        ftpaccess = dirname + '/' + FILE
		
        if os.path.exists(ftpaccess):
	    return ftpaccess
	       
        dirname = os.path.dirname(dirname)

        if dirname.count('/') == 1:
            break

    return ''


connection = psycopg2.connect(dbname="cedainfo", 
                                host="db1.ceda.ac.uk",
                                user="cedainfo", 
                                password="xxxxx")
cursor = connection.cursor()

sql = """
select logical_path, mountpoint, storage_pot  from cedainfoapp_fileset, cedainfoapp_partition
where cedainfoapp_fileset.partition_id = cedainfoapp_partition.id
and (logical_path like '/badc/%' or logical_path like '/neodc/%' or logical_path like '/sparc/%')
order by mountpoint"""

cursor.execute(sql)

recs = cursor.fetchall()

for rec in recs:
   
   logical_path = rec[0]
   directory = rec[1] + '/archive/' + rec[2]
   
#   print logical_path, directory
          
   if logical_path.count('/') <= 2:
       continue
   
   if not os.path.exists(logical_path):
       print 'ERROR path %s does not exist' % logical_path
       continue
   
   else:
       if not os.path.islink(logical_path):
           print 'ERROR %s is not a logical path' % logical_path
           continue
       else:
           link_destination = os.readlink(logical_path)
	   
	   link_destination = link_destination.rstrip('/')
	   directory = directory.rstrip('/')
	   
           if link_destination != directory:
	       print 'ERROR: link mismatch: %s %s' % \
	          (link_destination, directory)
	       continue
	       
   if not os.path.exists(directory):
       print 'ERROR directory %s does not exist' % directory
       continue
   
   nearest = find_nearest_ftpaccess_file(logical_path)
   current = directory + '/.ftpaccess'

   if not nearest:
       print 'ERROR could not find nearest ftpaccess file for %s' % logical_path
       continue
          
   if not os.path.exists(current):
       print 'No ftpaccess file: ', logical_path, directory 
       
       print 'cp %s %s (%s)' % (nearest, current, logical_path)

       if doit:
           subprocess.call(["cp", "-p", nearest, current])
       
   else:
       print 'Checking %s against %s' % (current, nearest)
       
       same = filecmp.cmp(current, nearest)
       
       if not same:
          print "WARNING: %s and %s (%s) differ" % (nearest, current, logical_path)          
          print 'cp %s %s (%s)' % (nearest, current, logical_path)
  
          if doit:
              subprocess.call(["cp", "-p", nearest, current])
 
