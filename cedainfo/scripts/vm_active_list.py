#
# Prints list of active VMs, suitable for checking using ansible facts. Excludes 'legacy' machines
#

  
from cedainfoapp.models import *

def run():
   
   vms = VM.objects.filter(status = 'active').order_by('name')
   
   for vm in vms:

       if vm.name.startswith('legacy:') or vm.name.startswith('00 unspecified'):
          continue
       else:
           print vm.name
           

