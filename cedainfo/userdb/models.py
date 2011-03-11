from django.db import models
import md5

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
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=50)
    email = models.EmailField()     
    tel = models.CharField(max_length=50, blank=True, null=True) 
    address = models.TextField(blank=True, null=True)
    postcode = models.CharField(max_length=10, blank=True, null=True)
    webpage = models.CharField(max_length=256, blank=True, null=True)    
    comments = models.TextField(blank=True, null=True)
    studying_for = models.CharField(max_length=20, blank=True, null=True,
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
    field = models.CharField(max_length=100, blank=True, null=True,  
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
    supervisor = models.CharField(max_length=50, blank=True, null=True)
    password_md5 = models.CharField(max_length=50, blank=True, null=True)# md5 encrypted password
    startdate = models.DateField(auto_now_add=True) # date account created
    reg_source = models.CharField(max_length=50, blank=True, null=True) # where the user registered (choices : as per current table)
    openid = models.CharField(max_length=256, blank=True, null=True)    
    username = models.CharField(max_length=50)
    institute =  models.ForeignKey(Institute)
    # TODO custom save method:
    #   - if emailaddress or institute are changned, notify helpdesk

    def __unicode__(self):
        return "%s %s %s" % (self.title, self.firstname, self.lastname)

    def update_passwd(self, passwd):

        md5password = md5.new(passwd).hexdigest()
	self.password_md5 = md5password
	#PasswdUtils::updatePasswd ($user, $CGIpasswd);

        # Write message to log file and send informational message
        msg = "updated password for accountID=%s userkey=%s (web)" % (self.username, self.pk)
        #WebRegUtils::write_log_msg(msg)
        mail_info_msg(user)

	

class Group(models.Model):
    # use implicit id as PK
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    valid_from = models.DateField(blank=True, null=True) # Default? Allow Blank/Null?
    valid_to = models.DateField(blank=True, null=True) # Default? Allow Blank/Null?
    comments = models.TextField()
    infourl = models.URLField(blank=True, null=True)
    datacentre = models.CharField(max_length=50) 
    

    def __unicode__(self):
        return self.name


    def emaillistlink(self):
        return '''<a href = "/userdb/group/emails/%s">Emails</a>''' %  (self.id,)
    emaillistlink.allow_tags = True

        
class Role(models.Model):
    # use implicit id as PK
    name = models.CharField(max_length=50) 
    description = models.TextField()
    
    # Suggested entries:
    # get (can read data)
    # put (can deposit ...not write!) data
    # admin (can grant/revoke any role to any other User in that Group)
    # receiveadminnotification 
    # viewmembership (can view membership of a Group)

    def __unicode__(self):
        return self.name

    
 

class Conditions(models.Model):
    # The text of any conditions that need signing up to to get a role in 
    # a group. THis may be shared text used by a number of groups.
    #
    # use implicit id as PK
    # ? name?
    #role = models.ForeignKey(Role)
    #group = models.ForeignKey(Group)
    # removing role and group and putting them in ApplicationProcess
    title = models.CharField(max_length=500,blank=True, null=True) # title of conditions 
    text = models.TextField() # text of conditions 
    version = models.CharField(max_length=50,blank=True, null=True) # title of conditions 
    comment = models.TextField() # internal annotation 
    
    def __unicode__(self):
        return "%s" % (self.title, )    #?
    
class ApplicationProcess(models.Model):
    # How to get a role in a group by signing up to a set of conditions
    role = models.ForeignKey(Role)
    group = models.ForeignKey(Group)
    conditions = models.ForeignKey(Conditions, blank=True, null=True)
    defaultreglength = models.IntegerField()
    authtype = models.CharField(max_length=50)
    script = models.CharField(max_length=300, blank=True, null=True)
    intro_text = models.TextField()  

    def __unicode__(self):
        return "%s %s" % (self.role, self.group)    #?
    

class Licence(models.Model):
    # use implicit id as PK
    user = models.ForeignKey(User)
    institute = models.CharField(max_length=200, blank=True, null=True) 
    email = models.EmailField(blank=True, null=True)     
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    research = models.TextField()     
    grantref = models.CharField(max_length=50, blank=True, null=True)
    funding_type =  models.CharField(max_length=100, blank=True, null=True,  
        choices=( 
	  ("NERC","NERC"),
	  ("AHRC","AHRC"),
	  ("BBSRC","BBSRC"),
	  ("EPSRC","EPSRC"),
	  ("ESRC","ESRC"),
	  ("MRC","MRC"),
	  ("STFC","STFC"),
	  ("Non-UK academic funding","Non-UK academic funding"),
	  ("Government department","Government department"),
	  ("Charitable trust","Charitable trust"),
	  ("Commercial","Commercial"),
	  ("Not funded","Not funded"),
	  ("Other","Other")))
    role = models.ForeignKey(Role)
    group = models.ForeignKey(Group)
    conditions = models.ForeignKey(Conditions, blank=True, null=True)
    request_date = models.DateTimeField(auto_now_add=True)
    extrainfo = models.TextField()
    fromhost = models.CharField(max_length=50, blank=True, null=True) 
    status = models.CharField(max_length=50, blank=True, null=True) 

    def __unicode__(self):
        return "%s - %s - %s" % (self.user.lastname, self.role, self.group)



# ditched fields

    # ditched from User
    #accounttype = models.CharField(max_length=30,       
    #          choices=(("Tornado","Tornado"),("Web","Web"),("Share","Share"),
    #                   ("None","None"))) 
    #encpasswd = models.CharField(max_length=30, blank=True, null=True) 
    #onlinereg = models.BooleanField() 
    #sharedetails = models.BooleanField() 
    #openid_username_component = models.CharField(max_length=200, blank=True, null=True) 
    #department = models.CharField(max_length=256, blank=True, null=True) 
    #address1 = models.CharField(max_length=256, blank=True, null=True) # TODO "address would be fine as textfield
    #address2 = models.CharField(max_length=256, blank=True, null=True) 
    #address3 = models.CharField(max_length=256, blank=True, null=True) 
    #address4 = models.CharField(max_length=256, blank=True, null=True)
    #address5 = models.CharField(max_length=256, blank=True, null=True)
    #institute = models.ForeignKey(Institute)

    # ditched from Role
    #authtype = models.CharField(max_length=50)
    #grouptype = models.CharField(max_length=50)
    #source = models.CharField(max_length=50)
    #ukmoform = models.BooleanField()
    #comments = models.TextField()
    #directory = models.CharField(max_length=200)
    #metdata = models.BooleanField()
    #conditions = models.CharField(max_length=200)
    #defaultreglength = models.IntegerField()
    #datacentre = models.CharField(max_length=50) 
    #infourl = models.CharField(max_length=200)
    #authorisers = models.ManyToManyField(User, blank=True)
    #authviewers = models.ManyToManyField(  
    
    # ditched from licence
    #ver = models.IntegerField()
    #endorsedby = models.CharField(max_length=50) 
    #nercfunded = models.BooleanField()
    #removed = models.BooleanField()
    #removeddate = models.DateField(null=True)
    #openpub = models.CharField(max_length=10, blank=True, null=True) 
    #extrainfo = models.TextField(blank=True, null=True) 
    #expiredate = models.DateField(null=True)
    

    
    
    
    
