#!/usr/bin/env python

import sys
from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *

   
class loader:
    def __init__(self,file):
        for line in open(file, 'r').readlines():
	    line = line.strip()
	    print line
            fields = line.split('\",\"')
	    object = self.parse_line(fields)
	    print "object:", object
	    object.save()

    # define some helper methods for cleaning fields
    def valornull(self,str):
        return str if len(str) > 0 else None

    def valorblank(self,str):
        return str if len(str) > 0 else ''

    def valordummy(self,str,dummystr):
        return str if len(str) > 0 else dummystr

    def trueorfalse(self,str):
        return True if str == "t" else False

    def decimalornone(self,str):
        try:
            n = float(str)
            return str
        except ValueError:
            return None
    
    def tb_to_b(self,str):
        try:
	    if (str != None) and (str != ''):    
                tb = int(float(str))
                return tb*1024*1024*1024*1024
	    else:
	        return None
        except ValueError:
            return None

    def get_host(self,id):
        try:
	    host = Host.objects.get(pk=id)
	    return host
	except:
	    return None
        
    def get_partition(self,id):
        try:
	    partition = Partition.objects.get(pk=id)
	    return partition
	except:
	    return None

    def get_person(self,id):
        try:
	    person = Person.objects.get(pk=id)
	    return person
	except:
	    return None

    def get_topleveldir(self,id):
        try:
	    tld = TopLevelDir.objects.get(pk=id)
	    return tld
	except:
	    return None

    def get_accessstatus(self,str):
        try:
	    obj = AccessStatus.objects.get(status=str)
	    return obj
	except:
	    return None

    def get_backuppolicy(self,str):
        try:
	    obj = BackupPolicy.objects.get(tool=str)
	    return obj
	except:
	    return None

    def get_curationcategory(self,str):
        try:
	    obj = CurationCategory.objects.get(category=str)
	    return obj
	except:
	    return None

class hostloader(loader):

    def parse_line(self, fields):
	 # read the file (1 host per line)


            field = {
                'id':                       self.valornull( fields[0].strip('\"') ),
                'hostname' :                self.valorblank( fields[1].strip('\"') ),
                'ip_addr' :                 self.valorblank( fields[2].strip('\"') ),
                'serial_no' :               self.valorblank( fields[3].strip('\"') ),
                'retired' :                 self.trueorfalse( fields[4].strip('\"') ),
                'po_no' :                   self.valorblank( fields[5].strip('\"') ),
                'organization' :            self.valorblank( fields[6].strip('\"') ),
                'height' :                  self.valornull( fields[7].strip('\"') ),
                'supplier' :                self.valorblank( fields[8].strip('\"') ),
                'arrival_date' :            self.valornull( fields[9].strip('\"') ),
                'planned_end_of_life' :     self.valornull( fields[10].strip('\"') ),
                'retirement' :              self.valorblank( fields[11].strip('\"') ),
                'notes' :                   self.valorblank( fields[12].strip('\"') ),
                'capacity' :                self.decimalornone( fields[13].replace("\"", "") ),
            }

            for name in ['id', 'hostname', 'ip_addr', 'serial_no','retired', 'po_no', 'organization', 'height', 'supplier', 'arrival_date', 'planned_end_of_life', 'retirement', 'notes', 'capacity']:
                print "%s\t:%s" % (name, field[name])       
            obj = Host(
	        id=field['id'],
		hostname=field['hostname'],
		ip_addr=field['ip_addr'],
		serial_no=field['serial_no'],
		retired=field['retired'],
		po_no=field['po_no'],
		organization=field['organization'],
		height=field['height'],
		supplier=field['supplier'],
		arrival_date=field['arrival_date'],
		planned_end_of_life=field['planned_end_of_life'],
		retirement=field['retirement'],
		notes=field['notes'],
		capacity=field['capacity'] )
	    
	    return obj

