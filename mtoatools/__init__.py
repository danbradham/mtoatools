# -*- coding: utf-8 -*-

__title__ = 'mtoatools'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'http://github.com//mtoatools.git'
__version__ = '0.1.0'
__license__ = 'MIT'
__description__ = 'Arnold for Autodesk Maya tools'


try:
    from maya import cmds
    cmds.loadPlugin('mtoa', quiet=True)
except RuntimeError:
    raise ImportError('Arnold plugin failed to load or does not exist...')

from .api import *
