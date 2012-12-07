from django.forms import *
from models import *
from django.contrib.admin import widgets
import choices

class UdjForm(forms.Form):
   fundingtype = ChoiceField(choices=choices.FUNDING_TYPES)
   nercfunded  = ChoiceField(choices=choices.NERC_FUNDED)
   openpub     = ChoiceField(choices=choices.OPEN_PUBLICATION)
   removed     = ChoiceField(choices=((0, "No"), (-1, "Yes")))

class DatasetRequestForm(forms.Form):
   fundingtype = ChoiceField(choices=choices.FUNDING_TYPES)
   nercfunded  = ChoiceField(choices=choices.NERC_FUNDED)
   openpub     = ChoiceField(choices=choices.OPEN_PUBLICATION)

class DatasetForm(ModelForm):
    # customise the form a bit
    comments = CharField(required=False, widget=forms.Textarea(attrs={'rows':'4', 'cols': '50'}))
    defaultreglength = CharField(initial=36, required=False, label='Default Registration length (months)', max_length=4, widget=forms.TextInput(attrs={'size': '4'}))
    conditions = CharField(required=False, widget=forms.TextInput(attrs={'size': '80'}))
    directory = CharField(required=False)  
    gid = IntegerField(initial=0, required=False, label='Associated Linux group ID (0 if not used)', max_value=90000, min_value=0)
#
#      Make sure we can cope with a blank gid
#     
    def clean_gid(self):
        if not self.cleaned_data["gid"]:
            return 0
        else:
            return self.cleaned_data["gid"]             
        
    class Meta:
        model = Dataset
#	fields = ('datasetid', 'authtype', 'grp', 'description', 'directory', 'conditions', 'defaultreglength', 'datacentre', 'infourl', 'comments')

class PrivilegeForm(ModelForm):

    comment = CharField(required=False, widget=forms.Textarea(attrs={'rows':'4', 'cols': '50'}))

    class Meta:
       model = Privilege


class UserForm(ModelForm):

    public_key = CharField(required=False, widget=forms.Textarea(attrs={'rows':'5', 'cols': '100'}))
    uid = IntegerField(initial=0, required=False, label='Associated Linux user ID (0 if not used)', max_value=90000, min_value=0)
#
#      Make sure we can cope with a blank uid
#
    def clean_uid(self):
         if not self.cleaned_data["uid"]:
             return 0
         else:
             return self.cleaned_data["uid"]             

    class Meta:
       model = User
