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

from udbadmin.SortHeaders import SortHeaders

import re
import requests
import datetime
import time
import http.client
import random
import ssl
from cedainfoapp.uptimerobot import get_all_monitors

logging = settings.LOG


class HostList(ListView):
    model = Host

    def get_ordering(self):
        ordering = self.request.GET.get("o", "-hostname")
        # validate ordering here
        return ordering


# host_detail view: includes details of host, plus services and history entries for that host
@login_required()
def host_detail(request, host_id):
    url = reverse("cedainfoapp.views.host_list", args=(None,))
    try:
        host = get_object_or_404(Host, pk=host_id)
        services = Service.objects.filter(host=host)
        history = HostHistory.objects.filter(host=host)
        return render(
            request,
            "cedainfoapp/host_detail.html",
            {
                "host": host,
                "services": services,
                "history": history,
                "user": request.user,
            },
        )
    except:
        message = "Unable to find host with id='%s'" % (host_id)
        return render(
            "error.html", {"message": message, "url": url, "user": request.user}
        )


@login_required()
def home(request):
    # Home page view
    return render(request, "cedainfoapp/home.html", {"user": request.user})


@login_required()
def problems(request):
    """Problems view"""
    probs = ["massage1", "message2"]
    fs_probs = FileSet.problems()
    part_probs = Partition.problems()
    audit_probs = Audit.problems()

    return render(
        "cedainfoapp/problems.html",
        {
            "user": request.user,
            "fileset_problems": fs_probs,
            "partition_problems": part_probs,
            "audit_problems": audit_probs,
        },
    )


@login_required()
def fileset_list(request):
    """Barebones list of filesets"""
    o = request.GET.get("o", "id")  # default order is ascending id
    search = request.GET.get("search", "")  # default order is ascending id
    backupinfo = request.GET.get("backupinfo", "")  # default order is ascending id
    qs = FileSet.objects.filter(logical_path__contains=search).order_by(o)

    # Use the object_list view.
    totalalloc = 0
    totaldu = 0
    totalnum = 0
    for fs in qs:
        lastsize = fs.last_size()
        if lastsize:
            totaldu += lastsize.size
            totalnum += lastsize.no_files
        totalalloc += fs.overall_final_size
    return list_detail.object_list(
        request,
        queryset=qs,
        template_name="cedainfoapp/fileset_list.html",
        template_object_name="fileset",
        extra_context={
            "totaldu": totaldu,
            "totalalloc": totalalloc,
            "totalnum": totalnum,
            "search": search,
            "backupinfo": backupinfo,
        },
    )


@login_required()
def underallocated_fs(request):
    qs = FileSet.objects.all()
    filesets = []
    # Use the object_list view.
    for fs in qs:
        lastsize = fs.last_size()
        if lastsize and (lastsize.size > fs.overall_final_size):
            filesets.append(fs)
    return render(
        "cedainfoapp/underallocated.html", {"filesets": filesets, "user": request.user}
    )


@login_required()
def audit_totals(request):
    # view total volume of all analyses audits
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")

    audits = Audit.objects.filter(auditstate="analysed")

    if start:
        start_datetime = datetime.datetime.strptime(start, "%Y-%m-%d")
        audits = audits.filter(starttime__gte=start_datetime)
    if end:
        end_datetime = datetime.datetime.strptime(end, "%Y-%m-%d")
        audits = audits.filter(endtime__lte=end_datetime)

    total_files = 0
    total_volume = 0
    naudits = 0
    total_time = datetime.timedelta(seconds=0)
    for a in audits:
        total_files += a.total_files
        total_volume += a.total_volume
        total_time += a.endtime - a.starttime
        naudits += 1

    return render(
        "cedainfoapp/audit_totals.html",
        {
            "total_files": total_files,
            "total_volume": total_volume,
            "naudits": naudits,
            "start": start,
            "end": end,
            "filesps": total_files / total_time.total_seconds(),
            "volps": total_volume / total_time.total_seconds(),
        },
    )


@login_required()
def audit_trace(request, path):
    # trace a path through audits
    filesets = FileSet.objects.all().order_by("-logical_path")

    audits = []
    for fs in filesets:
        if fs.logical_path == path[0 : len(fs.logical_path)]:
            break

    fsaudits = Audit.objects.filter(auditstate="analysed", fileset=fs).order_by(
        "starttime"
    )
    rel_path = path[len(fs.logical_path) + 1 :]
    for a in fsaudits:
        audits.append(a)
        a.loglines = []
        LOG = open(a.logfile)
        while 1:
            line = LOG.readline()
            if line == "":
                break
            if line[0 : len(rel_path)] == rel_path:
                a.loglines.append(line.strip())

    return render(
        "cedainfoapp/audit_trace.html",
        {"audits": audits, "path": path, "rel_path": rel_path},
    )


