from django.contrib import admin
from cedainfo.allocator.models import *
from django import forms

class BigIntegerInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('size', 80)
        super(BigIntegerInput, self).__init__(*args, **kwargs)

class PartitionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',
                    # 'exists',
		     'meter',
		     'mountpoint','host','used_bytes','capacity_bytes',
                   # 'allocated','list_allocated',
		     'links',)
    list_filter = ('status',)
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
    search_fields = ['mountpoint','host',]
admin.site.register(Partition, PartitionAdmin)

class FileSetAdmin(admin.ModelAdmin):
    list_display = ('logical_path','partition','storage_pot', 'spot_exists', 'logical_path_exists')
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
admin.site.register(FileSet,FileSetAdmin)

class FileSetSizeMeasurementAdmin(admin.ModelAdmin):
    formfield_overrides = { BigIntegerField: {'widget': BigIntegerInput} }
admin.site.register(FileSetSizeMeasurement,FileSetSizeMeasurementAdmin)

