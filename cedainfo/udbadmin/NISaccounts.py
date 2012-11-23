#
# Routines for interfacing with NIS passwd and group files
#
import tempfile   
import subprocess
import passwd


def getExtGroupFile():
#
#      Return group file for external NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ssh", "ypinfo@storm.badc.rl.ac.uk",  "ypcat", "group"], stdout=a)
    p1.wait()
    group = passwd.loadgrp(a.name)
    a.close()

    return group


def getIntGroupFile():
#
#      Return group file for internal NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ypcat", "group"], stdout=a)
    p1.wait()
    group = passwd.loadgrp(a.name)
    a.close()

    return group

def getExtPasswdFile():
#
#      Return group file for internal NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ssh", "ypinfo@storm.badc.rl.ac.uk",  "ypcat", "passwd"], stdout=a)
    p1.wait()
    pw = passwd.loadpw(a.name)
    a.close()

    return pw
    
    
def getIntPasswdFile():
#
#      Return group file for internal NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ypcat", "passwd"], stdout=a)
    p1.wait()
    pw = passwd.loadpw(a.name)
    a.close()

    return pw
    
