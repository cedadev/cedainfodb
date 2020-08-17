from django.forms import *
from models import *
from django.contrib.admin import widgets
from django.utils.safestring import mark_safe
import choices
import LDAP

class JasminUsersForm(forms.Form):
    show_ceda_users  =  BooleanField(required=False)
    show_jasmin_users = BooleanField(required=False)
    show_jasmin2_users  = BooleanField(required=False)
    
    email_only = BooleanField(required=False)
    
class LDAPuserForm(forms.Form):
    tagname = ChoiceField(choices=LDAP.peopleTagChoices())
    
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
    comments = CharField(required=False, widget=Textarea(attrs={'rows':'4', 'cols': '50'}))
    defaultreglength = CharField(initial=36, required=False, label='Default Registration length (months)', max_length=4, widget=TextInput(attrs={'size': '4'}))
    conditions = CharField(required=False, widget=TextInput(attrs={'size': '80'}))
    description = CharField(required=False, widget=TextInput(attrs={'size': '80'}))  
    directory = CharField(required=False, widget=TextInput(attrs={'size': '80'}))  
    infourl = CharField(required=False, widget=TextInput(attrs={'size': '80'}))  
    
    label = 'Associated Linux Group ID (0 if not used) <a target="_blank" href="/udbadmin/ldap/freegids">Find free gid</a>'
    gid = IntegerField(initial=0, required=False, label=mark_safe(label), max_value=90000, min_value=0)
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
        fields = ('datasetid', 'authtype', 'grp', 'description', 'directory', 'conditions', 'defaultreglength', 'datacentre', 'infourl', 'comments')

class PrivilegeForm(ModelForm):

    comment = CharField(required=False, widget=Textarea(attrs={'rows':'4', 'cols': '50'}))

    class Meta:
       model = Privilege
       exclude=('',)


class UserForm(ModelForm):

    surname      = CharField(required=False, widget=TextInput(attrs={'size': '60'}))  
    othernames   = CharField(required=False, widget=TextInput(attrs={'size': '60'}))  
    emailaddress = CharField(required=False, widget=TextInput(attrs={'size': '60'}))  
    telephoneno = CharField(required=False, widget=TextInput(attrs={'size': '60'}))  
    openid = CharField(required=False, widget=TextInput(attrs={'size': '60'}))  
    
    public_key = CharField(required=False, widget=Textarea(attrs={'rows':'5', 'cols': '100'}))
    label = 'Associated Linux user ID (0 if not used) <a target="_blank" href="/udbadmin/ldap/freeuids">Find free uid</a>'
    uid = IntegerField(initial=0, required=False, label=mark_safe(label), max_value=7059999, min_value=0)
    gid = IntegerField(initial=0, required=False, label='Primary group id (0= use default)', max_value=90000, min_value=0)
    shell = CharField(required=False, label='Shell - leave blank to use default')
    home_directory = CharField(required=False, label='Home directory. Leave blank to use default')

#
#   Insert empty email addresses as null so we can have a unique constraint on this field
#
    def clean_emailaddress(self):
        return self.cleaned_data['emailaddress'] or None

    
#
#      Make sure we can cope with a blank uid
#
    def clean_uid(self):
         if not self.cleaned_data["uid"]:
             return 0
         else:
             return self.cleaned_data["uid"]             

    def clean_gid(self):
         if not self.cleaned_data["gid"]:
             return 0
         else:
             return self.cleaned_data["gid"]             

    class Meta:
       model = User
       exclude=('',)
