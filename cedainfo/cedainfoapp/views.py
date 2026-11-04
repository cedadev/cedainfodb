# Create your views here.

from django.db.models import Q
from django.http import HttpResponse
from cedainfoapp.models import *
from cedainfoapp.forms import *
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic.list import ListView
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.context_processors import csrf

from . import helpscoutdocs

from .SortHeaders import SortHeaders

import re
import requests
import datetime
import time
import http.client
import random
import ssl
from cedainfoapp.uptimerobot import get_all_monitors

logging = settings.LOG



@login_required()
def home(request):
    # Home page view
    return render(request, "cedainfoapp/home.html", {"user": request.user})


# list of VMRequests presented for external viewers
@login_required()
def vmrequest_list(request):
    o = request.GET.get("o", "id")  # default order is ascending id

    filter = {}
    if request.method == "POST":  # if form was submitted
        form = VMRequestListFilterForm(
            request.POST,
            initial={"request_status": "ceda approved"},
        )
        filter["request_status"] = request.POST["request_status"]
        items = VMRequest.objects.filter(
            request_status__exact=filter["request_status"]
        ).order_by(o)
    else:  # provide a blank form
        form = VMRequestListFilterForm(
            initial={"request_status": "ceda approved"},
        )
        items = VMRequest.objects.order_by(o)

    for item in items:
        try:
            item.name_found = check_dns_entry(item.vm_name)
        except:
            item.name_found = False

        try:
            item.vm_found = check_dns_entry(item.vm.name)
        except:
            item.vm_found = False

    ctx = {
        "form": form,
        "items": items,
    }

    #    ctx = RequestContext(request, {
    #        'form': form,
    #        'items': items,
    #    })
    #    c.update(csrf(request))
    return render(request, "cedainfoapp/vmrequest_list.html", ctx)


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


@login_required()
def vmrequest_detail(request, id):
    item = get_object_or_404(VMRequest, pk=id)
    form = VMRequestDetailForm(instance=item)
    c = {
        "item": item,
        "form": form,
    }
    return render(request, "cedainfoapp/vmrequest_detail.html", c)


