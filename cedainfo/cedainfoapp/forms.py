from django.forms import *
from cedainfo.cedainfoapp.models import *
from django.contrib.admin import widgets
from cedainfo.cedainfoapp.custom_widgets import TinyMCE
from django.forms.extras.widgets import SelectDateWidget

import datetime

# make list of years to use in select box for date widget, current year minus 10
YEARS = []
start_year = -10 + datetime.date.today().year
i = 0
while i <= 10:
    YEARS.append(start_year+i)
    i = i + 1

class DataEntityForm(ModelForm):
    # customise the form a bit
    dataentity_id = CharField(widget=forms.TextInput(attrs={'size':'90'}), help_text="MOLES data entity id")
    friendly_name = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Friendly name e.g. (A)ATSR Multimission")
    symbolic_name = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Symbolic name e.g. (no special chars) aatsr_multimission")
    logical_path  = CharField(widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="Location of data within archive e.g. /neodc/aatsr_multimission")
    #fileset = ModelMultipleChoiceField(label="File set(s)", queryset=FileSet.objects.order_by('logical_path'), help_text="Select file sets that make up this data entity. Hold down \"Control\", or \"Command\" on a Mac, to select more than one.")
    notes = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}), required=False, help_text="(free text)")
    recipes_expression = CharField(label="Registration info", widget=forms.TextInput(attrs={'size':'60'}), required=False, help_text="URI to registration info e.g. http://neodc.nerc.ac.uk/dataset_info?datasetid=aatsr_multimission or multiple e.g. http://badc.nerc.ac.uk/dataset_info?datasetid=faam_core&datasetid=ecmwftrj. Leave blank if access_status = public")
    recipes_explanation = CharField(label="Registration info explanation", widget=forms.Textarea(attrs={'cols':'60','rows':'10'}), required=False, help_text="Text explanation of registration requirements if complex.")
    last_reviewed = DateField(widget=SelectDateWidget(years=YEARS), required=False, help_text="Date of last dataset review") # TODO find how to use some date time widget e.g. django.contrib.admin.widgets.AdminSplitDateTime. See http://faces.eti.br/2009/02/18/fixing-date-input-in-django/
    next_review = DateField(widget=SelectDateWidget(), required=False, help_text="Date of next dataset review") # TODO find how to use some date time widget e.g. django.contrib.admin.widgets.AdminSplitDateTime. See http://faces.eti.br/2009/02/18/fixing-date-input-in-django/
    class Meta:
        model = DataEntity
        exclude = ('db_match') # admin use only

class DataEntityRecipeForm(DataEntityForm):
    def __init__(self, *args, **kwargs):
        super(DataEntityRecipeForm, self).__init__(*args, **kwargs)
        # doesn't seem to work disabling fields here ...makes form incomplete & therefore invalid.
	self.fields['recipes_explanation'] = CharField(widget=forms.Textarea(attrs={'cols':'60','rows':'10'}))


### popupplus stuff see http://www.hoboes.com/Mimsy/hacks/replicating-djangos-admin/
from django.template.loader import render_to_string

class SelectWithPop(Select):
	def render(self, name, *args, **kwargs):
		html = super(SelectWithPop, self).render(name, *args, **kwargs)
		popupplus = render_to_string("form/popupplus.html", {'field': name})

		return html+popupplus

class MultipleSelectWithPop(SelectMultiple):
	def render(self, name, *args, **kwargs):
		html = super(MultipleSelectWithPop, self).render(name, *args, **kwargs)
		popupplus = render_to_string("form/popupplus.html", {'field': name})

		return html+popupplus
# end of popupplus stuff

# Subclass ModelChoiceForm with custom label_from_instance method to use custom label showing FileSetCollection AND PartitionPool
class FSCPPModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        pool = 'None'
        if ( obj.partitionpool is not None and obj.partitionpool != '' ):
            pool = obj.partitionpool
        return "FileSetCollection: %s PartitionPool: %s" % ( obj.logical_path, pool )

class FileSetCollectionLinkForm(Form):
    filesetcollection = FSCPPModelChoiceField( queryset=FileSetCollection.objects.all(), widget=SelectWithPop )

class FileSetMakerForm(Form):
    filesetcollection = ModelChoiceField( queryset=FileSetCollection.objects.all() )
    file = FileField()
    
        
        
