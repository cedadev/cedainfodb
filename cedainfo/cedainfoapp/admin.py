from django.contrib import admin
from cedainfo.cedainfoapp.models import *

admin.site.register(Partition)
admin.site.register(TopLevelDir)
admin.site.register(CurationCategory)
admin.site.register(BackupPolicy)
admin.site.register(AccessStatus)
admin.site.register(Role)
admin.site.register(Person)
admin.site.register(DataEntityContact)
admin.site.register(DataEntitySizeMeasurement)
admin.site.register(Rack)
admin.site.register(Allocation)
admin.site.register(Service)
admin.site.register(ServiceContact)
admin.site.register(HostHistory)
admin.site.register(DataEntityBackupLog)
admin.site.register(ServiceBackupLog)

# customise the Host admin interface
class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname','ip_addr')
    list_filter = ('supplier','planned_end_of_life', 'retired_on','host_type')
    ordering = ('hostname','planned_end_of_life',)
admin.site.register(Host, HostAdmin)

# customise the DataEntity admin interface
class DataEntityAdmin(admin.ModelAdmin):
    list_display = ('dataentity_id','symbolic_name','logical_path','curation_category','access_status',)
    list_filter = ('curation_category','access_status','availability_priority','availability_failover')
    ordering = ('dataentity_id','symbolic_name','logical_path','curation_category','access_status',)
admin.site.register(DataEntity, DataEntityAdmin)