# toggle operational status of a VM
@login_required()
def change_status(request, id):
    vm = VM.objects.get(pk=id)
    error = vm.change_status()
    if error:
        return render(request, "error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.headers["referer"])




#
# The following 'txt' views provide a simple text dump of selected tables. These are intended to be called
# using 'curl' or 'wget' from the command line rather than via a browser. Fields are separated by a tab
# character, which allows them to be simply cut up using the 'cut' command. The list of vms was requested by
# Peter Chiu. I added the host list for good measure (actually, I implemented it by mistake!).
#
# Note that they should not require a django login - curl or wget can't get past this. Instead, any
# security required should be added via the apache configuration for the site.
#
# Andrew 06/09/13
#
def txt_host_list(request):
    o = request.GET.get("o", "id")  # default order is ascending id
    subset = request.GET.get("subset", None)  # default order is ascending id

    # define the queryset, using the subset if available
    if subset == "active":
        hosts = Host.objects.filter(retired_on=None).order_by(o)
    else:
        hosts = Host.objects.all().order_by(o)

    output = ""

    fields = (
        "hostname",
        "ip_addr",
        "serial_no",
        "po_no",
        "organization",
        "supplier",
        "arrival_date",
        "planned_end_of_life",
        "retired_on",
        "mountpoints",
        "ftpmountpoints",
        "host_type",
        "os",
        "capacity",
    )

    for field in fields:
        output += field + "\t"
    output += "\n"

    for host in hosts:
        for field in fields:
            output += str(getattr(host, field))
            output += "\t"

        output += "\n"

    return HttpResponse(output, content_type="text/plain")


def txt_vms_list(request, vmname=""):
    if vmname:
        vm = VM.objects.filter(name=vmname)[0]

        output = ""

        fields = (
            "name",
            "type",
            "operation_type",
            "internal_requester",
            "description",
            "date_required",
            "cpu_required",
            "memory_required",
            "disk_space_required",
            "disk_activity_required",
            "network_required",
            "os_required",
            "other_info",
            "patch_responsible",
            "status",
            "created",
            "end_of_life",
            "retired",
            "timestamp",
        )

        for field in fields:
            output += field + ":\t"
            output += str(getattr(vm, field)) + "\n"

    else:
        vms = VM.objects.all().order_by("name")

        output = ""

        fields = (
            "name",
            "type",
            "operation_type",
            "internal_requester",
            "date_required",
            "cpu_required",
            "memory_required",
            "disk_space_required",
            "disk_activity_required",
            "network_required",
            "os_required",
            "other_info",
            "patch_responsible",
            "status",
            "created",
            "end_of_life",
            "retired",
            "timestamp",
        )

        for field in fields:
            output += field + "\t"
        output += "\n"

        for vm in vms:
            for field in fields:
                output += str(getattr(vm, field))
                output += "\t"

            output += "\n"

    return HttpResponse(output, content_type="text/plain")


def txt_service_list(request, vmname=""):
    if vmname:
        fields = ("name", "documentation")
        recs = NewService.objects.filter(host__name=vmname).exclude(
            status="decomissioned"
        )
    else:
        fields = ("name", "documentation", "host", "status")
        recs = NewService.objects.all().exclude(status="decomissioned").order_by("host")

    output = ""

    for field in fields:
        output += field + "\t"
    output += "\n"

    for rec in recs:
        for field in fields:
            output += str(getattr(rec, field))
            output += "\t"

        output += "\n"

    return HttpResponse(output, content_type="text/plain")


def txt_service_list2(request, vmname=""):
    if vmname:
        fields = ("name", "service_manager", "ports", "infolink", "documentation")
        recs = NewService.objects.filter(host__name=vmname).exclude(
            status="decomissioned"
        )
    else:
        fields = (
            "name",
            "service_manager",
            "ports",
            "infolink",
            "documentation",
            "host",
            "status",
        )
        recs = NewService.objects.all().exclude(status="decomissioned").order_by("host")

    output = ""

    for field in fields:
        output += field.capitalize() + "\t"
    output += "\n"

    for rec in recs:
        for field in fields:
            if field == "infolink":
                output += (
                    "http://cedadb.ceda.ac.uk/admin/cedainfoapp/newservice/%s/"
                    % str(rec.id)
                )
                output += "\t"
            else:
                output += str(getattr(rec, field))
                output += "\t"

        output += "\n"

    return HttpResponse(output, content_type="text/plain")


def txt_vm_request_list(request):
    vms = VMRequest.objects.all().order_by("vm_name")

    output = ""

    fields = (
        "vm_name",
        "type",
        "operation_type",
        "internal_requester",
        "date_required",
        "cpu_required",
        "memory_required",
        "disk_space_required",
        "disk_activity_required",
        "network_required",
        "os_required",
        "patch_responsible",
        "request_status",
        "end_of_life",
        "timestamp",
    )

    for field in fields:
        output += field + "\t"
    output += "\n"

    for vm in vms:
        for field in fields:
            try:
                output += str(getattr(vm, field))
            except:
                output += "Error extracting"

            output += "\t"

        output += "\n"

    return HttpResponse(output, content_type="text/plain")


@login_required()
def service_list_by_vm(request):
    HEADERS = (
        ("Name", "name"),
        ("Sysadmin", "patch_responsible__username"),
    )

    service_status = request.GET.get("status", "production")
    myform = ServiceForm(
        initial={"status": service_status},
    )

    sort_headers = SortHeaders(request, HEADERS)

    headers = list(sort_headers.headers())

    allvms = VM.objects.all()
    allvms = allvms.order_by(sort_headers.get_order_by())

    for vm in allvms:
        if vm.patch_responsible.username == "nobody":
            vm.patch_responsible.username = ""

    vms = []

    for vm in allvms:
        recs = NewService.objects.filter(host__name=vm.name).order_by("name")

        if service_status:
            recs = recs.filter(status=service_status)
        if len(recs) > 0:
            vm.prodservices = recs
            vms.append(vm)

    return render(request, "services/list_by_vm.html", locals())


@login_required()
def service_internet_facing(request):
    HEADERS = (
        ("Name", "name"),
        ("Sysadmin", "patch_responsible__username"),
    )

    sort_headers = SortHeaders(request, HEADERS)

    headers = list(sort_headers.headers())

    allvms = VM.objects.all()
    allvms = allvms.order_by(sort_headers.get_order_by())

    for vm in allvms:
        if vm.patch_responsible.username == "nobody":
            vm.patch_responsible.username = ""

    vms = []

    for vm in allvms:
        #
        #       Only continue if this vm has at least one external facing service
        #
        ext_services = (
            NewService.objects.filter(host__name=vm.name)
            .filter(status="production")
            .filter(Q(visibility="restricted") | Q(visibility="public"))
        )
        if not ext_services:
            continue

        recs = NewService.objects.filter(host__name=vm.name).order_by("name")

        if len(recs) > 0:
            vm.prodservices = recs
            vms.append(vm)

    return render(request, "services/internet_facing_service_list.html", locals())


@login_required()
def service_unusedvms(request):
    HEADERS = (
        ("Name", "name"),
        ("Sysadmin", "patch_responsible__username"),
        ("Type", "type"),
        ("Operation type", "operation_type"),
        ("Created", "created"),
        ("Internal requester", "internal_requester__username"),
    )

    service_status = request.GET.get("status", "production")
    myform = ServiceForm(
        initial={"status": service_status},
    )

    sort_headers = SortHeaders(request, HEADERS)

    headers = list(sort_headers.headers())

    allvms = VM.objects.all()
    allvms = allvms.order_by(sort_headers.get_order_by())

    for vm in allvms:
        if vm.patch_responsible.username == "nobody":
            vm.patch_responsible.username = ""

    vms = []

    for vm in allvms:
        #        if 'dev.' in vm.name or 'test.' in vm.name or 'dev1.' in vm.name or 'test1.' in vm.name:
        #    continue

        if vm.status == "retired":
            continue

        if vm.type == "legacy":
            continue

        if (
            vm.operation_type == "development"
            or vm.operation_type == "test"
            or vm.operation_type == "research"
        ):
            continue

        services = NewService.objects.filter(host__name=vm.name)

        recs = NewService.objects.filter(host__name=vm.name).filter(status="production")
        nprod = len(recs)

        recs = NewService.objects.filter(host__name=vm.name).filter(
            status="pre-production"
        )
        npreprod = len(recs)

        if nprod + npreprod == 0:
            vm.nservices = len(services)
            vms.append(vm)

    return render(request, "services/list_unused_vms.html", locals())


@login_required()
def service_review_selection(request):
    HEADERS = (
        ("Name", "name"),
        ("Host", "host"),
        ("Review Status", "review_status"),
        ("Last reviewed", "last_reviewed"),
        ("Visibility", "visibility"),
        ("Manager", "service_manager"),
        ("Owner", "owner"),
        ("Status", "status"),
    )

    review_status = request.GET.get("review_status", "")
    visibility = request.GET.get("visibility", "")
    status = request.GET.get("status", "")

    myform = ServiceForm(
        initial={
            "review_status": review_status,
            "visibility": visibility,
            "status": status,
        }
    )

    sort_headers = SortHeaders(request, HEADERS)

    headers = list(sort_headers.headers())

    services = NewService.objects.all()

    if review_status:
        services = services.filter(review_status=review_status)
    if visibility:
        services = services.filter(visibility=visibility)
    if status:
        services = services.filter(status=status)

    services = services.order_by(sort_headers.get_order_by())

    return render(request, "services/review_selection.html", locals())


@login_required()
def uptimerobot_monitors(request):
    monitors = get_all_monitors()
    monitors = sorted(monitors, key=lambda d: d["friendly_name"].lower())
    services = NewService.objects.filter(uptimerobot_monitor_id__isnull=False).exclude(
        status="decomissioned"
    )

    for monitor in monitors:
        for service in services:
            if service.uptimerobot_monitor_id:
                if monitor["id"] == service.uptimerobot_monitor_id:
                    monitor["has_service"] = True
                    break

    return render(request, "cedainfoapp/uptimerobot_monitors.html", locals())


@login_required()
def service_uptime_robot_check(request):
    HEADERS = (
        ("Service name", "name"),
        ("Visibility", "visibility"),
        ("Status", "status"),
        ("Priority", "priority"),
        ("Monitor ID", "uptimerobot_monitor_id"),
        ("Service url", "url"),
    )

    sort_headers = SortHeaders(request, HEADERS)

    headers = list(sort_headers.headers())

    services = NewService.objects.filter(status="production")

    services = services.order_by(sort_headers.get_order_by())

    monitors = get_all_monitors()

    for service in services:
        if service.uptimerobot_monitor_id:
            res = next(
                (
                    monitor
                    for monitor in monitors
                    if monitor["id"] == service.uptimerobot_monitor_id
                ),
                None,
            )
            if res:
                service.monitor = res

    return render(
        request, 
        "services/service_uptime_robot_check.html",
        locals(),
    )

@login_required()
def service_cert_check(request):

    HEADERS = (
        ("Service name", "name"),
        ("Visibility", "visibility"),
        ("Status", "status"),
        ("Host", "host"),
        ("Service url", "url"),
    )

    orderby = None

    if request.method == 'GET' and 'orderby' in request.GET:
        orderby = request.GET['orderby']

    sort_headers = SortHeaders(request, HEADERS)

    headers = list(sort_headers.headers())

    services = NewService.objects.filter(status="production")
    services = services.order_by(sort_headers.get_order_by())

    for service in services:
        service.cert_expire_date = '01-jan-1900'
        service.cert_issuer = ''

        if service.url:
            service.domain = get_domain(service.url)

            if check_dns_entry(service.domain):
                (expireDate, issuer) = get_certificate_details (service.domain)

                if issuer:
                    service.cert_issuer = issuer
                if expireDate:
                    service.cert_expire_date = expireDate
                else:
                    service.cert_invalid = True

    if orderby == 'cert-issuer':
        services = sorted(services, key=lambda d: d.cert_issuer) 
    if orderby == 'cert-expire-date':
        services = sorted(services, key=lambda d: datetime.datetime.strptime(d.cert_expire_date, "%d-%b-%Y"))


    return render(
        request,
        "services/cert_check.html",
        locals(),
    )

def get_domain (url):

    domain = url.replace('https://', '')
    domain = domain.replace('http://', '')
    loc = domain.find('/')

    if loc != -1:
        domain = domain[0:loc]
    
    domain = domain.strip()

    return domain

def fetch_certificate (domain):
     
    PORT = 443

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, PORT), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                certificate = ssock.getpeercert()

        return certificate
    except:
        return None           

