import getopt, sys
import os, errno
import datetime
from datetime import timedelta

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *



if __name__=="__main__":
 
    table = {}
    filesets = FileSet.objects.all().order_by('logical_path')
    
    toplevel = ''
    vol, nfiles = 0,0
    for f in filesets:
         slashcount = f.logical_path.count('/')
         if slashcount == 2: 
             table[toplevel] = (vol,nfiles)
             vol, nfiles = 0,0
             toplevel = f.logical_path

         size  = f.last_size()
         if size: 
             vol=vol+size.size
             nfiles = nfiles+size.no_files   

    lines = table.items()

    print "Top 10 largest datasets"
    lines.sort( key=lambda a:a[1][0], reverse=True )
    i=0
    for topfs, size in lines:
        print "%s | %2.2f TB | %s" % (topfs, size[0]/1.0e12, size[1])
        i+=1
        if i >9: break


    print "Top 10 datasets with most files"
    lines.sort( key=lambda a:a[1][1], reverse=True )
    i=0
    for topfs, size in lines:
        print "%s | %2.2f TB | %s" % (topfs, size[0]/1.0e12, size[1])
        i+=1
        if i >9: break




  


     
