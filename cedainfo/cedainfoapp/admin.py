from django.contrib import admin
from django.contrib.admin import SimpleListFilter
# from django.contrib.gis import admin
from .models import *
from .filters import MountpointFilter

from django.utils.safestring import mark_safe

from .forms import *

from django import forms
from django.db import models


def prettySize(size):
    '''Returns file size in human readable format'''

    suffixes = [("B", 1), ("K", 1000), ("M", 1000000), ("G", 1000000000), ("T", 1000000000000)]
    level_up_factor = 2000.0
    for suf, multipler in suffixes:
        if float(size) / multipler > level_up_factor:
            continue
        else:
            return round(size / float(multipler), 2).__str__() + suf
    return round(size / float(multipler), 2).__str__() + suf


class BigIntegerInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('size', 80)
        super(BigIntegerInput, self).__init__(*args, **kwargs)


BYTE_UNIT_SUFFIXES = {
    'b': 1,  # byte
    'kb': 1024,  # kilobyte
    'Mb': 1024 * 1024,  # megabyte
    'Gb': 1024 * 1024 * 1024,  # gigabyte
    'Tb': 1024 * 1024 * 1024 * 1024,  # terabyte
    'Pb': 1024 * 1024 * 1024 * 1024,  # petabyte
    'Eb': 1024 * 1024 * 1024 * 1024 * 1024,  # exabyte
}


class ByteSizeField(forms.CharField):
    def clean(self, value):
        try:
            # If it's a number followed by a suffix e.g. "4.23 Mb", split it & look at the suffix to determine the factor.
            if len(value.split()) > 1:
                (size, suffix) = value.split()
                # Find the matching suffix and multiply value by corresponding factor
                value = int(float(size) * BYTE_UNIT_SUFFIXES[suffix])
                return value
            else:
                return int(value)
        except:
            raise ValidationError(
                "Enter a value either as an integer number of bytes, or as a number followed by the suffix 'b', 'Mb', 'Gb', 'Tb', 'Pb, 'Eb'")


# don't need to edit curation cat
# admin.site.register(CurationCategory)

# don't need to change in admin interface
# admin.site.register(AccessStatus)

class PersonAdmin(admin.ModelAdmin):
    ordering = ('name',)
    list_display = ('name', 'username', 'email')


admin.site.register(Person, PersonAdmin)

# admin.site.register(HostHistory)
# admin.site.register(FileSetSizeMeasurement)
# admin.site.register(ServiceBackupLog)

# customise the Host admin interface

admin.site.register(ServiceKeyword)


class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ip_addr', 'serial_no', 'arrival_date', 'host_type', 'hypervisor', 'rack')
    list_filter = ('supplier', 'planned_end_of_life', 'retired_on', 'host_type', 'rack',)
    ordering = ('hostname', 'planned_end_of_life')
    search_fields = ['hostname', 'notes', 'serial_no']

    # for the "hypervisor" field, restrict the list of available hosts to those with host_type="hypervisor_server"
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "hypervisor":
            # kwargs["queryset"] =#Host.objects.filter(host_type="hypervisor_server").order_by('hypervisor') # seems to have no effect
            kwargs["queryset"] = Host.objects.filter(host_type="hypervisor_server")
            return db_field.formfield(**kwargs)
        return super(HostAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Host, HostAdmin)


# For the service admin we need a form with hosts listed in alphabetical order.
# Create a custom form, then use it in the ServiceAdmin class
class ServiceAdminForm(forms.ModelForm):
    pass


# host = forms.ModelChoiceField(Host.objects.all().order_by('hostname'))
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
    filter_horizontal = ('dependencies',)
##admin.site.register(Service, ServiceAdmin)


class ServiceHostFilter(SimpleListFilter):
    title = 'Host'
    parameter_name = 'Host'

    def lookups(self, request, model_admin):
        hosts = set([c.host for c in model_admin.model.objects.all()])
        hosts = list(hosts)
        hosts.sort(key=lambda x: x.name)
        return [(c.id, c.name) for c in hosts]

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(host__id__exact=self.value())
        else:
            return queryset


