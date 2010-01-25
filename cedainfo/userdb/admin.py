from userdb.usermanagement.models import User, Institute, Country, Role, Licence
from django.contrib import admin

admin.site.register(Institute)
admin.site.register(Country)
admin.site.register(Role)
admin.site.register(Licence)


class UserAdmin(admin.ModelAdmin):
    list_display = ('surname', 'othernames')
    search_fields = ['surname', 'othernames', 'accountid']

admin.site.register(User, UserAdmin)



