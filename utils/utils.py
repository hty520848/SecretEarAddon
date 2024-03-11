import bpy
import bmesh
import math


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
    # 尝试使用距离最近的点
    order_border_vert = []
    now_vert = selected_verts[0]
    unprocessed_vertex = selected_verts  # 未处理顶点
    while len(unprocessed_vertex) > 1:
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

    return order_border_vert


# 绘制曲线
def utils_draw_curve(order_border_co, name, depth):
    '''
        根据order_border_co绘制曲线，名称为name，粗细为depth
    '''
    active_obj = bpy.context.active_object
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
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
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            colvert.x = color[0]
            colvert.y = color[1]
            colvert.z = color[2]
        bm.to_mesh(me)
        bm.free()


def utils_copy_object(origin_name, copy_name):
    copy_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == "origin_name":
            copy_flag = True
            cur_obj = obj
            break
    # 复制一份挖孔前的模型以备用
    if copy_flag:
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = copy_name
        bpy.context.collection.objects.link(duplicate_obj)
    return copy_flag

def judge_normals():
    flag = True
    cut_plane = bpy.data.objects["CutPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)

    for v in cut_plane_mesh.verts:
        if v.normal[2] > 0:
            flag = False

    return flag


def get_cut_plane():
    bpy.data.objects["右耳"].select_set(False)
    cut_plane = bpy.data.objects["CutPlane"]
    bpy.context.view_layer.objects.active = cut_plane
    cut_plane.select_set(True)
    bpy.ops.object.convert(target='MESH')

    # 填充平面
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.fill()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.edge_face_add()

    if judge_normals():
        bpy.ops.mesh.flip_normals()

    bpy.data.objects["CutPlane"].select_set(False)
    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
    bpy.data.objects["右耳"].select_set(True)
    cut_plane.hide_set(True)
    bpy.ops.object.mode_set(mode='OBJECT')


def plane_boolean_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    # 获取活动对象
    obj = bpy.context.active_object
    # 添加一个修饰器
    modifier = obj.modifiers.new(name="BottomCut", type='BOOLEAN')
    bpy.context.object.modifiers["BottomCut"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["BottomCut"].object = bpy.data.objects["CutPlane"]

    bpy.context.object.modifiers["BottomCut"].solver = 'EXACT'
    # 应用修改器
    bpy.ops.object.modifier_apply(modifier="BottomCut", single_user=True)

    # 获取下边界顶点用于挤出
    bpy.ops.object.mode_set(mode='EDIT')
    # 创建bmesh对象
    bm = bmesh.from_edit_mesh(bpy.data.objects["右耳"].data)
    bottom_outer_border_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.delete(type='FACE')

    ori_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 将下边界加入顶点组
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')


def judge_if_need_invert():
    obj = bpy.data.objects["右耳"]
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    obj = bpy.data.objects["右耳"]
    bm = bmesh.from_edit_mesh(obj.data)
    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts): # 如果相等，说明切割成功了，不需要删除多余部分
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
    bottom_outer_border_vertex = bpy.data.objects["右耳"].vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 最后删掉没用的CutPlane
    bpy.data.objects.remove(bpy.data.objects["CutPlane"], do_unlink=True)


def plane_cut():
    get_cut_plane()
    plane_boolean_cut()
    delete_useless_part()
