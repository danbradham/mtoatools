#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mock
module_names = [
    'pymel',
    'pymel.core',
    'maya',
    'PySide',
    'maya.api',
    'maya.api.OpenMaya',
    'maya.api.OpenMayaUI',
    'maya.api.OpenMayaRender',
    'maya.api.OpenMayaAnim',
    'maya.OpenMayaRender']
sys.modules.update(dict((name, mock.MagicMock()) for name in module_names))

import mtoatools


extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'mtoatools'
copyright = u'2015, Dan Bradham'
version = mtoatools.__version__
release = mtoatools.__version__
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_static_path = ['_static']

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
