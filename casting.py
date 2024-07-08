import bpy
from bpy.types import WorkSpaceTool
from .tool import *


is_casting_submit = False            #铸造法是否提交  铸造法中厚度参数只在未提交时有效
is_casting_submitL = False
prev_casting_thickness = 0.2         #记录铸造法厚度,模块切换时保持厚度参数
prev_casting_thicknessL = 0.2



def frontToCasting():
    '''
    根据当前激活物体复制出来一份若存在CastingReset,用于该模块的重置操作与模块切换
    '''
    # 若存在CastingReset,则先将其删除
    # 根据当前激活物体,复制一份生成CastingReset
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "CastingReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
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
    name = bpy.context.scene.leftWindowObj
    cur_solidify_inner_obj = bpy.data.objects.get(name + "CastingSolidifyInner")
    handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    handle_solidify_inner_obj = bpy.data.objects.get(name + "HandleCastingSolidifyInner")
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if (cur_solidify_inner_obj != None):
        bpy.data.objects.remove(cur_solidify_inner_obj, do_unlink=True)
    if (handle_solidify_inner_obj != None):
        bpy.data.objects.remove(handle_solidify_inner_obj, do_unlink=True)
    if (handle_obj != None):
        # bpy.data.objects.remove(handle_obj, do_unlink=True)
        handle_obj.hide_set(True)
    if (label_obj != None):
        # bpy.data.objects.remove(label_obj, do_unlink=True)
        label_obj.hide_set(True)


    compare_obj = bpy.data.objects.get(name + "CastingCompare")
    if (compare_obj != None):
        bpy.data.objects.remove(compare_obj, do_unlink=True)
    compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
    if (compare_last_obj != None):
        bpy.data.objects.remove(compare_last_obj, do_unlink=True)

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
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    if (sprue_compare_obj != None):
        bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)



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

    castingSubmit()
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "CastingLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
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
    global is_casting_submit
    global is_casting_submitL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if (not is_casting_submit):
            # 执行加厚操作
            obj = bpy.data.objects.get(name)
            handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
            thickness = bpy.context.scene.ruanErMoHouDu
            if (obj != None):
                modifier_name = "CastingModifier"
                target_modifier = None
                for modifier in obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    target_modifier.thickness = thickness
            if (handle_obj != None):
                modifier_name = "HandleCastingModifier"
                target_modifier = None
                for modifier in handle_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    target_modifier.thickness = thickness
    elif name == '左耳':
        if (not is_casting_submitL):
            # 执行加厚操作
            obj = bpy.data.objects.get(name)
            handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
            thickness = bpy.context.scene.ruanErMoHouDuL
            if (obj != None):
                modifier_name = "CastingModifier"
                target_modifier = None
                for modifier in obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    target_modifier.thickness = thickness
            if (handle_obj != None):
                modifier_name = "HandleCastingModifier"
                target_modifier = None
                for modifier in handle_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier != None):
                    target_modifier.thickness = thickness







def castingInitial():
    global is_casting_submit
    global is_casting_submitL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        is_casting_submit = False
    elif name == '左耳':
        is_casting_submitL = False


    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    handle_obj = bpy.data.objects.get(name + "HandleReset")
    label_obj = bpy.data.objects.get(name + "LabelReset")
    handle_casting_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    label_casting_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    casting_ininial_obj = None
    if (handle_casting_obj != None):
        if (handle_obj != None):
            casting_ininial_obj = handle_obj
    # elif (label_casting_obj != None):
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







    #若模型已经添加过附件或字体,使用未添加附件或者字体的模型替换当前模型右耳,并将其设置未当前激活物体
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
    #为当前激活物体设置透明材质
    # cur_obj.data.materials.clear()
    # cur_obj.data.materials.append(bpy.data.materials['Transparency'])
    mat = bpy.data.materials.get("Yellow")
    mat.blend_method = 'BLEND'
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
    bpy.context.scene.transparent3Enum = 'OP3'


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










    #若模型添加过附件,为用于铸造法的附件添加透明材质,并将其设置为当前激活物体   (若添加过附件)
    name = bpy.context.scene.leftWindowObj
    handle_for_casting_name = name + "软耳膜附件Casting"
    handle_for_casting_obj = bpy.data.objects.get(handle_for_casting_name)
    if(handle_for_casting_obj != None):
        cur_obj.select_set(False)
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


        #将当前激活物体重新设置为右耳/左耳
        handle_for_casting_obj.select_set(False)
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj








    #若模型添加过字体
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if(label_obj != None):
        label_obj.hide_set(False)








