from cedainfo.dmp.models import *
from django.shortcuts import redirect, render_to_response, get_object_or_404

from django.contrib.auth.models import *

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
    if scisupcontact: user= User.objects.filter(username=scisupcontact)[0]

    projects = Project.objects.filter(sciSupContact=user)

    return render_to_response('my_projects.html', {'projects': projects, 'user':user})

