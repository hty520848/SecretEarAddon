import bpy
import bmesh
import re
import time

from ..utils.utils import utils_re_color
from ..tool import moveToRight, moveToLeft, newColor, is_on_object, \
    extrude_border_by_vertex_groups, apply_material, recover_to_dig
from .soft_eardrum.thickness_and_fill import soft_fill, reset_to_after_cut, reset_circle_info
from .hard_eardrum.hard_eardrum_cut import init_hard_cut, hard_recover_before_cut_and_remind_border, re_hard_cut
from .hard_eardrum.hard_eardrum_bottom_fill import hard_bottom_fill, recover_before_fill
from .shell_eardrum.shell_eardrum_bottom_fill import shell_bottom_fill, init_shell, submitCircleCutPlane, resetCircleCutPlane, \
    generate_circle_for_cut, generate_border_curve, reset_after_bottom_curve_change, generateShell
from .shell_eardrum.shell_canal import submit_shellcanal, submit_receiver, reset_shellcanal, saveInfoAndDeleteShellCanal
from .parameters_for_create_mould import get_hard_eardrum_border, get_left_hard_eardrum_border, \
    get_right_hard_eardrum_border_template, get_left_hard_eardrum_border_template
from .parameters_for_create_mould import set_hard_eardrum_border, set_left_hard_eardrum_border, \
    set_right_hard_eardrum_border_template, set_left_hard_eardrum_border_template
from .parameters_for_create_mould import get_soft_eardrum_border, get_left_soft_eardrum_border, \
    get_right_soft_eardrum_border_template, get_left_soft_eardrum_border_template
from .parameters_for_create_mould import set_soft_eardrum_border, set_left_soft_eardrum_border, \
    set_right_soft_eardrum_border_template, set_left_soft_eardrum_border_template
from .parameters_for_create_mould import get_frame_style_eardrum_border, get_left_frame_style_eardrum_border, \
    get_right_frame_style_eardrum_border_template, get_left_frame_style_eardrum_border_template
from .parameters_for_create_mould import set_frame_style_eardrum_border, set_left_frame_style_eardrum_border, \
    set_right_frame_style_eardrum_border_template, set_left_frame_style_eardrum_border_template
from .parameters_for_create_mould import set_right_frame_style_hole_border, set_left_frame_style_hole_border
from .parameters_for_create_mould import get_right_shell_border, get_left_shell_border
from .parameters_for_create_mould import set_right_shell_border, set_left_shell_border, set_right_shell_plane_border,\
    set_left_shell_plane_border
from .frame_style_eardrum.frame_style_eardrum_dig_hole import dig_hole, frame_fill
from .frame_style_eardrum.frame_fill_inner_face import fill_closest_point
from ..parameter import get_switch_time, get_switch_flag
from .collision import generate_cubes


# 用于控制创建模具的初始化、切割和补面的逻辑
is_init_finish = True
is_init_finishL = True
is_cut_finish = True
is_cut_finishL = True
is_fill_finish = True
is_fill_finishL = True

last_operate_type = None

def initialTransparency():
    mat = newColor("Transparency", 1, 0.319, 0.133, 1, 0.1)  # 创建材质
    mat.use_backface_culling = False


def set_is_cut_finish(val):
    global is_cut_finish
    global is_cut_finishL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_cut_finish = val
    elif (name == "左耳"):
        is_cut_finishL = val


def set_is_fill_finish(val):
    global is_fill_finish
    global is_fill_finishL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_fill_finish = val
    elif (name == "左耳"):
        is_fill_finishL = val


def set_type(val):
    global last_operate_type
    last_operate_type = val


def get_type():
    global last_operate_type
    return last_operate_type


def frontToCreateMould():
    # 创建MouldReset,用于模型重置  与 模块向前返回时的恢复(若存在MouldReset则先删除)
    # 模型初始化,完成挖孔和切割操作
    all_objs = bpy.data.objects
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name+"MouldReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "MouldReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    if name == '右耳':
        moveToRight(duplicate_obj1)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)
    # duplicate_obj1.hide_set(True)
    newColor('blue', 0, 0, 1, 1, 1)
    initialTransparency()
    duplicate_obj1.data.materials.clear()
    duplicate_obj1.data.materials.append(bpy.data.materials['Transparency'])
    bpy.data.objects[name+"MouldReset"].select_set(False)
    bpy.context.view_layer.objects.active = obj
    if name == '右耳':
        moveToRight(duplicate_obj1)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)
    apply_material()

    enum = bpy.context.scene.muJuTypeEnum
    global last_operate_type
    last_operate_type = enum
    create_mould_cut()

    # global is_init_finish
    # global is_init_finishL
    # if (name == "右耳"):
    #     is_init_finish = False
    # elif (name == "左耳"):
    #     is_init_finishL = False
    # global is_cut_finish
    # global is_cut_finishL
    # if (name == "右耳"):
    #     is_cut_finish = False
    # elif (name == "左耳"):
    #     is_cut_finishL = False


def frontToCreateMouldInit():
    # 复制一份挖孔前的模型以备用
    if bpy.data.objects.get(bpy.context.scene.leftWindowObj + "OriginForCreateMouldR") is not None:
        return
    cur_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    name = cur_obj.name
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    # generate_cubes()


