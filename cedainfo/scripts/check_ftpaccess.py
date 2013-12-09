#
# Report on any storage directory that does not contain an ftpaccess
# file. The ftp server needs a file in each linked directory in order
# to allow access to files within that directory. 
#
import os
import sys
import filecmp
import shutil
import subprocess

import psycopg2


FILE = '.ftpaccess'


def find_nearest_ftpaccess_file (dirname):
    '''
    Returns the location of the 'nearest' ftpaccess file to the given
    location. Returns an empty string if nothing is found.
    '''   
    dirname = dirname.rstrip('/')
    
    while True:
    
        ftpaccess = dirname + '/' + FILE
		
        if os.path.exists(ftpaccess):
	    return ftpaccess
	       
        dirname = os.path.dirname(dirname)

        if dirname.count('/') == 1:
            break

    return ''


connection = psycopg2.connect(dbname="cedainfo", 
                                host="bora.badc.rl.ac.uk",
                                user="cedainfo", 
                                password="ler239b")
cursor = connection.cursor()

sql = """
select logical_path, mountpoint, storage_pot  from cedainfoapp_fileset, cedainfoapp_partition
where cedainfoapp_fileset.partition_id = cedainfoapp_partition.id
and (logical_path like '/badc/%' or logical_path like '/neodc/%')
order by mountpoint"""

cursor.execute(sql)

recs = cursor.fetchall()

for rec in recs:
   
   logical_path = rec[0]
   directory = rec[1] + '/archive/' + rec[2]
   
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
   
   if not os.path.exists(current):
       print 'No ftpaccess file: ', logical_path, directory 
       print 'cp %s %s (%s)' % (nearest, current, logical_path)
       subprocess.call(["cp", "-p", nearest, current])
       
   else:
#       print 'Checking %s against %s' % (current, nearest)
       
       same = filecmp.cmp(current, nearest)
       
       if not same:
          print "%s and %s differ" % (nearest, current)


    
 
