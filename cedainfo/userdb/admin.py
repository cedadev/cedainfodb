from cedainfo.userdb.models import User, Institute, Country, Role, Licence
from django.contrib import admin

admin.site.register(Country)
admin.site.register(Role)
admin.site.register(Licence)


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