class ManagerFilter(SimpleListFilter):
    title = 'Manager'
    parameter_name = 'manager'

    def lookups(self, request, model_admin):
        users = set([c.service_manager for c in model_admin.model.objects.all()])
        if None in users: users.remove(None)
        #
        #       Sort results
        #
        users = list(users)
        users.sort(key=lambda x: x.username)

        count = {}
        for u in users:
            count[u.username] = len(model_admin.model.objects.filter(service_manager__username=u.username))

        return [(c.id, c.username + ' (%s)' % count[c.username]) for c in users]

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(service_manager__id__exact=self.value())
        else:
            return queryset


class OwnerFilter(SimpleListFilter):
    title = 'Owner'
    parameter_name = 'owner'

    def lookups(self, request, model_admin):
        users = set([c.owner for c in model_admin.model.objects.all()])
        if None in users: users.remove(None)
        #
        #       Sort results
        #
        users = list(users)
        users.sort(key=lambda x: x.username)

        count = {}
        for u in users:
            count[u.username] = len(model_admin.model.objects.filter(owner__username=u.username))

        return [(c.id, c.username + ' (%s)' % count[c.username]) for c in users]

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(owner__id__exact=self.value())
        else:
            return queryset


class SystemManagerFilter(SimpleListFilter):
    title = 'System Manager'
    parameter_name = 'sysadmin'

    def lookups(self, request, model_admin):
        users = set([c.host.patch_responsible for c in model_admin.model.objects.all()])
        if None in users: users.remove(None)
        #
        #       Sort results
        #
        users = list(users)
        users.sort(key=lambda x: x.username)

        count = {}
        for u in users:
            count[u.username] = len(model_admin.model.objects.filter(host__patch_responsible__username=u.username))

        return [(c.id, c.username + ' (%s)' % count[c.username]) for c in users]

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(host__patch_responsible__id__exact=self.value())
        else:
            return queryset


class VMStatusFilter(SimpleListFilter):
    title = 'VM status'
    parameter_name = 'vmstatus'

    def lookups(self, request, model_admin):
        vms = set([c.host.status for c in model_admin.model.objects.all()])
        if None in vms: vms.remove(None)
        #
        #       Sort results
        #
        vms = list(vms)
        vms.sort()

        count = {}
        for u in vms:
            count[u] = len(model_admin.model.objects.filter(host__status=u))

        return [(c, c + ' (%s)' % count[c]) for c in vms]

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(host__status__exact=self.value())
        else:
            return queryset

class NewServiceAdmin(admin.ModelAdmin):
    #    def wikiLink(self):
    #        url = self.documentation
    #
    #    if url:
    #            return mark_safe('<a href="%s">Wiki</a>' % (url))
    #        else:
    #        return ''
    #
    #    wikiLink.allow_tags = True
    #    wikiLink.short_description = 'Wiki'

    def availability(self):
        tolerance = self.availability_tolerance
        return tolerance

    def system_manager(self):
        if self.host.name.startswith('legacy:'):
            return ''
        else:
            return self.host.patch_responsible

    system_manager.admin_order_field = "host__patch_responsible__username"
    
    def docs(self):
        if self.documentation:
            return mark_safe('<a href="%s" title="View Helpscout documentation">Helpscout</a>' % (self.documentation))
        else:
            return ''
    docs.allow_tags = True
    docs.admin_order_field = "documentation"

    def vm_name (self):
    
        if self.host.status == 'deprecated':
            color = 'DarkViolet'
        elif self.host.status == 'retired':
            color = 'red'    
        else:
            color = 'none'
        
        return '<a href="/admin/cedainfoapp/vm/%s/" title="Status: %s"><span style="color: %s;">%s</span></a>' % (self.host.id, self.host.status, color, self.host.name)
    vm_name.allow_tags = True
    vm_name.admin_order_field = "host__name"
    
    
    def vm_os (self):

        return self.host.os_required
        
        
    vm_os.admin_order_field = "host__os_required"
    vm_os. short_description = "OS"
    
    list_display = ('name', docs, vm_name, vm_os, 'review_status', 'last_reviewed', 'visibility', 'status', 'priority', 'summary', 'service_manager', 'owner')
    list_editable = ('priority',)
    list_filter = ('visibility', 'priority', 'status', 'review_status', 'keywords', ManagerFilter, OwnerFilter, ServiceHostFilter, SystemManagerFilter, VMStatusFilter)
    search_fields = ('description', 'name', 'host__name')
    ordering = ('name',)

    filter_horizontal = ('keywords',)

    formfield_overrides = {
        models.URLField: {'widget': TextInput(attrs={'size': '120'})},
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
    }


