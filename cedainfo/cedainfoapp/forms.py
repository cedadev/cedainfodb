from django.forms import *
from cedainfo.cedainfoapp.models import *
from django.contrib.admin import widgets
from cedainfo.cedainfoapp.custom_widgets import TinyMCE


class DataEntityForm(ModelForm):
    # customise the form a bit
    dataentity_id = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    friendly_name = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    symbolic_name = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    backup_destination = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    notes = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))
    recipes_expression = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    recipes_explanation = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))
    class Meta:
        model = DataEntity

class DataEntityFormTinyMCE(ModelForm):
    # customise the form a bit
    dataentity_id = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    friendly_name = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    symbolic_name = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    backup_destination = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    notes = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))
    recipes_expression = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    recipes_explanation = CharField(widget=TinyMCE())
    class Meta:
        model = DataEntity

class DataEntityRecipeForm(DataEntityForm):
    def __init__(self, *args, **kwargs):
        super(DataEntityRecipeForm, self).__init__(*args, **kwargs)
        # doesn't seem to work disabling fields here ...makes form incomplete & therefore invalid.
	self.fields['recipes_explanation'] = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))
