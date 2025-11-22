import bpy
import bmesh
import math
from ..tool import set_vert_group, moveToRight, moveToLeft, delete_vert_group, newColor, recover_and_remind_border

min_z_before_cut = None
max_z_before_cut = None

# 获取VIEW_3D区域的上下文
def utils_get_override():
    '''
        获取VIEW_3D区域的上下文
    '''
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


# 对顶点进行排序用于画圈
def utils_get_order_border_vert(selected_verts):
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

        for vert in unprocessed_vertex:
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2 + (
                    vert[2] - now_vert_co[2]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert
        if min_distance > 2 and len(unprocessed_vertex) < 0.1 * size:
            finish = True

    return order_border_vert


# 绘制曲线
def utils_draw_curve(order_border_co, name, depth):
    '''
        根据order_border_co绘制曲线，名称为name，粗细为depth
    '''
    ori_name = bpy.context.scene.leftWindowObj
    active_obj = bpy.context.active_object
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    if ori_name == '右耳':
        moveToRight(obj)
    elif ori_name == '左耳':
        moveToLeft(obj)
    bpy.context.view_layer.objects.active = obj

    # 添加一个曲线样条
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(order_border_co) - 1)
    spline.use_cyclic_u = True

    # 设置每个点的坐标
    for i, point in enumerate(order_border_co):
        spline.points[i].co = (point[0], point[1], point[2], 1)

    # 更新场景
    # 这里可以自行调整数值
    # 解决上下文问题
    override = utils_get_override()
    with bpy.context.temp_override(**override):
        bpy.context.active_object.data.bevel_depth = depth
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


def utils_re_color(target_object_name, color):
    flag = False
    '''为模型重新上色'''
    # 遍历场景中的所有对象，并根据名称选择目标物体
    for obj in bpy.context.view_layer.objects:
        if obj.name == target_object_name:
            flag = True
            break
    if flag:
        me = obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        if len(bm.verts.layers.float_color) > 0:
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                colvert.x = color[0]
                colvert.y = color[1]
                colvert.z = color[2]
            bm.to_mesh(me)
            bm.free()
        else:
            # 目标物体没有颜色属性
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[target_object_name]
            bpy.data.objects[target_object_name].select_set(True)
            bpy.ops.geometry.color_attribute_add(name="Color", color=(1, 0.319, 0.133, 1))
            bm.free()
            bm2 = bmesh.new()
            bm2.from_mesh(me)
            color_lay = bm2.verts.layers.float_color["Color"]
            for vert in bm2.verts:
                colvert = vert[color_lay]
                colvert.x = color[0]
                colvert.y = color[1]
                colvert.z = color[2]
            bm2.to_mesh(me)
            bm2.free()


def utils_copy_object(origin_name, copy_name):
    copy_flag = False
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.context.view_layer.objects:
        if obj.name == origin_name:
            copy_flag = True
            cur_obj = obj
            break
    # 复制一份挖孔前的模型以备用
    if copy_flag:
        if bpy.data.objects.get(copy_name) != None:
            bpy.data.objects.remove(bpy.data.objects[copy_name], do_unlink=True)
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = copy_name
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
    return copy_flag


def judge_normals():
    name = bpy.context.scene.leftWindowObj
    cut_plane = bpy.data.objects[name + "CutPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)
    sum = 0
    for v in cut_plane_mesh.verts:
        sum += v.normal[2]
    return sum < 0


def get_cut_plane():
    # 外边界顶点组
    name = bpy.context.scene.leftWindowObj
    bpy.data.objects[name].select_set(False)
    cut_plane_outer = bpy.data.objects[name + "CutPlane"]
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_outer.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Outer", vert_index)

    # 中间边界顶点组
    bpy.data.objects[name + "CutPlane"].select_set(False)
    cut_plane_center = bpy.data.objects[name + "Center"]
    bpy.context.view_layer.objects.active = cut_plane_center
    cut_plane_center.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_center.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Center", vert_index)

    # 内边界顶点组
    bpy.data.objects[name + "Center"].select_set(False)
    cut_plane_inner = bpy.data.objects[name + "Inner"]
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
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)

    # # 最内补面
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='Inner')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.edge_face_add()

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
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    if judge_normals():
        bpy.ops.mesh.flip_normals()

    # bpy.ops.mesh.remove_doubles(threshold=0.25)


    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects[name + "CutPlane"].select_set(False)
    main_obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)


def plane_boolean_cut():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # for obj in bpy.data.objects:
    #     obj.select_set(False)
    #     if obj.name == name:
    #         obj.select_set(True)
    #         bpy.context.view_layer.objects.active = obj

    # 获取活动对象
    # obj = bpy.context.active_object

    # 存一下原先的顶点
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bm = bmesh.from_edit_mesh(obj.data)
    ori_border_index = [v.index for v in obj.data.vertices]
    all_verts = [v for v in obj.data.vertices]
    all_verts.sort(key=lambda vert: vert.co[2])
    global min_z_before_cut, max_z_before_cut
    min_z_before_cut = all_verts[0].co[2]
    max_z_before_cut = all_verts[-1].co[2]
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("all", ori_border_index)

    utils_bool_difference(name + "CutPlane")

    # 获取下边界顶点用于挤出
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='all')
    # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    # 创建bmesh对象
    bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
    bottom_outer_border_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.delete(type='FACE')

    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # 将下边界加入顶点组
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')
    delete_vert_group("all")


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


