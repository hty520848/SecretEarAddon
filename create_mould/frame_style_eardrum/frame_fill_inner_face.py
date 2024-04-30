import bpy
import bmesh
import re
from ...tool import set_vert_group
from ...utils.utils import utils_copy_object


def update_vert_group():
    bpy.ops.object.mode_set(mode='EDIT')
    # 底部外边界顶点组把内边界也选上了
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    # 同理，上部外边界也是
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    # 还需要处理HoleBorderVertex，将其改到内边界去，用于后续桥接
    number = 0
    for obj in bpy.data.objects:
        if re.match('HoleBorderCurve', obj.name) != None:
            number += 1

    for i in range(1, number + 1):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HoleBorderVertex' + str(i))
        bpy.ops.object.vertex_group_remove_from()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


# ***********************************桥接最近点方案***********************************

def get_closest_point(source_index, target_index_list):
    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    source_co = bm.verts[source_index].co[0:3]
    closest_index = None
    closest_distance = 10000000000
    for target_index in target_index_list:
        target_co = bm.verts[target_index].co[0:3]
        distance = ((source_co[0] - target_co[0]) ** 2 + (source_co[1] - target_co[1]) ** 2 + (
                source_co[2] - target_co[2]) ** 2) ** 0.5
        if distance < closest_distance:
            closest_distance = distance
            closest_index = target_index

    return closest_index


def get_linked_unprocessed_index(now_index, source_index):
    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
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


def select_between_point(start_index, end_index, route_group_index):
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    now_point = bm.verts[start_index]

    route_index = set()

    while (now_point.index != end_index):
        now_point.select_set(True)
        route_index.add(now_point.index)
        if now_point.index in route_group_index:
            route_group_index.remove(now_point.index)

        next_point_group_index = list()
        # 获取路径上的相邻点
        for edge in now_point.link_edges:
            # 获取边的顶点
            v1 = edge.verts[0]
            v2 = edge.verts[1]
            # 确保获取的顶点不是当前顶点
            link_vert = v1 if v1 != now_point else v2
            if link_vert.index in route_group_index:
                next_point_group_index.append(link_vert.index)

        if len(next_point_group_index) == 1:
            now_point = bm.verts[next_point_group_index[0]]
        # 左右两边都找到的话，选离终点最近的
        elif len(next_point_group_index) > 1:
            now_point = bm.verts[get_closest_point(end_index, next_point_group_index)]
        else:
            break
    # 处理终点
    bm.verts[end_index].select_set(True)
    route_index.add(end_index)
    if end_index in route_group_index:
        route_group_index.remove(end_index)

    return route_group_index, route_index


# 获取当前index属于哪个洞，返回对应的下标
def get_index_group(index, group_list):
    for i in range(0, len(group_list)):
        if index in group_list[i]:
            return i

    return None


def move_vertex_forward(source_index, group_list, all_group_index_list):
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    route_index = group_list[get_index_group(source_index, all_group_index_list)]
    path_index = list()

    now_index = source_index
    # 需要算上头尾
    length = len(route_index) + 2
    # 向前走1/3路程
    for i in range(0, round(length / 5)):
        # 把当前下标加入路径
        path_index.append(now_index)
        # 寻找下一个顶点
        now_point = bm.verts[now_index]
        for edge in now_point.link_edges:
            # 获取边的顶点
            v1 = edge.verts[0]
            v2 = edge.verts[1]
            # 确保获取的顶点不是当前顶点
            link_vert = v1 if v1 != now_point else v2
            if link_vert.index in route_index and link_vert.index not in path_index:
                now_index = link_vert.index
                break

    path_index.append(now_index)

    return path_index


