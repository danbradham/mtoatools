from maya import cmds
import pymel.core as pmc


SHADING_CLASSIFICATIONS = {
    'texture': {'asTexture': True},
    'shader': {'asShader': True},
    'light': {'asLight': True},
    'utility': {'asUtility': True},
    'rendering': {'asRendering': True},
    'postprocess': {'asPostProcess': True},
}


def add_bool_attr(node, name, value=None):

    node.addAttr(name, at='bool', dv=value or True, k=True)


def add_float_attr(node, name, value=None):

    node.addAttr(name, at='float', dv=value or 0, k=True)


def add_color_attr(node, name, value=None):

    node.addAttr(name, at='float3', uac=True)
    for c in 'RGB':
        node.addAttr(name + c, at='float', p=name)
    node.attr(name).set(e=True, k=True)
    for c in 'RGB':
        node.attr(name + c).set(e=True, k=True)

    if value:
        node.attr(name).set(*value)


def set_attributes(node, **attributes):
    '''Set a bunch of attributes on a node

    :param attributes: attribute names and values to set
        if the value is a pymel.general.Attribute instance, connect the attr
    '''

    for k, v in attributes.iteritems():
        if isinstance(v, pmc.Attribute):
            v.connect(node.attr(k), force=True)
        else:
            node.attr(k).set(v)


def create_node(type_, name=None, **attributes):

    kwargs = {}
    if name:
        kwargs['name'] = name

    node_name = None

    for shading_class, shading_kwargs in SHADING_CLASSIFICATIONS.iteritems():

        if cmds.getClassification(type_, satisfies=shading_class):
            node_name = cmds.shadingNode(type_, **shading_kwargs)
            if name:
                node_name = cmds.rename(node_name, name)
            if cmds.objectType(node_name, isType='transform'):
                node_name = cmds.listRelatives(node_name, shapes=True)[0]
                node_name = cmds.rename(node_name, name + 'Shape')

    if not node_name:
        node_name = cmds.createNode(type_, **kwargs)

    node = pmc.PyNode(node_name)
    set_attributes(node, **attributes)
    return node


def create_background_sphere(name):
    '''Create a sphere aligned to aiSkyDomeLight shape'''

    xform, _ =  pmc.polySphere(radius=995)
    shape = xform.getShape()
    xform.rename('HDR_Reflector')

    # align sphere to aiSkyDomeLight
    xform.rotateY.set(71.5)
    uv_count = pmc.polyEvaluate(shape, uv=True)
    pmc.polyFlipUV(
        '{}.map[0:{}]'.format(str(shape), uv_count),
        flipType=0,
        local=True
    )
    pmc.delete(xform, ch=True)
    pmc.makeIdentity(xform, apply=True)

    # set defaults
    shape.doubleSided.set(False)
    shape.castsShadows.set(False)
    shape.receiveShadows.set(False)
    shape.opposite.set(True)
    shape.aiSelfShadows.set(0)
    shape.aiOpaque.set(0)
    shape.aiVisibleInDiffuse.set(0)
    shape.aiVisibleInGlossy.set(0)

    return xform, shape


def create_light(type_, name, **defaults):
    '''Create a light and set some default values'''

    xform = pmc.shadingNode(type_, asLight=True)
    xform.rename(name)
    shape = xform.getShape()
    set_attributes(shape, **defaults)

    return xform, shape


def create_material(type_, name, **defaults):
    '''Create and set default values for a shader node'''

    mtl, sg = pmc.createSurfaceShader(type_, name=name)
    set_attributes(mtl, **defaults)
    return mtl, sg


def assign_material(mtl_or_sg, *nodes):
    '''Assign a material to a bunch of nodes

    :param mtl_or_sg: The material or shadingEngine to assign
    :param nodes: The nodes to be assigned to
    '''

    class_ = mtl_or_sg.classification()

    if 'shadingEngine' in class_:
        sg = mtl_or_sg
    elif 'shader/surface' in class_:
        sgs = pmc.listConnections(mtl_or_sg, type='shadingEngine')
        if sgs:
            sg = sgs[0]
        else:
            sg = pmc.sets(
                empty=True,
                renderable=True,
                name=str(mtl_or_sg) + 'SG'
                )
            mtl_or_sg.outColor.connect(sg.surfaceShader)
    else:
        raise TypeError('{} not a shader or shadingEngine'.format(mtl_or_sg))

    for node in nodes:
        pmc.sets(sg, forceElement=node)


