from django.core.management import setup_environ
import sys
import settings
setup_environ(settings)

from cedainfoapp.models import *

"""
This maps filesets to filesetcollections and sets up expansion directories and links.
"""

# Read in the filesets together with volume estimates from the the CSV file

import csv

csv_file = sys.argv[1]
fsc_path = sys.argv[2]
csvReader = csv.reader(open(csv_file), delimiter=',')

try:
    fsc = FileSetCollection.objects.get(logical_path=fsc_path)
except:
    print "Could not find FileSetCollection with logical path %s : exiting" % fsc_path
    sys.exit(1)

for row in csvReader:
    if ((row[4] is not None) and (row[4] != "")):
        (requested_vol,FileSet_relative_logical_path) = (row[3],row[4])
        print "Creating FileSet:  %s : %s" % (FileSet_relative_logical_path, requested_vol)
        fs = FileSet(overall_final_size=requested_vol)
        print "%s %s" % (fs, fs.overall_final_size)
        fs.save()
        fscr = FileSetCollectionRelation(fileset=fs, fileset_collection=fsc, logical_path=FileSet_relative_logical_path, is_primary=True)
        print "%s %s" % (fscr, fs.label)
        fscr.save() # save method should re-save fs so don't need to explicitly do fs.save() again
        print "%s %s" % (fscr, fs.label)
    else:
        print "Insufficient info : %s" % row[1]
        pass
