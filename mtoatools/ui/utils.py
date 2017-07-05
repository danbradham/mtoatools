import time
from Qt import QtWidgets


def get_maya_window():
    '''Get Maya MainWindow as a QWidget.'''
    for widget in QtWidgets.QApplication.instance().topLevelWidgets():
        if widget.objectName() == 'MayaWindow':
            return widget
    raise RuntimeError('Could not locate MayaWindow...')


def wait(delay=1):
    '''Delay python execution for a specified amount of time'''

    s = time.clock()

    while True:
        if time.clock() - s >= delay:
            return
        QtWidgets.QApplication.instance().processEvents()
