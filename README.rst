=======================
django-formtools-addons
=======================

.. image:: https://badge.fury.io/py/django-formtools-addons.png
    :target: https://badge.fury.io/py/django-formtools-addons

.. image:: https://travis-ci.org/vikingco/django-formtools-addons.png?branch=master
    :target: https://travis-ci.org/dirkmoors/django-formtools-addons

'Addons for Django Formtools'

Features
--------

* Add multiple forms to a single WizardView step (MultipleFormWizardView and subclasses)
* Use form wizard via JSON web API (WizardAPIView)

Quickstart
----------

Install formtools-addons::

    pip install django-formtools-addons

Then use it in a project::

    # Every *MultipleForm* WizardView that can be imported is an equivalent of a builtin *WizardView in Django Formtools
    from formtools_addons import (SessionMultipleFormWizardView, CookieMultipleFormWizardView,
                                  NamedUrlSessionMultipleFormWizardView, NamedUrlCookieMultipleFormWizardView,
                                  MultipleFormWizardView, NamedUrlMultipleFormWizardView)

    # The WizardAPIView is also based on the builtin WizardView, but does not have the classic request-response cycle,
    # since it exposes a JSON API
    from formtools_addons import WizardAPIView


WizardAPIView: Example use
--------------------------

.. code-block:: python

    from __future__ import unicode_literals

    from formtools_addons import WizardAPIView

    from .forms import Form1, Form2, Form3, Form4


    def show_substep_4(wizard):
        cleaned_data = wizard.get_cleaned_data_for_step('my-page1|my-substep-1') or {}
        return cleaned_data.get('some_field', None) != 'some_value'


    class TestWizardAPIView(WizardAPIView):
        form_list = [
            ("my-page1", (
                ("my-substep-1", Form1),
                ("my-substep-2", Form2),
                ("my-substep-3", Form3)
            )),
            ("my-page2", (
                ('my-substep-4', Form4),
            ))
        ]

        condition_dict = {
            'my-page2|my-substep-4':   show_substep_4,
        }

        form_templates = {
            "my-page1|my-substep-1": 'demo/page1_substep1.html',
            "my-page2|my-substep-4": 'demo/page2_substep4.html',
        }

        preview_templates = {
            "my-page1|my-substep-1": 'demo/page1_substep1_preview.html',
            "my-page2|my-substep-4": 'demo/page2_substep4_preview.html',
        }

        def render_form(self, step, form):
            # Get preview template url
            template_url = self.form_templates.get(step, None)
            if template_url is None:
                data = form.cleaned_data
                return '<p>NO TEMPLATE: STEP: %s, DATA: %s</p>' % (
                    step, json.dumps(data, default=self.json_encoder.default))

             # Load template
            template = get_template(template_url)

            # Create context
            context = Context()
            context['form'] = form

            return template.render(context)

        def render_preview(self, step, form):
            if not form.is_bound or not form.is_valid():
                return

            # Get preview template url
            template_url = self.preview_templates.get(step, None)
            if template_url is None:
                data = form.cleaned_data
                return '<p>NO TEMPLATE: STEP: %s, DATA: %s</p>' % (
                    step, json.dumps(data, default=self.json_encoder.default))

            # Load template
            template = get_template(template_url)

            # Create context
            context = Context()
            context['data'] = form.cleaned_data if (form.is_bound and form.is_valid()) else {}

            return template.render(context)

    ################################################################

    # testwizard/urls.py

    from __future__ import unicode_literals
    from django.conf.urls import url
    from django.views.decorators.csrf import ensure_csrf_cookie

    from .views import TestWizardAPIView

    test_wizard = TestWizardAPIView.as_view(url_name='wizard')

    urlpatterns = [
        # Registration Wizard API URL's
        url(r'^(?P<step>.+)/(?P<substep>.+)/$', ensure_csrf_cookie(test_wizard), name='wizard_step'),
        url(r'^(?P<step>.+)/$', ensure_csrf_cookie(test_wizard), name='wizard_step'),
    ]



MultipleFormWizardView: Example use
-----------------------------------

.. code-block:: python

    from __future__ import unicode_literals

    from django import forms
    from django.shortcuts import render_to_response

    from formtools_addons import SessionMultipleFormWizardView

    from .forms import Form1, Form2, Form3


    class Wizard(SessionMultipleFormWizardView):
        form_list = [
            ("start", Form1),
            ("user_info", (
                ('account', Form2),
                ('address', Form3)
            ))
        ]

        templates = {
            "start": 'demo/wizard-start.html',
            "user_info": 'demo/wizard-user_info.html'
        }

        def get_template_names(self):
            return [self.templates[self.steps.current]]

        def done(self, form_dict, **kwargs):
            result = {}

            for key in form_dict:
                form_collection = form_dict[key]
                if isinstance(form_collection, forms.Form):
                    result[key] = form_collection.cleaned_data
                elif isinstance(form_collection, dict):
                    result[key] = {}
                    for subkey in form_collection:
                        result[key][subkey] = form_collection[subkey].cleaned_data

            return render_to_response('demo/wizard-end.html', {
                'form_data': result,
            })

    ############################################################################################

    form = Wizard.as_view(form_list, instance_dict={
        'start': user,  # User model instance
        'user_info': {
            'account': Account.objects.get(user=user),
            'address': Address.objects.get(user=user),
        },
    })


Running Tests
--------------

::

    $ tox