def next_audit(request):
    # make a new audit to do next via a remote service - for parallelising on Lotus
    # pick an audit to do:
    # 1) any fileset that has no privious audit
    # 2) any fileset that has oldest audit
    # dont audit fileset where the primary is on tape
    filesets = FileSet.objects.filter(
        storage_pot_type="archive", primary_on_tape=False, storage_pot__isnull=False
    ).exclude(storage_pot="")
    fileset_to_audit = None
    oldest_audit = datetime.datetime.utcnow()
    for f in filesets:
        last_audit = f.last_audit()
        # if no audit done before then use this one
        if last_audit == None:
            fileset_to_audit = f
            break
            # skip if last audit not an analysed state then skip
        if (
            last_audit.auditstate != "analysed"
            and last_audit.auditstate != "copy verified"
        ):
            print(
                "Ignore - last audit not 'analysed' or 'copy verified' state.  state=%s"
                % last_audit.auditstate
            )
            continue
        # see if this is the oldest audit
        if last_audit.starttime < oldest_audit:
            oldest_audit = last_audit.starttime
            fileset_to_audit = f

    if fileset_to_audit:
        audit = Audit(
            fileset=fileset_to_audit,
            auditstate="started",
            starttime=datetime.datetime.utcnow(),
        )
        audit.save()
        # wait a ramdom time and then check there are no other started audits for this fileset
        # this is to solve a race condition
        time.sleep(0.1 * random.randint(1, 100))
        started_audits = Audit.objects.filter(
            fileset=fileset_to_audit, auditstate="started"
        )
        if len(started_audits) != 1:
            audit.delete()
            audit = None
    else:
        audit = None

    return render("cedainfoapp/next_audit.txt", {"audit": audit})


def upload_audit_results(request, id):
    # upload audit results from lotus job
    audit = get_object_or_404(Audit, pk=id)
    fileset = audit.fileset
    error = request.POST["error"]
    if error == "1":
        audit.auditstate = "error"
        audit.endtime = datetime.datetime.utcnow()
        audit.save()
        return render("cedainfoapp/next_audit.txt", {"audit": audit})

    if "checkm_loc" in request.POST:
        checkm = open(request.POST["checkm_loc"]).read()
    else:
        checkm = request.POST["checkm"]
    audit.auditstate = "finished"
    audit.endtime = datetime.datetime.utcnow()
    # make checkm directory for spot is missing
    if not os.path.exists("%s/%s" % (settings.CHECKM_DIR, fileset.storage_pot)):
        os.mkdir("%s/%s" % (settings.CHECKM_DIR, fileset.storage_pot))
    audit.logfile = "%s/%s/checkm.%s.%s.log" % (
        settings.CHECKM_DIR,
        fileset.storage_pot,
        fileset.storage_pot,
        time.strftime("%Y%m%d-%H%M"),
    )
    audit.save()
    LOG = open(audit.logfile, "w")
    LOG.write(checkm)
    LOG.close()

    audit.analyse()

    return render("cedainfoapp/next_audit.txt", {"audit": audit})


def audit_report(request, id):
    # report against a previous audit results
    audit = get_object_or_404(Audit, pk=id)
    prev_audit = audit.prev_audit()
    if prev_audit:
        result = audit.compare(prev_audit)
    else:
        result = None
    return render(
        "cedainfoapp/audit_report.html",
        {
            "audit": audit,
            "prev_audit": prev_audit,
            "result": result,
            "user": request.user,
        },
    )


