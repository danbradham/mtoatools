'''
mtoatools.plugins
=================
Arnold/Lighting related plugins for Autodesk Maya
'''

import os
import sys
from glob import glob
from types import ModuleType
from maya import cmds


plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')
try:
    plugin_path = os.environ['MAYA_PLUG_IN_PATH']
    plugin_path = plugins_path + os.pathsep + plugin_path
except KeyError:
    plugin_path = plugins_path
os.environ['MAYA_PLUG_IN_PATH'] = plugin_path


def get_module(mod_path, filepath):
    '''Compile a plugin module

    :param filepath: full filepath to python plugin module
    '''

    with open(filepath, 'r') as f:
        c = compile(f.read(), '', 'exec')

    module = ModuleType(mod_path)
    module.__file__ = filepath
    exec(c, module.__dict__)

    return module


for py_plugin_path in glob(os.path.join(plugins_path, '*.py')):
    mod_name = os.path.basename(py_plugin_path).rstrip('.py')
    mod_path = 'mtoatools.plugins.' + mod_name
    mod = get_module(mod_path, py_plugin_path)
    setattr(sys.modules[__name__], mod_name, mod)


def loaded(plugin):
    '''Is plugin loaded?'''

    return cmds.pluginInfo(plugin, q=True, loaded=True)


def load(plugin):
    '''Load plugin'''

    if loaded(plugin):
        return

    cmds.loadPlugin(plugin)


def unload(plugin):
    '''Unload plugin'''

    if not loaded(plugin):
        return

    cmds.unloadPlugin(plugin, force=False)


def reload(plugin):
    '''Reload plugin'''

    unload(plugin)
    load(plugin)
