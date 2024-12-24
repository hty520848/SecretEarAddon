import bpy
import bmesh
import re
from ...tool import set_vert_group, extrude_border_by_vertex_groups, moveToRight, moveToLeft, recover_to_dig, newColor
from ...utils.utils import utils_copy_object, utils_re_color
from .frame_eardrum_smooth import frame_extrude_smooth_initial
from .frame_style_eardrum_dig_hole import extrude_and_set_vert_group
import time
from mathutils import Vector

is_qmesh_finish = False


def update_vert_group():
    name = bpy.context.scene.leftWindowObj
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
        if re.match(name + 'HoleBorderCurve', obj.name) != None:
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

def get_closest_point(bm, source_index, target_index_list):
    source_co = bm.verts[source_index].co[0:3]
    closest_index = None
    closest_distance = 10000000000
    for target_index in target_index_list:
        target_co = bm.verts[target_index].co[0:3]
        # z坐标距离系数0.5用于减小高度的影响，避免最近点找到对侧
        distance = ((source_co[0] - target_co[0]) ** 2 + (source_co[1] - target_co[1]) ** 2 + 0.5 * (
                source_co[2] - target_co[2]) ** 2) ** 0.5
        if distance < closest_distance:
            closest_distance = distance
            closest_index = target_index

    return closest_index


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


def select_between_point(bm, start_index, end_index, route_group_index):
    bm.verts[start_index].select_set(True)
    bm.verts[end_index].select_set(True)

    route_index = set()
    route_index.add(start_index)
    route_index.add(end_index)
    bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
    for v in bm.verts:
        if v.select:
            route_index.add(v.index)

    # 处理终点
    if end_index in route_group_index:
        route_group_index.remove(end_index)

    return route_group_index, route_index


# 获取当前index属于哪个洞，返回对应的下标
def get_index_group(index, group_list):
    for i in range(0, len(group_list)):
        if index in group_list[i]:
            return i

    return None


