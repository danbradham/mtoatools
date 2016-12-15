from Qt import QtWidgets, QtCore, QtGui
import os

this_package = os.path.dirname(__file__)


def ui_path(*paths):
    return os.path.join(this_package, *paths)


def get_style(style=[]):
    if not style:
        style_path = ui_path('style.css')
        if os.path.exists(style_path):
            with open(style_path, 'r') as f:
                style.append(f.read())
    return style[0]


def get_icon(name, cache={}):
    if name in cache:
        return cache[name]

    off = ui_path('icons', name + '.png')
    on = ui_path('icons', name + '_pressed.png')

    icon = QtGui.QIcon()
    size = QtCore.QSize(24, 24)
    icon.addFile(off, size, QtGui.QIcon.Normal, QtGui.QIcon.On)
    icon.addFile(on, size, QtGui.QIcon.Active, QtGui.QIcon.On)
    cache[name] = icon
    return icon


class IconButton(QtWidgets.QLabel):

    clicked = QtCore.Signal()
    cache = {}

    def __init__(self, icon, icon_hover, *args, **kwargs):
        super(IconButton, self).__init__(*args, **kwargs)

        if icon not in self.cache:
            self.cache[icon] = QtGui.QPixmap(QtGui.QImage(icon))
        if icon_hover not in self.cache:
            self.cache[icon_hover] = QtGui.QPixmap(QtGui.QImage(icon_hover))

        self.normal = self.cache[icon]
        self.hover = self.cache[icon_hover]
        self.hovering = False
        self.setPixmap(self.normal)

    def mousePressEvent(self, event):

        self.setPixmap(self.normal)
        super(IconButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.hovering:
            self.setPixmap(self.hover)
        else:
            self.setPixmap(self.normal)
        super(IconButton, self).mouseReleaseEvent(event)
        if self.hovering:
            self.clicked.emit()

    def enterEvent(self, event):

        self.setPixmap(self.hover)
        self.hovering = True
        super(IconButton, self).enterEvent(event)

    def leaveEvent(self, event):

        self.setPixmap(self.normal)
        self.hovering = False
        super(IconButton, self).leaveEvent(event)


class ObjectItem(QtWidgets.QListWidgetItem):

    def __init__(self, aov, pynode, widget, *args, **kwargs):
        super(ObjectItem, self).__init__(*args, **kwargs)
        self.pynode = pynode
        self.widget = widget
        self.aov = aov

    def __lt__(self, other):
        return self.color() < other.color()

    def color(self):
        return self.pynode.attr(self.aov.mesh_attr_name).get()

    def refresh_color(self):
        self.widget.set_color(*self.color())


class ObjectWidget(QtWidgets.QWidget):

    color_cache = {}

    def __init__(self, text, *args, **kwargs):
        super(ObjectWidget, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        if '|' in text:
            text = text.split('|')[-1]
        if len(text) > 24:
            text = text[:24] + '...'

        self.label = QtWidgets.QLabel(text)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )

        self.del_button = IconButton(
            icon=ui_path('icons', 'delete.png'),
            icon_hover=ui_path('icons', 'delete_pressed.png'),
        )

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.del_button)

    def set_color(self, *color):
        if color not in self.color_cache:
            style = 'QLabel{{ color:rgb({},{},{}); font-size: 14px;}}'
            self.color_cache[color] = style.format(*[c * 255 for c in color])

        self.label.setStyleSheet(self.color_cache[color])


class MatteWidget(QtWidgets.QWidget):

    edited = QtCore.Signal(str)

    def __init__(self, text, *args, **kwargs):
        super(MatteWidget, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        if '|' in text:
            text = text.split('|')[-1]
        if len(text) > 24:
            text = text[:24] + '...'

        self.label = QtWidgets.QLabel(text)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        style = 'QLabel{font-size: 14px;}'
        self.label.setStyleSheet(style)

        self.editor = QtWidgets.QLineEdit()
        self.editor.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        style = 'QLineEdit{font-size: 14px; border:0;}'
        self.editor.setStyleSheet(style)
        self.editor.editingFinished.connect(self.finish_edit)
        self.editor.installEventFilter(self)

        self.editor.hide()

        self.del_button = IconButton(
            icon=ui_path('icons', 'delete.png'),
            icon_hover=ui_path('icons', 'delete_pressed.png'),
        )

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.editor)
        self.layout.addWidget(self.del_button)

        self.installEventFilter(self)

    def eventFilter(self, widget, event):
        '''Start editing when MatteWidget is double clicked...'''

        if widget == self.editor:
            is_keypress = (event.type() == QtCore.QEvent.KeyPress)
            is_keyesc = (event.key() == QtCore.Qt.Key_Escape)
            if is_keypress and is_keyesc:
                self.abort_edit()
                return True

        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.start_edit()
            return True

        return super(MatteWidget, self).eventFilter(widget, event)

    def start_edit(self):
        self.label.hide()
        self.editor.setText(self.label.text())
        self.editor.show()
        self.editor.setFocus()
        self.editor.selectAll()

    def abort_edit(self):
        self.editor.setText(self.label.text())
        self.editor.hide()
        self.label.show()

    def finish_edit(self):
        self.editor.hide()
        old_label = self.label.text()
        self.label.setText(self.editor.text())
        new_label = self.label.text()
        self.label.show()

        if new_label != old_label:
            self.edited.emit(new_label)


