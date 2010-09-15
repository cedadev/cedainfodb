import os, subprocess
import sys
import logging

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *

def usage():
    print "FileSet directory maker"
    print "Usage: %s <fsc_path>" % sys.argv[0]
    print "Arguments:"
    print "\t<fsc_path> = FileSetCollection logical path"
    

logging.basicConfig(level=logging.INFO)

fsc = None

# Find the FileSetCollection if one given
if len(sys.argv) == 2:
    fsc_path = sys.argv[1]
    try:
        fsc = FileSetCollection.objects.get(logical_path=fsc_path)
        logging.info( "Found FileSetCollection %s" % fsc )
    except:
        logging.error( "FileSetCollection not found : %s" % fsc_path )
        sys.exit(1)
else:
    logging.error( "No FileSetCollection specified : exiting" )
    usage()
    sys.exit(1)

if fsc is not None:
    logging.info( "Setting up fileset dirs for FileSetCollection %s" % fsc )
    # Find all the filesets in this FSC (by their filesetcollectionrelations)
    fscrs = FileSetCollectionRelation.objects.filter(fileset_collection=fsc)
    for fscr in fscrs:
        if fscr.is_primary:
            # Primary FSCR : 
            # Create the logical path within the FileSetCollection, of this FileSet (will be link source)
            fsdir = os.path.join( fscr.fileset_collection.logical_path, fscr.logical_path ) 
            # Obtain the actual path of this FileSet (...depends on allocation to a partition)
            # Is the fileset assigned to a partition?
            if (fscr.fileset.partition is not None) and fscr.fileset.partition != "":
                logging.info( "Partition for fileset %s is %s" % (fscr.fileset, fscr.fileset.partition) )
            else:
                logging.warn( "No partition allocated for fileset %s" % (fscr.fileset) )
            
        else:
            # Non-primary FSCR : TODO : work out what to do for non-primary FSCRs
            logging.error( "Non-primary FileSetCollectionRelations not handled yet" )
            pass
                
    