def move_vertex_forward(bm, source_index, group_list, all_group_index_list):
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
    name = bpy.context.scene.leftWindowObj

    # 复制一份用于后续恢复
    utils_copy_object(name, name + "OriginForFill")

    # n 为孔洞的数量
    n = 0
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            n += 1

    if n == 0:
        return

    move_border()  # 将边界移动一段距离
    # bpy.context.view_layer.objects.active = bpy.data.objects[name]
    # obj = bpy.context.active_object
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # # bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomExtrudeBorderVertex')
    bpy.ops.object.vertex_group_select()
    for i in range(1, n + 1):
        bpy.ops.object.vertex_group_set_active(group='HoleExtrudeBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()

    # 分离出桥接边界
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj = bpy.context.active_object
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != obj.name:
                inner_obj = o
    inner_obj.name = name + "Inner"
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(False)
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = inner_obj

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    bm.verts.ensure_lookup_table()
    bpy.ops.mesh.select_all(action='DESELECT')

    # # 获取底部边界顶点index
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # source_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.select_all(action='DESELECT')
    #
    # # 获取孔边界index
    # for i in range(1, n + 1):
    #     bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
    #     bpy.ops.object.vertex_group_select()
    #
    # target_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.select_all(action='DESELECT')

    # 获取底部边界顶点index
    bpy.ops.object.vertex_group_set_active(group='BottomExtrudeBorderVertex')
    bpy.ops.object.vertex_group_select()
    source_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')

    # 获取孔边界index
    for i in range(1, n + 1):
        bpy.ops.object.vertex_group_set_active(group='HoleExtrudeBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()
    target_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')

    if n > 1:
        # 分组存放孔边界index
        all_index_group_by_hole = list()

        for i in range(1, n + 1):
            # 分别获取每个洞的边界用于判断点所在区域
            # bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
            bpy.ops.object.vertex_group_set_active(group='HoleExtrudeBorderVertex' + str(i))
            bpy.ops.object.vertex_group_select()
            hole_index = [v.index for v in bm.verts if v.select]
            all_index_group_by_hole.append(hole_index)
            bpy.ops.mesh.select_all(action='DESELECT')

        # 只用于处理连接跳跃点之间的顶点
        unprocessed_up_route_index = set()
        unprocessed_up_route_index.update(target_index)

        # 存放未处理的点，用于后续洞之间的桥接
        processed_up_index = set()
        cross_group = list()

        # 按组存放桥接的面边界index
        bridge_face_index_group = list()

        first_index = source_index[0]
        up_first_index = get_closest_point(bm, first_index, target_index)
        now_index = source_index[0]

        # 底边和空洞边界进行桥接
        for i in range(0, len(source_index)):
            bpy.ops.mesh.select_all(action='DESELECT')
            link_index = get_linked_unprocessed_index(bm, now_index, source_index)
            if link_index is not None:
                # 获取最近点
                now_point_closest_index = get_closest_point(bm, now_index, target_index)
                linked_point_closest_index = get_closest_point(bm, link_index, target_index)

                processed_up_index.add(linked_point_closest_index)
                processed_up_index.add(now_point_closest_index)

                # 跨面可能会导致穿模，所以先不填充，记录下数据后续再统一处理
                if get_index_group(linked_point_closest_index, all_index_group_by_hole) != get_index_group(
                        now_point_closest_index, all_index_group_by_hole):
                    cross_group.append((now_index, now_point_closest_index, link_index, linked_point_closest_index))

                else:
                    # 为了防止选出来的点跳跃，选择两个点之间的路径上所有点
                    unprocessed_up_route_index, processed_route_index = select_between_point(bm, now_point_closest_index,
                                                                                             linked_point_closest_index,
                                                                                             unprocessed_up_route_index)

                    target_index = [x for x in target_index if
                                    x not in processed_route_index or x == linked_point_closest_index]
                    processed_up_index.update(processed_route_index)

                    bridge_face_index = list(processed_route_index)
                    bridge_face_index.append(link_index)
                    bridge_face_index.append(now_index)

                    bridge_face_index_group.append(bridge_face_index)

                source_index.remove(now_index)
                now_index = link_index

        # 最后要处理头尾相连的问题
        bpy.ops.mesh.select_all(action='DESELECT')
        last_group = list()
        last_group.append(now_index)
        last_group.append(first_index)
        last_group.append(up_first_index)
        last_group.append(get_closest_point(bm, now_index, target_index))
        bridge_face_index_group.append(last_group)

        for i in range(0, len(bridge_face_index_group)):
            bpy.ops.mesh.select_all(action='DESELECT')
            for index in bridge_face_index_group[i]:
                bm.verts[index].select_set(True)
            for edge in bm.edges:
                if edge.verts[0].select and edge.verts[1].select:
                    edge.select_set(True)
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

            now_move_path = move_vertex_forward(bm, cross_area[1], unprocessed_index_group_by_hole,
                                                all_index_group_by_hole)
            link_move_path = move_vertex_forward(bm, cross_area[3], unprocessed_index_group_by_hole,
                                                 all_index_group_by_hole)

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

    else:
        bottom_index = source_index.copy()
        min_dis, start_index, average_dis, dis_dict = find_start_index(bm, source_index, target_index)
        now_index = start_index
        now_closest_dist = min_dis
        endpoints = list()
        bridge_index_list = [[start_index]]
        not_bridge_index_list = []

        # 底边和空洞边界进行桥接
        # max_dis = average_dis
        max_dis = 10
        for i in range(0, len(source_index)):
            link_index = get_linked_unprocessed_index(bm, now_index, source_index)
            if link_index is not None:
                # link_closest_dist = get_closest_distance(bm, link_index, target_index)
                link_closest_dist = dis_dict[link_index]
                if link_closest_dist > max_dis:
                    # 分界点
                    if now_closest_dist <= max_dis:
                        not_bridge_index = [link_index]
                        not_bridge_index_list.append(not_bridge_index)
                        endpoints.append(now_index)
                    else:
                        not_bridge_index_list[-1].append(link_index)
                else:
                    if now_closest_dist > max_dis:
                        bridge_index = [link_index]
                        bridge_index_list.append(bridge_index)
                        endpoints.append(link_index)
                    else:
                        bridge_index_list[-1].append(link_index)

                source_index.remove(now_index)
                now_index = link_index
                now_closest_dist = link_closest_dist

        if len(endpoints) % 2 != 0:
            # 调试用
            # bpy.ops.mesh.select_all(action='DESELECT')
            # for bridge_index in bridge_index_list:
            #     for index in bridge_index:
            #         bm.verts[index].select_set(True)
            raise ValueError("寻找最近点错误")
    
        count = int(len(endpoints) / 2)
        subdivide_index_list = []
        all_subdivide_index = []
        move_vert_index = []
        for i in range(0, count):
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts[endpoints[i * 2]].select_set(True)
            bm.verts[endpoints[i * 2 + 1]].select_set(True)
            bpy.ops.mesh.edge_face_add()
            dis = (bm.verts[endpoints[i * 2]].co - bm.verts[endpoints[i * 2 + 1]].co).length
            bpy.ops.mesh.subdivide(number_cuts=int(dis))
            verts_index = [v.index for v in bm.verts if v.select]
            subdivide_index_list.append(verts_index)
            all_subdivide_index.extend(verts_index)
            bpy.ops.mesh.select_nth(skip=int(dis / 2) + 1)
            bm.verts.ensure_lookup_table()
            for index in verts_index:
                if bm.verts[index].select:
                    vert_index = index
            move_vert_index.append(vert_index)

        bm.verts.ensure_lookup_table()
        for bridge_index in bridge_index_list:
            for index in bridge_index:
                bm.verts[index].select_set(True)
        for index in target_index:
            bm.verts[index].select_set(True)
        for subdivide_index in subdivide_index_list:
            for index in subdivide_index:
                bm.verts[index].select_set(True)
        for edges in bm.edges:
            if edges.verts[0].select and edges.verts[1].select:
                edges.select_set(True)
        bpy.ops.mesh.bridge_edge_loops()
        # bpy.ops.mesh.looptools_bridge(cubic_strength=1, interpolation='cubic', loft=False, loft_loop=False, min_width=0,
        #                               mode='shortest', remove_faces=True, reverse=False, segments=1, twist=0)
        # bpy.ops.mesh.beautify_fill()
    
        for i in range(0, count):
            bpy.ops.mesh.select_all(action='DESELECT')
            # bm.verts[endpoints[i * 2]].select_set(True)
            # bm.verts[endpoints[i * 2 + 1]].select_set(True)
            for index in subdivide_index_list[i]:
                bm.verts[index].select_set(True)
            for index in not_bridge_index_list[i]:
                bm.verts[index].select_set(True)
            for edge in bm.edges:
                if edge.verts[0].select and edge.verts[1].select:
                    edge.select_set(True)
            bpy.ops.mesh.fill()

    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.beautify_fill()   # 避免一些跨度较大的面
    bpy.ops.mesh.tris_convert_to_quads()
    # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    # 切到边选择模式细分内部边
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    if n == 1:
        for edge in bm.edges:
            if edge.verts[0].index in all_subdivide_index and edge.verts[1].index in all_subdivide_index:
                edge.select_set(False)
    bpy.ops.mesh.subdivide(number_cuts=6, ngon=False, quadcorner='INNERVERT')

    # 回到顶点选择模式
    bpy.ops.mesh.select_mode(type='VERT')
    if n == 1:
        for index in move_vert_index:
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts.ensure_lookup_table()
            bm.verts[index].select_set(True)
            bpy.ops.transform.translate(value=(-0, -0, 3), orient_type='GLOBAL',
                                        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                        constraint_axis=(True, True, True), mirror=True, use_proportional_edit=True,
                                        proportional_edit_falloff='SMOOTH',
                                        proportional_size=closest_bottom_dis(bm, index, bottom_index),
                                        use_proportional_connected=False, use_proportional_projected=False, snap=False,
                                        snap_elements={'FACE'}, use_snap_project=False,
                                        snap_target='CENTER', use_snap_self=True, use_snap_edit=False,
                                        use_snap_nonedit=True, use_snap_selectable=False)  # 顶点移动

    # 平滑
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    # bpy.ops.mesh.vertices_smooth(factor=1, repeat=30)
    smooth_index = [v.index for v in bm.verts if v.select]
    bm.verts.ensure_lookup_table()
    for _ in range(0, 10):
        laplacian_smooth(bm, smooth_index, 1.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.frame.qmesh('INVOKE_DEFAULT')
    return

    # 重新设置上下边界顶点组
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_remove_from()

    # bpy.ops.mesh.select_all(action='SELECT')
    # inner_obj.vertex_groups.new(name="Inner")
    # bpy.ops.object.vertex_group_assign()

    # 设置平滑顶点组
    # bpy.ops.mesh.select_all(action='SELECT')
    # inner_obj.vertex_groups.new(name="SmoothVertex")
    # bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')
    # 合并回主物体
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.loop_to_region()
    obj.vertex_groups.new(name="Inner")
    bpy.ops.object.vertex_group_assign()

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

    # # 更新平滑顶点组，把上下边界加入
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='SmoothVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_assign()
    #
    # # 更新外壁顶点组
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    # bpy.ops.object.vertex_group_remove_from()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()

    # # 添加平滑修改器
    # modifier = obj.modifiers.new(name="Smooth", type='SMOOTH')
    # bpy.context.object.modifiers["Smooth"].iterations = 30
    # bpy.context.object.modifiers["Smooth"].vertex_group = "SmoothVertex"
    # bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    # smooth_border()

    # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    frame_eardrum_smooth_name = name + "FrameEarDrumForSmooth"
    frameeardrum_for_smooth_obj = bpy.data.objects.get(frame_eardrum_smooth_name)
    if (frameeardrum_for_smooth_obj != None):
        bpy.data.objects.remove(frameeardrum_for_smooth_obj, do_unlink=True)
    frameeardrum_for_smooth_obj = obj.copy()
    frameeardrum_for_smooth_obj.data = obj.data.copy()
    frameeardrum_for_smooth_obj.name = obj.name + "FrameEarDrumForSmooth"
    frameeardrum_for_smooth_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(frameeardrum_for_smooth_obj)
    if name == '右耳':
        moveToRight(frameeardrum_for_smooth_obj)
    else:
        moveToLeft(frameeardrum_for_smooth_obj)
    frameeardrum_for_smooth_obj.hide_set(True)
    # 框架式耳膜底部边缘平滑
    frame_extrude_smooth_initial()


def depart_inner_outer():
    main_obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_linked(delimit=set())
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != main_obj.name:
                inner_obj = o
    inner_obj.name = main_obj.name + "Inner"
    bpy.ops.object.select_all(action='DESELECT')
    main_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    return main_obj, inner_obj


def frame_retopo_offset_cut(obj_name, border_vert_group_name, width):
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

    bpy.ops.frameeardrum.smooth(width=width, center_border_group_name=border_vert_group_name)


def bevel_border():
    outer_offset = bpy.context.scene.waiBianYuanSheRuPianYi
    inner_offset = bpy.context.scene.neiBianYuanSheRuPianYi

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    # 分别对内外倒角进行重拓扑
    if outer_offset != 0:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=95, segments=16, affect='EDGES')
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_remove_from()
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
    bpy.ops.mesh.loop_to_region()
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

    # 上边界
    if outer_offset != 0:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=95, segments=16, affect='EDGES')
        bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
        bpy.ops.object.vertex_group_remove_from()
        # 更新顶点组
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove_from()
        for _ in range(int(16 / 2)):  # 16是bevel的segments
            bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_assign()

    # 删除内外壁之间的面，重新桥接
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.loop_to_region()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    if inner_offset != 0:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=95, segments=16, affect='EDGES')
        # 更新顶点组
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove_from()
        for _ in range(int(16 / 2)):  # 16是bevel的segments
            bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    # 平滑着色
    bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=3.14159)


