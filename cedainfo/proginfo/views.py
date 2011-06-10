# Create your views here.
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader
from cedainfo.proginfo.models import *
from django.shortcuts import render_to_response, get_object_or_404

import sys
sys.path.append('../utils')
# from gotw.client import GotwClient
import datetime

# The views are only the ones not included in the admin interface
# This means the view and edit functions are not here, but custom
# add and summary are. All notes are added this way. 


def index(request):
    # summary of all programmes
    prog_list = Programme.objects.all()
    prog_list = prog_list.order_by('name')
    nproj = []
    total_dps = {}
    total_pstate = {}

    for i in range(len(prog_list)):
        prog_list[i].nproj = prog_list[i].nprojects()

        # get status of data products
	dps = prog_list[i].dpstatus()
	# add to totals
	for k in dps.keys(): 
	   if total_dps.has_key(k): total_dps[k] = total_dps[k] +dps[k]
	   else: total_dps[k] = dps[k]
	# make charts
	labels=''
	values=''
	total = 0
	for k in dps.keys(): 
	    labels = '%s|%s:%s' % (labels,k, dps[k] )
	    values = '%s,%s' % (values, dps[k])
	    total = total + dps[k]
	if total != 0: 
	    values = values[1:]
	    labels = labels[1:]
            prog_list[i].dps = '<img src="http://chart.apis.google.com/chart?chs=250x100&cht=p&chd=t:%s&chl=%s&chco=FFFF00,00FFFF,FF00FF,FF0000,00FF00,0000FF">' % (values, labels)
        else: 
	    prog_list[i].dps = 'No data products'    
	    
	#  get status of projects    
	pstate = prog_list[i].pstatus()
	# add to totals
	for k in pstate.keys(): 
	   if total_pstate.has_key(k): total_pstate[k] = total_pstate[k] +pstate[k]
	   else: total_pstate[k] = pstate[k]
	# make charts
	labels=''
	values=''
	total = 0
	for k in pstate.keys(): 
	    labels = '%s|%s:%s' % (labels,k, pstate[k] )
	    values = '%s,%s' % (values, pstate[k])
	    total = total + pstate[k]
	if total != 0: 
	    values = values[1:]
	    labels = labels[1:]
            prog_list[i].pstate = '<img src="http://chart.apis.google.com/chart?chs=250x100&cht=p&chd=t:%s&chl=%s&chco=00FFFF,FF00FF,FF0000,00FF00,cccccc">' % (values, labels)
        else: 
	    prog_list[i].pstate = 'No Projects'    



    # make total data status chart
    labels=''
    values=''
    for k in total_dps.keys(): 
	labels = '%s|%s:%s' % (labels,k, total_dps[k] )
	values = '%s,%s' % (values, total_dps[k])
    values = values[1:]
    labels = labels[1:]
    datastatuschart = '<img src="http://chart.apis.google.com/chart?chs=500x200&cht=p&chd=t:%s&chl=%s&chco=FFFF00,00FFFF,FF00FF,FF0000,00FF00,0000FF">' % (values, labels)
	    
    # make totol status of projects chart    
    labels=''
    values=''
    for k in total_pstate.keys(): 
	labels = '%s|%s:%s' % (labels,k, total_pstate[k] )
	values = '%s,%s' % (values, total_pstate[k])
    values = values[1:]
    labels = labels[1:]
    projectstatuschart = '<img src="http://chart.apis.google.com/chart?chs=500x200&cht=p&chd=t:%s&chl=%s&chco=00FFFF,FF00FF,FF0000,00FF00,cccccc">' % (values, labels)



	    
    t = loader.get_template('prog_index.html')
    c = Context({
        'prog_list': prog_list,
        'datastatuschart': datastatuschart,
	'projectstatuschart': projectstatuschart,
    })
    return HttpResponse(t.render(c))

def newprojects(request):
    gotwClient = GotwClient(url='http://gotw.nerc.ac.uk/facadeservice/gotw.asmx')

    refNums = gotwClient.binding.GetGrantReferenceNumbers()
    refNums = refNums.String
    projects = []
    for n in refNums:     
        project = gotwClient.binding.GetDataByGrantReferenceNumber(n)
        projects.append(project)

        
 
    t = loader.get_template('newprojects.html')
    c = Context({
        'refnums': refNums,
        'projects': projects,
    })
    return HttpResponse(t.render(c))
    

