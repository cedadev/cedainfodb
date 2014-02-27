# Django settings for cedainfo project.

import os
import re
PROJECT_DIR= os.path.dirname(__file__) 

DEBUG          = False
TEMPLATE_DEBUG = False


DATABASES = {
    'default': {
     },

    'userdb': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'userdb',                      # Or path to database file if using sqlite3.
        'USER': 'badc',                      # Not used with sqlite3.
        'PASSWORD': 'rtp569w',                  # Not used with sqlite3.
        'HOST': 'bora.badc.rl.ac.uk',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },

}
DATABASE_ROUTERS = ['dbrouter.DatabaseAppsRouter']
DATABASE_APPS_MAPPING= {'udbadmin': 'userdb'}

ADDITIONAL_LDAP_GROUP_FILE = "/datacentre/opshome/etc/infrastructure/accounts/ldap/ldap_additional_groups.txt"
ADDITIONAL_LDAP_USER_FILE  = "/datacentre/opshome/etc/infrastructure/accounts/ldap/ldap_additional_users.txt"

# Make this unique, and don't share it with anybody.
SECRET_KEY = ')p*zn!&dkeiji48jkdjkkljd880rutxe%av0_oa*4kc(57_rkda8!c&o7w$#^'

#
# Url for LDAP server
#
LDAP_URL          = 'ldap://homer.esc.rl.ac.uk'

LDAP_WRITE_URL    = "ldap://homer.esc.rl.ac.uk"
LDAP_WRITE_PASSWD = 'TUbr7kUj'
LDAP_WRITE_DN     =  "cn=cedaadmin,ou=software,ou=People,o=hpc,dc=rl,dc=ac,dc=uk"

