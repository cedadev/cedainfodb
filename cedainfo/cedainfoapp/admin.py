from django.contrib import admin
from cedainfo.cedainfoapp.models import *

admin.site.register(Partition)
admin.site.register(TopLevelDir)
admin.site.register(CurationCategory)
admin.site.register(BackupPolicy)
admin.site.register(AccessStatus)
admin.site.register(Person)
admin.site.register(DataEntitySizeMeasurement)
admin.site.register(Allocation)
admin.site.register(Service)
admin.site.register(HostHistory)
admin.site.register(DataEntityBackupLog)
admin.site.register(ServiceBackupLog)

# customise the Host admin interface
class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname','ip_addr','host_type','hypervisor','rack')
    list_filter = ('supplier','planned_end_of_life', 'retired_on','host_type','rack')
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

# customise the Rack admin interface
class RackAdmin(admin.ModelAdmin):
    list_display = ('name', 'room')
    list_filter = ('room',)
    ordering = ('name', 'room')
admin.site.register(Rack, RackAdmin)

# customise the DataEntity admin interface
class DataEntityAdmin(admin.ModelAdmin):
    list_display = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed','recipes_expression',)
    list_filter = ('curation_category','responsible_officer','last_reviewed','access_status','availability_priority','availability_failover',)
    ordering = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed')
    search_fields = ['dataentity_id','symbolic_name',]
admin.site.register(DataEntity, DataEntityAdmin)