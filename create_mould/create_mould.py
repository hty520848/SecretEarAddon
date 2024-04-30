import bpy
import bmesh
import re

from ..utils.utils import *
from ..tool import moveToRight, initialTransparency, newColor, is_on_object
from .frame_style_eardrum.frame_style_eardrum import apply_frame_style_eardrum_template
from .soft_eardrum.soft_eardrum import apply_soft_eardrum_template
from .soft_eardrum.soft_eardrum import soft_eardrum_smooth_submit
from .soft_eardrum.thickness_and_fill import set_finish
from .hard_eardrum.hard_eardrum import apply_hard_eardrum_template
from .hard_eardrum.hard_eardrum import bottom_smooth
from .soft_eardrum.soft_eardrum import soft_fill, soft_cut
from .hard_eardrum.hard_eardrum import hard_cut, hard_fill


is_init_finish = True
is_cut_finish = True
is_fill_finish = True


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
    moveToRight(bpy.data.objects["右耳MouldReset"])
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

    global is_init_finish
    is_init_finish = False
    bpy.ops.object.createmouldinit('INVOKE_DEFAULT')

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
    # todo 先加到右耳集合，后续调整左右耳适配
    moveToRight(duplicate_obj)

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

    # 激活右耳为当前活动物体
    # bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.data.objects['右耳'].select_set(state=True)


def backToCreateMould():
    global is_init_finish
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
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.data.materials.clear()
        duplicate_obj.data.materials.append(bpy.data.materials['Yellow'])


        is_init_finish = False
        bpy.ops.object.createmouldinit('INVOKE_DEFAULT')
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
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.data.materials.clear()
        duplicate_obj.data.materials.append(bpy.data.materials['Yellow'])


        is_init_finish = False
        bpy.ops.object.createmouldinit('INVOKE_DEFAULT')

    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(False)

    if not bpy.data.materials.get('Transparency'):
        initialTransparency()

    bpy.data.objects["右耳MouldReset"].hide_set(False)
    bpy.data.objects["右耳MouldReset"].data.materials.clear()
    bpy.data.objects["右耳MouldReset"].data.materials.append(bpy.data.materials['Transparency'])

    # 这里本地调试时出现报错，需要激活右耳为当前活动物体
    # bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.data.objects['右耳'].select_set(state=True)


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
    moveToRight(bpy.data.objects["右耳MouldReset"])

    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = ["右耳OriginForCreateMouldR", "HoleCutCylinderBottomR", "meshBottomRingBorderR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", "右耳huanqiecompare", "FillPlane",
                                      "右耳ForGetFillPlane", "dragcurve", "selectcurve"]

    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()
    cur_obj_name = "右耳"
    cur_obj = bpy.data.objects.get(cur_obj_name)
    if (cur_obj != None):
        bpy.context.view_layer.objects.active = cur_obj
        soft_eardrum_smooth_submit()

    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)


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

        # bpy.data.objects["右耳MouldReset"].hide_set(False)

    return recover_flag


def complete():
    '''
    确认创建模具
    '''
    # 切出创建模具时 需要被删除的物体的名称数组
    need_to_delete_model_name_list = ["右耳OriginForCreateMouldR", "HoleCutCylinderBottomR", "meshBottomRingBorderR",
                                      "HoleBorderCurveR", "BottomRingBorderR", "cutPlane", "BottomRingBorderRForCutR",
                                      "右耳OriginForCutR", "右耳Circle", "右耳Torus","左耳Circle", "左耳Torus", "右耳huanqiecompare", "FillPlane",
                                      "右耳ForGetFillPlane", "dragcurve", "selectcurve"]

    delete_useless_object(need_to_delete_model_name_list)
    delete_hole_border()

    bpy.data.objects["右耳MouldReset"].hide_set(True)
    cur_obj_name = "右耳"
    cur_obj = bpy.data.objects.get(cur_obj_name)
    if(cur_obj != None):
        bpy.context.view_layer.objects.active = cur_obj
        soft_eardrum_smooth_submit()
    enum = bpy.context.scene.muJuTypeEnum
    if enum == "OP1":
        set_finish(True)


class CreateMould(bpy.types.Operator):
    bl_idname = "object.createmould"
    bl_label = "3D Model"

    def modal(self, context, event):
        if bpy.context.screen.areas[1].spaces.active.context == 'SCENE':
            if is_on_object('右耳MouldReset', context, event):
                bpy.data.objects["右耳MouldReset"].hide_set(False)
            else:
                bpy.data.objects["右耳MouldReset"].hide_set(True)

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class CreateMouldInit(bpy.types.Operator):
    bl_idname = "object.createmouldinit"
    bl_label = "3D Model"


    def modal(self, context, event):
        global is_init_finish
        if not is_init_finish:
            is_init_finish = True
            # 这里初始化
            frontToCreateMouldInit()
            global is_cut_finish
            is_cut_finish = False
            bpy.ops.object.createmouldcut('INVOKE_DEFAULT')
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class CreateMouldCut(bpy.types.Operator): # 这里切割外型
    bl_idname = "object.createmouldcut"
    bl_label = "3D Model"
    def modal(self, context, event):
        global is_cut_finish
        cut_success = True
        if not is_cut_finish:
            is_cut_finish = True
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    pass
                    print("软耳模切割")
                    soft_cut()
                    bpy.context.scene.neiBianJiXian = False
                elif mould_type == "OP2":
                    print("硬耳膜切割")
                    hard_cut()
                    bpy.context.scene.neiBianJiXian = False
            except:
                print("切割出错")
                cut_success = False
                # todo 回退到初始
            if cut_success:
                global is_fill_finish
                is_fill_finish = False
                bpy.ops.object.createmouldfill('INVOKE_DEFAULT')
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class CreateMouldFill(bpy.types.Operator): # 这里填充
    bl_idname = "object.createmouldfill"
    bl_label = "3D Model"
    def modal(self, context, event):
        global is_fill_finish
        fill_success = True
        if not is_fill_finish:
            is_fill_finish = True
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    pass
                    # print("软耳模填充")
                    # soft_fill()
                    # bpy.context.scene.neiBianJiXian = False
                elif mould_type == "OP2":
                    print("硬耳膜填充")
                    hard_fill()
                    bpy.context.scene.neiBianJiXian = False
            except:
                print("填充失败")
                fill_success = False
                # todo 回退到切割后
            return {'FINISHED'}

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



