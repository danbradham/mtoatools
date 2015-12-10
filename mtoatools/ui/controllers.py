import pymel.core as pmc
from functools import partial
from PySide import QtGui, QtCore
from .dialogs import MatteDialog, MatteWidget
from .utils import get_maya_window
from ..api import MatteAOV


class MatteController(MatteDialog):

    def __init__(self, parent=get_maya_window()):
        super(MatteController, self).__init__(parent=parent)

        self.matte_list.itemSelectionChanged.connect(self.matte_list_select)
        self.obj_list.itemSelectionChanged.connect(self.obj_list_select)
        self.refresh_matte_list()

    def set_aov(self, aov):
        self.aov = aov
        self.refresh_obj_list()

    def new_matte_item(self, aov):
        item = QtGui.QListWidgetItem()
        item.pynode = aov

        del_callback = partial(delete_matte_item, item, aov)
        widget = MatteWidget(aov.name)
        widget.del_button.clicked.connect(del_callback)

        self.matte_list.addItem(item)
        self.matte_list.setItemWidget(item, widget)

    def delete_matte_item(self, item, aov):
        self.matte_list.takeItem(self.matted_list.indexFromItem(item))
        aov.delete()
        if aov == self.aov:
            self.aov = None
            self.obj_list.clear()

    def new_obj_item(self, node, color):
        item = QtGui.QListWidgetItem()
        item.setText(str(node))
        item.pynode = node
        item.pycolor = color
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(*color))
        item.setBackground(brush)
        self.obj_list.addItem(item)

    def refresh_matte_list(self):
        self.obj_list.clear()
        self.matte_list.clear()

        for aov in MatteAOV.ls():
            self.new_matte_item(aov)

    def refresh_obj_list(self):
        self.obj_list.clear()
        for color, nodes in self.aov:
            for node in nodes:
                self.new_obj_item(node, color)

    def matte_list_select(self):
        item = self.matte_list.currentItem()
        self.set_aov(item.pynode)
        self.refresh_obj_list()

    def obj_list_select(self):
        nodes = []
        for item in self.obj_list.selectedItems():
            nodes.append(item.pynode)
        pmc.select(nodes, replace=True)