def smooth_border():
    outer_offset = bpy.context.scene.waiBianYuanSheRuPianYi
    inner_offset = bpy.context.scene.neiBianYuanSheRuPianYi
    # 分离出内外壁
    outer_obj, inner_obj = depart_inner_outer()
    # 拓扑外壁下边界
    frame_retopo_offset_cut(outer_obj.name, "BottomOuterBorderVertex", outer_offset)
    # 拓扑外壁上边界
    frame_retopo_offset_cut(outer_obj.name, "UpOuterBorderVertex", outer_offset)
    # 拓扑内壁下边界
    frame_retopo_offset_cut(inner_obj.name, "BottomInnerBorderVertex", inner_offset)
    # 拓扑内壁上边界
    frame_retopo_offset_cut(inner_obj.name, "UpInnerBorderVertex", inner_offset)

    # 合并内外壁
    bpy.ops.object.select_all(action='DESELECT')
    outer_obj.select_set(True)
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = outer_obj
    bpy.ops.object.join()

    # 桥接上线边界
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    # 桥接下线边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    # 调整法向
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    bevel_border()


def recover_and_refill():
    """ 为了调整厚度后重新桥接 """
    name = bpy.context.scene.leftWindowObj
    # 恢复到桥接前
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    cur_obj = bpy.data.objects[name + "OriginForFill"]
    cur_obj.hide_set(False)
    cur_obj.name = name
    bpy.context.view_layer.objects.active = cur_obj

    number = 0
    for obj in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', obj.name) != None:
            number += 1

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.delete(type='VERT')

    # extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")
    #
    # for i in range(1, number + 1):
    #     inside_border_index = extrude_border_by_vertex_groups("HoleBorderVertex" + str(i), "UpInnerBorderVertex")
    #     # 单个孔的内外边界也留一下
    #     set_vert_group("HoleInnerBorderVertex" + str(i), inside_border_index)
    #
    # update_vert_group()
    extrude_and_set_vert_group()
    fill_closest_point()

    utils_re_color(name, (1, 0.319, 0.133))


