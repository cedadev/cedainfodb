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
import udbadmin.choices as choices
import udbadmin.country_list  as country_list
import django.db.models.options as options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)

import base64

USERDB = 'userdb'

class Base64Field(models.TextField):
    def contribute_to_class(self, cls, name, private_only=False):
        if not self.db_column:
            self.db_column = name

        self.field_name = name + '_base64'
        super().contribute_to_class(cls,
                                    name)
        setattr(cls, self.field_name, property(self.get_data, self.set_data))

    def get_data(self, obj):
        return base64.b64encode(getattr(obj, self.name).encode('utf-8'))

    def set_data(self, obj, data):
        setattr(obj, self.field_name, base64.b64decode(data).decode('utf-8'))
	
class Dataset(models.Model):
    datasetid = models.CharField(max_length=40, primary_key=True)

    authtype = models.CharField(max_length=20,
       choices=choices.DATASET_REGISTRATION_TYPES
       )
    
    grp = models.CharField(max_length=40, verbose_name='Group', blank=True)
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
    datacentre = models.CharField(max_length=20, choices=choices.DATACENTRES, default='badc')
    infourl = models.CharField(max_length=200, blank=True)
    gid     = models.IntegerField(default=0, blank=True)
    public_key_required = models.BooleanField("Check for public key on registration", 
                                              default=False)
    
    def __str__(self):
        return self.datasetid
 
    def get_absolute_url(self):
        '''Return url for viewing details.'''    
        return "/%s/dataset/details/%s" \
            % (self._meta.app_label, self.datasetid)

    def browse_url (self):
        '''Returns url for browsing data directory (if appropriate)'''

        BROWSER = "http://badc.nerc.ac.uk/browse"

        if self.datasetid.startswith('gws_'):
            return None

        if self.datasetid.endswith('_ps'):
            return None

        if self.datasetid == 'gosta_cd':
            return None
    
        text = self.directory.strip()

        if text.startswith('http'):
            return text

        if not text.startswith('/'):    
            return None
      
        return BROWSER + self.directory

    def manual_processing_required(self):
#
#            Temporary fudge to indicate that the dataset requires "manual processing". 
#
#            26/09/13 This is now used to indicate which datasets should not receive
#            an automated e-mail when they are approved. 
#
        datasetid = self.datasetid 
       
        if datasetid.startswith('gws_') or \
           datasetid.startswith('vm_') \
           or datasetid == 'jasmin-login' \
           or datasetid == 'cems-login' \
           or datasetid == 'commercial-login':
            return True
        else:
            return False  

    def external_authoriser(self):
#
#       Returns True if this dataset has one or more authorisers who is not CEDA/BADC/NEODC
#        
        priv = Privilege.objects.filter(datasetid=self.datasetid, type='authorise')
         
        for p in priv:
            if p.userkey.userkey > 0:
                return True 

        return False
      
    class Meta:
        in_db = USERDB
        db_table = 'tbdatasets'
        ordering = ['datasetid']
        managed  = False

class Institute(models.Model):
    institutekey = models.IntegerField(primary_key=True)
    name = models.CharField('Institute Name', 
         help_text=
   'Name of institute, universtity or other organisation for which you work', 
         max_length=80)
    country = models.CharField('Institute Country', 
               help_text='Home country of your host institue', max_length=30,
               choices=country_list.COUNTRY_LIST)
    type = models.CharField('Institute type', max_length=30,
               help_text='Commercial, Government, University, etc',
               choices=choices.INSTITUTE_TYPES)
    link = models.CharField('Institute URL', blank=True,
                help_text='Public web page of Institute',
                max_length=100)
    class Meta:
        in_db = USERDB
        db_table = 'tbinstitutes'
        managed  = False

class Addresses(models.Model):
    addresskey = models.IntegerField(primary_key=True)
    institutekey = models.ForeignKey(Institute, on_delete=models.PROTECT, db_column='institutekey')
    department = models.CharField(max_length=100, blank=True, help_text='Your department within your host institute')

    def __str__ (self):
        return "%s" % self.addresskey
       
    class Meta:
        in_db = USERDB
        db_table = 'addresses'
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

    title = models.CharField(max_length=10, help_text='Title',
          choices=(
              ("Mr","Mr"),
              ("Mrs","Mrs"),
              ("Dr","Dr"),
              ("Miss","Miss"),
              ("Ms","Ms"),
              ("Mx", "Mx"),
              ("Prof","Prof")
          )
        ) 

    surname = models.CharField(max_length=50, help_text='Surname')
    othernames = models.CharField(max_length=50, verbose_name='Other names', help_text='Christian or Forenames')
    addresskey = models.OneToOneField(Addresses, on_delete=models.PROTECT, db_column='addresskey')
    telephoneno = models.CharField('Telephone number', max_length=50, blank=True, help_text='Your contact telephone number in case we need to call you (e.g. helpdesk assistance)')
    emailaddress = models.EmailField('Email Address', max_length=100, unique=False, help_text='Your institute/work email address. A personal email address may be used, but may cause delays in processing access applications.')
    comments = models.TextField(blank=True)
    endorsedby = models.CharField("Supervisor's name", 
                           max_length=50, 
                           blank=True, 
                           help_text='Your academic supervisor. This is a required field for all students')