def get_certificate_details (domain):

    certificate = fetch_certificate(domain)
    expireDate = None
    issuer = None


    if certificate:

        #issuer = certificate["issuer"][1][0][1])

        expireDate = datetime.datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expireDate = datetime.datetime.strftime(expireDate, '%d-%b-%Y')

        issuer_org = certificate["issuer"][1][0][1]
        issuer_type = certificate["issuer"][2][0][1]

        if issuer_org == "Let's Encrypt": 
            issuer = "LetsEncrypt"
        else:
            issuer = "Other"

    return (expireDate, issuer)

@login_required()
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
        helpscout_urls.append(doc.json()["article"]["publicUrl"])

    for service in services:
        if service.documentation and service.documentation not in helpscout_urls:
            service.url_ok = _url_exists(service.documentation)
            not_in_helpscout.append(service)
    #
    #   Get docs which are not linked to an active service record
    #
    not_in_cedainfodb = []

    for url in helpscout_urls:
        found = False

        for service in services:
            if service.documentation and service.documentation == url:
                found = True

        if not found:
            not_in_cedainfodb.append(url)

    return render(request, "services/doc_check.html", locals())


@login_required()
def decomissioned_service_doc_check(request):
    in_current = []

    services = NewService.objects.filter(status="decomissioned")

    helpscout_urls = helpscoutdocs.get_article_urls(
        helpscoutdocs.SERVICES_COLLECTION_ID
    )

    for service in services:
        if service.documentation and service.documentation in helpscout_urls:
            service.url_ok = _url_exists(service.documentation)
            in_current.append(service)

    return render(request, "services/decomissioned_doc_check.html", locals())


