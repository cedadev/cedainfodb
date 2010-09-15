from django.core.management import setup_environ
import sys
import settings
import logging

setup_environ(settings)

from cedainfoapp.models import *

"""
This maps filesets to filesetcollections and sets up expansion directories and links.
"""

# Read in the filesets together with volume estimates from the the CSV file

import csv

logging.basicConfig(level=logging.INFO)

csv_file = sys.argv[1]
fsc_path = sys.argv[2]
try:
    csvReader = csv.reader(open(csv_file), delimiter=',')
    logging.debug("Opened CSV file %s" % csv_file) 
except(IOError), e:
    logging.error("Could not open CSV file %s : exiting\n" % csv_file )
    sys.exit(1)

try:
    fsc = FileSetCollection.objects.get(logical_path=fsc_path)
    logging.debug("Found FileSetCollection %s" % fsc)
except:
    logging.error("Could not find FileSetCollection with logical path %s : exiting" % fsc_path)
    sys.exit(1)

for row in csvReader:
    if ((row[4] is not None) and (row[4] != "")):
        (requested_vol,FileSet_relative_logical_path) = (row[3],row[4])
        logging.info("Creating FileSet:  %s : %s" % (FileSet_relative_logical_path, requested_vol) )
        fs = FileSet(overall_final_size=requested_vol)
        logging.info( "%s %s" % (fs, fs.overall_final_size) )
        #fs.save()
        fscr = FileSetCollectionRelation(fileset=fs, fileset_collection=fsc, logical_path=FileSet_relative_logical_path, is_primary=True)
        logging.info( "%s %s" % (fscr, fs.label) )
        #fscr.save() # save method should re-save fs so don't need to explicitly do fs.save() again
        logging.info( "%s %s" % (fscr, fs.label) )
    else:
        logging.warn( "Insufficient info : %s" % row[1] )
        pass
