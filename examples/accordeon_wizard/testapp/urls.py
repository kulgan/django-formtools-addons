# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.views.decorators.csrf import ensure_csrf_cookie

from .views import TestWizard, TestWizardContainer


test_wizard_container = TestWizardContainer.as_view()
test_wizard = TestWizard.as_view(url_name='testapp:accordeon_wizard_step')

urlpatterns = [
    url(r'^(?P<step>.+)/(?P<substep>.+)/$', ensure_csrf_cookie(test_wizard), name='accordeon_wizard_step'),
    url(r'^(?P<step>.+)/$', ensure_csrf_cookie(test_wizard), name='accordeon_wizard_step'),
    url(r'^$', test_wizard_container, name='accordeon_wizard'),
]
