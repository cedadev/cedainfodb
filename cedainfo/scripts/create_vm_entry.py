#!/usr/local/cedainfodb/releases/current/venv/bin/python
#
#
# Template for adding a new legacy VM to the cedainfodb. 
#
#
import sys
import os

sys.path.append('/usr/local/cedainfodb/releases/current/cedainfo')

from django.core.management import setup_environ
from django.conf import settings

import settings as dbsettings

setup_environ(dbsettings)

from django.contrib.auth.models import *
from cedainfoapp.models import *

vm_name = 'legacy:triton.badc.rl.ac.uk'


try:
    a = VM.objects.get(name=vm_name)
    print "vm name already exists"
    sys.exit()
except:

    print "Creating: %s" % vm_name
    
    description = """
    This VM entry was added automatically. It is a skeleton entry based on the orginal entry in the 'host' table.
    """

    a= VM(
        name=vm_name,
        type='legacy',
        status='deprecated',
        description=description,
        internal_requester=User.objects.get(username='nobody'),
        date_required='1999-01-01',
        patch_responsible_id=User.objects.get(username='nobody').id
    )
    a.save()

