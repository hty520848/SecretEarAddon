import bpy
import bmesh
import re

from ..utils.utils import *
from ..tool import moveToRight, initialTransparency, newColor
from .frame_style_eardrum.frame_style_eardrum import apply_frame_style_eardrum_template
from .soft_eardrum.soft_eardrum import apply_soft_eardrum_template
from .soft_eardrum.thickness_and_fill import set_finish
from .hard_eardrum.hard_eardrum import apply_hard_eardrum_template
from .hard_eardrum.hard_eardrum import bottom_smooth


def frontToCreateMould():
    # 创建MouldReset,用于模型重置  与 模块向前返回时的恢复(若存在MouldReset则先删除)
    # 模型初始化,完成挖孔和切割操作                                          #TODO  初始化
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳MouldReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    utils_re_color("右耳", (1, 0.319, 0.133))
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "MouldReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    # duplicate_obj1.hide_set(True)
    newColor('blue', 0, 0, 1, 1, 1)
    initialTransparency()
    duplicate_obj1.data.materials.clear()
    duplicate_obj1.data.materials.append(bpy.data.materials['Transparency'])
    bpy.data.objects["右耳MouldReset"].select_set(False)
    bpy.context.view_layer.objects.active = obj
    moveToRight(duplicate_obj1)
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['Yellow'])

    apply_template()

    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(False)


def frontFromCreateMould():
    # 根据MouldReset复制出来一份物体以替换当前激活物体,完成模型的还原            #TODO   使用MouldReset恢复为刚进入Create Mould模块的状态
    # 将MouldReset和MouldLast删除
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    resetname = name + "MouldReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = ["右耳OriginForCreateMouldR", "HoleCutCylinderBottomR", "meshBottomRingBorderR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", "右耳huanqiecompare", "FillPlane",
                                      "右耳ForGetFillPlane", "dragcurve", "selectcurve"]
    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()
    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)


def backToCreateMould():
    # 先判断是否存在MouldReset                                            #TODO   使用MouldReset恢复为CreateMould模块执行后的最初状态,之后再初始化
    # 存在MouldReset时,将MouldReset复制一份用来替换当前激活物体，并执行初始化操作
    # 若不存在MouldReset,则说明直接跳过了 CreateMould  模块。根据上一个模块的最后保存的状态复制出来MouldReset,再根据MouldReset复制一份替换当前激活物体，再初始化，完成模型的恢复
    exist_MouldReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳MouldReset"):
            exist_MouldReset = True
            selected_obj.hide_set(False)
    if (exist_MouldReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "MouldReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.data.materials.clear()
        duplicate_obj.data.materials.append(bpy.data.materials['Yellow'])

        apply_template()
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳QieGeLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "MouldReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "MouldReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "MouldReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.data.materials.clear()
        duplicate_obj.data.materials.append(bpy.data.materials['Yellow'])

        apply_template()

    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(False)


def backFromCreateMould():
    # 创建MouldLast,用于 模型从后面模块返回时的恢复(若存在MouldLast则先将其删除)
    # 模型提交，将挖孔和切割操作提交                                       #TODO  提交

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳MouldLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
        elif (selected_obj.name == "右耳MouldReset"):
            selected_obj.hide_set(True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "MouldLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = ["右耳OriginForCreateMouldR", "HoleCutCylinderBottomR", "meshBottomRingBorderR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", "右耳huanqiecompare", "FillPlane",
                                      "右耳ForGetFillPlane", "dragcurve", "selectcurve"]

    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()

    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)
        
    bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['右耳'].select_set(state=True)


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
    moveToRight(duplicate_obj)
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
        utils_re_color("右耳", (1, 0.319, 0.133))


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
    recover_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == "右耳OriginForCreateMouldR":
            recover_flag = True
            break
    # 找到最初创建的  OriginForCreateMould 才能进行恢复
    if recover_flag:
        # 删除不需要的物体
        need_to_delete_model_name_list = ["右耳", "HoleCutCylinderBottomR",
                                          "HoleBorderCurveR", "BottomRingBorderR", "cutPlane",
                                          "BottomRingBorderRForCutR",
                                          "右耳OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", "右耳huanqiecompare", "FillPlane",
                                          "右耳ForGetFillPlane", "meshBottomRingBorderR", "dragcurve", "selectcurve"]
        delete_useless_object(need_to_delete_model_name_list)
        delete_hole_border()
        # 将最开始复制出来的OriginForCreateMould名称改为模型名称
        obj.hide_set(False)
        obj.name = "右耳"

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
        moveToRight(duplicate_obj)

    return recover_flag


def complete():
    '''
    确认创建模具
    '''
    need_to_delete_model_name_list = ["HoleCutCylinderBottomR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane",
                                      "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", "右耳huanqiecompare", "FillPlane",
                                      "右耳ForGetFillPlane", "meshBottomRingBorderR", "dragcurve", "selectcurve"]
    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()
    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)







