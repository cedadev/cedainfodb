#
# Setup file for external scripts that connect to the userdb
#
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'userdb',                      # Or path to database file if using sqlite3.
        'USER': 'badc',                      # Not used with sqlite3.
        'PASSWORD': 'rtp569w',                  # Not used with sqlite3.
        'HOST': 'bora.badc.rl.ac.uk',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': ''                      # Set to empty string for default. Not used with sqlite3. 
     }
}

import logging
logging.basicConfig(
level = logging.DEBUG,
    format = '%(name)s %(module)s %(levelname)s [%(asctime)s] %(message)s',
)
LOG=logging.getLogger('cedadb')