admin.site.register(NewService, NewServiceAdmin)


# customise the Rack admin interface
# class RackAdmin(admin.ModelAdmin):
#    list_display = ('name', 'room')
#    list_filter = ('room',)
#    ordering = ('name', 'room')
# admin.site.register(Rack, RackAdmin)

# customise the DataEntity admin interface
# class DataEntityAdmin(admin.ModelAdmin):
#    list_display = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed','recipes_expression',)
#    list_filter = ('friendly_name', 'curation_category','responsible_officer','last_reviewed','access_status','availability_priority','availability_failover',)
#    ordering = ('dataentity_id','symbolic_name','responsible_officer','last_reviewed')
#    search_fields = ['dataentity_id','symbolic_name',]
#
#    formfield_overrides = {
#           models.CharField: {'widget': TextInput(attrs={'size':'80'})},
#        }

# admin.site.register(DataEntity, DataEntityAdmin)

class PartitionAdminForm(forms.ModelForm):
    used_bytes = ByteSizeField()
    capacity_bytes = ByteSizeField()

    class Meta:
        model = Partition
        exclude = ('',)

class PartitionAdmin(admin.ModelAdmin):
    form = PartitionAdminForm
    list_display = ('__unicode__',
                    # 'exists', 
                    # 'meter',
                    'text_meter',
                    #'mountpoint',
                    'status',
                    # 'list_allocated',
                    #'links',
                    )
    list_filter = ('status',)


formfield_overrides = {ByteSizeField: {'widget': BigIntegerInput}}
search_fields = ['mountpoint']
actions = ['update_df']
list_editable = ['status']


def update_df(self, request, queryset):
    for i in queryset.all():
        i.df()


update_df.short_description = "Do a df on selected partitions"
##admin.site.register(Partition, PartitionAdmin)


# class SpatioTempAdmin(admin.OSMGeoAdmin):
#    pass
# admin.site.register(SpatioTemp, SpatioTempAdmin)

class TenancyAdmin(admin.ModelAdmin):
    list_display = ('name', 'summary')
    
admin.site.register(Tenancy, TenancyAdmin)


class GWSRequestAdmin(admin.ModelAdmin):
    list_display = (
    'gws_name', 'action_links', 'internal_requester', 'gws_manager', 'volume_filesize', 'et_quota_filesize',
    'backup_requirement', 'expiry_date', 'request_type', 'request_status', 'gws_link', 'timestamp')
    list_filter = ('request_status',)
    # readonly_fields = ('request_status',)
    ordering = ('timestamp',)
    search_fields = ('gws_name', 'path')


admin.site.register(GWSRequest, GWSRequestAdmin)


class GWSAdmin(admin.ModelAdmin):
    list_display = (
    'name', 'path', 'requested_volume_filesize', 'used_volume_filesize', 'et_quota_filesize', 'et_used_filesize',
    'action_links', 'last_size')
    list_filter = ('status', 'path',)
    search_fields = ('name', 'path')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(GWS, GWSAdmin)


class VMRequestAdmin(admin.ModelAdmin):
    list_display = (
    'coloured_vm_name', 'action_links', 'type', 'operation_type', 'internal_requester', 'patch_responsible',
    'date_required', 'timestamp', 'request_type', 'request_status', 'vm_link',)
    list_filter = ('type', 'operation_type', 'request_status', 'patch_responsible', MountpointFilter)
    search_fields = ('vm_name',)

    # readonly_fields = ('request_status',)
    # order vm dropdown by name

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "internal_requester":
            kwargs["queryset"] = User.objects.order_by('username')

        return super(VMRequestAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(VMRequest, VMRequestAdmin)


class VMAdmin(admin.ModelAdmin):

    def os (self):
        return self.os_required
    os. short_description = "OS"
    os.admin_order_field = "os_required"

    
    
    list_display = (
    'coloured_vm_name', 'type', 'operation_type', 'internal_requester', 'patch_responsible',
    'timestamp', 'status', 'end_of_life',  os, 'ping_last_ok')
    list_filter = ('type', 'operation_type', 'status', 'patch_responsible', MountpointFilter, 'os_required')
    search_fields = ('name',)
    

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "internal_requester":
            kwargs["queryset"] = User.objects.order_by('username')

        return super(VMAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(VM, VMAdmin)
