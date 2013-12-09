#
# Checks all the links in a given file to make sure they have .ftpaccess
# files in place.
#

import os

links_file = open ('links.lis', 'r')

for line in links_file:
    link = line.rstrip()
    
    if not os.path.islink(link):
        print 'ERROR: %s is not a link' % link
	continue
	
    target = os.readlink(link)
    
    if target.startswith('/datacentre/'):
#        print link, target

        
	if not os.path.exists(target + '/.ftpaccess'):
	    print 'Missing ftpaccess file in : %s ' % target	
	
    
    	
	
