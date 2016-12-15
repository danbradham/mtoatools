from tempfile import NamedTemporaryFile
import os
import sys
from Qt import QtWidgets, QtGui
try:
    from OpenGL.GL import *
    pyopengl_enabled = True
except ImportError:
    pyopengl_enabled = False
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMayaRender as omr
import maya.OpenMayaRender as omr1


def maya_useNewAPI():
    pass


TEXTURE_MANAGER = omr.MRenderer.getTextureManager()


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

    try:
        os.remove(tmp.name)
    except:
        pass

    return str(img.bits())


class Swatch(omui.MPxLocatorNode):

    id = om.MTypeId(0x00124dc1)
    name = 'Swatch'
    classification = 'drawdb/geometry/Swatch'
    registrantId = 'SwatchRegistrantId'
    tris = ([0, 1, 2], [2, 3, 0])
    verts = (om.MPoint(-1, -1, 0), om.MPoint(-1, 1, 0),
             om.MPoint(1, 1, 0), om.MPoint(1, -1, 0))
    coords = ([0, 0], [0, 1], [1, 1], [1, 0])

    def __init__(self):
        super(Swatch, self).__init__()
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

    def get_always_redraw(self):
        return om.MPlug(self.obj, self.always_redraw).asBool()

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
        if not pyopengl_enabled:
            return

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
        for tri in self.tris:
            for i in tri:
                uvs = self.coords[i]
                vert = self.verts[i]
                glTexCoord2f(*uvs)
                glVertex3f(vert[0], vert[1], vert[2])
        glEnd()

        glPopAttrib()
        view.endGL()

    def isBounded(self, *args):
        return True

    def boundingBox(self, *args):
        return om.MBoundingBox(om.MPoint(-1, -1, 0), om.MPoint(1, 1, 0))


class SwatchOverride(omr.MPxGeometryOverride):

    def __init__(self, obj):
        super(SwatchOverride, self).__init__(obj)
        self.obj = obj
        self.resolution = None
        self.width = None
        self.height = None
        self.color = None
        self._texture = None

    @classmethod
    def creator(cls, obj):
        return cls(obj)

    def get_texture(self):
        return self._texture

    def set_texture(self, tex):
        if self._texture:
            TEXTURE_MANAGER.releaseTexture(self._texture)
        self._texture = tex

    def __del__(self):
        if self._texture:
            TEXTURE_MANAGER.releaseTexture(self._texture)

    def get_color(self):
        return om.MPlug(self.obj, Swatch.inColor).asMDataHandle().asFloat3()

    def get_resolution(self):
        return om.MPlug(self.obj, Swatch.resolution).asInt()

    def supportedDrawAPIs(self):
        return omr.MRenderer.kOpenGL | omr.MRenderer.kOpenGLCoreProfile | omr.MRenderer.kDirectX11

    def hasUIDrawables(self):
        return True

    def updateDG(self):
        '''Retrieve and prepare data for drawing'''

        self.resolution = self.get_resolution()
        self.width = self.resolution
        self.height = self.resolution

        plug = om.MPlug(self.obj, Swatch.inColor)
        in_plugs = plug.connectedTo(True, False)
        if in_plugs:
            in_in_plugs = in_plugs[0].connectedTo(True, False)
            color_plug = in_in_plugs[0] if in_in_plugs else in_plugs[0]

            if color_plug.attribute().apiTypeStr != 'kAttribute3Float':
                self.color = om.MColor([1, 1, 1])
                self.set_texture(None)

            color_node = color_plug.node()
            if color_node.apiTypeStr == 'kFileTexture':
                depfn = om.MFnDependencyNode(color_node)
                file = depfn.findPlug('fileTextureName', False).asString()
                self.set_texture(TEXTURE_MANAGER.acquireTexture(
                    '',
                    color_plug,
                    self.width,
                    self.height,
                    False))
            else:
                self.set_texture(TEXTURE_MANAGER.acquireTexture(
                    '',
                    color_plug,
                    self.width,
                    self.height,
                    False)
                )
        else:
            self.set_texture(None)
            self.color = om.MColor(self.get_color())

    def addUIDrawables(self, dagpath, draw_manager, frame_context):
        draw_manager.beginDrawable()
        texture = self.get_texture()

        if texture:
            draw_manager.setTexture(texture)
        else:
            draw_manager.setColor(self.color)

        draw_manager.rect(
            om.MPoint(0, 0, 0),
            om.MVector(0, -1, 0),
            om.MVector(0, 0, 1),
            1,
            1,
            True,
        )

        draw_manager.endDrawable()

    def isStreamDirty(self, *args):
        return False

    def isIndexingDirty(self, *args):
        return False

    def cleanUp(self):
        pass

    def updateRenderItems(self, path, render_items):
        return render_items

    def populateGeometry(self, requirements, render_items, data):
        return data


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Autodesk", "3.0", "Any")

    try:
        plugin.registerNode(
            Swatch.name,
            Swatch.id,
            Swatch.creator,
            Swatch.initialize,
            om.MPxNode.kLocatorNode,
            Swatch.classification
        )
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        omr.MDrawRegistry.registerGeometryOverrideCreator(
            Swatch.classification,
            Swatch.registrantId,
            SwatchOverride.creator
        )
    except:
        sys.stderr.write("Failed to register override\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    try:
        plugin.deregisterNode(Swatch.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        pass

    try:
        omr.MDrawRegistry.deregisterGeometryOverrideCreator(
            Swatch.classification,
            Swatch.registrantId,
        )
    except:
        sys.stderr.write("Failed to deregister override\n")
        pass
