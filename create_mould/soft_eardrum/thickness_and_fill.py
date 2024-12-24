import bpy
from bpy import context
from bpy_extras import view3d_utils
import mathutils
import bmesh
from mathutils import Vector
from bpy.types import WorkSpaceTool
from contextlib import redirect_stdout
import io
from ...tool import *
from ...utils.utils import *
import math
import datetime
from math import *
import time
from ...parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running, \
    set_soft_modal_start, get_soft_modal_start, get_point_qiehuan_modal_start, get_drag_curve_modal_start, \
    get_smooth_curve_modal_start


def soft_fill():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if bpy.context.scene.neiBianJiXianR:
            bpy.context.scene.neiBianJiXianR = False
        if bpy.context.scene.shiFouShangBuQieGeMianBanR:
            bpy.context.scene.shiFouShangBuQieGeMianBanR = False
        if bpy.context.scene.KongQiangMianBanTypeEnumR != 'OP1':
            bpy.context.scene.KongQiangMianBanTypeEnumR = 'OP1'
    elif name == '左耳':
        if bpy.context.scene.neiBianJiXianL:
            bpy.context.scene.neiBianJiXianL = False
        if bpy.context.scene.shiFouShangBuQieGeMianBanL:
            bpy.context.scene.shiFouShangBuQieGeMianBanL = False
        if bpy.context.scene.KongQiangMianBanTypeEnumL != 'OP1':
            bpy.context.scene.KongQiangMianBanTypeEnumL = 'OP1'
    set_finish(True)
    copyModel(name)  # 复制一份底部切割完成后的物体用于回退
    soft_eardrum()
    utils_re_color(name, (1, 0.319, 0.133))
    set_finish(False)


def save_outer_and_inner_origin():
    name = bpy.context.scene.leftWindowObj
    outer_obj = bpy.data.objects[name]
    inner_obj = bpy.data.objects[name + "Inner"]

    if bpy.data.objects.get(name + "OuterOrigin") is not None:
        bpy.data.objects.remove(bpy.data.objects[name + "OuterOrigin"], do_unlink=True)
    if bpy.data.objects.get(name + "InnerOrigin") is not None:
        bpy.data.objects.remove(bpy.data.objects[name + "InnerOrigin"], do_unlink=True)

    outer_obj_copy = outer_obj.copy()
    outer_obj_copy.data = outer_obj.data.copy()
    outer_obj_copy.name = name + "OuterOrigin"
    bpy.context.collection.objects.link(outer_obj_copy)
    outer_obj_copy.hide_set(True)

    inner_obj_copy = inner_obj.copy()
    inner_obj_copy.data = inner_obj.data.copy()
    inner_obj_copy.name = name + "InnerOrigin"
    bpy.context.collection.objects.link(inner_obj_copy)
    inner_obj_copy.hide_set(True)

    if name == '右耳':
        moveToRight(outer_obj_copy)
        moveToRight(inner_obj_copy)
    else:
        moveToLeft(outer_obj_copy)
        moveToLeft(inner_obj_copy)


def save_inner_smooth():
    name = bpy.context.scene.leftWindowObj
    inner_obj = bpy.data.objects[name + "Inner"]

    if bpy.data.objects.get(name + "InnerSmooth") is not None:
        bpy.data.objects.remove(bpy.data.objects[name + "InnerSmooth"], do_unlink=True)

    inner_obj_copy = inner_obj.copy()
    inner_obj_copy.data = inner_obj.data.copy()
    inner_obj_copy.name = name + "InnerSmooth"
    bpy.context.collection.objects.link(inner_obj_copy)
    inner_obj_copy.hide_set(True)

    if name == '右耳':
        moveToRight(inner_obj_copy)
    else:
        moveToLeft(inner_obj_copy)


def save_outer_smooth():
    name = bpy.context.scene.leftWindowObj
    outer_obj = bpy.data.objects[name]

    if bpy.data.objects.get(name + "OuterSmooth") is not None:
        bpy.data.objects.remove(bpy.data.objects[name + "OuterSmooth"], do_unlink=True)

    outer_obj_copy = outer_obj.copy()
    outer_obj_copy.data = outer_obj.data.copy()
    outer_obj_copy.name = name + "OuterSmooth"
    bpy.context.collection.objects.link(outer_obj_copy)
    outer_obj_copy.hide_set(True)

    if name == '右耳':
        moveToRight(outer_obj_copy)
    else:
        moveToLeft(outer_obj_copy)


def save_outer_and_inner_retopo():
    name = bpy.context.scene.leftWindowObj
    outer_obj = bpy.data.objects[name]
    inner_obj = bpy.data.objects[name + "Inner"]

    if bpy.data.objects.get(name + "OuterRetopo") is not None:
        bpy.data.objects.remove(bpy.data.objects["OuterRetopo"], do_unlink=True)
    if bpy.data.objects.get(name + "InnerRetopo") is not None:
        bpy.data.objects.remove(bpy.data.objects["InnerRetopo"], do_unlink=True)

    outer_obj_copy = outer_obj.copy()
    outer_obj_copy.data = outer_obj.data.copy()
    outer_obj_copy.name = name + "OuterRetopo"
    bpy.context.collection.objects.link(outer_obj_copy)
    outer_obj_copy.hide_set(True)
    moveToRight(outer_obj_copy)

    inner_obj_copy = inner_obj.copy()
    inner_obj_copy.data = inner_obj.data.copy()
    inner_obj_copy.name = name + "InnerRetopo"
    bpy.context.collection.objects.link(inner_obj_copy)
    inner_obj_copy.hide_set(True)
    moveToRight(inner_obj_copy)


def judge_if_need_invert():
    obj = bpy.context.object
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def get_linked_unprocessed_index(bm, now_index, source_index):
    vert = bm.verts[now_index]
    for edge in vert.link_edges:
        # 获取边的顶点
        v1 = edge.verts[0]
        v2 = edge.verts[1]
        # 确保获取的顶点不是当前顶点
        link_vert = v1 if v1 != vert else v2
        if link_vert.index in source_index:
            return link_vert.index
    return None


# 删除多余部分
def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.object
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='CutBorderInnerVertex')
    bpy.ops.object.vertex_group_select()

    # 补面
    bpy.ops.mesh.fill()

    # 选择循环点
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        # 判断最低点是否被选择
        invert_flag = judge_if_need_invert()

        if invert_flag:
            # 不需要反转，直接删除面即可
            bpy.ops.mesh.delete(type='FACE')
        else:
            # 反转一下，删除顶点
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

    # 最后，删一下边界的直接的面
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = obj.vertex_groups.get("CutBorderInnerVertex")
    bpy.ops.object.vertex_group_set_active(group='CutBorderInnerVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')


def border_smooth():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        pianyi = bpy.context.scene.KongQiangMianBanSheRuPianYiR
    elif name == '左耳':
        pianyi = bpy.context.scene.KongQiangMianBanSheRuPianYiL

    duplicate_obj = bpy.data.objects.get(name + "Innersoftcutsmoothforreset")
    try:
        replace_obj = duplicate_obj.copy()
        replace_obj.data = duplicate_obj.data.copy()
        replace_obj.name = duplicate_obj.name + "copy"
        replace_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(replace_obj)
        if name == '右耳':
            moveToRight(replace_obj)
        else:
            moveToLeft(replace_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = replace_obj
        replace_obj.hide_set(False)
        replace_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='CutBorderInnerVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.region_to_loop()
        if pianyi > 0:
            global now_radius
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            # todo: 存在把底部的内边界切掉的问题
            bpy.ops.circle.smooth(width=pianyi, center_border_group_name='CutBorderInnerVertex',
                                  max_smooth_width=3, circle_radius=now_radius)
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.data.objects.get(name + "Inner") != None:
            bpy.data.objects.remove(bpy.data.objects.get(name + "Inner"), do_unlink=True)
        replace_obj.name = name + "Inner"
        save_inner_smooth()
        return replace_obj

    except:
        print('软耳模空腔平滑失败')
        if bpy.data.objects.get(duplicate_obj.name + 'copy'):
            bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'copy'], do_unlink=True)
        if bpy.data.objects.get(duplicate_obj.name + 'copyBridgeBorder'):
            bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'copyBridgeBorder'],do_unlink=True)

        reset_to_after_thickness()
        bpy.context.view_layer.objects.active = bpy.data.objects[name]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[name].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


# 删除多余部分
def delete_useless_part_upper():
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.object
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='CutBorderOuterVertex')
    bpy.ops.object.vertex_group_select()

    # 补面
    bpy.ops.mesh.fill()

    # 选择循环点
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        # 判断最低点是否被选择
        invert_flag = judge_if_need_invert()

        if invert_flag:
            # 不需要反转，直接删除面即可
            bpy.ops.mesh.delete(type='FACE')
        else:
            # 反转一下，删除顶点
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

    # 最后，删一下边界的直接的面
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = obj.vertex_groups.get("CutBorderOuterVertex")
    bpy.ops.object.vertex_group_set_active(group='CutBorderOuterVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')


def border_smooth_upper():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        pianyi = bpy.context.scene.shangBuQieGeMianBanPianYiR
    elif name == '左耳':
        pianyi = bpy.context.scene.shangBuQieGeMianBanPianYiL
    duplicate_obj = bpy.data.objects.get(name + "softcutsmoothforreset")
    try:
        replace_obj = duplicate_obj.copy()
        replace_obj.data = duplicate_obj.data.copy()
        replace_obj.name = duplicate_obj.name + "copy"
        replace_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(replace_obj)
        if name == '右耳':
            moveToRight(replace_obj)
        else:
            moveToLeft(replace_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = replace_obj
        replace_obj.hide_set(False)
        replace_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='CutBorderOuterVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.region_to_loop()
        if pianyi > 0:
            global now_radius_upper
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            bpy.ops.circle.smooth(width=pianyi, center_border_group_name='CutBorderOuterVertex',
                                  max_smooth_width=3, circle_radius=now_radius_upper)
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(bpy.data.objects.get(name), do_unlink=True)
        replace_obj.name = name
        save_outer_smooth()
        return replace_obj

    except:
        print('上部切割面板平滑失败')
        if bpy.data.objects.get(duplicate_obj.name + 'copy'):
            bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'copy'], do_unlink=True)
        if bpy.data.objects.get(duplicate_obj.name + 'copyBridgeBorder'):
            bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'copyBridgeBorder'],do_unlink=True)

        reset_to_after_thickness()
        bpy.context.view_layer.objects.active = bpy.data.objects[name]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[name].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


def fill():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        kongqiangeunm = bpy.context.scene.KongQiangMianBanTypeEnumR
        shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR
    elif name == '左耳':
        kongqiangeunm = bpy.context.scene.KongQiangMianBanTypeEnumL
        shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanL
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # 减少顶点数量
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    number = 0
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            number += 1
    if number >= 1:
        # for i in range(1, number + 1):
        #     bpy.ops.object.vertex_group_set_active(group='HoleBorderVertex' + str(i))
        #     bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 局部重拓扑
    # retopo(obj.name, "BottomOuterBorderVertex", 0.5)

    if shangbuqiege:
        obj = soft_eardrum_outer_cut(obj)
    inner_obj = soft_eardrum_thickness(obj)
    # 重拓扑内外壁
    # outer_offset = bpy.context.scene.waiBianYuanSheRuPianYi
    # inner_offset = bpy.context.scene.neiBianYuanSheRuPianYi
    # if outer_offset != 0:
    #     soft_retopo_offset_cut(name, "BottomOuterBorderVertex", 0.5)
    # if inner_offset != 0:
    #     soft_retopo_offset_cut(inner_obj.name, "BottomInnerBorderVertex", 0.5)
    # save_outer_and_inner_retopo()

    if kongqiangeunm == 'OP1':
        inner_obj = soft_eardrum_inner_cut(inner_obj)
    if shangbuqiege:
        obj = border_smooth_upper()
    if kongqiangeunm == 'OP1':
        inner_obj = border_smooth()

    if inner_obj is not None and obj is not None:
        # 最后，合并内外壁并桥接底边
        join_outer_and_inner(inner_obj, obj)

        # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        soft_eardrum_smooth_name = name + "SoftEarDrumForSmooth"
        softeardrum_for_smooth_obj = bpy.data.objects.get(soft_eardrum_smooth_name)
        if (softeardrum_for_smooth_obj != None):
            bpy.data.objects.remove(softeardrum_for_smooth_obj, do_unlink=True)
        softeardrum_for_smooth_obj = obj.copy()
        softeardrum_for_smooth_obj.data = obj.data.copy()
        softeardrum_for_smooth_obj.name = obj.name + "SoftEarDrumForSmooth"
        softeardrum_for_smooth_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(softeardrum_for_smooth_obj)
        if name == '右耳':
            moveToRight(softeardrum_for_smooth_obj)
        else:
            moveToLeft(softeardrum_for_smooth_obj)
        softeardrum_for_smooth_obj.hide_set(True)

        # 软耳模边缘平滑
        soft_extrude_smooth_initial()

    # soft_eardrum_bottom_fill()
    # # 设置新的内外区域顶点组
    # soft_eardrum_vertex = obj.vertex_groups.get('OuterVertexNew')
    # if (soft_eardrum_vertex != None):
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.object.vertex_group_set_active('OuterVertexNew')
    #     bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
    #     bpy.ops.object.mode_set(mode='OBJECT')
    # soft_eardrum_vertex = obj.vertex_groups.new(name='OuterVertexNew')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.object.vertex_group_set_active(group='Inner')
    # bpy.ops.object.vertex_group_deselect()
    # bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # soft_eardrum_vertex = obj.vertex_groups.get('InnerVertexNew')
    # if (soft_eardrum_vertex != None):
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.object.vertex_group_set_active('InnerVertexNew')
    #     bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
    #     bpy.ops.object.mode_set(mode='OBJECT')
    # soft_eardrum_vertex = obj.vertex_groups.new(name='InnerVertexNew')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='Inner')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_deselect()
    # bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # # 将桥接后的顶点细分并将顶点指定到顶点组BottomBorderVertex
    # obj = bpy.data.objects[name]
    # soft_eardrum_vertex = obj.vertex_groups.get('BottomBorderVertex')
    # if (soft_eardrum_vertex != None):
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.object.vertex_group_set_active('BottomBorderVertex')
    #     bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
    #     bpy.ops.object.mode_set(mode='OBJECT')
    # soft_eardrum_vertex = obj.vertex_groups.new(name='BottomBorderVertex')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    #
    # #设置新的内外边缘平滑顶点组   原本的边缘顶点组包含了细分后的顶点
    # soft_eardrum_vertex = obj.vertex_groups.get('BottomOuterBorderVertexNew')
    # if (soft_eardrum_vertex != None):
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.object.vertex_group_set_active('BottomOuterBorderVertexNew')
    #     bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
    #     bpy.ops.object.mode_set(mode='OBJECT')
    # soft_eardrum_vertex = obj.vertex_groups.new(name='BottomOuterBorderVertexNew')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    # bpy.ops.object.vertex_group_deselect()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # soft_eardrum_vertex = obj.vertex_groups.get('BottomInnerBorderVertexNew')
    # if (soft_eardrum_vertex != None):
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.object.vertex_group_set_active('BottomInnerBorderVertexNew')
    #     bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
    #     bpy.ops.object.mode_set(mode='OBJECT')
    # soft_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerBorderVertexNew')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.select_more()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_deselect()
    # bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
    # bpy.ops.object.vertex_group_deselect()
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    #
    #
    # # soft_retopo_offset_cut(name, "BottomOuterBorderVertexNew", bpy.context.scene.zongHouDuR * 2 / 3)
    # # bpy.ops.object.mode_set(mode='EDIT')
    # # bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0.2, offset_pct=96, segments=10, profile=0.5,
    # #                    mark_seam=True, mark_sharp=True, release_confirm=True)
    # # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
    # name = bpy.context.scene.leftWindowObj
    # obj = bpy.data.objects.get(name)
    # soft_eardrum_smooth_name = name + "SoftEarDrumForSmooth"
    # soft_eardrum_smooth_obj = bpy.data.objects.get(soft_eardrum_smooth_name)
    # if (soft_eardrum_smooth_obj != None):
    #     bpy.data.objects.remove(soft_eardrum_smooth_obj, do_unlink=True)
    # duplicate_obj = obj.copy()
    # duplicate_obj.data = obj.data.copy()
    # duplicate_obj.name = obj.name + "SoftEarDrumForSmooth"
    # duplicate_obj.animation_data_clear()
    # bpy.context.scene.collection.objects.link(duplicate_obj)
    # if name == '右耳':
    #     moveToRight(duplicate_obj)
    # else:
    #     moveToLeft(duplicate_obj)
    # duplicate_obj.hide_set(True)
    #
    # #调用平滑修改器函数进行平滑,外边缘平滑
    # soft_smooth_initial()


