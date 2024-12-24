import bpy
import bmesh
import math
import re

from ...tool import moveToRight, moveToLeft, convert_to_mesh, subdivide, newColor, set_vert_group, delete_vert_group, \
    extrude_border_by_vertex_groups, getOverride, utils_re_color
from ...utils.utils import resample_curve, utils_draw_curve, utils_copy_object

from ..soft_eardrum.thickness_and_fill import draw_cut_plane_upper, draw_cut_plane, soft_eardrum_thickness, \
    soft_eardrum_inner_cut, soft_eardrum_outer_cut, save_outer_and_inner_origin, join_outer_and_inner, \
    soft_extrude_smooth_initial, soft_eardrum, set_finish, copyModel, reset_to_after_cut, reset_to_after_dig, fill
from ..parameters_for_create_mould import get_right_frame_style_hole_border, get_left_frame_style_hole_border, \
    set_right_frame_style_hole_border, set_left_frame_style_hole_border

from mathutils import Vector

def calculate_angle(x, y):
    # 计算原点与给定坐标点之间的角度（弧度）
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees


# 对顶点进行排序用于画圈
def get_order_border_vert(selected_verts):
    size = len(selected_verts)
    finish = False
    # 尝试使用距离最近的点
    order_border_vert = []
    now_vert = selected_verts[0]
    unprocessed_vertex = selected_verts  # 未处理顶点
    while len(unprocessed_vertex) > 1 and not finish:
        order_border_vert.append(now_vert)
        unprocessed_vertex.remove(now_vert)

        min_distance = math.inf
        now_vert_co = now_vert

        # 2024/1/2 z轴落差过大会导致问题，这里只考虑xy坐标
        for vert in unprocessed_vertex:
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert
        if min_distance > 3 and len(unprocessed_vertex) < 0.1 * size:
            finish = True
    return order_border_vert


# 绘制曲线
def draw_border_curve(order_border_co, name, depth):
    active_obj = bpy.context.active_object
    new_node_list = list()
    for i in range(len(order_border_co)):
        if i % 2 == 0:
            new_node_list.append(order_border_co[i])
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # 添加一个曲线样条
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(new_node_list) - 1)
    spline.use_cyclic_u = True

    # 设置每个点的坐标
    for i, point in enumerate(new_node_list):
        spline.points[i].co = (point[0], point[1], point[2], 1)

    # 更新场景
    # 这里可以自行调整数值
    # 解决上下文问题
    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.context.active_object.data.bevel_depth = depth
        if bpy.context.scene.leftWindowObj == '右耳':
            moveToRight(bpy.context.active_object)
        elif bpy.context.scene.leftWindowObj == '左耳':
            moveToLeft(bpy.context.active_object)

        # 为圆环上色
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


