#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
#  Allows a users password to be changed using the new keycloak encryption
#
import sys

from udbadmin.models import User
from keycloakutils.password import generate_hash_data

def run():

# generate_hash_data(password)
 
    userkey = input('Userkey: ')

    user = User.objects.get(userkey=userkey)
    print(user.accountid, user.title, user.othernames, user.surname, user.emailaddress.lower())

    ans = input('Contine? ')

    if ans.lower() == 'y':         
        password = input('New password: ')
        user.secret_data = generate_hash_data(password)
        user.save()

   