@login_required()
def vm_ping_check(request):
    vms = VM.objects.exclude(status="retired")

    missing = []

    for vm in vms:
        name = vm.name
        name = name.replace("legacy:", "")
        (output, error) = subprocess.Popen(
            "ping -W1 -c 1 %s" % name,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        ).communicate()
        if error:
            missing.append(vm)

    #        if len(missing) > 2:
    #            break

    return render(request, "vm_ping_check.html", locals())


def _url_exists(url):
    r = requests.get(url)

    return r.status_code == 200


def _list_duplicates(seq):
    #
    #  Returns duplicate values from array
    #
    seen = set()
    seen_add = seen.add
    seen_twice = set(x for x in seq if x in seen or seen_add(x))
    return list(seen_twice)


@login_required()
def service_owner_manager_list(request):
    persons = Person.objects.order_by("name")

    counts = []

    services = NewService.objects.filter(status="production")

    for person in persons:
        owner_count = (
            NewService.objects.filter(owner__username=person.username)
            .filter(status="production")
            .count()
        )
        manager_count = (
            NewService.objects.filter(service_manager__username=person.username)
            .filter(status="production")
            .count()
        )
        deputy_manager_count = (
            NewService.objects.filter(deputy_service_manager__username=person.username)
            .filter(status="production")
            .count()
        )
        vm_count = (
            VM.objects.filter(internal_requester__username=person.username)
            .filter(status="active")
            .count()
        )

        rec = {}
        rec["name"] = person.name
        rec["username"] = person.username
        rec["owner_count"] = owner_count
        rec["manager_count"] = manager_count
        rec["deputy_manager_count"] = deputy_manager_count
        rec["vm_count"] = vm_count
        total = owner_count + manager_count + deputy_manager_count

        #        counts.append(rec)

        if total > 0:
            counts.append(rec)

    return render(request, "services/service_owner_manager_list.html", locals())


