# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http.response import JsonResponse
from django.template.context import Context
from django.template.loader import get_template
from django.views.generic.base import TemplateView

from formtools_addons.wizard.views.wizardapi import WizardAPIView
from .forms import *


class TestWizardContainer(TemplateView):
    template_name = 'formtools_addons/accordeon_wizard_app.html'


def show_testform_2_conditional(wizard):
    cleaned_data = wizard.get_cleaned_data_for_step('page1|testform1') or {}
    return cleaned_data.get('sender', None) != 'dirk@gmail.com'


def show_testform_5_conditional(wizard):
    cleaned_data = wizard.get_cleaned_data_for_step('page1|testform2') or {}
    return cleaned_data.get('message', '') != 'test'


class TestWizard(WizardAPIView):
    storage_name = 'formtools.wizard.storage.session.SessionStorage'

    form_list = [
        ('page1', (
            ('testform1', TestForm1),
            ('testform2', TestForm2),
            ('testform3', TestForm3),
        )),
        ('page2', (
            ('testform4', TestForm4),
            ('testform5', TestForm5),
        )),
    ]

    condition_dict = {
        'page1|testform2': show_testform_2_conditional,
        'page2|testform5': show_testform_5_conditional
    }

    templates = {
        'page1|testform1': 'testapp/testform1.html',
        'page1|testform2': 'testapp/testform2.html',
    }

    def render_form(self, step, form):
        template = get_template(self.templates.get(step, 'testapp/default_form.html'))

        context = Context()
        context['form'] = form

        return template.render(context)

    def done(self, form_list, **kwargs):
        """
        Wizard finish handler.
          The idea is to persist your data here
        """
        return JsonResponse({'next_url': '/next-page/'})
