#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
#  Reads a list of accountids from file 'users.lis' and prints out the 
#  associated email address
#
from udbadmin.models import User

f = open('users.lis', 'r')

def run():

    for line in f:
        username = line.strip()
    #   print username
        try: 
            user = User.objects.get(accountid=username)
        except:
            print 'ERROR: %s not found' % username

        print user.accountid, user.emailaddress.lower()
