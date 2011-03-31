from django.forms import *
from cedainfo.rar.models import *
from django.contrib.admin import widgets


class AvailForm(ModelForm):
    # customise the form a bit
    class Meta:
        model = Availability
        fields = ('value',)
