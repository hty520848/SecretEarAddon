import bpy
import bmesh
import re
from ...tool import set_vert_group, extrude_border_by_vertex_groups
from ...utils.utils import utils_copy_object, utils_re_color


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
    bm.verts.ensure_lookup_table()
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
    name = bpy.context.scene.leftWindowObj

    # 复制一份用于后续恢复
    utils_copy_object(name, name + "OriginForFill")

    # n 为孔洞的数量
    n = 0
    for o in bpy.data.objects:
        if re.match(name + 'HoleBorderCurve', o.name) != None:
            n += 1

    bpy.context.view_layer.objects.active = bpy.data.objects[name]
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)

    # 分离出桥接边界
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

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(inner_obj.data)

    # 获取底部边界顶点index
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    source_index = [v.index for v in bm.verts if v.select]

    bpy.ops.mesh.select_all(action='DESELECT')

    # 获取孔边界index
    for i in range(1, n + 1):
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
        bpy.ops.object.vertex_group_select()

    target_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')

    # 分组存放孔边界index
    all_index_group_by_hole = list()

    for i in range(1, n + 1):
        # 分别获取每个洞的边界用于判断点所在区域
        bpy.ops.object.vertex_group_set_active(group='HoleInnerBorderVertex' + str(i))
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
    up_first_index = get_closest_point(first_index, target_index)
    now_index = source_index[0]

    # 底边和空洞边界进行桥接
    for i in range(0, len(source_index)):
        bpy.ops.mesh.select_all(action='DESELECT')
        link_index = get_linked_unprocessed_index(now_index, source_index)
        if link_index is not None:
            # 获取最近点
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
    last_group.append(get_closest_point(now_index, target_index))
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

    if n > 1:
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

            now_move_path = move_vertex_forward(cross_area[1], unprocessed_index_group_by_hole, all_index_group_by_hole)
            link_move_path = move_vertex_forward(cross_area[3], unprocessed_index_group_by_hole,
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

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    # 切到边选择模式细分内部边
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.subdivide(number_cuts=10, ngon=False, quadcorner='INNERVERT')
    # 回到顶点选择模式
    bpy.ops.mesh.select_mode(type='VERT')
    # 重新设置上下边界顶点组
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_remove_from()

    # 设置平滑顶点组
    bpy.ops.mesh.select_all(action='SELECT')
    inner_obj.vertex_groups.new(name="SmoothVertex")
    bpy.ops.object.vertex_group_assign()
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

    # 更新平滑顶点组，把上下边界加入
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='SmoothVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_assign()

    # 更新外壁顶点组
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()

    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加平滑修改器
    modifier = obj.modifiers.new(name="Smooth", type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].iterations = 30
    bpy.context.object.modifiers["Smooth"].vertex_group = "SmoothVertex"
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    smooth_border()


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
    # 恢复到桥接前
    bpy.data.objects.remove(bpy.data.objects["右耳"], do_unlink=True)

    cur_obj = bpy.data.objects["右耳OriginForFill"]
    cur_obj.hide_set(False)
    cur_obj.name = "右耳"
    bpy.context.view_layer.objects.active = cur_obj

    number = 0
    for obj in bpy.data.objects:
        if re.match('HoleBorderCurve', obj.name) != None:
            number += 1

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.delete(type='VERT')

    extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")

    for i in range(1, number + 1):
        inside_border_index = extrude_border_by_vertex_groups("HoleBorderVertex" + str(i), "UpInnerBorderVertex")
        # 单个孔的内外边界也留一下
        set_vert_group("HoleInnerBorderVertex" + str(i), inside_border_index)

    update_vert_group()
    fill_closest_point()

    utils_re_color("右耳", (1, 0.319, 0.133))












