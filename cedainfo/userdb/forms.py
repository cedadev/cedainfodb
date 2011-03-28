from django.forms import *
from cedainfo.userdb.models import *
from django.contrib.admin import widgets


class UserForm(ModelForm):
    # customise the form a bit
    class Meta:
        model = User
        fields = ('title', 'firstname', 'lastname', 'email', 'tel', 'address', 'postcode', 
	          'webpage', 'studying_for', 'field', 'supervisor', 'openid', 'institute')


class NewUser(ModelForm):
    # customise the form a bit
    passwd = CharField(widget=PasswordInput)
    passwd2 = CharField(widget=PasswordInput)
    class Meta:
        model = User
        fields = ('title', 'firstname', 'lastname', 'email', 'username', 'institute')

    
class UserStatsForm(Form):
    # customise the form a bit
    role = ModelChoiceField(queryset= Role.objects.all().order_by('name'))
    group = ModelChoiceField(queryset= Group.objects.all().order_by('name'))


class ChangePassword(Form):
    passwd = CharField(widget=PasswordInput)
    passwd2 = CharField(widget=PasswordInput)
