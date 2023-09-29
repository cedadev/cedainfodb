#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
# https://towardsaws.com/use-python-to-check-ssl-tls-certificate-expiration-and-notify-with-aws-ses-1ce17ed25616

import sys

from cedainfoapp.models import *
from datetime import datetime
import OpenSSL
import ssl


def check_dns_entry(hostname):
    #
    #   Check if dns entry for given host exits
    #
    import socket

    try:
        address = socket.gethostbyname(hostname)
        return True
    except:
        return False

def fetch_certificate (domain):
     
    PORT = 443

    context = ssl.create_default_context()
    with socket.create_connection((domain, PORT), timeout=30) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            certificate = ssock.getpeercert()

    return certificate
       
       
def get_certificate_details (domain):

    certificate = fetch_certificate(domain)
    
    expireDate = None
    issuer = None

    if certificate:
        expireDate = datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z")
        issuer_full = certificate["issuer"][2][0][1]
        
        if issuer_full == 'R3':
            issuer = "LetsEncrypt"
        else:
            issuer = "Other"

    return (expireDate, issuer)

def run():

    for line in sys.stdin:
        domain = line.strip()

        if not domain:
            continue
        
        print(domain, end="   ")

        if check_dns_entry(domain):
            (expireDate, issuer) = get_certificate_details (domain)

            if (expireDate):
                print (datetime.strftime(expireDate, '%d-%b-%Y'), issuer, end="") 

        else:
            print ('No DNS', end=" ")

        print ("")

 #       certExpires = datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z")

       # print (certExpires)

        # if check_dns_entry(domain):
        #     print ('OK')
        # else:
        #     print ('Fail') 
        
