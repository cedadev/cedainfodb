#
# Compare vm information in cedainfodb against ansible 'fact' information
#
import json
import os
  
from cedainfoapp.models import *
from udbadmin.models import User, Institute

def run():
   
   institutes = Institute.objects.all()
   
   
   for i in institutes:
       print i.name
   

       
