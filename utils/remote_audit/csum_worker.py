#!/usr/bin/python
#BSUB -W 12:00
#BSUB -q lotus

# script to read from db and make an audit file

import urllib2, urllib
import sys
import datetime
import os
import hashlib
import traceback
import glob


# Error reporting?

# recursive function to make checkm filelines 
def checkm_log(listname, storage_path):
    # recursive function to make checkm log file
    logname = "%s.log" %listname
    LIST = open(listname)
    LOG = open(logname, 'w') 
    while 1:
        line = LIST.readline()
        if line=='': break
        path = line.strip()     
        relpath = path[len(storage_path)+1:]                     
        size = os.path.getsize(path)
        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%dT%H:%M:%SZ')
        F=open(path)
        m=hashlib.md5()
        while 1:
            buf= F.read(1024*1024)
            m.update(buf)
            if buf=="": break
        LOG.write("%s|md5|%s|%s|%s\n" % (relpath,m.hexdigest(),size,mtime))
        LOG.flush()
    LOG.close()

if __name__ == "__main__":
    listname = sys.argv[1]
    storage_path = sys.argv[2]

    print listname, storage_path
    checkm_log(listname, storage_path)
    os.system("touch %s.DONE" % listname)

