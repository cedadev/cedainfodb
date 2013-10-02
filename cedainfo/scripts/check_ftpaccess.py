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
   
   if not os.path.exists(directory + '/.ftpaccess'):
       print logical_path, directory 



    
 
