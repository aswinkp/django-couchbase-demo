from __future__ import unicode_literals
from decimal import Decimal
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
DOC_TYPE_FIELD_NAME = "type"

CHANNEL_PUBLIC = 'public'

# Create your models here.
class CouchbaseModelError(Exception):
    pass

class CBModelNew(models.Model):
    class Meta:
        abstract = True

    uid_prefix = 'st'
    doc_type = None
    _serializer = Serializer()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.get_uid() == other.get_uid()

    def __init__(self, *args, **kwargs):
        self.channels = []
        self.uid = None
        self.rev = None
        if 'uid_prefix' in kwargs:
            self.uid_prefix = kwargs['uid_prefix']
            del kwargs['uid_prefix']

        if 'uid' in kwargs:
            self.uid = kwargs['uid']
            del kwargs['uid']

        clean_kwargs = self.__clean_kwargs(kwargs)
        # we never pass args because we never use them
        super(CBModelNew, self).__init__(**clean_kwargs)

        if len(args) == 1:
            v = args[0]
            if isinstance(v, string_types):
                self.load(v)

    def get_uid(self):
        if self.is_new():
            pf = ShortUUIDField()
            self.uid = self.uid_prefix + '::' + pf.create_uuid()
        return self.uid

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

        data_dict = self.to_dict()
        if hasattr(self, 'rev') and self.rev:
            data_dict['_rev'] = self.rev
        if hasattr(self, 'rev') and self.rev:
            data_dict['_rev'] = self.rev
        if self.is_new():
            self.db.add(self.get_uid(), data_dict)
        else:
            self.db.set(self.get_uid(), data_dict)

    # for saving
    def to_dict(self):
        d = model_to_dict(self)
        tastyjson = self._serializer.to_json(d)
        d = self._serializer.from_json(tastyjson)

        d[DOC_TYPE_FIELD_NAME] = self.get_doc_type()
        d['uid'] = self.get_uid()
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
        if 'uid' in dict_payload.keys():
            self.uid = dict_payload['uid']

    def from_row(self, row):
        self.from_dict(row.value)
        self.uid = row.key

    def load(self, uid):
        try:
            doc = self.db.get(uid)
            self.from_row(doc)
        except:
            raise NotFoundError

    def delete(self):
        try:
            self.db.remove(self.uid)
        except NotFoundError:
            return HttpResponseNotFound

    def to_dict_nested(self, key, parent_dict):
        parent_dict[key] = getattr(self, key).to_dict()
        return parent_dict

    def to_dict_nested_list(self, key, parent_dict):
        parent_dict[key] = []
        for item in getattr(self, key):
            parent_dict[key].append(item.to_dict())
        return parent_dict

    def to_dict_reference(self, key, nested_klass, parent_dict):
        if key in parent_dict.keys():
            item = nested_klass()

        pass

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
        return not hasattr(self, 'uid') or not self.uid

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



    def from_sync_gateway_row(self, row):
        if 'error' in row:
            raise sync_gateway.SyncGatewayException(row)
        self.from_dict(row['doc'])
        self.uid = row['id']
        self.rev = row['value']['rev']
        # self.doc_type = row['doc']['doc_type']

    def to_json(self):
        d = self.to_dict()
        return self._serializer.to_json(d)

    def get_doc_type(self):
        if self.doc_type:
            return self.doc_type
        return self.__class__.__name__.lower()

    def append_channel(self, channel):
        self.append_to_references_list(CHANNELS_FIELD_NAME, channel)

    def clear_channels(self):
        self.channels = []

    def __unicode__(self):
        return u'%s: %s' % (self.uid, self.to_json())

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

    def load(self, uid):
        raise CouchbaseModelError('this object is not supposed to be loaded, it is nested')


