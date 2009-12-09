from django.contrib import admin
from cedainfo.cedainfoapp.models import *

admin.site.register(Partition)
admin.site.register(TopLevelDir)
admin.site.register(CurationCategory)
admin.site.register(BackupPolicy)
admin.site.register(AccessStatus)
admin.site.register(Role)
admin.site.register(Person)
admin.site.register(DataEntityAdministrator)
admin.site.register(Rack)
admin.site.register(Allocation)
admin.site.register(HostService)
admin.site.register(HostHistory)
admin.site.register(DataEntityBackupLog)
admin.site.register(ServiceBackupLog)
admin.site.register(HostTag)

# customise the Slot admin interface
class SlotAdmin(admin.ModelAdmin):
    list_display = ('parent_rack', 'position', 'occupant')
    list_filter = ('parent_rack', 'occupant')
    ordering = ('parent_rack', 'position',)
    search_fields = ('parent_rack', 'occupant',)
admin.site.register(Slot, SlotAdmin)

# customise the Host admin interface
class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname','ip_addr')
    list_filter = ('supplier','planned_end_of_life', 'retired','tags')
    ordering = ('hostname','planned_end_of_life',)
admin.site.register(Host, HostAdmin)

# customise the DataEntity admin interface
class DataEntityAdmin(admin.ModelAdmin):
    list_display = ('dataentity_id','symbolic_name','logical_path','curation_category','access_status',)
    list_filter = ('curation_category','access_status','availability_priority','availability_failover')
    ordering = ('dataentity_id','symbolic_name','logical_path','curation_category','access_status',)
admin.site.register(DataEntity, DataEntityAdmin)