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


msg = '''From: emailtest@archman1.ceda.ac.uk
To: andrew.harwood@stfc.ac.uk
Subject: My email test message

This is just a test message

'''

messageFrom='emailtest@archman1.ceda.ac.uk'
messageTo = 'andrew.harwood@stfc.ac.uk'

now=datetime.today()

try:
   server = smtplib.SMTP('localhost') 	
   server.sendmail(messageFrom, messageTo, msg)
   server.quit()
   print now, 'OK'
except:
   print now, 'ERROR'
    
 