def create_hdr_rig():

    # Dome shapes
    skydome_xform, skydome = create_light(
        'aiSkyDomeLight',
        name='HDR_SkyDomeLight')
    bg_xform, bg = create_background_sphere(name='HDR_Background')

    # Materials
    cam_mtl = create_node('surfaceShader', name='hdr_cam_mtl')
    bg_mtl, bg_sg = create_material(
        'aiRaySwitch',
        name='hdr_rayswitch',
        shadow=(0, 0, 0),
        diffuse=(0, 0, 0),
        glossy=(0, 0, 0))

    cam_mtl.outColor.connect(bg_mtl.camera)
    cam_mtl.outColor.connect(bg_sg.surfaceShader, force=True)
    bg_mtl.outColor.connect(bg_sg.aiSurfaceShader)
    assign_material(bg_sg, bg)

    # Shading Nodes
    texture = create_node('file', name='hdr_file')
    rgb2hsv = create_node('rgbToHsv')
    hsv = create_node('plusMinusAverage', name='hdr_hsv')
    hsv2rgb = create_node('hsvToRgb')
    gamma = create_node('gammaCorrect', name='hdr_gamma')
    preview = create_node(
        'ramp',
        name='hdr_preview',
        **{'colorEntryList[0].position': 0})
    bg_condition = create_node(
        'condition',
        name='bg_condition',
        secondTerm=1,
        colorIfFalse=(0, 0, 0))
    refr_condition = create_node(
        'condition',
        name='refr_condition',
        secondTerm=1,
        colorIfFalse=(0, 0, 0))
    refl_condition = create_node(
        'condition',
        name='refl_condition',
        secondTerm=1,
        colorIfFalse=(0, 0, 0))

    texture.outColor.connect(rgb2hsv.inRgb)
    rgb2hsv.outHsv.connect(hsv.input3D[0])
    hsv.output3D.connect(hsv2rgb.inHsv)
    hsv2rgb.outRgb.connect(gamma.value)
    gamma.outValue.connect(preview.colorEntryList[0].color)
    preview.outColor.connect(bg_condition.colorIfTrue)
    preview.outColor.connect(refl_condition.colorIfTrue)
    preview.outColor.connect(refr_condition.colorIfTrue)
    bg_condition.outColor.connect(cam_mtl.outColor)
    refr_condition.outColor.connect(bg_mtl.refraction)
    refl_condition.outColor.connect(bg_mtl.reflection)
    preview.outColor.connect(str(skydome) + '.color')

    # control
    control, _ = pmc.circle(radius=24)
    control.rename('HDR')
    control_shape = control.getShape()
    control_shape.overrideEnabled.set(True)
    control_shape.overrideColor.set(17)
    control.selectionChildHighlighting.set(0)
    pmc.parent([skydome_xform, bg_xform], control)
    pmc.delete(control, ch=True)

    add_bool_attr(control, 'showInViewport', 0)
    add_bool_attr(control, 'background')
    add_float_attr(control, 'backgroundMatteOpacity', 0)
    add_bool_attr(control, 'refractions')
    add_bool_attr(control, 'reflections')
    add_float_attr(control, 'hue')
    add_float_attr(control, 'saturation')
    add_float_attr(control, 'exposure')
    add_color_attr(control, 'gain', (1, 1, 1))
    add_color_attr(control, 'offset')
    add_color_attr(control, 'gamma', (1, 1, 1))

    # Connect everything
    control.showInViewport.connect(bg_xform.lodVisibility)
    control.showInViewport.connect(str(skydome) + '.lodVisibility')
    control.background.connect(bg_condition.firstTerm)
    control.backgroundMatteOpacity.connect(cam_mtl.outMatteOpacityR)
    control.backgroundMatteOpacity.connect(cam_mtl.outMatteOpacityG)
    control.backgroundMatteOpacity.connect(cam_mtl.outMatteOpacityB)
    control.reflections.connect(refl_condition.firstTerm)
    control.refractions.connect(refr_condition.firstTerm)
    control.hue.connect(hsv.input3D[1].input3Dx)
    control.saturation.connect(hsv.input3D[1].input3Dy)
    control.gain.connect(texture.colorGain)
    control.offset.connect(texture.colorOffset)
    control.exposure.connect(texture.exposure)
    control.gamma.connect(gamma.gamma)

    pmc.select(texture)