def frontFromCreateMould():
    # 根据MouldReset复制出来一份物体以替换当前激活物体,完成模型的还原
    # 将MouldReset和MouldLast删除
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    resetname = name + "MouldReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    utils_re_color(name, (1, 0.319, 0.133))   # 重新上色

    # 切出创建模具时 需要被删除的物体的名称数组
    enum = bpy.context.scene.muJuTypeEnum
    if enum == 'OP4':
        # need_to_delete_model_name_list = [name + "OriginForFill", name + "OriginForDigHole"]
        need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                          "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                          name + "OuterRetopo", name + "InnerRetopo", name + "Circle", name + "Torus",
                                          name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                          name + "OuterSmooth", name + "InnerSmooth"]
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)
        delete_hole_border()  # 删除框架式耳模中的挖孔边界
    elif enum == 'OP3':
        submitCircleCutPlane()
        saveInfoAndDeleteShellCanal()
        public_object_list = [name + "meshBottomRingBorderR", name + "BottomRingBorderR", name + "shellInnerObj",
                              name + "meshPlaneBorderCurve", name + "PlaneBorderCurve"]
        delete_useless_object(public_object_list)
        cubes_obj_list = [name + "cube1", name + "cube2", name + "cube3", name + "move_cube1", name + "move_cube2",
                          name + "move_cube3", name + "littleShellCube1", name + "littleShellCube2",
                          name + "littleShellCube3", name + "receiver", name + "ReceiverPlane",
                          name + "littleShellCube4", name + "littleShellCylinder1", name + "littleShellCylinder2"]
        delete_useless_object(cubes_obj_list)
    elif enum == 'OP2':
        need_to_delete_model_name_list = [name + "HardEarDrumForSmooth", name + 'ForBottomFillReset']
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)

    elif enum == "OP1":
        need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                          "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                          name + "OuterRetopo", name + "InnerRetopo", name + "Circle", name + "Torus",
                                          name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                          name + "OuterSmooth", name + "InnerSmooth"]
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if name == '右耳':
        bpy.context.scene.createmouldinitR = False
    elif name == '左耳':
        bpy.context.scene.createmouldinitL = False


def backToCreateMould():
    # global is_init_finish
    # global is_init_finishL
    global is_cut_finish
    global is_cut_finishL

    # 若添加铸造法之后切换到支撑或者排气孔模块,再由支撑或排气孔模块跳过铸造法模块直接切换回前面的模块,则需要对物体进行特殊的处理
    name = bpy.context.scene.leftWindowObj
    casting_name = name + "CastingCompare"
    casting_compare_obj = bpy.data.objects.get(casting_name)
    if (casting_compare_obj != None):
        cur_obj = bpy.data.objects.get(name)
        casting_reset_obj = bpy.data.objects.get(name + "CastingReset")
        casting_last_obj = bpy.data.objects.get(name + "CastingLast")
        casting_compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if (cur_obj != None and casting_reset_obj != None and casting_last_obj != None and casting_compare_last_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
            casting_compare_obj.name = name
            bpy.data.objects.remove(casting_reset_obj, do_unlink=True)
            bpy.data.objects.remove(casting_last_obj, do_unlink=True)
            bpy.data.objects.remove(casting_compare_last_obj, do_unlink=True)
    # 后面模块切换到传声孔的时候,判断是否存在用于铸造法的 软耳膜附件Casting  和  用于字体附件的 LabelPlaneForCasting 若存在则将其删除
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    # 将后续模块中的reset和last都删除
    sound_reset = bpy.data.objects.get(name + "SoundCanalReset")
    sound_last = bpy.data.objects.get(name + "SoundCanalLast")
    vent_reset = bpy.data.objects.get(name + "VentCanalReset")
    vent_last = bpy.data.objects.get(name + "VentCanalLast")
    handle_reset = bpy.data.objects.get(name + "HandleReset")
    handle_last = bpy.data.objects.get(name + "HandleLast")
    label_reset = bpy.data.objects.get(name + "LabelReset")
    label_last = bpy.data.objects.get(name + "LabelLast")
    casting_reset = bpy.data.objects.get(name + "CastingReset")
    casting_last = bpy.data.objects.get(name + "CastingLast")
    support_reset = bpy.data.objects.get(name + "SupportReset")
    support_last = bpy.data.objects.get(name + "SupportLast")
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
    if (sound_reset != None):
        bpy.data.objects.remove(sound_reset, do_unlink=True)
    if (sound_last != None):
        bpy.data.objects.remove(sound_last, do_unlink=True)
    if (vent_reset != None):
        bpy.data.objects.remove(vent_reset, do_unlink=True)
    if (vent_last != None):
        bpy.data.objects.remove(vent_last, do_unlink=True)
    if (handle_reset != None):
        bpy.data.objects.remove(handle_reset, do_unlink=True)
    if (handle_last != None):
        bpy.data.objects.remove(handle_last, do_unlink=True)
    if (label_reset != None):
        bpy.data.objects.remove(label_reset, do_unlink=True)
    if (label_last != None):
        bpy.data.objects.remove(label_last, do_unlink=True)
    if (casting_reset != None):
        bpy.data.objects.remove(casting_reset, do_unlink=True)
    if (casting_last != None):
        bpy.data.objects.remove(casting_last, do_unlink=True)
    if (support_reset != None):
        bpy.data.objects.remove(support_reset, do_unlink=True)
    if (support_last != None):
        bpy.data.objects.remove(support_last, do_unlink=True)
    if (sprue_reset != None):
        bpy.data.objects.remove(sprue_reset, do_unlink=True)
    if (sprue_last != None):
        bpy.data.objects.remove(sprue_last, do_unlink=True)
    support_casting_reset = bpy.data.objects.get(name + "CastingCompareSupportReset")
    support_casting_last = bpy.data.objects.get(name + "CastingCompareSupportLast")
    if (support_casting_reset != None):
        bpy.data.objects.remove(support_casting_reset, do_unlink=True)
    if (support_casting_last != None):
        bpy.data.objects.remove(support_casting_last, do_unlink=True)

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


    # 先判断是否存在MouldReset
    # 存在MouldReset时,将MouldReset复制一份用来替换当前激活物体，并执行初始化操作
    # 若不存在MouldReset,则说明直接跳过了 CreateMould  模块。根据上一个模块的最后保存的状态复制出来MouldReset,再根据MouldReset复制一份替换当前激活物体，再初始化，完成模型的恢复
    exist_MouldReset = False
    all_objs = bpy.data.objects
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name+"MouldReset"):
            exist_MouldReset = True
            selected_obj.hide_set(False)
    if (exist_MouldReset):
        obj = bpy.data.objects[name]
        resetname = name + "MouldReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        duplicate_obj.hide_select = False
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        apply_material()

        # if (name == "右耳"):
        #     is_init_finish = False
        # elif (name == "左耳"):
        #     is_init_finishL = False
        # if (name == "右耳"):
        #     is_cut_finish = False
        # elif (name == "左耳"):
        #     is_cut_finishL = False
    else:
        obj = bpy.data.objects[name]
        lastname = name+"QieGeLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "MouldReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name+"LocalThickLast") != None):
            lastname = name+"LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "MouldReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = name+"DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "MouldReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        if name == '右耳':
            moveToRight(ori_obj)
        elif name == '左耳':
            moveToLeft(ori_obj)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        apply_material()

        # if (name == "右耳"):
        #     is_init_finish = False
        # elif (name == "左耳"):
        #     is_init_finishL = False
        # if (name == "右耳"):
        #     is_cut_finish = False
        # elif (name == "左耳"):
        #     is_cut_finishL = False

    enum = bpy.context.scene.muJuTypeEnum
    global last_operate_type
    last_operate_type = enum

    if not bpy.data.materials.get('Transparency'):
        initialTransparency()

    bpy.data.objects[name+"MouldReset"].hide_set(False)
    newColor('blue', 0, 0, 1, 1, 1)
    bpy.data.objects[name+"MouldReset"].data.materials.clear()
    bpy.data.objects[name+"MouldReset"].data.materials.append(bpy.data.materials['Transparency'])
    create_mould_cut()


