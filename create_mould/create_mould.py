import bpy
import bmesh
import re

from ..utils.utils import *
from ..tool import moveToRight, moveToLeft, initialTransparency, newColor, is_on_object, \
    extrude_border_by_vertex_groups, apply_material
from .frame_style_eardrum.frame_style_eardrum import apply_frame_style_eardrum_template
from .soft_eardrum.soft_eardrum import apply_soft_eardrum_template
from .soft_eardrum.soft_eardrum import soft_eardrum_smooth_submit
from .soft_eardrum.thickness_and_fill import set_finish, reset_to_after_cut
from .hard_eardrum.hard_eardrum import apply_hard_eardrum_template
from .hard_eardrum.hard_eardrum import bottom_smooth
from .soft_eardrum.soft_eardrum import soft_fill, soft_cut
from .hard_eardrum.hard_eardrum import hard_fill
from .hard_eardrum.hard_eardrum_cut import init_hard_cut,hard_recover_before_cut_and_remind_border,re_hard_cut
from .hard_eardrum.hard_eardrum_bottom_fill import hard_bottom_fill
from .parameters_for_create_mould import get_hard_eardrum_border,get_left_hard_eardrum_border,get_right_hard_eardrum_border_and_normal_template,get_left_hard_eardrum_border_and_normal_template
from .parameters_for_create_mould import get_soft_eardrum_border,get_left_soft_eardrum_border,get_right_soft_eardrum_border_and_normal_template,get_left_soft_eardrum_border_and_normal_template
from .parameters_for_create_mould import get_frame_style_eardrum_border,get_left_frame_style_eardrum_border,get_right_frame_style_eardrum_border_and_normal_template,get_left_frame_style_eardrum_border_and_normal_template
from .frame_style_eardrum.frame_style_eardrum_dig_hole import dig_hole
from .frame_style_eardrum.frame_fill_inner_face import fill_closest_point

from ..tool import recover_and_remind_border


is_init_finish = True
is_init_finishL = True
is_cut_finish = True
is_cut_finishL = True
is_fill_finish = True
is_fill_finishL = True

def set_is_cut_finish(val):
    global is_cut_finish
    global is_cut_finishL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_cut_finish = val
    elif (name == "左耳"):
        is_cut_finishL = val

def frontToCreateMould():
    # 创建MouldReset,用于模型重置  与 模块向前返回时的恢复(若存在MouldReset则先删除)
    # 模型初始化,完成挖孔和切割操作                                          #TODO  初始化
    all_objs = bpy.data.objects
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name+"MouldReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    utils_re_color(name, (1, 0.319, 0.133))
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

    global is_init_finish
    global is_init_finishL
    if (name == "右耳"):
        is_init_finish = False
    elif (name == "左耳"):
        is_init_finishL = False


def frontToCreateMouldInit():

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    success = True
    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.context.active_object
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

def frontFromCreateMould():
    # 根据MouldReset复制出来一份物体以替换当前激活物体,完成模型的还原            #TODO   使用MouldReset恢复为刚进入Create Mould模块的状态
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

    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = [name + "OriginForCreateMouldR", name + "HoleCutCylinderBottomR", name + "meshBottomRingBorderR",
                                      name + "HoleBorderCurveR", name + "BottomRingBorderR", name + "cutPlane", name + "BottomRingBorderRForCutR",
                                      name + "OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", name + "huanqiecompare", name + "FillPlane",
                                      name + "ForGetFillPlane", name + "dragcurve", name + "selectcurve", name + "colorcurve", name + "point", name + "HardEarDrumForSmooth"]
    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()
    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def backToCreateMould():
    global is_init_finish
    global is_init_finishL

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
    handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (label_obj != None):
        bpy.data.objects.remove(label_obj, do_unlink=True)

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


    # 先判断是否存在MouldReset                                            #TODO   使用MouldReset恢复为CreateMould模块执行后的最初状态,之后再初始化
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
        # name = "右耳"  # TODO    根据导入文件名称更改
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
        apply_material()

        if (name == "右耳"):
            is_init_finish = False
        elif (name == "左耳"):
            is_init_finishL = False
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

        if (name == "右耳"):
            is_init_finish = False
        elif (name == "左耳"):
            is_init_finishL = False


    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(False)

    if not bpy.data.materials.get('Transparency'):
        initialTransparency()

    bpy.data.objects[name+"MouldReset"].hide_set(False)
    newColor('blue', 0, 0, 1, 1, 1)
    bpy.data.objects[name+"MouldReset"].data.materials.clear()
    bpy.data.objects[name+"MouldReset"].data.materials.append(bpy.data.materials['Transparency'])

    # 这里本地调试时出现报错，需要激活右耳为当前活动物体
    # bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.data.objects['右耳'].select_set(state=True)


