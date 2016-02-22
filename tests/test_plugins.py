import unittest

module_namespace = locals()


def setUpModule():
    from maya import standalone
    standalone.initialize(name='python')
    from maya import cmds
    from mtoatools import plugins

    module_namespace['standalone'] = standalone
    module_namespace['cmds'] = cmds
    module_namespace['plugins'] = plugins


class TestPlugins(unittest.TestCase):

    def setUp(self):
        cmds.file(new=True, force=True)

    def test_load_unload_swatch(self):
        '''Load swatch plugin'''

        cmds.loadPlugin('swatch')
        cmds.unloadPlugin('swatch', force=True)
