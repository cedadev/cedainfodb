#
# Does ping check on each VM and records result in database. 
#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript ping_check
#
  
from cedainfoapp.models import *

def run():
   
   vms = VM.objects.all().order_by('name')
   
   for vm in vms:
       print('Checking VM: %s' % vm.name, end=' ') 
       print(' ', vm.ping_ok())
