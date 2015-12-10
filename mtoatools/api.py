from operator import itemgetter
from collections import defaultdict
import pymel.core as pmc
from mtoa import aovs, core
from .utils import add_vector_attr, get_next_name

__all__ = ['Defaults', 'create_aov', 'MatteAOV']


class Defaults(object):

    def __init__(self):
        self._driver = None
        self._filter = None
        self._options = None

    @property
    def driver(self):
        if not self._driver:
            self._driver = pmc.PyNode('defaultArnoldDriver')
        return self._driver

    @property
    def filter(self):
        if not self._driver:
            self._driver = pmc.PyNode('defaultArnoldFilter')
        return self._driver

    @property
    def options(self):
        if not self._driver:
            self._driver = pmc.PyNode('defaultArnoldRenderOptions')
        return self._driver

Defaults = Defaults()


def create_aov(name, _type):
    '''Create a new aov

    :param name: Name of the new aov
    :param _type: Type of the aov to create
    '''

    return aovs.AOVInterface().addAOV(name, aovType=_type)


class MatteAOV(object):
    '''Arnold Matte AOV object. Used to manipulate a vector aov as if it were
    a set.
    '''

    def __init__(self, aov, user_data):
        self.aov = aov
        self.user_data = user_data

    @classmethod
    def create(cls, name):
        if pmc.objExists('aiAOV_' + name):
            name = get_next_name(name)

        selected = pmc.selected(type='transform')

        aov = create_aov(name, 'vector').node
        aov.addAttr('is_aov_matte', at='bool', dv=1)
        aov_name = str(aov).replace('aiAOV_', '')

        user_data = pmc.createNode('aiUserDataColor', name=aov_name + '_color')
        user_data.colorAttrName.set(aov_name)
        user_data.outColor.connect(aov.defaultValue)

        attr_name = 'mtoa_constant_' + aov_name
        for node in selected:
            shape = node.getShape()
            add_vector_attr(shape, attr_name)
            shape.attr(attr_name).set(1, 1, 1)

        return cls(aov, user_data)

    @property
    def name(self):
        return self.aov.attr('name').get()

    @property
    def color_attr_name(self):
        return self.user_data.colorAttrName.get()

    @property
    def mesh_attr_name(self):
        return 'mtoa_constant_' + self.color_attr_name

    def get_sorted_objects(self):
        objects = defaultdict(list)
        for node in self.get_objects():
            color = tuple(node.attr(self.mesh_attr_name).get())
            objects[color].append(node)

        return sorted(objects.items(), key=itemgetter(0))

    def get_objects(self):
        return pmc.ls('*.' + self.mesh_attr_name, r=True, objectsOnly=True)

    def __iter__(self):
        for color, nodes in self.get_sorted_objects():
            yield color, nodes

    def add(self, *nodes):
        for node in nodes:
            if node.type() == 'transform':
                node = node.getShape()
            if not hasattr(node, self.mesh_attr_name):
                add_vector_attr(node, self.mesh_attr_name)

    def discard(self, *nodes):
        for node in nodes:
            if (node.type() == 'transform'
                and not hasattr(node, self.mesh_attr_name)):
                node = node.getShape()
            if hasattr(node, self.mesh_attr_name):
                node.attr(self.mesh_attr_name).delete()

    def set_default_color(self, rgb):
        self.user_data.defaultValue.set(*rgb)

    def set_all_objects_color(self, rgb):
        for node in self.get_objects():
            node.attr(self.mesh_attr_name).set(*rgb)

    def set_objects_color(self, rgb, *nodes):
        for node in nodes:
            if not hasattr(node, self.mesh_attr_name):
                add_vector_attr(node, self.mesh_attr_name)
            node.attr(self.mesh_attr_name).set(*rgb)

    def delete(self):
        self.rem_objects(*self.get_objects())
        pmc.delete(self.aov)
        pmc.delete(self.user_data)

    @classmethod
    def ls(cls):
        aovs = []
        for node in pmc.ls('*.is_aov_matte', r=True, objectsOnly=True):
            aov.append(cls(node, node.defaultValue.inputs()[0]))
        return aovs


def show_matte_aov_ui(instance=[]):
    from .ui.controllers import MatteController
    if not instance:
        instance.append(MatteController())

    controller = instance[0]
    controller.show()
    return controller
