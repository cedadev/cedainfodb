from django.contrib import admin
#from django.contrib.gis import admin
from models import *
from filters import MountpointFilter 
from django import forms


def prettySize(size):
   '''Returns file size in human readable format'''
   
   suffixes = [("B",2**10), ("K",2**20), ("M",2**30), ("G",2**40), ("T",2**50)]
   for suf, lim in suffixes:
      if size > lim:
         continue
      else:
         return round(size/float(lim/2**10),2).__str__()+suf


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
    list_display = ('hostname','ip_addr', 'serial_no', 'arrival_date', 'host_type','hypervisor','rack')
    list_filter = ('supplier','planned_end_of_life', 'retired_on','host_type','rack','hostlist')
    ordering = ('hostname','planned_end_of_life')
    search_fields = ['hostname', 'notes', 'serial_no']

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
   pass
#    host = forms.ModelChoiceField(Host.objects.all().order_by('hostname'))
#    lemons = forms.CharField(max_length=80, label='snow')
#   documentationLink = forms.CharField(max_length=80, label='snow 2')
    
#    class Meta:
#        model = Service

class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = ('name', 'summary', 'host', 'active')
#    list_editable=('active',)
    list_filter = ('externally_visible', 'active', 'host')
    search_fields = ('description', 'name')
    ordering = ('-active', 'name')
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

class AuditAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',
		     'auditstate','fileset','corrupted_files', 'new_files', 
		     'deleted_files', 'modified_files', 'unchanges_files')
    actions=['delete']
    list_filter = ('auditstate',)  
    readonly_fields = ('auditstate','corrupted_files', 'new_files', 
		     'deleted_files', 'modified_files', 'unchanges_files', 'starttime', 'endtime', 'logfile')
admin.site.register(Audit, AuditAdmin)

class FileSetAdminForm(forms.ModelForm):

#    overall_final_size = ByteSizeField()
    overall_final_size = forms.CharField(widget=forms.TextInput(attrs={'size': '25'})) 
#
#      This is a copy of the help text in the models.py file. Must be a better way of doing this...
#    
    overall_final_size.help_text = "The allocation given to a fileset is an estimate of the final size on disk. If the dataset is going to grow indefinitely then estimate the size for 4 years ahead. Filesets can't be bigger than a single partition, but in order to aid disk managment they should not exceed 20% of the size of a partition."

    def clean_logical_path(self):
#
#              Make sure logical path does not have a '/' at the end as this causes problems later
#    
        data = self.cleaned_data['logical_path']
	data = data.strip()
	data = data.rstrip('/')
	
	return data
    
    class Meta:
        model = FileSet
	
	    
class FileSetAdmin(admin.ModelAdmin):
    form = FileSetAdminForm
    
    
    def niceOverallFinalSize(self):
       return prettySize(self.overall_final_size)

    niceOverallFinalSize.admin_order_field = 'overall_final_size'
    niceOverallFinalSize.short_description = 'Overall final size'     
     
    list_display = ('logical_path', niceOverallFinalSize, 
        'partition', 'partition_display',
        'spot_display',
#	'status',
	'last_size','responsible',
	'links',)
    list_filter = ('partition','sd_backup')
    
    ordering = ('-id',)
    readonly_fields = ('partition',
#        'migrate_to', 
        'storage_pot', 'complete', 'complete_date', niceOverallFinalSize)
	
    fields = (
    'logical_path', 
    'overall_final_size',
    niceOverallFinalSize,
    'notes',
    'partition',
    'storage_pot_type',
    'storage_pot',
    'migrate_to',
    'secondary_partition',
    'dmf_backup',
    'sd_backup',
    'complete',
    'complete_date',  
    )	
    
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



#class SpatioTempAdmin(admin.OSMGeoAdmin):
#    pass
#admin.site.register(SpatioTemp, SpatioTempAdmin)


class GWSRequestAdmin(admin.ModelAdmin):
    list_display = ('gws_name', 'action_links','internal_requester', 'gws_manager', 'requested_volume', 'backup_requirement', 'expiry_date', 'request_type', 'request_status', 'gws_link',  'timestamp')
    #list_filter = ('request_status',)
    #readonly_fields = ('request_status',)
    ordering = ('timestamp',)
    search_fields = ('gws_name', 'path')
admin.site.register(GWSRequest, GWSRequestAdmin)

class GWSAdmin(admin.ModelAdmin):
    list_display = ('name', 'internal_requester', 'gws_manager', 'requested_volume', 'backup_requirement', 'expiry_date', 'last_reviewed', 'status','volume',)
    #list_filter = ('status',)
    search_fields = ('name', 'path')
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(GWS, GWSAdmin)

class VMRequestAdmin(admin.ModelAdmin):
    list_display=('vm_name', 'action_links', 'type', 'operation_type', 'internal_requester', 'date_required','timestamp', 'request_type', 'request_status','vm_link',)
    list_filter=('type', 'operation_type', 'request_status', MountpointFilter,)
    search_fields = ('vm_name',)
    #readonly_fields = ('request_status',)
admin.site.register(VMRequest, VMRequestAdmin)

class VMAdmin(admin.ModelAdmin):
    list_display=('name', 'type', 'operation_type', 'internal_requester', 'timestamp', 'status', )
    list_filter=('type', 'operation_type', 'status', MountpointFilter,)
    search_fields = ('name',)
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(VM, VMAdmin)
