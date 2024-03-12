import bpy
import bmesh
import math
import os
from mathutils import Vector

# 导入模版文件
def import_template():
    files_dir = os.path.join(os.path.dirname(__file__))
    path_EarR = os.path.join(files_dir, "TemplateEarR.stl")
    path_EarL = os.path.join(files_dir, "TemplateEarL.stl")
    bpy.ops.wm.stl_import(filepath=path_EarR)
    bpy.ops.wm.stl_import(filepath=path_EarL)

# 获取旋转角度
def get_change_parameters():
    tar_obj = bpy.data.objects['右耳']
    ori_obj_R = bpy.data.objects['TemplateEarR']
    ori_obj_L = bpy.data.objects['TemplateEarL']

    # 获取模型最高点
    origin_highest_vert_index_R = get_highest_vert(ori_obj_R)
    origin_highest_vert_index_L = get_highest_vert(ori_obj_L)
    target_highest_vert_index = get_highest_vert(tar_obj)

    origin_highest_vert_R = ori_obj_R.data.vertices[origin_highest_vert_index_R].co @ ori_obj_R.matrix_world
    origin_highest_vert_L = ori_obj_L.data.vertices[origin_highest_vert_index_L].co @ ori_obj_R.matrix_world
    target_highest_vert = tar_obj.data.vertices[target_highest_vert_index].co @ tar_obj.matrix_world
    # 计算旋转角度
    angle_origin_R = calculate_angle(
        origin_highest_vert_R[0], origin_highest_vert_R[1])
    angle_origin_L = calculate_angle(
        origin_highest_vert_L[0], origin_highest_vert_L[1])
    angle_target = calculate_angle(
        target_highest_vert[0], target_highest_vert[1])
    rotate_angle_R = angle_target - angle_origin_R
    rotate_angle_L = angle_target - angle_origin_L

    return rotate_angle_R, rotate_angle_L

# 获取模型的z坐标范围
def getModelz(name):
    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)

    # 初始化最大距离为负无穷大
    z_max = float('-inf')
    z_min = float('inf')

    # 遍历的每个顶点并计算距离
    for vertex in bm.verts:
        z_max = max(z_max, vertex.co.z)
        z_min = min(z_min, vertex.co.z)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    return z_max, z_min


def get_highest_vert(obj):
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
    return vert_order_by_z[0].index


def calculate_angle(x, y):
    # 弧度
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees


def copy_object(name):
    # 获取当前选中的物体
    active_obj = bpy.data.objects[name]
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "copy"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)
    # moveToRight(duplicate_obj)
    generate_curve(duplicate_obj.name)

# 旋转对象
def rotate():
    # 获取场景中的选中对象
    obj_R = bpy.data.objects['TemplateEarR']
    obj_L = bpy.data.objects['TemplateEarL']
    rotate_angle_R, rotate_angle_L = get_change_parameters()
    # 假设选中对象存在
    if obj_R:
        # 定义旋转角度（以弧度为单位）
        rotate_angle_R = math.radians(rotate_angle_R)  # 将角度转换为弧度
        # 设置旋转角度
        obj_R.rotation_euler[2] += rotate_angle_R  # 在 Z 轴上添加旋转角度
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_R
        obj_R.select_set(True)
        bpy.ops.object.transform_apply(
            location=False, rotation=True, scale=False, isolate_users=True)

    if obj_L:
        rotate_angle_L = math.radians(rotate_angle_L)  # 将角度转换为弧度
        obj_L.rotation_euler[2] += rotate_angle_L  # 在 Z 轴上添加旋转角度
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_L
        obj_L.select_set(True)
        bpy.ops.object.transform_apply(
            location=False, rotation=True, scale=False, isolate_users=True)

# 在一定高度上分离出曲线用于判断
def generate_curve(name):
    y_max, y_min = getModelz(name)
    obj = bpy.data.objects[name]
    plane_z = y_min + 0.25*(y_max - y_min)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(plane_co=(0, 0, plane_z), plane_no=(0, 0, 1))
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')

    for obj in bpy.data.objects:
        if obj.name == name + '.001':
            obj.name = name + 'ForJudge'
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            # 重采样
            bpy.ops.object.convert(target='CURVE')
            modifier = obj.modifiers.new(name="Resample", type='NODES')
            bpy.ops.node.new_geometry_node_group_assign()
            input_node = modifier.node_group.nodes['Group Input']
            output_node = modifier.node_group.nodes['Group Output']
            resample_node = modifier.node_group.nodes.new(
                "GeometryNodeResampleCurve")
            resample_node.inputs[2].default_value = 100
            modifier.node_group.links.new(
                input_node.outputs[0], resample_node.inputs[0])
            modifier.node_group.links.new(
                resample_node.outputs[0], output_node.inputs[0])
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            # obj.hide_set(True)
            co = find_nearset_point(obj.name)
            vertex_co = obj.matrix_world @ co
            _, _, normal, _ = bpy.data.objects[name].closest_point_on_mesh(
                vertex_co)
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
            bpy.data.objects.remove(obj, do_unlink=True)
            return normal

# 返回离中心位置最近顶点的下标
def find_nearset_point(name):
    obj_data = bpy.data.objects[name].data
    bm = bmesh.new()
    bm.from_mesh(obj_data)
    min_dis = float('inf')
    min_dis_index = -1
    location = bpy.data.objects[name].location

    for vert in bm.verts:
        bm.verts.ensure_lookup_table()
        index = vert.index
        distance = math.dist(vert.co, location)
        if distance < min_dis:
            min_dis = distance
            min_dis_index = index
    return bm.verts[min_dis_index].co


def curvature_calculation(a, b, c):
    bc = ((c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2 + (c[2] - b[2]) ** 2) ** 0.5
    ab = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
    ac = ((c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2 + (c[2] - a[2]) ** 2) ** 0.5

    cos_bac = (ab ** 2 + ac ** 2 - bc ** 2) / (2 * ab * ac)
    sin_bac = (1 - cos_bac ** 2) ** 0.5
    # 曲率
    k = 2 * sin_bac / bc
    return k


def find_max_curvature(name):
    obj_data = bpy.data.objects[name].data
    bm = bmesh.new()
    bm.from_mesh(obj_data)
    max_curvature = 0
    max_curvature_index = -1
    for vert in bm.verts:
        bm.verts.ensure_lookup_table()
        index = vert.index
        before_index = ((index - 1) + 100) % 100
        after_index = (index + 1) % 100
        curvature = curvature_calculation(
            vert.co, bm.verts[before_index].co, bm.verts[after_index].co)
        if curvature > max_curvature:
            max_curvature = curvature
            max_curvature_index = index

    return max_curvature_index


def cal_cosine(normal1, normal2):
    normal1_norm = normal1.normalized()
    normal2_norm = normal2.normalized()
    correlation = normal1.dot(normal2) / (normal1_norm * normal2_norm)
    return correlation

# 左右耳识别
def judge():
    import_template()
    rotate()
    normalT = copy_object('右耳')
    normalR = generate_curve('TemplateEarR')
    normalL = generate_curve('TemplateEarL')
    # 判断法向方向的相似性
    cosineR = cal_cosine(Vector(normalT), Vector(normalR))
    cosineL = cal_cosine(Vector(normalT), Vector(normalL))
    if cosineR > cosineL:
        return True
    else:
        return False
