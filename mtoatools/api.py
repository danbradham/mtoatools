'''
mtoatools.api
=============
Public facing classes and functions
'''

from collections import Sequence
from maya import cmds
from .models import MatteAOV
from .plugins import load


def matte_aov(name):
    return MatteAOV.create(name)


def swatch(name):
    load('swatch')
    shape = cmds.createNode('Swatch', name=name + 'Shape')
    xform = cmds.listRelatives(shape, parent=True)[0]
    xform = cmds.rename(xform, name)
    shape = cmds.listRelatives(xform, shapes=True)[0]
    return xform, shape


def apply_swatch(lights=None):
    '''Apply swatch to lights'''

    light_types = ['VRayRectLight', 'aiAreaLight', 'areaLight', 'spotLight']
    if not lights:
        lights = cmds.ls(sl=True)

    if isinstance(lights, basestring):
        lights = [lights]
    elif not isinstance(lights, Sequence):
        return

    light_xforms_shapes = []
    for light in lights:
        if cmds.nodeType(light) == 'transform':
            xform = light
            shape = cmds.listRelatives(light, shapes=True)
            if shape:
                if cmds.nodeType(shape[0]) not in light_types:
                    continue
                light_xforms_shapes.append((xform, shape[0]))

        if cmds.nodeType(light) in light_types:
            shape = light
            xform = cmds.listRelatives(light, parent=True)[0]
            light_xforms_shapes.append((xform, shape))

    swatches = []
    for xform, shape in light_xforms_shapes:

        if not cmds.objExists(shape + '.viewportResolution'):
            cmds.addAttr(shape, ln='viewportResolution', sn='vpres', hnv=True,
                          hxv=True, min=32, max=1024, at='long')
            cmds.addAttr(shape, ln='viewportPreview', sn='vpprev', at='bool',
                          dv=1, k=True)

        sw_xform, sw_shape = swatch(str(xform) + '_swatch')
        cmds.setAttr(sw_shape + '.overrideEnabled', True)
        cmds.setAttr(sw_shape + '.overrideDisplayType', 2)

        cmds.connectAttr(shape + '.color', sw_shape + '.inColor')
        cmds.connectAttr(shape + '.viewportResolution',
                         sw_shape + '.resolution')
        cmds.connectAttr(shape + '.viewportPreview',
                         sw_shape + '.visibility')

        cmds.parent(sw_xform, xform, relative=True)
        swatches.append((sw_xform, sw_shape))

    return swatches


def show_mattes_ui(instance=[]):
    '''Show the mtoatools mattes ui'''
    from .ui.controllers import MattesController
    if not instance:
        instance.append(MattesController())

    controller = instance[0]
    controller.show()
    return controller
