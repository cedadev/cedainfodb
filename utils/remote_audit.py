
# script to read from db and make an audit file

import urllib2, urllib
import sys
import datetime
import os
import hashlib

# Error reporting?

# recursive function to make checkm filelines 
def checkm_log(directory, storage_path, LOG):
    # recursive function to make checkm log file
    reldir = directory[len(storage_path)+1:]
    names = os.listdir(directory)
    # look for diectories and recurse
    names.sort()
    for n in names:
        path = os.path.join(directory,n)    
        if os.path.isdir(path) and not os.path.islink(path):
            checkm_log(path, storage_path, LOG)
    # for each file 
    for n in names:
        path = os.path.join(directory,n)     
        relpath = os.path.join(reldir,n)                     
        # if path is reg file
        if os.path.isfile(path): 
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


# read from cedainfodb
# auditid and audit path
next_audit_url =  'http://127.0.0.1:8000/next_audit'
print "Opening url %s" % next_audit_url
f = urllib2.urlopen(next_audit_url)
line=f.readline()
line.strip()
bits = line.split()
if len(bits) != 2: sys.exit() # no audits to do	
auditid, auditpath = bits[0], bits[1]
print "Audit to do %s - %s" % (auditid, auditpath)

checkmfilename = '/tmp/checkm.audit-%s.txt' % auditid
print "Writing checkm log %s for this audit..." % checkmfilename
LOG = open(checkmfilename, 'w')
LOG.write('#%checkm_0.7\n')
LOG.write('# scaning path %s\n' % auditpath)
LOG.write('# generated %s\n' % datetime.datetime.utcnow())
LOG.write('# audit ID: %s\n' % auditid)
LOG.write('# \n')
LOG.write('# Filename|Algorithm|Digest|Length|ModTime\n')
checkm_log(auditpath, auditpath, LOG)
LOG.close()

print "Made checkm file"


# post results back to cedainfodb
upload_audit_results_url =  'http://127.0.0.1:8000/upload_audit_results/%s' % auditid
print "Opening url %s" % upload_audit_results_url
LOG = open(checkmfilename, 'r')
filecontent = LOG.read()
LOG.close()
values={'error':'','checkm':filecontent}
data = urllib.urlencode(values)
req = urllib2.Request(upload_audit_results_url, data)
response = urllib2.urlopen(req)
code = response.getcode()

print code


