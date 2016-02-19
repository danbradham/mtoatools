from tempfile import NamedTemporaryFile
from PySide import QtGui
from OpenGL.GL import *
from collections import Sequence, OrderedDict
import os
import sys
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMayaRender as omr
import maya.OpenMayaRender as omr1


def maya_useNewAPI():
    pass

glRenderer = omr1.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()
TEXTURE_MANAGER = omr.MRenderer.getTextureManager()

verts = (
    om.MPoint(-1, -1, 0), om.MPoint(-1, 1, 0),
    om.MPoint(1, 1, 0), om.MPoint(1, -1, 0),
)
tris = ([0, 1, 2], [2, 3, 0])
coords = ([0, 0], [0, 1], [1, 1], [1, 0])


def pointarray(l):
    '''Converts a list of vectors/points to an MPointArray'''

    return om.MPointArray([point(x) for x in l])


def get_bytes(plug, resolution):
    '''Get color plug with incoming connection as a string'''

    tex = TEXTURE_MANAGER.acquireTexture(
        plug.name(),
        plug,
        resolution,
        resolution,
        False)
    tmp = NamedTemporaryFile(suffix='.png')
    tmp.close()
    TEXTURE_MANAGER.saveTexture(tex, tmp.name)
    TEXTURE_MANAGER.releaseTexture(tex)

    # swap red and blue channels and flip horizontally
    img = QtGui.QImage(tmp.name).rgbSwapped().mirrored(True, False)

    try: # clean up
        os.remove(tmp.name)
    except:
        pass

    return str(img.bits())


def topmost_plug(plug):

    plugs = []
    plugs.append(plug)

    while True:
        in_plugs = plugs[-1].connectedTo(True, False)
        if not in_plugs:
            return plugs[-1]
        plugs.append(in_plugs[0])


def create(light_shapes=None):
    if not light_shapes:
        light_shapes = cmds.ls(sl=True, dag=True, leaf=True, lights=True)

    if isinstance(light_shapes, basestring):
        light_shapes = [light_shapes]
    elif not isinstance(light_shapes, Sequence):
        return

    locs = []
    for shape in light_shapes:
        loc = cmds.createNode('colorSwatch')
        cmds.setAttr(loc + '.overrideEnabled', True)
        cmds.setAttr(loc + '.overrideDisplayType', 2) # Reference display type

        # Add and connect attributes
        shape_xform = cmds.listRelatives(shape, parent=True)[0]
        if not cmds.objExists(shape + '.viewportResolution'):
            cmds.addAttr(shape, ln='viewportResolution', sn='vpres', hnv=True, hxv=True, min=32, max=1024, at='long')
            cmds.addAttr(shape, ln='viewportPreview', sn='vpprev', at='bool', dv=1, k=True)
        cmds.connectAttr(shape + '.message', loc + '.lightShape')
        cmds.connectAttr(shape +'.viewportResolution', loc + '.resolution')
        cmds.connectAttr(shape + '.viewportPreview', loc + '.visibility')

        # Parent locator
        loc_xform = cmds.listRelatives(loc, parent=True)[0]
        cmds.parent(loc_xform, shape_xform, relative=True)
        locs.append((loc_xform, loc))

    return locs


class ColorSwatch(omui.MPxLocatorNode):
    '''A Locator with variable shape'''

    id = om.MTypeId(0x00124dc1)
    name = 'colorSwatch'
    classification = 'drawdb/geometry/colorSwatch'
    registrantId = 'colorSwatchRegistrantId'

    def __init__(self):
        super(ColorSwatch, self).__init__()
        self.texture = None
        self.texture_res = 32
        self.color = [0, 0, 0]
        self.res = 32

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):
        numFn = om.MFnNumericAttribute()

        cls.inColor = numFn.createColor('inColor', 'ic')
        numFn.keyable = True
        numFn.storable = True
        numFn.readable = True
        numFn.writable = True
        numFn.default = (0, 0, 0)

        cls.resolution = numFn.create('resolution', 'res', om.MFnNumericData.kInt)
        numFn.keyable = True
        numFn.storable = True
        numFn.readable = True
        numFn.writable = True
        numFn.setMin(32)
        numFn.setMax(1024)
        numFn.default = 32

        cls.sentinel = numFn.create('sentinel', 'sntl', om.MFnNumericData.kBoolean)
        numFn.hidden = True
        numFn.default = True

        om.MPxNode.addAttribute(cls.inColor)
        om.MPxNode.addAttribute(cls.resolution)
        om.MPxNode.addAttribute(cls.sentinel)
        om.MPxNode.attributeAffects(cls.inColor, cls.sentinel)
        om.MPxNode.attributeAffects(cls.resolution, cls.sentinel)

    @property
    def obj(self):
        return self.thisMObject()

    def get_color(self):
        return om.MPlug(self.obj, self.inColor).asMDataHandle().asFloat3()

    def get_texture(self):
        plug = om.MPlug(self.obj, self.inColor)
        in_plug = plug.connectedTo(True, False)[0]
        in_plugs = plug.connectedTo(True, False)
        if in_plugs:
            in_plug = in_plugs[0]
        if in_plug.attribute().apiTypeStr != 'kAttribute3Float':
            return None
        return get_bytes(in_plug, self.res)

    def color_is_connected(self):
        return om.MPlug(self.obj, self.inColor).connectedTo(True, False)

    def get_resolution(self):
        return om.MPlug(self.obj, self.resolution).asInt()

    def force_compute(self):
        return om.MPlug(self.obj, self.sentinel).asBool()

    def compute(self, plug, data):
        if plug == self.sentinel:
            self.res = self.get_resolution()

            if self.color_is_connected():
                regen = (not data.isClean(self.inColor)
                         or not self.texture
                         or self.texture_res != self.res)
                if regen:
                    self.texture = self.get_texture()
                    self.texture_res = self.res
                self.color = [1, 1, 1]
            else:
                self.color = self.get_color()
                self.texture = None
                self.texture_res = self.res

    def draw(self, view, path, style, status):
        self.force_compute()

        width = height = self.res

        view.beginGL()
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glEnable(GL_BLEND)
        if self.texture:
            texture = glGenTextures(1)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                width,
                height,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                self.texture)
            glEnable(GL_TEXTURE_2D)
            glColor3f(*self.color)
        else:
            glColor3f(*self.color)

        glBegin(GL_TRIANGLES)
        for tri in tris:
            for i in tri:
                uvs = coords[i]
                vert = verts[i]
                glTexCoord2f(*uvs)
                glVertex3f(vert[0], vert[1], vert[2])
        glEnd()

        glPopAttrib()
        view.endGL()

    def isBounded(self, *args):
        return True

    def boundingBox(self, *args):
        return om.MBoundingBox(om.MPoint(-1, -1, 0), om.MPoint(1, 1, 0))


