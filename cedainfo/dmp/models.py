from django.db import models

# Create your models here.

from django.db import models

import datetime

import re

# import users 
from django.contrib.auth.models import *
from sizefield.models import FileSizeField
#-----

class DMP(models.Model):

    # Projects are activities under funding programmes that are examined
    # for their data management needs.

    title = models.CharField(max_length=200)
    dateAdded = models.DateTimeField(auto_now_add=True)
    desc = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    sciSupContact = models.ForeignKey(User, help_text="CEDA person contact for this DMP", blank=True, null=True)
    PI = models.CharField(max_length=200, blank=True, null=True)
    Contact1 = models.CharField(max_length=200, blank=True, null=True)
    Contact2 = models.CharField(max_length=200, blank=True, null=True)
    projectcost = models.IntegerField(blank=True, null=True)
    #thirdpartydata = models.TextField(blank=True, null=True)
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
    data_outputs = models.ManyToManyField('DataProduct', related_name='outputs+', blank=True, null=True)
    third_party_data = models.ManyToManyField('DataProduct', related_name='requirements+', 
                        blank=True, null=True)
    project_URL = models.URLField(blank=True, null=True)
	
    def __unicode__(self):
        return "%s" % self.title

    def ndata(self):
        return len(self.data_outputs.all())


    def dmp_groups(self):
        output = ''
        for dmpg in self.dmpgroup_set.all():
            output += '<a href="/admin/dmp/dmpgroup/%s">%s</a> ' % (dmpg.id, dmpg.name)
        return output
    dmp_groups.allow_tags = True    

    def grants(self):
        return Grant.objects.filter(dmp=self)

    def grant_links(self):
        output = ''
        for g in self.grants:
            output += '<a href="/admin/dmp/grant/%s">%s</a> ' % (g.id, g.number)
        return output
    dmp_groups.allow_tags = True    



#-----

class DataProduct(models.Model):

    # Data products are data streams produced by projects

    title = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    datavol = FileSizeField(default=0)
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
    status = models.CharField(max_length=200, blank=True, null=True,
            choices=( ("WithProjectTeam","With Project Team"),
                 ("Ingesting","Ingesting"),
                 ("Archived","Archived and complete"),
                 ("Defaulted","Defaulted - not archived due to project not supplying data"),
                 ("NotArchived","Not going to archive - planned")))
    data_URL = models.URLField(blank=True, null=True)
    
    def __unicode__(self):
        return "%s" % self.title

#    def dmps_where_output(self): 
#        return DMP.objects.filter('data_outputs__contains'==self)

    def dmps_where_output(self): 
        return DMP.objects.filter(data_outputs=self)
    def dmps_where_thirdparty(self): 
        return DMP.objects.filter(third_party_data=self)

class Grant(models.Model):
    dmp = models.ForeignKey('DMP', blank=True, null=True)
    number = models.CharField(max_length=200)
    title = models.CharField(max_length=800, blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        if not self.title: return "%s" % self.number
        elif len(self.title) > 100: return "%s: %s..." % (self.number, self.title[0:100])
        else: return "%s: %s" % (self.number, self.title)

    def gotw(self):
        if self.number: 
            return '<a href="http://gotw.nerc.ac.uk/list_full.asp?pcode=%s">%s</a>' %(self.number, self.number)
        else:
            return '-'
    gotw.allow_tags = True    


class DMPGroup(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    dmps = models.ManyToManyField('DMP', blank=True, null=True)

    def __unicode__(self):
        return "%s" % self.name



