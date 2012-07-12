from django.contrib import admin
from django.forms import *
from models import *
from django.utils.safestring import mark_safe
from forms import *

from django.contrib.auth.models import User as SiteUser
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
#admin.site.unregister(SiteUser)
#admin.site.unregister(Group)


class DatasetjoinAdmin(admin.ModelAdmin):

   def has_add_permission(self, request, obj=None):
       return False
   def has_delete_permission(self, request, obj=None):
       return False

   
   def editLink(self):
      url = "/%s/udj/%s" % (self._meta.app_label, self.id)
      return mark_safe('<a href="%s">Edit</a>' % url)
   editLink.allow_tags = True
   editLink.short_description = 'Edit'
   
   list_display = (editLink, 'userkey', 'datasetid', 'ver', 'research', 'removed')
   list_filter = ('removed', 'datasetid')
   readonly_fields = ('datasetid', 'userkey')
   search_fields =['research']


admin.site.register(Datasetjoin, DatasetjoinAdmin)



class DatasetAdmin(admin.ModelAdmin):

   form = DatasetForm
#
#    This overrides all fields in this form
#
   formfield_overrides = {
       models.CharField: {'widget': TextInput(attrs={'size':'50'})},
   }

   def showUsers (self):
      return  mark_safe ('<a href="/udbadmin/dataset/users/%s">Users</a>' % self.datasetid)
   showUsers.allow_tags = True
   showUsers.short_description = 'Show users'   

   list_display = ('datasetid', 'authtype', 'grp', 'description', 'datacentre', showUsers)
   list_filter = ('datacentre', 'authtype')
#   exclude = ('grouptype', 'source', 'ukmoform')
   fields = ('datasetid', 'authtype', 'grp', 'description', 'directory', 'conditions', 'defaultreglength', 'datacentre', 'infourl', 'comments')
   search_fields =['datasetid', 'description']
#
#     Set datasetid to be read-only on edit form but allow entry on create form
#
   def get_readonly_fields(self, request, obj = None):
       if obj: #In edit mode
           return ('datasetid',) + self.readonly_fields
       return self.readonly_fields   
       
admin.site.register(Dataset, DatasetAdmin)


class InstituteAdmin(admin.ModelAdmin):

#
#      Forbit adding and deleging users
#
   def has_add_permission(self, request, obj=None):
        return False
   def has_delete_permission(self, request, obj=None):
        return False

   list_display = ('institutekey', 'name', 'country', 'type', 'link')
   list_filter = ('type', 'country')
   search_fields = ('name',)

admin.site.register(Institute, InstituteAdmin)
    
class UserAdmin(admin.ModelAdmin):
#
#      Forbit adding and deleging users
#
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    def links (self):
    
       removedDatasets = len(self.datasets(removed=True))
       currentDatasets = len(self.datasets(removed=False))
       pendingDatasets = len(self.datasetRequests(status='pending'))
       
       nextUserkey     = self.nextUserkey()
       previousUserkey = self.previousUserkey()
       latestUserkey   = User.objects.maxUserkey()
       firstUserkey    = User.objects.minUserkey()
       
       
       a = '<table border="0"><tr><td>'
       a += ' <a href="/%s/user/datasets/current/%s">Current datasets (%s)</a> | ' % (self._meta.app_label, self.userkey, currentDatasets)
       a += ' <a href="/%s/user/datasets/removed/%s">Removed datasets (%s)</a> | ' % (self._meta.app_label, self.userkey, removedDatasets)
       a += ' <a href="/%s/authorise/%s">Pending datasets (%s)</a> | ' % (self._meta.app_label, self.userkey, pendingDatasets)
       a += ' <a href="/%s/user/datasets/add/%s">Add datasets</a>' % (self._meta.app_label, self.userkey)
       
       a += '</td><td>&nbsp;</td><td><b>User navigation</b>: '
       a += '<a href="/admin/udbadmin/user/%s">First</a> | ' % firstUserkey              
       a += '<a href="/admin/udbadmin/user/%s">Previous</a> | ' % previousUserkey       
       a += '<a href="/admin/udbadmin/user/%s">Next</a> | ' % nextUserkey
       a += '<a href="/admin/udbadmin/user/%s">Last</a>' % latestUserkey       
       a += '</td></tr></table>'
       return mark_safe(a)
       
    links.short_description = 'Related pages'

    def password (self):
          
       a = '<a target="_blank" href="http://team.ceda.ac.uk/cgi-bin/userdb/change_web_passwd.cgi.pl?accountid=%s">Change</a> | ' % self.userkey
       a += '<a target="_blank" href="http://team.ceda.ac.uk/cgi-bin/userdb/reset_passwd.cgi.pl?accountid=%s">Reset password and email user</a>' % self.userkey
       
       return mark_safe(a)
       
    password.short_description = 'Password'

    def showDatasets (self):
         
	 datasets = self.datasets(removed=False)
	 datasets = datasets.order_by("datasetid")

         a = 'Details: '
         a += ' <a href="/%s/user/datasets/current/%s">Current datasets</a> |' % (self._meta.app_label, self.userkey)
         a += ' <a href="/%s/user/datasets/removed/%s">Removed datasets</a> |' % (self._meta.app_label, self.userkey)
         a += ' <a href="/%s/authorise/%s">Pending datasets</a>' % (self._meta.app_label, self.userkey)	 
         a += '<p/>'
	 
	 a+= '<ul>'
	 for dataset in datasets:
            a +=  '<li>' + str(dataset.datasetid)
	 a+='</ul>'
	    
	 return mark_safe(a)
	 
    showDatasets.short_description = 'Datasets'
    	 
    def startdate (self):
       return self.startdate.strftime('%d-%b-%Y')

    startdate.admin_order_field = 'startdate' 
           	     	 
    list_display = ('userkey', 'title', 'othernames', 'surname', 'accountid', 'emailaddress', startdate, 'field', 'datasetCount')
    list_filter = ('title', 'degree', 'accounttype', 'field','startdate','datacenter')
    search_fields = ['surname', 'othernames', 'accountid', 'emailaddress']
    list_per_page = 200
    
