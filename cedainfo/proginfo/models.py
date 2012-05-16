from django.db import models

import datetime

import re

# Create your models here.


class Programme(models.Model):

    # This is funding pool the project which need data management are
    # in. 

    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True, null=True)
    dateAdded = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    sciSupContact = models.CharField(max_length=200, blank=True, null=True)
    fundingContact = models.CharField(max_length=200, blank=True, null=True)
    scienceContact = models.CharField(max_length=200, blank=True, null=True)
    programmeSize = models.IntegerField(blank=True, null=True)
    projectcode = models.CharField(max_length=200, blank=True, null=True)
    scopingFunds = models.IntegerField(blank=True, null=True)
    startDate = models.DateField(blank=True, null=True)
    endDate = models.DateField(blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True,
        choices=(("New","New"),
                 ("Active","Active"),
                 ("C","Complete")))
    dataCentre = models.CharField(max_length=20, blank=True, null=True,
        choices=(("BADC","BADC"),
                 ("NEODC","NEODC")) )
    progtype = models.CharField(max_length=200, blank=True, null=True)
    unresponsive = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s" % self.name

    def nprojects(self):
        return len(Project.objects.filter(prog__id=self.id))

    def dpstatus(self):
        # summary status of all data products in programme 
        dps = { "Unknown": 0,
	        "In Progress": 0,
		"Overdue": 0,
                "Archived": 0,
                "Not Archived": 0}
        for p in Project.objects.filter(prog__id=self.id):
            for dp in DataProduct.objects.filter(proj__id=p.id):
	        deldate = dp.deliverydate
		status = dp.status
		if status == None: status ="Unknown"
		if deldate == None: deldate = datetime.date(1980,1,1)
		if deldate < datetime.date.today() and status == "In Progress": 
		    status = "Overdue"
	        if dps.has_key(status): 
		    dps[status] += 1
		else:
		    dps[status] = 1
        return dps

    def pstatus(self):
        # summary status of all projects in programme
        pstate = { "Not scoped": 0,
                   "Scoping": 0,
                   "Active": 0,
		   "Overdue": 0,
                   "Complete": 0}
        for p in Project.objects.filter(prog__id=self.id):
	    startdate = p.startdate
	    enddate   = p.enddate
	    status    = p.status
            if status == None: status ="Not scoped"
	    if startdate == None: startdate = datetime.date(1980,1,1)
	    if enddate == None: enddate = datetime.date(1980,1,1)
	    if enddate < datetime.date.today() and status == "Active": status = "Overdue"
	    if pstate.has_key(status): 
		pstate[status] += 1
            else:
		pstate[status] = 1
        return pstate

    def data_man_costs(self): 
        (ndpt, nobs, nact, vol) = self.cost_params()
	costs = {'scoping': self.programmeSize * 0.001,
	         'tracking': self.programmeSize * 0.004,
		 'ingest': ndpt * 3.0,
		 'storage': vol * 1.0,
		 'metadata': (ndpt+nobs+nact) *1.0}
        return costs		 
    

    def cost_params(self):
	ndpt, nobs, nact, vol = (0, 0, 1, 0)     
        for p in Project.objects.filter(prog__id=self.id):
	    p_ndpt, p_nobs, p_nact, p_vol = p.cost_params()
	    ndpt = ndpt + p_ndpt   # sum number of DPTs
	    nobs = nobs + p_nobs   # sum number of obs stations
	    nact = nact + p_nact   # sum number of activities
	    vol  = vol  + p_vol    # sum TB of data
	return (ndpt, nobs, nact, vol) 

class Note:

    # This is a super class for a simple dated note. Programmes, Projects
    # and DataProducts have note attached to them. This is only a seperate class
    # because django can't handle inherited foreign keys.

    def __unicode__(self):
        x= re.sub(r"(http://.*?)[$|\s]", r'<a href="\1">\1</a>', self.text)
        x= re.sub(r"#(\d+)", r'<a href="http://proj.badc.rl.ac.uk/badc/ticket/\1">#\1</a>', x)
        x= re.sub(r"Q(\d+)", r'<a href="http://mistral.badc.rl.ac.uk/MRcgi/MRlogin.pl?DL=\1DA12">Q\1</a>', x)
        return x

    def html(self):
        return "HTML version of note:" % self.text

