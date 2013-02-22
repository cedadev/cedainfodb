'''
BSD Licence
Copyright (c) 2012, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, 
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the documentation
        and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC) 
        nor the names of its contributors may be used to endorse or promote 
        products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 28 Nov 2012

@author: Andrew Harwood
@author: Maurizio Nagni
'''
from django.db import models

from django.db.models import Max, Min

from datetime import datetime
from pytz import timezone
import choices
import django.db.models.options as options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)

USERDB = u'userdb'
        
class Dataset(models.Model):
    datasetid = models.CharField(max_length=40, primary_key=True)

    authtype = models.CharField(max_length=20,
       choices=choices.DATASET_REGISTRATION_TYPES
       )
    
    grp = models.CharField(max_length=40, verbose_name='Group')
    grouptype = models.CharField(max_length=20)
    description = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50)
    ukmoform = models.IntegerField(default=0)
#    ordr = models.IntegerField()
    comments = models.CharField(max_length=200, blank=True)
    directory = models.CharField(max_length=100, blank=True)
#    metdata = models.IntegerField()
    conditions = models.CharField(max_length=100, blank=True)
    defaultreglength = models.IntegerField()
    datacentre = models.CharField(max_length=20, choices=choices.DATACENTRES)
    infourl = models.CharField(max_length=200, blank=True)
    gid     = models.IntegerField(default=0, blank=True)
    public_key_required = models.BooleanField("Check for public key on registration", 
                                              default=False)
    
    def __unicode__(self):
        return self.datasetid
 
    def get_absolute_url(self):
        '''Return url for viewing details.'''    
        return "/%s/dataset/details/%s" \
            % (self._meta.app_label, self.datasetid)

    def manual_processing_required(self):
#
#            Temporary fudge to indicate that the dataset requires "manual processing", ie Andrew needs to do some work once this dataset/service is approved
#
        datasetid = self.datasetid 
       
        if datasetid.startswith('gws_') or datasetid.startswith('vm_') \
            or datasetid == 'jasmin-login' or datasetid == 'cems-login':
            return True
        else:
            return False  

              
    class Meta:
        in_db = USERDB
        db_table = u'tbdatasets'
        ordering = ['datasetid']
        managed  = False
 


class Institute(models.Model):
    institutekey = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=80)
    country = models.CharField(max_length=30)
    type = models.CharField(max_length=30)
    link = models.CharField(max_length=100)
    class Meta:
        in_db = USERDB
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
        in_db = USERDB
        db_table = u'addresses'
        managed  = False

