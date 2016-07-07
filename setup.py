#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pip.req import parse_requirements

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

__version__ = '0.1.14'

# parse_requirements() returns generator of pip.req.InstallRequirement objects
requirements = [str(ir.req) for ir in parse_requirements(os.path.join(BASE_DIR, 'requirements.txt'), session=False)]

if sys.argv[-1] == 'publish':
    try:
        import wheel
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (__version__, __version__))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='django-formtools-addons',
    version=__version__,
    description="""'Addons for Django Formtools'""",
    long_description=readme + '\n\n' + history,
    author='VikingCo',
    author_email='technology@vikingco.com',
    url='https://github.com/vikingco/django-formtools-addons',
    packages=[
        'formtools_addons',
    ],
    include_package_data=True,
    install_requires=requirements,
    extras_require={},
    license="BSD",
    zip_safe=False,
    keywords='django-formtools-addons',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
