import bpy
import bmesh
import math
from .bottom_ring import *
from ..tool import moveToRight


def re_color(target_object_name, color):
    '''为模型重新上色'''
    # 遍历场景中的所有对象，并根据名称选择目标物体
    for obj in bpy.context.view_layer.objects:
        if obj.name == target_object_name:
            break
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


# 获取洞边界顶点
def get_hole_border(template_highest_point, template_hole_border):
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        # 获取网格数据
        me = bpy.data.objects["右耳OriginForFitPlace"].data
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

        # 用于计算模板旋转
        # 特别注意，因为导入时候，每个模型的角度不同，所以要将模型最高点（即耳道顶部）x，y轴坐标旋转到模板位置
        angle_template = calculate_angle(template_highest_point[0], template_highest_point[1])
        angle_now = calculate_angle(highest_vert.co[0], highest_vert.co[1])
        rotate_angle = angle_now - angle_template

        dig_border = []  # 被选择的挖孔顶点

        for template_hole_border_point in template_hole_border:  # 通过向z负方向投射找到边界
            # 根据模板旋转的角度，边界顶点也做相应的旋转
            xx = template_hole_border_point[0] * math.cos(math.radians(rotate_angle)) - template_hole_border_point[
                1] * math.sin(math.radians(rotate_angle))
            yy = template_hole_border_point[0] * math.sin(math.radians(rotate_angle)) + template_hole_border_point[
                1] * math.cos(math.radians(rotate_angle))
            origin = (xx, yy, 10)
            direction = (0, 0, -1)
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)
            if hit:
                dig_border.append((loc[0], loc[1], loc[2]))

        order_hole_border_vert = get_order_border_vert(dig_border)

        draw_hole_border_curve(order_hole_border_vert, "HoleBorderCurveR", 0.18)
        cut_cylinder_buttom_co = darw_cylinder_bottom(order_hole_border_vert)

        # todo 先加到右耳集合，后续调整左右耳适配
        moveToRight(bpy.data.objects["HoleBorderCurveR"])
        moveToRight(bpy.data.objects["HoleCutCylinderBottomR"])
        bpy.ops.object.mode_set(mode='OBJECT')
        return cut_cylinder_buttom_co


def darw_cylinder_bottom(order_hole_border_vert):
    # 该变量存储布尔切割的圆柱体的底部
    cut_cylinder_buttom_co = []
    for vert in order_hole_border_vert:
        # 先直接用原坐标，后续尝试法向向外走一段
        co = vert
        cut_cylinder_buttom_co.append([co[0], co[1], co[2] - 1])
    draw_hole_border_curve(cut_cylinder_buttom_co, "HoleCutCylinderBottomR", 0)
    return cut_cylinder_buttom_co


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
def draw_hole_border_curve(order_border_co, name, depth):
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
        # color_matercal = bpy.data.materials.new(name="HoleBorderColor")
        # color_matercal.diffuse_color = (0.0, 0.0, 1.0, 1.0)
        if checkinitialBlueColor() == False:
            initialBlueColor()
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


# 将HoleCutCylinderBottom转化为圆柱用于挖孔
def translate_circle_to_cylinder():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "HoleCutCylinderBottomR":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    # 切换回编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill()
    bpy.ops.mesh.extrude_region_move(
        # todo 50为挤出高度，先写死，后续根据边界最高最低点调整
        TRANSFORM_OT_translate={"value": (0, 0, 12)}
    )
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.hide_set(True)


# 使用布尔修改器
def boolean_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    # 获取活动对象
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigHole"].object = bpy.data.objects["HoleCutCylinderBottomR"]
    bpy.context.object.modifiers["DigHole"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="DigHole", single_user=True)


# 删除布尔后多余的部分
def delete_useless_part(cut_cylinder_buttom_co):
    # 重新将布尔切割完成的物体转换为网格
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    # bpy.ops.object.convert(target='MESH')

    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='VERT')

    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')


# 挖孔
def dig_hole(template_highest_point, template_hole_border):
    # 绘制曲线
    cut_cylinder_buttom_co = get_hole_border(template_highest_point, template_hole_border)
    # 生成切割用的圆柱体
    translate_circle_to_cylinder()
    # 创建布尔修改器
    boolean_cut()
    # 删除差值后，底部多余的顶点
    delete_useless_part(cut_cylinder_buttom_co)