def draw_cylinder(outer_dig_border, inner_dig_border):
    order_outer_dig_border = get_order_border_vert(outer_dig_border)
    order_inner_dig_border = get_order_border_vert(inner_dig_border)
    order_outer_top = []
    order_outer_bottom = []
    order_inner_top = []
    order_inner_bottom = []

    for v in order_outer_dig_border:
        order_outer_top.append((v[0], v[1], 10))
        order_outer_bottom.append((v[0], v[1], v[2] - 0.2))
    for v in order_inner_dig_border:
        order_inner_bottom.append((v[0], v[1], -5))
        order_inner_top.append((v[0], v[1], v[2] + 1))

    draw_border_curve(order_outer_dig_border, "HoleBorderCurve", 0.18)
    draw_border_curve(order_outer_dig_border, "CylinderOuter", 0)
    draw_border_curve(order_inner_dig_border, "CylinderInner", 0)

    draw_border_curve(order_outer_top, "CylinderOuterTop", 0)
    draw_border_curve(order_outer_bottom, "CylinderOuterBottom", 0)

    draw_border_curve(order_inner_top, "CylinderInnerTop", 0)
    draw_border_curve(order_inner_bottom, "CylinderInnerBottom", 0)
    for obj in bpy.data.objects:
        obj.select_set(False)
    # 转换为网格，用于后续桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterTop"]
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuterTop"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuter"]
    bpy.data.objects["CylinderOuter"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuter"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterBottom"]
    bpy.data.objects["CylinderOuterBottom"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuterBottom"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerTop"]
    bpy.data.objects["CylinderInnerTop"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInnerTop"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInner"]
    bpy.data.objects["CylinderInner"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInner"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerBottom"]
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInnerBottom"].select_set(False)

    # 分段桥接出一个圆柱
    # 边合并边设置顶点组用于后续方便选择
    # 上段圆柱合并与桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterTop"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_top_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuterTop", cylinder_top_index)

    # 合并1，2段
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.data.objects["CylinderOuter"].select_set(True)
    bpy.ops.object.join()
    # 获取第二段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_outer_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuter", cylinder_outer_index)

    # 合并2，3段
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.data.objects["CylinderOuterBottom"].select_set(True)
    bpy.ops.object.join()
    # 获取第三段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuterBottom", cylinder_inner_index)

    # 依次桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderOuterTop')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderOuterBottom')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')

    # 修改切割圆柱名称
    bpy.data.objects["CylinderOuterTop"].name = "CylinderForOuterDig"
    bpy.data.objects["CylinderForOuterDig"].select_set(False)

    # 下段圆柱合并于桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerBottom"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_top_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInnerBottom", cylinder_top_index)

    # 合并1，2段
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.data.objects["CylinderInner"].select_set(True)
    bpy.ops.object.join()
    # 获取第二段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_outer_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInner", cylinder_outer_index)

    # 合并2，3段
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.data.objects["CylinderInnerTop"].select_set(True)
    bpy.ops.object.join()
    # 获取第三段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInnerTop", cylinder_inner_index)

    # 依次桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderInnerTop')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderInnerBottom')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')

    # 修改切割圆柱名称
    bpy.data.objects["CylinderInnerBottom"].name = "CylinderForInnerDig"
    bpy.data.objects["CylinderForInnerDig"].select_set(False)

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
    bpy.data.objects["右耳"].select_set(True)


