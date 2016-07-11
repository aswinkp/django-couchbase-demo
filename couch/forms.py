from django import forms
from django.forms import ModelForm
from .models import CBArticle

class ArticleForm(ModelForm):
    class Meta:
        model = CBArticle
        fields = ['title', 'year_published', 'is_draft' ]

class AddressForm(forms.Form):
    name = forms.CharField(max_length=20,min_length=2)
    address1 = forms.CharField(max_length=40)
    address2 = forms.CharField(max_length=40)
    city = forms.CharField(max_length=20)
    pin = forms.CharField(max_length=10)


class OrderItemForm(forms.Form):
    product = forms.CharField(max_length=20, min_length=2, strip=True, label="Product Name")
    qty = forms.DecimalField(decimal_places=2,label="Qty")

class ProductForm(forms.Form):
    name = forms.CharField(max_length=20, min_length=2, label="Product Name")
    description = forms.CharField(max_length=20, min_length=2, label="description")
    rate = forms.CharField(max_length=20, min_length=2, label="rate")

class OrderForm(forms.Form):
    date = forms.DateField()
    total = forms.DecimalField(decimal_places=2,label="Total")