#
# Tidy up documentation links by removing whitespace, trailing slashes and any hash text
#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
from cedainfoapp.models import *
import helpscoutdocs

def service_doc_fix():

    services = NewService.objects.all()

    for service in services:
        if service.documentation:
            
            if '#' in service.documentation:
                print (service.documentation)
                index = service.documentation.find('#')
                service.documentation = service.documentation[:index]
                print (service.name, service.documentation)
                service.save()

            tidy_link = service.documentation.strip()
            tidy_link = tidy_link.rstrip('/')

            if tidy_link != service.documentation:
                print ('Old: %s New: %s' % (service.documentation, tidy_link))
                service.documentation = tidy_link
                service.save()

def run():

    service_doc_fix()
  
