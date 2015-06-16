from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=100, help_text="Titles are limited to 100 characters.")
    description = models.TextField(blank=True)
