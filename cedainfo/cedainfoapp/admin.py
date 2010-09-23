from django.contrib import admin
from cedainfo.cedainfoapp.models import *
from django import forms

class BigIntegerInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('size', 80)
        super(BigIntegerInput, self).__init__(*args, **kwargs)

admin.site.register(CurationCategory)
admin.site.register(BackupPolicy)
admin.site.register(AccessStatus)
admin.site.register(Person)
#admin.site.register(Service)
admin.site.register(HostHistory)
admin.site.register(FileSetCollectionRelation)
admin.site.register(PartitionPool)
admin.site.register(FileSetBackupLog)
admin.site.register(ServiceBackupLog)
admin.site.register(FileSetAllocationPlan)

# customise the Host admin interface
class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname','ip_addr','host_type','hypervisor','rack')
    list_filter = ('supplier','planned_end_of_life', 'retired_on','host_type','rack','hostlist')
    ordering = ('hostname','planned_end_of_life')
    search_fields = ['hostname',]

    # for the "hypervisor" field, restrict the list of available hosts to those with host_type="hypervisor_server"
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "hypervisor":
	    #kwargs["queryset"] =#Host.objects.filter(host_type="hypervisor_server").order_by('hypervisor') # seems to have no effect
	    kwargs["queryset"] = Host.objects.filter(host_type="hypervisor_server")
	    return db_field.formfield(**kwargs)
	return super(HostAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
admin.site.register(Host, HostAdmin)

# For the service admin we need a form with hosts listed in alphabetical order.
# Create a custom form, then use it in the ServiceAdmin class
class ServiceAdminForm(forms.ModelForm):
    host = forms.ModelMultipleChoiceField(Host.objects.all().order_by('hostname'))
    dependencies = forms.ModelMultipleChoiceField(Service.objects.all().order_by('name'))
    class Meta:
        model = Host

class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
admin.site.register(Service, ServiceAdmin)

# customise the Rack admin interface
class RackAdmin(admin.ModelAdmin):
    list_display = ('name', 'room', 'racklist')
    list_filter = ('room','racklist')
    ordering = ('name', 'room')
admin.site.register(Rack, RackAdmin)

# customise the DataEntity admin interface
class DataEntityAdmin(admin.ModelAdmin):
    list_display = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed','recipes_expression',)
    list_filter = ('curation_category','responsible_officer','last_reviewed','access_status','availability_priority','availability_failover',)
    ordering = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed')
    search_fields = ['dataentity_id','symbolic_name',]
admin.site.register(DataEntity, DataEntityAdmin)

class PartitionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__','mountpoint','expansion_no','host','partition_pool','used_bytes','capacity_bytes',)
    list_filter = ('partition_pool','expansion_no')
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
    search_fields = ['mountpoint','host',]
admin.site.register(Partition, PartitionAdmin)

# Create an inline form to manage FileSetCollection memberships (to be used in FileSetCollection & FileSet Admins)
class FileSetCollectionRelationInline(admin.TabularInline):
    model = FileSetCollectionRelation
    extra = 1

class FileSetCollectionAdmin(admin.ModelAdmin):
    #inlines = (FileSetCollectionRelationInline,) # probably too many filesets for this to work well
    list_display = ('logical_path', 'partitionpool',)
    list_filter = ('partitionpool',)
admin.site.register(FileSetCollection,FileSetCollectionAdmin)

class FileSetAdmin(admin.ModelAdmin):
    list_display = ('label','partition',)
    inlines = (FileSetCollectionRelationInline,)
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
admin.site.register(FileSet,FileSetAdmin)

class FileSetSizeMeasurementAdmin(admin.ModelAdmin):
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
admin.site.register(FileSetSizeMeasurement,FileSetSizeMeasurementAdmin)

#class NodeListTagAdmin(admin.ModelAdmin):
#    list_display=('name',)
#    list_filter=('tag',)
#admin.site.register(NodeListTag, NodeListTagAdmin)
admin.site.register(NodeList)
admin.site.register(HostList)
admin.site.register(RackList)    