#python manage.py syncdb << EOF
#yes
#admin
#matt.pritchard@stfc.ac.uk
#foobar
#foobar
#EOF

python manage.py shell << EOF
#
from cedainfoapp.models import *
#
# setup some initial data

hosttag1 = HostTag(tag='vm_image', comment='Virtual machine')
hosttag1.save()
hosttag1 = HostTag(tag='hypervisor', comment='Host for virtual machines')
hosttag1.save()
hosttag1 = HostTag(tag='webserver')
hosttag1.save()
hosttag1 = HostTag(tag='archive_storage')
hosttag1.save()
hosttag1 = HostTag(tag='ingest_cache')
hosttag1.save()
hosttag1 = HostTag(tag='processing_cache')
hosttag1.save()
hosttag1 = HostTag(tag='dx_cache')
hosttag1.save()
hosttag1 = HostTag(tag='usb_drive_ingest')
hosttag1.save()
hosttag1 = HostTag(tag='workstation')
hosttag1.save()
hosttag1 = HostTag(tag='nas')
hosttag1.save()
hosttag1 = HostTag(tag='server')
hosttag1.save()
hosttag1 = HostTag(tag='supercomputer')
hosttag1.save()

host1 = Host(hostname='dummyhost',ip_addr='130.246.1.1',serial_no='123456',po_no='4111111',organization='neodc',height='3',supplier='dnuk',arrival_date='2009-01-01',planned_end_of_life='2009-01-01',retirement='mmm',capacity='1024')

host1.save()
#
host2 = Host(hostname='dummyhost2',ip_addr='130.246.1.2',serial_no='123457',po_no='4111112',organization='neodc',height='2',supplier='dnuk',arrival_date='2009-01-01',planned_end_of_life='2009-01-01',retirement='mmm',capacity='1024')
host2.save()
#
rack1 = Rack(name='rack1', building='r25', room='g100', size=24, notes='a big rack cabinet')
rack1.save()
#
rack2 = Rack(name='rack2', building='r25', room='g103', size=12, notes='a smaller one')
rack2.save()
#
# make a list of 24 slots to go in rack 1

for i in range(1,25):
    slotx = Slot(position=i,parent_rack=rack1)
    slotx.save()
    if i < 4:
        slotx.occupant = host1
    elif i < 6:
        slotx.occupant = host2

for i in range(1,13):
    slotx = Slot(position=i, parent_rack=rack2)
    slotx.save()

part1 = Partition(mountpoint='/badc/dummydata',host=host1,size=1024,capacity=1024,primary_use='storage',special='very',used=1024,avail=0,last_checked='2009-01-01 00:00:01')
part1.save()
#
tld1 = TopLevelDir(partition=part1, mounted_location='/disks/location1', badc_symlink_name='badcblah', neodc_symlink_name='neodcblah', dataset_type='bigdataset', notes='nothing interesting', size=14514, no_files=2, no_dirs=1, last_modified='2009-01-01 00:00:01', status_last_checked='2009-01-01 00:00:01', special='nothing special')
tld1.save()
#
cc1 = CurationCategory(category='A', description='Primary archive')
cc1.save()
cc2 = CurationCategory(category='B', description='Secondary archive')
cc2.save()
cc3 = CurationCategory(category='C', description='Facilitation mode')
cc3.save()
#
bp1 = BackupPolicy(tool='DMF', frequency='once a week', type='full', policy_version=1)
bp1.save()
#
de1 = DataEntity(top_level_dir=tld1, friendly_name='Matts dataset', current_size=1024, yearly_growth=1024, final_size=4096, curation_category=cc1, notes='some notes here', dataentity_id='neodc.nerc.ac.uk__ATOM__128473194731', symbolic_name='mattsdataset', availability_priority=False, availability_failover=False, backup_destination='/disks/backuploc1', current_backup_policy=bp1, recipes_expression='recipe1', recipes_explanation='Requires registering as a ...')
de1.save()
#
role1 = Role(role='Storage Administrator', comment='Decides what data goes where')
role1.save()
role2 = Role(role='Data Scientist', comment='Knows all about the data')
role2.save()
#
person1 = Person(name='Dan Hagon', email='dan.hagon@stfc.ac.uk', username='dhagon')
person1.save()
person2 = Person(name='Matt Pritchard', email='matt.pritchard@stfc.ac.uk', username='mpritcha')
person2.save()
#
dea1 = DataEntityAdministrator(role=role1, person=person1, data_entity=de1)
dea1.save()
dea2 = DataEntityAdministrator(role=role2, person=person2, data_entity=de1)
dea2.save()
#
EOF