@login_required()
def service_list_for_team_members(request):
    username = request.GET.get("username", None)
    person = Person.objects.get(username=username)

    SERVICE_HEADERS = (
        ("Name", "name"),
        ("Docs", "documentation"),
        ("Host", "host"),
        ("OS", "host__os_required"),
        ("Visibility", "visibility"),
        ("Status", "status"),
        ("Priority", "priority"),
        ("Owner", "owner"),
        ("Manager", "service_manager"),
        ("Deputy manager", "deputy_service_manager"),
    )

    owner_sort_headers = SortHeaders(request, SERVICE_HEADERS)
    owner_headers = list(owner_sort_headers.headers())

    owner_services = NewService.objects.filter(owner__username=username).order_by(
        "name"
    )
    owner_services = owner_services.filter(status="production") | owner_services.filter(
        status="pre-production"
    )
    owner_services = owner_services.order_by(owner_sort_headers.get_order_by())

    manager_sort_headers = SortHeaders(request, SERVICE_HEADERS)
    manager_headers = list(manager_sort_headers.headers())

    manager_services = NewService.objects.filter(
        service_manager__username=username
    ).order_by("name")
    manager_services = manager_services.filter(
        status="production"
    ) | manager_services.filter(status="pre-production")
    manager_services = manager_services.order_by(manager_sort_headers.get_order_by())

    deputy_manager_sort_headers = SortHeaders(request, SERVICE_HEADERS)
    deputy_manager_headers = list(deputy_manager_sort_headers.headers())

    deputy_manager_services = NewService.objects.filter(
        deputy_service_manager__username=username
    ).order_by("name")
    deputy_manager_services = deputy_manager_services.filter(
        status="production"
    ) | deputy_manager_services.filter(status="pre-production")
    deputy_manager_services = deputy_manager_services.order_by(
        deputy_manager_sort_headers.get_order_by()
    )

    active_vms = VM.objects.filter(internal_requester__username=person.username).filter(
        status="active"
    )

    return render(request, "services/list_services_for_team_members.html", locals())



@login_required()
def service_stats (request):
 
    services = NewService.objects.filter(status="production").order_by("name")
    
    data_array = []
    
    data_array.append(['GitHub pages', len(services.filter(host__name='00 GitHub Pages'))])
    data_array.append(['Cloud VM', len(services.filter(host__name='00 cloud'))])
    data_array.append(['kubernetes', len(services.filter(host__name='00 kubernetes'))])    
    data_array.append(['Hosted elsewhere', len(services.filter(host__name='00 unspecified'))])
    data_array.append(['R9', len(services.filter(host__name='00 unspecified R9'))])
 #
 # Assume that any service that does not have a hostname starting with '00' is a regular VM deployment
 #   
    data_array.append(['VM', len(NewService.objects.exclude(host__name__startswith='00').filter(status='production'))])
                
    h_title = 'Production services by deployment type'	    
    return render(request, "services/stats.html", locals())


def approve_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.approve()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.headers["referer"])


# convert an existing vmrequest into a vm
@login_required()
def convert_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.convert()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.headers["referer"])


# create an update request for a VM
@login_required()
def create_vm_update_request(request, id):
    vm = VM.objects.get(pk=id)
    reqid = vm.create_update_request()
    if reqid:
        return redirect("/admin/cedainfoapp/vmrequest/%i" % reqid)
    else:
        return render(
            "error.html", {"error": "no update id generated", "user": request.user}
        )

def reject_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.reject()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.headers["referer"])

