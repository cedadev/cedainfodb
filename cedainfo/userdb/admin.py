from cedainfo.userdb.models import *
from django.contrib import admin

admin.site.register(Country)

class UserAdmin(admin.ModelAdmin):
    list_display = ('lastname', 'firstname', 'username', 'email', 'startdate')
    search_fields = ['lastname', 'firstname', 'username', 'email']
    list_filter = ('field_of_study','startdate','reg_source')
admin.site.register(User, UserAdmin)


class InstituteAdmin(admin.ModelAdmin):
    list_display =  ('name', 'itype', 'country')
    search_fields = ['name', 'itype']
    list_filter = ('itype', 'country')
admin.site.register(Institute, InstituteAdmin)

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'emaillistlink')
    search_fields = ['name', 'description']
    #list_filter = ('datacentre',)
admin.site.register(Role, RoleAdmin)

class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'valid_from', 'valid_to')
    search_fields = ['name', 'description']
    #list_filter = ('valid_from', 'valid_to')
admin.site.register(Group, GroupAdmin)

class LicenceAdmin(admin.ModelAdmin):
    list_display = ('role', 'user', 'group', 'start_date', 'end_date')
    list_filter = ('role',)
admin.site.register(Licence, LicenceAdmin)

class ConditionsOfUseAdmin(admin.ModelAdmin):
    list_display = ('role', 'group', 'text')
    list_filter = ('role', 'group',)
admin.site.register(ConditionsOfUse, ConditionsOfUseAdmin)




