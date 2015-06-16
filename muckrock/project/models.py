from django.contrib.auth.models import User
from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=100, help_text='Titles are limited to 100 characters.')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images', blank=True, null=True)

    contributors = models.ManyToManyField(User, related_name='projects')

    def __unicode__(self):
        return self.title
