
# DO NOT USE UNLESS YOU UNDERSTAND WHAT IS GOING 

import getopt, sys
import os, errno, shutil

from django.core.management import setup_environ
import settings
setup_environ(settings)

import time
from cedainfoapp.models import *


if __name__=="__main__":

    auditid = sys.argv[1]
    
    audit = Audit.objects.get(pk=auditid)
    print audit

    f = audit.fileset
    print f

    # add comments to fileset
    f.notes += '\nAudit %s flagged corruption. This was resolved and the audit flag cleared on %s.' % (audit.pk, time.strftime('%Y%m%d-%H%M'))
    print f.notes

    audit.auditstate='analysed'

    f.save()
    audit.save()




