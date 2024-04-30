import bpy
import math
import bmesh
import mathutils

from ..tool import set_vert_group,delete_vert_group
from ..utils.utils import utils_draw_curve, utils_get_order_border_vert,utils_bool_difference


# ****************************** 这里复用了切割的代码，但做了修改 ******************************
def judge_normals():
    cut_plane = bpy.data.objects["CutPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)
    sum = 0
    for v in cut_plane_mesh.verts:
        sum += v.normal[2]
    return sum < 0


def get_cut_plane():
    main_obj = bpy.context.active_object
    # 外边界顶点组
    bpy.ops.object.select_all(action='DESELECT')
    cut_plane_outer = bpy.data.objects["CutPlane"]
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_outer.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Outer", vert_index)

    # 中间边界顶点组
    bpy.data.objects["CutPlane"].select_set(False)
    cut_plane_center = bpy.data.objects["Center"]
    bpy.context.view_layer.objects.active = cut_plane_center
    cut_plane_center.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_center.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Center", vert_index)

    # 内边界顶点组
    bpy.data.objects["Center"].select_set(False)
    cut_plane_inner = bpy.data.objects["Inner"]
    bpy.context.view_layer.objects.active = cut_plane_inner
    cut_plane_inner.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_inner.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Inner", vert_index)

    # 合并
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    cut_plane_center.select_set(True)
    cut_plane_inner.select_set(True)
    bpy.ops.object.join()

    # 拼接成面
    bpy.ops.object.mode_set(mode='EDIT')
    # 最内补面
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.edge_face_add()
    # 桥接内中边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='Center')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    # 桥接中外边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Outer')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='Center')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='SELECT')
    if judge_normals():
        bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects["CutPlane"].select_set(False)
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)


def plane_cut(border_vert_group_name):
    # 获取活动对象
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    # 存一下原先的顶点
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    ori_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    set_vert_group("all", ori_border_index)

    utils_bool_difference(obj.name, "CutPlane")

    # 获取下边界顶点用于挤出
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='all')
    # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    # 创建bmesh对象
    bm = bmesh.from_edit_mesh(obj.data)
    bottom_outer_border_index = [v.index for v in bm.verts if v.select]

    ori_obj = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    delete_vert_group("all")
    # 将下边界加入顶点组
    bottom_outer_border_vertex = ori_obj.vertex_groups.get(border_vert_group_name)
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name=border_vert_group_name)
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')


def judge_if_need_invert():
    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def delete_useless_part(border_vert_group_name):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.loop_to_region()

    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        bpy.ops.mesh.delete(type='FACE')


    # 最后，删一下边界的直接的面
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = obj.vertex_groups.get(border_vert_group_name)
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects.remove(bpy.data.objects["CutPlane"], do_unlink=True)


# ****************************** 复用结束 ******************************

def get_move_direction(plane_name):
    obj = bpy.data.objects[plane_name]

    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(obj.data)
    normal_x = 0
    normal_y = 0
    normal_z = 0

    size = len(bm.verts)

    for v in bm.verts:
        normal_x += v.normal[0]
        normal_y += v.normal[1]
        normal_z += v.normal[2]

    return (normal_x / size, normal_y / size, normal_z / size)


def retopo(name, border_vert_group_name, width):
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    retopo_border_co = list()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.2)

    mesh = obj.data
    bm = bmesh.from_edit_mesh(obj.data)

    border_co = [v.co[0:3] for v in bm.verts if v.select]

    co_for_cut = list()
    co_for_cut.extend(border_co)

    now_border_co = utils_get_order_border_vert(border_co)

    move_direction = get_move_direction("RetopoPlane")
    step = 0.5

    bpy.ops.object.mode_set(mode='OBJECT')
    # 最后一次要特殊处理，做出一个用于切割的平面，所以单独拿出来
    # 这里的循环次数就是总厚度/step -1
    for i in range(0, 4 - 1):
        retopo_border_co.append(now_border_co)
        temp_border_co = list()
        for co in now_border_co:
            temp_co = \
                (co[0] + move_direction[0] * step, co[1] + move_direction[1] * step, co[2] + move_direction[2] * step)
            _, closest_co, closest_normal, _ = obj.closest_point_on_mesh(mathutils.Vector(temp_co))
            temp_border_co.append(closest_co[0:3])

        now_border_co = temp_border_co

        # 用排序好的点画切割平面可能会有问题，所以切割和后续画圈补面的要分开
        temp_border_co = list()
        for co in co_for_cut:
            temp_co = (
            co[0] + move_direction[0] * step, co[1] + move_direction[1] * step, co[2] + move_direction[2] * step)
            _, closest_co, closest_normal, _ = obj.closest_point_on_mesh(mathutils.Vector(temp_co))
            temp_border_co.append(closest_co[0:3])

        co_for_cut = temp_border_co

    # 单独处理最后一次
    retopo_border_co.append(now_border_co)

    plane_center_border_co = list()
    plane_inner_border_co = list()
    plane_outer_border_co = list()
    for co in co_for_cut:
        temp_co = (co[0] + move_direction[0] * step, co[1] + move_direction[1] * step, co[2] + move_direction[2] * step)
        _, closest_co, closest_normal, _ = obj.closest_point_on_mesh(mathutils.Vector(temp_co))

        plane_center_border_co.append(closest_co[0:3])
        plane_inner_border_co.append((
            closest_co[0] - closest_normal[0] * step, closest_co[1] - closest_normal[1] * step,
            closest_co[2] - closest_normal[2] * step))
        plane_outer_border_co.append((
            closest_co[0] + closest_normal[0] * 0.6, closest_co[1] + closest_normal[1] * 0.6,
            closest_co[2] + closest_normal[2] * 0.6))

    utils_draw_curve(utils_get_order_border_vert(plane_center_border_co), "Center", 0)
    utils_draw_curve(utils_get_order_border_vert(plane_inner_border_co), "Inner", 0)
    utils_draw_curve(utils_get_order_border_vert(plane_outer_border_co), "CutPlane", 0)

    # 与软耳膜相同，切掉要重拓扑的部分
    get_cut_plane()
    plane_cut(border_vert_group_name)
    delete_useless_part(border_vert_group_name)

    # 翻转一下，一层层来
    retopo_border_co = retopo_border_co[::-1]

    for border_co in retopo_border_co:
        bridge_topo(border_co, border_vert_group_name)
    # bridge_topo(retopo_border_co[0], border_vert_group_name)

    bpy.ops.object.mode_set(mode='OBJECT')


def bridge_topo(border_co, border_vert_group_name):
    main_obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    utils_draw_curve(border_co, "border", 0)

    main_obj.select_set(False)
    border = bpy.data.objects["border"]
    bpy.context.view_layer.objects.active = border
    border.select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 将边界合并到主物体
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    border.select_set(True)
    bpy.ops.object.join()

    mesh = main_obj.data
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(mesh)
    set_vert_group('temp', [v.index for v in bm.verts if v.select])

    # 进行桥接
    bpy.ops.object.mode_set(mode='EDIT')
    # 分别按距离合并，不然可能和到一起

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_select()

    bpy.ops.object.vertex_group_set_active(group='temp')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='temp')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.2)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.2)

    # 删除辅助顶点组，将底部边界顶点组外移
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='temp')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_assign()
    delete_vert_group('temp')
