import json
import os
  
from cedainfoapp.models import *

source_dir = "/home/aharwood/vmchecker/out/"

memory_key = {'light': 1, 'moderate': 2, 'multiuser': 4, 'multithreaded': 8, 'max': 16, 'max24': 24, 'max32': 32}

cpu_key = {'minimal': 1, 'light': 2, 'moderate': 4, 'intermediate': 6, 'heavy': 8}


def run():
   
   vms = VM.objects.filter(status = 'active').order_by('name')
   
   for vm in vms:
       if vm.name.startswith('legacy:') or vm.name.startswith('00 unspecified'):
          continue
           
#       print 'Checking VM: %s' % vm.name
       fact_file = source_dir + vm.name
       
       if os.path.isfile(fact_file):

          try:
              with open(fact_file) as json_file:
                  data = json.load(json_file)

              p = data['ansible_facts']

              hostname = p['ansible_nodename']

              cpu_actual = int(p['ansible_processor_vcpus'])
              cpu_requested = cpu_key[vm.cpu_required]

              mem = p['facter_memorysize_mb']
              mem_actual = int(round(float(mem)/1000))
              mem_requested = memory_key[vm.memory_required]

              # if cpu_requested != cpu_actual:
              #   new_cpu_string = cpu_key.keys()[cpu_key.values().index(cpu_actual)]
              #   print hostname, "cpu:", cpu_requested, "->", cpu_actual, "(%s)" % new_cpu_string
              #   print "update cedainfoapp_vm set cpu_required='%s' where name = '%s'" % (new_cpu_string, vm.name)

              if mem_requested != mem_actual:
                 new_mem_string = memory_key.keys()[memory_key.values().index(mem_actual)]
                 print hostname, mem_requested, mem_actual, new_mem_string
                 print "update cedainfoapp_vm set memory_required='%s' where name = '%s'" % (new_mem_string, vm.name)
          except:
             print ('Error processing %s' % vm.name)
       else:
          print '   File %s NOT found' % fact_file

       
       
