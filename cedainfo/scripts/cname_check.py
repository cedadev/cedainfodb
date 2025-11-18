#
# Does ping check on each VM and records result in database. 
#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript ping_check
#
  
from cedainfoapp.models import *

import dns.resolver

def run():
   print('a')
   vms = VM.objects.all().order_by('name')
   print('b')
   for vm in vms:
       print('Checking VM: %s' % vm.name) 
      # print ('   ', vm.coloured_vm_name())
       print ('   ', vm.coloured_vm_name())
       #result = dns.resolver.query(vm.name, 'CNAME')


       #try:
       #    result = dns.resolver.query(vm.name, 'CNAME')
       #    for cnameval in result:
       #        print ('cname: ', cnameval.target)
       #except:
       #     print('error')
