# script to add storage pot for manual fileset set up.
# Sam Pepler 2011-09-22

import getopt, sys
import os, errno, math

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import *

class FormatSummary:

    def __init__(self,directory): 
        self.directory = directory
        self.nfiles =  {}  # number of files by extention
        self.samples = {}    #  files of type ext looked at
 
    def go(self):
        for root, dirs, files in os.walk(self.directory):
            print(root)
            for name in files:
                head, ext = os.path.splitext(name)
                if ext in self.nfiles: self.nfiles[ext] += 1
                else: self.nfiles[ext]=1

                if ext in self.samples:
                    if math.log(self.nfiles[ext],1.2) > len(self.samples[ext]): 
                        self.samples[ext].append(os.path.join(root,name)) 
                else: 
                    self.samples[ext] = [os.path.join(root,name)]

    def dump(self, dumpfile):
        EXTS = open(dumpfile+'.exts.txt', 'w')
        SAMPLES = open(dumpfile+'.samples.txt', 'w')
        for ext in list(self.nfiles.keys()):
            EXTS.write("%s|%s\n" % (ext,self.nfiles[ext]))
            for f in self.samples[ext]:
                SAMPLES.write("%s\n" % f)
        EXTS.close()
        SAMPLES.close() 

    def __repr__(self):
        return "%s\n\n%s" % (self.nfiles, self.samples)


if __name__=="__main__":

    format_audit_dir = '/datacentre/stats/format_audit'

    filesets = FileSet.objects.all()

    for fs in filesets:
        if not fs.storage_pot: continue
        print("Fileset %s" % fs)
        spot = fs.storage_path()
           
        formatsummary = FormatSummary(spot)
        formatsummary.go()
        formatsummary.dump(os.path.join(format_audit_dir,fs.storage_pot))

        