class ColorSwatchData(om.MUserData):

    def __init__(self):
        super(ColorSwatchData, self).__init__(True)
        self.resolution = None
        self.width = None
        self.height = None
        self.color = None
        self._texture = None
        self.is_file_texture = None
        self.line = None

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, tex):
        if self._texture:
            TEXTURE_MANAGER.releaseTexture(self._texture)
        self._texture = tex

    def __del__(self):
        if self.texture:
            TEXTURE_MANAGER.releaseTexture(self.texture)


class ColorSwatchOverride(omr.MPxDrawOverride):

    def __init__(self, obj):
        super(ColorSwatchOverride, self).__init__(obj, self.draw)
        self.obj = obj

    @classmethod
    def creator(cls, obj):
        return cls(obj)

    def isBounded(self, *args):
        return False

    def disableInternalBoundingBox(self, *args):
        return True

    def get_color(self):
        return om.MPlug(self.obj, ColorSwatch.inColor).asMDataHandle().asFloat3()

    def get_resolution(self):
        return om.MPlug(self.obj, ColorSwatch.resolution).asInt()

    def force_compute(self):
        return om.MPlug(self.obj, ColorSwatch.sentinel).asBool()

    def prepareForDraw(self, dagpath, camera_path, frame_context, data):
        '''Validate and update cache'''
        if not isinstance(data, ColorSwatchData):
            data = ColorSwatchData()

        data.resolution = self.get_resolution()
        data.width = data.resolution
        data.height = data.resolution

        plug = om.MPlug(self.obj, ColorSwatch.inColor)
        in_plugs = plug.connectedTo(True, False)
        if in_plugs:
            in_in_plugs = in_plugs[0].connectedTo(True, False)
            color_plug = in_in_plugs[0] if in_in_plugs else in_plugs[0]

            if color_plug.attribute().apiTypeStr != 'kAttribute3Float':
                data.color = om.MColor([1, 1, 1])
                data.texture = None
                data.is_file_texture = False

            color_node = color_plug.node()
            if color_node.apiTypeStr == 'kFileTexture':
                depfn = om.MFnDependencyNode(color_node)
                file = depfn.findPlug('fileTextureName', False).asString()
                data.is_file_texture = True
                data.texture = TEXTURE_MANAGER.acquireTexture(file)
            else:
                data.is_file_texture = False
                data.texture = TEXTURE_MANAGER.acquireTexture(
                    '',
                    color_plug,
                    data.width,
                    data.height,
                    False)
        else:
            data.texture = None
            data.is_file_texture = False
            data.color = om.MColor(self.get_color())

        return data

    def supportedDrawAPIs(self):
        return omr.MRenderer.kOpenGL | omr.MRenderer.kOpenGLCoreProfile | omr.MRenderer.kDirectX11

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, dagpath, draw_manager, frame_context, data):
        if not isinstance(data, ColorSwatchData):
            return

        draw_manager.beginDrawable()

        if data.texture:
            print 'dat data'
            draw_manager.setTexture(data.texture)
        else:
            draw_manager.setColor(data.color)
        draw_manager.rect(
            om.MPoint(0, 0, 0),
            om.MVector(0, 1, 0) if data.is_file_texture else om.MVector(0, -1, 0),
            om.MVector(0, 0, -1) if data.is_file_texture else om.MVector(0, 0, 1),
            1,
            1,
            True,
        )

        draw_manager.endDrawable()

    @staticmethod
    def draw(self, draw_context, *args):
        '''
        Drawing method unnecessary.
        Used only for MPxDrawOverride Construction
        '''
        pass


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Autodesk", "3.0", "Any")

    try:
        plugin.registerNode(
            ColorSwatch.name,
            ColorSwatch.id,
            ColorSwatch.creator,
            ColorSwatch.initialize,
            om.MPxNode.kLocatorNode,
            ColorSwatch.classification
        )
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(
            ColorSwatch.classification,
            ColorSwatch.registrantId,
            ColorSwatchOverride.creator
        )
    except:
        sys.stderr.write("Failed to register override\n")
        raise

def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(ColorSwatch.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        pass

    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(
            ColorSwatch.classification,
            ColorSwatch.registrantId,
        )
    except:
        sys.stderr.write("Failed to deregister override\n")
        pass
