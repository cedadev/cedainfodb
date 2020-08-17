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
    p1 = subprocess.Popen(["ssh", 
                           "-oBatchMode=yes", 
                           "ypinfo@storm.badc.rl.ac.uk",  
                           "ypcat", 
                           "group"], 
                           stdout=a)
    p1.wait()
    group = passwd.loadgrp(a.name)
    a.close()

    return group


def getIntGroupFile():
#
#      Return group file for internal NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ssh", 
                           "-oBatchMode=yes", 
                           "ypinfo@twister.badc.rl.ac.uk",  
                           "ypcat", 
                           "group"], 
                           stdout=a)
    p1.wait()
    group = passwd.loadgrp(a.name)
    a.close()

    return group

def getExtPasswdFile():
#
#      Return group file for external NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ssh",
                           "-oBatchMode=yes", 
                           "-oStrictHostKeyChecking=no",
                           "ypinfo@storm.badc.rl.ac.uk",  
                           "ypcat", 
                           "passwd"], 
                           stdout=a)
    p1.wait()
    pw = passwd.loadpw(a.name)
    a.close()

    return pw
    
    
def getIntPasswdFile():
#
#      Return group file for internal NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ssh",
                           "-oBatchMode=yes",
                           "-oStrictHostKeyChecking=no", 
                           "ypinfo@twister.badc.rl.ac.uk",  
                           "ypcat", 
                           "passwd"], 
                           stdout=a)
    p1.wait()
    pw = passwd.loadpw(a.name)
    a.close()

    return pw
    

def isExtNISUser (user):
    '''Returns True if the user should appear in the external NIS database.
       This should really be determined by checking for 'isJasminUser', 'isCemsUser' or 'isExtLinuxUser',
       but for now we will cheat and simply check if they are already in the external NIS passwd file.
    '''

    if user.accountid in EXT_PASSWD.keys():
        return True
    else:
        return False     

def isIntNISUser (user):
    '''Returns True if the user should appear in the internal NIS database.
    '''

    if user.accountid in INT_PASSWD.keys():
        return True
    else:
        return False     


#EXT_PASSWD = getExtPasswdFile()
#INT_PASSWD = getIntPasswdFile()