@login_required()
def partition_list(request):
    o = request.GET.get("o", "id")  # default order is ascending id
    partfilter = request.GET.get("filter", None)  # default order is ascending id
    partitions = Partition.objects.order_by(o)
    filtered_partitions = []
    # list overfilled partitions
    if partfilter == "overfill":
        for p in partitions:
            if (
                100.0 * p.used_bytes / (p.capacity_bytes + 1) > 98.0
                and p.status != "Retired"
            ):
                filtered_partitions.append(p)
                p.used_copy = p.use_summary()
                # list overallocated partitions
    elif partfilter == "overalloc":
        for p in partitions:
            allocated = p.allocated() + p.secondary_allocated()
            if (
                100.0 * allocated / (p.capacity_bytes + 1) > 85.0
                and p.status != "Retired"
            ):
                filtered_partitions.append(p)
    # list unalloced files on partition
    elif partfilter == "unalloc":
        for p in partitions:
            unalloc = (
                p.used_bytes - p.used_by_filesets() + p.secondary_used_by_filesets()
            )
            if (
                100.0 * unalloc / (p.capacity_bytes + 1) > 15.0
                and p.status != "Retired"
            ):
                filtered_partitions.append(p)
    else:
        filtered_partitions = partitions

    # Use the object_list view.
    return render(
        "cedainfoapp/partition_list.html",
        {"partitions": filtered_partitions, "user": request.user},
    )


@login_required()
def partition_vis(request, id):
    part = Partition.objects.get(pk=id)
    filesets = FileSet.objects.filter(partition=part)
    unalloc = part.capacity_bytes
    for f in filesets:
        alloc = f.overall_final_size * 100 / part.capacity_bytes
        # f.vis = '|' * alloc
        f.vis = alloc
        size = f.last_size().size
        f.allocused = min(f.overall_final_size, size)
        f.allocfree = max(f.overall_final_size - size, 0)
        f.overalloc = max(size - f.overall_final_size, 0)
        f.totalsize = max(f.overall_final_size, f.overall_final_size + f.overalloc)
        unalloc -= f.totalsize
    return render(
        "cedainfoapp/partition_vis.html",
        {"part": part, "filesets": filesets, "unalloc": unalloc},
    )


@login_required()
def partition_peplerdiagram(request, id):
    part = Partition.objects.get(pk=id)
    filesets = FileSet.objects.filter(partition=part).order_by("-overall_final_size")
    unalloc = part.capacity_bytes
    for f in filesets:
        alloc = f.overall_final_size * 100 / part.capacity_bytes
        # f.vis = '|' * alloc
        f.vis = alloc
        size = f.last_size().size
        f.allocused = min(f.overall_final_size, size)
        f.allocfree = max(f.overall_final_size - size, 0)
        f.overalloc = max(size - f.overall_final_size, 0)
        f.totalsize = max(f.overall_final_size, f.overall_final_size + f.overalloc)
        unalloc -= f.totalsize
    return render(
        "cedainfoapp/partition_peplerdiagram.html",
        {"part": part, "filesets": filesets, "unalloc": unalloc},
    )


# do df for a partition and redirect back to partitions list
@login_required()
def df(request, id):
    part = Partition.objects.get(pk=id)
    part.df()
    return redirect(request.META["HTTP_REFERER"])


# do du for a fileset and redirect back to fileset list
@login_required()
def du(request, id):
    fileset = FileSet.objects.get(pk=id)
    fileset.du()
    return redirect(request.META["HTTP_REFERER"])


@login_required()
def markcomplete(request, id):
    fileset = FileSet.objects.get(pk=id)
    confirm = request.GET.get("confirm", None)
    if confirm != None:
        fileset.complete = True
        fileset.complete_date = datetime.datetime.now()
        fileset.save()
        return redirect("/admin/cedainfoapp/fileset/%s" % id)
    else:
        return render(
            "cedainfoapp/fileset_markcomplete.html",
            {"fileset": fileset, "user": request.user},
        )

    # create storage pot and link archive