# ***********************************新增代码***********************************
# def fill_closest_point():
#     name = bpy.context.scene.leftWindowObj
#
#     # 复制一份用于后续恢复
#     utils_copy_object(name, name + "OriginForFill")
#
#     # n 为孔洞的数量
#     n = 0
#     for o in bpy.data.objects:
#         if re.match(name + 'HoleBorderCurve', o.name) != None:
#             n += 1
#
#     bpy.context.view_layer.objects.active = bpy.data.objects[name]
#     obj = bpy.context.active_object
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
#     bpy.ops.object.vertex_group_select()
#     bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
#     bpy.ops.object.vertex_group_select()
#     bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
#
#     # 分离出桥接边界
#     bpy.ops.mesh.separate(type='SELECTED')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     for o in bpy.data.objects:
#         if o.select_get():
#             if o.name != obj.name:
#                 inner_obj = o
#     inner_obj.name = name + "Inner"
#     bpy.ops.object.select_all(action='DESELECT')
#     obj.select_set(False)
#     inner_obj.select_set(True)
#     bpy.context.view_layer.objects.active = inner_obj
#
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bm = bmesh.from_edit_mesh(inner_obj.data)
#     bm.verts.ensure_lookup_table()
#     vert_layer = bm.verts.layers.int.get('FrameVerts')
#     if vert_layer:
#         bm.verts.layers.int.remove('FrameVerts')
#     vert_layer = bm.verts.layers.int.new('FrameVerts')
#
#     # 获取第一个孔洞的边界index
#     bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex1')
#     bpy.ops.object.vertex_group_select()
#     source_index = [v.index for v in bm.verts if v.select]
#     for index in source_index:
#         bm.verts[index][vert_layer] = 1
#     bpy.ops.mesh.select_all(action='DESELECT')
#
#     target_index = []        # 存放待处理的顶点下标
#     unprocessed_index = []   # 存放未处理的底部边界下标
#     # 获取底部和剩余孔洞的边界index
#     bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
#     bpy.ops.object.vertex_group_select()
#     bottom_index = [v.index for v in bm.verts if v.select]
#     for index in bottom_index:
#         bm.verts[index][vert_layer] = 0
#     target_index.extend(bottom_index)
#     unprocessed_index.extend(bottom_index)
#     for i in range(2, n + 1):
#         bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
#         bpy.ops.object.vertex_group_select()
#         vert_index = [v.index for v in bm.verts if v.select]
#         for index in vert_index:
#             bm.verts[index][vert_layer] = i
#         target_index.extend(vert_index)
#
#     bpy.ops.mesh.select_all(action='DESELECT')
#
#     # 存放未处理的点，用于后续洞之间的桥接
#     cross_group = list()
#
#     # 按组存放与底部相连的边界index
#     bridge_face_index_group = list()
#     # 与其余孔洞相连的边界index
#     fill_face_index = set()
#
#     while len(source_index) > 0:
#         # 从孔洞的第一个点开始寻找
#         first_index = source_index[0]
#         first_closest_index = get_closest_point(first_index, target_index)
#         now_index = source_index[0]
#
#         for i in range(0, len(source_index)):
#             bpy.ops.mesh.select_all(action='DESELECT')
#             link_index = get_linked_unprocessed_index(now_index, source_index)
#             if link_index is not None:
#                 # 获取最近点
#                 now_point_closest_index = get_closest_point(now_index, target_index)
#                 linked_point_closest_index = get_closest_point(link_index, target_index)
#
#                 # 跨面可能会导致穿模，所以先不填充，记录下数据后续再统一处理
#                 if bm.verts[now_point_closest_index][vert_layer] != bm.verts[linked_point_closest_index][vert_layer]:
#                     if bm.verts[now_point_closest_index][vert_layer] == 0:
#                         cross_group.append((now_index, now_point_closest_index))
#                     elif bm.verts[linked_point_closest_index][vert_layer] == 0:
#                         cross_group.append((link_index, linked_point_closest_index))
#                     else:
#                         fill_face_index.update(
#                             {now_index, now_point_closest_index, link_index, linked_point_closest_index})
#
#                 else:
#                     if bm.verts[now_point_closest_index][vert_layer] == 0:
#                         # 为了防止选出来的点跳跃，选择两个点之间的路径上所有点
#                         processed_route_index = select_between_point(now_point_closest_index,
#                                                                      linked_point_closest_index)
#
#                         target_index = [x for x in target_index if
#                                         x not in processed_route_index or x == linked_point_closest_index]
#                         unprocessed_index = [x for x in unprocessed_index if x not in processed_route_index]
#
#                         bridge_face_index = list(processed_route_index)
#                         bridge_face_index.append(link_index)
#                         bridge_face_index.append(now_index)
#
#                         bridge_face_index_group.append(bridge_face_index)
#
#                     else:
#                         fill_face_index.update(
#                             {now_index, now_point_closest_index, link_index, linked_point_closest_index})
#
#                 source_index.remove(now_index)
#                 now_index = link_index
#
#         # 最后要处理头尾相连的问题
#         bpy.ops.mesh.select_all(action='DESELECT')
#         now_closest_index = get_closest_point(now_index, target_index)
#         if bm.verts[now_closest_index][vert_layer] != bm.verts[first_closest_index][vert_layer]:
#             if bm.verts[now_closest_index][vert_layer] == 0:
#                 cross_group.append((now_index, now_closest_index))
#             elif bm.verts[first_closest_index][vert_layer] == 0:
#                 cross_group.append((first_index, first_closest_index))
#             else:
#                 fill_face_index.update({now_index, now_closest_index, first_index, first_closest_index})
#         else:
#             if bm.verts[now_closest_index][vert_layer] == 0:
#                 processed_route_index = select_between_point(now_closest_index,
#                                                              first_closest_index)
#                 target_index = [x for x in target_index if x not in processed_route_index or x == first_closest_index]
#                 unprocessed_index = [x for x in unprocessed_index if x not in processed_route_index]
#
#                 bridge_face_index = list(processed_route_index)
#                 bridge_face_index.append(first_index)
#                 bridge_face_index.append(now_index)
#
#                 bridge_face_index_group.append(bridge_face_index)
#
#             else:
#                 fill_face_index.update({now_index, now_closest_index, first_index, first_closest_index})
#         source_index.remove(now_index)
#
#         if n > 1:
#             source_index = [index for index in target_index if bm.verts[index][vert_layer] == n]
#             target_index = [x for x in target_index if x not in source_index]
#             n -= 1
#
#     # 将所有与底部相连的顶点依次桥接
#     for i in range(0, len(bridge_face_index_group)):
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for index in bridge_face_index_group[i]:
#             bm.verts[index].select_set(True)
#         for edge in bm.edges:
#             if edge.verts[0].select and edge.verts[1].select:
#                 edge.select_set(True)
#         bpy.ops.mesh.edge_face_add()
#
#     bpy.ops.mesh.select_all(action='DESELECT')
#
#     # n 为孔洞的数量
#     n = 0
#     for o in bpy.data.objects:
#         if re.match(name + 'HoleBorderCurve', o.name) != None:
#             n += 1
#     if n > 1:
#         while(len(cross_group)) > 0:
#             start_vert_index = cross_group[0][1]
#             start_up_vert_index = cross_group[0][0]
#             route_index, connect_up_index, group_index = find_connect_up_index(start_vert_index,
#                                                                               unprocessed_index,
#                                                                               cross_group)
#             bm.verts[start_vert_index].select_set(True)
#             bm.verts[start_up_vert_index].select_set(True)
#             bm.verts[connect_up_index].select_set(True)
#             for index in route_index:
#                 bm.verts[index].select_set(True)
#             for edge in bm.edges:
#                 if edge.verts[0].select and edge.verts[1].select:
#                     edge.select_set(True)
#             bpy.ops.mesh.edge_face_add()
#             cross_group.pop(0)
#             cross_group.pop(group_index)
#
#
#         # 填充与孔洞相连的顶点
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for index in fill_face_index:
#             bm.verts[index].select_set(True)
#
#         for edge in bm.edges:
#             if edge.verts[0].select and edge.verts[1].select:
#                 edge.select_set(True)
#         bpy.ops.mesh.fill()
#
#
# def select_between_point(start_index, end_index):
#     obj = bpy.context.active_object
#     bpy.ops.object.mode_set(mode='EDIT')
#     bm = bmesh.from_edit_mesh(obj.data)
#
#     bm.verts[start_index].select_set(True)
#     bm.verts[end_index].select_set(True)
#
#     route_index = set()
#     route_index.add(start_index)
#     route_index.add(end_index)
#     bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
#     for v in bm.verts:
#         if v.select:
#             route_index.add(v.index)
#
#     return route_index
#
#
# def find_connect_up_index(start_vert_index, index_group, cross_group):
#     obj = bpy.context.active_object
#     bm = bmesh.from_edit_mesh(obj.data)
#     bm.verts.ensure_lookup_table()
#     route_index = set()
#     route_index.add(start_vert_index)
#     index_group.remove(start_vert_index)
#     while(True):
#         link_vert = [edge.other_vert(bm.verts[start_vert_index]) for edge in bm.verts[start_vert_index].link_edges]
#         for vert in link_vert:
#             if vert.index in index_group:
#                 route_index.add(vert.index)
#                 index_group.remove(vert.index)
#                 start_vert_index = vert.index
#                 break
#             else:
#                 for idx, group in enumerate(cross_group):
#                     if start_vert_index == group[1]:
#                         connect_up_index = group[0]
#                         return route_index, connect_up_index, idx


