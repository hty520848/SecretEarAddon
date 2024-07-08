import bpy
import bmesh
import math
import re

from ...tool import moveToRight, convert_to_mesh, subdivide, newColor, set_vert_group, delete_vert_group, \
    extrude_border_by_vertex_groups

from ..parameters_for_create_mould import get_right_frame_style_hole_border, get_left_frame_style_hole_border

template_highest_point = (-10.3681, 2.2440, 12.1771)


# 获取VIEW_3D区域的上下文
def getOverride():
    area_type = 'VIEW_3D'  # change this to use the correct Area Type context you want to process in
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override


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
        moveToRight(bpy.context.active_object)

        # 为圆环上色
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


def darw_cylinder(outer_dig_border, inner_dig_border):
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
def get_hole_border(template_highest_point, template_hole_border, number):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        dig_border = []  # 被选择的挖孔顶点

        for template_hole_border_point in template_hole_border:  # 通过向z负方向投射找到边界
            # 根据模板旋转的角度，边界顶点也做相应的旋转
            xx = template_hole_border_point[0]
            yy = template_hole_border_point[1]
            origin = (xx, yy, 10)
            direction = (0, 0, -1)
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)
            if hit:
                dig_border.append((loc[0], loc[1], loc[2]))

        order_hole_border_vert = get_order_border_vert(dig_border)

        curve_name = 'HoleBorderCurve' + str(number)
        draw_border_curve(order_hole_border_vert, curve_name, 0.18)
        darw_cylinder_bottom(order_hole_border_vert)

        bpy.ops.object.mode_set(mode='OBJECT')


def dig_hole():
    name = bpy.context.scene.leftWindowObj

    template_hole_border_list = []
    template_highest_point = None
    if (name == "右耳"):
        template_hole_border_list = get_right_frame_style_hole_border()
        template_highest_point = (11.867500305175781, -8.64398193359375, 15.000337600708008)
    elif (name == "左耳"):
        template_hole_border_list = get_left_frame_style_hole_border()
        template_highest_point = (2.7108917236328125, -9.098304748535156, 16.62348747253418)
    # 复制切割补面完成后的物体
    cur_obj = bpy.data.objects[name]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForDigHole"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    moveToRight(duplicate_obj)

    number = len(template_hole_border_list)
    for template_hole_border in template_hole_border_list:
        get_hole_border(template_highest_point, template_hole_border, number)
        translate_circle_to_cylinder()
        # 创建布尔修改器
        boolean_cut()
        local_curve_name = 'HoleBorderCurve' + str(number)
        local_mesh_name = 'mesh' + local_curve_name
        subdivide(local_curve_name, 1)  # 细分曲线，防止曲线的点太少移动时穿模
        convert_to_mesh(local_curve_name, local_mesh_name, 0.18)  # 重新生成网格
        number -= 1

    # for obj in bpy.data.objects:
    #     if obj.name == 'HoleBorderCurve':
    #         obj.name = 'HoleBorderCurve1'
    #         subdivide('HoleBorderCurve1', 3)
    #         convert_to_mesh('HoleBorderCurve1', 'meshHoleBorderCurve1', 0.18)
    #
    #     if obj.name == 'HoleBorderCurve.001':
    #         obj.name = 'HoleBorderCurve2'
    #         subdivide('HoleBorderCurve2', 3)
    #         convert_to_mesh('HoleBorderCurve2', 'meshHoleBorderCurve2', 0.18)

    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]


def darw_cylinder_bottom(order_hole_border_vert):
    # 该变量存储布尔切割的圆柱体的底部
    cut_cylinder_buttom_co = []
    for vert in order_hole_border_vert:
        # 先直接用原坐标，后续尝试法向向外走一段
        co = vert
        cut_cylinder_buttom_co.append([co[0], co[1], co[2] - 1])
    draw_border_curve(cut_cylinder_buttom_co, "HoleCutCylinderBottom", 0)


def translate_circle_to_cylinder():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "HoleCutCylinderBottom":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')
    # 切换回编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.extrude_region_move(
        # todo 50为挤出高度，先写死，后续根据边界最高最低点调整
        TRANSFORM_OT_translate={"value": (0, 0, 12)}
    )
    bpy.ops.mesh.select_all(action='SELECT')
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.hide_set(True)


# 使用布尔修改器
def boolean_cut():
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
    bpy.data.objects["HoleCutCylinderBottom"].hide_set(False)
    bpy.data.objects["HoleCutCylinderBottom"].select_set(True)
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

    number = 0
    for obj in bpy.data.objects:
        if re.match('HoleBorderCurve', obj.name) != None:
            number += 1

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