def backFromCreateMould():
    # 创建MouldLast,用于 模型从后面模块返回时的恢复(若存在MouldLast则先将其删除)
    # 模型提交，将挖孔和切割操作提交

    all_objs = bpy.data.objects
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name+"MouldLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
        elif (selected_obj.name == name+"MouldReset"):
            selected_obj.hide_set(True)
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "MouldLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    if name == '右耳':
        moveToRight(duplicate_obj1)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)

    utils_re_color(name, (1, 0.319, 0.133))  # 重新上色

    # 切出创建模具时 需要被删除的物体的名称数组
    enum = bpy.context.scene.muJuTypeEnum
    if enum == 'OP4':
        # need_to_delete_model_name_list = [name + "OriginForFill", name + "OriginForDigHole"]
        need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                          "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                          name + "OuterRetopo", name + "InnerRetopo", name + "Circle", name + "Torus",
                                          name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                          name + "OuterSmooth", name + "InnerSmooth"]
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)
        delete_hole_border()  # 删除框架式耳模中的挖孔边界
    elif enum == 'OP3':
        submit_shellcanal()
        submitCircleCutPlane()
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR", name + "shellInnerObj",
                              name + "meshPlaneBorderCurve", name + "PlaneBorderCurve"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        cubes_obj_list = [name + "cube1", name + "cube2", name + "cube3", name + "move_cube1", name + "move_cube2",
                          name + "move_cube3", name + "littleShellCube1", name + "littleShellCube2",
                          name + "littleShellCube3", name + "receiver", name + "ReceiverPlane",
                          name + "littleShellCube4", name + "littleShellCylinder1", name + "littleShellCylinder2"]
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)
        delete_useless_object(cubes_obj_list)
    elif enum == 'OP2':
        need_to_delete_model_name_list = [name + "HardEarDrumForSmooth", name + 'ForBottomFillReset']
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)

    elif enum == "OP1":
        need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                          "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                          name + "OuterRetopo", name + "InnerRetopo", name + "Circle", name + "Torus",
                                          name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                          name + "OuterSmooth", name + "InnerSmooth"]
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if name == '右耳':
        bpy.context.scene.createmouldinitR = False
    elif name == '左耳':
        bpy.context.scene.createmouldinitL = False