def boolean_dig():
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigOuterHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigOuterHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigOuterHole"].object = bpy.data.objects["CylinderForOuterDig"]
    bpy.context.object.modifiers["DigOuterHole"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="DigOuterHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_outer_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpOuterBorderVertex", up_outer_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("OuterHoleBorderVertex", up_outer_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigInnerHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigInnerHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigInnerHole"].object = bpy.data.objects["CylinderForInnerDig"]
    bpy.context.object.modifiers["DigInnerHole"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="DigInnerHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_inner_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpInnerBorderVertex", up_inner_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("InnerHoleBorderVertex", up_inner_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # 桥接上下边界
    bpy.ops.object.vertex_group_set_active(group='InnerHoleBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.object.vertex_group_set_active(group='OuterHoleBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.bridge_edge_loops()

    # 删除辅助用的物体
    bpy.data.objects.remove(bpy.data.objects["CylinderForInnerDig"], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["CylinderForOuterDig"], do_unlink=True)

    delete_vert_group("InnerHoleBorderVertex")
    delete_vert_group("OuterHoleBorderVertex")

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


# 获取洞边界顶点
def get_hole_border(template_hole_border, number):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        dig_border = []  # 被选择的挖孔顶点

        for template_hole_border_point in template_hole_border:  # 通过向z负方向投射找到边界
            xx = template_hole_border_point[0]
            yy = template_hole_border_point[1]
            origin = (xx, yy, 10)
            direction = (0, 0, -1)
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)
            if hit:
                dig_border.append((loc[0], loc[1], loc[2]))

        order_hole_border_vert = get_order_border_vert(dig_border)

        curve_name = name + 'HoleBorderCurve' + str(number)
        draw_border_curve(order_hole_border_vert, curve_name, 0.18)
        draw_cylinder_bottom(order_hole_border_vert)

        bpy.ops.object.mode_set(mode='OBJECT')


# def dig_hole():
#     name = bpy.context.scene.leftWindowObj
#
#     template_hole_border_list = []
#     if (name == "右耳"):
#         template_hole_border_list = get_right_frame_style_hole_border()
#     elif (name == "左耳"):
#         template_hole_border_list = get_left_frame_style_hole_border()
#     # 复制切割补面完成后的物体
#     # cur_obj = bpy.data.objects[name]
#     # duplicate_obj = cur_obj.copy()
#     # duplicate_obj.data = cur_obj.data.copy()
#     # duplicate_obj.animation_data_clear()
#     # duplicate_obj.name = cur_obj.name + "OriginForDigHole"
#     # bpy.context.collection.objects.link(duplicate_obj)
#     # duplicate_obj.hide_set(True)
#     # moveToRight(duplicate_obj)
#
#     number = len(template_hole_border_list)
#     for template_hole_border in template_hole_border_list:
#         get_hole_border(template_hole_border, number)
#         translate_circle_to_cylinder()
#         # 创建布尔修改器
#         boolean_cut(number)
#         local_curve_name = name + 'HoleBorderCurve' + str(number)
#         local_mesh_name = name + 'meshHoleBorderCurve' + str(number)
#         # subdivide(local_curve_name, 1)  # 细分曲线，防止曲线的点太少移动时穿模
#         convert_to_mesh(local_curve_name, local_mesh_name, 0.18)  # 重新生成网格
#         number -= 1
#
#     # for obj in bpy.data.objects:
#     #     if obj.name == 'HoleBorderCurve':
#     #         obj.name = 'HoleBorderCurve1'
#     #         subdivide('HoleBorderCurve1', 3)
#     #         convert_to_mesh('HoleBorderCurve1', 'meshHoleBorderCurve1', 0.18)
#     #
#     #     if obj.name == 'HoleBorderCurve.001':
#     #         obj.name = 'HoleBorderCurve2'
#     #         subdivide('HoleBorderCurve2', 3)
#     #         convert_to_mesh('HoleBorderCurve2', 'meshHoleBorderCurve2', 0.18)
#
#     bpy.context.view_layer.objects.active = bpy.data.objects[name]


# def re_dig_hole():
#     name = bpy.context.scene.leftWindowObj
#
#     template_hole_border_list = []
#     if (name == "右耳"):
#         template_hole_border_list = get_right_frame_style_hole_border()
#     elif (name == "左耳"):
#         template_hole_border_list = get_left_frame_style_hole_border()
#     # 复制切割补面完成后的物体
#     cur_obj = bpy.data.objects[name]
#     duplicate_obj = cur_obj.copy()
#     duplicate_obj.data = cur_obj.data.copy()
#     duplicate_obj.animation_data_clear()
#     duplicate_obj.name = cur_obj.name + "OriginForDigHole"
#     bpy.context.collection.objects.link(duplicate_obj)
#     duplicate_obj.hide_set(True)
#     moveToRight(duplicate_obj)
#
#     number = len(template_hole_border_list)
#
#     for i in range(1, number + 1):
#         get_hole_border_by_curve(i)
#         translate_circle_to_cylinder()
#         # 创建布尔修改器
#         boolean_cut(i)
#         local_curve_name = name + 'HoleBorderCurve' + str(i)
#         local_mesh_name = name + 'meshHoleBorderCurve' + str(i)
#         # subdivide(local_curve_name, 1)  # 细分曲线，防止曲线的点太少移动时穿模
#         convert_to_mesh(local_curve_name, local_mesh_name, 0.18)  # 重新生成网格
#
#     bpy.context.view_layer.objects.active = bpy.data.objects[name]


def get_hole_border_by_curve(number):
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects[name + 'HoleBorderCurve' + str(number)]
    dig_border = [point.co[0:3] for point in curve_obj.data.splines[0].points]

    order_hole_border_vert = get_order_border_vert(dig_border)
    draw_cylinder_bottom(order_hole_border_vert)


def draw_cylinder_bottom(order_hole_border_vert):
    name = bpy.context.scene.leftWindowObj
    # 该变量存储布尔切割的圆柱体的底部
    cut_cylinder_buttom_co = []
    for vert in order_hole_border_vert:
        # 先直接用原坐标，后续尝试法向向外走一段
        co = vert
        cut_cylinder_buttom_co.append([co[0], co[1], co[2] - 2])
    draw_border_curve(cut_cylinder_buttom_co, name + "HoleCutCylinderBottom", 0)


def translate_circle_to_cylinder():
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == name + "HoleCutCylinderBottom":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')
    # 切换回编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, 12)}
    )
    bpy.ops.mesh.select_all(action='SELECT')
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.hide_set(True)


# 使用布尔修改器
def boolean_cut(number):
    name = bpy.context.scene.leftWindowObj
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects[name]
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # 新建顶点组
    obj.vertex_groups.new(name="FrameAll")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 使用布尔插件
    bpy.data.objects[name + "HoleCutCylinderBottom"].hide_set(False)
    bpy.data.objects[name + "HoleCutCylinderBottom"].select_set(True)
    bpy.ops.object.booltool_auto_difference()

    # 删除多余部分
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    delete_useless_part_finish_flag = False
    for i in range(0,2):
        if not delete_useless_part_finish_flag:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='FrameAll')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.loop_to_region()
            select_vert = [v.index for v in bm.verts if v.select]
            if len(select_vert) == len(bm.verts):
                delete_useless_part_finish_flag = True
            else:
                bpy.ops.mesh.delete(type='FACE')

    # 获取洞边界顶点
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='FrameAll')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')
    up_outer_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpOuterBorderVertex", up_outer_border_index)


    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("HoleBorderVertex" + str(number), up_outer_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # 删除辅助用的顶点组
    delete_vert_group("FrameAll")
    bpy.ops.object.mode_set(mode='OBJECT')

    inside_border_index = extrude_border_by_vertex_groups("HoleBorderVertex" + str(number), "UpInnerBorderVertex")
    # 单个孔的内外边界也留一下
    set_vert_group("HoleInnerBorderVertex" + str(number), inside_border_index)


# ***********************************新增代码***********************************
def extrude_and_set_vert_group():
    extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")

    number = 0
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', obj.name) != None:
            number += 1

    for i in range(1, number + 1):
        inside_border_index = extrude_border_by_vertex_groups("HoleBorderVertex" + str(i), "UpInnerBorderVertex")
        # 单个孔的内外边界也留一下
        set_vert_group("HoleInnerBorderVertex" + str(i), inside_border_index)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def extrude_border(name, step_out, step_in):
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name + 'ForBorderCut'
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    elif bpy.context.scene.leftWindowObj == '左耳':
        moveToLeft(duplicate_obj)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.select_set(True)
    duplicate_obj.data.bevel_depth = 0
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_face_add()
    duplicate_obj.vertex_groups.new(name="temp")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.extrude_region_shrink_fatten(TRANSFORM_OT_shrink_fatten={"value": step_out})
    bpy.ops.object.vertex_group_set_active(group="temp")
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.extrude_region_shrink_fatten(TRANSFORM_OT_shrink_fatten={"value": step_in})
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    if judge_normals():
        bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')

    return duplicate_obj.name


def dig_hole():
    """ 不存在边缘蓝线时的挖孔 """
    name = bpy.context.scene.leftWindowObj

    template_hole_border_list = []
    if name == "右耳":
        template_hole_border_list = get_right_frame_style_hole_border()
    elif name == "左耳":
        template_hole_border_list = get_left_frame_style_hole_border()

    number = len(template_hole_border_list)
    if number == 0:
        generate_curve()
        re_dig_hole()
    else:
        for template_hole_border in template_hole_border_list:
            local_curve_name = name + 'HoleBorderCurve' + str(number)
            local_mesh_name = name + 'meshHoleBorderCurve' + str(number)
            utils_draw_curve(template_hole_border, local_curve_name, 0.18)
            convert_to_mesh(local_curve_name, local_mesh_name, 0.18)  # 重新生成网格
            newColor('blue', 0, 0, 1, 1, 1)
            bpy.data.objects[local_curve_name].data.materials.append(bpy.data.materials['blue'])

            cut_obj_name = extrude_border(local_curve_name, 1, 1)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.data.objects[name].vertex_groups.new(name="all")
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.data.objects[cut_obj_name].select_set(True)
            bpy.ops.object.booltool_auto_difference()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='all')
            # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            # 用于上下桥接的顶点组，只包含当前孔边界
            bpy.context.object.vertex_groups.new(name="HoleBorderVertex" + str(number))
            bpy.ops.object.vertex_group_assign()
            bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
            up_outer_border_index = [v.index for v in bm.verts if v.select]
            bpy.ops.object.mode_set(mode='OBJECT')
            # 用于平滑的顶点组，包含所有孔边界顶点
            set_vert_group("UpOuterBorderVertex", up_outer_border_index)
            delete_vert_group("all")
            delete_useless_part(group_name="HoleBorderVertex" + str(number))

            number -= 1

        # extrude_and_set_vert_group()
        # 复制挖孔完成后的物体
        utils_copy_object(name, name + "OriginForDigHole")


def re_dig_hole():
    """ 存在边缘蓝线时的挖孔 """
    name = bpy.context.scene.leftWindowObj

    number = 0
    for obj in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', obj.name) != None:
            number += 1

    for i in range(1, number + 1):
        local_curve_name = name + 'HoleBorderCurve' + str(i)
        # local_mesh_name = name + 'meshHoleBorderCurve' + str(i)
        # convert_to_mesh(local_curve_name, local_mesh_name, 0.18)  # 重新生成网格

        cut_obj_name = extrude_border(local_curve_name, 1, 1)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[name]
        bpy.data.objects[name].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.data.objects[name].vertex_groups.new(name="all")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects[cut_obj_name].select_set(True)
        bpy.ops.object.booltool_auto_difference()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='all')
        # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        # 用于上下桥接的顶点组，只包含当前孔边界
        bpy.context.object.vertex_groups.new(name="HoleBorderVertex" + str(i))
        bpy.ops.object.vertex_group_assign()
        bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
        up_outer_border_index = [v.index for v in bm.verts if v.select]
        bpy.ops.object.mode_set(mode='OBJECT')
        # 用于平滑的顶点组，包含所有孔边界顶点
        set_vert_group("UpOuterBorderVertex", up_outer_border_index)
        delete_vert_group("all")
        delete_useless_part(group_name="HoleBorderVertex" + str(i))

    # extrude_and_set_vert_group()
    # 复制挖孔完成后的物体
    utils_copy_object(name, name + "OriginForDigHole")