#    degree = models.CharField('Degree you are studying for', max_length=20)
    
    degree = models.CharField('Degree you are studying for', max_length=20, blank=True, null=True, 
        help_text = 'Enter the qualification for which you are currently studying',
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
        
    field = models.CharField('Discipline', max_length=50, blank=False, null=True,  
        help_text = 'Select a subject discipline that closest matches the field you are working in',
        choices=(
            ("Atmospheric Physics","Atmospheric Physics"),
            ("Atmospheric Chemistry","Atmospheric Chemistry"),
            ("Climate Change","Climate Change"),
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
    
    accountid = models.CharField('User Name', 
                                 max_length=20, blank=True, 
                                 help_text='Your username for the CEDA site and services') 

    jasminaccountid = models.CharField('JASMIN accountid', 
                                 max_length=20, blank=True, 
                                 help_text='Username in JASMIN system')
 
    
    accounttype = models.CharField(max_length=10,
               choices=(
                       ("Web", "Web"), 
                       ("Openid", "Openid"),
                       ("None", "None"),   
                       ("Suspended", "Suspended"),                                     
                       )
    )

#    webpasswd = models.CharField(max_length=13)  #Don't use this field.
    encpasswd = models.CharField(max_length=13) 
    md5passwd = models.CharField(max_length=32)
    public_key = models.TextField('Public Key', blank=True,  
                                  help_text='RSA public key required for access to JASMIN or CEMS systems')  
    startdate = models.DateTimeField()
#    sharedetails = models.IntegerField()
    datacenter = models.CharField(max_length=30)
    openid_username_component = models.CharField('OpenID Username Component',max_length=100, 
                                  help_text='The unique part of your OpenID address')
    openid = models.URLField(max_length=100, blank=True, 
           help_text='This link address is your OpenID address for use where you see the "OpenID" log in option')
    uid     = models.IntegerField(default=0, blank=True)
    home_directory = models.CharField(max_length=150, blank=True)
    shell = models.CharField(max_length=50, blank=True)  
    gid   = models.IntegerField(default=0, blank=True)  
    reset_token = models.CharField(max_length=40, blank=True)  
    token_expire = models.DateTimeField(blank=True)
    secret_data = models.CharField(max_length=200, null=True, blank=True)
    
#    onlinereg = models.IntegerField()

    def institute (self):
        return self.addresskey.institutekey.name
    
    def address (self):
        """Dummy routine. Address no longer used."""
                       
        return ""
               
    def displayName (self, titleFirst=True):
        """ Displays name """
       
        if titleFirst:
            return '%s %s %s' % (self.title, self.othernames, self.surname)       
        else:
            return '%s, %s %s' % (self.surname, self.title, self.othernames)
       
    def datasets(self, removed=False, filter_duplicates=False):

        '''Returns list of dataset objects belonging to this user. 
           By default returns only current datasets. Optionally can
           return removed datasets. Can also optionally remove any
           duplicate datasets from current datasets (probably no
           point in doing this for removed datasets).
        '''
    
        if removed:
            datasets=self.datasetjoin_set.all().filter(removed__exact=-1)
        else:
            datasets=self.datasetjoin_set.all().filter(removed__exact=0)

            if filter_duplicates:
                filtered_datasets = []
                datasetids = []
                for dataset in datasets:
                        try:
                            if dataset.datasetid in datasetids:
                                pass
                            else:
                                filtered_datasets.append(dataset)
                                datasetids.append(dataset.datasetid)
                        except:
                            pass 
                return filtered_datasets
               
        return datasets

    def currentDatasets(self, filter_duplicates=False):
        return self.datasets(removed=False, filter_duplicates=filter_duplicates)

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
        
        if self.hasDataset("jasmin-login") or \
           self.hasDataset("cems-login") or \
           self.hasDataset("commercial-login"):
            return True
        else:
            return False                 

    def isSystemUser(self):
        '''Returns True if this is not a real person but a system account.'''
        
        if self.hasDataset("ldap_system_user") or \
           self.accountid == 'et_jasmin' or \
           self.othernames.startswith('system_user'):
            return True
        else:
            return False                 

    def pending_vm_request(self):
        
        """
        Checks if the given user has a pending request for a vm account
        """

        requests = self.pendingDatasets()
         
        for request in requests:
            if request.datasetid.datasetid == 'jasmin-login' or \
                request.datasetid.datasetid == 'cems-login' or \
                request.datasetid.datasetid == 'commercial-login':

                    return True

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
  
           
    def __str__(self):
        return str(self.userkey)

    objects = UserManager() 
    
    class Meta:
        in_db = USERDB
        ordering = ['-userkey']
        db_table = 'tbusers'
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
    userkey = models.ForeignKey(User, on_delete=models.PROTECT, db_column='userkey')
    datasetid = models.ForeignKey(Dataset, on_delete=models.PROTECT, db_column='datasetid')
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
    agreement = Base64Field(null=True, blank=True)

    def days_until_expires(self):
        '''
        Returns the number of days until the registraion expires, or None if
        this could not be calculated (e.g. there is no expiry date set).
        '''
        try:
            a = self.expiredate 

            b = datetime.today()
            delta = a - b
            return delta.days
        except:
            return None
                    
    def removeDataset(self):
        self.removed = -1
        self.removeddate = datetime.now(timezone('Europe/London'))
        self.save()
       
    class Meta:
        in_db = USERDB
        db_table = 'tbdatasetjoin'
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
    
    id = models.AutoField(primary_key=True)
    userkey = models.ForeignKey(User, on_delete=models.PROTECT, db_column='userkey')
    datasetid = models.ForeignKey(Dataset, on_delete=models.PROTECT, db_column='datasetid')
    requestdate = models.DateTimeField()
    research = models.CharField(max_length=1500)
    nercfunded = models.IntegerField()
    fundingtype = models.CharField(max_length=40, choices=choices.FUNDING_TYPES)
    grantref = models.CharField(max_length=40)
    openpub = models.TextField() # This field type is a guess.
    extrainfo = models.CharField(max_length=1000)
    fromhost = models.CharField(max_length=80)
    status = models.CharField(max_length=12)
    agreement = Base64Field(null=True, blank=True)
    
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
        b = Datasetjoin(userkey=self.userkey, 
                        datasetid=self.datasetid,
                        ver=version,
                        nercfunded=self.nercfunded,
                        removed=0,
                        endorsedby=endorsedby,
                        research=self.research,
                        endorseddate=datetime.now(timezone('Europe/London')),
                        fundingtype = self.fundingtype,
                        grantref=self.grantref,
                        openpub=self.openpub,
                        extrainfo=self.extrainfo,
                        expiredate=expireDate,
                        agreement=self.agreement)
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
        db_table = 'datasetrequest'
        managed  = False
        ordering = ['-requestdate']

class Privilege(models.Model):
    id      = models.AutoField(primary_key=True)
    userkey =  models.ForeignKey(User, on_delete=models.PROTECT, db_column='userkey', to_field='userkey', null=True)
    type    = models.CharField(max_length=25,
               choices=(
                       ("authorise", "Authorise"), 
                       ("viewusers", "Viewusers"),                                     
                       )
    )
    
    datasetid = models.ForeignKey(Dataset, on_delete=models.PROTECT, db_column='datasetid')
    comment = models.CharField(max_length=200, blank=True)

    def accountid (self):
        return self.userkey.accountid
  
    accountid.admin_order_field = 'userkey__accountid'

    class Meta:
        in_db = USERDB
        db_table = 'privilege'
        managed  = False


class Datasetexpirenotification(models.Model):
    id = models.AutoField(primary_key=True)
    userkey = models.IntegerField()
    datasetid = models.CharField(max_length=40)
    ver = models.IntegerField()
    date = models.DateTimeField()
    emailaddress = models.CharField(max_length=50)
    extrainfo = models.CharField(max_length=1500)
    class Meta:
        in_db = USERDB
        db_table = 'datasetexpirenotification'
        managed = False

class Fundingtypes(models.Model):
    id = models.IntegerField(primary_key=True)
    ordering = models.IntegerField()
    name = models.CharField(max_length=40)
    class Meta:
        in_db = USERDB
        db_table = 'fundingtypes'
        managed = False