def soft_eardrum_thickness(obj):
    number = 0
    name = bpy.context.scene.leftWindowObj
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            number += 1

    obj.vertex_groups.new(name="Inner")
    obj.vertex_groups.new(name="BottomInnerBorderVertex")

    delete_vert_group('Outer')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    obj.vertex_groups.new(name="Outer")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # if number >= 1:
    #     for i in range(1, number + 1):
    #         bpy.ops.object.vertex_group_set_active(group='HoleBorderVertex' + str(i))
    #         bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.remove_doubles(threshold=0.5)

    # 记录外边界顶点坐标
    # mesh = obj.data
    # bm = bmesh.from_edit_mesh(mesh)
    # ndigits = 1
    # bottom_outer_border_co = [(round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits)) for v in
    #                           bm.verts if v.select]
    # bottom_outer_border_co = [v.co for v in bm.verts if v.select]
    # first_bottom_vert_co = obj.matrix_world @ bottom_outer_border_co[0]

    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')

    # 首先，根据厚度使用一个实体化修改器
    if name == '右耳':
        thickness = bpy.context.scene.zongHouDuR
        # bianjixian = bpy.context.scene.neiBianJiXianR
    elif name == '左耳':
        thickness = bpy.context.scene.zongHouDuL
        # bianjixian = bpy.context.scene.neiBianJiXianL

    modifier = obj.modifiers.new(name="Thickness", type='SOLIDIFY')
    bpy.context.object.modifiers["Thickness"].solidify_mode = 'NON_MANIFOLD'
    bpy.context.object.modifiers["Thickness"].thickness = thickness
    # bpy.context.object.modifiers["Thickness"].use_rim = False
    bpy.context.object.modifiers["Thickness"].nonmanifold_thickness_mode = 'FIXED'  # 防止实体化之后某些顶点出现毛刺过长的现象
    bpy.context.object.modifiers["Thickness"].shell_vertex_group = "Inner"
    bpy.context.object.modifiers["Thickness"].rim_vertex_group = "BottomInnerBorderVertex"

    bpy.ops.object.modifier_apply(modifier="Thickness", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bpy.ops.mesh.select_all(action='DESELECT')
    # 选中内外边界
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    all_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_deselect()
    outer_index = [v.index for v in bm.verts if v.select]
    inner_index = [index for index in all_index if index not in outer_index]
    bpy.ops.object.mode_set(mode='OBJECT')
    delete_vert_group("BottomOuterBorderVertex")
    delete_vert_group("BottomInnerBorderVertex")
    set_vert_group("BottomOuterBorderVertex", outer_index)
    set_vert_group("BottomInnerBorderVertex", inner_index)

    # bpy.ops.object.mode_set(mode='EDIT')
    # bm = bmesh.from_edit_mesh(obj.data)
    # bpy.ops.mesh.select_all(action='DESELECT')

    # 选中与记录下的顶点坐标最接近的顶点，选中相连元素即为外壁
    # min_dist = float('inf')
    # closest_vertex = None
    # bm.verts.ensure_lookup_table()
    # verts = [v for v in bm.verts if v.is_boundary]
    # for vert in verts:
    #     world_co = obj.matrix_world @ vert.co
    #     dist = (world_co - first_bottom_vert_co).length
    #     if dist < min_dist:
    #         min_dist = dist
    #         closest_vertex = vert

    # 选择最近的顶点
    # if closest_vertex is not None:
    #     closest_vertex.select = True
    # bpy.ops.mesh.select_linked(delimit=set())
    # bpy.ops.mesh.select_all(action='INVERT')

    # 根据最高点分离出内外壁
    # top_vert = None
    # top_z = -math.inf
    # for v in bm.verts:
    #     if v.co[2] > top_z:
    #         top_z = v.co[2]
    #         top_vert = v
    # top_vert.select_set(True)
    # bpy.ops.mesh.select_linked(delimit=set())
    # bpy.ops.mesh.select_all(action='INVERT')

    # 根据底部边界的坐标分离出内外壁
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # verts = [v for v in bm.verts if v.select]
    # bpy.ops.mesh.select_all(action='DESELECT')
    # for v in verts:
    #     vert_co = (round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits))
    #     if vert_co not in bottom_outer_border_co:
    #         v.select = True
    # bpy.ops.mesh.select_linked(delimit=set())

    # 使用平滑修改器平滑内壁
    modifier = obj.modifiers.new(name="Smooth", type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].factor = 1
    bpy.context.object.modifiers["Smooth"].iterations = int(round(thickness, 1) * 10)
    bpy.context.object.modifiers["Smooth"].vertex_group = "Inner"
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != name:
                inner_obj = o
    inner_obj.name = name + "Inner"

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    if bpy.data.objects.get(obj.name + 'softcutsmoothforreset') != None:
        bpy.data.objects.remove(bpy.data.objects[obj.name + 'softcutsmoothforreset'], do_unlink=True)
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = obj.name + "softcutsmoothforreset"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)

    # 保存初始的内外壁, 用于红环切割、平滑时的回退
    save_outer_and_inner_origin()
    return inner_obj

    if number == 0 and not bianjixian:  # 不存在内编辑线
        # 重新设置内外壁顶点组和内壁顶点组
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # delete_vert_group('BottomOuterBorderVertex')
        delete_vert_group('Outer')
        bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bm = bmesh.from_edit_mesh(obj.data)
        # for v in bm.verts:
        #     if v.is_boundary:
        #         v.select_set(True)
        # obj.vertex_groups.new(name="BottomOuterBorderVertex")
        # bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='SELECT')
        obj.vertex_groups.new(name="Outer")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        inner_obj.select_set(True)
        bpy.context.view_layer.objects.active = inner_obj
        delete_vert_group('BottomOuterBorderVertex')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(inner_obj.data)
        for v in bm.verts:
            if v.is_boundary:
                v.select_set(True)
        inner_obj.vertex_groups.new(name="BottomInnerBorderVertex")
        bpy.ops.object.vertex_group_assign()
        # bpy.ops.mesh.select_all(action='SELECT')
        # inner_obj.vertex_groups.new(name="Inner")
        # bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

    elif number >= 1 and bianjixian:
        # 计算外壁顶点组的中心
        vertex_group_dict = {}
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        delete_vert_group('Outer')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        obj.vertex_groups.new(name="Outer")
        bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bottom_index = [v.index for v in bm.verts if v.select]
        bottom_center = sum([bm.verts[index].co for index in bottom_index], Vector()) / len(bottom_index)
        vertex_group_dict['BottomOuterBorderVertex'] = bottom_center

        for i in range(1, number + 1):
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='HoleBorderVertex' + str(i))
            bpy.ops.object.vertex_group_select()
            hole_index = [v.index for v in bm.verts if v.select]
            hole_center = sum([bm.verts[index].co for index in hole_index], Vector()) / len(hole_index)
            vertex_group_dict['HoleBorderVertex' + str(i)] = hole_center
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        inner_obj.select_set(True)
        bpy.context.view_layer.objects.active = inner_obj
        delete_vert_group('BottomOuterBorderVertex')
        for i in range(1, number + 1):
            delete_vert_group("HoleBorderVertex" + str(i))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(inner_obj.data)
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            if v.is_boundary:
                v.select_set(True)
        border_verts_index = [v.index for v in bm.verts if v.select]
        # bpy.ops.mesh.select_all(action='SELECT')
        # inner_obj.vertex_groups.new(name="Inner")
        # bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='DESELECT')
        upper_index = []
        while (len(border_verts_index) > 0):
            start_vert_index = border_verts_index[0]
            bm.verts[start_vert_index].select = True
            border_verts_index.remove(start_vert_index)
            now_vert_index = get_linked_unprocessed_index(bm, start_vert_index, border_verts_index)
            while (now_vert_index != None):
                bm.verts[now_vert_index].select = True
                border_verts_index.remove(now_vert_index)
                now_vert_index = get_linked_unprocessed_index(bm, now_vert_index, border_verts_index)
            select_verts_index = [v.index for v in bm.verts if v.select]
            center = sum([bm.verts[index].co for index in select_verts_index], Vector()) / len(select_verts_index)
            min_dis = float('inf')
            min_key = None
            for key in vertex_group_dict:
                ori_center = vertex_group_dict[key]
                dis = (center - ori_center).length
                if dis < min_dis:
                    min_dis = dis
                    min_key = key
            vertex_group_dict.pop(min_key)
            if min_key == 'BottomOuterBorderVertex':
                inner_obj.vertex_groups.new(name="BottomInnerBorderVertex")
                bpy.ops.object.vertex_group_assign()
            else:
                inner_obj.vertex_groups.new(name="HoleInnerBorderVertex" + min_key[-1])
                bpy.ops.object.vertex_group_assign()
                upper_index.extend(select_verts_index)
            bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        set_vert_group("UpInnerBorderVertex", upper_index)

    # 使用平滑修改器平滑内壁
    modifier = inner_obj.modifiers.new(name="Smooth", type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].factor = 1
    bpy.context.object.modifiers["Smooth"].iterations = int(round(thickness, 1) * 10)
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    # 保存初始的内外壁, 用于红环切割、平滑时的回退
    save_outer_and_inner_origin()
    return inner_obj


def soft_eardrum_inner_cut(inner_obj):
    global right_last_loc, right_last_ratation, right_last_radius, left_last_loc, left_last_ratation, left_last_radius
    name = bpy.context.scene.leftWindowObj
    # utils_bool_difference(inner_obj.name, name + "Circle")

    if name == '右耳':
        last_loc = right_last_loc
        last_ratation = right_last_ratation
        last_radius = right_last_radius
    elif name == '左耳':
        last_loc = left_last_loc
        last_ratation = left_last_ratation
        last_radius = left_last_radius
    if last_loc != None:
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=last_radius, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(last_ratation[0], last_ratation[1], last_ratation[2]), scale=(1.0, 1.0, 1.0))
        circle = bpy.context.active_object
        normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
        if normal.z > 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = inner_obj
        inner_obj.select_set(True)
        circle.select_set(True)
        bpy.ops.object.booltool_auto_difference()
    else:
        bpy.context.view_layer.objects.active = bpy.data.objects[inner_obj.name]
        utils_bool_difference(inner_obj.name, name + "Circle")

    # 切割完成后，设置切割边界顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    # 有时候切成功了，会直接把切面的新点选上，但顶点组会乱掉，所以把切完后自动选上的点从all里移出
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    mesh = inner_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    cut_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CutBorderInnerVertex", cut_border_index)
    delete_useless_part()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CutBorderInnerVertex')
    bpy.ops.object.vertex_group_select()
    # 将周围的面变成三角面
    # bpy.ops.mesh.select_more()
    # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='CutBorderInnerVertex')
    # bpy.ops.object.vertex_group_select()

    # 补面
    # bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.fill()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.data.objects.get(inner_obj.name + 'softcutsmoothforreset') != None:
        bpy.data.objects.remove(bpy.data.objects[inner_obj.name + 'softcutsmoothforreset'], do_unlink=True)
    duplicate_obj = inner_obj.copy()
    duplicate_obj.data = inner_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = inner_obj.name + "softcutsmoothforreset"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)
    return inner_obj


def soft_eardrum_outer_cut(outer_obj):
    global right_last_loc_upper, right_last_ratation_upper, right_last_radius_upper, \
        left_last_loc_upper, left_last_ratation_upper, left_last_radius_upper
    name = bpy.context.scene.leftWindowObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.context.active_object.vertex_groups.new(name="Outer")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # utils_bool_difference(inner_obj.name, name + "Circle")

    if name == '右耳':
        last_loc = right_last_loc_upper
        last_ratation = right_last_ratation_upper
        last_radius = right_last_radius_upper
    elif name == '左耳':
        last_loc = left_last_loc_upper
        last_ratation = left_last_ratation_upper
        last_radius = left_last_radius_upper
    if last_loc != None:
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=last_radius, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(last_ratation[0], last_ratation[1], last_ratation[2]), scale=(1.0, 1.0, 1.0))
        circle = bpy.context.active_object
        normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
        if normal.z > 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = outer_obj
        outer_obj.select_set(True)
        circle.select_set(True)
        bpy.ops.object.booltool_auto_difference()
    else:
        bpy.context.view_layer.objects.active = bpy.data.objects[outer_obj.name]
        utils_bool_difference(outer_obj.name, name + "UpperCircle")

    # 切割完成后，设置切割边界顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='Outer')
    # 有时候切成功了，会直接把切面的新点选上，但顶点组会乱掉，所以把切完后自动选上的点从all里移出
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    mesh = outer_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    cut_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CutBorderOuterVertex", cut_border_index)
    delete_useless_part_upper()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CutBorderOuterVertex')
    bpy.ops.object.vertex_group_select()
    # 将周围的面变成三角面
    # bpy.ops.mesh.select_more()
    # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='CutBorderOuterVertex')
    # bpy.ops.object.vertex_group_select()

    # 补面
    # bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.fill()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # if bpy.data.objects.get(outer_obj.name + 'softcutsmoothforreset') != None:
    #     bpy.data.objects.remove(bpy.data.objects[outer_obj.name + 'softcutsmoothforreset'], do_unlink=True)
    # duplicate_obj = outer_obj.copy()
    # duplicate_obj.data = outer_obj.data.copy()
    # duplicate_obj.animation_data_clear()
    # duplicate_obj.name = outer_obj.name + "softcutsmoothforreset"
    # bpy.context.collection.objects.link(duplicate_obj)
    # if name == '右耳':
    #     moveToRight(duplicate_obj)
    # else:
    #     moveToLeft(duplicate_obj)
    # duplicate_obj.hide_set(True)
    return outer_obj


def join_outer_and_inner(inner_obj, outer_obj):
    # number = 0
    # name = bpy.context.scene.leftWindowObj
    # for o in bpy.data.objects:
    #     if re.match(name + 'HoleBorderCurve', o.name) != None:
    #         number += 1
    #
    # if name == '右耳':
    #     bianjixian = bpy.context.scene.neiBianJiXianR
    # elif name == '左耳':
    #     bianjixian = bpy.context.scene.neiBianJiXianL
    #

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = outer_obj
    outer_obj.select_set(True)
    inner_obj.select_set(True)
    bpy.ops.object.join()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 对内部环切面板进行平滑后重新确定内顶点组
    delete_vert_group('Inner')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_set_active(group='Outer')
    bpy.ops.object.vertex_group_deselect()
    outer_obj.vertex_groups.new(name="Inner")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    return

    if number == 0 and not bianjixian:
        bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.remove_doubles(threshold=0.001)              #去除合并顶点后的重叠顶点
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.bridge_edge_loops()

        bm = bmesh.from_edit_mesh(outer_obj.data)
        origin_faces_num = len(bm.faces)
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        outer_verts_index = [v.index for v in bm.verts if v.select]

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        inner_verts_index = [v.index for v in bm.verts if v.select]
        bpy.ops.mesh.select_all(action='DESELECT')

        bm.verts.ensure_lookup_table()
        start_outer_vert = bm.verts[outer_verts_index[0]]
        start_outer_vert.select = True
        link_verts = [edge.other_vert(start_outer_vert) for edge in start_outer_vert.link_edges
                      if edge.other_vert(start_outer_vert).index in outer_verts_index]

        another_outer_vert = link_verts[0]
        another_outer_vert.select = True

        min_dis = float('inf')
        for index in inner_verts_index:
            vert = bm.verts[index]
            dis = (vert.co - start_outer_vert.co).length
            if dis < min_dis:
                min_dis = dis
                start_inner_vert = vert
        start_inner_vert.select = True

        link_verts = [edge.other_vert(start_inner_vert) for edge in start_inner_vert.link_edges
                      if edge.other_vert(start_inner_vert).index in inner_verts_index]

        min_dis = float('inf')
        for vert in link_verts:
            dis = (vert.co - another_outer_vert.co).length
            if dis < min_dis:
                min_dis = dis
                another_inner_vert = vert
        another_inner_vert.select = True

        # 先补一个面,再循环补面
        bpy.ops.mesh.edge_face_add()
        start_outer_vert.select = False
        start_inner_vert.select = False
        # 防止选到两个不相邻的点
        # link_verts = [edge.other_vert(start_outer_vert) for edge in start_outer_vert.link_edges]
        # if start_inner_vert.index in [v.index for v in link_verts]:
        #     start_inner_vert.select = False
        # else:
        #     another_inner_vert.select = False
        count = len(outer_verts_index)    # 应该补面的次数
        for _ in range(count):
            # before_fill_faces_num = len(bm.faces)
            bpy.ops.mesh.edge_face_add()
            # after_fill_faces_num = len(bm.faces)
            # if after_fill_faces_num == before_fill_faces_num:
            #     break

        new_faces_num = len(bm.faces)
        if len(outer_verts_index) != (new_faces_num - origin_faces_num):
            raise ValueError ('桥接循环边失败')

    elif number >= 1 and bianjixian:
        bpy.ops.object.mode_set(mode='EDIT')

        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_remove_from()
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.bridge_edge_loops()

        bm = bmesh.from_edit_mesh(outer_obj.data)
        origin_faces_num = len(bm.faces)
        # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        outer_verts_index = [v.index for v in bm.verts if v.select]

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        inner_verts_index = [v.index for v in bm.verts if v.select]
        bpy.ops.mesh.select_all(action='DESELECT')

        bm.verts.ensure_lookup_table()
        start_outer_vert = bm.verts[outer_verts_index[0]]
        start_outer_vert.select = True
        link_verts = [edge.other_vert(start_outer_vert) for edge in start_outer_vert.link_edges
                      if edge.other_vert(start_outer_vert).index in outer_verts_index]

        another_outer_vert = link_verts[0]
        another_outer_vert.select = True

        min_dis = float('inf')
        for index in inner_verts_index:
            vert = bm.verts[index]
            dis = (vert.co - start_outer_vert.co).length
            if dis < min_dis:
                min_dis = dis
                start_inner_vert = vert
        start_inner_vert.select = True

        link_verts = [edge.other_vert(start_inner_vert) for edge in start_inner_vert.link_edges
                      if edge.other_vert(start_inner_vert).index in inner_verts_index]

        min_dis = float('inf')
        for vert in link_verts:
            dis = (vert.co - another_outer_vert.co).length
            if dis < min_dis:
                min_dis = dis
                another_inner_vert = vert
        another_inner_vert.select = True

        # 先补一个面,再循环补面
        bpy.ops.mesh.edge_face_add()
        start_outer_vert.select = False
        start_inner_vert.select = False
        # 防止选到两个不相邻的点
        # link_verts = [edge.other_vert(start_outer_vert) for edge in start_outer_vert.link_edges]
        # if start_inner_vert.index in [v.index for v in link_verts]:
        #     start_inner_vert.select = False
        # else:
        #     another_inner_vert.select = False
        count = len(outer_verts_index)  # 应该补面的次数
        for _ in range(count):
            # before_fill_faces_num = len(bm.faces)
            bpy.ops.mesh.edge_face_add()
            # after_fill_faces_num = len(bm.faces)
            # if after_fill_faces_num == before_fill_faces_num:
            #     break

        new_faces_num = len(bm.faces)
        if len(outer_verts_index) != (new_faces_num - origin_faces_num):
            raise ValueError('桥接循环边失败')

        for i in range(1, number + 1):
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='HoleBorderVertex' + str(i))
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.bridge_edge_loops()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
        bpy.ops.object.vertex_group_remove_from()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')

    #由于环切后再合并可能改变了模型法线方向进而影响了内外边缘平滑,因此我们重新计算了法线
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 对内部环切面板进行平滑后重新确定内顶点组
    delete_vert_group('Inner')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_set_active(group='Outer')
    bpy.ops.object.vertex_group_deselect()
    outer_obj.vertex_groups.new(name="Inner")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.shade_smooth()


