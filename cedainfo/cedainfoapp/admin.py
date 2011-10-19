from django.contrib import admin
#from django.contrib.gis import admin
from cedainfo.cedainfoapp.models import *
from django import forms

class BigIntegerInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('size', 80)
        super(BigIntegerInput, self).__init__(*args, **kwargs)

BYTE_UNIT_SUFFIXES = {
    'b':   1,                          # byte
    'kb':   1024,                       # kilobyte
    'Mb':   1024*1024,                  # megabyte
    'Gb':   1024*1024*1024,             # gigabyte
    'Tb':   1024*1024*1024*1024,        # terabyte
    'Pb':   1024*1024*1024*1024,        # petabyte
    'Eb':   1024*1024*1024*1024*1024,   # exabyte
}

class ByteSizeField(forms.CharField):

    def clean(self, value):
        try:
            # If it's a number followed by a suffix e.g. "4.23 Mb", split it & look at the suffix to determine the factor.
            if len(value.split()) > 1:
                (size, suffix) = value.split()
                # Find the matching suffix and multiply value by corresponding factor
                value = int( float(size) * BYTE_UNIT_SUFFIXES[suffix] )
                return value
            else:
                return int(value)
        except:
            raise ValidationError(u"Enter a value either as an integer number of bytes, or as a number followed by the suffix 'b', 'Mb', 'Gb', 'Tb', 'Pb, 'Eb'")

        
        
# don't need to edit curation cat
#admin.site.register(CurationCategory)

# don't need to change in admin interface
admin.site.register(AccessStatus)

class PersonAdmin(admin.ModelAdmin):
   ordering = ('name',)
   list_display = ('name', 'username', 'email')
   
admin.site.register(Person, PersonAdmin)

admin.site.register(HostHistory)
admin.site.register(ServiceBackupLog)

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
    host = forms.ModelChoiceField(Host.objects.all().order_by('hostname'))
    class Meta:
        model = Host

class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = ('name', 'host', 'active')
    list_filter = ('host', 'active')
    search_fields = ('description', 'name')
    ordering = ('name',)
    filter_horizontal= ('dependencies',)    
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
    list_filter = ('friendly_name', 'curation_category','responsible_officer','last_reviewed','access_status','availability_priority','availability_failover',)
    ordering = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed')
    search_fields = ['dataentity_id','symbolic_name',]
admin.site.register(DataEntity, DataEntityAdmin)

class PartitionAdminForm(forms.ModelForm):
    used_bytes = ByteSizeField()
    capacity_bytes = ByteSizeField()    
    class Meta:
        model = Partition

class PartitionAdmin(admin.ModelAdmin):
    form = PartitionAdminForm
    list_display = ('__unicode__',
                    # 'exists', 
		     'meter',
		     'mountpoint','host','status','list_allocated',
		     'links',)
    list_filter = ('status',)
    formfield_overrides = { ByteSizeField: {'widget': BigIntegerInput} }
    search_fields = ['mountpoint']
    actions=['update_df']
    list_editable=['status']
    
    def update_df(self, request, queryset):
        for i in queryset.all():
            i.df()
    update_df.short_description = "Do a df on selected partitions"
admin.site.register(Partition, PartitionAdmin)

class FileSetAdminForm(forms.ModelForm):
    overall_final_size = ByteSizeField()    
    class Meta:
        model = FileSet

class FileSetAdmin(admin.ModelAdmin):
    
    list_display = ('logical_path','overall_final_size','partition', 'partition_display',
        'spot_display','status','last_size','responsible','links',)
    list_filter = ('partition',)
    readonly_fields = ('partition',
#        'migrate_to', 
        'storage_pot', )
    # TODO : add size history graph
    formfield_overrides = { ByteSizeField: {'widget': BigIntegerInput} }
    search_fields = ['logical_path', 'notes']
    actions=['bulk_allocate','bulk_du',]
    
    def bulk_allocate(self, request, queryset):
        for fs in queryset.all():
            fs.allocate()
    bulk_allocate.short_description = "Allocate partitions"
    
    def bulk_du(self, request, queryset):
        for fs in queryset.all():
            fs.du()
    bulk_du.short_description = "Measure size of selected FileSet(s)"

    # extra context for admin view TODO!!!!
    def change_view(self, request, object_id, extra_context=None):
    
        fssms = FileSetSizeMeasurement.objects.filter(fileset=object_id)
	#.objects.filter(fileset=self).order_by('date')
	#fssms = fssms.get()
#	for in
#        size_values = fssms.values_list('size', flat=True)
#        date_values = fssms.values_list('date', flat=True)    
        my_context = {'xx': 'MyContect', 'fssms':fssms}
        return super(FileSetAdmin, self).change_view(request, object_id,
            extra_context=my_context)

admin.site.register(FileSet,FileSetAdmin)

#class FileSetSizeMeasurementAdmin(admin.ModelAdmin):
#    formfield_overrides = { ByteSizeField: {'widget': BigIntegerInput} }
#    list_display = ('fileset','date', 'size')
#    list_filter = ('fileset',)
#admin.site.register(FileSetSizeMeasurement,FileSetSizeMeasurementAdmin)

admin.site.register(NodeList)
admin.site.register(HostList)
admin.site.register(RackList) 

admin.site.register(File)   
admin.site.register(FileState)
admin.site.register(Audit)
admin.site.register(AuditState)
admin.site.register(FileSetStatus)
admin.site.register(FileType)

#class SpatioTempAdmin(admin.OSMGeoAdmin):
#    pass
#admin.site.register(SpatioTemp, SpatioTempAdmin)