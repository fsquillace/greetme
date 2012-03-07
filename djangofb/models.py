from django.db import models

class FacebookUser(models.Model):
    uid = models.CharField(max_length=64) # Should be a primary key!!!
    aid = models.CharField(max_length=64) # Should be a primary key!!!
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    profile_url = models.CharField(max_length=255)
    access_token = models.CharField(max_length=128)
    username = models.CharField(max_length=255, null=True, blank=True, default='unknown')
    
    def __unicode__(self):
        return 'aid:'+ self.aid + ' - uid:' + self.uid + ' - ' + self.username
