import os
from maya import mel, cmds
from PySide import QtGui
from functools import partial
from collections import OrderedDict

this_package = os.path.abspath(os.path.dirname(__file__))
shelf_path = partial(os.path.join, this_package)

buttons = OrderedDict({
    'mattes': {
        'command': (
            'import mtoatools\n'
            'mtoatools.show_mattes_ui()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('mtoatools_mattes.png'),
        'annotation': 'AOV Matte management',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    },
    'hdrig': {
        'command': (
            'import mtoatools\n'
            'mtoatools.create_hdr_rig()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('mtoatools_hdrig.png'),
        'annotation': 'HDR Light Rig',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    },
    'patches': {
        'command': (
            'from mtoatools.menus import PatchesMenu\n'
            'PatchesMenu.show()'
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('mtoatools_patches.png'),
        'annotation': 'AOV Matte management',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    },
    'documentation': {
        'command': (
            "import webbrowser\n"
            "webbrowser.open('https://mtoatools.readthedocs.org')"
        ),
        'sourceType': 'python',
        'style': 'iconOnly',
        'image': shelf_path('mtoatools_docs.png'),
        'annotation': 'documentation',
        'enableCommandRepeat': False,
        'useAlpha': True,
        'flat': True,
        'enableBackground': False,
    }
})


def create_shelf():
    '''Create the mtoatools shelf'''

    tab_layout = mel.eval('$pytmp=$gShelfTopLevel')
    shelf_exists = cmds.shelfLayout('mtoatools', exists=True)

    if shelf_exists:
        cmds.deleteUI('mtoatools', layout=True)

    shelf = cmds.shelfLayout('mtoatools', parent=tab_layout)

    for button, kwargs in buttons.items():

        img = QtGui.QImage(kwargs['image'])
        kwargs['width'] = img.width()
        kwargs['height'] = img.height()

        cmds.shelfButton(label=button, parent=shelf, **kwargs)

create_shelf()
