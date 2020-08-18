# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22


# DO NOT USE UNLESS YOU UNDERSTAND WHAT IS GOING 

import getopt, sys
import os, errno

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import *


if __name__=="__main__":

    logical_path = sys.argv[1]
    filesets = FileSet.objects.filter(logical_path__startswith = logical_path)
    for fs in filesets:
        print("found fileset %s" % fs)
        fssm =  fs.last_size()
        new_size = max(fs.overall_final_size, fssm.size *1.002 + 1000000)
        if new_size > fs.overall_final_size: 
            print("%s (%s)" % (new_size, fs.overall_final_size))
        fs.overall_final_size = new_size

        #fs.save()        




