import os
import sys


sys.path.append('/usr/local/cedainfodb/releases/current/cedainfo')


from django.core.management import setup_environ
from django.conf import settings
import settings as dbsettings
import requests

setup_environ(dbsettings)

from cedainfoapp.models import *





#articles = _download_helpscout_service_articles ('59b25ba1042863033a1caf8f')
AUTH = ('47ff11d6d6207a05189271b8805a8b888533a49a', 'X')

list_url = 'https://docsapi.helpscout.net/v1/collections/%s/categories' % '59b25ba1042863033a1caf8f'
r = requests.get(list_url, auth=AUTH)

ncategories = len(r.json()["categories"]["items"])


for n in range(0, ncategories):

    print(r.json()["categories"]["items"][n]["name"], r.json()["categories"]["items"][n]["id"])

sys.exit()



