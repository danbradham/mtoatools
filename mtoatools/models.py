'''
mtoatools.models
================
'''

from operator import itemgetter
from collections import defaultdict
import pymel.core as pmc
from .utils import add_vector_attr, get_next_name
from .packages import yaml

__all__ = ['Defaults', 'create_aov', 'MatteAOV']


class Defaults(object):

    def __init__(self):
        self._driver = None
        self._filter = None
        self._options = None

    @property
    def driver(self):
        if not self._driver:
            try:
                self._driver = pmc.PyNode('defaultArnoldDriver')
            except TypeError:
                raise Exception('Arnod is not the current renderer')
        return self._driver

    @property
    def filter(self):
        if not self._driver:
            try:
                self._driver = pmc.PyNode('defaultArnoldFilter')
            except TypeError:
                raise Exception('Arnod is not the current renderer')
        return self._driver

    @property
    def options(self):
        if not self._driver:
            try:
                self._driver = pmc.PyNode('defaultArnoldRenderOptions')
            except TypeError:
                raise Exception('Arnod is not the current renderer')
        return self._driver

Defaults = Defaults()


def create_aov(name, _type):
    '''Create a new aov

    :param name: Name of the new aov
    :param _type: Type of the aov to create
    '''

    import mtoa.aovs
    return mtoa.aovs.AOVInterface().addAOV(name, aovType=_type)


class MatteAOV(object):
    '''Arnold Matte AOV object. Used to manipulate a vector aov as if it were
    a set.
    '''

    def __init__(self, aov, user_data):
        self.aov = aov
        self.user_data = user_data

    def __repr__(self):
        return '<MatteAOV>({}, {})'.format(str(self.aov), str(self.user_data))

    def __iter__(self):
        for node in self.get_objects():
            yield node, node.attr(self.mesh_attr_name).get()

    @classmethod
    def create(cls, name):
        name = cls.get_unused_name(name)

        selected = pmc.selected(type='transform')

        aov = create_aov(name, 'vector').node
        aov.addAttr('is_aov_matte', at='bool', dv=1)
        aov_name = str(aov).replace('aiAOV_', '')

        user_data = pmc.createNode('aiUserDataColor', name=aov_name + '_color')
        user_data.colorAttrName.set(aov_name)
        user_data.outColor.connect(aov.defaultValue)

        aov = cls(aov, user_data)
        aov.set_objects_color((1, 1, 1), *selected)

        return aov

    @classmethod
    def ls(cls):
        aovs = []
        for node in pmc.ls('*.is_aov_matte', r=True, objectsOnly=True):
            inputs = node.defaultValue.inputs()
            if inputs:
                aovs.append(cls(node, inputs[0]))
        return aovs

    @staticmethod
    def get_unused_name(name):
        if pmc.objExists('aiAOV_' + name):
            name = get_next_name(name)
        return name

    @property
    def name(self):
        return self.aov.attr('name').get()

    def rename(self, name):
        name = self.get_unused_name(name)
        mesh_attr_name = 'mtoa_constant_' + name

        # Rename mesh attributes
        for obj in self.get_objects():
            old_attr = str(obj.attr(self.mesh_attr_name))
            pmc.renameAttr(old_attr, mesh_attr_name)
            for c in 'RGB':
                pmc.renameAttr(old_attr + c, mesh_attr_name + c)

        # Rename AOV
        self.aov.attr('name').set(name)
        self.aov.rename('aiAOV_' + name)

        # Rename aiUserData and change attribute name
        self.user_data.rename(name + '_color')
        self.user_data.colorAttrName.set(name)

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

        return sorted(objects.items(), key=itemgetter(0), reverse=True)

    def get_objects(self):
        ls = set(pmc.ls('*.' + self.mesh_attr_name, r=True, objectsOnly=True))
        return list(ls)

    def add(self, *nodes):
        added_nodes = []
        for node in nodes:
            if node.type() == 'transform':
                node = node.getShape()
            if not hasattr(node, self.mesh_attr_name):
                add_vector_attr(node, self.mesh_attr_name)
                added_nodes.append(node)
        return added_nodes

    def discard(self, *nodes):
        removed_nodes = []
        for node in nodes:
            if (node.type() == 'transform'
                and not hasattr(node, self.mesh_attr_name)):
                node = node.getShape()
            if hasattr(node, self.mesh_attr_name):
                node.attr(self.mesh_attr_name).delete()
                removed_nodes.append(node)
        return removed_nodes

    def set_default_color(self, rgb):
        self.user_data.defaultValue.set(*rgb)

    def set_all_objects_color(self, rgb):
        for node in self.get_objects():
            node.attr(self.mesh_attr_name).set(*rgb)

    def set_objects_color(self, rgb, *nodes):
        for node in nodes:
            if node.type() == 'transform':
                node = node.getShape()
            if not hasattr(node, self.mesh_attr_name):
                self.add(node)
            node.attr(self.mesh_attr_name).set(*rgb)

    def delete(self):
        self.discard(*self.get_objects())
        pmc.delete(self.aov)
        pmc.delete(self.user_data)

    def data(self):
        '''Simple dict representation of matte aov for use with serialization
        '''

        data = {'name': self.name, 'shapes': []}
        for obj in self.get_objects():
            full_name = str(obj)
            parts = full_name.split(':')

            if len(parts) > 1:
                namespace = ':'.join(parts[:-1])
                name = parts[-1]
            else:
                namespace = None
                name = full_name

            data['shapes'].append({
                'name': name,
                'namespace': namespace,
                'color': tuple(obj.attr(self.mesh_attr_name).get())
            })

        return data

    def yaml(self):
        '''Serialize MatteAOV'''

        return yaml.safe_dump(self.data())

    @classmethod
    def load(cls, data, ignore_namespaces=False):
        '''Deserialize a MatteAOV from a yaml string or a data dict'''

        if isinstance(data, basestring):
            data = yaml.load(data)

        matte_name = 'aiAOV_' + data['name']
        if not pmc.objExists(matte_name):
            aov = cls.create(data['name'])
        else:
            pyaov = pmc.PyNode(matte_name)
            pyuserdata = pmc.PyNode(data['name'] + '_color')
            aov = cls(pyaov, pyuserdata)

        for shape in data['shapes']:
            if ignore_namespaces or not shape['namespace']:
                name = shape['name']
                matches = pmc.ls(name, r=True)
            else:
                name = shape['namespace'] + ':' + shape['name']
                matches = pmc.ls(name)
            aov.set_objects_color(shape['color'], *matches)

        return aov
