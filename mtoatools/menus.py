from Qt import QtCore, QtWidgets, QtGui
from .ui.utils import get_maya_window
from .patches import fix_aov_alias_attrs, fix_render_globals_window


class PatchesMenu(QtWidgets.QMenu):

    _instance = None

    def __init__(self, parent=get_maya_window()):
        super(PatchesMenu, self).__init__(parent)

        self.setTearOffEnabled(True)

        self.setTitle('Patches Menu')
        self.addAction('Fix AOV Alias Attrs', fix_aov_alias_attrs)
        self.addAction('Fix Render Globals Window', fix_render_globals_window)

    @classmethod
    def show(cls):
        if not cls._instance:
            cls._instance = cls()
        cls._instance.popup(QtGui.QCursor.pos() + QtCore.QPoint(-10, -15))
