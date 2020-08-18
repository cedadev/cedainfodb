import os
import sys


sys.path.append('/usr/local/cedainfodb/releases/current/cedainfo')


from django.core.management import setup_environ
from django.conf import settings
import settings as dbsettings
import requests

setup_environ(dbsettings)

from cedainfoapp.models import *

from . import helpscoutdocs

def list_duplicates(seq):
  seen = set()
  seen_add = seen.add
  seen_twice = set( x for x in seq if x in seen or seen_add(x) )
  return list( seen_twice )
  
  
services = NewService.objects.all()

urls = []

for service in services:
    if service.documentation:
        urls.append(service.documentation)


duplicate_docs = list_duplicates(urls)

duplicates = []


for d in duplicate_docs:
    rec = {}
    rec["doc"] = d
    rec["services"] = []
    
    res = NewService.objects.filter(documentation=d)
    
    for r in res:
        rec["services"].append(r)

    duplicates.append(rec)
    

for d in duplicates:
    print(d["doc"])
    
    for s in d["services"]:
        print(s.name)
