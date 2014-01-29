
# script to read from db and make an audit file

import urllib2, urllib
import sys
import datetime
import os
import hashlib
import traceback
import glob
import time

def make_inputlists(auditname, index, volume, nfiles, directory, storage_path, LIST):
    # recursive function to input lists for checksumming
    # list contain 1-10000 files and total no more than 100GB                                                                                    

    # if LIST is not open create it
    if LIST==None: LIST = open('%s.%s.list' % (auditname, index), 'w')
              
    reldir = directory[len(storage_path)+1:]
    names = os.listdir(directory)
    # look for diectories and recurse                                                                                                             
    names.sort()
    for n in names:
        if n == '.mnj_wrk': continue
        path = os.path.join(directory,n)
        if os.path.isdir(path) and not os.path.islink(path):
            (index, volume, nfiles, LIST) = make_inputlists(auditname, index, volume, nfiles, path, storage_path, LIST)
    # for each file                                                                                                                               
    for n in names:
        if n == '.ftpaccess': continue
        path = os.path.join(directory,n)
        relpath = os.path.join(reldir,n)
        # if path is reg file                                                                                                                     
        if os.path.isfile(path) and not os.path.islink(path):
            LIST.write(path+'\n')
            size = os.path.getsize(path)
            volume += size
            nfiles += 1
            if volume > 4000000000 or nfiles > 10000:
                LIST.close()
                volume = 0
                nfiles = 0
                index += 1
                LIST = open('%s.%s.list' % (auditname, index), 'w')
                 
    LIST.flush()
    return (index, volume, nfiles, LIST)

def write_log_start(auditname, auditpath):
    print "Writing checkm log %s for this audit..." % auditname
    LOG = open(auditname, 'w')
    LOG.write('#%checkm_0.7\n')
    LOG.write('# scaning path %s\n' % auditpath)
    LOG.write('# audit id: %s\n' % auditname)
    LOG.write('# generated %s\n' % datetime.datetime.utcnow())
    LOG.write('# \n')
    LOG.write('# Filename|Algorithm|Digest|Length|ModTime\n')
    LOG.close()

def make_work_lists(auditname, auditpath):
    (index, volume, nfiles, LIST) = make_inputlists(auditname, 0, 0, 0, auditpath, auditpath, None)
    LIST.close()
    print "wait 2 secs for files to close..."
    time.sleep(2)
    return index+1  #return number of jobs


def submit_worker_jobs(auditname, auditpath, njobs):
    for i in range(njobs):
        listfile = '%s.%s.list' % (auditname, i)
        print listfile
        #checkm_log(listfile, auditpath)
        os.system("bsub -o %s.out python ./csum_worker.py %s %s" % (auditname, listfile, auditpath))


def compile_output(auditname, auditpath, njobs):    
    LOG = open(auditname, 'a')
    starttime = time.time()
    for i in range(njobs):
        listfile = '%s.%s.list' % (auditname, i)
        logfile = '%s.%s.list.log' % (auditname, i)
        donefile = '%s.%s.list.DONE' % (auditname, i)
        while 1: 
            if os.path.exists(donefile):
                logcontent = open(logfile).read()
                print "Writing checkm log %s for this audit from %s..." % (auditname, logfile)
                LOG.write(logcontent)
                os.unlink(donefile)
                os.unlink(logfile)
                os.unlink(listfile)
                break
            else: 
                print "Sleeping waiting for %s" % donefile
                time.sleep(4)
                if time.time() - starttime >  2*24*3600:  # give up after 2 days
                    return True
        

#----------------
def get_auditname():
    # read from cedainfodb
    # auditid and audit path
  
    proxy_handler = urllib2.ProxyHandler({"http":"wwwcache.rl.ac.uk:8080"})
    opener = urllib2.build_opener(proxy_handler)
    next_audit_url =  'http://cedadb.ceda.ac.uk/next_audit'
    print "Opening url %s" % next_audit_url
    f = opener.open(next_audit_url)
    line=f.readline()
    line.strip()
    bits = line.split()
    if len(bits) != 2: sys.exit() # no audits to do
    auditid, auditpath = bits[0], bits[1]
    print "Audit to do %s - %s" % (auditid, auditpath)
    return (auditid, auditpath)

def upload_result(auditid, checkmfilename):
    # post results back to cedainfodb
    proxy_handler = urllib2.ProxyHandler({"http":"wwwcache.rl.ac.uk:8080"})
    opener = urllib2.build_opener(proxy_handler)
    upload_audit_results_url =  'http://cedadb.ceda.ac.uk/upload_audit_results/%s' % auditid
    print "Opening url %s" % upload_audit_results_url
    LOG = open(checkmfilename, 'r')
    filecontent = LOG.read()
    LOG.close()
    values={'error':0,'checkm':filecontent}
    data = urllib.urlencode(values)
    req = urllib2.Request(upload_audit_results_url, data)
    response = opener.open(req)
    code = response.getcode()
    print code
    print "Tidy up..."
    os.unlink(auditid)


def upload_error(auditid):
    # post erro back to cedainfodb
    proxy_handler = urllib2.ProxyHandler({"http":"wwwcache.rl.ac.uk:8080"})
    opener = urllib2.build_opener(proxy_handler)
    upload_audit_results_url =  'http://cedadb.ceda.ac.uk/upload_audit_results/%s' % auditid
    print "Opening url %s" % upload_audit_results_url
    values={'error':1,'checkm':''}
    data = urllib.urlencode(values)
    req = urllib2.Request(upload_audit_results_url, data)
    response = opener.open(req)
    code = response.getcode()
    print code

#-------------
               

# read next audit from cedadb
auditname, auditpath = get_auditname()

try:
    # write the audit header
    write_log_start(auditname, auditpath)

    # generate listing files to pass to the check summing worker processes 
    njobs = make_work_lists(auditname, auditpath)

    # submit jobs to the queue
    submit_worker_jobs(auditname, auditpath, njobs)



    # watch for output to compile
    error = compile_output(auditname, auditpath, njobs)

    if error: upload_error(auditname)
    else: upload_result(auditname, auditname)

except: 
    upload_error(auditname)
    print "Error in job coord"

print "FINISHED"
