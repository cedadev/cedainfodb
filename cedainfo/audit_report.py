# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import *


if __name__=="__main__":

    audit_id = int(sys.argv[1])
    audit = Audit.objects.filter(pk=audit_id)
    audit = audit[0]

    # find the last finished audit of this fileset for comparison
    prev_audit = Audit.objects.filter(fileset=audit.fileset, auditstate='analysed').order_by('-starttime')[0]

    result = audit.compare(prev_audit)
    print("Audit of %s\n============\nReported corruption of the following files\n" % audit.fileset)
    for line in result['corrupt']:
        print(line, end=' ')
