from django.db import models

# Create your models here.


class Country(models.Model):
    name = models.CharField(max_length=200)
    area = models.CharField(max_length=50,       
              choices=(("other","Other"),
                 ("UK","UK"),
                 ("europe","Europe")) )
    isocode =  models.CharField(max_length=200)


    def __unicode__(self):
        return self.name



class Institute(models.Model):
    name = models.CharField(max_length=200)
    country =  models.ForeignKey(Country)
    itype = models.CharField(max_length=200)
    link =  models.CharField(max_length=200, blank=True, null=True)
   
    def __unicode__(self):
        return self.name

class User(models.Model):
    title = models.CharField(max_length=10,       
              choices=(("Mr","Mr"),("Mrs","Mrs"),("Dr","Dr"),
                       ("Miss","Miss"),("Ms","Ms"), ("Prof","Prof"))) 
    surname = models.CharField(max_length=50) 
    othernames = models.CharField(max_length=100) 
    telephoneno = models.CharField(max_length=50, blank=True, null=True) 
    faxno = models.CharField(max_length=50, blank=True, null=True) 
    emailaddress = models.CharField(max_length=100) 
    comments = models.TextField(blank=True, null=True) 
    endorsedby = models.CharField(max_length=50, blank=True, null=True) 
    degree = models.CharField(max_length=20, blank=True, null=True,       
              choices=(("BS","BS"),("BSc","BSc"),("MA","MA"),
                       ("MPhil","MPhil"),("MSc","MSc"), ("MSci","MSci"),
		       ("PhD","PhD"),("RMS","RMS"),("Other","Other"))) 
    field = models.CharField(max_length=100, blank=True, null=True) 
    accountid = models.CharField(max_length=50) 
    accounttype = models.CharField(max_length=30,       
              choices=(("Tornado","Tornado"),("Web","Web"),("Share","Share"),
                       ("None","None"))) 
    encpasswd = models.CharField(max_length=30, blank=True, null=True) 
    md5passwd = models.CharField(max_length=50, blank=True, null=True) 
    startdate = models.DateField(auto_now_add=True) 
    onlinereg = models.BooleanField() 
    webpage = models.CharField(max_length=256, blank=True, null=True) 
    sharedetails = models.BooleanField() 
    datacentre = models.CharField(max_length=50, blank=True, null=True) 
    openid_username_component = models.CharField(max_length=200, blank=True, null=True) 
    openid = models.CharField(max_length=256, blank=True, null=True) 
    department = models.CharField(max_length=256, blank=True, null=True) 
    address1 = models.CharField(max_length=256, blank=True, null=True) 
    address2 = models.CharField(max_length=256, blank=True, null=True) 
    address3 = models.CharField(max_length=256, blank=True, null=True) 
    address4 = models.CharField(max_length=256, blank=True, null=True)
    address5 = models.CharField(max_length=256, blank=True, null=True)
    institute = models.ForeignKey(Institute)   

    def __unicode__(self):
        return "%s %s %s (%s)" % (self.title, self.othernames, self.surname, self.institute)
    

class Role(models.Model):
    name = models.CharField(max_length=50) 
    authtype = models.CharField(max_length=50)
    grouptype = models.CharField(max_length=50)
    description = models.TextField()
    source = models.CharField(max_length=50)
    ukmoform = models.BooleanField()
    comments = models.TextField()
    directory = models.CharField(max_length=200)
    metdata = models.BooleanField()
    conditions = models.CharField(max_length=200)
    defaultreglength = models.IntegerField()
    datacentre = models.CharField(max_length=50) 
    infourl = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name




class Licence(models.Model):
    role = models.ForeignKey(Role)
    user = models.ForeignKey(User)
    ver = models.IntegerField()
    endorsedby = models.CharField(max_length=50) 
    endorseddate = models.DateField(auto_now_add=True)
    research = models.TextField() 
    nercfunded = models.BooleanField()
    removed = models.BooleanField()
    removedate = models.DateField()
    grantref = models.CharField(max_length=50, blank=True, null=True) 
    openpub = models.CharField(max_length=10, blank=True, null=True) 
    extrainfo = models.CharField(max_length=200, blank=True, null=True) 
    expiredate = models.DateField()
    
    def __unicode__(self):
        return "%s - %s" % (self.role, self.user)
    
    
    
    
