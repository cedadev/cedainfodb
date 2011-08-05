import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *



if __name__=="__main__":

    filesets = FileSet.objects.filter(logical_path__startswith='/badc/cmip5/data/cmip5/output1/MOHC')
    for f in filesets:
         print f.storage_path()
	 
 

