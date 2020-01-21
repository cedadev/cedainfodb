#
#  Create new VM entries using information from a csv file
#
# Intended to be run via run_script
#
import json
import os
import sys
import csv

from cedainfoapp.models import *
from django.contrib.auth.models import *
from django.conf import settings




def get_cpu_string (cpu):

    cpu = cpu.strip()
    cpu_string = ''

    if cpu == "1":
        cpu_string = 'minimal'
    elif cpu == "2":
        cpu_string = 'light'
    elif cpu == "4":
        cpu_string = 'moderate'
    elif cpu == "6":
        cpu_string = 'intermediate'
    elif cpu == "8":
        cpu_string = 'heavy'
    elif cpu == "16":
        cpu_string = 'heavy16'
    else:
        sys.exit('Unexpected value (%s) for cpu' % cpu)

    return cpu_string

def get_ram_string (ram):

    ram = ram.strip()
    ram_string = ''

    if ram == "1":
        ram_string = "light"
    elif ram == "2":
        ram_string = "moderate"
    elif ram == "4":
        ram_string = "multiuser"
    elif ram == "8":
        ram_string = "multithreaded"
    elif ram == "12":
        ram_string = "max12"
    elif ram == "16":
        ram_string = "max16"
    elif ram == "24":
        ram_string = "max24"
    elif ram == "32":
        ram_string = "max32"
    elif ram == "48":
        ram_string = "max48"
    elif ram == "64":
        ram_string = "max64"
    else:
        sys.exit('Unexpected value (%s) for ram' % ram)

    return ram_string

def get_disk_string (disk):

    disk = disk.strip()
    disk_string = ''

    disk = int(disk)

    if disk <= 25:
        disk_string = "light"
    elif disk <= 35:
        disk_string = "moderate"
    elif disk <=85:
        disk_string = "large"
    elif disk  <=100:
        disk_string = "database"
    else:
        sys.exit('Unexpected value (%s) for disk' % disk)

    return disk_string

def run():


    with open('vms.txt') as csv_file:

        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0

        for row in csv_reader:
            vm_name = row[0]
            vm_cpu  = row[1]
            vm_ram  = row[2]
            vm_disk = row[3]
            vm_root_users = row[4]
            vm_tag   = row[5]
            vm_ip    = row[6]
            vm_other = row[7]

            cpu_string = get_cpu_string(vm_cpu)
            ram_string = get_ram_string(vm_ram)
            disk_string = get_disk_string(vm_disk)

            vm_description = 'Added automatically'
            if vm_tag: vm_description  +=  "\nTags: %s" % vm_tag
            if vm_ip: vm_description  +=  "\nIP: %s" % vm_ip
            if vm_other: vm_description  +=  "\nOther information: %s" % vm_other

            print vm_name,  vm_description
            line_count = line_count + 1

            try:
                a = VM.objects.get(name=vm_name)
                print "vm name already exists"
                sys.exit()
            except:

#                print "Creating: %s" % vm_name

                vm_type = 'legacy'
                vm_operation_type = 'production'
                vm_status = 'deprecated'
                vm_internal_requester  ='aharwood'
                vm_date_required = '1999-01-01'
                vm_patch_responsible = 'aharwood'

                a= VM(
                    name=vm_name,
                    type= vm_type,
                    operation_type = vm_operation_type,
                    cpu_required = cpu_string,
                    memory_required = ram_string,
                    disk_space_required = disk_string,
                    status= vm_status,
                    description= vm_description,
                    internal_requester=User.objects.get(username=vm_patch_responsible),
                    date_required='1999-01-01',
                    patch_responsible_id=User.objects.get(username=vm_patch_responsible).id,
                )

  ##              a.save()

    # vm_name = '00-ashtest'
    # vm_type = 'legacy'
    # vm_status = 'deprecated'
    # vm_description = 'Added automatically'
    # vm_internal_requester  ='aharwood'
    # vm_date_required = '1999-01-01'
    # vm_patch_responsible = 'aharwood'
    #
    # try:
    #     a = VM.objects.get(name=vm_name)
    #     print "vm name already exists"
    #     sys.exit()
    # except:
    #
    #     print "Creating: %s" % vm_name
    #
    #     a= VM(
    #         name=vm_name,
    #         type= vm_type,
    #         status= vm_status,
    #         description= vm_description,
    #         internal_requester=User.objects.get(username=vm_patch_responsible),
    #         date_required='1999-01-01',
    #         patch_responsible_id=User.objects.get(username=vm_patch_responsible).id,
    #     )
    #
    #     a.save()