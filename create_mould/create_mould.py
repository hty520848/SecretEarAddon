import bpy
import bmesh

from .dig_hole import dig_hole
from .bottom_ring import bottom_cut
from ..utils.utils import *
from .thickness import init_thickness
from ..tool import moveToRight


def frontToCreateMould():
    # 创建MouldReset,用于模型重置  与 模块向前返回时的恢复(若存在MouldReset则先删除)
    # 模型初始化,完成挖孔和切割操作                                          #TODO  初始化

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳MouldReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "MouldReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    apply_template()


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
    need_to_delete_model_name_list = ["右耳OriginForCreateMouldR", "HoleCutCylinderBottomR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR"]
    delete_useless_object(need_to_delete_model_name_list)


def backToCreateMould():
    # 先判断是否存在MouldReset                                            #TODO   使用MouldReset恢复为CreateMould模块执行后的最初状态,之后再初始化
    # 存在MouldReset时,将MouldReset复制一份用来替换当前激活物体，并执行初始化操作
    # 若不存在MouldReset,则说明直接跳过了 CreateMould  模块。根据上一个模块的最后保存的状态复制出来MouldReset,再根据MouldReset复制一份替换当前激活物体，再初始化，完成模型的恢复
    exist_MouldReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳MouldReset"):
            exist_MouldReset = True
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
        elif(bpy.data.objects.get("右耳LocalThickLast")!=None):
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

        apply_template()

def backFromCreateMould():
    # 创建MouldLast,用于 模型从后面模块返回时的恢复(若存在MouldLast则先将其删除)
    # 模型提交，将挖孔和切割操作提交                                       #TODO  提交

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳MouldLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "MouldLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = ["右耳OriginForCreateMouldR", "HoleCutCylinderBottomR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR"]

    delete_useless_object(need_to_delete_model_name_list)


def apply_template():

    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    # todo 先加到右耳集合，后续调整左右耳适配
    # moveToRight(duplicate_obj)

    dig_hole()
    bottom_cut()
    init_thickness()
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
        # 布尔后，需要重新上色
    utils_re_color("右耳", (1, 0.319, 0.133))


def delete_useless_object(need_to_delete_model_name_list):
    for selected_obj in bpy.data.objects:
        if (selected_obj.name in need_to_delete_model_name_list):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

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
                                          "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                          "右耳OriginForCutR"]
        delete_useless_object(need_to_delete_model_name_list)
        # 将最开始复制出来的OriginForCreateMould名称改为模型名称
        obj.name = "右耳"

    return recover_flag
