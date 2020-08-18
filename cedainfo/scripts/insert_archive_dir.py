import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib


from cedainfoapp.models import *


def run (*args):
    """Insert a directory at the given path. The directory will have the content of the original given path. """
    archive_path = args[0]
    archive_path = archive_path.rstrip('/')
    archive_parent_dir = os.path.dirname(archive_path)
    insert_dir = args[1]

    print(archive_path, insert_dir)

    if not os.path.isdir(archive_path):
        raise Exception("Need a existing directory in archive")

    if "/" in insert_dir:
        raise Exception("Can't have slashes in destination argument.")

    filesets_to_change = FileSet.objects.filter(logical_path__startswith=archive_path+"/")
    print(filesets_to_change)

    # new path
    new_path = os.path.join(archive_path, insert_dir)

    # make dir
    # os.mkdir(new_path, mode=0o755)

    for fs in filesets_to_change:
        print(fs.logical_path)
        print(fs.logical_path, " -> ", fs.logical_path.replace(archive_path, new_path))