def add_proj_gotw(request):
    # add a project from gotw info
    
    # get grant noumber from request
    grantno=request.GET['grantno']
    
    #set up Gotw client to grab grants info from NERC
    gotwClient = GotwClient(url='http://gotw.nerc.ac.uk/facadeservice/gotw.asmx')
    gotwinfo = gotwClient.binding.GetDataByGrantReferenceNumber(grantno)
    
    # pick out the bits of info needed
    sd = gotwinfo.StartDate
    ed = gotwinfo.EndDate
    PI = "%s, %s" % (gotwinfo.LeadInvestigator.Name,gotwinfo.LeadInvestigator.Institution)
    if len(gotwinfo.CoInvestigators.Investigator) >0:
        CoI1 = gotwinfo.CoInvestigators.Investigator[0]
        CoI1 = "%s, %s" % (CoI1.Name, CoI1.Institution)
    else: CoI1 = ''
    if len(gotwinfo.CoInvestigators.Investigator) >1:
        CoI2 = gotwinfo.CoInvestigators.Investigator[1]
        CoI2 = "%s, %s" % (CoI2.Name, CoI2.Institution)
    else: CoI2 = ''
    desc = "State: %s\nJeS State:%s\n\n%s" % (gotwinfo.State, gotwinfo.JesState, gotwinfo.Abstract)
    
    p = get_object_or_404(Programme, pk=25)
    newproj = Project(prog=p, grant=gotwinfo.ReferenceNumber ,
                              title=gotwinfo.Title,
			      desc=desc,
			      startdate=datetime.date(sd[0],sd[1],sd[2]),
			      enddate=datetime.date(ed[0],ed[1],ed[2]),
                              PI=PI, CoI1 = CoI1, CoI2 = CoI2,
			      cost = int(gotwinfo.Value * 0.001),
			      status = gotwinfo.State,
			       )
    newproj.save()
    return HttpResponseRedirect('/admin/proginfo/project/%s' % newproj.id)
    


def prog_DMP(request, prog_id):
    # a summary of a single programme
    p = get_object_or_404(Programme, pk=prog_id)
    n = ProgrammeNote.objects.filter(prog__id=prog_id)
    projs = Project.objects.filter(prog__id=prog_id)
    for proj in projs:
        proj.data_list = DataProduct.objects.filter(proj__id=proj.id)
    return render_to_response('prog_DMP.html', {'prog': p,
                                                   'notes': n,
                                                   'proj_list': projs})
def proj_DMP(request, proj_id):
    # a summary of a single project
    p = get_object_or_404(Project, pk=proj_id)
    n = ProjectNote.objects.filter(proj__id=proj_id)
    data_list = DataProduct.objects.filter(proj__id=proj_id)
    return render_to_response('proj_DMP.html', {'proj': p,
                                                   'notes': n,
                                                   'data_list': data_list})
def proj_summary(request, proj_id):
    # a summary of a single project
    p = get_object_or_404(Project, pk=proj_id)
    n = ProjectNote.objects.filter(proj__id=proj_id)
    data_list = DataProduct.objects.filter(proj__id=proj_id)
    return render_to_response('proj_summary.html', {'proj': p,
                                                   'notes': n,
                                                   'data_list': data_list})

def prog_cost(request, prog_id):
    # a costing of a single programme
    p = get_object_or_404(Programme, pk=prog_id)
    n = ProgrammeNote.objects.filter(prog__id=prog_id)
    projs = Project.objects.filter(prog__id=prog_id)
    costs = p.data_man_costs()
    for proj in projs:
        proj.data_list = DataProduct.objects.filter(proj__id=proj.id)
    return render_to_response('prog_costs.html', {'prog': p,
                                                   'notes': n,
						   'scoping': costs['scoping'],
						   'tracking': costs['tracking'],
						   'storage': costs['storage'],
						   'ingest': costs['ingest'],
						   'metadata': costs['metadata'],
						   'costs': costs,
                                                   'proj_list': projs})
						   
def prog_help(request, prog_id):
    # help for programmes
    p = get_object_or_404(Programme, pk=prog_id)
    return render_to_response('prog_help.html', {'prog': p})
						   
						   

def proj_help(request, proj_id):
    # help for project screen
    p = get_object_or_404(Project, pk=proj_id)
    return render_to_response('proj_help.html', {'proj': p})

def data_help(request, data_id):
    # help for data product screen
    d = get_object_or_404(DataProduct, pk=data_id)
    return render_to_response('data_help.html', {'data': d})




def add_proj(request, prog_id):
    # add a project to a given programme
    p = get_object_or_404(Programme, pk=prog_id)
    newproj = Project(prog=p, title="NEW PROJ")
    newproj.save()
    return HttpResponseRedirect('/admin/proginfo/project/%s' % newproj.id)


def add_data(request, proj_id):
    # add a data product to a given project
    p = get_object_or_404(Project, pk=proj_id)
    newdata = DataProduct(proj=p, DPT="NEW DPT", deliverydate=p.enddate,
                        contact1=p.PI, numobs=1, numact=0, datavol=0, 
			status="In Progress", preservation="Keep indefinately")
    newdata.save()
    return HttpResponseRedirect('/admin/proginfo/dataproduct/%s' % newdata.id)


def add_prog_note(request, prog_id):
    # add a note to a programme 
    p = get_object_or_404(Programme, pk=prog_id)
    newnote = ProgrammeNote(prog=p, text=request.POST['notetext'], who=request.user.username)
    newnote.save()
    return HttpResponseRedirect('/admin/proginfo/programme/%s' % p.id)

def add_proj_note(request, proj_id):
    # add a note to a project
    p = get_object_or_404(Project, pk=proj_id)
    newnote = ProjectNote(proj=p, text=request.POST['notetext'], who=request.user.username)
    newnote.save()
    return HttpResponseRedirect('/admin/proginfo/project/%s' % p.id)

def add_data_note(request, data_id):
    # add a note to a data product
    p = get_object_or_404(DataProduct, pk=data_id)
    newnote = DataProductNote(data=p, text=request.POST['notetext'], who=request.user.username)
    newnote.save()
    return HttpResponseRedirect('/admin/proginfo/dataproduct/%s' % p.id)


