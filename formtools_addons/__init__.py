__version__ = '0.1.9'

from .wizard.views.multipleformwizard import (
    SessionMultipleFormWizardView, CookieMultipleFormWizardView,
    NamedUrlSessionMultipleFormWizardView, NamedUrlCookieMultipleFormWizardView,
    MultipleFormWizardView, NamedUrlMultipleFormWizardView)

from .wizard.views.wizardapi import WizardAPIView
