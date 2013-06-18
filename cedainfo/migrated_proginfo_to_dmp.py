
#import sys
#sys.path.append('/home/spepler/play/cedainfo/cedainfo')

from django.core.management import setup_environ
import settings
setup_environ(settings)


from cedainfo.dmp.models import *

import cedainfo.proginfo.models as PI

progs = PI.Programme.objects.all()

print progs

for p in progs:
    
    # make a programme a dmp
    projectgroup=ProjectGroup(name=p.name, desc='')

    if p.title: projectgroup.desc += "%s\n\n" % p.title 
    if p.description: projectgroup.desc += "%s\n" % p.description 
    if p.scienceContact: projectgroup.desc += "Science contact: %s\n" % p.scienceContact 
    if p.fundingContact: projectgroup.desc += "Funding contact: %s\n" % p.fundingContact 
    if p.programmeSize: projectgroup.desc += "Programme size: %s\n" % p.programmeSize 
    if p.startDate: projectgroup.desc += "Start date: %s\n" % p.startDate 
    if p.endDate: projectgroup.desc += "End date: %s\n" % p.endDate 
    if p.state: projectgroup.desc += "Status: %s\n" % p.state 
    projectgroup.desc += '\n'

    notes = PI.ProgrammeNote.objects.filter(prog=p)
    for n in notes:
        projectgroup.desc += "[%s %s]: %s\n" % (n.who, n.added, n.text)
    projectgroup.save()

    # add projects...
    projects = PI.Project.objects.filter(prog=p)
    
    for proj in projects:
        newproject= Project(title=proj.title, 
                 desc=proj.desc, 
                 date_added = proj.added,
                 PI=proj.PI,
                 Contact1 = proj.CoI1,
                 Contact2 = proj.CoI2,
                 projectcost = proj.cost,
                 startdate =proj.startdate,
                 enddate=proj.enddate,
                 status=proj.status,
                 services = proj.services,
                 )


        if proj.grant: 
            g=Grant(number=proj.grant, project=newproject)
            g.save()

        notes = PI.ProjectNote.objects.filter(proj=proj)
        note = 'IMPORTED:\n\n'
        if proj.thirdpartydata: note += "Third party data: %s" % proj.thirdpartydata
        for n in notes:
            note += "[%s %s]: %s\n" % (n.who, n.added, n.text)
        newproject.notes= note
        newproject.save()

        # add dmp to dmp group
        projectgroup.projects.add(newproject)
             
        # add data products...
        dataprods = PI.DataProduct.objects.filter(proj=proj)
        for d in dataprods:
            dp = DataProduct(title=d.DPT,
                   datavol = d.datavol*1024*1024*1024*1024,        
                   contact1= d.contact1,
                   contact2= d.contact2,
                   deliverydate = d.deliverydate,
                   preservation_plan = d.preservation,
                   added = d.added,
                   status = d.status)
                 
            dp.desc=''
            if d.numobs: dp.desc += "Number of observations: %s\n" % d.numobs
            if d.numact: dp.desc += "Number of activities: %s\n" % d.numacts
            if d.formats: dp.desc += "Formats: %s\n" % d.formats
            if d.ipr: dp.desc += "IPR issues: %s\n" % d.ipr
            if d.versions: dp.desc += "versions: %s\n" % d.versions
            if d.numparameters: dp.desc += "Number of parameters: %s\n" % d.numparameters

            notes = PI.DataProductNote.objects.filter(data=d)
            note = 'IMPORTED:\n\n'
            for n in notes:
                note += "[%s %s]: %s\n" % (n.who, n.added, n.text)
            dp.notes= note
            dp.project = newproject
            dp.save()






