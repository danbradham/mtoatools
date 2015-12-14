from PySide import QtGui, QtCore
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


class IconButton(QtGui.QLabel):

    clicked = QtCore.Signal()

    def __init__(self, icon, icon_hover, *args, **kwargs):
        super(IconButton, self).__init__(*args, **kwargs)

        self.normal = QtGui.QPixmap(QtGui.QImage(icon))
        self.hover = QtGui.QPixmap(QtGui.QImage(icon_hover))
        self.hovering = False
        self.setPixmap(self.normal)

    def mousePressEvent(self, event):

        self.setPixmap(self.normal)
        super(IconButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super(IconButton, self).mouseReleaseEvent(event)
        if self.hovering:
            self.setPixmap(self.hover)
            self.clicked.emit()
        else:
            self.setPixmap(self.normal)

    def enterEvent(self, event):

        self.setPixmap(self.hover)
        self.hovering = True
        super(IconButton, self).enterEvent(event)

    def leaveEvent(self, event):

        self.setPixmap(self.normal)
        self.hovering = False
        super(IconButton, self).leaveEvent(event)


class ObjectItem(QtGui.QListWidgetItem):

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


class ObjectWidget(QtGui.QWidget):

    def __init__(self, text, *args, **kwargs):
        super(ObjectWidget, self).__init__(*args, **kwargs)

        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

        if '|' in text:
            text = text.split('|')[-1]
        if len(text) > 20:
            text = text[:20] + '...'

        self.label = QtGui.QLabel(text)
        self.label.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum
        )

        self.del_button = IconButton(
            icon=ui_path('icons', 'delete.png'),
            icon_hover=ui_path('icons', 'delete_pressed.png'),
        )

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.del_button)

    def set_color(self, *color):
        style = 'QLabel{{color:rgb({},{},{});font-size: 12px;}}'
        self.label.setStyleSheet(style.format(*[c * 255 for c in color]))


class MatteWidget(QtGui.QWidget):

    def __init__(self, text, *args, **kwargs):
        super(MatteWidget, self).__init__(*args, **kwargs)

        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

        if '|' in text:
            text = text.split('|')[-1]
        if len(text) > 20:
            text = text[:20] + '...'

        self.label = QtGui.QLabel(text)
        self.label.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum
        )
        style = 'QLabel{font-size: 12px;}'
        self.label.setStyleSheet(style)

        self.del_button = IconButton(
            icon=ui_path('icons', 'delete.png'),
            icon_hover=ui_path('icons', 'delete_pressed.png'),
        )

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.del_button)


class MatteList(QtGui.QListWidget):

    def __init__(self, *args, **kwargs):
        super(MatteList, self).__init__(*args, **kwargs)
        self.setObjectName('mattelist')
        self.setSortingEnabled(True)


class ObjectList(QtGui.QListWidget):

    def __init__(self, *args, **kwargs):
        super(ObjectList, self).__init__(*args, **kwargs)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setObjectName('objectlist')
        self.setSortingEnabled(True)


class Header(QtGui.QWidget):

    def __init__(self, text, parent=None):
        super(Header, self).__init__(parent=parent)

        self.setFixedHeight(40)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setObjectName('header')
        self.layout = QtGui.QHBoxLayout()
        self.layout.setContentsMargins(20, 0, 20, 0)
        self.setLayout(self.layout)

        self.icon = QtGui.QLabel()
        self.icon.setFixedSize(32, 32)
        self.icon.setPixmap(QtGui.QPixmap(ui_path('icons', 'icon.png')))

        self.label = QtGui.QLabel(text)
        self.label.setObjectName('header_label')

        self.button_refresh = QtGui.QPushButton(get_icon('refresh'), '')
        self.button_refresh.setFixedSize(32, 32)
        self.button_refresh.setToolTip('Refresh')
        self.button_refresh.setObjectName('refresh')

        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button_refresh)


class MatteDialog(QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(MatteDialog, self).__init__(*args, **kwargs)

        self.header = Header('mtoatools.mattes')
        self.button_refresh = self.header.button_refresh

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setRowStretch(2, 1)
        self.grid.setColumnMinimumWidth(3, 30)

        self.matte_label = QtGui.QLabel('Matte AOVS')
        self.matte_label.setObjectName('title')
        self.matte_line = QtGui.QLineEdit()
        self.button_new = QtGui.QPushButton(get_icon('plus'), '')
        self.button_new.setFixedSize(32, 32)
        self.button_new.setToolTip('Add a new matte')
        self.matte_list = MatteList()

        self.obj_label = QtGui.QLabel('Shapes')
        self.obj_label.setObjectName('title')
        self.obj_list = ObjectList()
        self.button_add = QtGui.QPushButton(get_icon('plus'), '')
        self.button_add.setFixedSize(32, 32)
        self.button_add.setToolTip('Add selected transforms')
        self.button_red = QtGui.QPushButton()
        self.button_red.setFixedSize(32, 32)
        self.button_red.setObjectName('red')
        self.button_green = QtGui.QPushButton()
        self.button_green.setFixedSize(32, 32)
        self.button_green.setObjectName('green')
        self.button_blue = QtGui.QPushButton()
        self.button_blue.setFixedSize(32, 32)
        self.button_blue.setObjectName('blue')
        self.button_white = QtGui.QPushButton()
        self.button_white.setFixedSize(32, 32)
        self.button_white.setObjectName('white')
        self.button_black = QtGui.QPushButton()
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

        self.layout = QtGui.QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setRowStretch(1, 1)
        self.layout.addWidget(self.header, 0, 0)
        self.layout.addLayout(self.grid, 1, 0)
        self.setLayout(self.layout)
        self.setStyleSheet(get_style())