def castingSubmit():
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
        # cur_solidify_inner_obj = bpy.data.objects.get(name + "CastingSolidifyInner")
        handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
        # handle_solidify_inner_obj = bpy.data.objects.get(name + "HandleCastingSolidifyInner")
        label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
        compare_obj = bpy.data.objects.get(name + "CastingCompare")
        #右耳模型铸造法的提交
        # if (compare_obj != None and cur_obj != None and cur_solidify_inner_obj != None):
        if (compare_obj != None and cur_obj != None):
            #将对比物材质由红色改为黄色
            cur_obj.select_set(False)
            compare_obj.select_set(True)
            bpy.context.view_layer.objects.active = compare_obj
            yellow_material = bpy.data.materials.new(name="yellowcompare")
            yellow_material.diffuse_color = (1, 0.319, 0.133, 1.0)
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





        #之前的模块若添加过附件
        # if (cur_obj != None and handle_obj != None and handle_solidify_inner_obj != None):
        if (cur_obj != None and handle_obj != None):
            # 将附件的实体化修改器提交
            cur_obj.select_set(False)
            handle_obj.select_set(True)
            bpy.context.view_layer.objects.active = handle_obj
            #复制保存一份软耳膜附件Casting并去除其中的实体化修改器,在附件铸造法提交之后将其作为新的软耳膜附件Casting替代
            duplicate_obj1 = handle_obj.copy()
            duplicate_obj1.data = handle_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = name + "软耳膜附件CastingReplace"
            bpy.context.scene.collection.objects.link(duplicate_obj1)
            if (name == "右耳"):
                moveToRight(duplicate_obj1)
            elif (name == "左耳"):
                moveToLeft(duplicate_obj1)
            #取消替代软耳膜附件Casting的物体中的实体化修改器
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
            RightEarAndHandleUnionForCasting = cur_obj.modifiers.new(name="RightEarAndHandleUnionForCasting", type='BOOLEAN')
            RightEarAndHandleUnionForCasting.object = handle_obj
            RightEarAndHandleUnionForCasting.operation = 'UNION'
            RightEarAndHandleUnionForCasting.solver = 'EXACT'
            bpy.ops.object.modifier_apply(modifier="RightEarAndHandleUnionForCasting", single_user=True)
            # handle_obj.hide_set(True)
            bpy.data.objects.remove(handle_obj, do_unlink=True)
            handle_replace_obj = bpy.data.objects.get(name + "软耳膜附件CastingReplace")
            handle_replace_obj.name = name + "软耳膜附件Casting"
            # bpy.data.objects.remove(handle_replace_obj, do_unlink=True)
            handle_replace_obj.hide_set(True)

            #布尔合并后连接区域可能无颜色,因此需要重新着色
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
            bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
            bpy.ops.paint.vertex_color_set()
            bpy.ops.object.mode_set(mode='OBJECT')


        #之前的模块若添加过外凸的字体
        if(label_obj != None):
            label_obj.hide_set(False)
            label_obj.select_set(False)
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            RightEarAndHandleUnionForCasting = cur_obj.modifiers.new(name="RightEarAndLabelUnionForCasting",type='BOOLEAN')
            RightEarAndHandleUnionForCasting.object = label_obj
            RightEarAndHandleUnionForCasting.operation = 'UNION'
            RightEarAndHandleUnionForCasting.solver = 'EXACT'
            bpy.ops.object.modifier_apply(modifier="RightEarAndLabelUnionForCasting", single_user=True)
            # bpy.data.objects.remove(label_obj, do_unlink=True)
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

