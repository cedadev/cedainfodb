from cedainfo.rar.models import *
from django.contrib import admin


class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'fedid', )
#    search_fields = ['lastname', 'firstname', 'username', 'email']
#    list_filter = ('field','startdate','reg_source')
admin.site.register(Person, PersonAdmin)

class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('person', 'month', 'value' )
#    search_fields = ['lastname', 'firstname', 'username', 'email']
    list_filter = ('person', 'month')
admin.site.register(Availability, AvailabilityAdmin)





