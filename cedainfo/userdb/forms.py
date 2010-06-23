from django.forms import *
from cedainfo.userdb.models import *
from django.contrib.admin import widgets


class UserForm(ModelForm):
    # customise the form a bit
#    dataentity_id = CharField(widget=forms.TextInput(attrs={'size':'60'}))
#    friendly_name = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False)
#    symbolic_name = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False)
#    backup_destination = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False)
#    notes = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}), required=False)
#    recipes_expression = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False)
#    recipes_explanation = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}), required=False)
    class Meta:
        model = User
    
class UserStatsForm(Form):
    # customise the form a bit
    Role = ModelChoiceField(queryset= Role.objects.all().order_by('name'))


