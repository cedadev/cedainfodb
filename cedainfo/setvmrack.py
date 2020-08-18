# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import *


if __name__=="__main__":

    vhosts = Host.objects.filter(host_type = "virtual_server")
    for vh in vhosts:
        print("Virtual host: %s (%s)  %s" % (vh, vh.hypervisor, vh.retired_on))
        
 
