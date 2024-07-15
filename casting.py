import bpy
from bpy.types import WorkSpaceTool
from .tool import *


is_casting_submit = False            #铸造法是否提交  铸造法中厚度参数只在未提交时有效
is_casting_submitL = False
prev_casting_thickness = 0.2         #记录铸造法厚度,模块切换时保持厚度参数
prev_casting_thicknessL = 0.2


def newColor(id, r, g, b, is_transparency, transparency_degree):
    mat = newMaterial(id)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.inputs[0].default_value = (r, g, b, 1)
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


def frontToCasting():
    '''
    根据当前激活物体复制出来一份若存在CastingReset,用于该模块的重置操作与模块切换
    '''
    # 若存在CastingReset,则先将其删除
    # 根据当前激活物体,复制一份生成CastingReset
    name = bpy.context.scene.leftWindowObj
    casting_reset_obj = bpy.data.objects.get(name + "CastingReset")
    if(casting_reset_obj != None):
        bpy.data.objects.remove(casting_reset_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "CastingReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)


    castingInitial()  # 初始化
    global prev_casting_thickness
    global prev_casting_thicknessL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        bpy.context.scene.ruanErMoHouDu = prev_casting_thickness
    elif name == '左耳':
        bpy.context.scene.ruanErMoHouDuL = prev_casting_thicknessL

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 设置旋转中心,将当前激活物体重新设置为右耳/左耳
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def frontFromCasting():
    #CastingCompare是铸造法的内层物体,右耳CastingCompareLast则用于后续的软耳膜支撑,排气孔添加之后,切换回铸造法后的重置
    # 根据CastingReset,复制出一份物体替代当前操作物体
    # 删除CastingReset与CastingLast
    #删除CastingCompare和右耳CastingCompareLast
    # 记录加厚参数
    global prev_casting_thickness
    global prev_casting_thicknessL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        prev_casting_thickness = bpy.context.scene.ruanErMoHouDu
    elif name == '左耳':
        prev_casting_thicknessL = bpy.context.scene.ruanErMoHouDuL



    #将铸造法初始化过程中复制的物体删除,将显示的物体重新设置为隐藏
    for obj in bpy.data.objects:
        patternR = r'右耳软耳膜附件Casting'
        patternL = r'左耳软耳膜附件Casting'
        if re.match(patternR, obj.name) or re.match(patternL, obj.name):
            handle_obj = obj
            handle_obj.hide_set(True)
    for obj in bpy.data.objects:
        patternR = r'右耳LabelPlaneForCasting'
        patternL = r'左耳LabelPlaneForCasting'
        if re.match(patternR, obj.name) or re.match(patternL, obj.name):
            label_obj = obj
            label_obj.hide_set(True)


    compare_obj = bpy.data.objects.get(name + "CastingCompare")
    if (compare_obj != None):
        bpy.data.objects.remove(compare_obj, do_unlink=True)
    compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
    if (compare_last_obj != None):
        bpy.data.objects.remove(compare_last_obj, do_unlink=True)

    obj = bpy.data.objects[name]
    resetname = name + "CastingReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if (name == "右耳"):
        moveToRight(duplicate_obj)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "CastingReset" or selected_obj.name == name + "CastingLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def backToCasting():
    # 将后续模块中的reset和last都删除
    name = bpy.context.scene.leftWindowObj
    support_reset = bpy.data.objects.get(name + "SupportReset")
    support_last = bpy.data.objects.get(name + "SupportLast")
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
    if (support_reset != None):
        bpy.data.objects.remove(support_reset, do_unlink=True)
    if (support_last != None):
        bpy.data.objects.remove(support_last, do_unlink=True)
    if (sprue_reset != None):
        bpy.data.objects.remove(sprue_reset, do_unlink=True)
    if (sprue_last != None):
        bpy.data.objects.remove(sprue_last, do_unlink=True)

    # 删除支撑和排气孔中可能存在的对比物体
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (soft_support_compare_obj != None):
        bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    if (hard_support_compare_obj != None):
        bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)


    # 判断是否存在CastingReset
    # 若没有CastingReset,则说明跳过了Casting模块,再直接由后面的模块返回该模块。
    # 若存在CastingReset,则直接将CastingReset复制一份用于替换当前操作物体
    global prev_casting_thickness
    global prev_casting_thicknessL
    exist_CastingReset = False
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "CastingReset"):
            exist_CastingReset = True
    if (exist_CastingReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "CastingReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        castingInitial()      #初始化
        if name == '右耳':
            bpy.context.scene.ruanErMoHouDu = prev_casting_thickness
        elif name == '左耳':
            bpy.context.scene.ruanErMoHouDuL = prev_casting_thicknessL


    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "LabelLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "HandleLast") != None):
            lastname = name + "HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "VentCanalLast") != None):
            lastname = name + "VentCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "SoundCanalLast") != None):
            lastname = name + "SoundCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "MouldLast") != None):
            lastname = name + "MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "QieGeLast") != None):
            lastname = name + "QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "LocalThickLast") != None):
            lastname = name + "LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = name + "DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        castingInitial()      #初始化
        if name == '右耳':
            bpy.context.scene.ruanErMoHouDu = prev_casting_thickness
        elif name == '左耳':
            bpy.context.scene.ruanErMoHouDuL = prev_casting_thicknessL

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 设置旋转中心,将当前激活物体重新设置为右耳/左耳
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj = bpy.data.objects.get(name)
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def backFromCasting():
    # 将铸造法提交
    # 将提交之后的模型保存CastingLast,用于模块切换,若存在CastingLast,则先将其删除
    #记录加厚参数
    global prev_casting_thickness
    global prev_casting_thicknessL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        prev_casting_thickness = bpy.context.scene.ruanErMoHouDu
    elif name == '左耳':
        prev_casting_thicknessL = bpy.context.scene.ruanErMoHouDuL

    #将铸造法提交
    castingSubmit()

    #根据当前物体复制一份用于生成CastingLast
    name = bpy.context.scene.leftWindowObj
    casting_last_obj = bpy.data.objects.get(name + "CastingLast" )
    if(casting_last_obj != None):
        bpy.data.objects.remove(casting_last_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "CastingLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj




def castingThicknessUpdate(thickness):
    '''
    根据面板参数调整模型铸造法外壳的厚度和附件外壳的厚度
    '''
    global is_casting_submit
    global is_casting_submitL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if (not is_casting_submit):
            #模型实体化厚度更新
            obj = bpy.data.objects.get(name)
            if (obj != None):
                modifier_name = "CastingModifier"
                target_modifier = None
                for modifier in obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    target_modifier.thickness = thickness
            #附件实体化厚度更新
            for obj in bpy.data.objects:
                patternR = r'右耳软耳膜附件Casting'
                patternL = r'左耳软耳膜附件Casting'
                if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                    handle_for_casting_obj = obj
                    # 调整附件实体化厚度
                    modifier_name = "HandleCastingModifier"
                    target_modifier = None
                    for modifier in handle_for_casting_obj.modifiers:
                        if modifier.name == modifier_name:
                            target_modifier = modifier
                    if (target_modifier != None):
                        target_modifier.thickness = thickness

    elif name == '左耳':
        if (not is_casting_submitL):
            # 模型实体化厚度更新
            obj = bpy.data.objects.get(name)
            if (obj != None):
                modifier_name = "CastingModifier"
                target_modifier = None
                for modifier in obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    target_modifier.thickness = thickness
            # 附件实体化厚度更新
            for obj in bpy.data.objects:
                patternR = r'右耳软耳膜附件Casting'
                patternL = r'左耳软耳膜附件Casting'
                if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                    handle_for_casting_obj = obj
                    # 调整附件实体化厚度
                    modifier_name = "HandleCastingModifier"
                    target_modifier = None
                    for modifier in handle_for_casting_obj.modifiers:
                        if modifier.name == modifier_name:
                            target_modifier = modifier
                    if (target_modifier != None):
                        target_modifier.thickness = thickness







def castingInitial():
    '''
    铸造法初始化
    首先替换铸造法外壳,以未添加过传声孔,通气孔,附件,字体的模型为基础进行实体化,防止实体化过程中顶点挤到一起形成褶皱
    对外壳添加实体化修改器根据厚度进行加厚
    对多个附件铸造法外壳添加实体化修改器根据厚度进行加厚
    将多个隐藏的字体外壳显示出来
    '''
    global is_casting_submit
    global is_casting_submitL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        is_casting_submit = False
    elif name == '左耳':
        is_casting_submitL = False

    #若之前的操作添加过传声孔,通气孔,附件,字体,则使用未添加过这些的模型替换生成铸造法外壳,防止实体化的时候顶点挤压到一起形成褶皱
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    sound_canal_obj = bpy.data.objects.get(name + "SoundCanalReset")
    vent_canal_obj = bpy.data.objects.get(name + "VentCanalReset")
    handle_obj = bpy.data.objects.get(name + "HandleReset")
    label_obj = bpy.data.objects.get(name + "LabelReset")
    casting_ininial_obj = None
    if(sound_canal_obj != None):
        casting_ininial_obj = sound_canal_obj
    elif(vent_canal_obj != None):
        casting_ininial_obj = vent_canal_obj
    elif (handle_obj != None):
        casting_ininial_obj = handle_obj
    elif (label_obj != None):
        casting_ininial_obj = label_obj



    #复制出一份模型作为对比,将复制的物体加入到场景集合中(附带附件和字体的模型)
    compare_obj = bpy.data.objects.get(name + "CastingCompare")                   #铸造法内部有附件和字体的红色对比模型
    if (compare_obj != None):
        bpy.data.objects.remove(compare_obj, do_unlink=True)
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.name = name + "CastingCompare"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if (name == "右耳"):
        moveToRight(duplicate_obj)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj)
    #将当前激活物体设置未对比物,并为对比物体添加红色材质
    cur_obj.select_set(False)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    duplicate_obj.data.materials.clear()
    duplicate_obj.data.materials.append(red_material)



    #若模型已经添加过传声孔,通气孔,附件或字体,使用未添加传声孔,通气孔,附件或者字体的模型替换当前模型右耳,并将其设置未当前激活物体
    if(casting_ininial_obj != None):
        name = bpy.context.scene.leftWindowObj
        bpy.data.objects.remove(cur_obj, do_unlink=True)
        cur_obj = casting_ininial_obj.copy()
        cur_obj.data = casting_ininial_obj.data.copy()
        cur_obj.name = name
        cur_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(cur_obj)
        if (name == "右耳"):
            moveToRight(cur_obj)
        elif (name == "左耳"):
            moveToLeft(cur_obj)
        duplicate_obj.select_set(False)
        cur_obj.hide_set(False)

    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj
    if bpy.context.scene.leftWindowObj == '右耳':
        mat = bpy.data.materials.get("YellowR")
        mat.blend_method = 'BLEND'
        bpy.context.scene.transparent3EnumR = 'OP3'
    elif bpy.context.scene.leftWindowObj == '左耳':
        mat = bpy.data.materials.get("YellowL")
        mat.blend_method = 'BLEND'
        bpy.context.scene.transparent3EnumL = 'OP3'

    # 为操作物体添加实体化修改器,通过参数实现铸造厚度
    modifier_name = "CastingModifier"
    target_modifier = None
    for modifier in cur_obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        soft_eardrum_casting_modifier = bpy.context.object.modifiers["Solidify"]
        soft_eardrum_casting_modifier.name = "CastingModifier"
    bpy.context.object.modifiers["CastingModifier"].solidify_mode = 'EXTRUDE'
    bpy.context.object.modifiers["CastingModifier"].offset = 1
    bpy.context.object.modifiers["CastingModifier"].thickness = 0.5
    bpy.context.object.modifiers["CastingModifier"].use_rim_only = True
    bpy.context.object.modifiers["CastingModifier"].use_rim = True


    #若模型添加过附件,为用于铸造法的附件添加透明材质   (若添加过附件)
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        patternR = r'右耳软耳膜附件Casting'
        patternL = r'左耳软耳膜附件Casting'
        if re.match(patternR, obj.name) or re.match(patternL, obj.name):
            handle_for_casting_obj = obj
            bpy.ops.object.select_all(action='DESELECT')
            handle_for_casting_obj.hide_set(False)
            handle_for_casting_obj.select_set(True)
            bpy.context.view_layer.objects.active = handle_for_casting_obj

            # 为操作物体添加实体化修改器,通过参数实现铸造厚度
            modifier_name = "HandleCastingModifier"
            target_modifier = None
            for modifier in handle_for_casting_obj.modifiers:
                if modifier.name == modifier_name:
                    target_modifier = modifier
            if (target_modifier == None):
                bpy.ops.object.modifier_add(type='SOLIDIFY')
                soft_eardrum_casting_modifier = bpy.context.object.modifiers["Solidify"]
                soft_eardrum_casting_modifier.name = "HandleCastingModifier"
            bpy.context.object.modifiers["HandleCastingModifier"].solidify_mode = 'EXTRUDE'
            bpy.context.object.modifiers["HandleCastingModifier"].offset = 1
            bpy.context.object.modifiers["HandleCastingModifier"].thickness = 0.5
            bpy.context.object.modifiers["HandleCastingModifier"].use_rim_only = True
            bpy.context.object.modifiers["HandleCastingModifier"].use_rim = True


    # 之前的模块若添加过外凸的字体
    for obj in bpy.data.objects:
        patternR = r'右耳LabelPlaneForCasting'
        patternL = r'左耳LabelPlaneForCasting'
        if re.match(patternR, obj.name) or re.match(patternL, obj.name):
            label_obj = obj
            label_obj.hide_set(False)




def castingSubmit():
    '''
    将模型外壳,附件外壳的实体化修改器提交
    将实体化后的附件外壳和字体外壳与模型作布尔合并
    '''
    global is_casting_submit
    global is_casting_submitL
    is_casting_submit_cur = False
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        is_casting_submit_cur = is_casting_submit
        if (not is_casting_submit):
            is_casting_submit = True
    elif name == '左耳':
        is_casting_submit_cur = is_casting_submitL
        if (not is_casting_submitL):
            is_casting_submitL = True
    if(not is_casting_submit_cur):
        name = bpy.context.scene.leftWindowObj
        cur_obj = bpy.data.objects.get(name)
        compare_obj = bpy.data.objects.get(name + "CastingCompare")
        #右耳模型铸造法的提交
        if (compare_obj != None and cur_obj != None):
            #将对比物材质由红色改为黄色
            cur_obj.select_set(False)
            compare_obj.select_set(True)
            bpy.context.view_layer.objects.active = compare_obj
            yellow_material = newColor("yellowcompare", 1, 0.319, 0.133, 0, 1)  # 创建材质
            compare_obj.data.materials.clear()
            compare_obj.data.materials.append(yellow_material)

            #将CastingCompare复制一份CastingCompareLast,可能用于之后的软耳膜支撑,排气孔中内层CastingCompare的还原
            compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
            if (compare_last_obj != None):
                bpy.data.objects.remove(compare_last_obj, do_unlink=True)
            duplicate_obj1 = compare_obj.copy()
            duplicate_obj1.data = compare_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = name + "CastingCompareLast"
            bpy.context.collection.objects.link(duplicate_obj1)
            if (name == "右耳"):
                moveToRight(duplicate_obj1)
            elif (name == "左耳"):
                moveToLeft(duplicate_obj1)
            duplicate_obj1.hide_set(True)

            #将右耳的实体化修改器提交
            compare_obj.select_set(False)
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            modifier_name = "CastingModifier"
            target_modifier = None
            for modifier in cur_obj.modifiers:
                if modifier.name == modifier_name:
                    target_modifier = modifier
            if (target_modifier != None):
                bpy.ops.object.modifier_apply(modifier="CastingModifier",single_user=True)
            # 使用平滑修改器平滑铸造法外壳
            # if(thickness > 0.8):
            #     iterations = 5
            #     if(thickness > 2):
            #         iterations = 30
            #     cur_obj.modifiers.new(name="CastingSmoothModifier", type='SMOOTH')
            #     bpy.context.object.modifiers["CastingSmoothModifier"].factor = 0.5
            #     bpy.context.object.modifiers["CastingSmoothModifier"].iterations = iterations
            #     bpy.ops.object.modifier_apply(modifier="CastingSmoothModifier", single_user=True)





        #若之前的模块若添加过附件
        for obj in bpy.data.objects:
            patternR = r'右耳软耳膜附件Casting'
            patternL = r'左耳软耳膜附件Casting'
            if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                handle_obj = obj
                bpy.ops.object.select_all(action='DESELECT')
                handle_obj.select_set(True)
                bpy.context.view_layer.objects.active = handle_obj
                #复制保存一份软耳膜附件Casting并去除其中的实体化修改器,在附件铸造法提交之后将其作为新的软耳膜附件Casting替代
                # (软耳膜附件Casting只在附件模块中的handleSubmit中生成,后续仍需要其进行重置等操作)
                duplicate_obj1 = handle_obj.copy()
                duplicate_obj1.data = handle_obj.data.copy()
                duplicate_obj1.animation_data_clear()
                duplicate_obj1.name = name + "软耳膜附件CastingReplace"
                bpy.context.scene.collection.objects.link(duplicate_obj1)
                if (name == "右耳"):
                    moveToRight(duplicate_obj1)
                elif (name == "左耳"):
                    moveToLeft(duplicate_obj1)
                handle_obj.select_set(False)
                duplicate_obj1.select_set(True)
                bpy.context.view_layer.objects.active = duplicate_obj1
                modifier_name = "HandleCastingModifier"
                target_modifier = None
                for modifier in duplicate_obj1.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    bpy.ops.object.modifier_remove(modifier="HandleCastingModifier")
                duplicate_obj1.select_set(False)
                duplicate_obj1.hide_set(True)
                #将软耳膜附件Casting中的实体化修改器提交
                handle_obj.select_set(True)
                bpy.context.view_layer.objects.active = handle_obj
                modifier_name = "HandleCastingModifier"
                target_modifier = None
                for modifier in handle_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    bpy.ops.object.modifier_apply(modifier="HandleCastingModifier", single_user=True)


                #将铸造法之后的右耳和附件合并并删除附件
                handle_obj.select_set(False)
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                EarAndHandleUnionForCasting = cur_obj.modifiers.new(name="EarAndHandleUnionForCasting", type='BOOLEAN')
                EarAndHandleUnionForCasting.object = handle_obj
                EarAndHandleUnionForCasting.operation = 'UNION'
                EarAndHandleUnionForCasting.solver = 'EXACT'
                bpy.ops.object.modifier_apply(modifier="EarAndHandleUnionForCasting", single_user=True)
                bpy.data.objects.remove(handle_obj, do_unlink=True)


                #布尔合并后连接区域可能无颜色,因此需要重新着色
                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
                bpy.ops.paint.vertex_color_set()
                bpy.ops.object.mode_set(mode='OBJECT')

        #将上述生成的软耳膜附件CastingReplace更名为软耳膜附件Casting
        for obj in bpy.data.objects:
            patternR = r'右耳软耳膜附件CastingReplace'
            patternL = r'左耳软耳膜附件CastingReplace'
            if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                handle_replace_obj = obj
                handle_replace_obj.name = name + "软耳膜附件Casting"
                handle_replace_obj.hide_set(True)



        #之前的模块若添加过外凸的字体
        for obj in bpy.data.objects:
            patternR = r'右耳LabelPlaneForCasting'
            patternL = r'左耳LabelPlaneForCasting'
            if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                label_obj = obj
                label_obj.hide_set(False)
                bpy.ops.object.select_all(action='DESELECT')
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                EarAndHandleUnionForCasting = cur_obj.modifiers.new(name="EarAndLabelUnionForCasting",type='BOOLEAN')
                EarAndHandleUnionForCasting.object = label_obj
                EarAndHandleUnionForCasting.operation = 'UNION'
                EarAndHandleUnionForCasting.solver = 'EXACT'
                bpy.ops.object.modifier_apply(modifier="EarAndLabelUnionForCasting", single_user=True)
                label_obj.hide_set(True)

                # 布尔合并后连接区域可能无颜色,因此需要重新着色
                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
                bpy.ops.paint.vertex_color_set()
                bpy.ops.object.mode_set(mode='OBJECT')





class CastingReset(bpy.types.Operator):
    bl_idname = "object.castingreset"
    bl_label = "铸造法重置"

    def invoke(self, context, event):

        bpy.context.scene.var = 100
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        #将铸造法厚度重置为默认值,若铸造法已经提交,则重新初始化
        global prev_casting_thickness
        global prev_casting_thicknessL
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            prev_casting_thickness = 0.2
            bpy.context.scene.ruanErMoHouDu = 0.2
        elif name == '左耳':
            prev_casting_thicknessL = 0.2
            bpy.context.scene.ruanErMoHouDuL = 0.2

        frontFromCasting()
        frontToCasting()
        return {'FINISHED'}




class CastingSubmit(bpy.types.Operator):
    bl_idname = "object.castingsubmit"
    bl_label = "铸造法提交"

    def invoke(self, context, event):
        bpy.context.scene.var == 101
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        print("铸造法提交")
        castingSubmit()
        return {'FINISHED'}









class MyTool_Casting1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_reset"
    bl_label = "铸造法重置"
    bl_description = (
        "重置模型,清除模型上的所有标签"
    )
    bl_icon = "ops.gpencil.sculpt_randomize"
    bl_widget = None
    bl_keymap = (
        ("object.castingreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Casting2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_submit"
    bl_label = "铸造法提交"
    bl_description = (
        "提交铸造法中所作的操作"
    )
    bl_icon = "ops.gpencil.sculpt_smear"
    bl_widget = None
    bl_keymap = (
        ("object.castingsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Casting3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_mirror"
    bl_label = "铸造法镜像"
    bl_description = (
        "将该模型上的铸造法操作镜像到另一个模型上"
    )
    bl_icon = "ops.gpencil.sculpt_smooth"
    bl_widget = None
    def draw_settings(context, layout, tool):
        pass

    # 注册类
_classes = [
    CastingReset,
    CastingSubmit
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Casting1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Casting2, separator=True, group=False, after={MyTool_Casting1.bl_idname})
    bpy.utils.register_tool(MyTool_Casting3, separator=True, group=False, after={MyTool_Casting2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Casting1)
    bpy.utils.unregister_tool(MyTool_Casting2)
    bpy.utils.unregister_tool(MyTool_Casting3)

