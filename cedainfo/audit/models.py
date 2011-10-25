from django.db import models
from cedainfoapp.models import FileSet
from datetime import datetime

# Create your models here.
class File(models.Model):
    '''Individual file'''
    logical_path = models.CharField(max_length=2048)
#    fileset = models.ForeignKey('FileSet', null=True, blank=True, on_delete=models.SET_NULL)
    def __unicode__(self):
        return self.logical_path
    
class FileState(models.Model):
    '''Recorded state of a file, from an audit or ingest inspection'''
    file = models.ForeignKey(File)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    audit = models.ForeignKey('Audit')
    filestate_time = models.DateTimeField( default=datetime.now() )
    size = models.BigIntegerField()
    checksum = models.CharField(max_length=127)
    deleted = models.BooleanField(default=False)
    filetype = models.ForeignKey('FileType', null=True, blank=True)
    
class Audit(models.Model):
    '''A record of inspecting a fileset'''
    fileset_logical_path = models.CharField(max_length=1024, help_text="logical path of the fileset, set as a record when the audit was created")
    fileset = models.ForeignKey(FileSet, help_text="FileSet which this audit related to at time of creation", on_delete=models.SET_NULL, null=True, blank=True)
    starttime = models.DateTimeField(null=True)
    endtime = models.DateTimeField(null=True)
    auditstate = models.CharField(max_length=50,       
        choices=(
            ("not started","not started"),
            ("started","started"),
            ("finished","finished"),
            ("killed","killed"),
            ("error","error"),
        ),
        default="not started",
        help_text="state of this audit"
    )
    corrupted_files = models.BigIntegerField(default=0)
    new_files = models.BigIntegerField(default=0)
    deleted_files = models.BigIntegerField(default=0)
    modified_files = models.BigIntegerField(default=0)
    unchanges_files = models.BigIntegerField(default=0)
    def __unicode__(self):
        return 'Audit of %s started %s' % (self.fileset, self.starttime)

class CodeList(models.Model):
    
    name = models.CharField(max_length=127)
    description = models.TextField(blank=True)
    def __unicode__(self):
        return self.name
    class Meta:
        abstract = True
        
class FileType(CodeList):
    '''Codelist of file types'''
    pass