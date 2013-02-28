import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import FileSet, Partition


def do_dfs():
    # do df for all partitions
    partitions = Partition.objects.all()
    for p in partitions:
        print "Doing df of partition: %s " % p
        p.df()


if __name__=="__main__":

    # do dfs
    do_dfs()

    
