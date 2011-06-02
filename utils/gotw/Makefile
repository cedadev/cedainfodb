#
# GOTW SOAP Client
#
# @author P J Kershaw 01/10/08
#
# Generate web service stubs from WSDL for GOTW client
#
# @copyright (C) 2010 STFC
#
# @license BSD - seee LICENSE file in top-level directory
#
# $Id:$
WSDL_URI = http://gotw.nerc.ac.uk/facadeservice/gotw.asmx?WSDL
WSDL_FILE=./gotw.wsdl
CMD=wsdl2py
OPTS=-be -f
    
generateStubs: getWSDL
	@echo Generate stub ...
	${CMD} ${OPTS} ${WSDL_FILE}
	@echo Done.

getWSDL:
	wget ${WSDL_URI} -O ${WSDL_FILE}
