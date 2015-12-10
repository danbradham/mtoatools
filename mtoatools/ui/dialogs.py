from PySide import QtGui, QtCore


class MatteWidget(QtGui.QWidget):

    def __init__(self, text, *args, **kwargs):
        super(MattListItem, self).__init__(*args, **kwargs)

        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QtGui.QLabel(text)
        self.del_button = QtGui.QPushButton('x')

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.del_buttotn)


class MatteList(QtGui.QListWidget):

    def __init__(self, *args, **kwargs):
        super(MatteList, self).__init__(*args, **kwargs)
        self.setObjectName('mattelist')


class ObjectList(QtGui.QListWidget):

    def __init__(self, *args, **kwargs):
        super(ObjectList, self).__init__(*args, **kwargs)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setObjectName('objectlist')


class MatteDialog(QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(MatteDialog, self).__init__(*args, **kwargs)

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setRowStretch(1, 1)
        self.setLayout(self.grid)

        self.matte_line = QtGui.QLineEdit()
        self.button_new = QtGui.QPushButton('Create')
        self.matte_list = MatteList()

        self.button_refresh = QtGui.QPushButton('Refresh')
        self.obj_list = ObjectList()
        self.button_red = QtGui.QPushButton('Red')
        self.button_green = QtGui.QPushButton('Green')
        self.button_blue = QtGui.QPushButton('Blue')
        self.button_white = QtGui.QPushButton('White')
        self.button_black = QtGui.QPushButton('Black')
        self.button_add = QtGui.QPushButton('Add')
        self.button_rem = QtGui.QPushButton('Remove')

        self.grid.addWidget(self.matte_line, 0, 0, 1, 2)
        self.grid.addWidget(self.button_new, 0, 2, 1, 1)
        self.grid.addWidget(self.matte_list, 1, 0, 1, 3)

        self.grid.addWidget(self.button_refresh, 0, 7, 1, 1)
        self.grid.addWidget(self.obj_list, 1, 3, 1, 5)
        self.grid.addWidget(self.button_add, 2, 6, 1, 1)
        self.grid.addWidget(self.button_rem, 2, 7, 1, 1)
        self.grid.addWidget(self.button_red, 3, 3, 1, 1)
        self.grid.addWidget(self.button_green, 3, 4, 1, 1)
        self.grid.addWidget(self.button_blue, 3, 5, 1, 1)
        self.grid.addWidget(self.button_white, 3, 6, 1, 1)
        self.grid.addWidget(self.button_black, 3, 7, 1, 1)


def test_main():

    import sys
    app = QtGui.QApplication(sys.argv)
    dialog = MatteDialog()
    sys.exit(dialog.exec_())

if __name__ == '__main__':
    test_main()
