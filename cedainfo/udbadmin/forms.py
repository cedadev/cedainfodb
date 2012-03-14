from django.forms import *
from models import *
from django.contrib.admin import widgets
import choices

class UdjForm(forms.Form):
   fundingtype = ChoiceField(choices=choices.FUNDING_TYPES)
   nercfunded  = ChoiceField(choices=choices.NERC_FUNDED)
   openpub     = ChoiceField(choices=choices.OPEN_PUBLICATION)
   removed     = ChoiceField(choices=((0, "No"), (-1, "Yes")))

class DatasetForm(ModelForm):
    # customise the form a bit
    comments = CharField(required=False, widget=forms.Textarea(attrs={'rows':'4', 'cols': '50'}))
    defaultreglength = CharField(initial=36, required=False, label='Default Registration length (months)', max_length=4, widget=forms.TextInput(attrs={'size': '4'}))
    conditions = CharField(widget=forms.TextInput(attrs={'size': '80'}))
    directory = CharField(required=False)   
    class Meta:
        model = Dataset
#	fields = ('datasetid', 'authtype', 'grp', 'description', 'directory', 'conditions', 'defaultreglength', 'datacentre', 'infourl', 'comments')

