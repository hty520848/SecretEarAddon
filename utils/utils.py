import bpy
import bmesh


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

def utils_copy_object(origin_name,copy_name):
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