#    exclude = ('encpasswd', 'md5passwd', 'onlinereg')
    readonly_fields = (showDatasets, 'datacenter', 'userkey', 'address', 'accountid', 'addresskey', 'startdate', 'encpasswd', 'md5passwd', 'institute', links, password)

    fields = (links, 'userkey', 'title', 'surname', 'othernames', 'emailaddress',
               'webpage', 'telephoneno', 'accountid', 'openid', 'accounttype',  password, 
	       'degree', 'endorsedby', 'field', 'startdate', showDatasets, 'datacenter', 'institute', 'address', 'comments')
#    list_editable = ('accountid','title')


admin.site.register(User, UserAdmin)

class DatasetrequestAdmin(admin.ModelAdmin):

   def has_add_permission(self, request, obj=None):
       return False
   def has_delete_permission(self, request, obj=None):
       return False

   def requestdate (self):
       return self.requestdate.strftime('%d-%b-%Y')
       	 
   requestdate.admin_order_field = 'requestdate' 
      
   def accountidLink(self):
      return mark_safe('<a href="/admin/%s/user/%s" title="View user details">%s</a>' % (self._meta.app_label, self.userkey, self.accountid()) )

   accountidLink.allow_tags = True         
   accountidLink.admin_order_field = 'userkey__accountid'
   accountidLink.short_description = 'AccountID'
               
   def authoriseLink(self):
      url = "/%s/authorise/%s" % (self._meta.app_label, self.userkey)
      return mark_safe('<a href="%s"><img src="http://badc.nerc.ac.uk/graphics/misc/tick.gif"></a>' % url)
   authoriseLink.allow_tags = True
   authoriseLink.short_description = 'Authorise'
      	       
   def nerc(self):
      if self.nercfunded:
         return "Yes"
      else:
         return "No"
   nerc.admin_order_field = 'nercfunded'
	 
   def editLink(self):
      url = "/%s/request/%s" % (self._meta.app_label, self.id)
      return mark_safe('<a href="%s">Edit</a>' % url)
   editLink.allow_tags = True
   editLink.short_description = 'Edit'

   	 	 	       
   list_display = (editLink, accountidLink, authoriseLink, 'datasetid', requestdate, 'research', nerc, 'status')
   list_filter = ('status', 'nercfunded', 'requestdate', 'datasetid',)

   readonly_fields = ('id', 'userkey', 'datasetid', 'requestdate',  'fromhost', 'status')

   fields = ('id', 'userkey', 'datasetid', 'requestdate', 'research', 'nercfunded', 'fundingtype', 
                     'grantref', 'openpub', 'extrainfo', 'fromhost', 'status')
   		      
   search_fields =['research']

admin.site.register(Datasetrequest, DatasetrequestAdmin)


class PrivilegeAdmin(admin.ModelAdmin):

   
   form = PrivilegeForm


   def accountidLink(self):
      return mark_safe('<a href="/admin/%s/user/%s" title="View user details">%s</a>' % (self._meta.app_label, self.userkey, self.accountid()) )

   accountidLink.allow_tags = True         
   accountidLink.admin_order_field = 'userkey__accountid'
   accountidLink.short_description = 'AccountID'
        
   list_display = ('id', 'userkey', accountidLink, 'type', 'datasetid', 'comment')
   list_filter = ('type', 'datasetid')
   search_fields =['datasetid__datasetid', 'userkey__accountid']
   
   fields = ('userkey',  'type', 'datasetid', 'comment')

admin.site.register(Privilege, PrivilegeAdmin)


class DatasetexpirenotificationAdmin(admin.ModelAdmin):

   def has_add_permission(self, request, obj=None):
       return False
   def has_delete_permission(self, request, obj=None):
       return False
       	 
      
   list_display = ('userkey', 'datasetid', 'ver', 'date', 'emailaddress')
   list_filter = ('date', 'datasetid')
   
   readonly_fields = ('id', 'userkey', 'datasetid', 'ver', 'date', 'emailaddress', 'extrainfo')
#   fields = ('userkey', 'accountid', 'type', 'datasetid', 'comment')

admin.site.register(Datasetexpirenotification, DatasetexpirenotificationAdmin)
#
# Remove 'delete selected' option on list page
#
admin.site.disable_action('delete_selected')


