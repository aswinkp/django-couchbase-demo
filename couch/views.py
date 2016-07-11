from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from couchbase.bucket import Bucket
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from couchbase.exceptions import KeyExistsError, NotFoundError
from django_extensions.db.fields import ShortUUIDField
from couchbase.views.params import Query
from couchbase.views.iterator import RowProcessor
import json
import jsonstruct
from couchbase.n1ql import CONSISTENCY_REQUEST
from couchbase.n1ql import N1QLQuery

from couch.models import Address, CBArticle
from .forms import ArticleForm,AddressForm
# Create your views here.

CONNSTR = 'couchbase://127.0.0.1:8091/default'

def connect_db():
    return Bucket(CONNSTR)

db = connect_db()

def form(request):
    pass

def invoice(request):
    pass

def invoice_create(request):
    pass

def invoice_show(request):
    pass

def invoice_update(request):
    pass

def invoice_delete(request):
    pass

def address(request):
    arr = []
    q = N1QLQuery('SELECT *, meta() AS meta FROM default WHERE type = "address"')
    q.consistency = CONSISTENCY_REQUEST
    for row in db.n1ql_query(q):
        arr.append(row)
    return render(request,'address/list.html', {'list': arr})

def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = request.POST
            mutable = request.POST._mutable
            request.POST._mutable = True
            address['type'] = 'address'
            if 'csrfmiddlewaretoken' in address:
                del address['csrfmiddlewaretoken']
            request.POST._mutable = mutable
            if not address:
                return HttpResponseNotFound
            pf = ShortUUIDField()
            id = address['name'] + '_' + pf.create_uuid()
            try:
                db.add(id, address)
                return HttpResponseRedirect(reverse('address_list', kwargs={}))

            except KeyExistsError:
                return HttpResponseNotFound
    else:
        form = AddressForm()
    return render(request, 'address/form_add.html', {'form': form})

def address_show(request,id):
    doc = db.get(id, quiet=True)
    if not doc.success:
        return HttpResponseNotFound
    return render(request, 'address/show.html', {'id':id, 'name':doc.value['name'],'doc':doc})

def address_update(request, id):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = request.POST
            mutable = request.POST._mutable
            request.POST._mutable = True
            address['type'] = 'address'
            if 'csrfmiddlewaretoken' in address:
                del address['csrfmiddlewaretoken']
            request.POST._mutable = mutable
            if not address:
                return HttpResponseNotFound
            try:
                db.set(id, address)
                return HttpResponseRedirect(reverse('address_list', kwargs={}))

            except KeyExistsError:
                return HttpResponseNotFound
    else:
        doc = db.get(id, quiet=True)
        if not doc.success:
            return HttpResponseNotFound
        form = AddressForm(Address(id=id, name=doc.value['name'], doc=doc))
    return render(request, 'address/form_update.html', {'form': form, 'id': id})

def address_delete(request, id):
    try:
        db.remove(id)
        return redirect(reverse('address_list', args =[]))

    except NotFoundError:
        return HttpResponseNotFound

def article(request):
    arr = []
    q = N1QLQuery('SELECT *, meta() AS meta FROM default WHERE type = "article"')
    q.consistency = CONSISTENCY_REQUEST
    for row in db.n1ql_query(q):
        arr.append(row)
    return render(request,'article/list.html', {'list': arr})


def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = request.POST
            if not article:
                return HttpResponseNotFound
            try:
                form.save()
                return HttpResponseRedirect(reverse('article_list', kwargs={}))

            except KeyExistsError:
                return HttpResponseNotFound
    else:
        form = ArticleForm()
    return render(request, 'article/form_add.html', {'form': form})

def article_show(request,id):
    doc = CBArticle(id)
    return render(request, 'article/show.html', {'id':id, 'doc':doc})

def article_update(request, id):
    if request.method == 'POST':
        instance = CBArticle(id)
        form = ArticleForm(request.POST or None, instance=instance)
        if form.is_valid():
            address = request.POST
            if not address:
                return HttpResponseNotFound
            try:
                form.save()
                return HttpResponseRedirect(reverse('article_list', kwargs={}))

            except KeyExistsError:
                return HttpResponseNotFound
    else:
        form = ArticleForm(instance = CBArticle(id))
    return render(request, 'article/form_update.html', {'form': form, 'id': id})

def article_delete(request, id):
    try:
        db.remove(id)
        return redirect(reverse('article_list', args =[]))

    except NotFoundError:
        return HttpResponseNotFound