# def apply_template():
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     success = True
#     # 复制一份挖孔前的模型以备用
#     cur_obj = bpy.context.active_object
#     duplicate_obj = cur_obj.copy()
#     duplicate_obj.data = cur_obj.data.copy()
#     duplicate_obj.animation_data_clear()
#     duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
#     bpy.context.collection.objects.link(duplicate_obj)
#     duplicate_obj.hide_set(True)
#     name = cur_obj.name
#     if name == '右耳':
#         moveToRight(duplicate_obj)
#     elif name == '左耳':
#         moveToLeft(duplicate_obj)
#     mould_type = bpy.context.scene.muJuTypeEnum
#
#     # 根据选择的模板调用对应的模板
#     if mould_type == "OP1":
#         print("软耳模")
#         success = apply_soft_eardrum_template()
#     elif mould_type == "OP2":
#         print("硬耳膜")
#         apply_hard_eardrum_template()
#     elif mould_type == "OP3":
#         print("一体外壳")
#     elif mould_type == "OP4":
#         print("框架式耳膜")
#         apply_frame_style_eardrum_template()
#     elif mould_type == "OP5":
#         print("常规外壳")
#     elif mould_type == "OP6":
#         print("实心面板")
#
#     for obj in bpy.context.view_layer.objects:
#         obj.select_set(False)
#         # 布尔后，需要重新上色
#     if success:
#         utils_re_color(name, (1, 0.319, 0.133))


def delete_useless_object(need_to_delete_model_name_list):
    for selected_obj in bpy.data.objects:
        if (selected_obj.name in need_to_delete_model_name_list):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=False)

