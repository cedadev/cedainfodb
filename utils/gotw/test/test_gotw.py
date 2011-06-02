#!/usr/bin/env python
"""NERC GOTW (Grants on the Web) unit test module
"""
__author__ = "P J Kershaw"
__date__ = "14/04/10"
__copyright__ = "(C) 2010 Science and Technology Facilities Council"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = "$Id: $"
import unittest
from gotw.client import GotwClient


class GotwUnitTestCase(unittest.TestCase):
    """Test NERC GOTW (Grants on the Web) SOAP client operations"""
    WS_URI = 'http://gotw.nerc.ac.uk/facadeservice/gotw.asmx'
    
    def test01GetGrantReferenceNumbers(self):
        gotwClient = GotwClient(url=GotwUnitTestCase.WS_URI)
        
        refNums = gotwClient.binding.GetGrantReferenceNumbers()
        self.assert_(refNums)
        self.assert_(getattr(refNums, 'String'))
        print refNums.String
        
    def test02GetDataByGrantReferenceNumber(self):
        gotwClient = GotwClient(url=GotwUnitTestCase.WS_URI)
        
        project = gotwClient.binding.GetDataByGrantReferenceNumber('NE/H006834/1')
        self.assert_(project)
        print project.Abstract
        print project.Department
        print project.StartDate
        
        
if __name__ == "__main__":
    unittest.main()