def laplacian_smooth(bm, smooth_index, factor):
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


def separate_bridge_border():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')  # 这个顶点组包含所有孔洞的边界
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
    # bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
    # 分离出边界
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != obj.name:
                inner_obj = o
    inner_obj.name = name + "Inner"
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(False)
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = inner_obj
    return inner_obj


def join_border(obj, inner_obj):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    inner_obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()


def group_by_distance(bm, inner_obj):
    name = bpy.context.scene.leftWindowObj
    # n 为孔洞的数量
    n = 0
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            n += 1

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    source_loop = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex1')
    bpy.ops.object.vertex_group_select()
    target_loop = [v.index for v in bm.verts if v.select]

    min_dis = find_closest_distance(bm, source_loop, target_loop)
    # 选中与目标顶点距离小于一定范围的顶点进行桥接
    bridge_source_vert_index = bridge_loops_with_distance(bm, min_dis * 2, target_loop, source_loop)
    # bridge_source_vert_index = bridge_loops_with_distance(10, target_loop, source_loop)
    not_bridge_source_vert_index = [index for index in source_loop if index not in bridge_source_vert_index]
    endpoints = []
    bm.verts.ensure_lookup_table()
    for index in bridge_source_vert_index:
        vert = bm.verts[index]
        connected_edges = [e for e in vert.link_edges if e.other_vert(vert).index in bridge_source_vert_index]
        if len(connected_edges) == 1:
            endpoints.append(vert.index)
        elif len(connected_edges) == 0:
            bridge_source_vert_index.remove(index)
            not_bridge_source_vert_index.append(index)

    if len(not_bridge_source_vert_index) == 0:
        # 上下边界直接桥接
        bpy.ops.mesh.select_all(action='SELECT')
        return False

    else:
        # 桥接选中的上下边界中的顶点
        # bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
        # bpy.ops.mesh.looptools_bridge(cubic_strength=1, interpolation='cubic', loft=False, loft_loop=False,
        #                               min_width=0, mode='shortest', remove_faces=True, reverse=False, segments=1,
        #                               twist=0)
        if len(endpoints) == 4:
            bpy.ops.mesh.select_all(action='DESELECT')
            connect_endpoints, route_index = group_endpoints(bm, endpoints, not_bridge_source_vert_index)
            if connect_endpoints != []:
                # add_face_between_end_points(bm, connect_endpoints, target_loop)
                for index in connect_endpoints:
                    bm.verts[index].select = True
                bpy.ops.mesh.edge_face_add()
                bpy.ops.mesh.select_all(action='DESELECT')

                another_connect_endpoints = [endpoints for endpoints in endpoints if endpoints not in connect_endpoints]
                # add_face_between_end_points(bm, another_connect_endpoints, target_loop)
                for index in another_connect_endpoints:
                    bm.verts[index].select = True
                bpy.ops.mesh.edge_face_add()

                for index in connect_endpoints:
                    bm.verts[index].select = True
                for index in bridge_source_vert_index:
                    bm.verts[index].select = True
                for index in target_loop:
                    bm.verts[index].select = True
                for edge in bm.edges:
                    if edge.verts[0].select and edge.verts[1].select:
                        edge.select_set(True)
                bpy.ops.mesh.bridge_edge_loops()

                another_route_index = [index for index in not_bridge_source_vert_index if index not in route_index]
                fill_not_bridge_source_vert(bm, connect_endpoints, route_index)
                fill_not_bridge_source_vert(bm, another_connect_endpoints, another_route_index)
                bpy.ops.mesh.select_all(action='SELECT')
            return True

        elif len(endpoints) == 2:
            bpy.ops.mesh.select_all(action='DESELECT')
            # add_face_between_end_points(bm, endpoints, target_loop)
            for index in endpoints:
                bm.verts[index].select = True
            bpy.ops.mesh.edge_face_add()

            for index in bridge_source_vert_index:
                bm.verts[index].select = True
            for index in target_loop:
                bm.verts[index].select = True
            for edge in bm.edges:
                if edge.verts[0].select and edge.verts[1].select:
                    edge.select_set(True)
            bpy.ops.mesh.bridge_edge_loops()

            fill_not_bridge_source_vert(bm, endpoints, not_bridge_source_vert_index)
            bpy.ops.mesh.select_all(action='SELECT')
            return True

        else:
            if len(endpoints) % 2 != 0:
                raise ValueError("寻找最近点错误")
            else:
                print("端点数大于4, 特殊处理")
                pass


