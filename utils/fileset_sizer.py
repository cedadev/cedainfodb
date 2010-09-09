import os, subprocess
import sys

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *
fsc = None

# Find the FileSetCollection if one given
if len(sys.argv) == 2:
    fsc_path = sys.argv[1]
    try:
        fsc = FileSetCollection.objects.get(logical_path=fsc_path)
    except:
        print "FileSetCollection not found : %s" % fsc_path
        sys.exit(1)


# Loop through all FileSets (or those belonging to the given FileSetCollection, if given) and measure their size. Record a timestampted FileSetSizeMeasurement for each.
if fsc is not None:
    fscrs = FileSetCollectionRelation.objects.filter(fileset_collection=fsc)
else:
    fscrs = FileSetCollectionRelation.objects.all()
for fscr in fscrs:
    if fscr.is_primary:
        # Path is composed of FileSetCollectionRelation.logical_path and FileSetCollection.logical_path
        fsdir = os.path.join( fscr.fileset_collection.logical_path, fscr.logical_path )
        sp = subprocess.Popen(['du','-s','nodelist'], stdout=subprocess.PIPE)
        (sout, serr) = sp.communicate()
        # TODO could set some "safe" timeout value here & optionally kill the subprocess?
        sp.wait()
        if sp.returncode == 0:
            size_in_bytes = sout.split('\t')[0] # size in bytes is 1st field of tab-delimited stdout
            size = FileSetSizeMeasurement(fscr.fileset, size_in_bytes)
            print size
        else:
            print "Failed to get size for directory %s" % fsdir