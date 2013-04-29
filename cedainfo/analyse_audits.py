# script to analyse finished audits

import getopt, sys
import os, errno
import datetime
from datetime import timedelta
import smtplib

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import FileSet, Partition, Audit


if __name__=="__main__":

    audits = Audit.objects.filter(auditstate='finished')
    for a in audits:
        a.analyse()


