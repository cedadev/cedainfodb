import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib

from cedainfoapp.models import *

def do_dus():
    # do a file set measurement for all the filesets which have not had it done in the last 10 days
    filesets = FileSet.objects.all()
    for f in filesets:
 
        fssms = FileSetSizeMeasurement.objects.filter(fileset=f).order_by('-date')
        first_time = (len(fssms) == 0) 

        if not first_time:
            last_fssm = fssms[0]
            not50 =  datetime.now() - last_fssm.date > timedelta(days=50)
            not20 =  datetime.now() - last_fssm.date > timedelta(days=20)
            not5 =  datetime.now() - last_fssm.date > timedelta(days=5)
            small =  last_fssm.no_files < 50000

            changing = False # assume static and look for changes
            npoints=0
            for fssm in fssms[1:]:                    # loop over fileset measurements from second to last...
                if datetime.now() - fssm.date > timedelta(days=120): break  # only look in past 120 days
                npoints +=1         # number of points within 120 days
                if fssm.size != last_fssm.size or fssm.no_files != last_fssm.no_files:
                    changing =True
            if npoints <2: changing = True    # if we have one or less points in the 120 days then assume changing.
        
        else:
            # first time defaults 
            last_fssm = None
            not50, not20, small, changing = True, True, True, True

        print "%s    " %f,

        doflag=False
        if first_time: doflag=True 
        elif not50: doflag=True 
        elif small:
            if changing and not5: doflag=True
            elif not20: doflag=True
        else:
            if changing and not20: doflag=True

        if doflag:
            print "Last done: %s    " % last_fssm,                   
            if not50: print "not50 ", 
            if not20: print "not20 ", 
            if not5: print "not5 ", 
            if small: print "small ", 
            if changing: print "changing", 
            print ''

            f.du()
        else: print "SKIP" 

def run ():
    do_dus()

    
