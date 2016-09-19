from __future__ import unicode_literals

from django.db import models
from django_couchbase.models import CBModel,CBNestedModel
from django_couchbase.fields import PartialReferenceField, ModelReferenceField
from couchbase.bucket import Bucket


from djangotoolbox.fields import ListField, EmbeddedModelField, DictField

class CBAuthor(CBNestedModel):
    class Meta:
        abstract = True

    doc_type = 'author'
    id_prefix = 'atr'

    name = models.CharField(max_length=45, null=True, blank=True)
    age = models.IntegerField(default=2014)

class CBAuthorRef(CBModel):
    class Meta:
        abstract = True

    doc_type = 'author'
    id_prefix = 'atr'
    db = Bucket('couchbase://127.0.0.1:8091/default')
    name = models.CharField(max_length=45, null=True, blank=True)
    age = models.IntegerField(default=2014)

class CBArticle(CBModel):
    class Meta:
        abstract = True

    doc_type = 'article'
    id_prefix = 'atl'
    db = Bucket('couchbase://127.0.0.1:8091/default')

    title = models.CharField(max_length=45, null=True, blank=True)
    year_published = models.IntegerField(default=2014)
    is_draft = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    # authors = ListField(EmbeddedModelField(CBAuthor))
    # author= EmbeddedModelField(CBAuthor)
    author = ModelReferenceField(CBAuthorRef)
    # authors = ListField(ModelReferenceField("CBAuthorRef"))

    # author = PartialReferenceField("CBAuthorRef")
    # author_name = models.CharField(max_length=45, null=True, blank=True)
    # author_age = models.IntegerField(default=2014)

    #for saving
    def to_dict(self):
        d = super(CBArticle, self).to_dict()
        # self.to_dict_reference('author', d)
        # self.to_dict_reference_list('authors', d)
        # self.to_dict_partial_reference('author', d, links={"author_name": "name","author_age":"age"})
        return d