def generate_curve():
    name = bpy.context.scene.leftWindowObj
    target_object = bpy.data.objects[name]
    bbox = [target_object.matrix_world @ Vector(corner) for corner in target_object.bound_box]
    min_corner = Vector((min([v[i] for v in bbox]) for i in range(3)))
    locx = min_corner.x * 0.3
    if name == "右耳":
        locy = min_corner.y * 0.3
    elif name == "左耳":
        locy = min_corner.y * -0.3
    min_dist = float('inf')
    index = None
    for vert in target_object.data.vertices:
        dist = (vert.co.x - locx) ** 2 + (vert.co.y - locy) ** 2
        if dist < min_dist:
            min_dist = dist
            index = vert.index

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(target_object.data)
    bm.verts.ensure_lookup_table()
    bm.verts[index].select = True
    for _ in range(0, 6):
        bpy.ops.mesh.select_more()
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != target_object.name:
                curve_obj = o
    curve_obj.name = name + "HoleBorderCurve1"
    bpy.ops.object.select_all(action='DESELECT')
    target_object.select_set(False)
    curve_obj.select_set(True)
    bpy.context.view_layer.objects.active = curve_obj

    bpy.ops.object.convert(target='CURVE')
    bpy.ops.object.mode_set(mode='EDIT')
    for i in range(0, 6):
        bpy.ops.curve.smooth()

    bpy.ops.object.mode_set(mode='OBJECT')
    resample_curve(len(curve_obj.data.splines[0].points), curve_obj.name)
    snaptoobject(curve_obj.name)
    convert_to_mesh(curve_obj.name, name + 'meshHoleBorderCurve1', 0.18)
    frame_hole_border_list = []
    dig_border = [point.co[0:3] for point in curve_obj.data.splines[0].points]
    frame_hole_border_list.append(dig_border)

    if name == '左耳':
        set_left_frame_style_hole_border(frame_hole_border_list)
    elif name == '右耳':
        set_right_frame_style_hole_border(frame_hole_border_list)

    curve_obj.select_set(False)
    bpy.context.view_layer.objects.active = target_object