@login_required()
def storagesummary(request):
    parts = Partition.objects.all()
    sumtable = [
        {
            "status": "Blank",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
        {
            "status": "Allocating",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
        {
            "status": "Allocating_ps",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
        {
            "status": "Closed",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
        {
            "status": "Migrating",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
        {
            "status": "Retired",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
        {
            "status": "Total",
            "npart": 0,
            "used": 0,
            "allocated": 0,
            "allocused": 0,
            "sec_allocated": 0,
            "sec_allocused": 0,
            "capacity": 0,
        },
    ]
    index = {}
    for i in range(len(sumtable)):
        index[sumtable[i]["status"]] = i

    for part in parts:
        i = index[part.status]
        sumtable[i]["npart"] += 1
        sumtable[i]["used"] += part.used_bytes
        sumtable[i]["allocated"] += part.allocated()
        sumtable[i]["allocused"] += part.used_by_filesets()
        sumtable[i]["sec_allocated"] += part.secondary_allocated()
        sumtable[i]["sec_allocused"] += part.secondary_used_by_filesets()
        sumtable[i]["capacity"] += part.capacity_bytes
        sumtable[6]["npart"] += 1
        sumtable[6]["used"] += part.used_bytes
        sumtable[6]["allocated"] += part.allocated()
        sumtable[6]["allocused"] += part.used_by_filesets()
        sumtable[6]["sec_allocated"] += part.secondary_allocated()
        sumtable[6]["sec_allocused"] += part.secondary_used_by_filesets()
        sumtable[6]["capacity"] += part.capacity_bytes

    return render(
        "cedainfoapp/sumtable.html", {"sumtable": sumtable, "user": request.user}
    )


# needs to be public to interact with scripts.
def primary_on_tape(request):
    """List filesets where the data is parimary on tape."""
    filesets = FileSet.objects.filter(
        sd_backup=True, storage_pot__isnull=False, primary_on_tape=True
    ).exclude(storage_pot="")
    return render(
        "cedainfoapp/primary_on_tape.txt",
        {"filesets": filesets, "user": request.user},
        content_type="text/plain",
    )


# needs to be public to interact with scripts.
def storaged_spotlist(request):
    #    filesets = FileSet.objects.filter(logical_path__startswith='/badc')
    withpath = request.GET.get("withpath", None)
    filesets = FileSet.objects.filter(
        sd_backup=True, storage_pot__isnull=False
    ).exclude(storage_pot="")
    if withpath != None:
        return render(
            "cedainfoapp/storage-d_spotlist_withpath.html",
            {"filesets": filesets, "user": request.user},
            content_type="text/plain",
        )
    else:
        return render(
            "cedainfoapp/storage-d_spotlist.html",
            {"filesets": filesets, "user": request.user},
            content_type="text/plain",
        )


#
# Provide 'external' access to simple list of spots for use by e-science. Login is disabled for this view. If any access protection is required then it can be added to the apache configuration file.
#
def storaged_spotlist_public(request):
    filesets = FileSet.objects.filter(
        sd_backup=True, storage_pot__isnull=False
    ).exclude(storage_pot="")

    output = ""

    for fs in filesets:
        output += fs.storage_pot + "\n"

    return HttpResponse(output, content_type="text/plain")


@login_required()
def detailed_spotlist(request):
    """detailed table of spots including latest FSSM for each one"""
    filesets = FileSet.objects.filter(
        sd_backup=True, storage_pot__isnull=False
    ).exclude(storage_pot="")
    for fs in filesets:
        # find FSSMs for this fs ordered by date
        fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by("-date")
        if len(fssms) > 0:
            fs.latest_size = fssms[len(fssms) - 1]
        else:
            fs.latest_suze = 0
    return render(
        "cedainfoapp/detailed_spotlist.html",
        {"filesets": filesets, "user": request.user},
        content_type="text/plain",
    )


# make list of rsync commands for makeing a secondary copies
# needs to be open for automation
#
def make_secondary_copies(request):
    filesets = FileSet.objects.filter(secondary_partition__isnull=False).exclude(
        storage_pot=""
    )
    return render(
        "cedainfoapp/make_secondary_copies.txt",
        {"filesets": filesets, "user": request.user},
        content_type="text/plain",
    )


# make list of download stats configuration
# needs to be open for automation
#
def download_conf(request):
    filesets = FileSet.objects.all().exclude(storage_pot="")
    return render(
        "cedainfoapp/download_conf.txt",
        {"filesets": filesets, "user": request.user},
        content_type="text/plain",
    )


# make list filesets for depositserver
# needs to be open for automation
#
def complete_filesets(request):
    filesets = FileSet.objects.all()
    return render(
        "cedainfoapp/complete.txt",
        {"filesets": filesets, "user": request.user},
        content_type="text/plain",
    )


# make list filesets for access stats
# needs to be open for automation
#
def spotlist(request):
    filesets = FileSet.objects.all()
    return render(
        "cedainfoapp/spotlist.txt",
        {"filesets": filesets, "user": request.user},
        content_type="text/plain",
    )


# make a fileset from simple web request.
def make_fileset(request):
    path = request.GET.get("path", None)
    size_in = request.GET.get("size", None)
    on_tape = request.GET.get("on_tape", False)
    simple = request.GET.get("simple", False)
    if simple:
        template = "cedainfoapp/fileset_make_simple.json"
        mimetype = "application/json"
    else:
        template = "cedainfoapp/fileset_make.html"
        mimetype = "text/html"

    # check parameters ok
    if path is None:
        return render(
            template,
            {
                "path": path,
                "size": size_in,
                "fileset_created": False,
                "message": "no path specified",
            },
            content_type=mimetype,
        )
    if not size_in:
        return render(
            template,
            {
                "path": path,
                "size": size_in,
                "fileset_created": False,
                "message": "no size specified",
            },
            content_type=mimetype,
        )

    # make sure filesets have no spaces or slashes at the end
    path = path.strip()
    path = path.rstrip("/")

    # Find size
    if size_in[-2:].upper() == "KB":
        size = int(size_in[0:-2]) * 1000
    elif size_in[-2:].upper() == "MB":
        size = int(size_in[0:-2]) * 1000000
    elif size_in[-2:].upper() == "GB":
        size = int(size_in[0:-2]) * 1000 * 1000000
    elif size_in[-2:].upper() == "TB":
        size = int(size_in[0:-2]) * 1000000 * 1000000
    else:
        size = int(size_in)

    new_fs = FileSet(logical_path=path, overall_final_size=size)
    try:
        new_fs.make_fileset(path, size, on_tape)
    except FilseSetCreationError:
        error_msg = "Fileset creation error: %s" % sys.exc_info()[1]
        return render(
            template,
            {
                "path": path,
                "size": size_in,
                "fileset_created": False,
                "message": error_msg,
            },
            content_type=mimetype,
        )

    return render(
        template,
        {
            "path": "",
            "size": "",
            "fileset_created": True,
            "message": "Fileset created.",
            "fs": new_fs,
        },
        content_type=mimetype,
    )


def split_fileset(request):
    path = request.GET.get("path", None)
    size_in = request.GET.get("size", None)
    if path == None:
        return render(
            "cedainfoapp/fileset_split.html",
            {"path": path, "size": size_in, "error": "Need a path."},
        )
    if size_in == None:
        return render(
            "cedainfoapp/fileset_split.html",
            {"path": path, "size": size_in, "error": "Need a size."},
        )

        # make sure filesets have no spaces or slashes at the end
    path = path.strip()
    path = path.rstrip("/")

    # Find size
    if size_in[-2:].upper() == "KB":
        size = int(size_in[0:-2]) * 1000
    elif size_in[-2:].upper() == "MB":
        size = int(size_in[0:-2]) * 1000000
    elif size_in[-2:].upper() == "GB":
        size = int(size_in[0:-2]) * 1000 * 1000000
    elif size_in[-2:].upper() == "TB":
        size = int(size_in[0:-2]) * 1000000 * 1000000
    else:
        size = int(size_in)

    # find parent fileset
    filesets = FileSet.objects.all()
    parent = None
    # find fileset to break
    for f in filesets:
        if f.logical_path == path[0 : len(f.logical_path)]:
            if parent == None:
                parent = f
            elif len(parent.logical_path) < len(f.logical_path):
                parent = f
            print(f, parent)

    # if no parent found exit
    if parent == None:
        return render(
            "cedainfoapp/fileset_split.html",
            {"path": path, "size": size_in, "error": "No parent fileset found"},
        )

    try:
        new_fs = parent.split_fileset(path, size)
    except FilseSetCreationError:
        return render(
            "cedainfoapp/fileset_split.html",
            {
                "path": path,
                "size": size_in,
                "error": "Fileset split error: %s" % sys.exc_info()[1],
            },
        )

    return render(
        "cedainfoapp/fileset_split.html",
        {"path": path, "size": size_in, "error": "Fileset split.", "fs": new_fs},
    )


# approve an existing gwsrequest
@login_required()
def reject_gwsrequest(request, id):
    gwsrequest = GWSRequest.objects.get(pk=id)
    error = gwsrequest.reject()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.META["HTTP_REFERER"])


# approve an existing gwsrequest
@login_required()
def approve_gwsrequest(request, id):
    gwsrequest = GWSRequest.objects.get(pk=id)
    error = gwsrequest.approve()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.META["HTTP_REFERER"])


# convert an existing gwsrequest into a gws
@login_required()
def convert_gwsrequest(request, id):
    gwsrequest = GWSRequest.objects.get(pk=id)
    error = gwsrequest.convert()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.META["HTTP_REFERER"])


# create an update request for a GWS
@login_required
def create_gws_update_request(request, id):
    gws = GWS.objects.get(pk=id)
    reqid = gws.create_update_request()
    if reqid:
        return redirect("/admin/cedainfoapp/gwsrequest/%i" % reqid)
    else:
        return render(
            "error.html", {"error": "no update id generated", "user": request.user}
        )


# convert an existing vmrequest into a vm
@login_required()
def reject_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.reject()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.META["HTTP_REFERER"])


# convert an existing vmrequest into a vm
@login_required()
def approve_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.approve()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.META["HTTP_REFERER"])


# convert an existing vmrequest into a vm
@login_required()
def convert_vmrequest(request, id):
    vmrequest = VMRequest.objects.get(pk=id)
    error = vmrequest.convert()
    if error:
        return render("error.html", {"error": error, "user": request.user})
    else:
        return redirect(request.META["HTTP_REFERER"])


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


# list of GWSs presented for external viewers
@login_required()
def gwsrequest_list(request):
    o = request.GET.get("o", "id")  # default order is ascending id

    filter = {}
    if request.method == "POST":  # if form was submitted
        form = GWSRequestListFilterForm(
            request.POST,
            initial={"request_status": "ceda approved"},
        )
        filter["request_status"] = request.POST["request_status"]
        items = GWSRequest.objects.filter(
            request_status__exact=filter["request_status"]
        ).order_by(o)
    else:  # provide a blank form
        form = GWSRequestListFilterForm(
            initial={"request_status": "ceda approved"},
        )
        items = GWSRequest.objects.order_by(o)

    c = {
        "form": form,
        "items": items,
    }

    return render("cedainfoapp/gwsrequest_list.html", c)


@login_required()
def gwsrequest_detail(request, id):
    item = get_object_or_404(GWSRequest, pk=id)
    form = GWSRequestDetailForm(instance=item)
    c = {
        "item": item,
        "form": form,
    }
    return render("cedainfoapp/gwsrequest_detail.html", c)


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
        return redirect(request.META["HTTP_REFERER"])


# list of actual GWSs presented for external viewers
@login_required()
def gws_list(request):
    o = request.GET.get("o", "id")  # default order is ascending id

    filter = {}
    if request.method == "POST":  # if form was submitted
        form = GWSListFilterForm(
            request.POST,
            initial={"status": "active"},
        )
        filter["status"] = request.POST["status"]
        filter["path"] = request.POST["path"]
        items = GWS.objects.filter(
            status__exact=filter["status"], path__exact=filter["path"]
        ).order_by(o)

    else:  # provide a blank form
        form = GWSListFilterForm(
            initial={"status": "active"},
        )
        items = GWS.objects.order_by(o)

    total_volume = 0
    for i in items:
        total_volume += i.requested_volume

    c = {
        "form": form,
        "items": items,
        "total_volume": total_volume,
    }

    return render(request, "cedainfoapp/gws_list.html", c)


# GWS dashboard
# @login_required()
def gws_dashboard(request):
    items = GWS.objects.all()
    c = RequestContext(
        request,
        {
            "items": items,
        },
    )
    c.update(csrf(request))
    return render(request, "cedainfoapp/gws_dashboard.html", c)


# do du for a gws and redirect back to gws list
@login_required()
def gwsdu(request, id):
    gws = GWS.objects.get(pk=id)
    gws.du()
    return redirect(request.META["HTTP_REFERER"])


# do df for a gws and redirect back to gws list
@login_required()
def gwsdf(request, id):
    gws = GWS.objects.get(pk=id)
    gws.pan_df()
    return redirect(request.META["HTTP_REFERER"])


# GWS Manager list, for digestion by Elastic Tape system
# needs to be public to interact with scripts.
def gws_list_etexport(request):
    gwss = GWS.objects.filter(status="active")
    return render(
        request, 
        "cedainfoapp/gws_list_etexport.html", {"items": gwss}, content_type="text/plain"
    )


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
        expireDate = datetime.datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expireDate = datetime.datetime.strftime(expireDate, '%d-%b-%Y')
        issuer_full = certificate["issuer"][2][0][1]
        
        if issuer_full == 'R3':
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


# @login_required()
# def service_list_for_team_members (request):
#
#
#   username = request.GET.get('username', None)
#    person = Person.objects.get(username=username)
#
#    manager_services  = NewService.objects.filter(service_manager__username=username).order_by('name')
#    manager_services = manager_services.filter(status='production') | manager_services.filter(status='pre-production')
#
#    owner_services = NewService.objects.filter(owner__username=username).order_by('name')
#    owner_services = owner_services.filter(status='production') | owner_services.filter(status='pre-production')
#
#    return render('services/list_services_for_team_members.html', locals())
