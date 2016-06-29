import os
import tempfile

from django import forms
from django.core.files.storage import FileSystemStorage
from django.forms.formsets import formset_factory
from django.shortcuts import redirect

from formtools_addons.wizard.views.wizardapi import WizardAPIView

temp_storage_location = tempfile.mkdtemp(dir=os.environ.get('DJANGO_TEST_TEMP_DIR'))
temp_storage = FileSystemStorage(location=temp_storage_location)


class Page1(forms.Form):
    name = forms.CharField(max_length=100)
    thirsty = forms.BooleanField()


class Page2(forms.Form):
    address1 = forms.CharField(max_length=100)
    address2 = forms.CharField(max_length=100)
    # file1 = forms.FileField()


class Page3(forms.Form):
    random_crap = forms.CharField(max_length=100)

Page4 = formset_factory(Page3, extra=2)


class ContactWizardAPIView(WizardAPIView):
    storage_name = 'formtools.wizard.storage.session.SessionStorage'
    form_list = (Page1, Page2)

    def done(self, form_list, **kwargs):
        return redirect('/next-page/')


class NamedContactWizardAPIView(WizardAPIView):
    storage_name = 'formtools.wizard.storage.session.SessionStorage'
    form_list = (
        ('page1', Page1),
        ('page2', Page2)
    )

    def done(self, form_list, **kwargs):
        return redirect('/next-page/')


class SubStepContactWizardAPIView(WizardAPIView):
    storage_name = 'formtools.wizard.storage.session.SessionStorage'
    form_list = (
        (
            ('step1.1', Page1),
            ('step1.2', Page2)
        ),
        (
            ('step2.1', Page3),
        )
    )

    def done(self, form_list, **kwargs):
        return redirect('/next-page/')


class NamedSubStepContactWizardAPIView(WizardAPIView):
    storage_name = 'formtools.wizard.storage.session.SessionStorage'
    form_list = (
        ('page1', (
            ('step1.1', Page1),
            ('step1.2', Page2)
        )),
        ('page2', (
            ('step2.1', Page3),
        ))
    )

    def done(self, form_list, **kwargs):
        return redirect('/next-page/')


def show_page2_step2(wizard):
    data = wizard.get_cleaned_data_for_step('page1|step1.1') or {}
    return data.get('name', '') != 'hurray'


class ComplexNamedSubStepContactWizardAPIView(WizardAPIView):
    storage_name = 'formtools.wizard.storage.session.SessionStorage'
    form_list = (
        ('page1', (
            ('step1.1', Page1),
            ('step1.2', Page2),
            ('step1.3', Page3)
        )),
        ('page2', (
            ('step2.1', Page1),
            ('step2.2', Page2),
        ))
    )

    condition_dict = {
        'page2|step2.2': show_page2_step2
    }

    def done(self, form_list, **kwargs):
        return redirect('/next-page/')