def snaptoobject(curve_name):
    ''' 将指定的曲线对象吸附到最近的顶点上 '''
    name = bpy.context.scene.leftWindowObj
    # 获取曲线对象
    curve_object = bpy.data.objects[curve_name]
    # 获取目标物体
    target_object = bpy.data.objects[name + "MouldReset"]
    # 获取数据
    curve_data = curve_object.data

    # 将曲线的每个顶点吸附到目标物体的表面
    for spline in curve_data.splines:
        for point in spline.points:
            # 获取顶点原位置
            vertex_co = curve_object.matrix_world @ Vector(point.co[0:3])

            # 计算顶点在目标物体面上的 closest point
            _, closest_co, _, _ = target_object.closest_point_on_mesh(
                vertex_co)

            # 将顶点位置设置为 closest point
            point.co[0:3] = closest_co
            point.co[3] = 1


def delete_useless_part(group_name):
    bpy.ops.object.mode_set(mode='EDIT')
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group=group_name)
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
    name = bpy.context.scene.leftWindowObj
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = bpy.data.objects[name].vertex_groups.get(group_name)
    bpy.ops.object.vertex_group_set_active(group=group_name)
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 判断切割是否把整个切掉了
    target_me = obj.data
    # 创建bmesh对象
    target_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    target_bm.from_mesh(target_me)
    if len(target_bm.verts) < 100:
        print("切割出错，完全切掉了")
        raise ValueError("切割出错，完全切掉了")


