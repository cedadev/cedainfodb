#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
import sys

from django.db.models import Q
  
from udbadmin.models import *

# Produce list of users with Distinguishing Name (DN) in the form
# /DC=uk/DC=ac/DC=ceda/O=STFC RAL/CN=$OPENID accountid

DN_PREFIX = "/DC=uk/DC=ac/DC=ceda/O=STFC RAL/CN="
     
def run():

    udjs = Datasetjoin.objects.filter(
        Q(datasetid="jasmin-login") | Q(datasetid="cems-login"),
        Q(userkey__gt=0),
        Q(removed=0)
    
    accountids = []
    
    for udj in udjs:
       accountids.append(udj.userkey.accountid)
       
    
    
    users = User.objects.filter(
        Q(accountid__in=accountids),
        Q(pk__gt=0),
        Q(openid__isnull=False),
        Q(accountid__isnull=False)
    ).exclude(openid="").exclude(accountid="")
    
    for user in users:
        print "%s%s %s" % (DN_PREFIX, user.openid, user.accountid)


        
#    for user in User.objects.filter(pk__gt=0).filter(openid__isnull=False).filter(accountid__isnull=False).exclude(openid="").exclude(accountid=""):
#        print "%s%s %s" % (DN_PREFIX, user.openid, user.accountid)