#
# class CBNoSync(CouchbaseModel):
#
#     # def db(self):
#     #     return Bucket('couchbase://'+self.server+'/'+self.bkt)
#
#     def get_uid(self):
#         if self.is_new():
#             pf = ShortUUIDField()
#             self.uid = self.uid_prefix + '::' + pf.create_uuid()
#         return self.uid
#
#     def save(self, *args, **kwargs):
#         self.updated = timezone.now()
#         if not hasattr(self, 'created') or self.created is None:
#             self.created = self.updated
#
#         # save files
#         for field in self._meta.fields:
#             if isinstance(field, FileField):
#                 file_field = getattr(self, field.name)
#
#                 if not file_field._committed:
#                     file_field.save(file_field.name, file_field, False)
#
#         data_dict = self.to_dict()
#         if hasattr(self, 'rev') and self.rev:
#             data_dict['_rev'] = self.rev
#         if hasattr(self, 'rev') and self.rev:
#             data_dict['_rev'] = self.rev
#         if self.is_new():
#             self.db.add(self.get_uid(), data_dict)
#         else:
#             self.db.set(self.get_uid(), data_dict)
#
#     #for saving
#     def to_dict(self):
#         d = model_to_dict(self)
#         tastyjson = self._serializer.to_json(d)
#         d = self._serializer.from_json(tastyjson)
#
#         d[DOC_TYPE_FIELD_NAME] = self.get_doc_type()
#         d['uid'] = self.get_uid()
#         if 'cbnosync_ptr' in d: del d['cbnosync_ptr']
#         if 'channels' in d: del d['channels']
#         if 'csrfmiddlewaretoken' in d: del d['csrfmiddlewaretoken']
#         if 'st_deleted' in d: del d['st_deleted']
#         del d['id']
#         for field in self._meta.fields:
#             if isinstance(field, DateTimeField):
#                 d[field.name] = self._string_from_date(field.name)
#         return d
#
#     def from_dict(self, dict_payload, embeded_key=[]):
#         for field in self._meta.fields:
#             if field.name not in dict_payload:
#                 continue
#             if field.name in embeded_key:
#                 continue
#             if isinstance(field, DateTimeField):
#                 self._date_from_string(field.name, dict_payload.get(field.name))
#             elif isinstance(field, DecimalField):
#                 self._decimal_from_string(field.name, dict_payload.get(field.name))
#             elif field.name in dict_payload:
#                 setattr(self, field.name, dict_payload[field.name])
#         if 'uid' in dict_payload.keys():
#             self.uid = dict_payload['uid']
#
#     def from_row(self, row):
#         self.from_dict(row.value)
#         self.uid = row.key
#
#     def load(self, uid):
#         try:
#             doc = self.db.get(uid)
#             self.from_row(doc)
#         except:
#             raise NotFoundError
#
#     def delete(self):
#         try:
#             self.db.remove(self.uid)
#         except NotFoundError:
#             return HttpResponseNotFound
#
#     def to_dict_nested(self, key, parent_dict):
#         parent_dict[key] = getattr(self, key).to_dict()
#         return parent_dict
#
#
#     def to_dict_nested_list(self, key, parent_dict):
#         parent_dict[key] = []
#         for item in getattr(self, key):
#             parent_dict[key].append(item.to_dict())
#         return parent_dict
#
#     def to_dict_reference(self, key, nested_klass, parent_dict):
#         if key in parent_dict.keys():
#             item = nested_klass()
#
#         pass
#
#
#     def from_dict_nested(self, key, nested_klass, dict_payload):
#         if key in dict_payload.keys():
#             item = nested_klass()
#             item.from_dict(dict_payload[key])
#             nested_list = item
#             setattr(self, key, nested_list)
#
#     def from_dict_nested_list(self, key, nested_klass, dict_payload):
#         setattr(self, key, [])
#         nested_list = getattr(self, key)
#         if key in dict_payload.keys():
#             for d in dict_payload[key]:
#                 item = nested_klass()
#                 item.from_dict(d)
#                 nested_list.append(item)
#
#
# class CBNestedNoSync(CBNoSync):
#     class Meta:
#         abstract = True
#
#     def __init__(self, *args, **kwargs):
#         super(CBNestedNoSync, self).__init__(**kwargs)
#         delattr(self, 'created')
#         delattr(self, 'updated')
#
#     def save(self, *args, **kwargs):
#         raise CouchbaseModelError('this object is not supposed to be saved, it is nested')
#
#     def load(self, uid):
#         raise CouchbaseModelError('this object is not supposed to be loaded, it is nested')