class UserManager(models.Manager):
    '''Contains class methods for User class.'''
   
    def maxUserkey (self):       
        '''Returns the maximum userkey value'''
        return User.objects.aggregate(Max('userkey'))['userkey__max']
      
    def minUserkey (self):       
        '''Returns the minimum userkey value'''
        return User.objects.aggregate(Min('userkey'))['userkey__min']

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
    emailaddress = models.CharField(max_length=100)
    comments = models.TextField(blank=True)
    endorsedby = models.CharField(max_length=50, blank=True)
    degree = models.CharField(max_length=20)
    
    degree = models.CharField(max_length=20, blank=True, null=True, verbose_name='Studying for',
        choices=(
            ("BA","BA"),
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
    public_key = models.TextField(blank=True) 
    startdate = models.DateTimeField()
    webpage = models.CharField(max_length=100, blank=True)
#    sharedetails = models.IntegerField()
    datacenter = models.CharField(max_length=30)
    openid_username_component = models.CharField(max_length=100)
    openid = models.CharField(max_length=100, blank=True)

    uid     = models.IntegerField(default=0, blank=True)
    home_directory = models.CharField(max_length=150, blank=True)
    shell = models.CharField(max_length=50, blank=True)  
    gid   = models.IntegerField(default=0, blank=True)  
#    onlinereg = models.IntegerField()

    def institute (self):
        return self.addresskey.institutekey.name
    
    def address (self):
        """Returns full address as string. Each line is separated by a comma."""
        
        a1 = self.addresskey.address1.rstrip(", ")
        a2 = self.addresskey.address2.rstrip(", ")
        a3 = self.addresskey.address3.rstrip(", ")
        a4 = self.addresskey.address4.rstrip(", ")
        a5 = self.addresskey.address5.rstrip(", ")
        
        addressLine = a1
        if a2: addressLine = addressLine + ", " + a2
        if a3: addressLine = addressLine + ", " + a3
        if a4: addressLine = addressLine + ", " + a4
        if a5: addressLine = addressLine + ", " + a5
                
        return addressLine
             
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

    def currentDatasets(self):
        return self.datasets(removed=False)

    def removedDatasets(self):
        return self.datasets(removed=True)
        
    def pendingDatasets(self):
        return self.datasetRequests(status='pending')
       
    def datasetCount(self, removed=False):    
        return len(self.datasets(removed=removed))

    datasetCount.short_description='Datasets'         
           
    def datasetRequests(self, status=''):
        '''Return users entries in datasetRequests table. Optionally only returns entries for given status.'''    

        if status:
            requests=self.datasetrequest_set.all().filter(status__exact=status)
        else:
            requests=self.datasetrequest_set.all()
        return requests

    def hasDataset(self, datasetid):
        """Checks if the user has access to the given datasetid"""
           
        if self.datasetjoin_set.all().filter(removed__exact=0, datasetid=datasetid):  
            return True
        else:
            return False    

    def isJasminCemsUser(self):
        '''Returns True if the user should have a jasmin/cems account'''
        
        if self.hasDataset("jasmin-login") or self.hasDataset("cems-login"):
            return True
        else:
            return False                 
     
    def nextUserkey (self):        
        '''Returns the next userkey value'''

        if self.userkey == User.objects.maxUserkey():
            return self.userkey
        else:
            next = self.userkey + 1
           
            if next == 0: 
                next = 1   
            return next

    def previousUserkey (self):      
        '''Returns the previous userkey value'''
        return self.userkey -1
  
           
    def __unicode__(self):
        return str(self.userkey)

    objects = UserManager() 
    
    class Meta:
        in_db = USERDB
        ordering = ['-userkey']
        db_table = u'tbusers'
        managed  = False
        get_latest_by = 'startdate'


class DatasetJoinManager(models.Manager):
    '''Contains class methods for DatasetJoin table class.'''
    def getDatasetVersion (self, userkey, datasetid):       
        '''Returns the version number to use for registering the given dataset to the given user.'''

        #
        #          Find the maximum version number already used for this dataset for this user and increment. 
        #
        q = Datasetjoin.objects.filter(userkey=userkey).filter(datasetid=datasetid).aggregate(Max('ver'))
      
        if q['ver__max'] != None:
            return q['ver__max'] + 1
        else:
            return 0
                 
class Datasetjoin(models.Model):
    id =      models.AutoField(primary_key=True)
    userkey = models.ForeignKey(User, db_column='userkey')
    datasetid = models.ForeignKey(Dataset, db_column='datasetid')
    ver = models.IntegerField()
    endorsedby = models.CharField(max_length=50)
    endorseddate = models.DateTimeField()
    research = models.CharField(max_length=1500)
    nercfunded = models.IntegerField(default=0)
    removed = models.IntegerField(default=0)
    removeddate = models.DateTimeField()
    fundingtype = models.CharField(max_length=40, choices=choices.FUNDING_TYPES)
    grantref = models.CharField(max_length=40)
    openpub = models.CharField(max_length=1) # This field type is a guess.
    extrainfo = models.CharField(max_length=3000)
    expiredate = models.DateTimeField()
                
    def removeDataset(self):
        self.removed = -1
        self.removeddate = datetime.now(timezone('Europe/London'))
        self.save()
       
    class Meta:
        in_db = USERDB
        db_table = u'tbdatasetjoin'
        managed  = False

    objects = DatasetJoinManager() 

class Datasetrequest(models.Model):
#
#      Define allowed states for requests
#
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    JUNK     = 'junk'
    PENDING  = 'pending'
    
    id = models.IntegerField(primary_key=True)
    userkey = models.ForeignKey(User, db_column='userkey')
    datasetid = models.ForeignKey(Dataset, db_column='datasetid')
    requestdate = models.DateTimeField()
    research = models.CharField(max_length=1500)
    nercfunded = models.IntegerField()
    fundingtype = models.CharField(max_length=40, choices=choices.FUNDING_TYPES)
    grantref = models.CharField(max_length=40)
    openpub = models.TextField() # This field type is a guess.
    extrainfo = models.CharField(max_length=1000)
    fromhost = models.CharField(max_length=80)
    status = models.CharField(max_length=12)
    
    def accountid (self):
        '''Return user accountid associated with this request.'''
        return self.userkey.accountid
  
    accountid.admin_order_field = 'userkey__accountid'
           
           
    def accept (self, endorsedby='', expireDate=''):
        '''Accept the dataset request'''        
#
#               Set 'version' to appropriate value by finding highest version number for this user and this dataset and incrementing
#
        version = Datasetjoin.objects.getDatasetVersion(self.userkey, self.datasetid)
#
#               Create new entry in datasetjoin table, copying values from datasetreqest
#        
        b = Datasetjoin(userkey=self.userkey, datasetid=self.datasetid, ver=version, nercfunded=0, removed=0, endorsedby=endorsedby, research=self.research, endorseddate=datetime.now(timezone('Europe/London')), fundingtype = self.fundingtype, grantref=self.grantref, openpub=self.openpub, extrainfo=self.extrainfo, expiredate=expireDate)
        b.save()
         
        self.status = self.ACCEPTED
        self.save()

    def reject (self):
        '''Reject the dataset request'''        
         
        self.status = self.REJECTED
        self.save()

    def junk (self):
        '''Junk the dataset request'''        
         
        self.status = self.JUNK
        self.save()
           
           
    class Meta:
        in_db = USERDB
        db_table = u'datasetrequest'
        managed  = False
        ordering = ['-requestdate']

class Privilege(models.Model):
    id      = models.AutoField(primary_key=True)
    userkey =  models.ForeignKey(User, db_column='userkey', to_field='userkey', null=True)
    type    = models.CharField(max_length=25,
               choices=(
                       ("authorise", "Authorise"), 
                       ("viewusers", "Viewusers"),                                     
                       )
    )
    
    datasetid = models.ForeignKey(Dataset, db_column='datasetid')
    comment = models.CharField(max_length=200, blank=True)

    def accountid (self):
        return self.userkey.accountid
  
    accountid.admin_order_field = 'userkey__accountid'

    class Meta:
        in_db = USERDB
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
        in_db = USERDB
        db_table = u'datasetexpirenotification'
        managed = False

class Fundingtypes(models.Model):
    id = models.IntegerField(primary_key=True)
    ordering = models.IntegerField()
    name = models.CharField(max_length=40)
    class Meta:
        in_db = USERDB
        db_table = u'fundingtypes'
        managed = False
