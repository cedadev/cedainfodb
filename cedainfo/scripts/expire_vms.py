#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
# https://towardsaws.com/use-python-to-check-ssl-tls-certificate-expiration-and-notify-with-aws-ses-1ce17ed25616

import sys

from cedainfoapp.models import *
import datetime
#import OpenSSL
import ssl


def check_dns_entry(hostname):
    #
    #   Check if dns entry for given host exits
    #
    import socket

    try:
        address = socket.gethostbyname(hostname)
        return True
    except:
        return False




def run():

    vms = VM.objects.filter(status = 'active').order_by('name')

    for vm in vms:
        if not check_dns_entry(vm.name):
            vm.status='retired'
            vm.save()
            print (vm.name, check_dns_entry(vm.name))