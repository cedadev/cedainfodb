from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.conf import settings

class MountpointFilter(SimpleListFilter):
    # Human-readable title displayed in 
    # right admin sidebar just above filter options
    title = _('mount points')
    
    # Parameter for filter that will be used in the URL query
    parameter_name = 'mountpoints'
    
    def lookups(self, request, model_admin):
        '''
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        '''
        return settings.MOUNT_CHOICES
        #return (
        #    ('archvol_ro', _(u'/datacentre/archvol ro')),
        #    ('archvol_rw', _(u'/datacentre/archvol rw')),
        #)
    
    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either 'archvol_ro' or 'archvol_rw')
        # to decide how to filter the queryset.
        #return queryset.filter(self.value() in mountpoints_required)
        if self.value() is not None:
            return queryset.filter(mountpoints_required__icontains=self.value())
        else:
            return queryset