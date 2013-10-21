#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
import sys
  
from udbadmin.models import *

# Produce list of users with Distinguishing Name (DN) in the form
# /DC=uk/DC=ac/DC=ceda/O=STFC RAL/CN=$OPENID accountid

DN_PREFIX = "/DC=uk/DC=ac/DC=ceda/O=STFC RAL/CN="
     
def run():

    for user in User.objects.filter(pk_gt=0):
        print "%s%s %s" % (DN_PREFIX, user.openid, user.accountid)