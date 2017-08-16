#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages
import os
import sys

if sys.argv[-1] == 'cheeseit!':
    try:
        check_call('python setup.py sdist bdist_wheel')
        check_call('twine upload dist/*')
    finally:
        shutil.rmtree('dist')
        shutil.rmtree('build')
        shutil.rmtree('mtoatools.egg-info')
    sys.exit()
elif sys.argv[-1] == 'testit!':
    check_call('python setup.py sdist bdist_wheel upload -r pypitest')
    sys.exit()


def get_info(pyfile):
    '''Retrieve dunder values from a pyfile'''

    info = {}
    info_re = re.compile(r"^__(\w+)__ = ['\"](.*)['\"]")
    with open(pyfile, 'r') as f:
        for line in f.readlines():
            match = info_re.search(line)
            if match:
                info[match.group(1)] = match.group(2)

    return info

info = get_info('mtoatools/__init__.py')


with open("README.rst") as f:
    readme = f.read()

setup(
    name=info['title'],
    version=info['version'],
    description=info['description'],
    long_description=readme,
    author=info['author'],
    author_email=info['email'],
    url=info['url'],
    license=info['license'],
    packages=find_packages(exclude=['tests']),
    package_data={
        '': ['LICENSE', 'README.rst', 'HISTORY.rst'],
    },
    include_package_data=True,
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
    ),
    install_requires=['Qt.py'],
)
