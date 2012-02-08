from django.db import models
import md5
import choices

from django.db.models.base import ModelBase



class Dataset(models.Model):
    datasetid = models.CharField(max_length=40, primary_key=True)

    authtype = models.CharField(max_length=20,
       choices=choices.DATASET_REGISTRATION_TYPES
       )
    
    grp = models.CharField(max_length=40, verbose_name='Group')
    grouptype = models.CharField(max_length=20)
    description = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50)
    ukmoform = models.IntegerField()
#    ordr = models.IntegerField()
    comments = models.CharField(max_length=200, blank=True)
    directory = models.CharField(max_length=100, blank=True)
#    metdata = models.IntegerField()
    conditions = models.CharField(max_length=100, blank=True)
    defaultreglength = models.IntegerField()
    datacentre = models.CharField(max_length=20, choices=choices.DATACENTRES)
    infourl = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.datasetid
 
    def get_absolute_url(self):
       return "/%s/dataset/details/%s" % (self._meta.app_label, self.datasetid)
       
    class Meta:
        db_table = u'tbdatasets'
        managed  = False
 


class Institute(models.Model):
    institutekey = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=80)
    country = models.CharField(max_length=30)
    type = models.CharField(max_length=30)
    link = models.CharField(max_length=100)
    class Meta:
        db_table = u'tbinstitutes'
	managed  = False

class Addresses(models.Model):
    addresskey = models.IntegerField(primary_key=True)
    institutekey = models.ForeignKey(Institute, db_column='institutekey')
    department = models.CharField(max_length=100)
    address1 = models.CharField(max_length=150)
    address2 = models.CharField(max_length=100)
    address3 = models.CharField(max_length=100)
    address4 = models.CharField(max_length=100)
    address5 = models.CharField(max_length=100)
    nerc = models.IntegerField()

    def __unicode__ (self):
       return "%s" % self.address1
       
    class Meta:
        db_table = u'addresses'
	managed  = False


class User (models.Model):
    userkey = models.AutoField(primary_key=True)

    title = models.CharField(max_length=10,       
          choices=(
              ("Mr","Mr"),
              ("Mrs","Mrs"),
              ("Dr","Dr"),
              ("Miss","Miss"),
              ("Ms","Ms"),
              ("Prof","Prof")
          )
	) 

    surname = models.CharField(max_length=50)
    othernames = models.CharField(max_length=50, verbose_name='First name(s)')
    addresskey = models.OneToOneField(Addresses, db_column='addresskey')
    telephoneno = models.CharField(max_length=50, blank=True)
    faxno = models.CharField(max_length=50, blank=True)
    emailaddress = models.CharField(max_length=50)
    comments = models.TextField()
    endorsedby = models.CharField(max_length=50, blank=True)
    degree = models.CharField(max_length=20)
    
    degree = models.CharField(max_length=20, blank=True, null=True, verbose_name='Studying for',
        choices=(
            ("BS","BS"),
            ("BSc","BSc"),
            ("MA","MA"),
            ("MPhil","MPhil"),
            ("MSc","MSc"),
            ("MSci","MSci"),
            ("PhD","PhD"),
            ("RMS","RMS"),
            ("Other","Other")
        )
    ) 
        
    field = models.CharField(max_length=50, blank=True, null=True,  
        choices=(
	    ("Atmospheric Physics","Atmospheric Physics"),
	    ("Atmospheric Chemistry","Atmospheric Chemistry"),
	    ("Earth Science","Earth Science"),
	    ("Marine Science","Marine Science"),
	    ("Terrestrial and Fresh Water","Terrestrial and Fresh Water"),
	    ("Earth Observation","Earth Observation"),
	    ("Polar Science","Polar Science"),
	    ("Geography","Geography"),
	    ("Engineering","Engineering"),
	    ("Medical/Biological Sciences","Medical/Biological Sciences"),
	    ("Maths/Computing Sciences","Maths/Computing Sciences"),
	    ("Economics","Economics"),
	    ("Personal use","Personal use"),
	    ("Other","Other")
	)
    )
    
    accountid = models.CharField(max_length=20, blank=True)
    
    accounttype = models.CharField(max_length=10,
               choices=(
	               ("Web", "Web"), 
	               ("Tornado", "Tornado"), 
		       ("Openid", "Openid"),
                       ("None", "None"),   
		       ("Removed", "Removed"),
		       ("Suspended", "Suspended"),   	   			       
	               )
    )