class partitionloader(loader):

    def parse_line(self, fields):
        print "Partition loader"

	print fields

        field = {
	    'id':                   fields[0].strip('\"'),
            'mountpoint':           self.valorblank( fields[1].strip('\"') ),
            'host' :                self.valornull( fields[2].strip('\"') ),
            'size' :                self.valornull( fields[3].strip('\"') ),
            'capacity' :            self.valornull( fields[4].strip('\"') ),
            'primary_use' :         self.valorblank( fields[5].strip('\"') ),
            'special' :             self.valorblank( fields[6].strip('\"') ),
            'used' :                self.valornull( fields[7].strip('\"') ),
            'type' :                self.valorblank( fields[8].strip('\"') ),
            'avail' :               self.valornull( fields[9].strip('\"') ),
            'last_checked' :        self.valornull( fields[10].strip('\"') ),
        }

        for name in ['mountpoint', 'host', 'size', 'capacity', 'primary_use', 'special', 'used', 'type', 'avail', 'last_checked']:
            print "%s\t:%s" % (name, field[name])       

        obj = Partition(
            id=field['id'],
	    mountpoint=field['mountpoint'],
            host=self.get_host(field['host']),
	    size=field['size'],
	    capacity=field['capacity'],
	    primary_use=field['primary_use'],
	    special=field['special'],
	    used=field['used'],
	    type=field['type'],
	    avail=field['avail'],
	    last_checked=field['last_checked']
        )
	    
	return obj
     
class tldloader(loader):

    def parse_line(self, fields):
        print "Top Level Directory loader"

	print fields

        field = {
            'id':                   fields[0].strip('\"'),
            'partition' :                self.valornull( fields[1].strip('\"') ),
            'mounted_location' :                self.valorblank( fields[2].strip('\"') ),
            'badc_symlink_name' :            self.valorblank( fields[3].strip('\"') ),
            'neodc_symlink_name' :         self.valorblank( fields[4].strip('\"') ),
            'dataset_type' :         self.valorblank( fields[5].strip('\"') ),
            'notes' :         self.valorblank( fields[6].strip('\"') ),
            'size' :         self.valornull( fields[7].strip('\"') ),
            'no_files' :         self.valornull( fields[8].strip('\"') ),
            'no_dirs' :         self.valornull( fields[9].strip('\"') ),
            'last_modified' :         self.valornull( fields[10].strip('\"') ),
            'status_last_checked' :         self.valornull( fields[11].strip('\"') ),
            'special' :         self.valorblank( fields[12].strip('\"') ),

        }

        for name in ['id','partition','mounted_location','badc_symlink_name','neodc_symlink_name','dataset_type','notes','size','no_files','no_dirs','last_modified','status_last_checked','special']:
            print "%s\t:%s" % (name, field[name])       

        obj = TopLevelDir(
	    id = field['id'],
            partition = self.get_partition(field['partition']), 
            mounted_location = field['mounted_location'],
            badc_symlink_name = field['badc_symlink_name'],
            neodc_symlink_name = field['neodc_symlink_name'],
            dataset_type = field['dataset_type'],
            notes = field['notes'],
            size = field['size'],
            no_files = field['no_files'],
            no_dirs = field['no_dirs'],
            last_modified = field['last_modified'],
            status_last_checked = field['status_last_checked'],
            special = field['special'],
        )
            
        return obj

class dataentityloader(loader):

    def parse_line(self, fields):
        print "Data Entity loader"

	print fields

        field = {
            'top_level_dir' :                self.valornull( fields[1].strip('\"') ),
            'friendly_name' :                self.valordummy( fields[0].strip('\"'), '<friendly_name>' ),
            'current_size' :                 self.valornull( fields[2].strip('\"') ),
            'yearly_growth' :                self.valornull( fields[3].strip('\"') ),
            'final_size' :                   self.valornull( fields[4].strip('\"') ),
            'notes' :                        self.valorblank( fields[5].strip('\"') ),
	    'dataentity_id' :                self.valordummy( '', '<moles_dataentity_id>'),
	    'symbolic_name' :                self.valordummy( '', '<symbolic_name>'),
	    'availability_priority' :        self.trueorfalse( fields[6].strip('\"') ),
	    'availability_failover' :        self.trueorfalse( fields[6].strip('\"') ), # note same as above for now
	    'backup_destination' :           self.valordummy( '', '<backup_destination>'),
            'recipes_expression' :           self.valordummy( '', '<recipes_expression>'),
	    'recipes_explanation' :          self.valordummy( '', '<recipes_explanation>'),

        }

        for name in ['friendly_name','top_level_dir','current_size','yearly_growth','final_size','notes']:
            print "%s\t:%s" % (name, field[name])       

        obj = DataEntity(
            top_level_dir = self.get_topleveldir(field['top_level_dir']), 
            friendly_name = field['friendly_name'],
            current_size = self.tb_to_b(field['current_size']),
            yearly_growth = self.tb_to_b(field['yearly_growth']),
            final_size = self.tb_to_b(field['final_size']),
	    curation_category = self.get_curationcategory('<?>'),
            notes = field['notes'],
	    dataentity_id = field['dataentity_id'],
	    symbolic_name = field['symbolic_name'],
	    availability_priority = field['availability_priority'],
	    availability_failover = field['availability_failover'],
	    backup_destination = field['backup_destination'],
	    current_backup_policy= self.get_backuppolicy('<?>'),
	    recipes_expression = field['recipes_expression'],
	    recipes_explanation = field['recipes_explanation'],
	    access_status = self.get_accessstatus('<?>')
        )
            
        return obj

