from django.db import models

# Create your models here.

class Person(models.Model):
    name = models.CharField(max_length=200)
    username = models.CharField(max_length=20)
    active = models.BooleanField() 
    CEDA = models.BooleanField() 
    fedid = models.CharField(max_length=20)
    band = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

   
class Availability(models.Model):
    person =  models.ForeignKey(Person)
    month = models.DateField()
    value = models.FloatField()
    
class Code(models.Model):
       
    title = models.CharField(max_length=200)
    project =  models.CharField(max_length=200)
    task =  models.CharField(max_length=200)
    notes = models.TextField()
    CEDA = models.BooleanField() 
    PRO = models.ForeignKey(Person)
    status = models.CharField(max_length=50,       
              choices=(("Potential","Potential"),
                 ("Open","Open"),
                 ("Closed","Closed")) )
    funding_type = models.CharField(max_length=50,       
              choices=(("COM","Commercail"),
                 ("NC","NERC NC"),
                 ("RP","NERC RP"),
                 ("RM","NERC RM"),
                 ("EU","European")) )

    def __unicode__(self):
        return self.title

class Allocation(models.Model):
    person =  models.ForeignKey(Person)
    person =  models.ForeignKey(Code)
    month = models.DateField()
    value = models.FloatField()