def backFromCreateMould():
    # 创建MouldLast,用于 模型从后面模块返回时的恢复(若存在MouldLast则先将其删除)
    # 模型提交，将挖孔和切割操作提交                                       #TODO  提交

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

    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = [name + "OriginForCreateMouldR", name + "HoleCutCylinderBottomR", name + "meshBottomRingBorderR",
                                      name + "HoleBorderCurveR", name + "BottomRingBorderR", name + "cutPlane", name + "BottomRingBorderRForCutR",
                                      name + "OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", name + "huanqiecompare", name + "FillPlane",
                                      name + "ForGetFillPlane", name + "dragcurve", name + "selectcurve", name + "colorcurve", name + "point", name + "HardEarDrumForSmooth"]

    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()
    cur_obj_name = name
    cur_obj = bpy.data.objects.get(cur_obj_name)
    if (cur_obj != None):
        bpy.context.view_layer.objects.active = cur_obj
        soft_eardrum_smooth_submit()

    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def apply_template():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    success = True
    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    # todo 先加到右耳集合，后续调整左右耳适配
    name = cur_obj.name
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    mould_type = bpy.context.scene.muJuTypeEnum

    # 根据选择的模板调用对应的模板
    if mould_type == "OP1":
        print("软耳模")
        success = apply_soft_eardrum_template()
        bpy.context.scene.neiBianJiXian = False
    elif mould_type == "OP2":
        print("硬耳膜")
        apply_hard_eardrum_template()
        bpy.context.scene.neiBianJiXian = False
    elif mould_type == "OP3":
        print("一体外壳")
    elif mould_type == "OP4":
        print("框架式耳膜")
        apply_frame_style_eardrum_template()
        bpy.context.scene.neiBianJiXian = True
    elif mould_type == "OP5":
        print("常规外壳")
    elif mould_type == "OP6":
        print("实心面板")

    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
        # 布尔后，需要重新上色
    if success:
        utils_re_color(name, (1, 0.319, 0.133))


def delete_useless_object(need_to_delete_model_name_list):
    for selected_obj in bpy.data.objects:
        if (selected_obj.name in need_to_delete_model_name_list):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=False)

