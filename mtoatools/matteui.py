import pymel.core as pmc
from PySide import QtGui, QtCore


class ObjectList(QtGui.QListWidget):

    def __init__(self, *args, **kwargs):
        super(ObjectList, self).__init__(*args, **kwargs)
        self.aov = None
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.setObjectName('objectlist')

    def set_aov(self, aov):
        self.aov = aov
        self.refresh_list()

    def refresh_list(self):
        self.clear()
        for color, nodes in self.aov:
            for node in nodes:
                item = QtGui.QListWidgetItem()
                item.setText(str(node))
                item.pynode = node
                item.pycolor = color
                brush = QtGui.QBrush()
                brush.setColor(QtGui.QColor(*color))
                item.setBackground(brush)
                self.addItem(item)

    def on_selection_changed(self):
        nodes = []
        for item in self.selectedItems():
            nodes.append(item.pynode)
        pmc.select(nodes, replace=True)


class MatteView(QtGui.QDialog):

    def __init__(self):

        w = QtGui.QWidget(self)
        self.setWidget(w)

        self.grid = QtGui.QGridLayout()
        w.setLayout(self.grid)
