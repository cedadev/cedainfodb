import getopt, sys
import os, errno
import datetime, time
from datetime import timedelta
import smtplib

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import FileSet, Partition, Audit


def start(self):
        
    checksumsfile = os.path.join(self.fileset.storage_path(), '.checksums') 
    if not os.path.exists(checksumsfile):
        print "no checksums file."
        return

    # time of audit
    mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(checksumsfile))	    
    self.starttime = mtime
    self.auditstate = 'started'
    self.save()
    try: 
        self.checkm_log()
    except Exception, e:
        self.endtime = datetime.datetime.utcnow()
        self.auditstate = 'error'
        self.save()
        raise e  
	    
    self.endtime = self.starttime
	
    self.auditstate = 'analysed'
    self.save()

Audit.start = start


def _checkm_log(self, directory, storage_path, LOG):
    # recursive function to make checkm log file
    reldir = directory[len(storage_path)+1:]
    names = os.listdir(directory)
    # look for diectories and recurse
    names.sort()
    for n in names:
        path = os.path.join(directory,n)    
        if os.path.isdir(path) and not os.path.islink(path):
            self._checkm_log(path, storage_path, LOG)
    # read old .checksuns file
    checksumsfile = os.path.join(directory, '.checksums') 
    if os.path.exists(checksumsfile):
        CS = open(checksumsfile)
        lines = CS.readlines()
#        print lines
        checksums = {}
        filenames = []
        for l in lines:
            bits = l.split(':')
            name, digest, size, mtime = bits[0], bits[1], bits[2],bits[3]
            checksums[name]=(digest, size, mtime)
            filenames.append(name)

        filenames.sort()
        for name in filenames:
            relpath = os.path.join(reldir, name)  
            (digest, size, mtime) = checksums[name] 
            LOG.write("%s|md5|%s|%s|%s\n" % (relpath,digest ,size,
                      time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(float(mtime)))))

Audit._checkm_log = _checkm_log
	


if __name__=="__main__":


    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"
    


    filesets  =   FileSet.objects.filter(storage_pot__isnull=False).exclude(storage_pot='')
    for fs in filesets:
        print "===== %s ====" % fs
        checksumsfile = os.path.join(fs.storage_path(), '.checksums') 
        if not os.path.exists(checksumsfile):
            print "no checksums file for %s." % fs.logical_path
            continue
        
        # check that .checksums Audit does not exist
        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(checksumsfile))	    
        audits = Audit.objects.filter(fileset=fs, starttime=mtime)
        if len(audits) >0:
            print "audit already done or already started. %s." % fs.logical_path
            continue
             
        # scan for checksums   
        print "Do audit for %s" %  fs.logical_path
        audit=Audit(fileset=fs)
        audit.start() 
        audit.save()  

