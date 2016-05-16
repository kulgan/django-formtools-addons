# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url, include

urlpatterns = [
    # Frontend
    url(r'^wizard/', include('testapp.urls', namespace='testapp'))
]