def find_closest_distance(bm, source_loop, target_loop):
    min_dis = float('inf')
    for source_idx in source_loop:
        source_vert = bm.verts[source_idx]
        for target_idx in target_loop:
            target_vert = bm.verts[target_idx]
            # dis = ((source_vert.co[0] - target_vert.co[0]) ** 2 + (source_vert.co[1] - target_vert.co[1]) ** 2 + 0.5 * (
            #     source_vert.co[2] - target_vert.co[2]) ** 2) ** 0.5
            dis = (source_vert.co - target_vert.co).length
            if dis < min_dis:
                min_dis = dis
    return min_dis


def bridge_loops_with_distance(bm, max_distance, target_index, source_index):
    # 找到与目标顶点最接近的源顶点进行桥接
    bridge_source_index = []
    for source_idx in source_index:
        closest_idx = None
        min_dist = float('inf')
        source_vert = bm.verts[source_idx]

        for target_idx in target_index:
            target_vert = bm.verts[target_idx]
            # dist = ((source_vert.co[0] - target_vert.co[0]) ** 2 + (source_vert.co[1] - target_vert.co[1]) ** 2 + 0.5 * (
            #     source_vert.co[2] - target_vert.co[2]) ** 2) ** 0.5
            dist = (source_vert.co - target_vert.co).length
            if dist < min_dist and dist <= max_distance:
                min_dist = dist
                closest_idx = source_idx

        if closest_idx:
            bridge_source_index.append(closest_idx)

    # for target_idx in target_index:
    #     bm.verts[target_idx].select = True
    # for bridge_index in bridge_source_index:
    #     bm.verts[bridge_index].select = True
    # for edge in bm.edges:
    #     if edge.verts[0].select and edge.verts[1].select:
    #         edge.select_set(True)
    return bridge_source_index


