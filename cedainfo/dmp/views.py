from cedainfo.dmp.models import *
from django.shortcuts import redirect, render_to_response, get_object_or_404

from django.contrib.auth.models import *
import settings

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

def link_grant_to_project(request, id):
    # list projects for logged in user
    if request.user.is_authenticated(): user=request.user
    else: user = None

    grant = get_object_or_404(Grant, pk=id)

    searchstring = request.GET.get('search', '') 
    project_id = request.GET.get('project', None) 

    # if projectid set then set and redirest back to grant page
    if project_id: 
        project = get_object_or_404(Project, pk=project_id)
        grant.project = project
        grant.save()
        return redirect('/admin/dmp/grant?o=3' )
 
    projectscores = {}
    searchstrings = searchstring.split()
    
    stopwords = "a,an,and,are,as,at,by,for,from,had,has,have,how,if,in,into,is,it,"
    stopwords += "its,no,not,of,off,on,or,so,some,than,that,the,then,there,these,they,"
    stopwords += "this,to,too,us,wants,was,were,what,when,where,which,while,who,why,"
    stopwords += "will,with,would,dr,prof,doctor,professor"
    stopwords = stopwords.split(',')
    
    for s in searchstrings:
        if s.lower() in stopwords: continue
           
        projects_bytitle = Project.objects.filter(title__icontains=s)
        projects_bypi = Project.objects.filter(PI__icontains=s)

        for p in projects_bytitle: 
            if projectscores.has_key(p): projectscores[p] += 1
            else: projectscores[p] = 1 
        for p in projects_bypi: 
            if projectscores.has_key(p): projectscores[p] += 1
            else: projectscores[p] = 1 

    topprojectscores = sorted(projectscores, key=projectscores.get) 
    topprojectscores = topprojectscores[-8:]
    topprojectscores.reverse()
    for i in range(len(topprojectscores)):
        project = topprojectscores[i]
        score = projectscores[project]
        topprojectscores[i] = (project, score)
    context = {'projectscores':topprojectscores, 'grant':grant, 'user':user, 
               'search':searchstring}
    
    return render_to_response('link_grant_to_project.html', context)



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

def projects_vis(request):

    # list projects for logged in user
    if request.user.is_authenticated(): user=request.user
    else: user = None

    # if set override login user
    order = request.GET.get('order', None) 
    show = request.GET.get('show', None) 
    scisupcontact = request.GET.get('scisupcontact', None) 
    if scisupcontact == 'None': scisupcontact=None
    if scisupcontact: user= User.objects.filter(username=scisupcontact)[0]

    projects = Project.objects.filter(sciSupContact=user)
    
    # if set override login user
    listall = request.GET.get('listall', None)
    if not listall:  
        projects = projects.exclude(status='Proposal').exclude(status='NotFunded')
        projects = projects.exclude(status='NoData').exclude(status='Defaulted').exclude(status='Complete')

    if not order: projects = projects.order_by('modified')
    else: projects = projects.order_by(order)

    return render_to_response('projects_vis.html', {'projects': projects, 'user':user, 
                              'listall':listall, 'show':show,
                              'modchecktime':datetime.datetime.now()-datetime.timedelta( days=90)})

def showproject(request, project_id):
    # a summary of a single project
    project = get_object_or_404(Project, pk=project_id)
    return render_to_response('showproject.html', {'project': project,})


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
#        os.unlink(tmpfile)

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



def make_project_from_rss_export(request, id):
    grant = get_object_or_404(Grant, pk=id)
    
    exports_file = settings.DATAMAD_RSS_FILE
    
    import os, sys, subprocess, re, time, string, datetime
    months = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
              'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
                        
    if not grant.number: redirect('/admin/dmp/grant/%s' % id)

    import xml.etree.ElementTree as ET
    import re

    tree = ET.parse(exports_file)
    root = tree.getroot()
    channel = root.findall('channel')[0]

    def find_field(desc, text):
        m = re.search('<div><b>%s:</b>(.*?)</div>' % text ,desc)
        if m: return m.group(1).strip()
        else: return ''
    
    def find_long_field(desc, text):
        m = re.search('<div><b>%s:</b> <div class=".*?">(.*?)</div>' % text ,desc, re.S)
        if m: return m.group(1).strip()
        else: return ''

    for item in channel.findall('item'):
        desc = item.find('description').text
        title = item.find('title').text
        grant_ref =  find_field(desc, 'Grant Reference')
        if grant_ref == grant.number: break
    else:
        redirect('/admin/dmp/grant/%s' % id)
        
        
    PI =  find_field(desc, 'Grant Holder')
    email =  find_field(desc, 'E-Mail')
    abstract =  find_long_field(desc, 'Abstract')
    objectives =  find_long_field(desc, 'Objectives')
    project_description="Abstract: %s\n\nObjectives: %s" % (abstract, objectives)
    startdate =  find_field(desc, 'Actual Start Date')
    enddate =  find_field(desc, 'Actual End Date')
    startdate = datetime.datetime.strptime(startdate, "%d/%m/%Y")
    enddate = datetime.datetime.strptime(enddate, "%d/%m/%Y")
    programme =  find_field(desc, 'Call')

    notes = "Added via DataMAD RSS export %s.\n" % time.strftime("%Y-%m-%d %H:%M")
    scisupcontact=request.user

    # make new project
    projs = Project.objects.filter(title=title)
    if len(projs) == 0:
        p  = Project(startdate=startdate, enddate=enddate, PI="%s (%s)"%(PI,email), 
                     notes=notes, 
                     title=title, desc=project_description, 
                     status="Active", sciSupContact=scisupcontact)
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

        # redirect back to grants list
        return redirect('/admin/dmp/grant?o=3' )
    else:
        return render_to_response('dup_title.html', {'projs': projs, 'grant':grant})
 
    
    return redirect('/admin/dmp/grant/%s' % id)



def vmreg(request):
    # make page to register for vm and gws
    projs = Project.objects.exclude(vms__isnull=True)
    return render_to_response('vmreg.html', {'projects': projs})

    
