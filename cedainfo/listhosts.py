# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *


if __name__=="__main__":

    hosts = Host.objects.filter(retired_on__isnull=True)
    for h in hosts:
        print "%s" % h
 
 
