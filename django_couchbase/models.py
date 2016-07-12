from __future__ import unicode_literals
from decimal import Decimal

from djangotoolbox.fields import ListField
from six import string_types
import logging
from django.utils import timezone, dateparse
from tastypie.serializers import Serializer

logger = logging.getLogger(__name__)

import couchbase
from django.db import models
from django.forms.models import model_to_dict
from django.http import HttpResponseNotFound
from django_cbtools import sync_gateway
from django.db import models
from django.utils import timezone
from django.db.models.fields.files import FileField
from couchbase.bucket import Bucket, NotFoundError
from django_extensions.db.fields import ShortUUIDField
from django.db.models.fields import DateTimeField, DecimalField
#from django_cbtools.models import CouchbaseModel, CouchbaseModelError

from django_couchbase.fields import ModelReferenceField

CHANNELS_FIELD_NAME = "channels"
DOC_TYPE_FIELD_NAME = "doc_type"

CHANNEL_PUBLIC = 'public'

# Create your models here.
class CouchbaseModelError(Exception):
    pass

class CBModelNew(models.Model):
    class Meta:
        abstract = True

    id_prefix = 'st'
    doc_type = None
    _serializer = Serializer()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.get_id() == other.get_id()

    def __init__(self, *args, **kwargs):
        self.channels = []
        self.id = None
        self.rev = None
        if 'id_prefix' in kwargs:
            self.id_prefix = kwargs['id_prefix']
            del kwargs['id_prefix']

        if 'id' in kwargs:
            self.id = kwargs['id']
            del kwargs['id']

        clean_kwargs = self.__clean_kwargs(kwargs)
        # we never pass args because we never use them
        super(CBModelNew, self).__init__(**clean_kwargs)

        if len(args) == 1:
            v = args[0]
            if isinstance(v, string_types):
                self.load(v)

    def get_id(self):
        if self.is_new():
            pf = ShortUUIDField()
            self.id = self.id_prefix + '::' + pf.create_uuid()
        return self.id

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        if not hasattr(self, 'created') or self.created is None:
            self.created = self.updated

        # save files
        for field in self._meta.fields:
            if isinstance(field, FileField):
                file_field = getattr(self, field.name)

                if not file_field._committed:
                    file_field.save(file_field.name, file_field, False)

            if isinstance(field, ModelReferenceField):
                ref_obj = getattr(self, field.name)
                if ref_obj and not isinstance(ref_obj, unicode):
                    ref_obj.save()
                    setattr(self,field.name,ref_obj.id)

            if isinstance(field, ListField) and isinstance(field.item_field, ModelReferenceField ):
                ref_objs = getattr(self, field.name)
                id_arr = []
                if isinstance(ref_objs, list) and len(ref_objs):
                    for obj in ref_objs:
                        if obj and not isinstance(obj, unicode):
                            obj.save()
                            id_arr.append(obj.id)
                    setattr(self, field.name, id_arr)

        data_dict = self.to_dict()
        if self.is_new():
            self.db.add(self.get_id(), data_dict)
        else:
            self.db.set(self.get_id(), data_dict)

    # for saving
    def to_dict(self):
        d = model_to_dict(self)
        tastyjson = self._serializer.to_json(d)
        d = self._serializer.from_json(tastyjson)

        d[DOC_TYPE_FIELD_NAME] = self.get_doc_type()
        d['id'] = self.get_id()
        if 'cbnosync_ptr' in d: del d['cbnosync_ptr']
        if 'csrfmiddlewaretoken' in d: del d['csrfmiddlewaretoken']
        for field in self._meta.fields:
            if isinstance(field, DateTimeField):
                d[field.name] = self._string_from_date(field.name)
        return d

    def from_dict(self, dict_payload, embeded_key=[]):
        for field in self._meta.fields:
            if field.name not in dict_payload:
                continue
            if field.name in embeded_key:
                continue
            if isinstance(field, DateTimeField):
                self._date_from_string(field.name, dict_payload.get(field.name))
            elif isinstance(field, DecimalField):
                self._decimal_from_string(field.name, dict_payload.get(field.name))
            elif field.name in dict_payload:
                setattr(self, field.name, dict_payload[field.name])
        if 'id' in dict_payload.keys():
            self.id = dict_payload['id']

    def from_row(self, row):
        self.from_dict(row.value)
        self.id = row.key

    def load(self, id):
        try:
            doc = self.db.get(id)
            self.from_row(doc)
        except:
            raise NotFoundError

    def delete(self):
        try:
            self.db.remove(self.id)
        except NotFoundError:
            return HttpResponseNotFound

    def load_related(self,related_attr, related_klass):
        id = getattr(self, related_attr)
        return related_klass(id)

    def load_related_list(self,related_attr, related_klass):
        ids = getattr(self, related_attr)
        objs = []
        for id in ids:
            objs.append(related_klass(id))
        return objs

    def to_dict_nested(self, key, parent_dict):
        parent_dict[key] = getattr(self, key).to_dict()
        return parent_dict

    def to_dict_nested_list(self, key, parent_dict):
        parent_dict[key] = []
        for item in getattr(self, key):
            parent_dict[key].append(item.to_dict())
        return parent_dict

    def from_dict_nested(self, key, nested_klass, dict_payload):
        if key in dict_payload.keys():
            item = nested_klass()
            item.from_dict(dict_payload[key])
            nested_list = item
            setattr(self, key, nested_list)

    def from_dict_nested_list(self, key, nested_klass, dict_payload):
        setattr(self, key, [])
        nested_list = getattr(self, key)
        if key in dict_payload.keys():
            for d in dict_payload[key]:
                item = nested_klass()
                item.from_dict(d)
                nested_list.append(item)

    def append_to_references_list(self, key, value):
        v = getattr(self, key, [])

        if not isinstance(v, list):
            v = []

        if value not in v:
            v.append(value)

        setattr(self, key, v)

    def get_references_list(self, key):
        v = getattr(self, key, [])

        if not isinstance(v, list):
            v = []

        return v

    def delete_from_references_list(self, key, value):
        v = getattr(self, key, [])

        if not isinstance(v, list):
            v = []

        if value in v:
            v.remove(value)

        setattr(self, key, v)

    def is_new(self):
        return not hasattr(self, 'id') or not self.id

    def from_json(self, json_payload):
        d = self._serializer.from_json(json_payload)
        self.from_dict(d)

    def _date_from_string(self, field_name, val):
        try:
            setattr(self, field_name, dateparse.parse_datetime(val))
        except Exception as e:
            setattr(self, field_name, val)
            logger.warning('can not parse date (raw value used) %s: %s', field_name, e)

    def _string_from_date(self, field_name):
        try:
            return getattr(self, field_name).isoformat()
        except:
            return None

    def _decimal_from_string(self, field_name, val):
        try:
            setattr(self, field_name, Decimal(val))
        except Exception as e:
            setattr(self, field_name, val)
            logger.warning('can not parse decimal (raw value used) %s: %s', field_name, e)

    def to_json(self):
        d = self.to_dict()
        return self._serializer.to_json(d)

    def get_doc_type(self):
        if self.doc_type:
            return self.doc_type
        return self.__class__.__name__.lower()


    def __unicode__(self):
        return u'%s: %s' % (self.id, self.to_json())

    def __clean_kwargs(self, data):
        common = set.intersection(
            {f.name for f in self._meta.get_fields()},
            data.keys(),
        )
        return {fname: data[fname] for fname in common}


class CouchbaseNestedModelNew(CBModelNew):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        raise CouchbaseModelError('this object is not supposed to be saved, it is nested')

    def load(self, id):
        raise CouchbaseModelError('this object is not supposed to be loaded, it is nested')
