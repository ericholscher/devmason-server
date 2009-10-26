import tagging
from django.db import models
from django.contrib.auth.models import User
from .fields import JSONField

class Project(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User, related_name='projects', blank=True, null=True)
    
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('project_detail', [self.slug])

class Build(models.Model):
    project = models.ForeignKey(Project, related_name='builds')
    success = models.BooleanField()
    started = models.DateTimeField()
    finished = models.DateTimeField()
    host = models.CharField(max_length=250)
    arch = models.CharField(max_length=250)
    user = models.ForeignKey(User, blank=True, null=True, related_name='builds')
    extra_info = JSONField()
    
    class Meta:
        ordering = ['-finished']

    def __unicode__(self):
        return u"Build %s for %s" % (self.pk, self.project)
        
    @models.permalink
    def get_absolute_url(self):
        return ('build_detail', [self.project.slug, self.pk])

tagging.register(Build)

class BuildStep(models.Model):
    build = models.ForeignKey(Build, related_name='steps')
    success = models.BooleanField()
    started = models.DateTimeField()
    finished = models.DateTimeField()
    name = models.CharField(max_length=250)
    output = models.TextField(blank=True)
    errout = models.TextField(blank=True)
    extra_info = JSONField()
    
    class Meta:
        ordering = ['build', 'started']
        
    def __unicode__(self):
        return "%s: %s" % (self.build, self.name)

