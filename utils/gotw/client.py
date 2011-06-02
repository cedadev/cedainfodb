"""NERC GOTW (Grants on the Web) client module

"""
__author__ = "P J Kershaw"
__date__ = "14/04/10"
__copyright__ = "(C) 2010 Science and Technology Facilities Council"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = "$Id: $"
from gotw.http_proxy import ProxyHTTPConnection
from gotw.Gotw_services import GotwLocator


class GotwClient(object):
    """NERC GOTW (Grants on the Web) SOAP Web Service Client.  See the unit
    test module for example usage: gotw.test.test_gotw
    """
    
    def __init__(self, url=None):
        """Create a binding to the web service and associate as an attribute of
        this class.  The binding is created with a custom HTTP Connection class
        which enables it communicate through site HTTP proxies.  Set http_proxy
        environment variable in order to set the proxy address
        
        @param url: Web service endpoint to connect to.  May default to None but
        in this case it must be set at a later stage and before any web service
        methods are invoked
        @type url: basestring/None 
        """
        locator = GotwLocator()
        self.binding = locator.getGotwSoap(url=url,
                                           transport=ProxyHTTPConnection)
