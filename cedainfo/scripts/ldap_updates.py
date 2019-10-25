#!/usr/local/cedainfodb/releases/current/venv/bin/python

#
# Prints all ldap commands needed to syncronise the userdb with the current
# ldap system
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


dbconf     = dbsettings.DATABASES['userdb']
connection = psycopg2.connect(dbname=dbconf['NAME'], 
                                host=dbconf['HOST'],
                                user=dbconf['USER'], 
                                password=dbconf['PASSWORD'])

cmds = udb_ldap.ldif_all_user_updates()

print cmds
