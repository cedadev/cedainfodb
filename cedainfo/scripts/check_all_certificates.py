#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
# https://towardsaws.com/use-python-to-check-ssl-tls-certificate-expiration-and-notify-with-aws-ses-1ce17ed25616

import sys

from cedainfoapp.models import *
import datetime
#import OpenSSL
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

def get_domain (url):

    domain = url.replace('https://', '')
    domain = domain.replace('http://', '')
    loc = domain.find('/')

    if loc != -1:
        domain = domain[0:loc]
    
    domain = domain.strip()

    return domain


def fetch_certificate (domain):
     
    PORT = 443

    context = ssl.create_default_context()
    with socket.create_connection((domain, PORT), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            certificate = ssock.getpeercert()

    return certificate
       
def get_certificate_details (domain):

    certificate = fetch_certificate(domain)
    expireDate = None
    issuer = None

    print(certificate)

    if certificate:

        #issuer = certificate["issuer"][1][0][1])

        expireDate = datetime.datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expireDate = datetime.datetime.strftime(expireDate, '%d-%b-%Y')

        issuer_org = certificate["issuer"][1][0][1]
        issuer_type = certificate["issuer"][2][0][1]

        if issuer_org == "Let's Encrypt": 
            issuer = "LetsEncrypt"
        else:
            issuer = "Other"

    return (expireDate, issuer)
       
import idna
from socket import socket
from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID


def get_certificate(hostname, port):
    hostname_idna = idna.encode(hostname)
    sock = socket()

    sock.connect((hostname, port))
    peername = sock.getpeername()
    ctx = SSL.Context(SSL.SSLv23_METHOD) # most compatible
    ctx.check_hostname = False
    ctx.verify_mode = SSL.VERIFY_NONE

    sock_ssl = SSL.Connection(ctx, sock)
    sock_ssl.set_connect_state()
    sock_ssl.set_tlsext_host_name(hostname_idna)
    sock_ssl.do_handshake()
    cert = sock_ssl.get_peer_certificate()
    crypto_cert = cert.to_cryptography()
    sock_ssl.close()
    sock.close()

    return crypto_cert

def get_issuer(cert):
    try:
        names = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        return names[0].value
    except x509.ExtensionNotFound:
        return None


def get_issuer_org(cert):
    try:
        names = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        return names[0].value
    except x509.ExtensionNotFound:
        return None
def run():

#     cert = get_certificate('users.ceda.ac.uk', 443)
#     print(get_issuer(cert))
#  #   (expireDate, issuer) = get_certificate_details ('users.ceda.ac.uk') 
#     sys.exit()
   
    services = NewService.objects.filter(status="production").order_by("url")

    for service in services:
        service.cert_expire_date = '01-jan-1900'
        service.cert_issuer = ''

        if service.url:
            service.domain = get_domain(service.url)

            if check_dns_entry(service.domain):
                print ('Checking: %s' % service.domain)
                try:
                    cert = get_certificate(service.domain, 443)
                    print ('  ', service.domain, get_issuer_org(cert), cert.not_valid_after)
                except:
                    print ('ERROR %s' % service.domain)
 #       certExpires = datetime.strptime(certificate["notAfter"], "%b %d %H:%M:%S %Y %Z")

       # print (certExpires)

        # if check_dns_entry(domain):
        #     print ('OK')
        # else:
        #     print ('Fail') 
        
