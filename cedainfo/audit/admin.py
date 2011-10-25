from django.contrib import admin
from cedainfo.audit.models import *

admin.site.register(File)   
admin.site.register(FileState)
admin.site.register(Audit)
admin.site.register(FileType)