def delete_useless_part():
    name = bpy.context.scene.leftWindowObj
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        # 判断最低点是否被选择
        invert_flag = judge_if_need_invert()

        if not invert_flag:
            # 不需要反转，直接删除面即可
            bpy.ops.mesh.delete(type='FACE')
        else:
            # 反转一下，删除顶点
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

    # 最后，删一下边界的直接的面
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = bpy.data.objects[name].vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
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
    global min_z_before_cut, max_z_before_cut
    all_verts = [v for v in target_bm.verts]
    all_verts.sort(key=lambda vert: vert.co[2])
    if len(target_bm.verts) < 100:
        print("切割出错，完全切掉了")
        raise ValueError("切割出错，完全切掉了")
    elif min_z_before_cut == all_verts[0].co[2]:
        print("切割出错，没有切掉下半部分")
        if all_verts[-1].co[2] != max_z_before_cut:
            print("切反了")
            # recover_and_remind_border()
            # # 翻转平面法线
            # bpy.ops.object.select_all(action='DESELECT')
            # bpy.context.view_layer.objects.active = bpy.data.objects[name + "CutPlane"]
            # bpy.data.objects[name + "CutPlane"].select_set(True)
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='SELECT')
            # bpy.ops.mesh.flip_normals()
            # bpy.ops.object.mode_set(mode='OBJECT')
            # plane_boolean_cut()
            # delete_useless_part()
        else:
            raise ValueError("切割出错，没有切掉下半部分")

    # 最后删掉没用的CutPlane
    bpy.data.objects.remove(bpy.data.objects[name + "CutPlane"], do_unlink=True)


def utils_plane_cut():
    get_cut_plane()
    plane_boolean_cut()
    delete_useless_part()


def utils_bool_difference(cut_obj_name):
    name = bpy.context.scene.leftWindowObj
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.data.objects[main_obj_name].select_set(True)
    cut_obj = bpy.data.objects[cut_obj_name]
    # 该布尔插件会直接删掉切割平面，最好是使用复制去切，以防后续会用到
    duplicate_obj = cut_obj.copy()
    duplicate_obj.data = cut_obj.data.copy()
    duplicate_obj.animation_data_clear()
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.select_set(True)
    # 使用布尔插件
    bpy.ops.object.booltool_auto_difference()


# 利用几何节点重采样上下边界使其顶点数量一致
def resample_curve(point_num, curve_name):
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects[curve_name]
    main_obj = bpy.data.objects[name]

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = curve_obj
    curve_obj.select_set(True)
    bpy.context.object.data.bevel_depth = 0

    # 添加几何节点修改器
    modifier = curve_obj.modifiers.new(name="Resample", type='NODES')
    bpy.ops.node.new_geometry_node_group_assign()

    node_tree = bpy.data.node_groups[0]
    node_links = node_tree.links

    input_node = node_tree.nodes[0]
    output_node = node_tree.nodes[1]

    resample_node = node_tree.nodes.new("GeometryNodeResampleCurve")
    resample_node.inputs[2].default_value = point_num

    node_links.new(input_node.outputs[0], resample_node.inputs[0])
    node_links.new(resample_node.outputs[0], output_node.inputs[0])

    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.convert(target='CURVE')
    bpy.context.object.data.bevel_depth = 0.18
    # bpy.ops.object.shade_smooth(use_auto_smooth=True)
    if not bpy.data.materials.get('blue'):
        newColor('blue', 0, 0, 1, 0, 1)
    bpy.data.objects[curve_name].data.materials.append(bpy.data.materials['blue'])

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    # 2024/05/30 几何节点用完之后，删除掉，避免无限堆积
    bpy.data.node_groups.remove(node_tree)


def generate_cut_plane(step_number_in, step_number_out):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name + 'BottomRingBorderR']

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj.data.bevel_depth = 0
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.select_set(state=True)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    duplicate_obj.vertex_groups.new(name='Center')
    bpy.ops.object.vertex_group_assign()
    extrude_direction = {}
    bm = bmesh.from_edit_mesh(duplicate_obj.data)
    target_object = bpy.data.objects[name + "MouldReset"]

    for vert in bm.verts:
        # 获取顶点原位置
        vertex_co = duplicate_obj.matrix_world @ vert.co
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)
        key = (vertex_co[0], vertex_co[1], vertex_co[2])
        extrude_direction[key] = normal

    # 复制选中的顶点并沿着各自的法线方向移动
    bpy.ops.mesh.duplicate()

    # 获取所有选中的顶点
    inside_border_vert = [v for v in bm.verts if v.select]
    for vert in inside_border_vert:
        vertex_co = duplicate_obj.matrix_world @ vert.co
        key = (vertex_co[0], vertex_co[1], vertex_co[2])
        dir = extrude_direction[key]
        vert.co -= dir * step_number_in
    duplicate_obj.vertex_groups.new(name='Inner')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group="Center")
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.object.vertex_group_set_active(group="Inner")
    bpy.ops.object.vertex_group_deselect()

    # 复制选中的顶点并沿着各自的法线方向移动
    bpy.ops.mesh.duplicate()

    # 获取所有选中的顶点
    outside_border_vert = [v for v in bm.verts if v.select]
    for vert in outside_border_vert:
        vertex_co = duplicate_obj.matrix_world @ vert.co
        key = (vertex_co[0], vertex_co[1], vertex_co[2])
        dir = extrude_direction[key]
        vert.co += dir * step_number_out
    duplicate_obj.vertex_groups.new(name='Outer')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group="Center")
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    if judge_normals():
        bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode='OBJECT')