def soft_eardrum_bottom_fill():
    '''
    对软耳膜内外壁的切割底部进行补面
    '''
    #将软耳膜内外壁之间的底部分离出来
    name = bpy.context.scene.leftWindowObj
    # main_obj = bpy.data.objects.get(name)
    main_obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')
    for obj in bpy.data.objects:
        if obj.select_get() and obj != main_obj:
            inner_obj = obj
            break
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = inner_obj
    inner_obj.name = name + "SoftBottom"
    if name == '右耳':
        moveToRight(inner_obj)
    elif name == '左耳':
        moveToLeft(inner_obj)

    # 将分离出的底面细分
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    edges = [e for e in bm.edges if e.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='EDGE')
    for e in edges:
        if not e.is_boundary:
            e.select_set(True)
    bpy.ops.mesh.subdivide(number_cuts=6, ngon=False, quadcorner='INNERVERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 计算软耳膜外边缘平滑的分组距离并设置顶点组
    soft_eardrum_outer_smooth = 0
    if (name == "右耳"):
        soft_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiR, 1)
    elif (name == "左耳"):
        soft_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiL, 1)

    # 外边界平滑不为0的时候,将软耳膜底面的外边界沿法线挤出向下走使其凸起
    if (soft_eardrum_outer_smooth != 0):
        extrudeOuterVertex(soft_eardrum_outer_smooth)


    #将分离出的底面与软耳膜模型合并
    bpy.ops.object.select_all(action='DESELECT')
    inner_obj.select_set(True)
    main_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return main_obj






soft_eardrum_outer_vert_index1 = []           #分段存储软耳膜平滑中用于Smooth函数的顶点索引
soft_eardrum_outer_vert_index2 = []           #分段存储软耳膜平滑中用于Smooth函数的顶点索引
soft_eardrum_outer_vert_index3 = []           #分段存储软耳膜平滑中用于Smooth函数的顶点索引


def getSoftEarDrumOuterIndex1():
    global soft_eardrum_outer_vert_index1
    return soft_eardrum_outer_vert_index1

def getSoftEarDrumOuterIndex2():
    global soft_eardrum_outer_vert_index2
    return soft_eardrum_outer_vert_index2

def getSoftEarDrumOuterIndex3():
    global soft_eardrum_outer_vert_index3
    return soft_eardrum_outer_vert_index3


soft_eardrum_inner_vert_index1 = []           #分段存储软耳膜平滑中用于Smooth函数的顶点索引
soft_eardrum_inner_vert_index2 = []           #分段存储软耳膜平滑中用于Smooth函数的顶点索引
soft_eardrum_inner_vert_index3 = []           #分段存储软耳膜平滑中用于Smooth函数的顶点索引


def getSoftEarDrumInnerIndex1():
    global soft_eardrum_inner_vert_index1
    return soft_eardrum_inner_vert_index1

def getSoftEarDrumInnerIndex2():
    global soft_eardrum_inner_vert_index2
    return soft_eardrum_inner_vert_index2

def getSoftEarDrumInnerIndex3():
    global soft_eardrum_inner_vert_index3
    return soft_eardrum_inner_vert_index3


def vert_index_to_vertex_group(vert_index_list, vertex_group_name):
    '''
    针对当前激活的物体,根据给出的顶点组名称,创建一个顶点组,并将顶点索引中的顶点加入到该顶点组中
    '''

    # 将满足距离的顶点选中:
    obj = bpy.context.active_object
    if(obj != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            for vert_index in vert_index_list:
                vert = bm.verts[vert_index]
                vert.select_set(True)
            bm.to_mesh(me)
            bm.free()
        # 根据底部边缘顶点扩大范围得到用于底部平滑的顶点组
        hard_eardrum_vertex = obj.vertex_groups.get(vertex_group_name)
        if (hard_eardrum_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group=vertex_group_name)
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        hard_eardrum_vertex = obj.vertex_groups.new(name=vertex_group_name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group=vertex_group_name)
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')

def laplacian_smooth(smooth_index, factor):
    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    select_vert = list()
    for index in smooth_index:
        select_vert.append(bm.verts[index])

    for v in select_vert:
        final_co = v.co * 0
        if len(v.link_edges) == 0:
            continue
        for edge in v.link_edges:
            # 确保获取的顶点不是当前顶点
            link_vert = edge.other_vert(v)
            final_co += link_vert.co
        final_co /= len(v.link_edges)
        v.co = v.co + factor * (final_co - v.co)

def extrudeOuterVertex(outer_smooth):
    '''
    将软耳膜底部的顶点根据外边缘平滑参数的大小向内走一段距离形成向内的凸起
    '''
    """ 将顶点沿法线凹陷 """
    prev_vertex_index = []  # 记录选中内圈时已经选中过的顶点
    new_vertex_index = []  # 记录新选中的内圈顶点,当无新选中的内圈顶点时,说明底部平面的所有内圈顶点都已经被选中的,结束循环
    cur_vertex_index = []  # 记录扩散区域后当前选中的顶点
    inner_circle_index = -1  # 判断当前选中顶点的圈数,根据圈数确定往里走的距离
    index_normal_dict = dict()  # 由于移动一圈顶点后，剩下的顶点的法向会变，导致突出方向出现问题，所以需要存一下初始的方向

    name = bpy.context.scene.leftWindowObj
    inner_obj = bpy.data.objects.get(name + "SoftBottom")
    obj = inner_obj
    if (obj != None):
        #将底面的外边界点选中
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.mode_set(mode='OBJECT')
        # 初始化集合
        if obj.type == 'MESH':
            # 获取当前激活物体的网格数据
            me = obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            # 根据面板参数设置偏移值
            for vert in bm.verts:
                if (vert.select == True):
                    prev_vertex_index.append(vert.index)
                index_normal_dict[vert.index] = vert.normal[0:3]
            bm.to_mesh(me)
            bm.free()
        # 初始化集合使得其能够进入while循环
        new_vertex_index.append(0)
        # print("初始化长度:", len(prev_vertex_index))
        # print("初始化长度:", len(new_vertex_index))
        while (len(new_vertex_index) != 0 and inner_circle_index<= 4):
            # while(inner_circle_index <= 6):
            inner_circle_index += 1
            # print("当前圈数:", inner_circle_index)
            # 根据当前选中顶点扩散得到新选中的顶点
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_more()
            bpy.ops.object.mode_set(mode='OBJECT')
            # 根据之前记录的选中顶点数组将之前顶点取消选中,使得只有新增的内圈顶点被选中
            cur_vertex_index.clear()
            if obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                for vert in bm.verts:
                    if (vert.select == True):
                        cur_vertex_index.append(vert.index)
                bm.to_mesh(me)
                bm.free()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            result = [x for x in cur_vertex_index if x not in prev_vertex_index]
            # 将集合new_vertex_index_set清空并将新选中的内圈顶点保存到集合中
            new_vertex_index.clear()
            new_vertex_index = result
            if obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                for vert_index in new_vertex_index:
                    vert = bm.verts[vert_index]
                    vert.select_set(True)
                bm.to_mesh(me)
                bm.free()
            # 新选中的内圈顶点沿着法线向内放缩
            if obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                # 为了不让平滑边缘出现锐角，前几圈往外突，后几圈才内凹
                #            if inner_circle_index < 3:
                #                dir = -1.5
                #            else:
                dir = -0.6                               #外边缘平滑参数为2时,dir为-0.6
                if(outer_smooth != 0):
                    dir = -0.6 * (outer_smooth / 2)
                #底部细分参数为6,中间有6圈,第0,1,2,3圈step依次增加,第4,5圈再依次降低
                if(inner_circle_index != 4 and inner_circle_index !=5):
                    step = (1 - 0.9 ** (inner_circle_index + 1)) * 5 * dir
                elif(inner_circle_index == 4):
                    step = (1 - 0.9 ** (3)) * 5 * dir
                else:
                    step = (1 - 0.9 ** (2)) * 5 * dir
                # 根据面板参数设置偏移值
                for vert in bm.verts:
                    if (vert.select == True):
                        dir = index_normal_dict[vert.index]
                        vert.co[0] -= dir[0] * step
                        vert.co[1] -= dir[1] * step
                        vert.co[2] -= dir[2] * step
                bm.to_mesh(me)
                bm.free()
            # 更新集合prev_vertex_index_set
            prev_vertex_index.extend(new_vertex_index)
            # print("新增顶点数:", len(new_vertex_index))
            # print("保存之前的顶点数:", len(prev_vertex_index))


def soft_extrude_smooth_initial():
    '''
    处理软耳膜内外边缘切割后桥接得到的底面
    根据面板的内外边缘参数决定底面外边缘向内挤出的距离,对内外边缘进行平滑
    '''

    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    soft_eardrum_smooth_name = name + "SoftEarDrumForSmooth"
    softeardrum_for_smooth_obj = bpy.data.objects.get(soft_eardrum_smooth_name)

    try:
        if(cur_obj != None and softeardrum_for_smooth_obj != None):
            duplicate_obj = softeardrum_for_smooth_obj.copy()
            duplicate_obj.data = softeardrum_for_smooth_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = name + "SoftEarDrumForSmoothing"
            bpy.context.scene.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            else:
                moveToLeft(duplicate_obj)
            bpy.ops.object.select_all(action='DESELECT')
            duplicate_obj.hide_set(False)
            duplicate_obj.select_set(True)
            bpy.context.view_layer.objects.active = duplicate_obj

            #对于软耳膜切割后形成的内外边缘桥接得到的底面,根据外边缘平滑参数的大小决定底面向内挤出的大小
            obj = soft_eardrum_bottom_fill()

            # 设置新的内外区域顶点组
            soft_eardrum_vertex = obj.vertex_groups.get('OuterVertexNew')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('OuterVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='OuterVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='Inner')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            soft_eardrum_vertex = obj.vertex_groups.get('InnerVertexNew')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('InnerVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='InnerVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='Inner')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='Inner')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            # bpy.ops.mesh.select_less()
            # bpy.ops.mesh.select_less()
            # bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            # 将桥接后的顶点细分并将顶点指定到顶点组BottomBorderVertex
            soft_eardrum_vertex = obj.vertex_groups.get('BottomBorderVertex')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomBorderVertex')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomBorderVertex')
            bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            # bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            # 设置新的内外边缘平滑顶点组   原本的边缘顶点组包含了细分后的顶点
            soft_eardrum_vertex = obj.vertex_groups.get('BottomOuterBorderVertexNew')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomOuterBorderVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomOuterBorderVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            soft_eardrum_vertex = obj.vertex_groups.get('BottomInnerBorderVertexNew')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerBorderVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerBorderVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.mesh.select_more()
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_deselect()
            # bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            # bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            soft_eardrum_vertex = obj.vertex_groups.get('BottomOuterSmooth')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomOuterSmooth')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomOuterSmooth')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterSmooth')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            soft_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')



            #定义内边缘平滑顶点组
            soft_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth1')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth1')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth1')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            soft_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth2')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth2')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth2')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterSmooth')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            soft_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth3')
            if (soft_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth3')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth3')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth3')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            # 调用平滑修改器函数进行平滑,内外边缘平滑
            soft_smooth_initial()

    except:
        print("软耳膜边缘平滑失败")
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'SoftEarDrumForSmoothing'):
            bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'SoftEarDrumForSmoothing'], do_unlink=True)
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'SoftEarDrumForSmoothing.001'):
            bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'SoftEarDrumForSmoothing.001'], do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
        bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(True)
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


