#
# Report on any storage directory that does not contain an ftpaccess
# file. The ftp server needs a file in each linked directory in order
# to allow access to files within that directory. 
#
import os
import sys

import psycopg2


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
   
   else:
       if not os.path.islink(logical_path):
           print 'ERROR %s is not a logical path' % logical_path
   
       else:
           link_destination = os.readlink(logical_path)
	   
	   link_destination = link_destination.rstrip('/')
	   directory = directory.rstrip('/')
	   
           if link_destination != directory:
	       print 'ERROR: link mismatch: %s %s' % \
	          (link_destination, directory)
	   
   if not os.path.exists(directory):
       print 'ERROR directory %s does not exist' % directory
       continue
   
   if not os.path.exists(directory + '/.ftpaccess'):
       print logical_path, directory 



    
 