def group_endpoints(bm, endpoints, not_bridge_source_vert_index):
    route_index = []
    first_endpoint_index = endpoints[0]
    visited = set()
    while True:
        visited.add(first_endpoint_index)
        link_vert = [edge.other_vert(bm.verts[first_endpoint_index]) for edge in bm.verts[first_endpoint_index].link_edges]

        for vert in link_vert:
            if vert.index == endpoints[1]:
                return [endpoints[0], endpoints[1]], route_index
            elif vert.index == endpoints[2]:
                return [endpoints[0], endpoints[2]], route_index
            elif vert.index == endpoints[3]:
                return [endpoints[0], endpoints[3]], route_index
            else:
                if vert.index in not_bridge_source_vert_index and vert.index not in visited:
                    first_endpoint_index = vert.index
                    route_index.append(first_endpoint_index)
                    break  # 重新开始循环，避免继续处理同一顶点
        else:
            # 如果没有找到新的顶点，退出循环
            break


def add_face_between_end_points(bm, endpoints, target_loop):
    bpy.ops.mesh.select_all(action='DESELECT')
    # 找到孔洞边界中与端点相连的两个顶点并选中
    for index in endpoints:
        for edge in bm.verts[index].link_edges:
            if edge.other_vert(bm.verts[index]).index in target_loop:
                edge.other_vert(bm.verts[index]).select = True

    for index in endpoints:
        bm.verts[index].select = True
    for edge in bm.edges:
        if edge.verts[0].select and edge.verts[1].select:
            edge.select_set(True)
    bpy.ops.mesh.edge_face_add()


def fill_not_bridge_source_vert(bm, endpoints, not_bridge_source_vert_index):
    bpy.ops.mesh.select_all(action='DESELECT')
    for index in endpoints:
        for edge in bm.verts[index].link_edges:
            if edge.other_vert(bm.verts[index]).index in not_bridge_source_vert_index:
                edge.select_set(True)
                edge.other_vert(bm.verts[index]).select = True
            elif edge.other_vert(bm.verts[index]).index in endpoints:
                edge.select_set(True)

    bpy.ops.mesh.edge_face_add()
    for index in endpoints:
        bm.verts[index].select = False

    count = int(len(not_bridge_source_vert_index) / 2) + 2
    while (count > 0):
        bpy.ops.mesh.edge_face_add()
        count = count - 1


def connect_possible_vertex(bm, vertex_indices, bridge_source_vert_index):
    min_len = float('inf')
    pair = []
    for i in range(len(vertex_indices)):
        for j in range(i + 1, len(vertex_indices)):
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts[vertex_indices[i]].select = True
            bm.verts[vertex_indices[j]].select = True
            bpy.ops.mesh.shortest_path_select()
            selected_verts = [v.index for v in bm.verts if v.select]
            if len(selected_verts) == 0:
                continue
            for index in selected_verts:
                if index in bridge_source_vert_index:
                    continue
            if len(selected_verts) < min_len:
                min_len = len(selected_verts)
                pair = [vertex_indices[i], vertex_indices[j]]
    return pair


def find_start_index(bm, source_loop, target_loop):
    closest_dis = float('inf')
    closest_index = None
    sum_dis =  0
    min_dis_dict = {}
    for source_idx in source_loop:
        source_vert = bm.verts[source_idx]
        min_dis = float('inf')
        for target_idx in target_loop:
            target_vert = bm.verts[target_idx]
            dis = ((source_vert.co[0] - target_vert.co[0]) ** 2 + (source_vert.co[1] - target_vert.co[1]) ** 2 + 0.5 * (
                source_vert.co[2] - target_vert.co[2]) ** 2) ** 0.5
            if dis < min_dis:
                min_dis = dis
        sum_dis += min_dis
        min_dis_dict[source_idx] = min_dis
        if min_dis < closest_dis:
            closest_dis = min_dis
            closest_index = source_idx
    return closest_dis, closest_index, sum_dis/len(source_loop), min_dis_dict


def get_closest_distance(bm, source_idx, target_loop):
    min_dis = float('inf')
    source_vert = bm.verts[source_idx]
    for target_idx in target_loop:
        target_vert = bm.verts[target_idx]
        dis = ((source_vert.co[0] - target_vert.co[0]) ** 2 + (source_vert.co[1] - target_vert.co[1]) ** 2 + 0.5 * (
            source_vert.co[2] - target_vert.co[2]) ** 2) ** 0.5
        if dis < min_dis:
            min_dis = dis
    return min_dis


def closest_bottom_dis(bm, index, bottom_index):
    min_dis = float('inf')
    vert = bm.verts[index]
    for bottom_idx in bottom_index:
        bottom_vert = bm.verts[bottom_idx]
        dis = (vert.co - bottom_vert.co).length
        if dis < min_dis:
            min_dis = dis
    return min_dis


def move_border():
    name = bpy.context.scene.leftWindowObj
    n = 0
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            n += 1

    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.active_object
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.duplicate_move(TRANSFORM_OT_translate={"value": (0, 0, 0.5)})
    bpy.ops.object.vertex_group_remove_from()
    obj.vertex_groups.new(name="BottomExtrudeBorderVertex")
    bpy.ops.object.vertex_group_assign()

    for i in range(1, n + 1):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.duplicate_move(TRANSFORM_OT_translate={"value": (0, 0, -0.5)})
        bpy.ops.object.vertex_group_remove_from()
        obj.vertex_groups.new(name="HoleExtrudeBorderVertex" + str(i))
        bpy.ops.object.vertex_group_assign()


