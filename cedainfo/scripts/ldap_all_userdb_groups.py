#!/usr/local/cedainfodb/releases/current/venv/bin/python
#
# Prints all ldap user information generated from the userdb
#
import sys
import os
import tempfile
import psycopg2
import smtplib
import time


from django.core.management import setup_environ

sys.path.append('/usr/local/cedainfodb/releases/current/cedainfo')

import cron_settings as dbsettings
setup_environ(dbsettings)

import udbadmin.LDAP as LDAP
import udbadmin.update_check as update_check
import udbadmin.udb_ldap as udb_ldap

from django.db import connections

a = udb_ldap.ldif_all_groups(add_additions_file=False)

a.seek(0)
lines = a.readlines()

for line in lines:
    print(line, end=' ')

