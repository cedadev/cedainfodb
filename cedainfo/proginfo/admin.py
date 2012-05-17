from cedainfo.proginfo.models import *
from django.contrib import admin

# this is the customisation of the admin interface

#-----
# This is the interface for the data products

class DataProductAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('DPT', 'proj', 'status')
    search_fields = ('DPT', 'contact')
    list_filter = ('status','proj')

    def render_change_form(self, request, context, *args, **kwargs):
        # this custom functions allows extra context info to be added to the
        # interface for rendering
        if context.has_key("object_id"):
            note_list = DataProductNote.objects.filter(data__id=context["object_id"])
        else:
            note_list = []
        extra = {
            'has_file_field': True, # Make your form render as multi-part.
            'note_list': note_list,
            'context': context
        }  
        context.update(extra)
        superclass = super(DataProductAdmin, self)
        return superclass.render_change_form(request, context, *args, **kwargs)

admin.site.register(DataProduct, DataProductAdmin)


#-----
# This is the interface for the projects

class ProjectAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('title', 'prog', 'status', 'ndata', 'dpstatus')
    search_fields = ('title', 'desc', 'PI', 'CoI1', 'CoI2')
    list_filter = ('status','prog')

    def render_change_form(self, request, context, *args, **kwargs):
        # this custom functions allows extra context info to be added to the
        # interface for rendering
        if context.has_key("object_id"):
            data_list = DataProduct.objects.filter(proj__id=context["object_id"])
	    data_list = data_list.order_by('deliverydate')
            note_list = ProjectNote.objects.filter(proj__id=context["object_id"])
        else:
            note_list = []
            data_list = []
        extra = {
            'has_file_field': True, # Make your form render as multi-part.
            'data_list': data_list,
            'note_list': note_list,
            'context': context
        }  
        context.update(extra)        
        superclass = super(ProjectAdmin, self)
        return superclass.render_change_form(request, context, *args, **kwargs)

admin.site.register(Project, ProjectAdmin)


#-----
# This is the interface for the programme

class ProgrammeAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'title', 'nprojects', 'dpstatus')
    search_fields = ('title', 'name', 'description')

    def render_change_form(self, request, context, *args, **kwargs):
        # this custom functions allows extra context info to be added to the
        # interface for rendering
        if context.has_key("object_id"):
            proj_list = Project.objects.filter(prog__id=context["object_id"])
	    proj_list = proj_list.order_by('enddate')
            note_list = ProgrammeNote.objects.filter(prog__id=context["object_id"])
            prog_list = Programme.objects.all()
        else:
            proj_list = []
            note_list = []
            prog_list = []
        extra = {
            'has_file_field': True, # Make your form render as multi-part.
            'prog_list': prog_list,
            'proj_list': proj_list,
            'note_list': note_list,
            'context': context
        }  
        context.update(extra)
        superclass = super(ProgrammeAdmin, self)
        return superclass.render_change_form(request, context, *args, **kwargs)

admin.site.register(Programme, ProgrammeAdmin)


#-----
# The note interface are added uncustomised, but they are not really needed.

admin.site.register(DataProductNote)
admin.site.register(ProjectNote)
admin.site.register(ProgrammeNote)
