import sys
from PySide import QtGui
from . import tests_path

sys.path.insert(1, tests_path('../mtoatools/ui'))


def test_matte_ui():
    from dialogs import MatteDialog

    app = QtGui.QApplication(sys.argv)
    dialog = MatteDialog()
    sys.exit(dialog.exec_())
