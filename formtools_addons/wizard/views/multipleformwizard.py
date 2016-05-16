# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import six
from collections import OrderedDict

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms import formsets
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from formtools.wizard.storage.exceptions import NoFileStorageConfigured
from formtools.wizard.views import ManagementForm, WizardView as BaseWizardView


class MultipleFormWizardView(BaseWizardView):
    template_name = 'formtools_addons/wizard/wizard_form.html'
    cleaned_data_in_context = False
    _form_list_factory = None

    @classmethod
    def get_initkwargs(cls, form_list=None, initial_dict=None,
            instance_dict=None, condition_dict=None, *args, **kwargs):
        """
        Creates a dict with all needed parameters for the form wizard instances.

        * `form_list` - is a list of forms, or a callable that returns a list of forms.
          The list entries can be single form classes, tuples of (`step_name`, `form_class`) or tuples
          of (`step_name`, {`form_name`: `form_class`}).
          If you pass a list of forms, the wizardview will convert the class list to
          (`zero_based_counter`, `form_class`). This is needed to access the
          form for a specific step.
        * `initial_dict` - contains a dictionary of initial data dictionaries.
          The key should be equal to the `step_name` in the `form_list` (or
          the str of the zero based counter - if no step_names added in the
          `form_list`)
        * `instance_dict` - contains a dictionary whose values are model
          instances if the step is based on a ``ModelForm`` and querysets if
          the step is based on a ``ModelFormSet``. The key should be equal to
          the `step_name` in the `form_list`. Same rules as for `initial_dict`
          apply.
        * `condition_dict` - contains a dictionary of boolean values or
          callables. If the value of for a specific `step_name` is callable it
          will be called with the wizardview instance as the only argument.
          If the return value is true, the step's form will be used.
        """

        kwargs.update({
            'initial_dict': initial_dict or kwargs.pop('initial_dict',
                getattr(cls, 'initial_dict', None)) or {},
            'instance_dict': instance_dict or kwargs.pop('instance_dict',
                getattr(cls, 'instance_dict', None)) or {},
            'condition_dict': condition_dict or kwargs.pop('condition_dict',
                getattr(cls, 'condition_dict', None)) or {}
        })

        form_list = form_list or kwargs.pop('form_list', getattr(cls, 'form_list', None)) or []

        if isinstance(form_list, six.string_types) or callable(form_list):
            kwargs['form_list'] = []  # The actual form list will be loaded later
            kwargs['_form_list_factory'] = form_list
            return kwargs

        # build the kwargs for the wizardview instances
        kwargs['form_list'] = cls.compute_form_list(form_list, *args, **kwargs)
        return kwargs

    @classmethod
    def compute_form_list(cls, form_list, *args, **kwargs):
        computed_form_list = OrderedDict()

        assert len(form_list) > 0, 'at least one form is needed'

        # walk through the passed form list
        for i, form in enumerate(form_list):
            if isinstance(form, (list, tuple)):
                # if the element is a tuple, add the tuple to the new created
                # sorted dictionary.

                (step_name, form) = form
                if isinstance(form, dict):
                    form_mapping = form
                    computed_form_list[six.text_type(step_name)] = form_mapping
                elif isinstance(form, (list, tuple)):
                    form_mapping = OrderedDict(form)
                    computed_form_list[six.text_type(step_name)] = form_mapping
                elif issubclass(form, (forms.Form, forms.BaseForm, forms.BaseFormSet)):
                    computed_form_list[six.text_type(step_name)] = form
            else:
                # if not, add the form with a zero based counter as unicode
                computed_form_list[six.text_type(i)] = form

        # walk through the new created list of forms
        for form in six.itervalues(computed_form_list):
            form_collection = []
            if isinstance(form, dict):
                form_collection = form.values()
            elif issubclass(form, formsets.BaseFormSet):
                # if the element is based on BaseFormSet (FormSet/ModelFormSet)
                # we need to override the form variable.
                form = form.form
                form_collection = [form]

            for form in form_collection:
                # must test for BaseFormSet again in case form_collection
                # is a dict containing one.
                if issubclass(form, formsets.BaseFormSet):
                    # if the element is based on BaseFormSet (FormSet or
                    # ModelFormSet) we need to override the form variable.
                    form = form.form
                # check if any form contains a FileField, if yes, we need a
                # file_storage added to the wizardview (by subclassing).
                for field in six.itervalues(form.base_fields):
                    if (isinstance(field, forms.FileField) and
                            not hasattr(cls, 'file_storage')):
                        raise NoFileStorageConfigured(
                            "You need to define 'file_storage' in your "
                            "wizard view in order to handle file uploads.")

        return computed_form_list


    def render(self, forms=None, **kwargs):
        """
        Returns a ``HttpResponse`` containing all needed context data.
        """
        forms = forms or self.get_forms()
        context = self.get_context_data(forms=forms, **kwargs)
        return self.render_to_response(context)

    def render_next_step(self, form, **kwargs):
        """
        This method gets called when the next step/form should be rendered.
        `form` contains the last/current form.
        """
        # get the form instance based on the data from the storage backend
        # (if available).
        next_step = self.steps.next
        new_forms = self.get_forms(next_step,
            data=self.storage.get_step_data(next_step),
            files=self.storage.get_step_files(next_step))

        # change the stored current step
        self.storage.current_step = next_step
        return self.render(new_forms, **kwargs)

    def render_goto_step(self, goto_step, **kwargs):
        """
        This method gets called when the current step has to be changed.
        `goto_step` contains the requested step to go to.
        """
        self.storage.current_step = goto_step
        forms = self.get_forms(
            data=self.storage.get_step_data(self.steps.current),
            files=self.storage.get_step_files(self.steps.current))
        return self.render(forms)

    def render_done(self, form, **kwargs):
        """
        This method gets called when all forms passed. The method should also
        re-validate all steps to prevent manipulation. If any form fails to
        validate, `render_revalidation_failure` should get called.
        If everything is fine call `done`.
        """
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_objs = self.get_forms(step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key))
            final_forms[form_key] = []
            for form_obj in form_objs:
                if not form_obj.is_valid():
                    return self.render_revalidation_failure(form_key, form_obj, **kwargs)
                final_forms[form_key].append(form_obj)

        result_forms = {}
        result_forms_dict = {}
        for form_key in final_forms:
            formcollection = final_forms[form_key]
            result_forms_dict[form_key] = {}
            for form in formcollection:
                if hasattr(form, '_tag'):
                    result_forms_dict[form_key][form._tag] = form

            if len(formcollection) == 1:
                result_forms[form_key] = formcollection[0]
            elif len(formcollection) > 1:
                # We expect a _tag property
                formcollection_dict = {}
                for form in formcollection:
                    formcollection_dict[form._tag] = form
                    delattr(form, '_tag')
                result_forms[form_key] = formcollection_dict


        # Construct a result list, ordered by step number
        form_list = [result_forms[key] for key in sorted(result_forms.keys())]

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(form_list=form_list, form_dict=result_forms_dict, **kwargs)
        self.storage.reset()
        return done_response

    def get(self, request, *args, **kwargs):
        """
        This method handles GET requests.

        If a GET request reaches this point, the wizard assumes that the user
        just starts at the first step or wants to restart the process.
        The data of the wizard will be resetted before rendering the first step.
        """
        self.ensure_form_list()

        self.storage.reset()

        # reset the current step to the first step.
        self.storage.current_step = self.steps.first
        return self.render(self.get_forms())

    def post(self, *args, **kwargs):
        """
        This method handles POST requests.

        The wizard will render either the current step (if form validation
        wasn't successful), the next step (if the current step was stored
        successful) or the done view (if no more steps are available)
        """
        self.ensure_form_list()

        # Look for a wizard_goto_step element in the posted data which
        # contains a valid step name. If one was found, render the requested
        # form. (This makes stepping back a lot easier).
        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            return self.render_goto_step(wizard_goto_step)

        # Check if form was refreshed
        management_form = ManagementForm(self.request.POST, prefix=self.prefix)
        if not management_form.is_valid():
            raise ValidationError(
                _('ManagementForm data is missing or has been tampered.'),
                code='missing_management_form',
            )

        form_current_step = management_form.cleaned_data['current_step']
        if (form_current_step != self.steps.current and
                self.storage.current_step is not None):
            # form refreshed, change current step
            self.storage.current_step = form_current_step

        # get the form for the current step
        forms = self.get_forms(data=self.request.POST, files=self.request.FILES)

        # and try to validate
        all_valid = True
        for form in forms:
            if not form.is_valid():
                all_valid = False

        if all_valid:
            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            self.storage.set_step_files(self.steps.current, self.process_step_files(form))

            # check if the current step is the last step
            if self.steps.current == self.steps.last:
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)

        return self.render(forms)

    def get_forms(self, step=None, data=None, files=None):
        """
        Constructs the form for a given `step`. If no `step` is defined, the
        current step will be determined automatically.

        The form will be initialized using the `data` argument to prefill the
        new form. If needed, instance or queryset (for `ModelForm` or
        `ModelFormSet`) will be added too.
        """
        if step is None:
            step = self.steps.current
        form_struct = self.form_list[step]
        # prepare the kwargs for the form instance.

        form_collection = []
        if isinstance(form_struct, dict):
            initial_dict = self.get_form_initial(step)
            instance_dict = self.get_form_instance(step)
            form_collection = []
            for form_name, form_class in form_struct.items():
                initial = initial_dict.get(form_name, None) if initial_dict else None
                instance = instance_dict.get(form_name, None) if instance_dict else None
                kwargs = self.get_form_kwargs(step)
                kwargs.update({
                    'data': data,
                    'files': files,
                    'prefix': self.get_form_prefix(step, form_name),
                    'initial': initial
                })
                if issubclass(form_class, (forms.ModelForm, forms.models.BaseInlineFormSet)):
                    # If the form is based on ModelForm or InlineFormSet,
                    # add instance if available and not previously set.
                    kwargs.setdefault('instance', instance)
                elif issubclass(form_class, forms.models.BaseModelFormSet):
                    # If the form is based on ModelFormSet, add queryset if available
                    # and not previous set.
                    kwargs.setdefault('queryset', instance)
                form = form_class(**kwargs)
                form._tag = form_name
                form_collection.append(form)
        elif issubclass(form_struct, (forms.ModelForm, forms.models.BaseInlineFormSet)):
            # If the form is based on ModelForm or InlineFormSet,
            # add instance if available and not previously set.
            form_class = form_struct
            kwargs = self.get_form_kwargs(step)
            kwargs.update({
                'data': data,
                'files': files,
                'prefix': self.get_form_prefix(step, form_class),
                'initial': self.get_form_initial(step)
            })
            kwargs.setdefault('instance', self.get_form_instance(step))
            form_collection = [form_class(**kwargs)]
        elif issubclass(form_struct, (forms.Form, forms.BaseFormSet)):
            form_class = form_struct
            kwargs = self.get_form_kwargs(step)
            kwargs.update({
                'data': data,
                'files': files,
                'prefix': self.get_form_prefix(step, form_class),
                'initial': self.get_form_initial(step)
            })
            form_collection = [form_class(**kwargs)]
        elif issubclass(form_struct, forms.models.BaseModelFormSet):
            # If the form is based on ModelFormSet, add queryset if available
            # and not previous set.
            form_class = form_struct
            kwargs = self.get_form_kwargs(step)
            kwargs.update({
                'data': data,
                'files': files,
                'prefix': self.get_form_prefix(step, form_class),
                'initial': self.get_form_initial(step)
            })
            kwargs.setdefault('queryset', self.get_form_instance(step))
            form_collection = [form_class(**kwargs)]
        return form_collection

    def get_context_data(self, forms, **kwargs):
        """
        Returns the template context for a step. You can overwrite this method
        to add more data for all or some steps. This method returns a
        dictionary containing the rendered form step. Available template
        context variables are:

         * all extra data stored in the storage backend
         * `wizard` - a dictionary representation of the wizard instance

        Example:

        .. code-block:: python

            class MyWizard(WizardView):
                def get_context_data(self, form, **kwargs):
                    context = super(MyWizard, self).get_context_data(form=form, **kwargs)
                    if self.steps.current == 'my_step_name':
                        context.update({'another_var': True})
                    return context
        """
        if 'view' not in kwargs:
            kwargs['view'] = self
        context = kwargs
        context.update(self.storage.extra_data)

        if self.cleaned_data_in_context:
            context.update({
                'cleaned_data': self.get_all_cleaned_data_dict()
            })

        context['wizard'] = {
            'forms': forms,
            'steps': self.steps,
            'management_form': ManagementForm(prefix=self.prefix, initial={
                'current_step': self.steps.current,
            }),
        }
        return context

    def get_all_cleaned_data(self):
        """
        Returns a merged dictionary of all step cleaned_data dictionaries.
        If a step contains a `FormSet`, the key will be prefixed with
        'formset-' and contain a list of the formset cleaned_data dictionaries.
        """
        cleaned_data = {}
        for form_key in self.get_form_list():
            form_collection = self.get_forms(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            for form_obj in form_collection:
                if form_obj.is_valid():
                    if isinstance(form_obj.cleaned_data, (tuple, list)):
                        cleaned_data.update({
                            'formset-%s' % form_key: form_obj.cleaned_data
                        })
                    else:
                        cleaned_data.update(form_obj.cleaned_data)
        return cleaned_data

    def get_cleaned_data_for_step(self, step):
        """
        Returns the cleaned data for a given `step`. Before returning the
        cleaned data, the stored values are revalidated through the form.
        If the data doesn't validate, None will be returned.
        """
        cleaned_data = {}
        if step in self.form_list:
            form_collection = self.get_forms(
                step=step,
                data=self.storage.get_step_data(step),
                files=self.storage.get_step_files(step))

            multiple_forms = isinstance(self.form_list[step], dict)

            if multiple_forms:
                multiple_form_keys = list(self.form_list[step].keys())

            for i, form_obj in enumerate(form_collection):
                if form_obj.is_valid():
                    form_data = form_obj.cleaned_data
                    if isinstance(form_data, (tuple, list)):
                        form_key = step
                        cleaned_data.update({
                            'formset-%s' % form_key: form_data
                        })
                    elif multiple_forms and multiple_form_keys:
                        cleaned_data[multiple_form_keys[i]] = form_data
                    else:
                        cleaned_data.update(form_data)
        return cleaned_data

    def get_all_cleaned_data_dict(self):
        """
        Returns a merged dictionary of all step cleaned_data dictionaries, grouped per step.
        If a step contains a `FormSet`, the key will be prefixed with
        'formset-' and contain a list of the formset cleaned_data dictionaries.
        """
        cleaned_data = {}
        for step in self.form_list:
            data = self.get_cleaned_data_for_step(step)
            if not data:
                continue
            cleaned_data[step] = data
        return cleaned_data

    def ensure_form_list(self):
        self._form_list_initialized = getattr(self, '_form_list_initialized', False)

        # If the form list is initialized, return
        if self._form_list_initialized:
            return

        # If we already have a form list, return
        if self.form_list:
            self._form_list_initialized = True
            return

        # It seems we need a form_list_factory
        assert self._form_list_factory is not None, 'form_list should be a list of forms or a function reference'

        factory_fnc = None
        if isinstance(self._form_list_factory, six.string_types):
            factory_fnc = getattr(self, self._form_list_factory)
        elif callable(self._form_list_factory):
            factory_fnc = self._form_list_factory

        # Make sure we retrieved a factory function
        assert factory_fnc is not None

        # Call form_list_factory method on object, which should return a conventional form_list structure
        form_list = factory_fnc(self)

        # Compute the internal form list from that
        computed_form_list = self.__class__.compute_form_list(form_list=form_list)

        # Overwrite the form_list on 'self'
        self.form_list = computed_form_list

        # Make sure we won't repeat ourselves
        self._form_list_initialized = True


class SessionMultipleFormWizardView(MultipleFormWizardView):
    """
    A WizardView with pre-configured SessionStorage backend.
    """
    storage_name = 'formtools.wizard.storage.session.SessionStorage'


class CookieMultipleFormWizardView(MultipleFormWizardView):
    """
    A WizardView with pre-configured CookieStorage backend.
    """
    storage_name = 'formtools.wizard.storage.cookie.CookieStorage'


class NamedUrlMultipleFormWizardView(MultipleFormWizardView):
    """
    A WizardView with URL named steps support.
    """
    url_name = None
    done_step_name = None

    @classmethod
    def get_initkwargs(cls, *args, **kwargs):
        """
        We require a url_name to reverse URLs later. Additionally users can
        pass a done_step_name to change the URL name of the "done" view.
        """
        url_name = kwargs.pop('url_name', getattr(cls, 'url_name', None)) or None
        done_step_name = kwargs.pop('done_step_name', getattr(cls, 'done_step_name', None)) or 'done'

        assert url_name is not None, 'URL name is needed to resolve correct wizard URLs'
        extra_kwargs = {
            'done_step_name': done_step_name,
            'url_name': url_name,
        }
        initkwargs = super(NamedUrlMultipleFormWizardView, cls).get_initkwargs(*args, **kwargs)
        initkwargs.update(extra_kwargs)

        assert initkwargs['done_step_name'] not in initkwargs['form_list'], \
            'step name "%s" is reserved for "done" view' % initkwargs['done_step_name']
        return initkwargs

    def get_step_url(self, step):
        kwargs = self.kwargs
        kwargs.update({'step': step})
        return reverse(self.url_name, kwargs=kwargs)

    def get(self, *args, **kwargs):
        """
        This renders the form or, if needed, does the http redirects.
        """
        self.ensure_form_list()

        step_url = kwargs.get('step', None)
        if step_url is None:
            if 'reset' in self.request.GET:
                self.storage.reset()
                self.storage.current_step = self.steps.first
            if self.request.GET:
                query_string = "?%s" % self.request.GET.urlencode()
            else:
                query_string = ""
            return redirect(self.get_step_url(self.steps.current)
                            + query_string)

        # is the current step the "done" name/view?
        elif step_url == self.done_step_name:
            last_step = self.steps.last
            return self.render_done(self.get_forms(step=last_step,
                data=self.storage.get_step_data(last_step),
                files=self.storage.get_step_files(last_step)
            ), **kwargs)

        # is the url step name not equal to the step in the storage?
        # if yes, change the step in the storage (if name exists)
        elif step_url == self.steps.current:
            # URL step name and storage step name are equal, render!
            return self.render(self.get_forms(
                data=self.storage.current_step_data,
                files=self.storage.current_step_files,
            ), **kwargs)

        elif step_url in self.get_form_list():
            self.storage.current_step = step_url
            return self.render(self.get_forms(
                data=self.storage.current_step_data,
                files=self.storage.current_step_files,
            ), **kwargs)

        # invalid step name, reset to first and redirect.
        else:
            self.storage.current_step = self.steps.first
            return redirect(self.get_step_url(self.steps.first))

    def post(self, *args, **kwargs):
        """
        Do a redirect if user presses the prev. step button. The rest of this
        is super'd from WizardView.
        """
        self.ensure_form_list()

        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            return self.render_goto_step(wizard_goto_step)
        return super(NamedUrlMultipleFormWizardView, self).post(*args, **kwargs)

    def get_context_data(self, forms, **kwargs):
        """
        NamedUrlWizardView provides the url_name of this wizard in the context
        dict `wizard`.
        """
        context = super(NamedUrlMultipleFormWizardView, self).get_context_data(forms=forms, **kwargs)
        context['wizard']['url_name'] = self.url_name
        return context

    def render_next_step(self, form, **kwargs):
        """
        When using the NamedUrlWizardView, we have to redirect to update the
        browser's URL to match the shown step.
        """
        next_step = self.get_next_step()
        self.storage.current_step = next_step
        return redirect(self.get_step_url(next_step))

    def render_goto_step(self, goto_step, **kwargs):
        """
        This method gets called when the current step has to be changed.
        `goto_step` contains the requested step to go to.
        """
        self.storage.current_step = goto_step
        return redirect(self.get_step_url(goto_step))

    def render_revalidation_failure(self, failed_step, form, **kwargs):
        """
        When a step fails, we have to redirect the user to the first failing
        step.
        """
        self.storage.current_step = failed_step
        return redirect(self.get_step_url(failed_step))

    def render_done(self, form, **kwargs):
        """
        When rendering the done view, we have to redirect first (if the URL
        name doesn't fit).
        """
        if kwargs.get('step', None) != self.done_step_name:
            return redirect(self.get_step_url(self.done_step_name))
        return super(NamedUrlMultipleFormWizardView, self).render_done(form, **kwargs)


class NamedUrlSessionMultipleFormWizardView(NamedUrlMultipleFormWizardView):
    """
    A NamedUrlWizardView with pre-configured SessionStorage backend.
    """
    storage_name = 'formtools.wizard.storage.session.SessionStorage'


class NamedUrlCookieMultipleFormWizardView(NamedUrlMultipleFormWizardView):
    """
    A NamedUrlFormWizard with pre-configured CookieStorageBackend.
    """
    storage_name = 'formtools.wizard.storage.cookie.CookieStorage'
