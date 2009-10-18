from django.db import models

# Create your models here.

class Package(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name

class Client(models.Model):
    arch = models.CharField(max_length=200, blank=True, null=True)
    duration = models.FloatField( blank=True, null=True)
    host = models.CharField(max_length=200, blank=True, null=True)
    package = models.ForeignKey('Package', related_name='clients', blank=True, null=True)
    success = models.BooleanField()
    tags = models.ManyToManyField('Tag', related_name='clients', blank=True, null=True)
    tempdir = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return u"%s : %s : %s" % (self.host, self.arch, self.package)

class Result(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    client = models.ForeignKey(Client, related_name='results', blank=True, null=True)

    command = models.CharField(max_length=200, blank=True, null=True)
    out = models.CharField(max_length=200, blank=True, null=True)
    errout = models.CharField(max_length=200, blank=True, null=True)
    status = models.NullBooleanField()
    type = models.CharField(max_length=200, blank=True, null=True)
    version_type = models.CharField(max_length=200, blank=True, null=True)
    version_info = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.client.package, self.name)