class MatteList(QtWidgets.QListWidget):

    def __init__(self, *args, **kwargs):
        super(MatteList, self).__init__(*args, **kwargs)
        self.setObjectName('mattelist')
        self.setSortingEnabled(True)


class ObjectList(QtWidgets.QListWidget):

    def __init__(self, *args, **kwargs):
        super(ObjectList, self).__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setObjectName('objectlist')
        self.setSortingEnabled(True)


class Header(QtWidgets.QWidget):

    def __init__(self, text, parent=None):
        super(Header, self).__init__(parent=parent)

        self.setFixedHeight(40)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setObjectName('header')
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(20, 0, 20, 0)
        self.setLayout(self.layout)

        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(32, 32)
        self.icon.setPixmap(QtGui.QPixmap(ui_path('icons', 'icon.png')))

        self.label = QtWidgets.QLabel(text)
        self.label.setObjectName('header_label')

        self.button_refresh = QtWidgets.QPushButton(get_icon('refresh'), '')
        self.button_refresh.setFixedSize(32, 32)
        self.button_refresh.setToolTip('Refresh')
        self.button_refresh.setObjectName('headerbutton')

        self.button_help = QtWidgets.QPushButton(get_icon('help'), '')
        self.button_help.setFixedSize(32, 32)
        self.button_help.setToolTip('Help')
        self.button_help.setObjectName('headerbutton')

        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button_refresh)
        self.layout.addWidget(self.button_help)


class MatteSaveDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        super(MatteSaveDialog, self).__init__(*args, **kwargs)

        self.label = QtWidgets.QLabel('Save selected mattes')

        self.matte_list = MatteList()
        self.matte_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.matte_list)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        self.setWindowTitle('Save Matte AOVS')


class MatteLoadDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        super(MatteLoadDialog, self).__init__(*args, **kwargs)

        self.label = QtWidgets.QLabel('Load selected mattes')

        self.matte_list = MatteList()
        self.matte_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.ignore_namespaces = QtWidgets.QCheckBox('ignore namespaces')

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Apply | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(
            self.accept
        )
        self.button_box.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.matte_list)
        self.layout.addWidget(self.ignore_namespaces)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        self.setWindowTitle('Load Matte AOVS')


class MatteDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        super(MatteDialog, self).__init__(*args, **kwargs)

        self.menu_bar = QtWidgets.QMenuBar()
        self.file_menu = self.menu_bar.addMenu('file')

        self.header = Header('mtoatools.mattes')
        self.button_refresh = self.header.button_refresh
        self.button_help = self.header.button_help

        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setRowStretch(2, 1)
        self.grid.setColumnMinimumWidth(3, 30)

        self.matte_label = QtWidgets.QLabel('Matte AOVS')
        self.matte_label.setObjectName('title')
        self.matte_line = QtWidgets.QLineEdit()
        self.button_new = QtWidgets.QPushButton(get_icon('plus'), '')
        self.button_new.setFixedSize(32, 32)
        self.button_new.setToolTip('Add a new matte')
        self.matte_list = MatteList()

        self.obj_label = QtWidgets.QLabel('Shapes')
        self.obj_label.setObjectName('title')
        self.obj_list = ObjectList()
        self.button_add = QtWidgets.QPushButton(get_icon('plus'), '')
        self.button_add.setFixedSize(32, 32)
        self.button_add.setToolTip('Add selected transforms')
        self.button_red = QtWidgets.QPushButton()
        self.button_red.setFixedSize(32, 32)
        self.button_red.setObjectName('red')
        self.button_green = QtWidgets.QPushButton()
        self.button_green.setFixedSize(32, 32)
        self.button_green.setObjectName('green')
        self.button_blue = QtWidgets.QPushButton()
        self.button_blue.setFixedSize(32, 32)
        self.button_blue.setObjectName('blue')
        self.button_white = QtWidgets.QPushButton()
        self.button_white.setFixedSize(32, 32)
        self.button_white.setObjectName('white')
        self.button_black = QtWidgets.QPushButton()
        self.button_black.setFixedSize(32, 32)
        self.button_black.setObjectName('black')

        self.grid.addWidget(self.matte_label, 0, 0, 1, 3)
        self.grid.addWidget(self.matte_line, 1, 0, 1, 2)
        self.grid.addWidget(self.button_new, 1, 2, 1, 1)
        self.grid.addWidget(self.matte_list, 2, 0, 1, 3)

        self.grid.addWidget(self.obj_label, 0, 4, 1, 5)
        self.grid.addWidget(self.button_red, 1, 4, 1, 1)
        self.grid.addWidget(self.button_green, 1, 5, 1, 1)
        self.grid.addWidget(self.button_blue, 1, 6, 1, 1)
        self.grid.addWidget(self.button_white, 1, 7, 1, 1)
        self.grid.addWidget(self.button_black, 1, 8, 1, 1)
        self.grid.addWidget(self.button_add, 1, 9, 1, 1)
        self.grid.addWidget(self.obj_list, 2, 4, 1, 6)

        self.layout = QtWidgets.QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setRowStretch(2, 1)
        self.layout.addWidget(self.menu_bar, 0, 0)
        self.layout.addWidget(self.header, 1, 0)
        self.layout.addLayout(self.grid, 2, 0)
        self.setLayout(self.layout)
        self.setStyleSheet(get_style())