class rackloader(loader):

    def parse_line(self, fields):
        print "Rack loader"

	print fields

        field = {
            'name' :                fields[0].strip('\"'),
            'building' :            fields[1].strip('\"'),
            'room' :                fields[2].strip('\"'),
        }

        for name in ['name','building','room',]:
            print "%s\t:%s" % (name, field[name])       

        obj = Rack(
            name = field['name'], 
            building = field['building'],
            room = field['room'],
	    size=0
        )
            
        return obj


class curationcategorymaker():
    def __init__(self):
        CurationCategory(category='A',description='primary archive').save()
        CurationCategory(category='B',description='secondary archive').save()
        CurationCategory(category='C',description='facilitation mode').save()

class backuppolicymaker():
    def __init__(self):
        BackupPolicy(tool='DMF',frequency='daily',type='?',policy_version=1).save()

class accessstatusmaker():
    def __init__(self):
	AccessStatus(status='public',comment='Public access no restriction').save()
	AccessStatus(status='registered',comment='Available to any registered user').save()
	AccessStatus(status='restricted',comment='Dataset registration required').save()

class personmaker():
    def __init__(self):
        Person(name='Kevin Marsh',email='kevin.marsh@stfc.ac.uk',username='kmarsh').save()
        Person(name='Sarah Callaghan',email='sarah.callaghan@stfc.ac.uk',username='scallagh').save()
        Person(name='Alan Iwi',email='alan.iwi@stfc.ac.uk',username='iwi').save()
	Person(name='Victoria Bennett',email='victoria.bennett@stfc.ac.uk',username='vjay').save()
	Person(name='Graham Parton',email='graham.parton@stfc.ac.uk',username='gparton').save()
        Person(name='Sam Pepler',email='sam.pepler@stfc.ac.uk',username='spepler').save()
        Person(name='Matt Pritchard',email='matt.pritchard@stfc.ac.uk',username='mpritcha').save()
        Person(name='Stephen Pascoe',email='stephen.pascoe@stfc.ac.uk',username='spascoe').save()
        Person(name='Charlotte Pascoe',email='charlotte.pascoe@stfc.ac.uk',username='hearnsha').save()
        Person(name='Anabelle Guillory',email='anabelle.guillory@stfc.ac.uk',username='menochet').save()
        Person(name='Wendy Garland',email='wendy.garland@stfc.ac.uk',username='wgarland').save()
        Person(name='Martin Juckes',email='martin.juckes@stfc.ac.uk',username='mjuckes').save()
        Person(name='Spiros Ventouras',email='spiros.ventouras@stfc.ac.uk',username='sventour').save()
        Person(name='Peter Chiu',email='peter.chiu@stfc.ac.uk',username='pcmc').save()
        Person(name='Dan Hagon',email='dan.hagon@stfc.ac.uk',username='dfhagon').save()

class rolemaker():
    def __init__(self):
        Role(role="Data scientist").save()
        Role(role="Storage administrator").save()
        Role(role="System administrator").save()

class hosttagmaker():
    def __init__(self):
        HostTag(tag='vm_image', comment='Virtual machine').save()
        HostTag(tag='hypervisor', comment='Host for virtual machines').save()
        HostTag(tag='webserver').save()
        HostTag(tag='archive_storage').save()
        HostTag(tag='ingest_cache').save()
        HostTag(tag='processing_cache').save()
        HostTag(tag='dx_cache').save()
        HostTag(tag='usb_drive_ingest').save()
        HostTag(tag='workstation').save()
        HostTag(tag='nas').save()
        HostTag(tag='server').save()
        HostTag(tag='supercomputer').save()
		


if __name__=="__main__":
    hostfile=sys.argv[1]
    partitionfile=sys.argv[2]
    tldfile=sys.argv[3]
    defile=sys.argv[4]
    rackfile=sys.argv[5]

    # invoke each of the loaders / makers...
    hosttagmaker()
    hostloader(hostfile)
    partitionloader(partitionfile)
    tldloader(tldfile)
    curationcategorymaker()
    backuppolicymaker()
    accessstatusmaker()
    personmaker()
    rolemaker()
    #dataentityloader(defile)
    rackloader(rackfile)
