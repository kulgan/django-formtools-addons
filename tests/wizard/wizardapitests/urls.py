"""
This is a URLconf to be loaded by tests.py. Add any URLs needed for tests only.
"""

from django.conf.urls import url

from .forms import ContactWizardAPIView, NamedContactWizardAPIView, SubStepContactWizardAPIView, \
    NamedSubStepContactWizardAPIView, ComplexNamedSubStepContactWizardAPIView

test_wizard1 = ContactWizardAPIView.as_view(url_name='wizard_step')
test_wizard2 = NamedContactWizardAPIView.as_view(url_name='wizard_step')
test_wizard3 = SubStepContactWizardAPIView.as_view(url_name='wizard_step')
test_wizard4 = NamedSubStepContactWizardAPIView.as_view(url_name='wizard_step')
test_wizard5 = ComplexNamedSubStepContactWizardAPIView.as_view(url_name='wizard_step')


urlpatterns = [
    # Steps will be index ints
    url(r'^wizard/(?P<step>.+)/$', test_wizard1, name='wizard_step'),
    url(r'^wizard/$', test_wizard1, name='wizard'),

    # Steps will be (hopefully descriptive) strings
    url(r'^named-wizard/(?P<step>.+)/$', test_wizard2, name='named_wizard_step'),
    url(r'^named-wizard/$', test_wizard2, name='named_wizard'),

    # Steps will be index ints
    url(r'^substep-wizard/(?P<step>.+)/$', test_wizard3, name='substep_wizard_step'),
    url(r'^substep-wizard/$', test_wizard3, name='substep_wizard'),

    # Steps will be (hopefully descriptive) strings
    url(r'^named-substep-wizard/(?P<step>.+)/$', test_wizard4, name='named_substep_wizard_step'),
    url(r'^named-substep-wizard/$', test_wizard4, name='named_substep_wizard'),

    # Steps will be (hopefully descriptive) strings
    url(r'^complex-named-substep-wizard/(?P<step>.+)/(?P<substep>.+)/$', test_wizard5, name='complex_named_substep_wizard_step'),
    url(r'^complex-named-substep-wizard/(?P<step>.+)/$', test_wizard5, name='complex_named_substep_wizard_step'),
    url(r'^complex-named-substep-wizard/$', test_wizard5, name='complex_named_substep_wizard'),
]
