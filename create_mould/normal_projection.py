import bpy
import bmesh
import math
from ..tool import moveToRight

def checkinitialBlueColor():
    ''' 确认是否生成蓝色材质 '''
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'blue':
            return True
    return False

def initialBlueColor():
    ''' 生成蓝色材质 '''
    material = bpy.data.materials.new(name="blue")
    material.use_nodes = True
    bpy.data.materials["blue"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        0, 0, 1, 1.0)
    material.blend_method = "BLEND"
    material.use_backface_culling = True

def calculate_angle(x, y):
    # 计算原点与给定坐标点之间的角度（弧度）
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees


def get_highest_vert(name):
    obj = bpy.data.objects[name]
    # 获取网格数据
    me = obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    return vert_order_by_z[0].co


def get_change_parameters(origin_highest_vert):
    angle_origin = calculate_angle(origin_highest_vert[0], origin_highest_vert[1])
    origin_highest_z = origin_highest_vert[2]

    target_highest_vert = get_highest_vert("右耳")
    angle_target = calculate_angle(target_highest_vert[0], target_highest_vert[1])
    target_highest_z = target_highest_vert[2]

    rotate_angle = angle_target - angle_origin

    return rotate_angle, target_highest_z - origin_highest_z


def get_origin_border(bm):
    border_vert_co_and_normal = list()

    color_lay = bm.verts.layers.float_color["Color"]
    for vert in bm.verts:
        colvert = vert[color_lay]
        if round(colvert.x, 3) == 0.000 and round(colvert.y, 3) == 0.000 and round(colvert.z, 3) == 1.000:
            co = (vert.co[0], vert.co[1], vert.co[2])
            normal = (vert.normal[0], vert.normal[1], vert.normal[2])
            border_vert_co_and_normal.append((co, normal))

    return border_vert_co_and_normal


def normal_ray_cast(template_vert, rotate_angle, height_difference, target_bm):
    closest_vert = None

    # 获取顶点的法向
    origin_normal = template_vert[1]
    origin_co = template_vert[0]

    # 计算得到实际的起点坐标
    xx_co = origin_co[0] * math.cos(math.radians(rotate_angle)) - origin_co[1] * math.sin(math.radians(rotate_angle))
    yy_co = origin_co[0] * math.sin(math.radians(rotate_angle)) + origin_co[1] * math.cos(math.radians(rotate_angle))
    zz_co = origin_co[2] + height_difference
    actual_co = (xx_co, yy_co, zz_co)

    xx_normal = origin_normal[0] * math.cos(math.radians(rotate_angle)) - origin_normal[1] * math.sin(
        math.radians(rotate_angle))
    yy_normal = origin_normal[0] * math.sin(math.radians(rotate_angle)) + origin_normal[1] * math.cos(
        math.radians(rotate_angle))
    actual_normal = (xx_normal, yy_normal, origin_normal[2])

    target_obj = bpy.data.objects["右耳"]

    hit, loc, normal, index = target_obj.ray_cast(actual_co, actual_normal)
    # 没有命中，那就反向向内尝试一下
    if not hit:
        reverse_normal = (-xx_normal, -yy_normal, -origin_normal[2])
        hit, loc, normal, index = target_obj.ray_cast(actual_co, reverse_normal)

    if hit:
        # 进入这里就说明向外或向内命中了
        target_mesh = target_obj.data
        hit_face = target_mesh.polygons[index]
        # 获取这个面的顶点索引
        face_verts_index = hit_face.vertices

        min_distance = math.inf
        for vert_index in face_verts_index:
            vert = target_bm.verts[vert_index]
            distance = (loc[0] - vert.co[0]) ** 2 + (loc[1] - vert.co[1]) ** 2 + (loc[2] - vert.co[2]) ** 2
            if distance < min_distance:
                closest_vert = vert
                min_distance = distance

        return closest_vert


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

        for vert in unprocessed_vertex:
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2 + (
                    vert[2] - now_vert_co[2]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert
        # 排序后最后老有几个歪到天边去了，所以干脆最后几个歪了的话就不管了
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

        # 为圆环上色
        # color_matercal = bpy.data.materials.new(name="BottomRingColor")
        # color_matercal.diffuse_color = (0.0, 0.0, 1.0, 1.0)
        # bpy.context.active_object.data.materials.append(color_matercal)
        if checkinitialBlueColor() == False:
            initialBlueColor()
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj

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


def normal_projection_to_darw_bottom_ring(origin_highest_vert, border_vert_co_and_normal):
    # 存储模板耳道口边界的坐标与法向以及最高点坐标

    # 为了解决节点dead的问题，把bmesh信息获取拿出来，作为传参进去
    target_obj = bpy.data.objects["右耳"]
    # 获取网格数据
    target_me = target_obj.data

    # 创建bmesh对象
    target_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    target_bm.from_mesh(target_me)
    target_bm.verts.ensure_lookup_table()

    border_vert = list()
    border_vert_co = list()
    rotate_angle, height_difference = get_change_parameters(origin_highest_vert)

    for vert in border_vert_co_and_normal:
        cast_vert = normal_ray_cast(vert, rotate_angle, height_difference, target_bm)
        if cast_vert is not None and cast_vert not in border_vert:
            border_vert.append(cast_vert)
            border_vert_co.append(cast_vert.co)

    order_border_vert = get_order_border_vert(border_vert_co)
    draw_border_curve(order_border_vert, "BottomRingBorderR", 0.3)
    moveToRight(bpy.data.objects["BottomRingBorderR"])