def judge_if_need_invert():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def judge_normals():
    obj_mesh = bmesh.from_edit_mesh(bpy.context.active_object.data)
    sum = 0
    for v in obj_mesh.verts:
        sum += v.normal[2]
    return sum < 0


def frame_fill():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if not bpy.context.scene.neiBianJiXianR:
            bpy.context.scene.neiBianJiXianR = True
        if not bpy.context.scene.shiFouShangBuQieGeMianBanR:
            bpy.context.scene.shiFouShangBuQieGeMianBanR = True
        if bpy.context.scene.KongQiangMianBanTypeEnumR != 'OP1':
            bpy.context.scene.KongQiangMianBanTypeEnumR = 'OP1'
    elif name == '左耳':
        if not bpy.context.scene.neiBianJiXianL:
            bpy.context.scene.neiBianJiXianL = True
        if not bpy.context.scene.shiFouShangBuQieGeMianBanL:
            bpy.context.scene.shiFouShangBuQieGeMianBanL = True
        if bpy.context.scene.KongQiangMianBanTypeEnumL != 'OP1':
            bpy.context.scene.KongQiangMianBanTypeEnumL = 'OP1'

    set_finish(True)
    copyModel(name)
    dig_hole()
    soft_eardrum()
    utils_re_color(name, (1, 0.319, 0.133))
    set_finish(False)


def reset_and_dig_and_refill():
    try:
        name = bpy.context.scene.leftWindowObj
        if bpy.data.objects.get(name + 'HoleBorderCurve1') is not None:
            reset_to_after_dig()
        else:
            # 首先reset到切割完成
            reset_to_after_cut()
            dig_hole()
        fill()

        if name == "右耳":
            bpy.data.objects[name].data.materials.clear()
            bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowR"])
        elif name == "左耳":
            bpy.data.objects[name].data.materials.clear()
            bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowL"])

    except:
        # 重新填充失败时将模型变成金色
        reset_to_after_cut()
        name = bpy.context.scene.leftWindowObj
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])
