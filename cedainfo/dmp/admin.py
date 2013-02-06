from cedainfo.dmp.models import *
from django.contrib.auth.models import *
from django.contrib import admin

# this is the customisation of the admin interface

#-----
# This is the interface for the data products

class DataProductAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('title', 'status','sciSupContact',)
    search_fields = ('title', 'contact')
    list_filter = ('sciSupContact','status',)


admin.site.register(DataProduct, DataProductAdmin)


#-----
# This is the interface for the projects

class DMPAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('title', 'dmp_groups', 'status', 'ndata','sciSupContact',)
    search_fields = ('title', 'desc', 'PI', 'CoI1', 'CoI2')
    list_filter = ('status', 'sciSupContact')
    filter_horizontal = ('data_outputs', 'third_party_data')

admin.site.register(DMP, DMPAdmin)


class GrantAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('number', 'title', 'dmp', 'gotw')
    search_fields = ('number', 'title', 'desc')
admin.site.register(Grant, GrantAdmin)

class DMPGroupAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'desc')
    search_fields = ('name', 'desc')
    filter_horizontal = ('dmps',)
admin.site.register(DMPGroup, DMPGroupAdmin)




