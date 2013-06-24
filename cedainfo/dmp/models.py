from django.db import models

# Create your models here.

from django.db import models

import datetime

import re

# import users 
from django.contrib.auth.models import *
from cedainfoapp.models import *
from sizefield.models import FileSizeField

#-----

class Project(models.Model):

    # Projects are activities under funding programmes that are examined
    # for their data management needs.

    title = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)
    desc = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    data_activities = models.TextField(blank=True, null=True, help_text="Short description of data generation activities. eg Data will be collected by FAAM aircraft/ground instruments. Are there intensive measurement campaigns?")
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    sciSupContact = models.ForeignKey(User, help_text="CEDA person contact for this Project", blank=True, null=True)
    PI = models.CharField(max_length=200, blank=True, null=True)
    Contact1 = models.CharField(max_length=200, blank=True, null=True)
    Contact2 = models.CharField(max_length=200, blank=True, null=True)
    projectcost = models.IntegerField(blank=True, null=True)
    services = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=200, blank=True, null=True,
            choices=(("Proposal","Proposal"),
                 ("NotFunded","Not Funded"),
                 ("NotStarted","NotStarted"),
                 ("Active","Active"),
                 ("NoData","NoData"),
                 ("EndedWithDataToCome","Ended with data to come"),
                 ("Defaulted","Defaulted"),
                 ("Complete","Complete")))
    modified = models.DateTimeField(auto_now=True)
    third_party_data = models.ManyToManyField('DataProduct', related_name='requirements+', 
                        blank=True, null=True)
    vms = models.ManyToManyField(VM, blank=True, null=True)
    groupworkspaces = models.ManyToManyField(GWS, blank=True, null=True)
    project_URL = models.URLField(blank=True, null=True)
    project_usergroup = models.CharField(max_length=200, blank=True, null=True, help_text="Group name for registration for this group")
	
    def __unicode__(self):
        return "%s" % self.title

    def ndata(self):
        dps = DataProduct.objects.filter(project=self)
        return len(dps)

    def data_outputs(self):
        dps = DataProduct.objects.filter(project=self)
        return dps

    def project_groups_links(self):
        output = ''
        for g in self.projectgroup_set.all():
            output += '<a href="/admin/dmp/projectgroup/%s">%s</a> ' % (g.id, g.name)
        return output
    project_groups_links.allow_tags = True    

    def project_groups(self):
        return ProjectGroup.objects.filter(projects=self)   

    def grants(self):
        return Grant.objects.filter(project=self)

    def grant_links(self):
        output = ''
        for g in self.grants():
            output += '<a href="/admin/dmp/grant/%s">%s</a> ' % (g.id, g.number)
        return output
    grant_links.allow_tags = True    

    def is_jasmin(self):
        #look for jasmin in vm mountpoints 
        for vm in self.vms.all():
            for mount in vm.mountpoints_required:
                if mount.find("jasmin") != -1: return True
        #look for jasmin in groupworkspaces
        for gws in self.groupworkspaces.all():
            if gws.path.find("jasmin") != -1: return True
        return False

    def is_cems(self):
        #look for cems in vm mountpoints 
        for vm in self.vms.all():
            for mount in vm.mountpoints_required:
                if mount.find("cems") != -1: return True
        #look for cems in groupworkspaces
        for gws in self.groupworkspaces.all():
            if gws.path.find("cems") != -1: return True
        return False



#-----

class DataProduct(models.Model):

    # Data products are data streams produced by projects

    title = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    datavol = FileSizeField(default=0)
    project = models.ForeignKey(Project, help_text="Project producing this data", blank=True, null=True)
    sciSupContact = models.ForeignKey(User, help_text="CEDA person contact for this data", blank=True, null=True)
    contact1 = models.CharField(max_length=200, blank=True, null=True)
    contact2 = models.CharField(max_length=200, blank=True, null=True)
    deliverydate = models.DateField(blank=True, null=True)
    preservation_plan = models.CharField(max_length=200, blank=True, 
              null=True, choices=( ("KeepIndefinitely","Keep Indefinitely"),
                 ("KeepAsIs","Keep as is - Even if obsolete"),
                 ("Dispose5years ","Review for disposal 5 years after project completes"),
                 ("ManageInProject","Don't Archive - manage the data within the project"),
                 ("Subset","Plan to keep a subset of the data indefinitely"),
                 ("TBD","TBD")))
    added = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    review_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=200, blank=True, null=True,
            choices=( ("WithProjectTeam","With Project Team"),
                 ("Ingesting","Ingesting"),
                 ("Archived","Archived and complete"),
                 ("Defaulted","Defaulted - not archived due to project not supplying data"),
                 ("NotArchived","Not going to archive - planned")))
    data_URL = models.URLField(blank=True, null=True)
    
    def __unicode__(self):
        return "%s" % self.title

    def projects_where_thirdparty(self): 
        return Projects.objects.filter(third_party_data=self)

class Grant(models.Model):
    project = models.ForeignKey('Project', blank=True, null=True)
    number = models.CharField(max_length=200)
    title = models.CharField(max_length=800, blank=True, null=True)
    pi = models.CharField(max_length=200, blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        if not self.title: return "%s" % self.number
        elif len(self.title) > 100: return "%s: %s..." % (self.number, self.title[0:100])
        else: return "%s: %s" % (self.number, self.title)

    def gotw(self):
        if self.number: 
            return '<a style="color:red; background-color:lightblue; border:2px blue dashed" href="http://gotw.nerc.ac.uk/list_full.asp?pcode=%s">%s</a>' %(self.number, self.number)
        else:
            return '-'
    gotw.allow_tags = True    



class ProjectGroup(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    projects = models.ManyToManyField('Project', blank=True, null=True)

    def __unicode__(self):
        return "%s" % self.name



