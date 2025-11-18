#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
from cedainfoapp.models import *
import helpscoutdocs

def _list_duplicates(seq):
    #
    #  Returns duplicate values from array
    #
    seen = set()
    seen_add = seen.add
    seen_twice = set(x for x in seq if x in seen or seen_add(x))
    return list(seen_twice)

def _url_exists(url):
    r = requests.get(url)

    return r.status_code == 200

def service_doc_check(request):
    #
    #   Get duplicate docs links
    #
    services = NewService.objects.all()

    urls = []

    for service in services:
        if service.documentation:
            urls.append(service.documentation)

    duplicate_docs = _list_duplicates(urls)

    duplicates = []

    for d in duplicate_docs:
        rec = {}
        rec["doc"] = d
        rec["services"] = []

        res = NewService.objects.filter(documentation=d)

        for r in res:
            rec["services"].append(r)

        duplicates.append(rec)
    #
    #   Get services where doc is not in correct collection and category
    #
    not_in_helpscout = []

    services = NewService.objects.exclude(status="decomissioned")

    collection = helpscoutdocs.get_collection(helpscoutdocs.SERVICES_COLLECTION_ID)

    docs = helpscoutdocs.get_articles_in_category(
        collection, helpscoutdocs.SERVICES_DOCUMENTATION_CATEGORY_ID
    )

    helpscout_urls = []

    for doc in docs:
        print (doc.json()["article"])
        sys.exit()
        helpscout_urls.append(doc.json()["article"]["publicUrl"])

    for service in services:
        if service.documentation and service.documentation not in helpscout_urls:
            service.url_ok = _url_exists(service.documentation)
            not_in_helpscout.append(service)
    #
    #   Get docs which are not linked to an active service record
    #
    # not_in_cedainfodb = []

    # for url in helpscout_urls:
    #     found = False

    #     for service in services:
    #         if service.documentation and service.documentation == url:
    #             found = True

    #     if not found:
    #         not_in_cedainfodb.append(url)


def run():

    service_doc_check('a')
  #  services = NewService.objects.all()


   # for service in services:
    #    if service.status == 'production':
     #       if service.host:
      #          print (service.host.name)
        

