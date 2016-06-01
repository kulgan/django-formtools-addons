# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms


class BaseForm(forms.Form):
    def is_valid(self):
        return super(BaseForm, self).is_valid()


class TestForm1(BaseForm):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()


class TestForm2(BaseForm):
    message = forms.CharField(widget=forms.Textarea)
    multivalue = forms.MultipleChoiceField(choices=[('testa', 'Test A'), ('testb', 'Test B')])


class TestForm3(BaseForm):
    field1 = forms.CharField(max_length=100)
    field2 = forms.CharField(max_length=100)


class TestForm4(BaseForm):
    field1 = forms.IntegerField()


class TestForm5(BaseForm):
    name = forms.ChoiceField(choices=[('test1', 'Test 1'), ('test2', 'Test 2')])