def smooth_and_bridge(inner_obj):
    name = bpy.context.scene.leftWindowObj
    n = 0
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            n += 1

    main_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    inner_obj.vertex_groups.new(name="BridgeVerts")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    bm.verts.ensure_lookup_table()
    border_verts_index = [v.index for v in bm.verts if v.is_boundary]
    count = 0
    vertex_group_dict = {}
    while (len(border_verts_index) > 0):
        start_vert_index = border_verts_index[0]
        bm.verts[start_vert_index].select = True
        border_verts_index.remove(start_vert_index)
        count += 1
        now_vert_index = get_linked_unprocessed_index(bm, start_vert_index, border_verts_index)
        while (now_vert_index != None):
            bm.verts[now_vert_index].select = True
            border_verts_index.remove(now_vert_index)
            now_vert_index = get_linked_unprocessed_index(bm, now_vert_index, border_verts_index)
        select_verts_index = [v.index for v in bm.verts if v.select]
        center = sum([bm.verts[index].co for index in select_verts_index], Vector()) / len(select_verts_index)
        vertex_group_dict["BorderVerts" + str(count)] = center
        inner_obj.vertex_groups.new(name="BorderVerts" + str(count))
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    inner_obj.select_set(True)
    main_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(main_obj.data)

    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bm.verts.ensure_lookup_table()
    bottom_index = [v.index for v in bm.verts if v.select]
    bottom_center = sum([bm.verts[index].co for index in bottom_index], Vector()) / len(bottom_index)
    min_dis = float('inf')
    min_key = None
    for key in vertex_group_dict:
        center = vertex_group_dict[key]
        dis = (center - bottom_center).length
        if dis < min_dis:
            min_dis = dis
            min_key = key
    vertex_group_dict.pop(min_key)
    bpy.ops.object.vertex_group_set_active(group=min_key)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    for i in range(1, n + 1):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()
        bm.verts.ensure_lookup_table()
        hole_index = [v.index for v in bm.verts if v.select]
        hole_center = sum([bm.verts[index].co for index in hole_index], Vector()) / len(hole_index)
        min_dis = float('inf')
        min_key = None
        for key in vertex_group_dict:
            center = vertex_group_dict[key]
            dis = (center - hole_center).length
            if dis < min_dis:
                min_dis = dis
                min_key = key
        vertex_group_dict.pop(min_key)
        bpy.ops.object.vertex_group_set_active(group=min_key)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group="BridgeVerts")
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=10)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.loop_to_region()
    main_obj.vertex_groups.new(name="Inner")
    bpy.ops.object.vertex_group_assign()

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

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()

    # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    frame_eardrum_smooth_name = name + "FrameEarDrumForSmooth"
    frameeardrum_for_smooth_obj = bpy.data.objects.get(frame_eardrum_smooth_name)
    if (frameeardrum_for_smooth_obj != None):
        bpy.data.objects.remove(frameeardrum_for_smooth_obj, do_unlink=True)
    frameeardrum_for_smooth_obj = obj.copy()
    frameeardrum_for_smooth_obj.data = obj.data.copy()
    frameeardrum_for_smooth_obj.name = obj.name + "FrameEarDrumForSmooth"
    frameeardrum_for_smooth_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(frameeardrum_for_smooth_obj)
    if name == '右耳':
        moveToRight(frameeardrum_for_smooth_obj)
    else:
        moveToLeft(frameeardrum_for_smooth_obj)
    frameeardrum_for_smooth_obj.hide_set(True)
    # 框架式耳膜底部边缘平滑
    frame_extrude_smooth_initial()


class FrameBorderQmesh(bpy.types.Operator):
    bl_idname = "frame.qmesh"
    bl_label = "框架式耳膜补面时将内边界重拓扑"

    def __init__(self):
        self.start_time = None

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)  # 进入modal模式
        bpy.context.scene.qremesher.use_materials = True
        bpy.context.scene.qremesher.target_count = 600
        bpy.context.scene.qremesher.autodetect_hard_edges = False
        # bpy.context.scene.qremesher.adaptive_size = 100
        bpy.ops.qremesher.remesh()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_qmesh_finish
        name = context.scene.leftWindowObj
        operator_name = name + "Inner"
        retopo_name = "Retopo_" + operator_name
        if self.start_time is None:
            self.start_time = time.time()

        current_time = time.time()
        elapsed_time = current_time - self.start_time
        if bpy.data.objects.get(retopo_name) != None and not is_qmesh_finish:
            is_qmesh_finish = True
            retopo_obj = bpy.data.objects.get(retopo_name)
            bpy.data.objects.remove(bpy.data.objects[operator_name], do_unlink=True)
            retopo_obj.name = operator_name
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = retopo_obj
            retopo_obj.select_set(True)
            try:
                smooth_and_bridge(retopo_obj)
            except:
                recover_to_dig()
                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])
            is_qmesh_finish = False
            return {'FINISHED'}

        if elapsed_time > 2.0:
            print("Qmesh超时")
            bpy.data.objects.remove(bpy.data.objects[operator_name], do_unlink=True)
            recover_to_dig()
            return {'FINISHED'}

        return {'PASS_THROUGH'}


def register():
    bpy.utils.register_class(FrameBorderQmesh)


def unregister():
    bpy.utils.unregister_class(FrameBorderQmesh)
