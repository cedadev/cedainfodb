import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib


from cedainfoapp.models import *


def run (*args):
    archive_path = args[0]
    archive_path = archive_path.rstrip('/')
    archive_parent_dir = os.path.dirname(archive_path)
    change_to = args[1]

    print archive_path, change_to

    if not os.path.isdir(archive_path):
        raise Exception("Need a existing directory in archive")

    if "/" in change_to:
        raise Exception("Can't have slashes in destination argument.")

    filesets_to_change = FileSet.objects.filter(logical_path__startswith=archive_path)
    print filesets_to_change

    # new path
    new_path = os.path.join(archive_parent_dir, change_to)

    # rename dir
    print "rename %s -> %s" % (archive_path, new_path)
    os.rename(archive_path, new_path)

    for fs in filesets_to_change:
        print fs.logical_path, " -> ", fs.logical_path.replace(archive_path, new_path)
        fs.logical_path = fs.logical_path.replace(archive_path, new_path)
        fs.save()