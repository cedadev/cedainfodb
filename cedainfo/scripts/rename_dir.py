import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib


from cedainfoapp.models import *


def run ():
    archive_path = sys.argv[1]
    archive_path = archive_path.rstrip('/')
    archive_parent_dir = os.path.dirname(archive_path)
    change_to = sys.argv[2]

    print archive_path, change_to

    if "/" in change_to:
        raise Exception("Can't have slashes in change to argument.")

    filesets_to_change = FileSet.objects.filter(logical_path__startswith=archive_path)
    print filesets_to_change

    # new path
    new_path = os.path.join(archive_parent_dir, change_to)

    # rename dir
    # os.rename(archive_path, new_path)

    for fs in filesets_to_change:
        print fs.logical_path
        print fs.logical_path, " -> ", fs.logical_path.replace(archive_path, new_path)
