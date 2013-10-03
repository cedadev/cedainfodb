from cedainfo.dmp.models import *
from django.shortcuts import redirect, render_to_response, get_object_or_404

from django.contrib.auth.models import *

import datetime

def dmp_draft(request, project_id):
    # a summary of a single project
    project = get_object_or_404(Project, pk=project_id)
    return render_to_response('dmp_draft.html', {'project': project,})

def add_dataproduct(request, project_id):
    # add a data product to a project
    if request.user.is_authenticated(): user=request.user
    else: user = None

    project = get_object_or_404(Project, pk=project_id)
    dp = DataProduct(title="NEW DATA PRODUCT",
                   datavol = 1000*1000*1000,        
                   contact1= project.PI,
                   preservation_plan = "KeepIndefinitely",
                   sciSupContact = user,
                   project = project,
                   status = "WithProjectTeam")
    dp.save()
   
    return redirect('/admin/dmp/dataproduct/%s' % dp.pk)


def my_projects(request):
    # list projects for logged in user
    if request.user.is_authenticated(): user=request.user
    else: user = None

    # if set override login user
    scisupcontact = request.GET.get('scisupcontact', None) 
    if scisupcontact == 'None': scisupcontact=None
    if scisupcontact: user= User.objects.filter(username=scisupcontact)[0]

    projects = Project.objects.filter(sciSupContact=user)
    
    # if set override login user
    listall = request.GET.get('listall', None)
    if not listall:  
        projects = projects.exclude(status='Proposal').exclude(status='NotFunded')
        projects = projects.exclude(status='NoData').exclude(status='Defaulted').exclude(status='Complete')

    projects = projects.order_by('modified')

    return render_to_response('my_projects.html', {'projects': projects, 'user':user, 'listall':listall, 'modchecktime':datetime.datetime.now()-datetime.timedelta( days=90)})

def projects_by_person(request):

    projects = Project.objects.all()
    projects = projects.exclude(status='Proposal').exclude(status='NotFunded')
    projects = projects.exclude(status='NoData').exclude(status='Defaulted').exclude(status='Complete')

    summary = {}
    for p in projects:
        if p.sciSupContact: username = p.sciSupContact.username
        else: username = None

        if not summary.has_key(username): 
            summary[username] = [1,[]]
            for pg in p.project_groups():
                if pg not in summary[username][1]: summary[username][1].append(pg)
        else: 
            summary[username] = [summary[username][0]+1, summary[username][1]]
            for pg in p.project_groups(): 
                if pg not in summary[username][1]: summary[username][1].append(pg)

    return render_to_response('projects_by_person.html', {'summary': summary})


def gotw_scrape(request, id):
    grant = get_object_or_404(Grant, pk=id)

    import os, sys, subprocess, re, time, string
    if not grant.number: redirect('/admin/dmp/grant/%s' % id)
    tmpfile = "/tmp/grantscrape.html" 
    url='http://gotw.nerc.ac.uk/list_full.asp?pcode=%s&cookieConsent=A' %grant.number
    try:
        subprocess.check_call('wget -O %s %s' % (tmpfile, url), shell=True)
        time.sleep(4)
        G = open(tmpfile)
        content = G.read()
        os.unlink(tmpfile)

        m = re.search('<p class="awardtitle"><b>(.*?)</b></p>', content)
        grant.title=str(m.group(1))
        m = re.search('<p class="small"><b>Abstract:</b> (.*?)</p>', content)
        desc=m.group(1)
        filtered_desc = ''.join(filter(lambda x: x in string.printable, desc))
        grant.desc=filtered_desc
        m = re.search('<b>Principal Investigator</b>: <a href="list_med_pi.asp\?pi=.*?">(.*?)</a>', content)
        grant.pi=str(m.group(1))
        grant.save()
    except:
        pass
    
    return redirect('/admin/dmp/grant/%s' % id)





def make_project_from_scrape(request, id):
    grant = get_object_or_404(Grant, pk=id)
 
    import os, sys, subprocess, re, time, string, datetime
    months = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
              'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    if not grant.number: redirect('/admin/dmp/grant/%s' % id)
    tmpfile = "/tmp/grantscrape.html" 
    url='http://gotw.nerc.ac.uk/list_full.asp?pcode=%s&cookieConsent=A' %grant.number
    #try:
    if 1:
        subprocess.check_call('wget -O %s %s' % (tmpfile, url), shell=True)
        time.sleep(4)
        G = open(tmpfile)
        content = G.read()
        os.unlink(tmpfile)

        p = Project()
        m = re.search('<p class="awardtitle"><b>(.*?)</b></p>', content)
        title=str(m.group(1))
        m = re.search('<p class="small"><b>Abstract:</b> (.*?)</p>', content)
        desc=m.group(1)
        desc = ''.join(filter(lambda x: x in string.printable, desc))
        m = re.search('<b>Principal Investigator</b>: <a href="list_med_pi.asp\?pi=.*?">(.*?)</a>', content)
        pi=str(m.group(1))
        notes = "Added via grants on the web scrap %s.\n" % time.strftime("%Y-%m-%d %H:%M")
        m = re.search('<b>Period of Award</b>:\s*<span class="detailsText">(\d+) (.*?) (\d+) - (\d+) (.*?) (\d+)</span>', content)
        startdate = datetime.date(int(m.group(3)),months[m.group(2)],int(m.group(1)))
        enddate = datetime.date(int(m.group(6)),months[m.group(5)],int(m.group(4)))
   
        scisupcontact=request.user
        m = re.search('<b>Programme</b>: <span class="detailsText"> <a href="list_them.asp\?them=.*?">(.*?)</a></span>', content)
        programme = m.group(1)
        print programme

        # make new project
        projs = Project.objects.filter(title=title)
        if len(projs) == 0:
            p  = Project(startdate=startdate, enddate=enddate, PI=pi, notes=notes, title=title, desc=desc, status="Active", sciSupContact=scisupcontact)
            p.save()

            # link grant to new project
            grant.project=p
            grant.save()

            # make new programme if on found
            progs = ProjectGroup.objects.filter(name=programme)
            if len(progs) == 0:
                pg = ProjectGroup(name=programme)
                pg.save()
                pg.projects.add(p)
            else:
                progs[0].projects.add(p)

            # redirect back to project page
            return redirect('/admin/dmp/project/%s' % p.pk)
        else:
            return render_to_response('dup_title.html', {'projs': projs, 'grant':grant})
 
    #except:
    #    pass
    
    return redirect('/admin/dmp/grant/%s' % id)



def vmreg(request):
    # make page to register for vm and gws
    projs = Project.objects.exclude(vms__isnull=True)
    return render_to_response('vmreg.html', {'projects': projs})

    
