from django.forms import *
from cedainfo.cedainfoapp.models import *
from django.contrib.admin import widgets
from cedainfo.cedainfoapp.custom_widgets import TinyMCE
from django.forms.extras.widgets import SelectDateWidget

class DataEntityForm(ModelForm):
    # customise the form a bit
    dataentity_id = CharField(widget=forms.TextInput(attrs={'size':'90'}), help_text="MOLES data entity id")
    friendly_name = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Friendly name e.g. (A)ATSR Multimission")
    symbolic_name = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Symbolic name e.g. (no special chars) aatsr_multimission")
    logical_path  = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Location of data within archive e.g. /neodc/aatsr_multimission")
    
    backup_destination = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Backup destination [TODO: e.g. ??]")
    notes = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}), required=False, help_text="(free text)")
    recipes_expression = CharField(label="Registration info", widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="URI to registration info e.g. http://neodc.nerc.ac.uk/dataset_info?datasetid=aatsr_multimission or multiple e.g. http://badc.nerc.ac.uk/dataset_info?datasetid=faam_core&datasetid=ecmwftrj. Leave blank if access_status = public")
    recipes_explanation = CharField(label="Registration info explanation", widget=forms.Textarea(attrs={'cols':'60','rows':'10'}), required=False, help_text="Text explanation of registration requirements if complex.")
    last_reviewed = DateField(widget=SelectDateWidget(), label="Date of last dataset review") # TODO find how to use some date time widget e.g. django.contrib.admin.widgets.AdminSplitDateTime. See http://faces.eti.br/2009/02/18/fixing-date-input-in-django/
    class Meta:
        model = DataEntity
        exclude = ('db_match') # admin use only

class DataEntityFormTinyMCE(ModelForm):
    # customise the form a bit
    dataentity_id = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    friendly_name = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    symbolic_name = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    backup_destination = CharField(widget=forms.TextInput(attrs={'size':'60'}))
    notes = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))
    recipes_expression = CharField(widget=forms.TextInput(attrs={'size':'80'}))
    recipes_explanation = CharField(widget=TinyMCE())
    class Meta:
        model = DataEntity

class DataEntityRecipeForm(DataEntityForm):
    def __init__(self, *args, **kwargs):
        super(DataEntityRecipeForm, self).__init__(*args, **kwargs)
        # doesn't seem to work disabling fields here ...makes form incomplete & therefore invalid.
	self.fields['recipes_explanation'] = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))
