#!/usr/local/cedainfodb/releases/current/venv/bin/python
#
# Sends out email notifying user that new datasets have
# been added to their account. This is normally called
# automatically when the CEDA team authorise a new
# dataset.
#
# Usage: new_datasets_msg.py [--send] userkey
#
#   --send Send the message via email. Otherwise, just
#          print the message that would be sent (useful
#          for testing). 
#

import sys
import os
import argparse
import smtplib
import jinja2
from datetime import datetime, timedelta
from pytz import timezone

import django
sys.path.append('/usr/local/cedainfodb/releases/current/cedainfo')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cedainfo.settings")
django.setup()
from django.conf import settings

from udbadmin.models import *


TEMPLATE_DIR    = os.path.dirname(__file__)


parser = argparse.ArgumentParser(
           description='Notify user that new datasets have been added')
           
           
parser.add_argument('userkey', type=int, help='Userkey of user')
parser.add_argument('-send', '--send', action='store_true', 
                    help='Send message to user')
args = parser.parse_args()


try:
    user = User.objects.get(userkey=args.userkey)
except:
    sys.exit('Error reading details for userkey %s' % args.userkey)

udjs = Datasetjoin.objects.filter(userkey=user.userkey).filter(removed=0).order_by('-endorseddate')
    
#udjs = user.currentDatasets(filter_duplicates=True)
#udjs = Datasetjoin.objects.filter(removed=0)

display_datasets = []

badc_count  = 0
neodc_count = 0

for udj in udjs:
#
#   Check that this entry corresponds with an entry in the tbdatasets
#   table. It should do, but just in case...
#    
    if not hasattr(udj, 'datasetid'):
        continue

    directory = udj.datasetid.directory
    

    if directory:
        directory = directory.strip()
        
        if directory.startswith('/badc/') or \
           directory.startswith('/neodc/'):
               udj.ftpdirectory = directory
                   
        if directory.startswith('/badc/'):
            udj.webdirectory = 'http://data.ceda.ac.uk%s' % directory
           
        if directory.startswith('/neodc/'):
            udj.webdirectory = 'http://data.ceda.ac.uk%s' % directory
               
        if directory.startswith('http'):
            udj.webdirectory = directory           
          
    display_datasets.append(udj)
#
#   Don't display the expire date if it has been set to a date far in the future 
#    
    expire_string = ''
    
    if udj.expiredate:
        today = datetime.today()

        if today + timedelta(days=3650) > udj.expiredate:
            expire_string = udj.expiredate.strftime('%d-%b-%Y')
	
        udj.expire_string = expire_string
	
template_loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
env = jinja2.Environment(loader=template_loader)
#
# To needs to be a list for smplib.sendmail if more than one address
#
##messageTo   = ["andrew.harwood@stfc.ac.uk"]
messageTo   = [user.emailaddress]

messageFrom = "support@ceda.ac.uk"
template = env.get_template('ceda_new_datasets.jinja')


subject = "New datasets added to account %s" % user.accountid

msg = template.render({"from":  messageFrom, 
                       "to": user.emailaddress, 
                       "subject": subject, 
		       "accountid": user.accountid, 
                       "title": user.title, 
                       "surname": user.surname, 
                       "datasets": display_datasets})

if args.send:
    print ('Sending email...')
    
    try:
        server = smtplib.SMTP('localhost')
        server.sendmail(messageFrom, messageTo, msg)
        server.quit()
    except:
        sys.stderr.write('Error sending new_datasets message to: %s. Email: %s\n'
	% (user.accountid, user.emailaddress))
        sys.exit(99)
else:
    print (msg)