class ProgrammeNote(models.Model, Note):
    # A note on a programme
    text = models.TextField()
    added = models.DateTimeField(auto_now_add=True)
    prog = models.ForeignKey(Programme)
    who = models.CharField(max_length=100, blank=True, null=True)

#-----

class Project(models.Model):

    # Projects are activities under funding programmes that are examined
    # for their data management needs.

    grant = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    PI = models.CharField(max_length=200, blank=True, null=True)
    CoI1 = models.CharField(max_length=200, blank=True, null=True)
    CoI2 = models.CharField(max_length=200, blank=True, null=True)
    cost = models.IntegerField(blank=True, null=True)
    thirdpartydata = models.TextField(blank=True, null=True)
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
    added = models.DateTimeField(auto_now_add=True)
    prog = models.ForeignKey(Programme)
    unresponsive = models.BooleanField(default=False)
	
    def __unicode__(self):
        return "%s" % self.title

    def ndata(self):
        return len(DataProduct.objects.filter(proj__id=self.id))

    def cost_params(self):
	ndtp, nobs, nact, vol = (0, 0, 1, 0)     
        for dp in DataProduct.objects.filter(proj__id=self.id):
	    ndpt = ndtp + 1
	    dp_nobs, dp_nact, dp_vol = dp.cost_params()
	    nobs = nobs + dp_nobs   # sum number of obs stations
	    nact = nact + dp_nact   # sum number of activities
	    vol  = vol  + dp_vol    # sum TB of data
	return (ndtp, nobs, nact, vol) 
    
    def dpstatus(self):
        # summary status of all data products in programme 
        dps = { "Unknown": 0,
	        "In Progress": 0,
		"Overdue": 0,
                "Archived": 0,
                "Not Archived": 0}
        for dp in DataProduct.objects.filter(proj__id=self.id):
	    deldate = dp.deliverydate
            status = dp.status
	    if status == None: status ="Unknown"
            if deldate == None: deldate = datetime.date(1980,1,1)
            if deldate < datetime.date.today() and status == "In Progress": 
		status = "Overdue"
	    if dps.has_key(status): 
		dps[status] += 1
            else:
		dps[status] = 1
        return dps


class ProjectNote(models.Model, Note):
    # note on a Project
    text = models.TextField()
    added = models.DateTimeField(auto_now_add=True)
    proj = models.ForeignKey(Project)
    who = models.CharField(max_length=100, blank=True, null=True)


#-----

class DataProduct(models.Model):

    # Data products are data streams produced by projects

    DPT = models.CharField(max_length=200)
    numobs = models.IntegerField(blank=True, null=True)
    numact = models.IntegerField(blank=True, null=True)
    datavol = models.IntegerField(blank=True, null=True)
    contact1 = models.CharField(max_length=200, blank=True, null=True)
    contact2 = models.CharField(max_length=200, blank=True, null=True)
    deliverydate = models.DateField(blank=True, null=True)
    formats = models.CharField(max_length=200, blank=True, null=True)
    ipr = models.CharField(max_length=200, blank=True, null=True)
    versions = models.CharField(max_length=200, blank=True, null=True)
    numparameters = models.IntegerField(blank=True, null=True)
    preservation = models.CharField(max_length=200, blank=True, null=True)
    unresponsive = models.BooleanField(default=False)
    proj = models.ForeignKey(Project)
    added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=200, blank=True, null=True,
            choices=( ("In Progress","In Progress"),
                 ("Archived","Archived"),
                 ("Not Archived","Not going to archive")))
    
    def __unicode__(self):
        return "%s" % self.DPT

    def cost_params(self):
        numobs, numact, datavol = 0, 0, 0
	if self.numobs != None: numobs = self.numobs
	if self.numact != None: numact = self.numact
	if self.datavol != None: datavol = self.datavol 
        return (numobs, numact, datavol)
        


class DataProductNote(models.Model, Note):
    # notes on data products
    text = models.TextField()
    added = models.DateTimeField(auto_now_add=True)
    data = models.ForeignKey(DataProduct)
    who = models.CharField(max_length=100, blank=True, null=True)

