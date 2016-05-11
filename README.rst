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

Quickstart
----------

Install formtools-addons::

    pip install django-formtools-addons

Then use it in a project::

    # Every *WizardView that can be imported is an equivalent of a builtin *WizardView in Django Formtools
    from formtools_addons import (SessionMultipleFormWizardView, CookieMultipleFormWizardView,
                                  NamedUrlSessionMultipleFormWizardView, NamedUrlCookieMultipleFormWizardView,
                                  MultipleFormWizardView, NamedUrlMultipleFormWizardView)

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

