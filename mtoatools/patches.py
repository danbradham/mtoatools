from maya import cmds, mel


def fix_aov_alias_attrs():
    '''Fixes the alias attribute aov name errors. Rebuilds the
    attributeAliasList attribute on all shadingEngine nodes.
    '''

    print 'Rebuilding AOV Alias Attributes...\n'
    for sg in cmds.ls(type='shadingEngine'):
        print '....', sg
        num_aovs = cmds.getAttr(sg + '.aovs', size=True)
        if not cmds.objExists(sg + '.aal'):
            cmds.addAttr(sg, sn='aal', ln='attributeAliasList', dt='attributeAlias')
        if cmds.objExists(sg + '.ihi'):
            cmds.setAttr(sg + '.ihi', 0)
        if cmds.objExists(sg + '.ro'):
            cmds.setAttr(sg + '.ro', True)
        alias_list = []
        for i in xrange(num_aovs):
            aov_name = cmds.getAttr('{}.aovs[{}].aov_name'.format(sg, i))
            full_aov_name = 'ai_aov_' + aov_name
            cust_aov_name = 'aiCustomAOVs[{}]'.format(i)
            alias_list.append(full_aov_name)
            alias_list.append(cust_aov_name)
        cmds.setAttr(sg + '.aal', alias_list, type='attributeAlias')

    print '\nDone!'


def fix_render_globals_window():
    '''Rebuilds the render settings window'''

    cmds.setAttr('defaultRenderGlobals.currentRenderer', l=False)
    cmds.setAttr(
        'defaultRenderGlobals.currentRenderer',
        'mayaSoftware',
        type='string'
    )
    if cmds.window('unifiedRenderGlobalsWindow', exists=True):
        cmds.deleteUI('unifiedRenderGlobalsWindow')

    mel.eval('unifiedRenderGlobalsWindow;')
