#
#  Copies information from original vm to new vm
#
# Intended to be run via run_script
#
# python ../manage.py runscript copy_vm_info --script-args ~/cedainfodb/vms/batch1.txt
#
import json
import os
import sys
import csv

from cedainfoapp.models import *
from django.contrib.auth.models import *
from django.conf import settings


def run(*script_args):

    vm_file = script_args[0]

    if not vm_file:
        os.exit("No file given")

    with open(vm_file) as csv_file:

        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0

        for row in csv_reader:
            old_vm = row[0]
            vm_name = row[1]
            vm_cpu  = row[2]
            vm_ram  = row[3]
            vm_disk = row[4]
            vm_root_users = row[5]
            vm_tag   = row[6]
            vm_ip    = row[7]
            vm_ip_private = row[8]
            vm_other = row[9]


            print(old_vm, vm_name)
            line_count = line_count + 1

            print(row)

            try:
                old = VM.objects.get(name=old_vm)
            except:
                print("Old machine %s does not exist for new machine %s, skipping" % (old_vm, vm_name))
                continue

            new = VM.objects.get(name=vm_name)

            print(old.type, new.type)
            new.type = old.type

            print(old.operation_type, new.operation_type)
            new.operation_type = old.operation_type

            print(old.internal_requester, new.internal_requester)
            new.internal_requester = old.internal_requester

            description = "centos7 machine to replace %s\n\nDescription copied from %s:\n\n" % (old.name, old.name)
            description = description + old.description
            new.description = description

            print(old.disk_activity_required, new.disk_activity_required)
            new.disk_activity_required = old.disk_activity_required

            print(old.mountpoints_required, new.mountpoints_required)
            new.mountpoints_required = old.mountpoints_required

            print(old.network_required)
            new.network_required = old.network_required

            other = 'This record was generated automatically for centos7 update.\n\n'

            extra = ''
            if vm_tag: extra  +=  "Tags: %s\n" % vm_tag
            if vm_ip: extra  +=  "IP: %s\n" % vm_ip
            if vm_ip_private: extra += "IP (private): %s\n" % vm_ip_private
            if vm_other: extra  +=  "Other information: %s\n" % vm_other

            if extra:
                other += 'Information from VM request:\n\n'
                other += extra

            if old.other_info:
                other += '\nOther information from %s record: \n\n' % old.name
                other += old.other_info

            new.other_info = other

            new.patch_responsible = old.patch_responsible
            new.tenancy = old.tenancy

            new.root_users = old.root_users.all()

            new.save()