def fill_closest_point():
    # 复制一份用于后续恢复
    utils_copy_object("右耳", "右耳OriginForFill")

    # n 为孔洞的数量
    n = 0
    for o in bpy.data.objects:
        if re.match('HoleBorderCurve', o.name) != None:
            n += 1

    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取底部边界顶点index
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    source_index = [v.index for v in bm.verts if v.select]

    bpy.ops.mesh.select_all(action='DESELECT')

    # 获取孔边界index 因为有多个洞 后续改成for循环
    for i in range(1,n+1):
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()

    target_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')

    # 分组存放孔边界index
    all_index_group_by_hole = list()

    for i in range(1,n+1):
        # 分别获取每个洞的边界用于判断点所在区域
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()
        hole_index = [v.index for v in bm.verts if v.select]
        all_index_group_by_hole.append(hole_index)
        bpy.ops.mesh.select_all(action='DESELECT')


    # 只用于处理连接跳跃点之间的顶点
    unprocessed_up_route_index = list()
    unprocessed_up_route_index.extend(target_index)

    # 存放未处理的点，用于后续洞之间的桥接
    processed_up_index = set()
    cross_group = list()

    first_index = source_index[0]
    now_index = source_index[0]

    # 底边和空洞边界进行桥接
    for i in range(0, len(source_index)):
        # for i in range(0,2):
        bpy.ops.mesh.select_all(action='DESELECT')
        link_index = get_linked_unprocessed_index(now_index, source_index)
        if link_index is not None:
            now_point_closest_index = get_closest_point(now_index, target_index)
            linked_point_closest_index = get_closest_point(link_index, target_index)

            processed_up_index.add(linked_point_closest_index)
            processed_up_index.add(now_point_closest_index)

            # 跨面可能会导致穿模，所以先不填充，记录下数据后续再统一处理
            if get_index_group(linked_point_closest_index, all_index_group_by_hole) != get_index_group(
                    now_point_closest_index, all_index_group_by_hole):
                cross_group.append((now_index, now_point_closest_index, link_index, linked_point_closest_index))

            else:
                # 为了防止选出来的点跳跃，选择两个点之间的路径上所有点
                unprocessed_up_route_index, processed_route_index = select_between_point(now_point_closest_index,
                                                                                         linked_point_closest_index,
                                                                                         unprocessed_up_route_index)
                processed_up_index.update(processed_route_index)
                link_set = set()
                for edge in bm.verts[now_point_closest_index].link_edges:
                    link_set.add(edge.verts[0].index)
                    link_set.add(edge.verts[1].index)

                bm.verts[link_index].select_set(True)
                bm.verts[now_index].select_set(True)
                bpy.ops.mesh.edge_face_add()

            source_index.remove(now_index)

            now_index = link_index

    # 最后要处理头尾相连的问题
    bm.verts[now_index].select_set(True)
    bm.verts[first_index].select_set(True)
    bm.verts[get_closest_point(first_index, target_index)].select_set(True)
    bm.verts[get_closest_point(now_index, target_index)].select_set(True)
    bpy.ops.mesh.edge_face_add()

    bpy.ops.mesh.select_all(action='DESELECT')

    # 区分未处理的顶点分属于哪个孔
    # n 为孔洞的数量
    unprocessed_index_group_by_hole = [[] for _ in range(n)]
    # 分类未处理的顶点
    for i in target_index:
        if i not in processed_up_index:
            unprocessed_index_group_by_hole[get_index_group(i, all_index_group_by_hole)].append(i)

    move_end_point = list()
    # 处理跨越区域
    for cross_area in cross_group:

        bm.verts[cross_area[0]].select_set(True)
        bm.verts[cross_area[1]].select_set(True)
        bm.verts[cross_area[2]].select_set(True)
        bm.verts[cross_area[3]].select_set(True)
        # t = [v for v in bm.verts if v.select]

        now_move_path = move_vertex_forward(cross_area[1], unprocessed_index_group_by_hole, all_index_group_by_hole)
        link_move_path = move_vertex_forward(cross_area[3], unprocessed_index_group_by_hole, all_index_group_by_hole)

        move_end_point.append(now_move_path[-1])
        move_end_point.append(link_move_path[-1])

        bpy.ops.mesh.select_all(action='DESELECT')
        for index in now_move_path:
            bm.verts[index].select_set(True)
        bm.verts[cross_area[0]].select_set(True)
        bpy.ops.mesh.edge_face_add()
        processed_up_index.update(now_move_path)

        bpy.ops.mesh.select_all(action='DESELECT')
        for index in link_move_path:
            bm.verts[index].select_set(True)
        bm.verts[cross_area[2]].select_set(True)
        bpy.ops.mesh.edge_face_add()
        processed_up_index.update(link_move_path)

        bpy.ops.mesh.select_all(action='DESELECT')
        bm.verts[cross_area[0]].select_set(True)
        bm.verts[cross_area[2]].select_set(True)
        bm.verts[now_move_path[-1]].select_set(True)
        bm.verts[link_move_path[-1]].select_set(True)
        bpy.ops.mesh.edge_face_add()

    # 填充未连上的顶点
    bpy.ops.mesh.select_all(action='DESELECT')
    for index in target_index:
        if index not in processed_up_index:
            bm.verts[index].select_set(True)
    for index in move_end_point:
        bm.verts[index].select_set(True)

    for edge in bm.edges:
        if edge.verts[0].select and edge.verts[1].select:
            edge.select_set(True)
    bpy.ops.mesh.fill()

    # 开始细分平滑重拓扑
    for i in range(1, n+1):
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.subdivide()
    bpy.ops.mesh.subdivide()
    bpy.ops.mesh.subdivide()

    bpy.ops.mesh.remove_doubles(threshold=0.2)
    inner_face = [v.index for v in bm.verts if v.select]

    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("inner", inner_face)

    # 添加平滑修改器
    modifier = obj.modifiers.new(name="Smooth", type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].iterations = 30
    bpy.context.object.modifiers["Smooth"].vertex_group = "inner"
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    # bpy.context.scene.qremesher.autodetect_hard_edges = False
    # bpy.ops.qremesher.remesh()

    # # bpy.data.objects.remove(obj, do_unlink=True)
    # obj = bpy.context.active_object
