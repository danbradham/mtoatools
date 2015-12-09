import pymel.core as pmc


def add_vector_attr(node, name):

    node.addAttr(name, at='float3', uac=True)
    for c in 'RGB':
        node.addAttr(name + c, at='float', p=name)
    node.attr(name).set(e=True, k=True)
    for c in 'RGB':
        node.attr(name + c).set(e=True, k=True)


def get_next_name(name):
    i = 0
    while True:

        if not pmc.objExists('aiAOV_' + name):
            return name

        try:
            int(name[-1])
            name = name[:-1] + str(i + 1)
        except ValueError:
            name = name + str(i + 1)
        i += 1