def soft_smooth_initial():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name + "SoftEarDrumForSmoothing")
    #计算软耳膜外边缘平滑的分组距离并设置顶点组
    soft_eardrum_outer_smooth = 0
    if (name == "右耳"):
        soft_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiR, 1)
    elif (name == "左耳"):
        soft_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiL, 1)

    select_vert_index = []  # 保存根据底部顶点扩散得到的顶点
    soft_eardrum_vert_index1 = []  # 保存用于底部平滑的顶点
    soft_eardrum_vert_index2 = []  # 保存用于底部平滑的顶点
    soft_eardrum_vert_index3 = []  # 保存用于底部平滑的顶点
    soft_eardrum_vert_index4 = []  # 保存用于底部平滑的顶点
    global soft_eardrum_outer_vert_index1
    global soft_eardrum_outer_vert_index2
    global soft_eardrum_outer_vert_index3
    soft_eardrum_outer_vert_index1 = []  # 保存用于smooth函数边缘平滑的顶点
    soft_eardrum_outer_vert_index2 = []  # 保存用于smooth函数边缘平滑的顶点
    soft_eardrum_outer_vert_index3 = []  # 保存用于smooth函数边缘平滑的顶点

    print("软耳膜平滑初始化开始:", datetime.datetime.now())
    # 将底部一圈顶点复制出来用于计算最短距离
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    bottom_outer_obj = bpy.data.objects.get(name + "SoftEarDrumForSmoothing" + ".001")
    if (name == "右耳"):
        moveToRight(bottom_outer_obj)
    elif (name == "左耳"):
        moveToLeft(bottom_outer_obj)
    #将该复制出的平面设置为当前激活物体
    obj.select_set(False)
    bottom_outer_obj.select_set(True)
    bpy.context.view_layer.objects.active = bottom_outer_obj
    #选中底面复制出的一圈顶点并挤出形成一个柱面
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -0.05), "orient_type": 'GLOBAL',"orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),})
    bpy.ops.object.mode_set(mode='OBJECT')
    #将激活物体重新设置为左右耳模型
    bottom_outer_obj.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


    # 根据底部顶点组将扩散选中的顶点保存到数组中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.select_all(action='SELECT')
    for i in range(0,12):
        bpy.ops.mesh.select_more()
    bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
    bpy.ops.object.vertex_group_deselect()
    bpy.ops.object.mode_set(mode='OBJECT')
    if obj.type == 'MESH':
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for vert in bm.verts:
            if (vert.select == True):
                select_vert_index.append(vert.index)
        bm.to_mesh(me)
        bm.free()
    print("开始计算距离:", datetime.datetime.now())
    # 根据距离选中顶点
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if obj.type == 'MESH':
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for vert_index in select_vert_index:
            vert_co = bm.verts[vert_index].co
            _, closest_co, _, _ = bottom_outer_obj.closest_point_on_mesh(vert_co)
            min_distance = math.sqrt((vert_co[0] - closest_co[0]) ** 2 + (vert_co[1] - closest_co[1]) ** 2 + (
                    vert_co[2] - closest_co[2]) ** 2)
            if(soft_eardrum_outer_smooth < 0.5):
                # 调用平滑函数分段
                if (min_distance < 0.6):
                    soft_eardrum_outer_vert_index1.append(vert_index)
                if (min_distance >   0.4 and min_distance <   0.8):
                    soft_eardrum_outer_vert_index2.append(vert_index)
                if (min_distance < 1):
                    soft_eardrum_outer_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance <   (0.25 + 0.1)):
                    soft_eardrum_vert_index1.append(vert_index)
                if (min_distance >   (0.25 - 0.1) and min_distance <   (0.5 + 0.1)):
                    soft_eardrum_vert_index2.append(vert_index)
                if (min_distance >   (0.5 - 0.1) and min_distance <   (0.75 + 0.1)):
                    soft_eardrum_vert_index3.append(vert_index)
                if (min_distance > (0.75 - 0.1) and min_distance < 1):
                    soft_eardrum_vert_index4.append(vert_index)
            else:
                # 调用平滑函数分段
                if (min_distance < soft_eardrum_outer_smooth * 0.4):
                    soft_eardrum_outer_vert_index1.append(vert_index)
                if (min_distance > soft_eardrum_outer_smooth * 0.3 and min_distance < soft_eardrum_outer_smooth * 0.6):
                    soft_eardrum_outer_vert_index2.append(vert_index)
                if (min_distance < soft_eardrum_outer_smooth):
                    soft_eardrum_outer_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < soft_eardrum_outer_smooth * (0.25 + 0.1)):
                    soft_eardrum_vert_index1.append(vert_index)
                if (min_distance > soft_eardrum_outer_smooth * (0.25 - 0.1) and min_distance < soft_eardrum_outer_smooth * (0.5 + 0.1)):
                    soft_eardrum_vert_index2.append(vert_index)
                if (min_distance > soft_eardrum_outer_smooth * (0.5 - 0.1) and min_distance < soft_eardrum_outer_smooth * (0.75 + 0.1)):
                    soft_eardrum_vert_index3.append(vert_index)
                if (min_distance > soft_eardrum_outer_smooth * (0.75 - 0.1) and min_distance < soft_eardrum_outer_smooth):
                    soft_eardrum_vert_index4.append(vert_index)

    #将用于计算距离的底部平面删除
    bpy.data.objects.remove(bottom_outer_obj, do_unlink=True)

    print("将顶点索引赋值给顶点组:", datetime.datetime.now())
    #根据顶点索引将选中的顶点保存到顶点组中
    vert_index_to_vertex_group(soft_eardrum_vert_index1, "SoftEarDrumOuterVertex1")
    vert_index_to_vertex_group(soft_eardrum_vert_index2, "SoftEarDrumOuterVertex2")
    vert_index_to_vertex_group(soft_eardrum_vert_index3, "SoftEarDrumOuterVertex3")
    vert_index_to_vertex_group(soft_eardrum_vert_index4, "SoftEarDrumOuterVertex4")
    # vert_index_to_vertex_group(select_vert_index, "SoftEarDrumOuterVertex10")

    # 设置矫正平滑顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex1')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex2')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex3')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex4')
    bpy.ops.object.vertex_group_select()
    soft_eardrum_vertex = obj.vertex_groups.get("SoftEarDrumOuterVertex5")
    if (soft_eardrum_vertex != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="SoftEarDrumOuterVertex5")
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    soft_eardrum_vertex = obj.vertex_groups.new(name="SoftEarDrumOuterVertex5")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group="SoftEarDrumOuterVertex5")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')










    #计算软耳膜内边缘平滑的分组距离并设置顶点组
    soft_eardrum_inner_smooth = 0
    if (name == "右耳"):
        soft_eardrum_inner_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYiR, 1)
    elif (name == "左耳"):
        soft_eardrum_inner_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYiL, 1)

    select_vert_index = []  # 保存根据底部顶点扩散得到的顶点
    soft_eardrum_vert_index1 = []  # 保存用于底部平滑的顶点
    soft_eardrum_vert_index2 = []  # 保存用于底部平滑的顶点
    soft_eardrum_vert_index3 = []  # 保存用于底部平滑的顶点
    soft_eardrum_vert_index4 = []  # 保存用于底部平滑的顶点
    global soft_eardrum_inner_vert_index1
    global soft_eardrum_inner_vert_index2
    global soft_eardrum_inner_vert_index3
    soft_eardrum_inner_vert_index1 = []  # 保存用于smooth函数边缘平滑的顶点
    soft_eardrum_inner_vert_index2 = []  # 保存用于smooth函数边缘平滑的顶点
    soft_eardrum_inner_vert_index3 = []  # 保存用于smooth函数边缘平滑的顶点

    print("软耳膜平滑初始化开始:", datetime.datetime.now())
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # 将底部一圈顶点复制出来用于计算最短距离
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    bottom_inner_obj = bpy.data.objects.get(name + "SoftEarDrumForSmoothing" + ".001")
    if (name == "右耳"):
        moveToRight(bottom_inner_obj)
    elif (name == "左耳"):
        moveToLeft(bottom_inner_obj)
    # 将该复制出的平面设置为当前激活物体
    obj.select_set(False)
    bottom_inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = bottom_inner_obj
    # 选中底面复制出的一圈顶点并挤出形成一个柱面
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -0.05), "orient_type": 'GLOBAL',
                                                            "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), })
    bpy.ops.object.mode_set(mode='OBJECT')
    # 将激活物体重新设置为左右耳模型
    bottom_inner_obj.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 根据底部顶点组将扩散选中的顶点保存到数组中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    for i in range(0, 12):
        bpy.ops.mesh.select_more()
    bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
    bpy.ops.object.vertex_group_deselect()
    bpy.ops.object.mode_set(mode='OBJECT')
    if obj.type == 'MESH':
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for vert in bm.verts:
            if (vert.select == True):
                select_vert_index.append(vert.index)
        bm.to_mesh(me)
        bm.free()
    print("开始计算距离:", datetime.datetime.now())
    # 根据距离选中顶点
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if obj.type == 'MESH':
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for vert_index in select_vert_index:
            vert_co = bm.verts[vert_index].co
            _, closest_co, _, _ = bottom_inner_obj.closest_point_on_mesh(vert_co)
            min_distance = math.sqrt((vert_co[0] - closest_co[0]) ** 2 + (vert_co[1] - closest_co[1]) ** 2 + (
                    vert_co[2] - closest_co[2]) ** 2)
            if(soft_eardrum_inner_smooth < 0.5):
                # 调用平滑函数分段
                if (min_distance < 0.6):
                    soft_eardrum_inner_vert_index1.append(vert_index)
                if (min_distance > 0.4 and min_distance < 0.8):
                    soft_eardrum_inner_vert_index2.append(vert_index)
                if (min_distance < 1):
                    soft_eardrum_inner_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < (0.25 + 0.1)):
                    soft_eardrum_vert_index1.append(vert_index)
                if (min_distance > (0.25 - 0.1) and min_distance < (0.5 + 0.1)):
                    soft_eardrum_vert_index2.append(vert_index)
                if (min_distance > (0.5 - 0.1) and min_distance < (0.75 + 0.1)):
                    soft_eardrum_vert_index3.append(vert_index)
                if (min_distance > (0.75 - 0.1) and min_distance < 1):
                    soft_eardrum_vert_index4.append(vert_index)
            else:
                # 调用平滑函数分段
                if (min_distance < soft_eardrum_inner_smooth * 0.4):
                    soft_eardrum_inner_vert_index1.append(vert_index)
                if (min_distance > soft_eardrum_inner_smooth * 0.3 and min_distance < soft_eardrum_inner_smooth * 0.6):
                    soft_eardrum_inner_vert_index2.append(vert_index)
                if (min_distance < soft_eardrum_inner_smooth):
                    soft_eardrum_inner_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < soft_eardrum_inner_smooth * (0.25 + 0.1)):
                    soft_eardrum_vert_index1.append(vert_index)
                if (min_distance > soft_eardrum_inner_smooth * (0.25 - 0.1) and min_distance < soft_eardrum_inner_smooth * (0.5 + 0.1)):
                    soft_eardrum_vert_index2.append(vert_index)
                if (min_distance > soft_eardrum_inner_smooth * (0.5 - 0.1) and min_distance < soft_eardrum_inner_smooth * ( 0.75 + 0.1)):
                    soft_eardrum_vert_index3.append(vert_index)
                if (min_distance > soft_eardrum_inner_smooth * (0.75 - 0.1) and min_distance < soft_eardrum_inner_smooth):
                    soft_eardrum_vert_index4.append(vert_index)

    # 将用于计算距离的底部平面删除
    bpy.data.objects.remove(bottom_inner_obj, do_unlink=True)

    print("将顶点索引赋值给顶点组:", datetime.datetime.now())
    # 根据顶点索引将选中的顶点保存到顶点组中
    vert_index_to_vertex_group(soft_eardrum_vert_index1, "SoftEarDrumInnerVertex1")
    vert_index_to_vertex_group(soft_eardrum_vert_index2, "SoftEarDrumInnerVertex2")
    vert_index_to_vertex_group(soft_eardrum_vert_index3, "SoftEarDrumInnerVertex3")
    vert_index_to_vertex_group(soft_eardrum_vert_index4, "SoftEarDrumInnerVertex4")

    # 设置矫正平滑顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex1')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex2')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex3')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex4')
    bpy.ops.object.vertex_group_select()
    soft_eardrum_vertex = obj.vertex_groups.get("SoftEarDrumInnerVertex5")
    if (soft_eardrum_vertex != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="SoftEarDrumInnerVertex5")
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    soft_eardrum_vertex = obj.vertex_groups.new(name="SoftEarDrumInnerVertex5")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group="SoftEarDrumInnerVertex5")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')









    #外边缘平滑
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterSmooth')
    bpy.ops.object.vertex_group_select()
    if(soft_eardrum_outer_smooth != 0):
        bpy.ops.mesh.vertices_smooth(factor=1, repeat=int(soft_eardrum_outer_smooth * 2), wait_for_input=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    #内边缘平滑
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    # if (soft_eardrum_inner_smooth != 0):
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.vertices_smooth(factor=1, wait_for_input=False)
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.vertices_smooth(factor=soft_eardrum_inner_smooth/4, repeat=8, wait_for_input=False)
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.vertices_smooth(factor=soft_eardrum_inner_smooth/5, repeat=8, wait_for_input=False)
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth3')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.vertices_smooth(factor=soft_eardrum_inner_smooth/7, repeat=8, wait_for_input=False)
    bpy.ops.object.mode_set(mode='OBJECT')


    # print("创建修改器:", datetime.datetime.now())
    # modifier_name = "SoftEarDrumModifier10"
    # target_modifier = None
    # for modifier in obj.modifiers:
    #     if modifier.name == modifier_name:
    #         target_modifier = modifier
    # if (target_modifier == None):
    #     modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier10", type='SMOOTH')
    #     modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumOuterVertex10"
    #     target_modifier = modifierSoftEarDrumSmooth
    # target_modifier.factor = 0.8
    # target_modifier.iterations = int(soft_eardrum_outer_smooth * 3)
    # bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier10")
    # 创建平滑修改器,指定软耳膜外边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier4"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier4", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumOuterVertex4"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.4
    target_modifier.iterations = int(soft_eardrum_outer_smooth)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier4")

    # 创建平滑修改器,指定软耳膜外边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier3"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier3", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumOuterVertex3"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.4
    target_modifier.iterations = int(soft_eardrum_outer_smooth * 3)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier3")

    # 创建平滑修改器,指定软耳膜外边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier2"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier2", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumOuterVertex2"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.5
    target_modifier.iterations = int(soft_eardrum_outer_smooth * 5)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier2")

    # 创建平滑修改器,指定软耳膜外边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier1"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier1", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumOuterVertex1"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.6
    target_modifier.iterations = int(soft_eardrum_outer_smooth * 7)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier1")

    # 创建平滑修改器,指定软耳膜内边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier4"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier4", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumInnerVertex4"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.3
    target_modifier.iterations = int(soft_eardrum_inner_smooth)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier4")

    # 创建平滑修改器,指定软耳膜内边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier3"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier3", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumInnerVertex3"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.3
    target_modifier.iterations = int(soft_eardrum_inner_smooth * 3)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier3")

    # 创建平滑修改器,指定软耳膜内边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier2"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier2", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumInnerVertex2"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.4
    target_modifier.iterations = int(soft_eardrum_inner_smooth * 7)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier2")

    # 创建平滑修改器,指定软耳膜内边缘平滑顶点组
    modifier_name = "SoftEarDrumModifier1"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier1", type='SMOOTH')
        modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumInnerVertex1"
        target_modifier = modifierSoftEarDrumSmooth
    target_modifier.factor = 0.6
    target_modifier.iterations = int(soft_eardrum_inner_smooth * 10)
    bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier1")



    if soft_eardrum_outer_smooth != 0:
        # 创建矫正平滑修改器,指定软耳膜外边缘平滑顶点组
        modifier_name = "SoftEarDrumModifier5"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier5", type='CORRECTIVE_SMOOTH')
            modifierSoftEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
            modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumOuterVertex5"
            modifierSoftEarDrumSmooth.scale = 0
            target_modifier = modifierSoftEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = 10
        bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier5")
        print("调用smooth平滑函数:", datetime.datetime.now())
        bpy.ops.object.mode_set(mode='EDIT')
        if(soft_eardrum_outer_smooth < 0.5):
            # for i in range(7):
            #     laplacian_smooth(getSoftEarDrumOuterIndex1(), 0.4 * soft_eardrum_outer_smooth)
            # for i in range(5):
            #     laplacian_smooth(getSoftEarDrumOuterIndex2(), 0.6 * soft_eardrum_outer_smooth)
            for i in range(1):
                laplacian_smooth(getSoftEarDrumOuterIndex3(), 0.8 * soft_eardrum_outer_smooth)
        else:
            # for i in range(7):
            #     laplacian_smooth(getSoftEarDrumOuterIndex1(), 0.6)
            # for i in range(5):
            #     laplacian_smooth(getSoftEarDrumOuterIndex2(), 0.5)
            for i in range(1):
                laplacian_smooth(getSoftEarDrumOuterIndex3(), 0.4)
        bpy.ops.object.mode_set(mode='OBJECT')

    if soft_eardrum_inner_smooth != 0:
        # 创建矫正平滑修改器,指定软耳膜内边缘平滑顶点组
        modifier_name = "SoftEarDrumModifier5"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierSoftEarDrumSmooth = obj.modifiers.new(name="SoftEarDrumModifier5", type='CORRECTIVE_SMOOTH')
            modifierSoftEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
            modifierSoftEarDrumSmooth.vertex_group = "SoftEarDrumInnerVertex5"
            modifierSoftEarDrumSmooth.scale = 0
            target_modifier = modifierSoftEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = 5
        bpy.ops.object.modifier_apply(modifier="SoftEarDrumModifier5")
        print("调用smooth平滑函数:", datetime.datetime.now())
        bpy.ops.object.mode_set(mode='EDIT')
        if (soft_eardrum_inner_smooth < 0.5):
            # for i in range(7):
            #     laplacian_smooth(getSoftEarDrumInnerIndex1(), 0.4 * soft_eardrum_inner_smooth)
            # for i in range(5):
            #     laplacian_smooth(getSoftEarDrumInnerIndex2(), 0.6 * soft_eardrum_inner_smooth)
            for i in range(2):
                laplacian_smooth(getSoftEarDrumInnerIndex3(), 0.8 * soft_eardrum_inner_smooth)
        else:
            # for i in range(7):
            #     laplacian_smooth(getSoftEarDrumInnerIndex1(), 0.6)
            # for i in range(5):
            #     laplacian_smooth(getSoftEarDrumInnerIndex2(), 0.5)
            for i in range(2):
                laplacian_smooth(getSoftEarDrumInnerIndex3(), 0.4)
        bpy.ops.object.mode_set(mode='OBJECT')
    print("平滑初始化结束:", datetime.datetime.now())

    #平滑成功之后,用平滑后的物体替换左/右耳
    bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
    obj.name = bpy.context.scene.leftWindowObj






def soft_smooth_initial1():
    name = bpy.context.scene.leftWindowObj
    hardeardrum_for_smooth_obj = bpy.data.objects.get(name + "HardEarDrumForSmooth1")
    # 根据HardEarDrumForSmooth复制出一份物体用于平滑操作
    duplicate_obj = hardeardrum_for_smooth_obj.copy()
    duplicate_obj.data = hardeardrum_for_smooth_obj.data.copy()
    duplicate_obj.name = hardeardrum_for_smooth_obj.name + "copy"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.hide_set(False)
    duplicate_obj.select_set(True)
    obj = duplicate_obj

    hard_eardrum_smooth = 0
    if (name == "右耳"):
        hard_eardrum_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYi, 1)
    elif (name == "左耳"):
        hard_eardrum_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYi, 1)

    select_vert_index = []  # 保存根据底部顶点扩散得到的顶点
    hard_eardrum_vert_index1 = []  # 保存用于底部平滑的顶点
    hard_eardrum_vert_index2 = []  # 保存用于底部平滑的顶点
    hard_eardrum_vert_index3 = []  # 保存用于底部平滑的顶点
    hard_eardrum_vert_index4 = []  # 保存用于底部平滑的顶点
    global soft_eardrum_inner_vert_index1
    global soft_eardrum_inner_vert_index2
    global soft_eardrum_inner_vert_index3
    soft_eardrum_inner_vert_index1 = []  # 保存用于smooth函数边缘平滑的顶点
    soft_eardrum_inner_vert_index2 = []  # 保存用于smooth函数边缘平滑的顶点
    soft_eardrum_inner_vert_index3 = []  # 保存用于smooth函数边缘平滑的顶点

    if (obj != None):
        print("硬耳膜平滑初始化开始:", datetime.datetime.now())
        # 将底部一圈顶点复制出来用于计算最短距离
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        bottom_outer_obj = bpy.data.objects.get(name + "HardEarDrumForSmooth1copy" + ".001")
        if (name == "右耳"):
            moveToRight(bottom_outer_obj)
        elif (name == "左耳"):
            moveToLeft(bottom_outer_obj)
        #将该复制出的平面设置为当前激活物体
        obj.select_set(False)
        bottom_outer_obj.select_set(True)
        bpy.context.view_layer.objects.active = bottom_outer_obj
        #选中底面复制出的一圈顶点并挤出形成一个柱面
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -0.05), "orient_type": 'GLOBAL',"orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),})
        bpy.ops.object.mode_set(mode='OBJECT')
        #将激活物体重新设置为左右耳模型
        bottom_outer_obj.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj


        # 根据底部顶点组将扩散选中的顶点保存到数组中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
        bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.select_all(action='SELECT')
        for i in range(0,12):
            bpy.ops.mesh.select_more()
        bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.mode_set(mode='OBJECT')
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            for vert in bm.verts:
                if (vert.select == True):
                    select_vert_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()
        print("开始计算距离:", datetime.datetime.now())
        # 根据距离选中顶点
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        hard_eardrum_vert_index = []
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            for vert_index in select_vert_index:
                vert_co = bm.verts[vert_index].co
                _, closest_co, _, _ = bottom_outer_obj.closest_point_on_mesh(vert_co)
                min_distance = math.sqrt((vert_co[0] - closest_co[0]) ** 2 + (vert_co[1] - closest_co[1]) ** 2 + (
                        vert_co[2] - closest_co[2]) ** 2)
                # if(hard_eardrum_smooth < 0.5):
                if(False):
                    # 调用平滑函数分段
                    if (min_distance < 0.6):
                        soft_eardrum_inner_vert_index1.append(vert_index)
                    if (min_distance >   0.4 and min_distance <   0.8):
                        soft_eardrum_inner_vert_index2.append(vert_index)
                    if (min_distance < 1):
                        soft_eardrum_inner_vert_index3.append(vert_index)
                    # 调用平滑修改器分段
                    if (min_distance <   (0.25 + 0.1)):
                        hard_eardrum_vert_index1.append(vert_index)
                    if (min_distance >   (0.25 - 0.1) and min_distance <   (0.5 + 0.1)):
                        hard_eardrum_vert_index2.append(vert_index)
                    if (min_distance >   (0.5 - 0.1) and min_distance <   (0.75 + 0.1)):
                        hard_eardrum_vert_index3.append(vert_index)
                    if (min_distance > (0.75 - 0.1) and min_distance < 1):
                        hard_eardrum_vert_index4.append(vert_index)
                else:
                    # 调用平滑函数分段
                    if (min_distance < hard_eardrum_smooth * 0.4):
                        soft_eardrum_inner_vert_index1.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * 0.3 and min_distance < hard_eardrum_smooth * 0.6):
                        soft_eardrum_inner_vert_index2.append(vert_index)
                    if (min_distance < hard_eardrum_smooth):
                        soft_eardrum_inner_vert_index3.append(vert_index)
                    # 调用平滑修改器分段
                    if (min_distance < hard_eardrum_smooth * (0.25 + 0.1)):
                        hard_eardrum_vert_index1.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * (0.25 - 0.1) and min_distance < hard_eardrum_smooth * (0.5 + 0.1)):
                        hard_eardrum_vert_index2.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * (0.5 - 0.1) and min_distance < hard_eardrum_smooth * (0.75 + 0.1)):
                        hard_eardrum_vert_index3.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * (0.75 - 0.1) and min_distance < hard_eardrum_smooth):
                        hard_eardrum_vert_index4.append(vert_index)

        #将用于计算距离的底部平面删除
        bpy.data.objects.remove(bottom_outer_obj, do_unlink=True)

        print("将顶点索引赋值给顶点组:", datetime.datetime.now())
        #根据顶点索引将选中的顶点保存到顶点组中
        vert_index_to_vertex_group(hard_eardrum_vert_index1, "HardEarDrumInnerVertex1")
        vert_index_to_vertex_group(hard_eardrum_vert_index2, "HardEarDrumInnerVertex2")
        vert_index_to_vertex_group(hard_eardrum_vert_index3, "HardEarDrumInnerVertex3")
        vert_index_to_vertex_group(hard_eardrum_vert_index4, "HardEarDrumInnerVertex4")

        # 设置矫正平滑顶点组
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumInnerVertex1')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumInnerVertex2')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumInnerVertex3')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumInnerVertex4')
        bpy.ops.object.vertex_group_select()
        hard_eardrum_vertex = obj.vertex_groups.get("HardEarDrumInnerVertex5")
        if (hard_eardrum_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="HardEarDrumInnerVertex5")
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        hard_eardrum_vertex = obj.vertex_groups.new(name="HardEarDrumInnerVertex5")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="HardEarDrumInnerVertex5")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        print("创建修改器:", datetime.datetime.now())

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier4"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier4", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumInnerVertex4"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier4")

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier3"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier3", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumInnerVertex3"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth * 3)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier3")

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier2"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier2", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumInnerVertex2"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth * 7)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier2")

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier1"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier1", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumInnerVertex1"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth * 10)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier1")

        if hard_eardrum_smooth != 0:
            # 创建矫正平滑修改器,指定硬耳膜平滑顶点组
            modifier_name = "HardEarDrumModifier5"
            target_modifier = None
            for modifier in obj.modifiers:
                if modifier.name == modifier_name:
                    target_modifier = modifier
            if (target_modifier == None):
                modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier5", type='CORRECTIVE_SMOOTH')
                modifierHardEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
                modifierHardEarDrumSmooth.vertex_group = "HardEarDrumInnerVertex5"
                modifierHardEarDrumSmooth.scale = 0
                target_modifier = modifierHardEarDrumSmooth
            target_modifier.factor = 0.5
            target_modifier.iterations = 5
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier5")
            print("调用smooth平滑函数:", datetime.datetime.now())
            bpy.ops.object.mode_set(mode='EDIT')
            if(hard_eardrum_smooth < 1):
                for i in range(7):
                    laplacian_smooth(getSoftEarDrumInnerIndex1(), 0.4 * hard_eardrum_smooth)
                for i in range(5):
                    laplacian_smooth(getSoftEarDrumInnerIndex2(), 0.6 * hard_eardrum_smooth)
                for i in range(2):
                    laplacian_smooth(getSoftEarDrumInnerIndex3(), 0.8 * hard_eardrum_smooth)
            else:
                for i in range(7):
                    laplacian_smooth(getSoftEarDrumInnerIndex1(), 0.3)
                for i in range(5):
                    laplacian_smooth(getSoftEarDrumInnerIndex2(), 0.3)
                for i in range(2):
                    laplacian_smooth(getSoftEarDrumInnerIndex3(), 0.3)
            bpy.ops.object.mode_set(mode='OBJECT')
        print("平滑初始化结束:", datetime.datetime.now())

        #平滑成功之后,用平滑后的物体替换左/右耳
        bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
        obj.name = bpy.context.scene.leftWindowObj