#    webpasswd = models.CharField(max_length=13)  #Don't use this field.
    encpasswd = models.CharField(max_length=13) 
    md5passwd = models.CharField(max_length=32) 
    startdate = models.DateTimeField()
    webpage = models.CharField(max_length=100, blank=True)
#    sharedetails = models.IntegerField()
    datacenter = models.CharField(max_length=30)
    openid_username_component = models.CharField(max_length=100)
    openid = models.CharField(max_length=100)
#    onlinereg = models.IntegerField()

    def institute (self):
       return self.addresskey.institutekey.name
    
    def address (self):
       """Returns full address as string"""
       return self.addresskey.address1 + self.addresskey.address2 +  self.addresskey.address3 + self.addresskey.address4 + self.addresskey.address5 
             
    def displayName (self, titleFirst=True):
       """ Displays name """
       
       if titleFirst:
          return '%s %s %s' % (self.title, self.othernames, self.surname)       
       else:
          return '%s, %s %s' % (self.surname, self.title, self.othernames)
       
    def datasets(self, removed=False):
#
#             Returns list of dataset objects belonging to this user. By default returns only current datasets. Optionally can
#             return removed datasets
#    
        if removed:
           datasets=self.datasetjoin_set.all().filter(removed__exact=-1)
	else:
	   datasets=self.datasetjoin_set.all().filter(removed__exact=0)
	   
        return datasets

    def datasetCount(self, removed=False):
    
       return len(self.datasets(removed=removed))

    datasetCount.short_description='Datasets'
           
    def datasetRequests(self):
        requests=self.datasetrequest_set.all()
	   
        return requests
 
          
    def __unicode__(self):
        return str(self.userkey)

    class Meta:
        ordering = ['-userkey']
        db_table = u'tbusers'
	managed  = False
	get_latest_by = 'startdate'


class Datasetjoin(models.Model):
    id =      models.AutoField(primary_key=True)
    userkey = models.ForeignKey(User, db_column='userkey')
    datasetid = models.ForeignKey(Dataset, db_column='datasetid')
    ver = models.IntegerField()
    endorsedby = models.CharField(max_length=50)
    endorseddate = models.DateTimeField()
    research = models.CharField(max_length=1500)
    nercfunded = models.BooleanField()
    removed = models.IntegerField()
    removeddate = models.DateTimeField()
    fundingtype = models.CharField(max_length=40)
    grantref = models.CharField(max_length=40)
    openpub = models.CharField(max_length=1) # This field type is a guess.
    extrainfo = models.CharField(max_length=3000)
    expiredate = models.DateTimeField()
    class Meta:
        db_table = u'tbdatasetjoin'
	managed  = False

class Datasetrequest(models.Model):
    id = models.IntegerField(primary_key=True)
    userkey = models.ForeignKey(User, db_column='userkey')
    datasetid = models.ForeignKey(Dataset, db_column='datasetid')
    requestdate = models.DateTimeField()
    research = models.CharField(max_length=1500)
    nercfunded = models.IntegerField()
    fundingtype = models.CharField(max_length=40)
    grantref = models.CharField(max_length=40)
    openpub = models.TextField() # This field type is a guess.
    extrainfo = models.CharField(max_length=1000)
    fromhost = models.CharField(max_length=80)
    status = models.CharField(max_length=12)
    
    def accountid (self):
       return self.userkey.accountid
  
    accountid.admin_order_field = 'userkey__accountid'
           
    class Meta:
        db_table = u'datasetrequest'
	managed  = False

class Privilege(models.Model):
    id      = models.IntegerField(primary_key=True)
    userkey =  models.ForeignKey(User, db_column='userkey')
    type    = models.CharField(max_length=25,
               choices=(
	               ("authorise", "Authorise"), 
	               ("viewusers", "Viewusers"),   	   			       
	               )
    )
    
    datasetid = models.ForeignKey(Dataset, db_column='datasetid')
    comment = models.CharField(max_length=200)

    def accountid (self):
       return self.userkey.accountid
  
    accountid.admin_order_field = 'userkey__accountid'

    class Meta:
        db_table = u'privilege'
	managed  = False


class Datasetexpirenotification(models.Model):
    id = models.IntegerField(primary_key=True)
    userkey = models.IntegerField()
    datasetid = models.CharField(max_length=40)
    ver = models.IntegerField()
    date = models.DateTimeField()
    emailaddress = models.CharField(max_length=50)
    extrainfo = models.CharField(max_length=1500)
    class Meta:
        db_table = u'datasetexpirenotification'
        managed = False
