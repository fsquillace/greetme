from django.db import models
from djangofb.models import FacebookUser


class Language(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=20)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Greeting(models.Model):
    GENDER_CHOICES = (
        (u'M', u'Male'),
        (u'F', u'Female'),
    )
    gender = models.CharField(max_length=2, null=True, blank=True, choices=GENDER_CHOICES)
    lang = models.ForeignKey(Language)
     # Define the user optional when we want to create default greetings
    users = models.ManyToManyField(FacebookUser, null=True, blank=True)
    greeting = models.CharField(max_length=512)
    default = models.BooleanField()
    
    
    def __unicode__(self):
        return self.greeting
    
    
class DefaultLanguage(models.Model):
    user = models.ForeignKey(FacebookUser, primary_key=True)
    lang = models.ForeignKey(Language)
    def __unicode__(self):
        return str(self.user.uid) +' - '+ str(self.lang.name)
        
    
class ExcludedFriend(models.Model):
    user = models.ForeignKey(FacebookUser)
    friend_id = models.CharField(max_length=50, null=False, blank=False)
    
    def __unicode__(self):
        return str(self.user.uid) +' -> '+ str(self.friend_id)
    