def re_smooth(origin_obj_name, update_retopo_obj_name, retopo_obj_name, retopo_border_name, width):
    '''
    origin_obj_name: 需要重新重拓扑还原用物体名称
    update_retopo_obj_name: 需要更新的重拓扑后的物体名称
    retopo_obj_name: 不需要重拓扑的物体
    retopo_border_name: 重拓扑物体的边缘顶点组名称
    width: 重拓扑物体的边缘宽度
    '''
    origin_obj = bpy.data.objects[origin_obj_name]
    retopo_obj = bpy.data.objects[retopo_obj_name]
    update_retopo_obj = bpy.data.objects[update_retopo_obj_name]

    # 删除右耳物体与需要更新的重拓扑物体
    bpy.data.objects.remove(bpy.data.objects["右耳"], do_unlink=True)
    bpy.data.objects.remove(update_retopo_obj, do_unlink=True)

    # 复制一份origin_obj并重拓扑
    new_origin_obj = origin_obj.copy()
    new_origin_obj.data = origin_obj.data.copy()
    new_origin_obj.name = "右耳"
    bpy.context.collection.objects.link(new_origin_obj)
    new_origin_obj.hide_set(False)
    moveToRight(new_origin_obj)

    bpy.ops.object.select_all(action='DESELECT')
    new_origin_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_origin_obj
    if width != 0:
        soft_retopo_offset_cut(new_origin_obj.name, retopo_border_name, width)
    # 更新重拓扑物体
    new_retopo_obj = new_origin_obj.copy()
    new_retopo_obj.data = new_origin_obj.data.copy()
    new_retopo_obj.name = update_retopo_obj_name
    bpy.context.collection.objects.link(new_retopo_obj)
    new_retopo_obj.hide_set(True)
    moveToRight(new_retopo_obj)

    # 复制不需要重拓扑的物体，进行桥接
    new_retopo_obj = retopo_obj.copy()
    new_retopo_obj.data = retopo_obj.data.copy()
    bpy.context.collection.objects.link(new_retopo_obj)
    new_retopo_obj.hide_set(False)

    # 桥接
    bpy.ops.object.select_all(action='DESELECT')
    new_retopo_obj.select_set(True)
    new_origin_obj.select_set(True)
    bpy.context.view_layer.objects.active = new_origin_obj
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bevel_soft_border()


def bevel_soft_border():
    outer_offset = bpy.context.scene.waiBianYuanSheRuPianYiR
    inner_offset = bpy.context.scene.neiBianYuanSheRuPianYiL

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    # 分别对内外倒角进行重拓扑
    if outer_offset != 0:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=95, segments=16, affect='EDGES')
        # 更新顶点组
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove_from()
        for _ in range(int(16 / 2)):  # 16是bevel的segments
            bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_assign()

    # 删除内外壁之间的面，重新桥接
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    if inner_offset != 0:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=95, segments=16, affect='EDGES')
        # 更新顶点组
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove_from()
        for _ in range(int(16 / 2)):  # 16是bevel的segments
            bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    # 平滑着色
    bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=3.14159)



def soft_retopo_offset_cut(obj_name, border_vert_group_name, width):
    main_obj = bpy.data.objects[obj_name]

    bpy.ops.object.select_all(action='DESELECT')
    main_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    main_obj.vertex_groups.new(name="all")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_select()

    bpy.ops.softeardrum.smooth(width=width, center_border_group_name=border_vert_group_name)


def soft_eardrum():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        kongqiangeunm = bpy.context.scene.KongQiangMianBanTypeEnumR
        shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR
    elif name == '左耳':
        kongqiangeunm = bpy.context.scene.KongQiangMianBanTypeEnumL
        shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanL
    if kongqiangeunm == 'OP1' and bpy.data.objects.get(name + "Torus") is None:
        draw_cut_plane(name)                         #初始化圆圈与圆环
    if shangbuqiege and bpy.data.objects.get(name + "UpperTorus") is None:
        draw_cut_plane_upper(name)
    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.ops.object.softeardrumcirclecut('INVOKE_DEFAULT')
    fill()


# 重置回到底部切割完成
def reset_to_after_cut():
    name = bpy.context.scene.leftWindowObj
    need_to_delete_model_name_list = [name, name + "FillPlane", name + "ForGetFillPlane", name + "Inner", "RetopoPart",
                                      name + "OuterOrigin", name + "InnerOrigin", name + "OuterRetopo", name + "InnerRetopo"]
    for obj in bpy.context.view_layer.objects:
        if obj.name in need_to_delete_model_name_list:
            bpy.data.objects.remove(obj, do_unlink=True)
    obj = bpy.data.objects[name + "huanqiecompare"]
    obj.name = name
    obj.hide_set(False)
    # 重新获取平面并且完成切割填充
    copyModel(name)
    bpy.context.view_layer.objects.active = bpy.data.objects[name]


# 重置回到挖洞完成
def reset_to_after_dig():
    name = bpy.context.scene.leftWindowObj
    need_to_delete_model_name_list = [name, name + "FillPlane", name + "ForGetFillPlane", name + "Inner", "RetopoPart",
                                      name + "OuterOrigin", name + "InnerOrigin", name + "OuterRetopo", name + "InnerRetopo"]
    for obj in bpy.context.view_layer.objects:
        if obj.name in need_to_delete_model_name_list:
            bpy.data.objects.remove(obj, do_unlink=True)
    obj = bpy.data.objects[name + "OriginForDigHole"]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.scene.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(False)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    bpy.context.view_layer.objects.active = bpy.data.objects[name]


# 重置回到实体化完成
def reset_to_after_thickness():
    name = bpy.context.scene.leftWindowObj
    need_to_delete_model_name_list = [name, name + "FillPlane", name + "ForGetFillPlane", name + "Inner", "RetopoPart",
                                      name + "OuterRetopo", name + "InnerRetopo"]
    for obj in bpy.context.view_layer.objects:
        if obj.name in need_to_delete_model_name_list:
            bpy.data.objects.remove(obj, do_unlink=True)
    obj = bpy.data.objects[name + "OuterOrigin"]
    obj.name = name
    obj.hide_set(False)
    # 重新获取平面并且完成切割填充
    outer_obj_copy = obj.copy()
    outer_obj_copy.data = obj.data.copy()
    outer_obj_copy.name = name + "OuterOrigin"
    bpy.context.collection.objects.link(outer_obj_copy)
    outer_obj_copy.hide_set(True)
    if name == '右耳':
        moveToRight(outer_obj_copy)
    else:
        moveToLeft(outer_obj_copy)


def reset_and_refill():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        neibianjixian = bpy.context.scene.neiBianJiXianR
    elif name == '左耳':
        neibianjixian = bpy.context.scene.neiBianJiXianL
    try:
        if neibianjixian:
            reset_to_after_dig()
        else:
            # 首先reset到切割完成
            reset_to_after_cut()
        fill()
        if name == "右耳":
            bpy.data.objects[name].data.materials.clear()
            bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowR"])
        elif name == "左耳":
            bpy.data.objects[name].data.materials.clear()
            bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowL"])

    except:
        # 重新填充失败时将模型变成金色
        if neibianjixian:
            reset_to_after_dig()
        else:
            reset_to_after_cut()
        name = bpy.context.scene.leftWindowObj
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


def refill_after_cavity_plane_change():
    try:
        # 首先reset到实体化完成
        reset_to_after_thickness()
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name + "InnerOrigin"]
        # 重新获取内壁并且完成切割填充
        inner_obj = obj.copy()
        inner_obj.data = obj.data.copy()
        inner_obj.name = name + "Inner"
        bpy.context.collection.objects.link(inner_obj)
        inner_obj.hide_set(False)
        if name == '右耳':
            shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR
            moveToRight(inner_obj)
        else:
            shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanL
            moveToLeft(inner_obj)

        if bpy.data.objects.get(name + "OuterSmooth") is not None and shangbuqiege:
            obj = bpy.data.objects[name + "OuterSmooth"]
            outer_obj = obj.copy()
            outer_obj.data = obj.data.copy()
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
            outer_obj.name = name
            bpy.context.collection.objects.link(outer_obj)
            outer_obj.hide_set(False)
            if name == '右耳':
                moveToRight(outer_obj)
            else:
                moveToLeft(outer_obj)
        else:
            outer_obj = bpy.data.objects[name]

        soft_eardrum_inner_cut(inner_obj)
        inner_obj = border_smooth()
        if inner_obj is not None:
            join_outer_and_inner(inner_obj, outer_obj)

            # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
            name = bpy.context.scene.leftWindowObj
            obj = bpy.data.objects.get(name)
            soft_eardrum_smooth_name = name + "SoftEarDrumForSmooth"
            softeardrum_for_smooth_obj = bpy.data.objects.get(soft_eardrum_smooth_name)
            if (softeardrum_for_smooth_obj != None):
                bpy.data.objects.remove(softeardrum_for_smooth_obj, do_unlink=True)
            softeardrum_for_smooth_obj = obj.copy()
            softeardrum_for_smooth_obj.data = obj.data.copy()
            softeardrum_for_smooth_obj.name = obj.name + "SoftEarDrumForSmooth"
            softeardrum_for_smooth_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(softeardrum_for_smooth_obj)
            if name == '右耳':
                moveToRight(softeardrum_for_smooth_obj)
            else:
                moveToLeft(softeardrum_for_smooth_obj)
            softeardrum_for_smooth_obj.hide_set(True)

            # 软耳模边缘平滑
            soft_extrude_smooth_initial()

    except:
        name = bpy.context.scene.leftWindowObj
        if bpy.data.objects.get(name + "Inner") is not None:
            bpy.data.objects.remove(bpy.data.objects.get(name + "Inner"), do_unlink=True)
        if bpy.data.objects.get(name + "OuterOrigin") is not None:
            reset_to_after_thickness()
        else:
            if name == '右耳':
                neibianjixian = bpy.context.scene.neiBianJiXianR
            elif name == '左耳':
                neibianjixian = bpy.context.scene.neiBianJiXianL
            if neibianjixian:
                reset_to_after_dig()
            else:
                # 首先reset到切割完成
                reset_to_after_cut()
        # if name == '右耳':
        #     neibianjixian = bpy.context.scene.neiBianJiXianR
        # elif name == '左耳':
        #     neibianjixian = bpy.context.scene.neiBianJiXianL
        # if neibianjixian:
        #     reset_to_after_dig()
        # else:
        #     reset_to_after_cut()
        # if name == '右耳':
        #     shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR
        # elif name == '左耳':
        #     shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanL
        #
        # obj = bpy.data.objects[name]
        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = obj
        # obj.select_set(True)
        #
        # # 减少顶点数量
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # number = 0
        # for o in bpy.data.objects:
        #     if re.match(name + 'HoleBorderCurve', o.name) != None:
        #         number += 1
        # if number >= 1:
        #     for i in range(1, number + 1):
        #         bpy.ops.object.vertex_group_set_active(group='HoleBorderVertex' + str(i))
        #         bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.remove_doubles(threshold=0.5)
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.mode_set(mode='OBJECT')
        # if shangbuqiege:
        #     soft_eardrum_outer_cut(obj)
        # soft_eardrum_thickness(obj)

        obj = bpy.data.objects[name]
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        obj.data.materials.clear()
        obj.data.materials.append(bpy.data.materials["error_yellow"])


