from __future__ import unicode_literals

from django.db import models
from django_couchbase.models import CBModel,CBNestedModel
from django_couchbase.fields import PartialReferenceField, ModelReferenceField


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
    bucket = "MAIN_BUCKET"
    name = models.CharField(max_length=45, null=True, blank=True)
    age = models.IntegerField(default=2014)

class CBArticle(CBModel):
    class Meta:
        abstract = True

    doc_type = 'article'
    id_prefix = 'atl'

    bucket = "MAIN_BUCKET"

    title = models.CharField(max_length=45, null=True, blank=True)
    year_published = models.IntegerField(default=2014)
    is_draft = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    # authors = ListField(EmbeddedModelField(CBAuthor))
    # author= EmbeddedModelField(CBAuthor)
    # author = ModelReferenceField(CBAuthorRef)
    authors = ListField(ModelReferenceField("CBAuthorRef"))

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

class Article(CBNestedModel):
    class Meta:
        abstract = True

    doc_type = 'article'
    id_prefix = 'art'

    title = models.CharField(max_length=45, null=True, blank=True)

class Blog(CBNestedModel):
    class Meta:
        abstract = True

    doc_type = 'blog'
    id_prefix = 'blg'

    url = models.CharField(max_length=45, null=True, blank=True)
    articles = ListField(EmbeddedModelField(Article))

class Publisher(CBModel):
    class Meta:
        abstract = True

    doc_type = 'publisher'
    id_prefix = 'pub'
    bucket = "MAIN_BUCKET"

    name = models.CharField(max_length=45, null=True, blank=True)

class Book(CBModel):
    class Meta:
        abstract = True

    doc_type = 'book'
    id_prefix = 'bk'
    bucket = "MAIN_BUCKET"

    name = models.CharField(max_length=45, null=True, blank=True)
    pages = models.IntegerField()
    publisher = ModelReferenceField(Publisher)

class Address(CBModel):
    class Meta:
        abstract = True

    doc_type = 'address'
    id_prefix = 'addr'
    bucket = "MAIN_BUCKET"

    street = models.CharField(max_length=45, null=True, blank=True)
    city = models.CharField(max_length=45, null=True, blank=True)

class Author(CBModel):
    class Meta:
        abstract = True

    doc_type = 'author'
    id_prefix = 'atr'
    bucket = "MAIN_BUCKET"

    name = models.CharField(max_length=45, null=True, blank=True)
    blog = EmbeddedModelField(Blog)
    books = ListField(ModelReferenceField(Book))
    address = ModelReferenceField(Address)

