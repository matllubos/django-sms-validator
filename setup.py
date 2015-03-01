#!/usr/bin/env python
# -*- coding: utf-8 -*-
from security.version import get_version

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='django-sms-validator',
    version=get_version(),
    description="Python library for sms validation.",
    keywords='django, sms, python',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/sms-validator',
    license='LGPL',
    package_dir={'sms_validator': 'sms_validator'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 0 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU LESSER GENERAL PUBLIC LICENSE (LGPL)',
        'Natural Language :: Czech',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=[
        'django-chamber>=0.0.7',
        'django-sms-operator>=0.0.1',
    ],
    dependency_links=[
        'https://github.com/matllubos/django-chamber/tarball/0.0.7#egg=django-chamber-0.0.7',
        'https://github.com/matllubos/django-sms-operator/tarball/0.0.7#egg=django-sms-operator-0.0.1',
    ],
    zip_safe=False
)