def refill_after_cavity_smooth():
    try:
        smooth__obj = border_smooth()
        if smooth__obj is not None:
            name = bpy.context.scene.leftWindowObj
            if name == '右耳':
                shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR
            else:
                shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR

            if bpy.data.objects.get(name + "OuterSmooth") is not None and shangbuqiege:
                obj = bpy.data.objects[name + "OuterSmooth"]
                outer_obj = obj.copy()
                outer_obj.data = obj.data.copy()
                bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
                outer_obj.name = name
                bpy.context.collection.objects.link(outer_obj)
                outer_obj.hide_set(False)
                if name == '右耳':
                    moveToRight(outer_obj)
                else:
                    moveToLeft(outer_obj)
            else:
                obj = bpy.data.objects[name + "OuterOrigin"]
                outer_obj = obj.copy()
                outer_obj.data = obj.data.copy()
                bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
                outer_obj.name = name
                bpy.context.collection.objects.link(outer_obj)
                outer_obj.hide_set(False)
                if name == '右耳':
                    moveToRight(outer_obj)
                else:
                    moveToLeft(outer_obj)

            if bpy.data.objects.get(name + "Inner") != None:
                inner_obj = bpy.data.objects.get(name + "Inner")
                join_outer_and_inner(inner_obj, outer_obj)

                # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
                name = bpy.context.scene.leftWindowObj
                obj = bpy.data.objects.get(name)
                soft_eardrum_smooth_name = name + "SoftEarDrumForSmooth"
                softeardrum_for_smooth_obj = bpy.data.objects.get(soft_eardrum_smooth_name)
                if (softeardrum_for_smooth_obj != None):
                    bpy.data.objects.remove(softeardrum_for_smooth_obj, do_unlink=True)
                softeardrum_for_smooth_obj = obj.copy()
                softeardrum_for_smooth_obj.data = obj.data.copy()
                softeardrum_for_smooth_obj.name = obj.name + "SoftEarDrumForSmooth"
                softeardrum_for_smooth_obj.animation_data_clear()
                bpy.context.scene.collection.objects.link(softeardrum_for_smooth_obj)
                if name == '右耳':
                    moveToRight(softeardrum_for_smooth_obj)
                else:
                    moveToLeft(softeardrum_for_smooth_obj)
                softeardrum_for_smooth_obj.hide_set(True)

                # 软耳模边缘平滑
                soft_extrude_smooth_initial()

    except:
        reset_to_after_thickness()
        name = bpy.context.scene.leftWindowObj
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


def refill_after_upper_smooth():
    try:
        smooth_upper_obj = border_smooth_upper()
        if smooth_upper_obj is not None:
            name = bpy.context.scene.leftWindowObj
            if name == '右耳':
                kongqiangeunm = bpy.context.scene.KongQiangMianBanTypeEnumR
            else:
                kongqiangeunm = bpy.context.scene.KongQiangMianBanTypeEnumL

            if bpy.data.objects.get(name + "InnerSmooth") is not None and kongqiangeunm == 'OP1':
                obj = bpy.data.objects[name + "InnerSmooth"]
                inner_obj = obj.copy()
                inner_obj.data = obj.data.copy()
                inner_obj.name = name + "Inner"
                bpy.context.collection.objects.link(inner_obj)
                inner_obj.hide_set(False)
                if name == '右耳':
                    moveToRight(inner_obj)
                else:
                    moveToLeft(inner_obj)
            else:
                obj = bpy.data.objects[name + "InnerOrigin"]
                inner_obj = obj.copy()
                inner_obj.data = obj.data.copy()
                inner_obj.name = name + "Inner"
                bpy.context.collection.objects.link(inner_obj)
                inner_obj.hide_set(False)
                if name == '右耳':
                    moveToRight(inner_obj)
                else:
                    moveToLeft(inner_obj)

            if bpy.data.objects.get(name) is not None:
                outer_obj = bpy.data.objects.get(name)
                join_outer_and_inner(inner_obj, outer_obj)

                # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
                name = bpy.context.scene.leftWindowObj
                obj = bpy.data.objects.get(name)
                soft_eardrum_smooth_name = name + "SoftEarDrumForSmooth"
                softeardrum_for_smooth_obj = bpy.data.objects.get(soft_eardrum_smooth_name)
                if (softeardrum_for_smooth_obj != None):
                    bpy.data.objects.remove(softeardrum_for_smooth_obj, do_unlink=True)
                softeardrum_for_smooth_obj = obj.copy()
                softeardrum_for_smooth_obj.data = obj.data.copy()
                softeardrum_for_smooth_obj.name = obj.name + "SoftEarDrumForSmooth"
                softeardrum_for_smooth_obj.animation_data_clear()
                bpy.context.scene.collection.objects.link(softeardrum_for_smooth_obj)
                if name == '右耳':
                    moveToRight(softeardrum_for_smooth_obj)
                else:
                    moveToLeft(softeardrum_for_smooth_obj)
                softeardrum_for_smooth_obj.hide_set(True)

                # 软耳模边缘平滑
                soft_extrude_smooth_initial()

    except:
        reset_to_after_thickness()
        name = bpy.context.scene.leftWindowObj
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


def soft_eardrum_smooth_initial():

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    cur_obj_name = "右耳"
    cur_obj = bpy.data.objects.get(cur_obj_name)

    if (cur_obj != None):
        soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
        soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
        if(soft_eardrum_bottom_outer_vertex != None and soft_eardrum_bottom_inner_vertex != None):
            bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerVertex")
            if (soft_eardrum_outer_vertex == None):
                soft_eardrum_outer_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumInnerVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.loop_to_region()
            bpy.ops.mesh.loop_to_region(select_bigger=False)
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterVertex")
            if (soft_eardrum_inner_vertex == None):
                soft_eardrum_inner_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumOuterVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')



            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.subdivide()
            bpy.ops.mesh.subdivide(number_cuts=2)
            bpy.ops.mesh.remove_doubles(threshold=0.15)
            bpy.ops.object.mode_set(mode='OBJECT')

            bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
            bottom_innner_border_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
            if (bottom_outer_border_vertex != None and bottom_innner_border_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.mode_set(mode='OBJECT')

                # 将选中的顶点范围扩大
                bpy.ops.object.mode_set(mode='EDIT')
                for i in range(6):
                    bpy.ops.mesh.select_more()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='OBJECT')
                soft_eardrum_select_vertex = cur_obj.vertex_groups.get("SoftEarDrumSelectVertex")
                if (soft_eardrum_select_vertex == None):
                    soft_eardrum_select_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumSelectVertex")
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                # 添加平滑修改器
                modifier_name = "SoftEarDrumOuterSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "BottomOuterBorderVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumOuterSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].factor = 1.6
                bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].iterations = 2

                modifier_name = "SoftEarDrumInnerSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "BottomInnerBorderVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumInnerSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].factor = 1.6
                bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].iterations = 2

                modifier_name = "SoftEarDrumAllInnerSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "SoftEarDrumInnerVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumAllInnerSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumAllInnerSmoothModifier"].factor = 0.8
                bpy.context.object.modifiers["SoftEarDrumAllInnerSmoothModifier"].iterations = 16


finish = True  # 用于控制modal的运行, True表示modal暂停

old_radius = 8.0
old_radius_upper = 8.0
now_radius = 0
now_radius_upper = 8.0
scale_ratio = 1
zmax = 0
zmin = 0
# 圆环是否在物体上
on_obj = True
# 切割时的圆环信息（右耳）
right_last_loc = None
right_last_radius = None
right_last_ratation = None
right_last_loc_upper = None
right_last_radius_upper = None
right_last_ratation_upper = None
# 切割时的圆环信息 （左耳）
left_last_loc = None
left_last_radius = None
left_last_ratation = None
left_last_loc_upper = None
left_last_radius_upper = None
left_last_ratation_upper = None

# soft_modal_start = False

operator_obj = ''  # 当前操作的物体是左耳还是右耳
operator_torus_obj = None
operator_circle_obj = None

mouse_loc = None  # 记录鼠标在圆环上的位置


# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    global mouse_loc, operator_obj, operator_torus_obj, operator_circle_obj

    torus_name = [operator_obj + 'Torus', operator_obj + 'UpperTorus']
    # active_obj = bpy.data.objects[operator_obj+'Torus']
    is_on_object = False  # 初始化变量
    cast_loc = None

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    if event.mouse_region_x > region1.width:
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y))
    else:
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    if event.mouse_region_x > region1.width:
        region = region2
        space = area.spaces.active

    ray_dir = view3d_utils.region_2d_to_vector_3d(
        region,
        space.region_3d,
        mv
    )
    ray_orig = view3d_utils.region_2d_to_origin_3d(
        region,
        space.region_3d,
        mv
    )

    start = ray_orig
    end = ray_orig + ray_dir

    for obj_name in torus_name:
        active_obj = bpy.data.objects.get(obj_name)
        if active_obj is None:
            continue
        # 确定光线和对象的相交
        mwi = active_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if active_obj.type == 'MESH':
            if (active_obj.mode == 'OBJECT'):
                mesh = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                loc, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    co = loc
                    mouse_loc = loc
                    # print('loc',loc)
                    # if(co.x > 0 and co.y >0):
                    #     print('右上')
                    # elif(co.x < 0 and co.y > 0):
                    #     print('左上')
                    # elif(co.x < 0 and co.y < 0):
                    #     print('左下')
                    # elif(co.x > 0 and co.y < 0):
                    #     print('右下')
                    is_on_object = True  # 如果发生交叉，将变量设为True
                    operator_torus_obj = obj_name
                    if operator_torus_obj == operator_obj + 'Torus':
                        operator_circle_obj = operator_obj + 'Circle'
                    else:
                        operator_circle_obj = operator_obj + 'UpperCircle'
    return is_on_object


# 复制初始模型，并赋予透明材质
def copyModel(obj_name):
    # 获取当前选中的物体
    obj_ori = bpy.data.objects[obj_name]
    # 复制物体用于对比突出加厚的预览效果
    obj_all = bpy.data.objects
    copy_compare = True  # 判断是否复制当前物体作为透明的参照,不存在参照物体时默认会复制一份新的参照物体
    for selected_obj in obj_all:
        if (selected_obj.name == obj_name + "huanqiecompare"):
            copy_compare = False  # 当存在参照物体时便不再复制新的物体
            # break
    if (copy_compare):  # 复制一份物体作为透明的参照
        active_obj = obj_ori
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.name = active_obj.name + "huanqiecompare"
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if obj_name == '右耳':
            moveToRight(duplicate_obj)
        elif obj_name == '左耳':
            moveToLeft(duplicate_obj)


# 获取模型的Z坐标范围
def getModelZ(obj_name):
    global zmax, zmin
    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects[obj_name]
    # bpy.context.view_layer.objects.active = obj_main
    # bpy.ops.object.mode_set(mode='EDIT')
    # bm = bmesh.from_edit_mesh(obj_main.data)
    vertices = obj_main.data.vertices

    # 初始化最大距离为负无穷大
    z_max = float('-inf')
    z_min = float('inf')

    # 遍历的每个顶点并计算距离
    for vertex in vertices:
        z_max = max(z_max, vertex.co.z)
        z_min = min(z_min, vertex.co.z)

    zmax = z_max
    zmin = z_min
    # 切换回对象模式
    # bpy.ops.object.mode_set(mode='OBJECT')


# 新建与RGB颜色相同的材质
def newColor(id, r, g, b, is_transparency, transparency_degree):
    mat = newMaterial(id)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.inputs[0].default_value = (r, g, b, 1)
    shader.inputs[6].default_value = 0.46
    shader.inputs[7].default_value = 0
    shader.inputs[9].default_value = 0.472
    shader.inputs[14].default_value = 1
    shader.inputs[15].default_value = 0.105
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


# 初始化圆环颜色
def initialTorusColor():
    red_material = newColor("red", 1, 0, 0, 0, 1)


def reset_circle_info():
    global right_last_loc, left_last_loc
    global right_last_loc_upper, left_last_loc_upper
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        right_last_loc = None
        right_last_loc_upper = None
    elif name == "左耳":
        left_last_loc = None
        left_last_loc_upper = None


def draw_cut_plane(obj_name):
    '''
    初始化圆圈与圆环
    '''
    global old_radius, scale_ratio, now_radius
    global right_last_loc, right_last_radius, right_last_ratation, left_last_loc, left_last_radius, left_last_ratation
    global zmax, zmin, operator_obj

    obj_main = bpy.data.objects[obj_name]
    operator_obj = obj_name

    if obj_name == '右耳':
        last_loc = right_last_loc
        last_ratation = right_last_ratation
        last_radius = right_last_radius
    elif obj_name == '左耳':
        last_loc = left_last_loc
        last_ratation = left_last_ratation
        last_radius = left_last_radius

    # copyModel(obj_name)  # 复制一份底部切割完成后的物体用于回退
    getModelZ(obj_name)

    initZ = round(zmax * 0.5, 2)

    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)
    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
    center = (0, 0, 0)
    if selected_verts:
        # 计算平面的几何中心
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        # 输出几何中心坐标
        print("Geometry Center:", center)

    # 初始化最大距离为负无穷大
    max_distance = float('-inf')
    min_distance = float('inf')
    # 遍历的每个顶点并计算距离
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)
        min_distance = min(min_distance, distance)
    # old_radius = max_distance / cos(math.radians(30))
    # old_radius = 12
    old_radius = round(max_distance, 2) + 0.5
    now_radius = round(min_distance, 2)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    # print('当前位置', last_loc)

    initX = center.x
    initY = center.y
    # if obj_name == '左耳':
    #     initY = -initY

    # 正常初始化
    if last_loc == None:
        print('正常初始化')
        # 大圆环
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            # location=((-10.4251, 2.3513, 6.7393))
            location=(initX, initY, initZ)

            ,
            rotation=(0.0, 0.0, 0.0)
            # rotation=(-0.1633, 0.1414, -0.1150)
            , scale=(
                1.0, 1.0, 1.0))

        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD',
                                         # location=((-10.4251, 2.3513, 6.7393))
                                         location=(initX, initY, initZ)
                                         ,
                                         rotation=(0.0, 0, 0)
                                         # rotation=(-0.1633, 0.1414, -0.1150)
                                         , major_segments=80, minor_segments=80, major_radius=old_radius,
                                         minor_radius=0.4)



    else:
        print('切割后初始化')
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(
                last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                1.0, 1.0, 1.0))
        # 初始化环体       last_loc   last_ratation   last_radius
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
            last_ratation[0], last_ratation[1], last_ratation[2]), major_segments=80, minor_segments=80,
                                         major_radius=last_radius, minor_radius=0.4)
        old_radius = last_radius

    obj = bpy.context.active_object
    obj.name = obj_name + 'Torus'
    if obj_name == '右耳':
        moveToRight(obj)
    elif obj_name == '左耳':
        moveToLeft(obj)
    # 环体颜色
    initialTorusColor()
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['red'])
    # 选择圆环
    obj_circle = bpy.data.objects['Circle']
    obj_circle.name = obj_name + 'Circle'
    if obj_name == '右耳':
        moveToRight(obj_circle)
    elif obj_name == '左耳':
        moveToLeft(obj_circle)
    # 物体位于右边窗口
    if obj_name == bpy.context.scene.rightWindowObj:
        override2 = getOverride2()
        with bpy.context.temp_override(**override2):
            # 进入编辑模式
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_circle
            obj_circle.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            # 翻转圆环法线
            bpy.ops.mesh.flip_normals(only_clnors=False)
            # 隐藏圆环
            obj_circle.hide_set(True)
            # 返回对象模式
            bpy.ops.object.mode_set(mode='OBJECT')
    else:
        # 进入编辑模式
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_circle
        obj_circle.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # 翻转圆环法线
        bpy.ops.mesh.flip_normals(only_clnors=False)
        # 隐藏圆环
        obj_circle.hide_set(True)
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')


