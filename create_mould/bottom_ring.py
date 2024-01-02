import bpy
import math
import bmesh


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


def get_lowest_point(angle_degrees, z_co, count, origin_loc, origin_normal):
    '''
    算法大体思想是在当前平面内，找到距离z轴最近的点
    :param angle_degrees: 当前角度
    :param z_co: 模板的z坐标
    :param count: 第几个交点
    :param origin_loc: 模板套用后的初始点
    :return:
    '''
    # 获取活动对象
    active_obj = bpy.context.active_object

    min_distance = origin_loc[0] ** 2 + origin_loc[1] ** 2
    lowest_point = origin_loc
    lowest_normal = origin_normal
    # 投射光线的方向
    direction = (math.cos(math.radians(angle_degrees)), math.sin(math.radians(angle_degrees)), 0)
    h = z_co - 1.5
    while h < z_co + 1.5:
        origin = (0, 0, h)
        for times in range(0, count):  # 找到当前高度h的第n次交点（初始点是第几次交点就和第几次交点比）
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)
            if hit:  # 如果有交点，去找下一个交点
                origin = (loc[0] + math.cos(math.radians(angle_degrees)) / 100,
                          loc[1] + math.sin(math.radians(angle_degrees)) / 100, loc[2])
            else:
                break
        if hit:
            distance = loc[0] ** 2 + loc[1] ** 2
            if distance < min_distance:
                min_distance = distance
                lowest_point = (loc[0], loc[1], loc[2])
                lowest_normal = normal

        h = h + 0.2

    return lowest_point, lowest_normal


# 对顶点进行排序用于画圈
def get_order_border_vert(selected_verts):
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
def draw_cut_border_curve(order_border_co, name, depth):
    active_obj = bpy.context.active_object
    new_node_list = list()
    for i in range(len(order_border_co)):
        if i % 2 == 1:  # 最后一个点连上去有点奇怪 所以换个方式
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
        # 为圆环上色
        color_matercal = bpy.data.materials.new(name="BottomRingColor")
        color_matercal.diffuse_color = (0.0, 0.0, 1.0, 1.0)
        bpy.context.active_object.data.materials.append(color_matercal)

        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


def translate_circle_to_plane():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "cutPlane":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    # 切换回编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill()
    bpy.ops.mesh.normals_make_consistent(inside=True)
    # bpy.ops.mesh.flip_normals()
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.hide_set(True)

def boolean_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    # 获取活动对象
    obj = bpy.context.active_object
    # 添加一个修饰器
    modifier = obj.modifiers.new(name="PlaneCut", type='BOOLEAN')
    bpy.context.object.modifiers["PlaneCut"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["PlaneCut"].object = bpy.data.objects["cutPlane"]


def delete_useless_part():

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    # bpy.ops.object.convert(target='MESH')
    bpy.ops.object.modifier_apply(modifier="PlaneCut",single_user=True)
    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    # 获取活动对象的数据
    obj = bpy.context.active_object
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.mesh.delete(type='FACE')
    bmesh.update_edit_mesh(mesh)
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')


def get_plane_height(high_percent):
    active_obj = bpy.context.active_object
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    bm2 = bm.copy()
    bm.verts.ensure_lookup_table()

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    highest_vert = vert_order_by_z[0]
    lowest_vert = vert_order_by_z[-1]

    return lowest_vert.co[2] + high_percent * (highest_vert.co[2] - lowest_vert.co[2])


def bottom_cut():
    high_percent = 0.25
    # 获取活动对象
    active_obj = bpy.context.active_object

    # 确保活动对象的类型是网格
    if active_obj.type == 'MESH':
        # origin z坐标后续根据比例来设置
        origin = (0, 0, get_plane_height(high_percent))
        order_border_co = []
        cut_plane = []
        for angle_degrees in range(0, 360, 1):
            direction = (
                math.cos(math.radians(angle_degrees)), math.sin(math.radians(angle_degrees)), 0)  # 举例：从起点向 x 轴正方向投射光线
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)

            if hit:
                # 相交后，继续向外走，找到最外侧的交点
                # 第一次交点
                count = 1
                while hit:
                    # 把当前交点加入边界数组
                    order_border_co.append((loc[0], loc[1], loc[2]))
                    # 这里是平面切割
                    cut_plane.append((loc[0] + math.cos(math.radians(angle_degrees)) * 20,
                                      loc[1] + math.sin(math.radians(angle_degrees)) * 20, loc[2]))

                    # todo 找到附近最凹处，并实现曲面切割
                    # lowest_point, lowest_normal = get_lowest_point(angle_degrees, -8, count, (loc[0], loc[1], loc[2]),
                    #                                                (normal[0], normal[1], normal[2]))
                    # order_border_co.append(lowest_point)
                    # # 沿法线方向移出控制点
                    # cut_plane.append((lowest_point[0] + lowest_normal[0] / 2,
                    #                   lowest_point[1] + lowest_normal[1] / 2,
                    #                   lowest_point[2] + lowest_normal[2] / 2))

                    # 去找下一个交点
                    # 注意 这里起始位置要往前走一点，否则一直会交在同一个点
                    hit, loc, normal, index = active_obj.ray_cast((loc[0] + math.cos(
                        math.radians(angle_degrees)) / 100, loc[1] + math.sin(
                        math.radians(angle_degrees)) / 100, loc[2]), direction)
                    # 相交次数+1
                    count = count + 1

        draw_cut_border_curve(get_order_border_vert(order_border_co), "BottomRingBorder", 0.18)
        draw_cut_border_curve(get_order_border_vert(cut_plane), "cutPlane", 0)

        translate_circle_to_plane()
        boolean_cut()
        delete_useless_part()