def delete_hole_border():
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', obj.name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if re.match(name + 'meshHoleBorderCurve', obj.name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def recover(enum, restart=True):
    '''
    挖孔和底部切割线变化后，先恢复为最初状态，再重新切割
    '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    recover_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == name+"OriginForCreateMouldR":
            recover_flag = True
            break
    # 找到最初创建的  OriginForCreateMould 才能进行恢复
    if recover_flag:
        if enum == 'OP4':
            # need_to_delete_model_name_list = [name + "OriginForFill", name + "OriginForDigHole"]
            need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                              "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                              name + "OuterRetopo", name + "InnerRetopo", name + "Circle",
                                              name + "Torus",
                                              name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                              name + "OuterSmooth", name + "InnerSmooth"]
            public_object_list = [name, name + "meshBottomRingBorderR", name + "BottomRingBorderR"]
            curve_list = [name, name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(public_object_list)
            delete_useless_object(curve_list)
            delete_hole_border()  # 删除框架式耳模中的挖孔边界
            reset_circle_info()
            if name == '右耳':
                # set_frame_style_eardrum_border([])
                set_right_frame_style_eardrum_border_template([])
                set_right_frame_style_hole_border([])
            elif name == '左耳':
                # set_left_frame_style_eardrum_border([])
                set_left_frame_style_eardrum_border_template([])
                set_left_frame_style_hole_border([])

        elif enum == 'OP3':
            reset_shellcanal()
            resetCircleCutPlane()
            public_object_list = [name, name + "meshBottomRingBorderR", name + "BottomRingBorderR",
                                  name + "meshPlaneBorderCurve", name + "PlaneBorderCurve"]
            cubes_obj_list = [name + "cube1", name + "cube2", name + "cube3", name + "move_cube1", name + "move_cube2",
                              name + "move_cube3", name + "littleShellCube1", name + "littleShellCube2",
                              name + "littleShellCube3", name + "receiver", name + "ReceiverPlane",
                              name + "littleShellCube4", name + "littleShellCylinder1", name + "littleShellCylinder2"]
            delete_useless_object(public_object_list)
            delete_useless_object(cubes_obj_list)
            if name == '右耳':
                set_right_shell_border([])
                set_right_shell_plane_border([])
            elif name == '左耳':
                set_left_shell_border([])
                set_left_shell_plane_border([])

        elif enum == 'OP2':
            need_to_delete_model_name_list = [name + "HardEarDrumForSmooth", name + 'ForBottomFillReset']
            public_object_list = [name, name + "meshBottomRingBorderR", name + "BottomRingBorderR"]
            curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(public_object_list)
            delete_useless_object(curve_list)
            if name == '右耳':
                # set_soft_eardrum_border([])
                set_right_soft_eardrum_border_template([])
            elif name == '左耳':
                # set_left_soft_eardrum_border([])
                set_left_soft_eardrum_border_template([])

        elif enum == "OP1":
            need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                              "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                              name + "OuterRetopo", name + "InnerRetopo", name + "Circle",
                                              name + "Torus",
                                              name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                              name + "OuterSmooth", name + "InnerSmooth"]
            public_object_list = [name, name + "meshBottomRingBorderR", name + "BottomRingBorderR"]
            curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(public_object_list)
            delete_useless_object(curve_list)
            reset_circle_info()
            if name == '右耳':
                # set_hard_eardrum_border([])
                set_right_hard_eardrum_border_template([])
            elif name == '左耳':
                # set_left_hard_eardrum_border([])
                set_left_hard_eardrum_border_template([])

        # 将最开始复制出来的OriginForCreateMould名称改为模型名称
        obj.hide_set(False)
        obj.name = name

        bpy.context.view_layer.objects.active = obj
        # 恢复完后重新复制一份
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)

        if enum == 'OP3' and restart:
            generateShell()

        # bpy.data.objects["右耳MouldReset"].hide_set(False)

    return recover_flag


def complete():
    '''
    确认创建模具
    '''
    name = bpy.context.scene.leftWindowObj
    # 切出创建模具时 需要被删除的物体的名称数组
    enum = bpy.context.scene.muJuTypeEnum
    if enum == 'OP4':
        # need_to_delete_model_name_list = [name + "OriginForFill", name + "OriginForDigHole"]
        need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                          "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                          name + "OuterRetopo", name + "InnerRetopo", name + "Circle", name + "Torus",
                                          name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                          name + "OuterSmooth", name + "InnerSmooth"]
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)
        delete_hole_border()  # 删除框架式耳模中的挖孔边界
    elif enum == "OP3":
        submit_shellcanal()
        submit_receiver()
        submitCircleCutPlane()      #先提交管道,再提交删除圆环和其他平面等物体;前者会使用到后者的物体
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR",  name + "shellInnerObj",
                              name + "meshPlaneBorderCurve", name + "PlaneBorderCurve"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        cubes_obj_list = [name + "cube1", name + "cube2", name + "cube3", name + "move_cube1", name + "move_cube2",
                          name + "move_cube3", name + "littleShellCube1", name + "littleShellCube2",
                          name + "littleShellCube3", name + "receiver", name + "ReceiverPlane",
                          name + "littleShellCube4", name + "littleShellCylinder1", name + "littleShellCylinder2"]
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)
        delete_useless_object(cubes_obj_list)
    elif enum == 'OP2':
        need_to_delete_model_name_list = [name + "HardEarDrumForSmooth", name + 'ForBottomFillReset']
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)

    elif enum == "OP1":
        need_to_delete_model_name_list = [name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                          "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                          name + "OuterRetopo", name + "InnerRetopo", name + "Circle", name + "Torus",
                                          name + "huanqiecompare", name + "UpperCircle", name + "UpperTorus",
                                          name + "OuterSmooth", name + "InnerSmooth"]
        public_object_list = [name + "OriginForCreateMouldR", name + "meshBottomRingBorderR",
                              name + "BottomRingBorderR"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        delete_useless_object(need_to_delete_model_name_list)
        delete_useless_object(public_object_list)
        delete_useless_object(curve_list)

    name = bpy.context.scene.leftWindowObj
    bpy.data.objects[name + "MouldReset"].hide_set(True)


class CreateMould(bpy.types.Operator):
    bl_idname = "object.createmould"
    bl_label = "3D Model"

    def modal(self, context, event):
        # 主窗口物体
        name = bpy.context.scene.leftWindowObj
        if bpy.context.screen.areas[0].spaces.active.context == 'SCENE':
            if is_on_object(name+'MouldReset', context, event):
                bpy.data.objects[name+"MouldReset"].hide_set(False)
            else:
                bpy.data.objects[name+"MouldReset"].hide_set(True)

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class CreateMouldInit(bpy.types.Operator):
    bl_idname = "object.createmouldinit"
    bl_label = "3D Model"

    def modal(self, context, event):
        global is_init_finish
        global is_init_finishL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            if not is_init_finish and get_switch_flag() and get_switch_time() == None:
                is_init_finish = True
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == 'OP2':
                    bpy.context.scene.yingErMoSheRuPianYiR = 0
                # 这里初始化
                frontToCreateMouldInit()
                global is_cut_finish
                is_cut_finish = False
        elif (name == "左耳"):
            if not is_init_finishL and get_switch_flag() and get_switch_time() == None:
                is_init_finishL = True
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == 'OP2':
                    bpy.context.scene.yingErMoSheRuPianYiL = 0
                # 这里初始化
                frontToCreateMouldInit()
                global is_cut_finishL
                is_cut_finishL = False

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def create_mould_cut():
    name = bpy.context.scene.leftWindowObj
    mould_type = bpy.context.scene.muJuTypeEnum
    if mould_type == 'OP2':
        if name == '右耳':
            bpy.context.scene.yingErMoSheRuPianYiR = 0
        elif name == '左耳':
            bpy.context.scene.yingErMoSheRuPianYiL = 0
    # 这里初始化
    frontToCreateMouldInit()
    cut_success = True
    try:
        mould_type = bpy.context.scene.muJuTypeEnum
        if mould_type == "OP1":
            print("软耳模切割")
            name = bpy.context.scene.leftWindowObj
            soft_eardrum_border = None
            if name == '右耳':
                soft_eardrum_border = get_right_soft_eardrum_border_template()
            elif name == '左耳':
                print("获取左耳模板")
                soft_eardrum_border = get_left_soft_eardrum_border_template()

            if len(soft_eardrum_border) == 0:
                if name == '右耳':
                    soft_eardrum_border = get_soft_eardrum_border()
                elif name == '左耳':
                    print("获取左耳模板")
                    soft_eardrum_border = get_left_soft_eardrum_border()
                init_hard_cut(soft_eardrum_border)
            # 说明修改过蓝线
            else:
                print("有过记录")
                re_hard_cut(soft_eardrum_border, 2, 2)

        elif mould_type == "OP2":
            print("硬耳膜切割")
            name = bpy.context.scene.leftWindowObj
            hard_eardrum_border = None
            if name == '右耳':
                hard_eardrum_border = get_right_hard_eardrum_border_template()
            elif name == '左耳':
                print("获取左耳模板")
                hard_eardrum_border = get_left_hard_eardrum_border_template()

            if len(hard_eardrum_border) == 0:
                if name == '右耳':
                    hard_eardrum_border = get_hard_eardrum_border()
                elif name == '左耳':
                    print("获取左耳模板")
                    hard_eardrum_border = get_left_hard_eardrum_border()
                init_hard_cut(hard_eardrum_border)
            # 说明修改过蓝线
            else:
                print("有过记录")
                re_hard_cut(hard_eardrum_border, 2, 2)

        elif mould_type == "OP3":
            print("外壳耳模切割")
            name = bpy.context.scene.leftWindowObj
            shell_border = None
            if name == '右耳':
                shell_border = get_right_shell_border()
            elif name == '左耳':
                print("获取左耳模板")
                shell_border = get_left_shell_border()

            generate_circle_for_cut()
            if len(shell_border) == 0:
                generate_border_curve()
            # 说明修改过蓝线
            else:
                print("有过记录")
                re_hard_cut(shell_border, 2, 2)

        elif mould_type == "OP4":
            print("框架式耳膜切割")
            name = bpy.context.scene.leftWindowObj
            frame_style_eardrum_border = None
            if name == '右耳':
                frame_style_eardrum_border = get_right_frame_style_eardrum_border_template()
            elif name == '左耳':
                print("获取左耳模板")
                frame_style_eardrum_border = get_left_frame_style_eardrum_border_template()

            if len(frame_style_eardrum_border) == 0:
                if name == '右耳':
                    frame_style_eardrum_border = get_frame_style_eardrum_border()
                elif name == '左耳':
                    print("获取左耳模板")
                    frame_style_eardrum_border = get_left_frame_style_eardrum_border()
                init_hard_cut(frame_style_eardrum_border)
            # 说明修改过蓝线
            else:
                print("有过记录")
                re_hard_cut(frame_style_eardrum_border, 2, 2)

            # extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")

    except:
        print("切割出错")
        cut_success = False
        # 回退到初始
        mould_type = bpy.context.scene.muJuTypeEnum
        if mould_type == "OP1":
            hard_recover_before_cut_and_remind_border()
        elif mould_type == "OP2":
            hard_recover_before_cut_and_remind_border()
        elif mould_type == "OP3":
            hard_recover_before_cut_and_remind_border()
        elif mould_type == "OP4":
            hard_recover_before_cut_and_remind_border()
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])

    if cut_success:
        create_mould_fill()


def create_mould_fill():
    name = bpy.context.scene.leftWindowObj
    mould_type = bpy.context.scene.muJuTypeEnum
    try:
        if mould_type == "OP1":
            print("软耳模填充")
            soft_fill()
        elif mould_type == "OP2":
            print("硬耳膜填充")
            hard_bottom_fill()
        elif mould_type == "OP3":
            print("外壳填充")
            init_shell()
        elif mould_type == "OP4":
            print("框架式耳膜挖洞与填充")
            # 之前版本：挖洞后上下边界桥接补面
            # dig_hole()
            # fill_closest_point()
            # 当前版本：在软耳膜的基础上挖洞
            frame_fill()
        if name == '右耳':
            bpy.context.scene.createmouldinitR = True
        elif name == '左耳':
            bpy.context.scene.createmouldinitL = True

    except:
        print("填充失败")
        mould_type = bpy.context.scene.muJuTypeEnum
        bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
        if mould_type == "OP2":
            # 回退到补面前的状态
            recover_before_fill()
            # 将选择模式改回点选择
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        elif mould_type == "OP1":
            reset_to_after_cut()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        elif mould_type == "OP3":
            reset_after_bottom_curve_change()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        elif mould_type == "OP4":
            # recover_to_dig()
            reset_to_after_cut()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])
        if name == '右耳':
            bpy.context.scene.createmouldinitR = True
        elif name == '左耳':
            bpy.context.scene.createmouldinitL = True



class CreateMouldCut(bpy.types.Operator): # 这里切割外型
    bl_idname = "object.createmouldcut"
    bl_label = "3D Model"

    def modal(self, context, event):
        global is_cut_finish
        global is_cut_finishL
        name = bpy.context.scene.leftWindowObj
        is_cut_finish_cur = True
        if (name == "右耳"):
            is_cut_finish_cur = is_cut_finish
            # if(not is_cut_finish):
            #     is_cut_finish = True
        elif (name == "左耳"):
            is_cut_finish_cur = is_cut_finishL
            # if (not is_cut_finishL):
            #     is_cut_finishL = True
        cut_success = True
        if not is_cut_finish_cur and get_switch_flag() and get_switch_time() == None:
            if name == '右耳':
                is_cut_finish = True
            elif name == '左耳':
                is_cut_finishL = True
            mould_type = bpy.context.scene.muJuTypeEnum
            if mould_type == 'OP2':
                if name == '右耳':
                    bpy.context.scene.yingErMoSheRuPianYiR = 0
                elif name == '左耳':
                    bpy.context.scene.yingErMoSheRuPianYiL = 0
            # 这里初始化
            frontToCreateMouldInit()
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    print("软耳模切割")
                    name = bpy.context.scene.leftWindowObj
                    soft_eardrum_border = None
                    if name == '右耳':
                        soft_eardrum_border = get_right_soft_eardrum_border_template()
                    elif name == '左耳':
                        print("获取左耳模板")
                        soft_eardrum_border = get_left_soft_eardrum_border_template()

                    if len(soft_eardrum_border) == 0:
                        if name == '右耳':
                            soft_eardrum_border = get_soft_eardrum_border()
                        elif name == '左耳':
                            print("获取左耳模板")
                            soft_eardrum_border = get_left_soft_eardrum_border()
                        init_hard_cut(soft_eardrum_border)
                    # 说明修改过蓝线
                    else:
                        print("有过记录")
                        re_hard_cut(soft_eardrum_border, 2, 2)

                elif mould_type == "OP2":
                    print("硬耳膜切割")
                    name = bpy.context.scene.leftWindowObj
                    hard_eardrum_border = None
                    if name == '右耳':
                        hard_eardrum_border = get_right_hard_eardrum_border_template()
                    elif name == '左耳':
                        print("获取左耳模板")
                        hard_eardrum_border = get_left_hard_eardrum_border_template()

                    if len(hard_eardrum_border) == 0:
                        if name == '右耳':
                            hard_eardrum_border = get_hard_eardrum_border()
                        elif name == '左耳':
                            print("获取左耳模板")
                            hard_eardrum_border = get_left_hard_eardrum_border()
                        init_hard_cut(hard_eardrum_border)
                    # 说明修改过蓝线
                    else:
                        print("有过记录")
                        re_hard_cut(hard_eardrum_border, 2, 2)

                elif mould_type == "OP3":
                    print("外壳耳模切割")
                    name = bpy.context.scene.leftWindowObj
                    shell_border = None
                    if name == '右耳':
                        shell_border = get_right_shell_border()
                    elif name == '左耳':
                        print("获取左耳模板")
                        shell_border = get_left_shell_border()

                    generate_circle_for_cut()
                    if len(shell_border) == 0:
                        generate_border_curve()
                    # 说明修改过蓝线
                    else:
                        print("有过记录")
                        re_hard_cut(shell_border, 2, 2)

                elif mould_type == "OP4":
                    print("框架式耳膜切割")
                    name = bpy.context.scene.leftWindowObj
                    frame_style_eardrum_border = None
                    if name == '右耳':
                        frame_style_eardrum_border = get_right_frame_style_eardrum_border_template()
                    elif name == '左耳':
                        print("获取左耳模板")
                        frame_style_eardrum_border = get_left_frame_style_eardrum_border_template()

                    if len(frame_style_eardrum_border) == 0:
                        if name == '右耳':
                            frame_style_eardrum_border = get_frame_style_eardrum_border()
                        elif name == '左耳':
                            print("获取左耳模板")
                            frame_style_eardrum_border = get_left_frame_style_eardrum_border()
                        init_hard_cut(frame_style_eardrum_border)
                    # 说明修改过蓝线
                    else:
                        print("有过记录")
                        re_hard_cut(frame_style_eardrum_border, 2, 2)

                    # extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")

            except:
                print("切割出错")
                cut_success = False
                # 回退到初始
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    hard_recover_before_cut_and_remind_border()
                elif mould_type == "OP2":
                    hard_recover_before_cut_and_remind_border()
                elif mould_type == "OP3":
                    hard_recover_before_cut_and_remind_border()
                elif mould_type == "OP4":
                    hard_recover_before_cut_and_remind_border()
                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])

            if cut_success:
                global is_fill_finish
                global is_fill_finishL
                if (name == "右耳"):
                    is_fill_finish = False
                elif (name == "左耳"):
                    is_fill_finishL = False

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class CreateMouldFill(bpy.types.Operator): # 这里填充
    bl_idname = "object.createmouldfill"
    bl_label = "3D Model"

    def modal(self, context, event):
        global is_fill_finish
        global is_fill_finishL
        is_fill_finish_cur = True
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            is_fill_finish_cur = is_fill_finish
            if(not is_fill_finish):
                is_fill_finish = True
        elif (name == "左耳"):
            is_fill_finish_cur = is_fill_finishL
            if (not is_fill_finishL):
                is_fill_finishL = True
        fill_success = True
        if not is_fill_finish_cur:
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    print("软耳模填充")
                    soft_fill()
                elif mould_type == "OP2":
                    print("硬耳膜填充")
                    hard_bottom_fill()
                elif mould_type == "OP3":
                    print("外壳填充")
                    init_shell()
                elif mould_type == "OP4":
                    print("框架式耳膜挖洞与填充")
                    # 之前版本：挖洞后上下边界桥接补面
                    # dig_hole()
                    # fill_closest_point()
                    # 当前版本：在软耳膜的基础上挖洞
                    start_time = time.time()
                    frame_fill()
                    end_time = time.time()
                    print(f"框架式耳模挖洞与填充时间：{end_time - start_time}")
                if name == '右耳':
                    bpy.context.scene.createmouldinitR = True
                elif name == '左耳':
                    bpy.context.scene.createmouldinitL = True

            except:
                print("填充失败")
                fill_success = False
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP2":
                    # 回退到补面前的状态
                    recover_before_fill()
                    # 将选择模式改回点选择
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                elif mould_type == "OP1":
                    reset_to_after_cut()
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                elif mould_type == "OP3":
                    reset_after_bottom_curve_change()
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                elif mould_type == "OP4":
                    # recover_to_dig()
                    reset_to_after_cut()
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])
                if name == '右耳':
                    bpy.context.scene.createmouldinitR = True
                elif name == '左耳':
                    bpy.context.scene.createmouldinitL = True


        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class TEST_OT_resethmould(bpy.types.Operator):
    bl_idname = "object.resetmould"
    bl_label = "重置操作"
    bl_description = "点击按钮重置创建磨具"

    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 32
        return {'FINISHED'}

    def execute(self, context):
        print("开始重置")
        enum = bpy.context.scene.muJuTypeEnum
        recover(enum)   # 恢复到切割前的状态

        # enum = bpy.context.scene.muJuTypeEnum
        # if enum == "OP1":
        #     set_finish(True)
        # elif enum == "OP2": # 硬耳膜重置之后，要进行初始化切割
        #     # 重置记录的模板为空
        #     if name == '右耳':
        #         set_left_hard_eardrum_border_and_normal_template([])
        #         hard_eardrum_border = get_hard_eardrum_border()
        #     elif name == '左耳':
        #         set_left_hard_eardrum_border_and_normal_template([])
        #         hard_eardrum_border = get_left_hard_eardrum_border()
        #     reset_cut_success = True
        #     try:
        #         init_hard_cut(hard_eardrum_border)
        #     except:
        #         print("重置切割出错")
        #         reset_cut_success = False
        #         # 回退到初始
        #         hard_recover_before_cut_and_remind_border()
        #
        #     if reset_cut_success:
        #         bpy.ops.object.pointfill('INVOKE_DEFAULT')
        #         global is_fill_finish
        #         is_fill_finish = False


class TEST_OT_finishmould(bpy.types.Operator):
    bl_idname = "object.finishmould"
    bl_label = "完成操作"
    bl_description = "点击按钮完成创建磨具"

    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 31
        return {'FINISHED'}

    def execute(self, context):
        complete()


class resetmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetmould"
    bl_label = "重置创建磨具"
    bl_description = (
        "点击重置创建磨具"
    )
    bl_icon = "ops.curves.sculpt_comb"
    bl_widget = None
    bl_keymap = (
        ("object.resetmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class finishmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishmould"
    bl_label = "完成创建磨具"
    bl_description = (
        "点击完成创建磨具"
    )
    bl_icon = "ops.curves.sculpt_delete"
    bl_widget = None
    bl_keymap = (
        ("object.finishmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class canalmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.canalmould"
    bl_label = "初始化创建通道"
    bl_description = (
        "点击在磨具上创建通道"
    )
    bl_icon = "brush.sculpt.clay_thumb"
    bl_widget = None
    bl_keymap = (
        ("object.updateshellcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class limitmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.limitmould"
    bl_label = "限制器件不能脱出磨具范围"
    bl_description = (
        "点击限制磨具"
    )
    bl_icon = "brush.sculpt.clay_strips"
    bl_widget = None
    bl_keymap = (
        ("object.updatecollision", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrormould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrormould"
    bl_label = "镜像创建磨具"
    bl_description = (
        "点击镜像创建磨具"
    )
    bl_icon = "brush.gpencil_draw.tint"
    bl_widget = None
    bl_keymap = (
        ("object.mirrormould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    # CreateMouldInit,
    # CreateMouldCut,
    # CreateMouldFill,
    TEST_OT_resethmould,
    TEST_OT_finishmould,
]


def register_createmould_tools():
    bpy.utils.register_tool(resetmould_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishmould_MyTool, separator=True,
                            group=False, after={resetmould_MyTool.bl_idname})
    bpy.utils.register_tool(canalmould_MyTool, separator=True, group=False,
                            after={finishmould_MyTool.bl_idname})
    bpy.utils.register_tool(limitmould_MyTool, separator=True, group=False,
                            after={canalmould_MyTool.bl_idname})
    bpy.utils.register_tool(mirrormould_MyTool, separator=True,
                            group=False, after={limitmould_MyTool.bl_idname})


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(resetmould_MyTool, separator=True, group=False)
    # bpy.utils.register_tool(finishmould_MyTool, separator=True,
    #                         group=False, after={resetmould_MyTool.bl_idname})
    # bpy.utils.register_tool(canalmould_MyTool, separator=True, group=False,
    #                         after={finishmould_MyTool.bl_idname})
    # bpy.utils.register_tool(limitmould_MyTool, separator=True, group=False,
    #                         after={canalmould_MyTool.bl_idname})
    # bpy.utils.register_tool(mirrormould_MyTool, separator=True,
    #                         group=False, after={limitmould_MyTool.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(resetmould_MyTool)
    bpy.utils.unregister_tool(finishmould_MyTool)
    bpy.utils.unregister_tool(canalmould_MyTool)
    bpy.utils.unregister_tool(limitmould_MyTool)
    bpy.utils.unregister_tool(mirrormould_MyTool)