def draw_cut_plane_upper(obj_name):
    '''
    初始化上部切割面板的圆圈与圆环
    '''
    global old_radius_upper, scale_ratio, now_radius_upper
    global right_last_loc_upper, right_last_radius_upper, right_last_ratation_upper, left_last_loc_upper, left_last_radius_upper, left_last_ratation_upper
    global zmax, zmin, operator_obj

    obj_main = bpy.data.objects[obj_name]
    operator_obj = obj_name

    if obj_name == '右耳':
        last_loc = right_last_loc_upper
        last_ratation = right_last_ratation_upper
        last_radius = right_last_radius_upper
    elif obj_name == '左耳':
        last_loc = left_last_loc_upper
        last_ratation = left_last_ratation_upper
        last_radius = left_last_radius_upper

    # copyModel(obj_name)  # 复制一份底部切割完成后的物体用于回退
    getModelZ(obj_name)

    initZ = round(zmax * 0.95, 2)

    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)
    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
    center = (0, 0, 0)
    if selected_verts:
        # 计算平面的几何中心
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        # 输出几何中心坐标
        print("Geometry Center:", center)

    # 初始化最大距离为负无穷大
    max_distance = float('-inf')
    min_distance = float('inf')
    # 遍历的每个顶点并计算距离
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)
        min_distance = min(min_distance, distance)
    # old_radius_upper = max_distance / cos(math.radians(30))
    # old_radius_upper = 12
    old_radius_upper = round(max_distance, 2) + 0.5
    now_radius_upper = round(min_distance, 2)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    # print('当前位置', last_loc)

    initX = center.x
    initY = center.y
    # if obj_name == '左耳':
    #     initY = -initY

    # 正常初始化
    if last_loc == None:
        print('正常初始化')
        # 大圆环
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            # location=((-10.4251, 2.3513, 6.7393))
            location=(initX, initY, initZ)

            ,
            rotation=(0.0, 0.0, 0.0)
            # rotation=(-0.1633, 0.1414, -0.1150)
            , scale=(
                1.0, 1.0, 1.0))

        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD',
                                         # location=((-10.4251, 2.3513, 6.7393))
                                         location=(initX, initY, initZ)
                                         ,
                                         rotation=(0.0, 0, 0)
                                         # rotation=(-0.1633, 0.1414, -0.1150)
                                         , major_segments=80, minor_segments=80, major_radius=old_radius_upper,
                                         minor_radius=0.4)



    else:
        print('切割后初始化')
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(
                last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                1.0, 1.0, 1.0))
        # 初始化环体       last_loc   last_ratation   last_radius
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
            last_ratation[0], last_ratation[1], last_ratation[2]), major_segments=80, minor_segments=80,
                                         major_radius=last_radius, minor_radius=0.4)
        old_radius_upper = last_radius

    obj = bpy.context.active_object
    obj.name = obj_name + 'UpperTorus'
    if obj_name == '右耳':
        moveToRight(obj)
    elif obj_name == '左耳':
        moveToLeft(obj)
    # 环体颜色
    initialTorusColor()
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['red'])
    # 选择圆环
    obj_circle = bpy.data.objects['Circle']
    obj_circle.name = obj_name + 'UpperCircle'
    if obj_name == '右耳':
        moveToRight(obj_circle)
    elif obj_name == '左耳':
        moveToLeft(obj_circle)
    # 物体位于右边窗口
    if obj_name == bpy.context.scene.rightWindowObj:
        override2 = getOverride2()
        with bpy.context.temp_override(**override2):
            # 进入编辑模式
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_circle
            obj_circle.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            # 翻转圆环法线
            bpy.ops.mesh.flip_normals(only_clnors=False)
            # 隐藏圆环
            obj_circle.hide_set(True)
            # 返回对象模式
            bpy.ops.object.mode_set(mode='OBJECT')
    else:
        # 进入编辑模式
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_circle
        obj_circle.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # 翻转圆环法线
        bpy.ops.mesh.flip_normals(only_clnors=False)
        # 隐藏圆环
        obj_circle.hide_set(True)
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')


# 获取截面半径
def getRadius(op):
    global old_radius, scale_ratio, now_radius, on_obj, operator_obj, mouse_loc

    # 翻转圆环法线
    obj_torus = bpy.data.objects[operator_obj + 'Torus']
    obj_circle = bpy.data.objects[operator_obj + 'Circle']
    active_obj = bpy.data.objects[operator_obj + 'huanqiecompare']
    for selected_obj in bpy.data.objects:
        if (selected_obj.name == operator_obj + "huanqiecompareintersect"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = active_obj.name + "intersect"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)
    if operator_obj == '右耳':
        moveToRight(duplicate_obj)
    elif operator_obj == '左耳':
        moveToLeft(duplicate_obj)

    bpy.context.view_layer.objects.active = duplicate_obj
    # 添加修改器,获取交面

    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate_obj.modifiers.new(name="Boolean Intersect", type='BOOLEAN')
    duplicate_obj.modifiers[0].operation = 'INTERSECT'
    duplicate_obj.modifiers[0].object = obj_circle
    duplicate_obj.modifiers[0].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect', single_user=True)

    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    rbm = bmesh.from_edit_mesh(duplicate_obj.data)
    # rbm = bmesh.new()
    # rbm.from_mesh(duplicate_obj.data)

    # 获取截面上的点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()
    plane_verts = [v for v in rbm.verts if distance_to_plane(plane_normal, plane_point, v.co) == 0]
    # print(len(plane_verts))

    # 圆环不在物体上
    if (len(plane_verts) == 0):
        on_obj = False
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        on_obj = True

    # print('圆环是否在物体上',on_obj)

    if on_obj:
        for v in plane_verts:
            v.select = True
        for edge in rbm.edges:
            if edge.verts[0].select and edge.verts[1].select:
                edge.select_set(True)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.select_get():
                if obj.name != duplicate_obj.name:
                    temp_plane_obj = obj
        bpy.context.view_layer.objects.active = temp_plane_obj
        duplicate_obj.select_set(False)
        temp_plane_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(temp_plane_obj.data)
        verts = [v for v in bm.verts]
        verts[0].select = True
        bpy.ops.mesh.select_linked(delimit=set())
        select_verts = [v for v in bm.verts if v.select]
        unselect_verts = [v for v in bm.verts if not v.select]

        if len(select_verts) == len(verts):
            # print("选中的顶点数和平面上的顶点数一致")
            center = sum((v.co for v in verts), Vector()) / len(verts)

            # 初始化最大距离为负无穷大
            max_distance = float('-inf')
            min_distance = float('inf')

            # 遍历的每个顶点并计算距离
            for vertex in verts:
                distance = (vertex.co - obj_torus.location).length
                max_distance = max(max_distance, distance)
                min_distance = min(min_distance, distance)

            radius = round(max_distance, 2)
            radius = radius + 0.5
            # print('最大半径',radius)
            # print('最小半径',min_distance)
            now_radius = round(min_distance, 2)

        else:
            # print("选中的顶点数和平面上的顶点数不一致")
            center1 = sum((v.co for v in select_verts), Vector()) / len(select_verts)
            center2 = sum((v.co for v in unselect_verts), Vector()) / len(unselect_verts)
            if (mouse_loc - center1).length < (mouse_loc - center2).length:
                center = center1
                verts = select_verts
            else:
                center = center2
                verts = unselect_verts

            # 初始化最大距离为负无穷大
            max_distance = float('-inf')
            min_distance = float('inf')

            # 遍历的每个顶点并计算距离
            for vertex in verts:
                distance = (vertex.co - obj_torus.location).length
                max_distance = max(max_distance, distance)
                min_distance = min(min_distance, distance)

            radius = round(max_distance, 2)
            radius = radius + 0.5
            # print('最大半径',radius)
            # print('最小半径',min_distance)
            now_radius = round(min_distance, 2)

        bpy.ops.object.mode_set(mode='OBJECT')
        # 删除复制的物体
        bpy.data.objects.remove(duplicate_obj, do_unlink=True)
        bpy.data.objects.remove(temp_plane_obj, do_unlink=True)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_torus
        obj_torus.select_set(True)
        # 缩放圆环及调整位置
        if op == 'move':
            obj_torus.location = center
            obj_circle.location = center
        scale_ratio = round(radius / old_radius, 3)
        # print('缩放比例', scale_ratio)
        obj_torus.scale = (scale_ratio, scale_ratio, 1)


def getRadius_upper(op):
    global old_radius_upper, scale_ratio, now_radius_upper, on_obj, operator_obj, mouse_loc

    # 翻转圆环法线
    obj_torus = bpy.data.objects[operator_obj + 'UpperTorus']
    obj_circle = bpy.data.objects[operator_obj + 'UpperCircle']
    active_obj = bpy.data.objects[operator_obj + 'huanqiecompare']
    for selected_obj in bpy.data.objects:
        if (selected_obj.name == operator_obj + "huanqiecompareintersect"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = active_obj.name + "intersect"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)
    if operator_obj == '右耳':
        moveToRight(duplicate_obj)
    elif operator_obj == '左耳':
        moveToLeft(duplicate_obj)

    bpy.context.view_layer.objects.active = duplicate_obj
    # 添加修改器,获取交面

    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate_obj.modifiers.new(name="Boolean Intersect", type='BOOLEAN')
    duplicate_obj.modifiers[0].operation = 'INTERSECT'
    duplicate_obj.modifiers[0].object = obj_circle
    duplicate_obj.modifiers[0].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect', single_user=True)

    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    rbm = bmesh.from_edit_mesh(duplicate_obj.data)
    # rbm = bmesh.new()
    # rbm.from_mesh(duplicate_obj.data)

    # 获取截面上的点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()
    plane_verts = [v for v in rbm.verts if distance_to_plane(plane_normal, plane_point, v.co) == 0]
    # print(len(plane_verts))

    # 圆环不在物体上
    if (len(plane_verts) == 0):
        on_obj = False
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        on_obj = True

    # print('圆环是否在物体上',on_obj)

    if on_obj:
        for v in plane_verts:
            v.select = True
        for edge in rbm.edges:
            if edge.verts[0].select and edge.verts[1].select:
                edge.select_set(True)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.select_get():
                if obj.name != duplicate_obj.name:
                    temp_plane_obj = obj
        bpy.context.view_layer.objects.active = temp_plane_obj
        duplicate_obj.select_set(False)
        temp_plane_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(temp_plane_obj.data)
        verts = [v for v in bm.verts]
        verts[0].select = True
        bpy.ops.mesh.select_linked(delimit=set())
        select_verts = [v for v in bm.verts if v.select]
        unselect_verts = [v for v in bm.verts if not v.select]

        if len(select_verts) == len(verts):
            # print("选中的顶点数和平面上的顶点数一致")
            center = sum((v.co for v in verts), Vector()) / len(verts)

            # 初始化最大距离为负无穷大
            max_distance = float('-inf')
            min_distance = float('inf')

            # 遍历的每个顶点并计算距离
            for vertex in verts:
                distance = (vertex.co - obj_torus.location).length
                max_distance = max(max_distance, distance)
                min_distance = min(min_distance, distance)

            radius = round(max_distance, 2)
            radius = radius + 0.5
            # print('最大半径',radius)
            # print('最小半径',min_distance)
            now_radius_upper = round(min_distance, 2)

        else:
            # print("选中的顶点数和平面上的顶点数不一致")
            center1 = sum((v.co for v in select_verts), Vector()) / len(select_verts)
            center2 = sum((v.co for v in unselect_verts), Vector()) / len(unselect_verts)
            if (mouse_loc - center1).length < (mouse_loc - center2).length:
                center = center1
                verts = select_verts
            else:
                center = center2
                verts = unselect_verts

            # 初始化最大距离为负无穷大
            max_distance = float('-inf')
            min_distance = float('inf')

            # 遍历的每个顶点并计算距离
            for vertex in verts:
                distance = (vertex.co - obj_torus.location).length
                max_distance = max(max_distance, distance)
                min_distance = min(min_distance, distance)

            radius = round(max_distance, 2)
            radius = radius + 0.5
            # print('最大半径',radius)
            # print('最小半径',min_distance)
            now_radius_upper = round(min_distance, 2)

        bpy.ops.object.mode_set(mode='OBJECT')
        # 删除复制的物体
        bpy.data.objects.remove(duplicate_obj, do_unlink=True)
        bpy.data.objects.remove(temp_plane_obj, do_unlink=True)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_torus
        obj_torus.select_set(True)
        # 缩放圆环及调整位置
        if op == 'move':
            obj_torus.location = center
            obj_circle.location = center
        scale_ratio = round(radius / old_radius_upper, 3)
        # print('缩放比例', scale_ratio)
        obj_torus.scale = (scale_ratio, scale_ratio, 1)


# 计算点到平面的距离
def distance_to_plane(plane_normal, plane_point, point):
    return round(abs(plane_normal.dot(point - plane_point)), 4)


def set_finish(is_finish):
    global finish
    finish = is_finish


def saveCir():
    global old_radius, right_last_loc, right_last_radius, right_last_ratation, left_last_loc, left_last_radius, left_last_ratation, operator_obj
    obj_torus = bpy.data.objects[operator_obj + 'Torus']
    last_loc = obj_torus.location.copy()
    last_radius = round(old_radius * obj_torus.scale[0], 2)
    last_ratation = obj_torus.rotation_euler.copy()
    if operator_obj == '右耳':
        right_last_loc = last_loc
        right_last_radius = last_radius
        right_last_ratation = last_ratation
    else:
        left_last_loc = last_loc
        left_last_radius = last_radius
        left_last_ratation = last_ratation


def saveCir_upper():
    global old_radius_upper, right_last_loc_upper, right_last_radius_upper, right_last_ratation_upper, left_last_loc_upper, left_last_radius_upper, left_last_ratation_upper, operator_obj
    obj_torus = bpy.data.objects[operator_obj + 'UpperTorus']
    last_loc = obj_torus.location.copy()
    last_radius = round(old_radius_upper * obj_torus.scale[0], 2)
    last_ratation = obj_torus.rotation_euler.copy()
    if operator_obj == '右耳':
        right_last_loc_upper = last_loc
        right_last_radius_upper = last_radius
        right_last_ratation_upper = last_ratation
    else:
        left_last_loc_upper = last_loc
        left_last_radius_upper = last_radius
        left_last_ratation_upper = last_ratation


