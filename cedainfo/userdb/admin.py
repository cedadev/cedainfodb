from cedainfo.userdb.models import User, Institute, Country, Role, Licence
from django.contrib import admin

admin.site.register(Country)


class UserAdmin(admin.ModelAdmin):
    list_display = ('surname', 'othernames', 'accountid', 'emailaddress', 'startdate')
    search_fields = ['surname', 'othernames', 'accountid', 'emailaddress']
    list_filter = ('accounttype',)
admin.site.register(User, UserAdmin)


class InstituteAdmin(admin.ModelAdmin):
    list_display =  ('name', 'itype', 'country')
    search_fields = ['name', 'itype']
    list_filter = ('itype', 'country')
admin.site.register(Institute, InstituteAdmin)

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'authtype', 'description')
    search_fields = ['name', 'description']
    list_filter = ('datacentre',)
admin.site.register(Role, RoleAdmin)

class LicenceAdmin(admin.ModelAdmin):
    list_display = ('role', 'user', 'ver', 'removed')
    list_filter = ('role',)
admin.site.register(Licence, LicenceAdmin)




