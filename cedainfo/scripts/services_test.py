#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
from cedainfoapp.models import *
from datetime import datetime
import OpenSSL
import ssl

def run():

    services = NewService.objects.all()


    for service in services:
        if service.status == 'production':
            if service.url:
                if service.url.startswith('https://'):
                    a = service.url.replace('https://', '')
                    print (a)
        