class Soft_Eardrum_Circle_Cut(bpy.types.Operator):
    bl_idname = "object.softeardrumcirclecut"
    bl_label = "圆环切割"

    __initial_rotation_x = None  # 初始x轴旋转角度
    __initial_rotation_y = None
    __initial_rotation_z = None
    __left_mouse_down = False  # 按下右键未松开时，旋转圆环角度
    __right_mouse_down = False  # 按下右键未松开时，圆环上下移动
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __is_moving = False
    __dx = 0
    __dy = 0

    def cast_ray(self, context, event):

        # cast ray from mouse location, return data from ray
        scene = context.scene
        #   region = context.region
        #   rv3d = context.region_data

        # 左边窗口区域
        override1 = getOverride()
        override2 = getOverride2()
        region1 = override1['region']
        region2 = override2['region']
        area1 = override1['area']
        area2 = override2['area']
        if (event.mouse_region_x > region1.width):
            #   print('右窗口')
            coord = event.mouse_region_x - region1.width, event.mouse_region_y
            region = region2
            rv3d = area2.spaces.active.region_3d
        else:
            #   print('左窗口')
            coord = event.mouse_region_x, event.mouse_region_y
            region = region1
            rv3d = area1.spaces.active.region_3d
        viewlayer = context.view_layer.depsgraph
        # get the ray from the viewport and mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        hit, location, normal, index, object, matrix = scene.ray_cast(viewlayer, ray_origin, view_vector)
        return hit, location, normal, index, object, matrix

    def invoke(self, context, event):

        op_cls = Soft_Eardrum_Circle_Cut

        op_cls.__initial_rotation_x = None
        op_cls.__initial_rotation_y = None
        op_cls.__initial_rotation_z = None
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None

        if not get_soft_modal_start():
            context.window_manager.modal_handler_add(self)
            print('soft_modal invoke')
            set_soft_modal_start(True)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global finish, operator_obj, mouse_loc, operator_torus_obj, operator_circle_obj
        op_cls = Soft_Eardrum_Circle_Cut
        mould_type = bpy.context.scene.muJuTypeEnum

        mouse_x = event.mouse_x
        mouse_y = event.mouse_y
        override1 = getOverride()
        area = override1['area']

        if bpy.context.screen.areas[0].spaces.active.context == 'SCENE':

            # 物体处在报错状态下, 将暂停的状态取消
            if bpy.data.objects[context.scene.leftWindowObj].data.materials[0].name == "error_yellow" and \
                    context.mode == 'OBJECT' and finish:
                finish = False

            # 未切割时起效
            if mouse_x < area.width and area.y < mouse_y < area.y+area.height and finish == False:
                if mould_type == "OP1":  # 初始化圆环物体及双窗口下的操作
                    mouse_x = event.mouse_x
                    mouse_y = event.mouse_y
                    override1 = getOverride()
                    area = override1['area']
                    override2 = getOverride2()
                    area2 = override2['area']

                    workspace = bpy.context.window.workspace.name
                    # 双窗口模式下
                    if workspace == '布局.001':
                        # 根据鼠标位置判断当前操作窗口
                        if (mouse_x > area.width and mouse_y > area2.y):
                            # print('右窗口')
                            operator_obj = context.scene.rightWindowObj
                        else:
                            # print('左窗口')
                            operator_obj = context.scene.leftWindowObj
                    elif workspace == '布局':
                        operator_obj = context.scene.leftWindowObj

                    obj_torus = bpy.data.objects.get(operator_obj + 'Torus')
                    obj_upper_torus = bpy.data.objects.get(operator_obj + 'UpperTorus')
                    # 初始化环体
                    # if obj_torus == None:
                    #     # 正常初始化
                    #     if last_loc == None:
                    #         # 初始化环体
                    #         bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(
                    #             0, 0, 0), rotation=(0.0, 0, 0), major_segments=80, minor_segments=80,
                    #                                          major_radius=old_radius,
                    #                                          minor_radius=0.4)
                    #
                    #     else:
                    #         # 初始化环体
                    #         bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
                    #             last_ratation[0], last_ratation[1], last_ratation[2]), major_segments=80, minor_segments=80,
                    #                                          major_radius=last_radius, minor_radius=0.4)
                    #         old_radius = last_radius
                    #
                    #     obj = bpy.context.active_object
                    #     obj.name = operator_obj + 'Torus'
                    #     if operator_obj == '右耳':
                    #         moveToRight(obj)
                    #     elif operator_obj == '左耳':
                    #         moveToLeft(obj)
                    #     # 环体颜色
                    #     initialTorusColor()
                    #     obj.data.materials.clear()
                    #     obj.data.materials.append(bpy.data.materials['red'])
                    #     obj_torus = bpy.data.objects.get(operator_obj + 'Torus')
                    #
                    active_obj = bpy.data.objects.get(operator_obj + 'Circle')
                    active_upper_obj = bpy.data.objects.get(operator_obj + 'UpperCircle')
                    # 初始化圆圈
                    # if active_obj == None:
                    #     # 正常初始化
                    #     if last_loc == None:
                    #         # 大圆环
                    #         bpy.ops.mesh.primitive_circle_add(
                    #             vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                    #             align='WORLD', location=(
                    #                 0, 0, 0), rotation=(
                    #                 0.0, 0.0, 0.0), scale=(
                    #                 1.0, 1.0, 1.0))
                    #     else:
                    #         bpy.ops.mesh.primitive_circle_add(
                    #             vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                    #             align='WORLD',
                    #             location=last_loc, rotation=(
                    #                 last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                    #                 1.0, 1.0, 1.0))
                    #         old_radius = last_radius
                    #     obj = bpy.context.active_object
                    #     obj.name = operator_obj + 'Circle'
                    #     obj.hide_set(True)
                    #     if operator_obj == '右耳':
                    #         moveToRight(obj)
                    #     elif operator_obj == '左耳':
                    #         moveToLeft(obj)
                    #     active_obj = bpy.data.objects.get(operator_obj + 'Circle')
                    #
                    # bpy.ops.object.select_all(action='DESELECT')
                    # bpy.context.view_layer.objects.active = obj_torus
                    # obj_torus.select_set(True)

                    if (obj_torus == None or active_obj == None) and (obj_upper_torus == None or active_upper_obj == None):
                        return {'PASS_THROUGH'}

                # 鼠标是否在圆环上
                if (mould_type == "OP1" or mould_type == "OP4") and is_mouse_on_object(context, event):
                    if operator_circle_obj is None or operator_torus_obj is None:
                        return {'PASS_THROUGH'}
                    obj_torus = bpy.data.objects.get(operator_torus_obj)
                    active_obj = bpy.data.objects.get(operator_circle_obj)
                    if obj_torus is None or active_obj is None:
                        return {'PASS_THROUGH'}

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj_torus
                    obj_torus.select_set(True)

                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            op_cls.__is_moving = True
                            op_cls.__left_mouse_down = True
                            op_cls.__initial_rotation_x = obj_torus.rotation_euler[0]
                            op_cls.__initial_rotation_y = obj_torus.rotation_euler[1]
                            op_cls.__initial_rotation_z = obj_torus.rotation_euler[2]
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y

                            op_cls.__dx = round(mouse_loc.x, 2)
                            op_cls.__dy = round(mouse_loc.y, 2)

                        # 取消
                        elif event.value == 'RELEASE':
                            normal = active_obj.matrix_world.to_3x3(
                            ) @ active_obj.data.polygons[0].normal
                            if normal.z > 0:  # 反转法线
                                print('圆环法线', normal)
                                print('反转法线')
                                override1 = getOverride()
                                override2 = getOverride2()
                                region1 = override1['region']
                                region2 = override2['region']
                                if event.mouse_region_x > region1.width:
                                    with bpy.context.temp_override(**override2):
                                        active_obj.hide_set(False)
                                        bpy.context.view_layer.objects.active = active_obj
                                        bpy.ops.object.mode_set(mode='EDIT')
                                        bpy.ops.mesh.select_all(action='SELECT')
                                        # 翻转圆环法线
                                        # bpy.ops.mesh.flip_normals(only_clnors=False)
                                        bpy.ops.mesh.flip_normals()
                                        # bpy.ops.mesh.normals_make_consistent(inside=True)
                                        # 隐藏圆环
                                        active_obj.hide_set(True)
                                        # 返回对象模式
                                        bpy.ops.object.mode_set(mode='OBJECT')
                                        print('反转后法线', active_obj.matrix_world.to_3x3(
                                        ) @ active_obj.data.polygons[0].normal)
                                else:
                                    active_obj.hide_set(False)
                                    bpy.context.view_layer.objects.active = active_obj
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    bpy.ops.mesh.select_all(action='SELECT')
                                    # 翻转圆环法线
                                    # bpy.ops.mesh.flip_normals(only_clnors=False)
                                    bpy.ops.mesh.flip_normals()
                                    # bpy.ops.mesh.normals_make_consistent(inside=True)
                                    # 隐藏圆环
                                    active_obj.hide_set(True)
                                    # 返回对象模式
                                    bpy.ops.object.mode_set(mode='OBJECT')
                                    print('反转后法线', active_obj.matrix_world.to_3x3(
                                    ) @ active_obj.data.polygons[0].normal)
                            # soft_eardrum_smooth_initial()
                            # bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()\
                            if operator_torus_obj == operator_obj + 'Torus':
                                saveCir()  # 保存数据 圆环位置,旋转,尺寸大小
                                refill_after_cavity_plane_change()  # 重新补面填充
                            elif operator_torus_obj == operator_obj + 'UpperTorus':
                                saveCir_upper()
                                reset_and_refill()

                            op_cls.__is_moving = False
                            op_cls.__left_mouse_down = False
                            op_cls.__initial_rotation_x = None
                            op_cls.__initial_rotation_y = None
                            op_cls.__initial_rotation_z = None
                            op_cls.__initial_mouse_x = None
                            op_cls.__initial_mouse_y = None

                        return {'RUNNING_MODAL'}

                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            op_cls.__is_moving = True
                            op_cls.__right_mouse_down = True
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                        elif event.value == 'RELEASE':
                            # soft_eardrum_smooth_initial()
                            # bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()
                            if operator_torus_obj == operator_obj + 'Torus':
                                saveCir()  # 保存数据 圆环位置,旋转,尺寸大小
                                refill_after_cavity_plane_change()  # 重新补面填充
                            elif operator_torus_obj == operator_obj + 'UpperTorus':
                                saveCir_upper()
                                reset_and_refill()

                            op_cls.__is_moving = False
                            op_cls.__right_mouse_down = False
                            op_cls.__initial_mouse_x = None
                            op_cls.__initial_mouse_y = None

                        return {'RUNNING_MODAL'}

                    elif event.type == 'MOUSEMOVE':
                        # 左键按住旋转
                        if op_cls.__left_mouse_down:
                            # 旋转角度正负号
                            if (op_cls.__dy < 0):
                                symx = -1
                            else:
                                symx = 1

                            if (op_cls.__dx > 0):
                                symy = -1
                            else:
                                symy = 1

                            # x,y轴旋转比例
                            px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                       4)
                            py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                       4)

                            # 旋转角度
                            rotate_angle_x = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                            rotate_angle_y = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                            rotate_angle_z = round((event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)

                            active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                           rotate_angle_x * symx
                            active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                           rotate_angle_y * symy
                            active_obj.rotation_euler[2] = op_cls.__initial_rotation_z + \
                                                           rotate_angle_z

                            obj_torus.rotation_euler[0] = active_obj.rotation_euler[0]
                            obj_torus.rotation_euler[1] = active_obj.rotation_euler[1]
                            obj_torus.rotation_euler[2] = active_obj.rotation_euler[2]

                            if operator_torus_obj == operator_obj + 'Torus':
                                getRadius('rotate')
                            elif operator_torus_obj == operator_obj + 'UpperTorus':
                                getRadius_upper('rotate')
                            return {'RUNNING_MODAL'}
                        elif op_cls.__right_mouse_down:
                            # 平面法线方向
                            normal = active_obj.matrix_world.to_3x3(
                            ) @ active_obj.data.polygons[0].normal

                            dis = event.mouse_region_y - op_cls.__initial_mouse_y
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            print('距离', dis)
                            active_obj.location -= normal * dis * 0.05
                            obj_torus.location -= normal * dis * 0.05

                            if operator_torus_obj == operator_obj + 'Torus':
                                getRadius('move')
                            elif operator_torus_obj == operator_obj + 'UpperTorus':
                                getRadius_upper('move')
                            return {'RUNNING_MODAL'}

                    return {'PASS_THROUGH'}
                    # return {'RUNNING_MODAL'}

                elif mould_type != "OP1" and mould_type != 'OP4':
                    set_soft_modal_start(False)
                    print("soft_modal finish")
                    return {'FINISHED'}

                else:
                    tar_obj = bpy.data.objects[operator_obj]
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = tar_obj
                    tar_obj.select_set(True)
                    # print('不在圆环上')
                    # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    # obj_torus = bpy.data.objects[operator_obj + 'Torus']
                    # active_obj = bpy.data.objects[operator_obj + 'Circle']
                    if operator_circle_obj is None or operator_torus_obj is None:
                        return {'PASS_THROUGH'}
                    obj_torus = bpy.data.objects.get(operator_torus_obj)
                    active_obj = bpy.data.objects.get(operator_circle_obj)
                    if obj_torus is None or active_obj is None:
                        return {'PASS_THROUGH'}
                    if event.value == 'RELEASE' and op_cls.__is_moving:
                        normal = active_obj.matrix_world.to_3x3(
                        ) @ active_obj.data.polygons[0].normal
                        if normal.z > 0:
                            print('圆环法线', normal)
                            print('反转法线')
                            override1 = getOverride()
                            override2 = getOverride2()
                            region1 = override1['region']
                            region2 = override2['region']
                            # 右窗口
                            if event.mouse_region_x > region1.width:
                                with bpy.context.temp_override(**override2):
                                    active_obj.hide_set(False)
                                    bpy.context.view_layer.objects.active = active_obj
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    bpy.ops.mesh.select_all(action='SELECT')
                                    # 翻转圆环法线
                                    # bpy.ops.mesh.flip_normals(only_clnors=False)
                                    bpy.ops.mesh.flip_normals()
                                    # bpy.ops.mesh.normals_make_consistent(inside=True)
                                    # 隐藏圆环
                                    active_obj.hide_set(True)
                                    # 返回对象模式
                                    bpy.ops.object.mode_set(mode='OBJECT')
                                    print('反转后法线', active_obj.matrix_world.to_3x3(
                                    ) @ active_obj.data.polygons[0].normal)
                            else:
                                active_obj.hide_set(False)
                                bpy.context.view_layer.objects.active = active_obj
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.select_all(action='SELECT')
                                # 翻转圆环法线
                                # bpy.ops.mesh.flip_normals(only_clnors=False)
                                bpy.ops.mesh.flip_normals()
                                # bpy.ops.mesh.normals_make_consistent(inside=True)
                                # 隐藏圆环
                                active_obj.hide_set(True)
                                # 返回对象模式
                                bpy.ops.object.mode_set(mode='OBJECT')
                                print('反转后法线', active_obj.matrix_world.to_3x3(
                                ) @ active_obj.data.polygons[0].normal)
                        # soft_eardrum_smooth_initial()
                        # bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()
                        if operator_torus_obj == operator_obj + 'Torus':
                            saveCir()
                            refill_after_cavity_plane_change()  # 重新补面填充
                        elif operator_torus_obj == operator_obj + 'UpperTorus':
                            saveCir_upper()
                            reset_and_refill()

                        op_cls.__is_moving = False
                        op_cls.__left_mouse_down = False
                        op_cls.__right_mouse_down = False
                        op_cls.__initial_rotation_x = None
                        op_cls.__initial_rotation_y = None
                        op_cls.__initial_rotation_z = None
                        op_cls.__initial_mouse_x = None
                        op_cls.__initial_mouse_y = None

                    if event.type == 'MOUSEMOVE':
                        # 左键按住旋转
                        if op_cls.__left_mouse_down:
                            # 旋转正负号
                            if (op_cls.__dy < 0):
                                symx = -1
                            else:
                                symx = 1

                            if (op_cls.__dx > 0):
                                symy = -1
                            else:
                                symy = 1

                            # print('symx',symx)
                            # print('symy',symy)

                            #  x,y轴旋转比例
                            px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                       4)
                            py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                       4)
                            # print('px',px)
                            # print('py',py)

                            # 旋转角度
                            rotate_angle_x = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                            rotate_angle_y = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                            rotate_angle_z = round((event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)

                            active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                           rotate_angle_x * symx
                            active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                           rotate_angle_y * symy
                            active_obj.rotation_euler[2] = op_cls.__initial_rotation_z + \
                                                           rotate_angle_z
                            obj_torus.rotation_euler[0] = active_obj.rotation_euler[0]
                            obj_torus.rotation_euler[1] = active_obj.rotation_euler[1]
                            obj_torus.rotation_euler[2] = active_obj.rotation_euler[2]

                            if operator_torus_obj == operator_obj + 'Torus':
                                getRadius('rotate')
                            elif operator_torus_obj == operator_obj + 'UpperTorus':
                                getRadius_upper('rotate')
                            return {'RUNNING_MODAL'}

                        elif op_cls.__right_mouse_down:
                            # 平面法线方向
                            normal = active_obj.matrix_world.to_3x3(
                            ) @ active_obj.data.polygons[0].normal

                            dis = event.mouse_region_y - op_cls.__initial_mouse_y
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            print('距离', dis)
                            active_obj.location -= normal * dis * 0.05
                            obj_torus.location -= normal * dis * 0.05
                            if operator_torus_obj == operator_obj + 'Torus':
                                getRadius('move')
                            elif operator_torus_obj == operator_obj + 'UpperTorus':
                                getRadius_upper('move')
                            return {'RUNNING_MODAL'}
                    return {'PASS_THROUGH'}

            else:
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                set_soft_modal_start(False)
                print("soft_modal finish")
                if (not get_point_qiehuan_modal_start() and not get_drag_curve_modal_start()
                        and not get_smooth_curve_modal_start()):
                    set_switch_time(None)
                return {'FINISHED'}
            return {'PASS_THROUGH'}


# 根据点到平面的距离，计算移动的长度
def displacement(distance, a, b):
    dis = a * (distance - b) * (distance - b)
    return dis


def smooth_inner_plane(inner_obj):
    global operator_obj
    obj_circle = bpy.data.objects[operator_obj + 'Circle']
    bpy.ops.object.mode_set(mode='EDIT')

    mesh = inner_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.vertex_group_set_active(group='CutBorderVertex')
    bpy.ops.object.vertex_group_select()
    for _ in range(0, 3):
        bpy.ops.mesh.select_more()

    select_vert = [v for v in bm.verts if v.select]

    # 圆环平面法向量和平面上一点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()

    smooth_vert = list()
    max_distance = 0
    for v in select_vert:
        dis = distance_to_plane(plane_normal, plane_point, v.co)
        if dis < 1:
            smooth_vert.append(v)
            max_distance = max(dis, max_distance)
    bpy.ops.mesh.select_all(action='DESELECT')

    for v in smooth_vert:
        distance = distance_to_plane(plane_normal, plane_point, v.co)
        move = displacement(distance, 0.5, max_distance)
        center = plane_point.copy()
        to_center = v.co - center
        # 计算径向位移的增量
        movement = to_center.normalized() * move
        v.co -= movement

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


def register():
    bpy.utils.register_class(Soft_Eardrum_Circle_Cut)


def unregister():
    bpy.utils.unregister_class(Soft_Eardrum_Circle_Cut)