def delete_hole_border():
    for obj in bpy.data.objects:
        if re.match('HoleBorderCurve', obj.name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if re.match('meshHoleBorderCurve', obj.name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def recover():
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
        # 删除不需要的物体
        need_to_delete_model_name_list = [name, name + "HoleCutCylinderBottomR",
                                          name + "HoleBorderCurveR", name + "BottomRingBorderR", name + "cutPlane",
                                          name + "BottomRingBorderRForCutR",
                                          name + "OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", name + "huanqiecompare", name + "FillPlane",
                                          name + "ForGetFillPlane", name + "meshBottomRingBorderR", name + "dragcurve", name + "selectcurve", name + "colorcurve", name + "point", name + "HardEarDrumForSmooth"]
        delete_useless_object(need_to_delete_model_name_list)
        delete_hole_border()
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
        # todo 先加到右耳集合，后续调整左右耳适配
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)

        # bpy.data.objects["右耳MouldReset"].hide_set(False)

    return recover_flag


def complete():
    '''
    确认创建模具
    '''
    name = bpy.context.scene.leftWindowObj
    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = [name + "OriginForCreateMouldR", name + "HoleCutCylinderBottomR", name + "meshBottomRingBorderR",
                                      name + "HoleBorderCurveR", name + "BottomRingBorderR", name + "cutPlane", name + "BottomRingBorderRForCutR",
                                      name + "OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", name + "huanqiecompare", name + "FillPlane",
                                      name + "ForGetFillPlane", name + "dragcurve", name + "selectcurve", name + "colorcurve", name + "point", name + "HardEarDrumForSmooth"]

    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    bpy.data.objects[name+"MouldReset"].hide_set(True)
    cur_obj_name = name
    cur_obj = bpy.data.objects.get(cur_obj_name)
    if(cur_obj != None):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cur_obj
        cur_obj.select_set(True)
        modifier_name = "HardEarDrumModifier3"
        target_modifier = None
        for modifier in cur_obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier3")
        modifier_name = "HardEarDrumModifier2"
        target_modifier = None
        for modifier in cur_obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier2")
        modifier_name = "HardEarDrumModifier1"
        target_modifier = None
        for modifier in cur_obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier1")
        modifier_name = "HardEarDrumModifier"
        target_modifier = None
        for modifier in cur_obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier")
        modifier_name = "HardEarDrumModifier4"
        target_modifier = None
        for modifier in cur_obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier4")
        # soft_eardrum_smooth_submit()
    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)


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
            if not is_init_finish:
                is_init_finish = True
                # 这里初始化
                frontToCreateMouldInit()
                global is_cut_finish
                is_cut_finish = False
        elif (name == "左耳"):
            if not is_init_finishL:
                is_init_finishL = True
                # 这里初始化
                frontToCreateMouldInit()
                global is_cut_finishL
                is_cut_finishL = False



        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

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
            if(not is_cut_finish):
                is_cut_finish = True
        elif (name == "左耳"):
            is_cut_finish_cur = is_cut_finishL
            if (not is_cut_finishL):
                is_cut_finishL = True
        cut_success = True
        if not is_cut_finish_cur:
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    # pass
                    print("软耳模切割")
                    name = bpy.context.scene.leftWindowObj
                    soft_eardrum_border = None
                    if name == '右耳':
                        soft_eardrum_border = get_right_soft_eardrum_border_and_normal_template()
                    elif name == '左耳':
                        print("获取左耳模板")
                        # 改成获取left
                        soft_eardrum_border = get_left_soft_eardrum_border_and_normal_template()

                    # 说明修改过蓝线
                    if len(soft_eardrum_border) == 0:
                        if name == '右耳':
                            soft_eardrum_border = get_soft_eardrum_border()
                        elif name == '左耳':
                            print("获取左耳模板")
                            soft_eardrum_border = get_left_soft_eardrum_border()
                        init_hard_cut(soft_eardrum_border)
                    else:
                        print("有过记录")
                        re_hard_cut(soft_eardrum_border, 1.2, 0.7)

                    bpy.context.scene.neiBianJiXian = False
                elif mould_type == "OP2":

                    print("硬耳膜切割")
                    name = bpy.context.scene.leftWindowObj
                    hard_eardrum_border = None
                    if name == '右耳':
                        hard_eardrum_border = get_right_hard_eardrum_border_and_normal_template()
                    elif name == '左耳':
                        print("获取左耳模板")
                        # todo 改成获取left
                        hard_eardrum_border = get_left_hard_eardrum_border_and_normal_template()

                    #说明修改过蓝线
                    if len(hard_eardrum_border) == 0:
                        if name == '右耳':
                            hard_eardrum_border = get_hard_eardrum_border()
                        elif name == '左耳':
                            print("获取左耳模板")
                            hard_eardrum_border = get_left_hard_eardrum_border()
                        init_hard_cut(hard_eardrum_border)
                    else:
                        print("有过记录")
                        re_hard_cut(hard_eardrum_border, 1.2, 0.7)

                    bpy.context.scene.neiBianJiXian = False

                elif mould_type == "OP4":
                    print("框架式耳膜切割")
                    name = bpy.context.scene.leftWindowObj
                    frame_style_eardrum_border = None
                    if name == '右耳':
                        frame_style_eardrum_border = get_right_frame_style_eardrum_border_and_normal_template()
                    elif name == '左耳':
                        print("获取左耳模板")
                        # 改成获取left
                        frame_style_eardrum_border = get_left_frame_style_eardrum_border_and_normal_template()

                    # 说明修改过蓝线
                    if len(frame_style_eardrum_border) == 0:
                        if name == '右耳':
                            frame_style_eardrum_border = get_frame_style_eardrum_border()
                        elif name == '左耳':
                            print("获取左耳模板")
                            frame_style_eardrum_border = get_left_frame_style_eardrum_border()
                        init_hard_cut(frame_style_eardrum_border)
                    else:
                        print("有过记录")
                        re_hard_cut(frame_style_eardrum_border, 1.2, 0.7)
                    # 需要额外挤出底部边界
                    extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")

                    bpy.context.scene.neiBianJiXian = False
            except:
                print("切割出错")
                cut_success = False
                # 回退到初始
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    hard_recover_before_cut_and_remind_border()
                if mould_type == "OP2":
                    hard_recover_before_cut_and_remind_border()
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
                    # pass
                    print("软耳模填充")
                    soft_fill()
                    bpy.context.scene.neiBianJiXian = False
                elif mould_type == "OP2":
                    print("硬耳膜填充")
                    hard_bottom_fill()
                    # hard_fill()
                    bpy.context.scene.neiBianJiXian = False
                elif mould_type == "OP4":
                    print("框架式耳膜挖洞与填充")
                    dig_hole()
                    fill_closest_point()

                    bpy.context.scene.neiBianJiXian = False
            except:
                print("填充失败")
                fill_success = False
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP2":
                    # 回退到切割后
                    hard_recover_before_cut_and_remind_border()
                    # 将选择模式改回点选择
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                if mould_type == "OP1":
                    reset_to_after_cut()
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')


        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


# 注册类
_classes = [
    CreateMouldInit,
    CreateMouldCut,
    CreateMouldFill
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)



