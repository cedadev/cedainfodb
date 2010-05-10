from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.core import serializers
from cedainfoapp import models
import sys
import socket
import re
import logging

log = logging.getLogger("nodelistparser")

class nodelistparser:
    '''Parser for nodelist file listing servers, cabinets, xen servers etc'''
    def __init__(self, nodelistfile):
        self.parselist(nodelistfile)

    def parselist(self, nodelistfile):
        '''parse the list, and return a dictionary of lists'''
        log.debug("Opening sourcefile")
        sourcefile = open(nodelistfile, 'r')
        resolve = True

        lines = []
        discarded_lines = []
        export_lines=[]

        # regexp to match lines containing only whitespace
        whitespace_only=re.compile('^[\s]*$')
        one_or_more_spaces=re.compile('[\s]*')

        try:
            for line in sourcefile:
                line = line.rstrip('\n')
                # discard lines commented out, or containing only whitespace
                if ( line.startswith('#') or whitespace_only.match(line) ):
                    discarded_lines.append(line)
                elif ( line.startswith('export') ):
                    export_lines.append(line)
                else:
                    lines.append(line)
        finally:
            sourcefile.close()

        self.host_lists = {}
        lookup = {}
        # Handle "normal" lines:
        # assign all key="value1 $value2" lists to keys in host_list
        for line in lines:
            # split with "=" into key=valuelist pairs (then split valuelist later)
            try:
                (key, valuelist) = line.split('=')
                # strip double quotes from valuelist
                valuelist = valuelist.replace('\"', '')
                # parse the value list into a list stored as the value of a dictionary entry
                values = valuelist.split() #on any whitespace character(s) ...some have double spaces
                # Create a non-duplicating list (i.e. sub-dict) for this valuelist
                # (See Python Cookbook section 4.15 p174)
                for value in values:
                    if value == '':
                        print 'Error line: %s' % line
                    self.host_lists.setdefault(key, {})[value] = 1
                                    
            except Exception:
                print "Couldn't parse following line:\n%s" % line
                
    def get_list(self, name, resolve=False):
        '''if a single value e.g. $value2 starts with $ it is a variable and needs resolving :
        return a (unique-ified) list, optionally with values resolved'''
        # find a list
        # iterate through its keys
        # if any keys are variables (have $ or are in lookup) then substitute with values of that list & append to list, returning the new list
        tmp_list = self.host_lists[name].keys()
        if resolve:
            # iterate through tmp_list, replace members with lists of same name
            count=0
            for itemkey in tmp_list:
                if itemkey.startswith('$'):
                    # this may itself be a dictionary key to another list of items
                    itemname = itemkey.replace('$', '')
                    # remove the offending item
                    tmp_list[count:count+1] = self.host_lists[itemname].keys()
                count = count + 1
        # return the list, uniuqe-ifying it on the fly
        return list(set(tmp_list))

    def showXenServers(self):
        '''Show the XENServers'''
        # For each entry in XENServerList, there is a corresponding list XENServer_servername which lists the clients to that XENServer.
        # first print list of XENServers (hypervisors)
        for host in sorted(self.get_list('XENServerList', True)):
            print "XENServer:\t%s" % host

    def showXenClients(self):
        '''Show the VMs (XENClients) running on each XENServer'''
        for xenserver_name in sorted(self.get_list('XENServerList', True)):
            # need to prepend "XENServer_" to name to make name of xenclients belonging to this server
            # despite using hyphens in machine names e.g. ddp-ps1, hyphens are not allowed in variable names
            # i.e. the left hand side of assignments in the nodelist file (which is a shell script)
            # so here we need to replace hyphens by underscores to retrieve the variable name used for the server
            xenserver_name = xenserver_name.replace('-','_')
            client_list_name = 'XENServer_%s' % xenserver_name
            for xenclient in sorted(self.get_list(client_list_name, True)):
                print "XENClient:\t%s\t\t(%s)" % (xenclient, xenserver_name)

    def hackLists(self):
        '''Hack the dictionary of lists to create our own groupings'''
        self.host_lists["CEDAList"] = {'$NEODCList': 1, '$DDPList': 1, '$XENServerList': 1, '$XENClientList': 1, '$BADCList': 1, '$GRAPEList': 1, '$BDANList': 1}
        self.host_lists["MISCBADCList"]={'almond': 1, 'ceda-batch1': 1, 'ceda-wps1': 1,  'cirrus': 1, 'drought': 1, 'esg-dev1': 1, 'flood': 1, 'hail': 1, 'halny': 1, 'lunar': 1, 'neptune': 1, 'warm': 1}
        self.host_lists["MISCNEODCList"]={'urals': 1, 'pennines': 1}
        
    def insertHosts(self):
        '''If not already present, insert parsed hosts into the db'''
        default_host_suffix = '.badc.rl.ac.uk'
        for host in sorted(self.get_list('CEDAList', True)):
            # is this a member of (BADCList or DDPList) or NEODCList?
            if ( host in self.get_list('BADCList', True) or host in self.get_list('DDPList', True) or host in self.get_list('GRAPEList', True) or host in self.get_list('MISCBADCList', True)):
                fullhostname = '%s.badc.rl.ac.uk' % host
            elif ( host in self.get_list('NEODCList', True)  or host in self.get_list('MISCNEODCList', True)):
                fullhostname = '%s.neodc.rl.ac.uk' % host
            elif (host in self.get_list('BDANList', True)):
                # odd ones : some have full host name, others don't
                bdan_suffix = ".ral2.bdan.ncas.ac.uk"
                if host.endswith(bdan_suffix):
                    fullhostname = host
                else:
                    fullhostname = '%s%s' % (host, bdan_suffix)
            else:
                fullhostname = '%s%s' % (host, default_host_suffix)
            search_host = models.Host.objects.filter(hostname=fullhostname)
            if len(search_host) > 0:
                print "Found host %s" % fullhostname
            else:
                print "Need new entry for %s" % fullhostname
                try:
                    ipaddr = socket.gethostbyaddr( fullhostname )[2][0]
                    new_host = models.Host(hostname=fullhostname, ip_addr=ipaddr)
                    print "Made new host object with ip for %s ...not saved yet" % fullhostname
                    new_host.save()
                    print "Saved %s" % new_host
                except:
                    print "Can't resolve %s to an ip address" % fullhostname
                    new_host = models.Host(hostname=fullhostname, ip_addr='')
                    print "Made new host object (no ip) for %s ...not saved yet" % fullhostname
                    new_host.save()
                    print "Saved %s" % new_host

    def checkHosts(self):
        '''Reverse check by fetching hosts from DB & seeing if there in one of the lists'''
        # Reverse check : get list from DB, list those not in the nodelist file (filter out those retired already)
        log.info("Reverse check : Problem hosts either retired or not in a list")
        db_hosts = models.Host.objects.filter(retired_on=None)
        for host in db_hosts:
            hostname = host.hostname.split('.')[0]
            if (hostname not in self.get_list('CEDAList', True)) and (hostname not in self.get_list('MISCNEODCList', True)) and (hostname not in self.get_list('MISCBADCList', True)):
                print "Not OK:\t%s\t(retired_on = %s)" % (hostname, host.retired_on)

    def assignRacks(self):
        '''Assign hosts to racks based on rack contents lists'''
        # Move rack stuff to place marked above
        log.info("Racks")
        # BADC
        for rack in ['BADCCab1', 'BADCCab2', 'BADCCab3','BADCCab4','BADCCab5','BADCCab6','BADCCab7','BADCCab8','ATSRCab1','ATSRCab2','ATSRCab4','CEDACab1']:
            target_rack = models.Rack.objects.get(name=rack)
            default_host_suffix = '.badc.rl.ac.uk'
            for host in sorted(self.get_list(rack, True)):
                if ( host in self.get_list('BADCList', True) or host in self.get_list('DDPList', True) or host in self.get_list('GRAPEList', True) or host in self.get_list('MISCBADCList', True)):
                    fullhostname = '%s.badc.rl.ac.uk' % host
                elif ( host in self.get_list('NEODCList', True)  or host in self.get_list('MISCNEODCList', True)):
                    fullhostname = '%s.neodc.rl.ac.uk' % host
                elif (host in self.get_list('BDANList', True)):
                    # odd ones : some have full host name, others don't
                    bdan_suffix = ".ral2.bdan.ncas.ac.uk"
                    if host.endswith(bdan_suffix):
                        fullhostname = host
                    else:
                        fullhostname = '%s%s' % (host, bdan_suffix)
                else:
                    fullhostname = '%s%s' % (host, default_host_suffix)

                try:
                    target_host = models.Host.objects.get(hostname=fullhostname)
                except:
                    print 'problem assigning rack for host %s (%s?)' % (host, fullhostname)
                    target_host = None

                if target_host != None:
                    target_host.rack = target_rack
                    print "Set rack to %s for host %s" % (target_host.rack, target_host)
                    target_host.save()


if __name__=="__main__":

    # setup logging stuff
    logging.basicConfig()
    log = logging.getLogger("nodelistparser")
    log.setLevel(logging.DEBUG)
    log.debug("Starting...")

    # do some things
    nodelistfile = sys.argv[1]
    parser = nodelistparser(nodelistfile)
    #parser.showXenServers()
    #parser.showXenClients()
    parser.hackLists()
    #parser.insertHosts()
    parser.checkHosts()
    parser.assignRacks()

# ATSR
#for rack in sorted(get_list('ATSRCabList', False)):
#    print rack
#    for host in sorted(get_list(rack, True)):
#        print host     
