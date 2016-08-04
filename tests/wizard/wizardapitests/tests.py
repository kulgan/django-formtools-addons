# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.urlresolvers import reverse
from django.http.response import JsonResponse
from django.test.testcases import TestCase
from django.test.utils import override_settings

from formtools_addons.enums import HTTP_APPLICATION_JSON
from formtools_addons.wizard.views.wizardapi import WizardAPIView


@override_settings(
    ROOT_URLCONF='tests.wizard.wizardapitests.urls',
)
class WizardAPITests(TestCase):
    DEFAULT_HEADERS = {'HTTP_ACCEPT': HTTP_APPLICATION_JSON}

    ####################################################################################################################
    # Regular wizard, index based
    ####################################################################################################################
    def test_get_wizard_without_step(self):
        response = self.client.get(reverse('wizard'), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == '0'

    def test_get_wizard_data_step(self):
        response = self.client.get(reverse('wizard_step', kwargs={'step': 'data'}), **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        data = self._get_response_data(response)
        assert data['structure'] == ['0', '1']

    def test_get_wizard_with_step(self):
        response = self.client.get(reverse('wizard_step', kwargs={'step': '1'}), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == '1'

    def test_post_wizard_step_incomplete(self):
        data = {
            'name': 'test'
        }
        response = self.client.post(reverse('wizard_step', kwargs={'step': '0'}), data, **self.DEFAULT_HEADERS)
        assert response.status_code == 400

    def test_post_wizard_step(self):
        # Perform step 0
        input_data1 = {
            'name': 'test',
            'thirsty': True
        }
        response = self.client.post(reverse('wizard_step', kwargs={'step': '0'}), input_data1, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == '1'  # Next step's name
        assert data['done'] is False
        assert data['steps']['0']['data']['name'] == input_data1['name']
        assert data['steps']['0']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['0']['valid'] is True
        assert data['steps']['1']['valid'] is False

        # Perform step 1
        input_data2 = {
            'address1': 'Address 1',
            'address2': 'Address 2'
        }
        response = self.client.post(reverse('wizard_step', kwargs={'step': '1'}), input_data2, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # Next step's name
        assert data['done'] is True
        assert data['steps']['1']['data']['address1'] == input_data2['address1']
        assert data['steps']['1']['data']['address2'] == input_data2['address2']
        assert data['steps']['1']['valid'] is True

        # Fetch data
        response = self.client.get(reverse('wizard_step', kwargs={'step': 'data'}), {}, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # There should not be another step
        assert data['done'] is True
        assert data['steps']['0']['data']['name'] == input_data1['name']
        assert data['steps']['0']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['0']['valid'] is True
        assert data['steps']['1']['data']['address1'] == input_data2['address1']
        assert data['steps']['1']['data']['address2'] == input_data2['address2']
        assert data['steps']['1']['valid'] is True

        # Commit data
        response = self.client.post(reverse('wizard_step', kwargs={'step': 'commit'}), {}, **self.DEFAULT_HEADERS)

        assert response.status_code == 302

    ####################################################################################################################
    # Regular wizard, name based
    ####################################################################################################################
    def test_get_named_wizard_without_step(self):
        response = self.client.get(reverse('named_wizard'), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == 'page1'

    def test_get_named_wizard_data_step(self):
        response = self.client.get(reverse('named_wizard_step', kwargs={'step': 'data'}), **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        data = self._get_response_data(response)
        assert data['structure'] == ['page1', 'page2']

    def test_get_named_wizard_with_step(self):
        response = self.client.get(reverse('named_wizard_step', kwargs={'step': 'page2'}), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == 'page2'

    def test_post_named_wizard_step_incomplete(self):
        data = {
            'name': 'test'
        }
        response = self.client.post(reverse('named_wizard_step', kwargs={'step': 'page1'}), data,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 400

    def test_post_named_wizard_step(self):
        # Perform step 0
        input_data1 = {
            'name': 'test',
            'thirsty': True
        }
        response = self.client.post(reverse('named_wizard_step', kwargs={'step': 'page1'}), input_data1,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page2'  # Next step's name
        assert data['done'] is False
        assert data['steps']['page1']['data']['name'] == input_data1['name']
        assert data['steps']['page1']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['page1']['valid'] is True
        assert data['steps']['page2']['valid'] is False

        # Perform step 1
        input_data2 = {
            'address1': 'Address 1',
            'address2': 'Address 2'
        }
        response = self.client.post(reverse('named_wizard_step', kwargs={'step': 'page2'}), input_data2,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # Next step's name
        assert data['done'] is True
        assert data['steps']['page2']['data']['address1'] == input_data2['address1']
        assert data['steps']['page2']['data']['address2'] == input_data2['address2']
        assert data['steps']['page2']['valid'] is True

        # Fetch data
        response = self.client.get(reverse('named_wizard_step', kwargs={'step': 'data'}), {}, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # There should not be another step
        assert data['done'] is True
        assert data['steps']['page1']['data']['name'] == input_data1['name']
        assert data['steps']['page1']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['page1']['valid'] is True
        assert data['steps']['page2']['data']['address1'] == input_data2['address1']
        assert data['steps']['page2']['data']['address2'] == input_data2['address2']
        assert data['steps']['page2']['valid'] is True

        # Commit data
        response = self.client.post(reverse('named_wizard_step', kwargs={'step': 'commit'}), {}, **self.DEFAULT_HEADERS)

        assert response.status_code == 302

    ####################################################################################################################
    # Substep wizard, index based
    ####################################################################################################################
    def test_get_substep_wizard_without_step(self):
        response = self.client.get(reverse('substep_wizard'), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == '0|step1.1'

    def test_get_substep_wizard_data_step(self):
        response = self.client.get(reverse('substep_wizard_step', kwargs={'step': 'data'}), **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        data = self._get_response_data(response)
        assert data['structure'] == ['0|step1.1', '0|step1.2', '1|step2.1']

    def test_get_substep_wizard_with_step(self):
        response = self.client.get(reverse('substep_wizard_step', kwargs={'step': '0|step1.2'}), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == '0|step1.2'

    def test_post_substep_wizard_step_incomplete(self):
        data = {
            'name': 'test'
        }
        response = self.client.post(reverse('substep_wizard_step', kwargs={'step': '0|step1.1'}), data,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 400

    def test_post_substep_wizard_step(self):
        # Perform step 0
        input_data1 = {
            'name': 'test',
            'thirsty': True
        }
        response = self.client.post(reverse('substep_wizard_step', kwargs={'step': '0|step1.1'}), input_data1,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == '0|step1.2'  # Next step's name
        assert data['done'] is False
        assert data['steps']['0|step1.1']['data']['name'] == input_data1['name']
        assert data['steps']['0|step1.1']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['0|step1.1']['valid'] is True
        assert data['steps']['0|step1.2']['valid'] is False
        assert data['steps']['1|step2.1']['valid'] is False

        # Perform step 1
        input_data2 = {
            'address1': 'Address 1',
            'address2': 'Address 2'
        }
        response = self.client.post(reverse('substep_wizard_step', kwargs={'step': '0|step1.2'}), input_data2,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == '1|step2.1'  # Next step's name
        assert data['done'] is False
        assert data['steps']['0|step1.2']['data']['address1'] == input_data2['address1']
        assert data['steps']['0|step1.2']['data']['address2'] == input_data2['address2']
        assert data['steps']['0|step1.2']['valid'] is True
        assert data['steps']['1|step2.1']['valid'] is False

        # Perform step 2
        input_data3 = {
            'random_crap': 'Blablabla'
        }
        response = self.client.post(reverse('substep_wizard_step', kwargs={'step': '1|step2.1'}), input_data3, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # Next step's name
        assert data['done'] is True
        assert data['steps']['1|step2.1']['data']['random_crap'] == input_data3['random_crap']
        assert data['steps']['1|step2.1']['valid'] is True

        # Fetch data
        response = self.client.get(reverse('substep_wizard_step', kwargs={'step': 'data'}), {}, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # There should not be another step
        assert data['done'] is True
        assert data['steps']['0|step1.1']['data']['name'] == input_data1['name']
        assert data['steps']['0|step1.1']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['0|step1.1']['valid'] is True
        assert data['steps']['0|step1.2']['data']['address1'] == input_data2['address1']
        assert data['steps']['0|step1.2']['data']['address2'] == input_data2['address2']
        assert data['steps']['0|step1.2']['valid'] is True
        assert data['steps']['1|step2.1']['data']['random_crap'] == input_data3['random_crap']
        assert data['steps']['1|step2.1']['valid'] is True

        # Commit data
        response = self.client.post(reverse('substep_wizard_step', kwargs={'step': 'commit'}), {},
                                    **self.DEFAULT_HEADERS)

        assert response.status_code == 302

    ####################################################################################################################
    # Substep wizard, name based
    ####################################################################################################################
    def test_get_named_substep_wizard_without_step(self):
        response = self.client.get(reverse('named_substep_wizard'), **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == 'page1|step1.1'

    def test_get_named_substep_wizard_data_step(self):
        response = self.client.get(reverse('named_substep_wizard_step', kwargs={'step': 'data'}),
                                   **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        data = self._get_response_data(response)
        assert data['structure'] == ['page1|step1.1', 'page1|step1.2', 'page2|step2.1']

    def test_get_named_substep_wizard_with_step(self):
        response = self.client.get(reverse('named_substep_wizard_step', kwargs={'step': 'page1|step1.2'}),
                                   **self.DEFAULT_HEADERS)
        assert response.status_code == 200
        assert self._get_response_data(response)['current_step'] == 'page1|step1.2'

    def test_post_named_substep_wizard_step_incomplete(self):
        data = {
            'name': 'test'
        }
        response = self.client.post(reverse('named_substep_wizard_step', kwargs={'step': 'page1|step1.1'}), data,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 400

    def test_post_named_substep_wizard_step(self):
        # Perform step 0
        input_data1 = {
            'name': 'test',
            'thirsty': True
        }
        response = self.client.post(reverse('named_substep_wizard_step', kwargs={'step': 'page1|step1.1'}), input_data1,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page1|step1.2'  # Next step's name
        assert data['done'] is False
        assert data['steps']['page1|step1.1']['data']['name'] == input_data1['name']
        assert data['steps']['page1|step1.1']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['page1|step1.1']['valid'] is True
        assert data['steps']['page1|step1.2']['valid'] is False
        assert data['steps']['page2|step2.1']['valid'] is False

        # Perform step 1
        input_data2 = {
            'address1': 'Address 1',
            'address2': 'Address 2'
        }
        response = self.client.post(reverse('named_substep_wizard_step', kwargs={'step': 'page1|step1.2'}), input_data2,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page2|step2.1'  # Next step's name
        assert data['done'] is False
        assert data['steps']['page1|step1.2']['data']['address1'] == input_data2['address1']
        assert data['steps']['page1|step1.2']['data']['address2'] == input_data2['address2']
        assert data['steps']['page1|step1.2']['valid'] is True
        assert data['steps']['page2|step2.1']['valid'] is False

        # Perform step 2
        input_data3 = {
            'random_crap': 'Blablabla'
        }
        response = self.client.post(reverse('named_substep_wizard_step', kwargs={'step': 'page2|step2.1'}), input_data3,
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # Next step's name
        assert data['done'] is True
        assert data['steps']['page2|step2.1']['data']['random_crap'] == input_data3['random_crap']
        assert data['steps']['page2|step2.1']['valid'] is True

        # Fetch data
        response = self.client.get(reverse('named_substep_wizard_step', kwargs={'step': 'data'}), {},
                                   **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # There should not be another step
        assert data['done'] is True
        assert data['steps']['page1|step1.1']['data']['name'] == input_data1['name']
        assert data['steps']['page1|step1.1']['data']['thirsty'] == input_data1['thirsty']
        assert data['steps']['page1|step1.1']['valid'] is True
        assert data['steps']['page1|step1.2']['data']['address1'] == input_data2['address1']
        assert data['steps']['page1|step1.2']['data']['address2'] == input_data2['address2']
        assert data['steps']['page1|step1.2']['valid'] is True
        assert data['steps']['page2|step2.1']['data']['random_crap'] == input_data3['random_crap']
        assert data['steps']['page2|step2.1']['valid'] is True

        # Commit data
        response = self.client.post(reverse('named_substep_wizard_step', kwargs={'step': 'commit'}), {},
                                    **self.DEFAULT_HEADERS)

        assert response.status_code == 302

    def test_post_complex_named_substep_wizard_step(self):
        # Perform step 0
        input_data1 = {
            'name': 'test',
            'thirsty': True
        }
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'page1|step1.1'}),
                                    input_data1, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page1|step1.2'  # Next step's name
        assert data['done'] is False

        # Perform step 1
        input_data2 = {
            'address1': 'Address 1',
            'address2': 'Address 2'
        }
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'page1|step1.2'}),
                                    input_data2, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page1|step1.3'  # Next step's name
        assert data['done'] is False

        # Perform step 2
        input_data3 = {
            'random_crap': 'Blablabla'
        }
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'page1|step1.3'}),
                                    input_data3, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page2|step2.1'  # Next step's name
        assert data['done'] is False

        # Perform step 3
        input_data4 = {
            'name': 'test2',
            'thirsty': True
        }
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'page2|step2.1'}),
                                    input_data4, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page2|step2.2'  # Next step's name
        assert data['done'] is False

        ############################################################################################################
        # NOW WE JUMP BACK TO STEP 1.1!
        ############################################################################################################
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'goto/page1|step1.1'}),
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page1|step1.1'  # Next step's name
        assert data['done'] is False
        assert data['valid'] is False
        assert 'page2|step2.2' in data['steps']

        # We change the 'name' value to 'hurray' (see tests/wizard/wizardapitests/url.py)
        input_data5 = {
            'name': 'hurray',
            'thirsty': True
        }
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'page1|step1.1'}),
                                    input_data5, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page1|step1.2'  # Next step's name
        assert data['done'] is False
        assert data['valid'] is True
        assert 'page2|step2.2' not in data['steps']

        ############################################################################################################
        # NOW WE JUMP FORWARD TO STEP 2.1!
        ############################################################################################################
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'goto/page2|step2.1'}),
                                    **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] == 'page2|step2.1'  # Next step's name
        assert data['done'] is False
        assert data['valid'] is True

        # Perform step 3
        input_data6 = {
            'name': 'test2',
            'thirsty': True
        }
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'page2|step2.1'}),
                                    input_data6, **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # Next step's name
        assert data['done'] is True
        assert data['valid'] is True

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # Next step's name
        assert data['done'] is True

        # Fetch data
        response = self.client.get(reverse('complex_named_substep_wizard_step', kwargs={'step': 'data'}), {},
                                   **self.DEFAULT_HEADERS)
        assert response.status_code == 200

        # Get data
        data = self._get_response_data(response)
        assert data['current_step'] is None  # There should not be another step
        assert data['done'] is True
        assert data['steps']['page1|step1.1']['data']['name'] == input_data5['name']
        assert data['steps']['page1|step1.1']['data']['thirsty'] == input_data5['thirsty']
        assert data['steps']['page1|step1.1']['valid'] is True
        assert data['steps']['page1|step1.2']['data']['address1'] == input_data2['address1']
        assert data['steps']['page1|step1.2']['data']['address2'] == input_data2['address2']
        assert data['steps']['page1|step1.2']['valid'] is True
        assert data['steps']['page1|step1.3']['data']['random_crap'] == input_data3['random_crap']
        assert data['steps']['page1|step1.3']['valid'] is True
        assert data['steps']['page2|step2.1']['data']['name'] == input_data4['name']
        assert data['steps']['page2|step2.1']['data']['thirsty'] == input_data4['thirsty']
        assert data['steps']['page2|step2.1']['valid'] is True
        assert 'page2|step2.2' not in data['steps']

        # Commit data
        response = self.client.post(reverse('complex_named_substep_wizard_step', kwargs={'step': 'commit'}), {},
                                    **self.DEFAULT_HEADERS)

        assert response.status_code == 302

    def _get_response_data(self, response):
        assert isinstance(response, JsonResponse)
        return json.loads(response.content.decode('utf-8'))

