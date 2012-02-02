from django.contrib import admin
from cedainfo.udbadmin.models import *
from django.utils.safestring import mark_safe


from django.contrib.auth.models import User as SiteUser
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
admin.site.unregister(SiteUser)
admin.site.unregister(Group)



class DatasetjoinAdmin(admin.ModelAdmin):

   def has_add_permission(self, request, obj=None):
       return False
   def has_delete_permission(self, request, obj=None):
       return False

   list_display = ('userkey', 'datasetid', 'ver', 'research')
   list_filter = ('datasetid',)
   readonly_fields = ('datasetid', 'userkey')
   search_fields =['research']


admin.site.register(Datasetjoin, DatasetjoinAdmin)

class DatasetAdmin(admin.ModelAdmin):
   list_display = ('datasetid', 'authtype', 'grp', 'description', 'datacentre')
   list_filter = ('datacentre', 'authtype')
   exclude = ('grouptype', 'source')

   search_fields =['datasetid']
   
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
       
       a = '<a href="http://team.ceda.ac.uk/cgi-bin/userdb/edit_user_details.cgi.pl?userkey=%s">Team editor</a>|' % self.userkey
       a += ' <a href="/%s/user/datasets/current/%s">Current datasets (%s)</a>|' % (self._meta.app_label, self.userkey, currentDatasets)
       a += ' <a href="/%s/user/datasets/removed/%s">Removed datasets (%s)</a>|' % (self._meta.app_label, self.userkey, removedDatasets)
       return mark_safe(a)
       
    links.short_description = 'Related pages'

    def showDatasets (self):
         
	 datasets = self.datasets(removed=False)
	 datasets = datasets.order_by("datasetid")

         a = 'Details: '
         a += ' <a href="/%s/user/datasets/current/%s">Current datasets</a> |' % (self._meta.app_label, self.userkey)
         a += ' <a href="/%s/user/datasets/removed/%s">Removed datasets</a>' % (self._meta.app_label, self.userkey)
         a += '<p>'
	 
	 for dataset in datasets:
            a +=  str(dataset.datasetid) + '<br>'
	 
	 return mark_safe(a)
	 
    showDatasets.short_description = 'Datasets'
    	 
    list_display = ('userkey', 'title', 'othernames', 'surname', 'accountid', 'emailaddress', 'startdate', 'field')
    list_filter = ('title', 'degree', 'field','startdate','datacenter')
    search_fields = ['surname', 'othernames', 'accountid', 'emailaddress']
    list_per_page = 200
    
#    exclude = ('encpasswd', 'md5passwd', 'onlinereg')
    readonly_fields = (showDatasets, 'datacenter', 'userkey', 'address', 'accountid', 'addresskey', 'startdate', 'openid', 'encpasswd', 'md5passwd', 'institute', links)

    fields = (links, 'userkey', 'title', 'surname', 'othernames', 'emailaddress',
               'webpage', 'telephoneno', 'accountid', 'openid', 'accounttype', 
	       'degree', 'endorsedby', 'field', 'startdate', showDatasets, 'datacenter', 'institute', 'address', 'comments')
#    list_editable = ('accountid','title')


 

admin.site.register(User, UserAdmin)
#admin.site.register(Tbinstitutes)


#
# Remove 'delete selected' option on list page
#
admin.site.disable_action('delete_selected')


