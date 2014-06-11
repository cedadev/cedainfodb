#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
#  Reads a list of accountids piped into standard input and prints out the 
#  associated email address
#
import sys

from udbadmin.models import User


def run():

    for line in sys.stdin:
        username = line.strip()
	
	if not username:
	    continue
        try: 
            user = User.objects.get(accountid=username)
	    print user.accountid, user.emailaddress.lower()
        except:
            print 'ERROR: %s not found' % username

        
