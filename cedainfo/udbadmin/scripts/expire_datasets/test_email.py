#!/usr/local/userdb/venv/bin/python
#
# Simple script to check for problems sending email
# using smtplib
#
import sys
import os
import smtplib
from datetime import datetime
from pytz import timezone


msg = '''From: support@ceda.ac.uk 
To: runnerharwood@gmail.com 
Subject: My email test message

This is just a test message

'''

messageFrom='support@ceda.ac.uk'
messageTo = 'runnerharwood@gmail.com'

now=datetime.today()

try:
   server = smtplib.SMTP('localhost') 	
   server.sendmail(messageFrom, messageTo, msg)
   server.quit()
   print (now, 'OK')
except:
   print (now, 'ERROR')
    
 
