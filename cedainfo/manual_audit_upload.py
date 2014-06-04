
# DO NOT USE UNLESS YOU UNDERSTAND WHAT IS GOING 

import getopt, sys
import os, errno, shutil

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


if __name__=="__main__":

    auditid = sys.argv[1]
    checkmfilename = sys.argv[2]
    
    audit = Audit.objects.get(pk=auditid)
    print audit

    if not os.path.exists('%s/%s' %(settings.CHECKM_DIR, audit.fileset.storage_pot)): 
        os.mkdir('%s/%s' %(settings.CHECKM_DIR, fileset.storage_pot))
    audit.logfile ='%s/%s/checkm.%s.%s.log' % (settings.CHECKM_DIR, audit.fileset.storage_pot,
                                               audit.fileset.storage_pot, time.strftime('%Y%m%d-%H%M'))     
    audit.save()
    shutil.copy(checkmfilename, audit.logfile) 

    audit.analyse()    





