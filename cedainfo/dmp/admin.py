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

class ProjectAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('title', 'project_groups_links', 'status', 'ndata','sciSupContact',)
    search_fields = ('title', 'desc', 'PI', 'Contact1', 'Contact2')
    list_filter = ('status', 'sciSupContact')
    filter_horizontal = ('third_party_data','vms', 'groupworkspaces')

admin.site.register(Project, ProjectAdmin)


class GrantAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('number', 'title', 'project', 'gotw')
    search_fields = ('number', 'title', 'desc')
    readonly_fields=('title', 'pi', 'desc')
admin.site.register(Grant, GrantAdmin)

class ProjectGroupAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'desc')
    search_fields = ('name', 'desc')
    filter_horizontal = ('projects', )
admin.site.register(ProjectGroup, ProjectGroupAdmin)




