from __future__ import unicode_literals


from django.db import models
from django_couchbase.models import CBModelNew,CouchbaseNestedModelNew
from django_couchbase.fields import ModelReferenceField
from couchbase.bucket import Bucket


from djangotoolbox.fields import ListField,EmbeddedModelField, DictField

class CBArticle(CBModelNew):
    class Meta:
        abstract = True

    doc_type = 'article'
    uid_prefix = 'atl'
    server = '127.0.0.1:8091'
    bkt = 'default'
    db = Bucket('couchbase://127.0.0.1:8091/default')

    title = models.CharField(max_length=45, null=True, blank=True)
    year_published = models.IntegerField(default=2014)
    is_draft = models.BooleanField(default=True)
    authors = ListField(EmbeddedModelField("CBAuthor"))
    author= EmbeddedModelField("CBAuthor")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    atr_ref = ModelReferenceField("CBAuthor")

    #for saving
    def to_dict(self):
        d = super(CBArticle, self).to_dict()
        self.to_dict_nested('author', d)
        self.to_dict_nested_list('authors', d)

        return d

    #for loading
    def from_dict(self, dict_payload):
        self.from_dict_nested('author', CBAuthor, dict_payload)
        self.from_dict_nested_list('authors', CBAuthor, dict_payload)
        super(CBArticle, self).from_dict(dict_payload, ['authors','author'])

class CBAuthor(CouchbaseNestedModelNew):
    class Meta:
        abstract = True

    doc_type = 'author'
    uid_prefix = 'atr'
    server = '127.0.0.1:8091'
    bkt = 'default'

    name = models.CharField(max_length=45, null=True, blank=True)
    age = models.IntegerField(default=2014)


class Address(object):
    def __init__(self, name, _=None, id='', doc=None):
        self.id = id
        self.name = name

        if doc:
            self.doc = doc.value
        else:
            self.doc = None

    def get(self, name):
        if not self.doc:
            return ""
        return self.doc.get(name, "")

class Invoice(object):
    def __init__(self, name, _=None, id='', doc=None):
        self.id = id
        self.name = name

        if doc:
            self.doc = doc.value
        else:
            self.doc = None

    def get(self, name):
        if not self.doc:
            return ""
        return self.doc.get(name, "")