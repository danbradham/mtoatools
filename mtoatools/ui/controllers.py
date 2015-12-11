import os
from functools import partial
from collections import defaultdict
from PySide import QtGui, QtCore
import pymel.core as pmc
from maya import OpenMaya
from contextlib import contextmanager
from .dialogs import MatteDialog, MatteWidget, ObjectWidget
from .utils import get_maya_window
from ..api import MatteAOV


class MayaHooks(QtCore.QObject):

    scene_changed = QtCore.Signal()
    scene_selection_changed = QtCore.Signal()

    def __init__(self, parent=None):
        self.parent = parent
        super(MayaHooks, self).__init__(parent=parent)
        self.callback_ids = defaultdict(list)
        self.scriptJobs = defaultdict(list)
        OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterOpen,
            self.emit_scene_changed
        )
        OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterNew,
            self.emit_scene_changed
        )
        OpenMaya.MEventMessage.addEventCallback(
            'SelectionChanged',
            self.emit_scene_selection_changed
        )

    def emit_scene_changed(self, *args):
        self.scene_changed.emit()

    def emit_scene_selection_changed(self, *args):
        self.scene_selection_changed.emit()

    def add_item_callbacks(self, node, attr, item, del_callback=None):

        def attr_changed(*args):
            with self.parent.maintain_obj_list():
                self.parent.refresh_obj_list()

        changed_id = pmc.scriptJob(
            attributeChange=[str(node) + '.' + attr, attr_changed],
            kws=True,
        )

        def cleanup(*args):
            callback_ids = self.callback_ids.get(pop, None)
            if callback_ids:
                OpenMaya.MMessage.removeCallbacks(callback_ids)
            if del_callback:
                del_callback()

        destroyed_id = OpenMaya.MNodeMessage.addNodeDestroyedCallback(
            node.__apimobject__(),
            cleanup,
        )
        self.callback_ids[node].append(destroyed_id)

    def clear_item_callbacks(self):
        for node, callback_ids in self.callback_ids.items():
            for callback_id in callback_ids:
                OpenMaya.MMessage.removeCallback(callback_id)
        self.callback_ids = defaultdict(list)

        for node, scriptjob_ids in self.scriptJobs.items():
            for scriptjob_id in scriptjob_ids:
                pmc.scriptJob(kill=scriptjob_id, force=True)
        self.scriptJobs = defaultdict(list)


class MatteController(MatteDialog):

    def __init__(self, parent=get_maya_window()):
        super(MatteController, self).__init__(parent=parent)

        self.matte_list.currentItemChanged.connect(self.matte_list_select)
        self.obj_list.currentItemChanged.connect(self.obj_list_select)
        self.button_new.clicked.connect(self.new_clicked)
        self.header.button_refresh.clicked.connect(self.refresh_matte_list)
        self.button_add.clicked.connect(self.add_clicked)
        self.button_red.clicked.connect(self.color_clicked(1, 0, 0))
        self.button_green.clicked.connect(self.color_clicked(0, 1, 0))
        self.button_blue.clicked.connect(self.color_clicked(0, 0, 1))
        self.button_white.clicked.connect(self.color_clicked(1, 1, 1))
        self.button_black.clicked.connect(self.color_clicked(0, 0, 0))
        self.refresh_matte_list()

        self.maya_hooks = MayaHooks(parent=self)
        self.maya_hooks.scene_changed.connect(self.refresh_matte_list)
        self.maya_hooks.scene_selection_changed.connect(self.scene_sel_changed)

    def set_aov(self, aov):
        self.aov = aov
        self.refresh_obj_list()

    def scene_sel_changed(self):
        count = self.obj_list.count()
        if count == 0:
            return

        selection = pmc.ls(sl=True)
        for i in xrange(count):
            item = self.obj_list.item(i)
            if item.pynode.getParent() in selection:
                item.setSelected(True)

    def selected_nodes(self):
        pre_select = self.obj_list.selectedItems()
        if pre_select:
            nodes = [item.pynode for item in pre_select]
        else:
            nodes = []

        return nodes

    def select_nodes(self, nodes):
        for i in xrange(self.obj_list.count()):
            item = self.obj_list.item(i)
            if item.pynode in nodes:
                item.setSelected(True)

    @contextmanager
    def maintain_obj_list(self):
        old_nodes = self.selected_nodes()
        try:
            yield
        except:
            raise
        finally:
            self.select_nodes(old_nodes)

    def color_clicked(self, *color):
        def on_click():
            items = self.obj_list.selectedItems()
            if not items:
                return

            with self.maintain_obj_list():
                nodes = [item.pynode for item in items]
                self.aov.set_objects_color(color, *nodes)
                self.refresh_obj_list()

        return on_click

    def add_clicked(self):
        if not self.aov:
            return

        self.aov.set_objects_color((1,1,1), *pmc.ls(sl=True, transforms=True))
        with self.maintain_obj_list():
            self.refresh_obj_list()

    def new_clicked(self):
        name = self.matte_line.text()
        if not name:
            self.matte_line.setFocus()
            return

        aov = MatteAOV.create(name)
        self.new_matte_item(aov)

    def new_matte_item(self, aov):
        item = QtGui.QListWidgetItem()
        item.pynode = aov

        del_callback = partial(self.delete_matte_item, item, aov)
        widget = MatteWidget(aov.name)
        widget.del_button.clicked.connect(del_callback)

        item.setSizeHint(widget.sizeHint())
        self.matte_list.addItem(item)
        self.matte_list.setItemWidget(item, widget)

    def delete_matte_item(self, item, aov):
        self.matte_list.takeItem(self.matte_list.indexFromItem(item).row())
        aov.delete()
        if aov == self.aov:
            self.aov = None
            self.obj_list.clear()

    def delete_obj_item(self, item, node):
        self.obj_list.takeItem(self.obj_list.indexFromItem(item).row())
        self.aov.discard(node)

    def new_obj_item(self, node, color):
        item = QtGui.QListWidgetItem()
        item.pynode = node

        del_callback = partial(self.delete_obj_item, item, node)
        widget = ObjectWidget(str(node))
        widget.del_button.clicked.connect(del_callback)
        widget.set_color(*color)

        item.setSizeHint(widget.sizeHint())
        self.obj_list.addItem(item)
        self.obj_list.setItemWidget(item, widget)
        self.maya_hooks.add_item_callbacks(
            node,
            self.aov.mesh_attr_name,
            item,
            del_callback
        )

    def refresh_matte_list(self):
        self.obj_list.clear()
        self.matte_list.clear()

        for aov in MatteAOV.ls():
            self.new_matte_item(aov)

    def refresh_obj_list(self):
        self.maya_hooks.clear_item_callbacks()
        self.obj_list.clear()
        for color, nodes in self.aov:
            for node in nodes:
                self.new_obj_item(node, color)

    def matte_list_select(self):
        item = self.matte_list.currentItem()
        if not item:
            return
        self.set_aov(item.pynode)
        self.refresh_obj_list()

    def obj_list_select(self):
        nodes = []
        items = self.obj_list.selectedItems()
        if not items:
            return

        for item in items:
            nodes.append(item.pynode)
        pmc.select(nodes, replace=True)
