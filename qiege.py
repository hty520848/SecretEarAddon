import bpy
from bpy import context
from bpy_extras import view3d_utils
import mathutils
import bmesh
from mathutils import Vector
from bpy.types import WorkSpaceTool
from .tool import *
import math
from math import *

# 当前的context
gcontext = ''

flag = 0
old_radius = 8.0
now_radius = 0
scale_ratio = 1
zmax = 0
zmin = 0
# 圆环是否在物体上
on_obj = True
# 切割时的圆环信息
last_loc = None
last_radius = None
last_ratation = None
finish = False
# 模型进入切割模式的原始网格
oridata = None
# old_loc_sphere1 = [10.290, -8.958, 6.600]
# old_loc_sphere2 = [5.266, -9.473, 6.613]
# old_loc_sphere3 = [11.282, -2.077, 6.607]
# old_loc_sphere4 = [8.107, -6.029, 13.345]

old_loc_sphere1 = []
old_loc_sphere2 = []
old_loc_sphere3 = []
old_loc_sphere4 = []

qiegeenum = 1  # 当前切割的模式，1为环切，2为侧切


# 复制初始模型，并赋予透明材质


def copyModel():
    # 获取当前选中的物体
    obj_ori = bpy.data.objects['右耳']
    # 复制物体用于对比突出加厚的预览效果
    obj_all = bpy.data.objects
    copy_compare = True  # 判断是否复制当前物体作为透明的参照,不存在参照物体时默认会复制一份新的参照物体
    for selected_obj in obj_all:
        if (selected_obj.name == "右耳huanqiecompare"):
            copy_compare = False  # 当存在参照物体时便不再复制新的物体
            # break
    if (copy_compare):  # 复制一份物体作为透明的参照
        active_obj = obj_ori
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.name = active_obj.name + "huanqiecompare"
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)

        moveToRight(duplicate_obj)

        # print('复制的', duplicate_obj.name)


# 计算点到平面的距离
def distance_to_plane(plane_normal, plane_point, point):
    return round(abs(plane_normal.dot(point - plane_point)), 4)


# 根据点到平面的距离，计算移动的长度
def displacement(distance, a, b):
    dis = a * (distance - b) * (distance - b)
    return dis

# 计算距离圆环中心的距离，用于限制平滑的范围
def dis_smooth(vert,cir):
    dis = (vert - cir).length
    return dis


# 平滑边缘
def smooth():
    global now_radius,on_obj
    obj_ori = bpy.data.objects['右耳huanqiecompare']
    obj_main = bpy.data.objects['右耳']
    obj_circle = bpy.data.objects['Circle']
    obj_torus = bpy.data.objects['Torus']
    # 从透明对比物体 获取原始网格数据
    orime = obj_ori.data
    oribm = bmesh.new()
    oribm.from_mesh(orime)
    # 应用原始网格数据
    oribm.to_mesh(obj_main.data)
    # 不存在，则添加
    if not obj_main.modifiers:
        bool_modifier = obj_main.modifiers.new(
            name="Boolean Modifier", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = obj_circle
        # bool_modifier.solver = 'FAST'

    # 圆环在物体上，则进行平滑
    if on_obj:
        # 应用修改器
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_main
        obj_main.select_set(True)
        bpy.ops.object.make_single_user(
            object=True, obdata=True, material=False, animation=False, obdata_animation=False)
        bpy.ops.object.modifier_apply(modifier="Boolean Modifier")
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_circle
        obj_circle.select_set(True)

        bm = bmesh.new()
        bm.from_mesh(obj_main.data)
        z_circle = obj_circle.location.z
        selected_vert = [v for v in bm.verts if round(v.co.z, 2) == round(z_circle, 2)]
        # # 圆环中心
        # center = sum((v.co for v in selected_vert), Vector()) / len(selected_vert)

        # 创建一个空的选中集合
        selected_faces = []

        selected_faces = [polygon.index for polygon in obj_main.data.polygons if polygon.center.z >= z_circle - 2]
        # print('face num:',len(selected_faces))

        # 设置选中的面
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_torus
        obj_torus.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = obj_main
        bpy.context.view_layer.objects.active.data.polygons.foreach_set("select", [i in selected_faces for i in
                                                                                range(len(obj_main.data.polygons))])
        bpy.ops.object.mode_set(mode='EDIT')
        # 转换4边面
        bpy.ops.mesh.tris_convert_to_quads()
        # 细分
        bpy.ops.mesh.subdivide()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 融并第一圈顶点
        first_line = []
        for vert in selected_vert:
            for edge in vert.link_edges:
                v1 = edge.verts[0]
                v2 = edge.verts[1]
                link_vert = v1 if v1 != vert else v2
                if not (link_vert in selected_vert):
                    if not (link_vert in first_line):
                        first_line.append(link_vert.index)

        # print('第一圈',len(first_line))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = obj_main
        bpy.context.view_layer.objects.active.data.vertices.foreach_set("select", [i in first_line for i in
                                                                                range(len(obj_main.data.vertices))])
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.dissolve_verts()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 圆环平面法向量和平面上一点
        plane_normal = obj_circle.matrix_world.to_3x3(
        ) @ obj_circle.data.polygons[0].normal
        plane_point = obj_circle.location.copy()
        # 舍入偏移参数
        a = bpy.context.scene.qiegesheRuPianYi
        # 最大偏移值
        b = round(math.sqrt((now_radius)), 2)
        

        bpy.context.view_layer.update()

        # 获取圆环的坐标范围
        cbm = bmesh.new()
        cbm.from_mesh(obj_circle.data)
        xmin = float('inf')
        xmax = float('-inf')
        for vert in cbm.verts:
            xmax = max(vert.co.x, xmax)
            xmin = min(vert.co.x, xmin)
        xmax = obj_circle.location.x + xmax
        xmin = obj_circle.location.x + xmin
        # print('xmin',xmin)
        # print('xmax',xmax)

        # 所有点
        vert_order_by_z = []
        # 平面上的点
        vert_plane = []
        for vert in bm.verts:
            vert_order_by_z.append(vert)
            point = vert.co
            distance = distance_to_plane(plane_normal, plane_point, point)
            if distance == 0:
                vert_plane.append(vert)
                
        # 按z坐标倒序排列
        vert_plane.sort(key=lambda vert: vert.co[2], reverse=True)
        highest_vert = vert_plane[0]

        # 从最高点开始 广搜
        # 需要保存的点
        save_part = []
        # 用于存放当前一轮还未处理的顶点
        wait_to_find_link_vert = []
        visited_vert = []  # 存放被访问过的节点防止重复访问
        un_reindex_vert = vert_order_by_z

        # 初始化处理第一个点
        wait_to_find_link_vert.append(highest_vert)
        visited_vert.append(highest_vert)
        un_reindex_vert.remove(highest_vert)

        while wait_to_find_link_vert:
            save_part.extend(wait_to_find_link_vert)
            temp_vert = []  # 存放下一层将要遍历的顶点，即与 wait_to_find_link_vert中顶点 相邻的点
            for vert in wait_to_find_link_vert:
                # 遍历顶点的连接边找寻顶点
                for edge in vert.link_edges:
                    # 获取边的顶点
                    v1 = edge.verts[0]
                    v2 = edge.verts[1]
                    # 确保获取的顶点不是当前顶点
                    link_vert = v1 if v1 != vert else v2
                    if link_vert not in visited_vert and distance_to_plane(plane_normal, plane_point, link_vert.co) <= b:
                        temp_vert.append(link_vert)
                        visited_vert.append(link_vert)
                        un_reindex_vert.remove(link_vert)
            wait_to_find_link_vert = temp_vert

        

        # 平滑操作
        for vert in save_part:
            point = vert.co
            distance = distance_to_plane(plane_normal, plane_point, point)
            # print('距中心点距离',dis_smt)
            if distance <= b:
                move = displacement(distance, a, b)
                center = plane_point.copy()
                center = center + distance * plane_normal
                to_center = vert.co - center
                # 计算径向位移的增量
                movement = to_center.normalized() * move
                vert.co -= movement

        bm.to_mesh(obj_main.data)
        bm.free()


# 获取模型的Z坐标范围
def getModelZ():
    global zmax, zmin
    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects['右耳']
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

    zmax = z_max
    zmin = z_min
    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')


# 获取截面半径
def getRadius():
    global old_radius, scale_ratio, now_radius, on_obj

    # 翻转圆环法线
    obj_torus = bpy.data.objects['Torus']
    obj_circle = bpy.data.objects['Circle']
    active_obj = bpy.data.objects['右耳huanqiecompare']
    for selected_obj in bpy.data.objects:
        if (selected_obj.name == "右耳huanqiecompareintersect"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = active_obj.name + "intersect"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)

    bpy.context.view_layer.objects.active = duplicate_obj
    # 添加修改器,获取交面

    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate_obj.modifiers.new(name="Boolean Intersect", type='BOOLEAN')
    duplicate_obj.modifiers[0].operation = 'INTERSECT'
    duplicate_obj.modifiers[0].object = obj_circle
    duplicate_obj.modifiers[0].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect')

    rbm = bmesh.new()
    rbm.from_mesh(duplicate_obj.data)

    # 获取截面上的点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()
    plane_verts = []
    plane_verts = [v for v in rbm.verts if distance_to_plane(plane_normal, plane_point, v.co) == 0]
    # print(len(plane_verts))

    # 圆环不在物体上
    if (len(plane_verts) == 0):
        on_obj = False
    else:
        on_obj = True

    # print('圆环是否在物体上',on_obj)

    if on_obj:
        center = sum((v.co for v in plane_verts), Vector()) / len(plane_verts)

        # 初始化最大距离为负无穷大
        max_distance = float('-inf')
        min_distance = float('inf')

        # 遍历的每个顶点并计算距离
        for vertex in plane_verts:
            distance = (vertex.co - center).length
            max_distance = max(max_distance, distance)
            min_distance = min(min_distance, distance)

        radius = round(max_distance, 2)
        radius = radius + 0.5
        # print('最大半径',radius)
        # print('最小半径',min_distance)
        now_radius = round(min_distance, 2)

        # 删除复制的物体
        bpy.data.objects.remove(duplicate_obj, do_unlink=True)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_torus
        obj_torus.select_set(True)
        # 缩放圆环及调整位置
        obj_torus.location = center
        obj_circle.location = center
        scale_ratio = round(radius / old_radius, 3)
        # print('缩放比例', scale_ratio)
        obj_torus.scale = (scale_ratio, scale_ratio, 1)


# 保存模型原始网格数据
def saveOriobj():
    print('保存原始网格数据')
    global oridata
    obj_ori = bpy.data.objects['右耳']
    orime = obj_ori.data
    oribm = bmesh.new()
    oribm.from_mesh(orime)
    oridata = oribm.copy()


# 初始化
def initCircle():
    global old_radius, scale_ratio, now_radius, last_loc, last_radius, last_ratation
    global zmax, zmin, oridata, init1, init2

    obj_main = bpy.data.objects['右耳']

    copyModel()
    getModelZ()

    initZ = round(zmax * 0.8, 2)
    # 获取目标物体的编辑模式网格

    obj_main.data.materials.clear()
    if (checkinitialModelColor() == False):
        initialModelColor()
    obj_main.data.materials.append(bpy.data.materials['yellow'])
    if (checkinitialTransparency() == False):
        initialTransparency()
    obj_compare = bpy.data.objects['右耳huanqiecompare']
    obj_compare.data.materials.clear()
    obj_compare.data.materials.append(bpy.data.materials['yellow2'])
    # bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj_main
    # obj_main.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)
    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
    if selected_verts:
        # 计算平面的几何中心
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        # 输出几何中心坐标
        print("Geometry Center:", center)

    # 初始化最大距离为负无穷大
    max_distance = float('-inf')
    min_distance = float('inf')
    # 遍历的每个顶点并计算距离
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)
        min_distance = min(min_distance, distance)
    old_radius = max_distance / cos(math.radians(30))
    old_radius = 7
    now_radius = round(min_distance, 2)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    # print('当前位置', last_loc)

    # 正常初始化
    if last_loc == None:
        print('正常初始化')
        # 大圆环
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD', location=(
                center.x, center.y, initZ), rotation=(
                -0.5, 0.0, 0.0), scale=(
                1.0, 1.0, 1.0))

        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(
            center.x, center.y, initZ), rotation=(-0.5, 0, 0), major_radius=old_radius, minor_radius=0.4)



    else:
        print('切割后初始化')
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(
                last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                1.0, 1.0, 1.0))
        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
            last_ratation[0], last_ratation[1], last_ratation[2]), major_radius=last_radius, minor_radius=0.4)
        old_radius = last_radius

    obj = bpy.context.active_object
    moveToRight(obj)
    # 环体颜色
    initialTorusColor()
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['red'])
    # 选择圆环
    obj_circle = bpy.data.objects['Circle']
    moveToRight(obj_circle)
    # 进入编辑模式
    bpy.context.view_layer.objects.active = obj_circle
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # 翻转圆环法线
    bpy.ops.mesh.flip_normals(only_clnors=False)
    # 隐藏圆环
    obj_circle.hide_set(True)
    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    # 为模型添加布尔修改器
    obj_main = bpy.data.objects['右耳']
    bool_modifier = obj_main.modifiers.new(
        name="Boolean Modifier", type='BOOLEAN')
    # 设置布尔修饰符作用对象
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = obj_circle
    # bool_modifier.solver = 'FAST'

    smooth()

    # override = getOverride()
    # with bpy.context.temp_override(**override):
    bpy.ops.object.circlecut('INVOKE_DEFAULT')


def new_sphere(name, loc):
    # 创建一个新的网格
    mesh = bpy.data.meshes.new("MyMesh")
    obj = bpy.data.objects.new(name, mesh)

    # 在场景中添加新的对象
    scene = bpy.context.scene
    scene.collection.objects.link(obj)
    moveToRight(obj)

    # 切换到编辑模式
    # bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    for i in bpy.context.visible_objects:
        if i.name == name:
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')

    # 获取编辑模式下的网格数据
    bm = bmesh.from_edit_mesh(obj.data)

    # 设置圆球的参数
    radius = 0.2  # 半径
    segments = 32  # 分段数

    # 在指定位置生成圆球
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                              radius=radius * 2)

    # 更新网格数据
    bmesh.update_edit_mesh(obj.data)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    # 设置圆球的位置
    obj.location = loc  # 指定的位置坐标


def new_plane(name):
    mesh = bpy.data.meshes.new("MyMesh")
    obj = bpy.data.objects.new(name, mesh)

    # 在场景中添加新的对象
    scene = bpy.context.scene
    scene.collection.objects.link(obj)
    moveToRight(obj)

    bpy.ops.object.select_all(action='DESELECT')
    for i in bpy.context.visible_objects:
        if i.name == name:
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    # 创建四个顶点
    verts = [bm.verts.new((0, 0, 0)),
             bm.verts.new((1, 0, 0)),
             bm.verts.new((1, 1, 0)),
             bm.verts.new((0, 1, 0))]

    # 创建两个面
    bm.faces.new(verts[:3])
    bm.faces.new(verts[1:])

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=True)

    # 更新网格数据
    bmesh.update_edit_mesh(obj.data)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    object = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(object.data)
    bm.faces.ensure_lookup_table()
    bm.faces[1].normal_flip()
    object.hide_set(True)

    bool_modifier = object.modifiers.new(
        name="smooth", type='BEVEL')
    bool_modifier.segments = 32
    bool_modifier.width = bpy.context.scene.qiegewaiBianYuan
    bool_modifier.limit_method = 'NONE'


def update_plane():
    # 获取坐标
    loc = [bpy.data.objects['StepCutSphere1'].location,
           bpy.data.objects['StepCutSphere2'].location,
           bpy.data.objects['StepCutSphere3'].location,
           bpy.data.objects['StepCutSphere4'].location]

    # 更新位置
    obj = bpy.data.objects['StepCutplane']
    bm = obj.data
    if bm.vertices:
        for i in range(0, 4):
            vertex = bm.vertices[i]
            vertex.co = loc[i]

    mesh = bmesh.new()
    mesh.from_mesh(bm)

    mesh.verts.ensure_lookup_table()
    dis = (mesh.verts[1].co - mesh.verts[2].co).normalized()
    mesh.verts[1].co += dis * 20
    mesh.verts[2].co -= dis * 20
    dis2 = (mesh.verts[0].co - (mesh.verts[1].co +
                                mesh.verts[2].co) / 2).normalized()
    mesh.verts[0].co += dis2 * 20
    dis3 = (mesh.verts[3].co - (mesh.verts[1].co +
                                mesh.verts[2].co) / 2).normalized()
    mesh.verts[3].co += dis3 * 20

    # 更新网格数据
    mesh.to_mesh(bm)
    mesh.free()


def initialModelColor():
    yellow_material = bpy.data.materials.new(name="yellow")
    yellow_material.use_nodes = True
    bpy.data.materials["yellow"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1.0, 0.319, 0.133, 1.0)


# 初始化圆环颜色
def initialTorusColor():
    yellow_material = bpy.data.materials.new(name="red")
    yellow_material.use_nodes = True
    bpy.data.materials["red"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1.0, 0.0, 0, 1.0)


def checkinitialModelColor():
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'yellow':
            return True
    return False


def initialTransparency():
    yellow_material_t = bpy.data.materials.new(name="yellow2")
    yellow_material_t.use_nodes = True
    bpy.data.materials["yellow2"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1.0, 0.319, 0.133, 1.0)
    yellow_material_t.blend_method = "BLEND"
    yellow_material_t.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.5


def checkinitialTransparency():
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'yellow2':
            return True
    return False

def checkinitialRed():
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'Red':
            return True
    return False

# 确定四个圆球的位置
def initsphereloc():
    global zmax
    global old_loc_sphere1
    global old_loc_sphere2
    global old_loc_sphere3
    global old_loc_sphere4
    getModelZ()
    initZ = round(zmax * 0.8, 2)
    bm = bmesh.new()
    obj = bpy.data.objects['右耳']
    objdata = bpy.data.objects['右耳'].data
    bm.from_mesh(objdata)
    selected_verts = [v.co for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]

    # 找到具有最大或最小坐标的顶点
    old_loc_sphere1 = min(selected_verts, key=lambda v: v[1])
    old_loc_sphere2 = min(selected_verts, key=lambda v: v[0])
    old_loc_sphere3 = max(selected_verts, key=lambda v: v[0])

    initx = (old_loc_sphere2[0] + old_loc_sphere3[0]) / 2
    selected_verts2 = [v.co for v in bm.verts if round(v.co.x, 2) < round(
        initx, 2) + 0.1 and round(v.co.x, 2) > round(initx, 2) - 0.1]
    old_loc_sphere4 = max(selected_verts2, key=lambda v: v[2])


# 初始化侧切模块中用于切割的平面
def initPlane():
    global qiegeenum
    global old_loc_sphere1
    global old_loc_sphere2
    global old_loc_sphere3
    global old_loc_sphere4

    qiegeenum = 2
    initsphereloc()
    # 新建圆球
    new_sphere('StepCutSphere1', old_loc_sphere1)
    new_sphere('StepCutSphere2', old_loc_sphere2)
    new_sphere('StepCutSphere3', old_loc_sphere3)
    new_sphere('StepCutSphere4', old_loc_sphere4)
    new_plane('StepCutplane')

    if checkinitialRed() == False:
        bpy.data.materials.new(name="Red")
    red_material = bpy.data.materials['Red']
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    bpy.data.objects['StepCutSphere1'].data.materials.append(red_material)
    bpy.data.objects['StepCutSphere2'].data.materials.append(red_material)
    bpy.data.objects['StepCutSphere3'].data.materials.append(red_material)
    bpy.data.objects['StepCutSphere4'].data.materials.append(red_material)

    # 开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    for i in bpy.context.visible_objects:
        if i.name == "右耳":
            bpy.context.view_layer.objects.active = i
            obj = bpy.context.active_object
            obj_copy = obj.copy()
            obj_copy.name = obj.name + 'ceqieCompare'
            obj_copy.data = obj.data.copy()
            obj_copy.animation_data_clear()
            scene = bpy.context.scene
            scene.collection.objects.link(obj_copy)
            moveToRight(obj)
            moveToRight(obj_copy)
            obj.hide_select = True
            obj_copy.hide_select = True

    if (checkinitialModelColor() == False):
        initialModelColor()
    if (checkinitialTransparency() == False):
        initialTransparency()

    bpy.data.objects['右耳'].data.materials.clear()
    bpy.data.objects['右耳'].data.materials.append(bpy.data.materials['yellow'])
    bpy.data.objects['右耳ceqieCompare'].data.materials.clear()
    bpy.data.objects['右耳ceqieCompare'].data.materials.append(
        bpy.data.materials['yellow2'])
    bpy.ops.object.select_all(action='DESELECT')

    plane = bpy.data.objects['StepCutplane']
    obj_main = bpy.data.objects['右耳']
    bool_modifier = obj_main.modifiers.new(
        name="step cut", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = plane

    # 调用调整按钮
    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.ops.object.stepcut('INVOKE_DEFAULT')


# 获取VIEW_3D区域的上下文
def getOverride():
    # change this to use the correct Area Type context you want to process in
    area_type = 'VIEW_3D'
    areas = [
        area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(
            f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override


# 切割完成时，保存圆环的信息
def saveCir():
    global old_radius, last_loc, last_radius, last_ratation
    obj_torus = bpy.data.objects['Torus']
    last_loc = obj_torus.location.copy()
    last_radius = round(old_radius * obj_torus.scale[0], 2)
    last_ratation = obj_torus.rotation_euler.copy()
    # print('当前位置',last_loc)
    # print('当前半径',last_radius)
    # print('当前角度',last_ratation)


def saveStep():
    global old_loc_sphere1
    global old_loc_sphere2
    global old_loc_sphere3
    global old_loc_sphere4

    old_loc_sphere1 = []
    old_loc_sphere1.append(round(bpy.data.objects['StepCutSphere1'].location.x, 3))
    old_loc_sphere1.append(round(bpy.data.objects['StepCutSphere1'].location.y, 3))
    old_loc_sphere1.append(round(bpy.data.objects['StepCutSphere1'].location.z, 3))
    old_loc_sphere2 = []
    old_loc_sphere2.append(round(bpy.data.objects['StepCutSphere2'].location.x, 3))
    old_loc_sphere2.append(round(bpy.data.objects['StepCutSphere2'].location.y, 3))
    old_loc_sphere2.append(round(bpy.data.objects['StepCutSphere2'].location.z, 3))
    old_loc_sphere3 = []
    old_loc_sphere3.append(round(bpy.data.objects['StepCutSphere3'].location.x, 3))
    old_loc_sphere3.append(round(bpy.data.objects['StepCutSphere3'].location.y, 3))
    old_loc_sphere3.append(round(bpy.data.objects['StepCutSphere3'].location.z, 3))
    old_loc_sphere4 = []
    old_loc_sphere4.append(round(bpy.data.objects['StepCutSphere4'].location.x, 3))
    old_loc_sphere4.append(round(bpy.data.objects['StepCutSphere4'].location.y, 3))
    old_loc_sphere4.append(round(bpy.data.objects['StepCutSphere4'].location.z, 3))

    print('圆球的坐标为')
    print(old_loc_sphere1)
    print(old_loc_sphere2)
    print(old_loc_sphere3)
    print(old_loc_sphere4)


# 退出操作
def quitCut():
    global finish
    # 切割未完成
    if finish == False:
        # all_objs = bpy.data.objects
        # for selected_obj in all_objs:  # 删除用于对比的未被激活的模型
        #     print('name',selected_obj.name)
        #     if (
        #             selected_obj.name != "右耳huanqiecompare" and selected_obj.name != "右耳LocalThickCopy" and selected_obj.name != "右耳DamoCopy" and selected_obj.name != "DamoReset"):
        #         bpy.data.objects.remove(selected_obj, do_unlink=True)

        del_objs = ['Circle', 'Torus', '右耳']

        for obj in del_objs:
            if (bpy.data.objects[obj]):
                obj1 = bpy.data.objects[obj]
                bpy.data.objects.remove(obj1, do_unlink=True)
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=False)
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects["右耳huanqiecompare"]
        obj.hide_set(False)
        bpy.context.view_layer.objects.active = obj
        obj.name = '右耳'
        obj.data.materials.clear()
    # 已切割
    # else:
    #     print('已切割')
    #     print('还原网格')
    #     obj_main = bpy.data.objects['右耳']
    #     oridata.to_mesh(obj_main.data)


def quitStepCut():
    global finish

    # 切割未完成
    if finish == False:
        for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
            if i.name == "右耳":
                bpy.context.view_layer.objects.active = i
                i.select_set(state=True)
        bpy.ops.object.modifier_remove(modifier='step cut', report=False)
        bpy.data.objects['右耳'].data.materials.clear()
        if (bpy.data.objects['StepCutSphere1']):
            obj = bpy.data.objects['StepCutSphere1']
            bpy.data.objects.remove(obj, do_unlink=True)
        if (bpy.data.objects['StepCutSphere2']):
            obj = bpy.data.objects['StepCutSphere2']
            bpy.data.objects.remove(obj, do_unlink=True)
        if (bpy.data.objects['StepCutSphere3']):
            obj = bpy.data.objects['StepCutSphere3']
            bpy.data.objects.remove(obj, do_unlink=True)
        if (bpy.data.objects['StepCutSphere4']):
            obj = bpy.data.objects['StepCutSphere4']
            bpy.data.objects.remove(obj, do_unlink=True)
        if (bpy.data.objects['StepCutplane']):
            obj = bpy.data.objects['StepCutplane']
            bpy.data.objects.remove(obj, do_unlink=True)
        if (bpy.data.objects['右耳ceqieCompare']):
            obj = bpy.data.objects['右耳ceqieCompare']
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=False)
    # 切割已完成
    # else:
    #     print('已切割')
    #     print('还原网格')
    #     obj_main = bpy.data.objects['右耳']
    #     oridata.to_mesh(obj_main.data)


class Circle_Cut(bpy.types.Operator):
    bl_idname = "object.circlecut"
    bl_label = "圆环切割"

    __initial_rotation_x = None  # 初始x轴旋转角度
    __initial_rotation_y = None
    __left_mouse_down = False  # 按下右键未松开时，旋转圆环角度
    __right_mouse_down = False  # 按下右键未松开时，圆环上下移动
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __is_moving = False

    def invoke(self, context, event):

        op_cls = Circle_Cut

        global qiegeenum
        qiegeenum = 1

        print('invokeCir')

        op_cls.__initial_rotation_x = None
        op_cls.__initial_rotation_y = None
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None

        context.window_manager.modal_handler_add(self)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global old_radius, finish
        global scale_ratio, zmax, zmin, on_obj
        op_cls = Circle_Cut

        if context.area:
            context.area.tag_redraw()
        # 未切割时起效
        if finish == False:
            if qiegeenum == 1:
                obj_torus = bpy.data.objects['Torus']
                active_obj = bpy.data.objects['Circle']
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj_torus
                obj_torus.select_set(True)
            # 鼠标是否在圆环上
            if (qiegeenum == 1 and is_mouse_on_object(context, event)):
                # print('在圆环上')

                # bpy.ops.object.select_all(action='DESELECT')
                # bpy.context.view_layer.objects.active = active_obj
                # active_obj.select_set(True)

                if event.type == 'LEFTMOUSE':
                    if event.value == 'PRESS':
                        op_cls.__is_moving = True
                        op_cls.__left_mouse_down = True
                        op_cls.__initial_rotation_x = obj_torus.rotation_euler[0]
                        op_cls.__initial_rotation_y = obj_torus.rotation_euler[1]
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                    # 取消
                    elif event.value == 'RELEASE':
                        normal = active_obj.matrix_world.to_3x3(
                        ) @ active_obj.data.polygons[0].normal
                        print('圆环法线',normal)
                        if normal.z > 0:
                            print('反转法线')
                            active_obj.hide_set(False)
                            bpy.context.view_layer.objects.active = active_obj
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='SELECT')
                            # 翻转圆环法线
                            bpy.ops.mesh.flip_normals(only_clnors=False)
                            # 隐藏圆环
                            active_obj.hide_set(True)
                            # 返回对象模式
                            bpy.ops.object.mode_set(mode='OBJECT')
                        smooth()
                        op_cls.__is_moving = False
                        op_cls.__left_mouse_down = False
                        op_cls.__initial_rotation_x = None
                        op_cls.__initial_rotation_y = None
                        op_cls.__initial_mouse_x = None
                        op_cls.__initial_mouse_y = None
                        
                        
                    return {'RUNNING_MODAL'}

                elif event.type == 'RIGHTMOUSE':
                    if event.value == 'PRESS':
                        op_cls.__is_moving = True
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                    elif event.value == 'RELEASE':
                        smooth()
                        op_cls.__is_moving = False
                        op_cls.__right_mouse_down = False
                        op_cls.__initial_mouse_x = None
                        op_cls.__initial_mouse_y = None

                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # x轴旋转角度
                        rotate_angle_x = (
                                                 event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005
                        rotate_angle_y = (
                                                 event.mouse_region_y - op_cls.__initial_mouse_y) * 0.005
                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                       rotate_angle_x
                        active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                       rotate_angle_y
                        obj_torus.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                      rotate_angle_x
                        obj_torus.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                      rotate_angle_y
                        getRadius()
                        return {'RUNNING_MODAL'}
                    elif op_cls.__right_mouse_down:
                        obj_circle = bpy.data.objects['Circle']
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = 0.25
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal
                        if (op_cls.__now_mouse_y > op_cls.__initial_mouse_y):
                            # print('上移')
                            obj_circle.location -= normal * dis
                            obj_torus.location -= normal * dis
                        elif (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            # print('下移')
                            obj_circle.location += normal * dis
                            obj_torus.location += normal * dis
                        getRadius()
                        return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}
                # return {'RUNNING_MODAL'}

            elif (qiegeenum != 1):
                return {'FINISHED'}

            else:
                # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                obj_torus = bpy.data.objects['Torus']
                active_obj = bpy.data.objects['Circle']
                if event.value == 'RELEASE' and op_cls.__is_moving:
                    normal = active_obj.matrix_world.to_3x3(
                        ) @ active_obj.data.polygons[0].normal
                    print('圆环法线',normal)
                    if normal.z > 0:
                        print('反转法线')
                        active_obj.hide_set(False)
                        bpy.context.view_layer.objects.active = active_obj
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        # 翻转圆环法线
                        bpy.ops.mesh.flip_normals(only_clnors=False)
                        # 隐藏圆环
                        active_obj.hide_set(True)
                        # 返回对象模式
                        bpy.ops.object.mode_set(mode='OBJECT')
                    smooth()
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__right_mouse_down = False
                    op_cls.__initial_rotation_x = None
                    op_cls.__initial_rotation_y = None
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
                if event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # x轴旋转角度
                        rotate_angle_x = (
                                                 event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005
                        rotate_angle_y = (
                                                 event.mouse_region_y - op_cls.__initial_mouse_y) * 0.005
                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                       rotate_angle_x
                        active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                       rotate_angle_y
                        obj_torus.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                      rotate_angle_x
                        obj_torus.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                      rotate_angle_y
                        getRadius()
                        return {'RUNNING_MODAL'}

                    elif op_cls.__right_mouse_down:
                        obj_circle = bpy.data.objects['Circle']
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = 0.25
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal

                        if (op_cls.__now_mouse_y > op_cls.__initial_mouse_y):
                            # print('上移')
                            obj_circle.location -= normal * dis
                            obj_torus.location -= normal * dis
                        elif (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            # print('下移')
                            obj_circle.location += normal * dis
                            obj_torus.location += normal * dis
                        getRadius()
                        return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}

        else:
            return {'PASS_THROUGH'}


class Step_Cut(bpy.types.Operator):
    bl_idname = "object.stepcut"
    bl_label = "阶梯切割"

    _timer = None

    def invoke(self, context, event):
        print('invokeStep')
        global qiegeenum
        qiegeenum = 2
        Step_Cut._timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
        bpy.context.object.data.use_auto_smooth = True
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        update_plane()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if context.area:
            context.area.tag_redraw()

        global qiegeenum
        global finish
        # 未切割时起效
        if finish == False:

            # 鼠标在圆球上
            if (qiegeenum == 2 and is_mouse_on_which_object(context, event) != 5):
                if (is_changed_stepcut(context, event)):
                    bpy.ops.wm.tool_set_by_id(name="builtin.select")

                if (event.type == 'TIMER'):
                    update_plane()
                    return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}

            elif (qiegeenum != 2):
                context.window_manager.event_timer_remove(Step_Cut._timer)
                Step_Cut._timer = None
                print('timer remove')
                return {'FINISHED'}

            elif (is_changed_stepcut(context, event)):
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            return {'PASS_THROUGH'}

        elif (finish == True):
            context.window_manager.event_timer_remove(Step_Cut._timer)
            Step_Cut._timer = None
            print('timer remove')
            return {'FINISHED'}

        else:
            return {'PASS_THROUGH'}


class Finish_Cut(bpy.types.Operator):
    bl_idname = "object.finishcut"
    bl_label = "完成切割"

    def invoke(self, context, event):
        self.excute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context):
        global qiegeenum, finish
        if (qiegeenum == 1):
            # 完成切割
            finish = True
            # 保存圆环信息
            saveCir()
            # all_objs = bpy.data.objects
            # for selected_obj in all_objs:  # 删除用于对比的未被激活的模型
            #     if (selected_obj.name != "右耳"):
            #         bpy.data.objects.remove(selected_obj, do_unlink=True)
            # bpy.ops.outliner.orphans_purge(
            #     do_local_ids=True, do_linked_ids=True, do_recursive=False)

            del_objs = ['Circle', 'Torus', '右耳huanqiecompare']

            for obj in del_objs:
                if (bpy.data.objects[obj]):
                    obj1 = bpy.data.objects[obj]
                    bpy.data.objects.remove(obj1, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)

        if (qiegeenum == 2):
            # 完成切割
            finish = True
            saveStep()
            for i in bpy.context.visible_objects:
                if i.name == "右耳":
                    bpy.context.view_layer.objects.active = i
                    bpy.ops.object.modifier_apply(modifier="step cut")
            for i in bpy.context.visible_objects:
                if i.name == "StepCutplane":
                    i.hide_set(False)
                    bpy.context.view_layer.objects.active = i
                    bpy.ops.object.modifier_apply(modifier="smooth")
            bpy.data.objects.remove(
                bpy.data.objects['StepCutSphere1'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['StepCutSphere2'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['StepCutSphere3'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['StepCutSphere4'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['StepCutplane'], do_unlink=True)
            bpy.data.objects.remove(bpy.data.objects['右耳ceqieCompare'], do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = obj

        return {'FINISHED'}


class Reset_Cut(bpy.types.Operator):
    bl_idname = "object.resetcut"
    bl_label = "重置切割"

    def invoke(self, context, event):
        global finish
        print('invoke')
        if finish == False:
            print('unfinish')
            self.excute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context):
        global qiegeenum
        if (qiegeenum == 1):
            qiegeenum = 4
            all_objs = bpy.data.objects
            for selected_obj in all_objs:  # 删除用于对比的未被激活的模型
                if (selected_obj.name != "右耳huanqiecompare"):
                    bpy.data.objects.remove(selected_obj, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
            bpy.ops.object.select_all(action='DESELECT')
            obj = bpy.data.objects["右耳huanqiecompare"]
            obj.hide_set(False)
            bpy.context.view_layer.objects.active = obj
            obj.name = '右耳'
            obj.data.materials.clear()
            initCircle()

        if (qiegeenum == 2):
            qiegeenum = 4
            # 回到原来的位置
            global old_loc_sphere1, old_loc_sphere2, old_loc_sphere3, old_loc_sphere4
            initsphereloc()
            # 回到原来的位置
            bpy.data.objects['StepCutSphere1'].location = old_loc_sphere1
            bpy.data.objects['StepCutSphere2'].location = old_loc_sphere2
            bpy.data.objects['StepCutSphere3'].location = old_loc_sphere3
            bpy.data.objects['StepCutSphere4'].location = old_loc_sphere4
            bpy.ops.object.stepcut('INVOKE_DEFAULT')

        # if (a == 3):
        #     a = 4
        #     if(bpy.context.scene.qieGeTypeEnum == 'OP1'):
        #         initCircle()
        #     if (bpy.context.scene.qieGeTypeEnum == 'OP2'):
        #         initPlane()

        return {'FINISHED'}


class qiegeTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetcut"
    bl_label = "重置切割"
    bl_description = (
        "点击完成重置操作"
    )
    bl_icon = "ops.mesh.loopcut_slide"
    bl_widget = None
    bl_keymap = (
        ("object.resetcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class qiegeTool2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishcut"
    bl_label = "完成"
    bl_description = (
        "点击完成切割操作"
    )
    bl_icon = "ops.mesh.offset_edge_loops_slide"

    bl_widget = None
    bl_keymap = (
        ("object.finishcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


def frontToQieGe():
    global finish
    finish = False
    # 将当前激活物体复制一份保存,用于切割之后的模块回到切割时还原
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳QieGeCopy"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "QieGeCopy"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    duplicate_obj1.hide_set(False)
    duplicate_obj1.hide_set(True)

    enum = bpy.context.scene.qieGeTypeEnum
    if enum == "OP1":
        initCircle()
    if enum == "OP2":
        initPlane()


def frontFromQieGe():
    global qiegeenum
    enum = bpy.context.scene.qieGeTypeEnum
    if enum == "OP1":
        quitCut()
        initialModelColor()
        bpy.data.objects["右耳"].data.materials.append(bpy.data.materials['yellow'])
    if enum == "OP2":
        quitStepCut()
        initialModelColor()
        bpy.data.objects["右耳"].data.materials.append(bpy.data.materials['yellow'])
    # 将切割模式中运行的Model退出
    qiegeenum = 0


def backToQieGe():
    global finish
    finish = False

    # 根据切割中保存的物体,将其复制一份替换当前激活物体
    name = "右耳"
    obj = bpy.data.objects.get(name)
    copyname = "右耳QieGeCopy"  # TODO    根据导入文件名称更改
    copy_obj = bpy.data.objects.get(copyname)
    #当不存在QieGeCopy时，说明不是顺序执行的，直接跳过了切割这一步，
    if(copy_obj == None):
        lastname = "右耳LocalThickLast"
        last_obj = bpy.data.objects.get(lastname)
        if(last_obj != None):
            copy_obj = last_obj.copy()
            copy_obj.data = last_obj.data.copy()
            copy_obj.animation_data_clear()
            copy_obj.name = name + "QieGeCopy"
            bpy.context.collection.objects.link(copy_obj)
            copy_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            copy_obj = last_obj.copy()
            copy_obj.data = last_obj.data.copy()
            copy_obj.animation_data_clear()
            copy_obj.name = name + "QieGeCopy"
            bpy.context.collection.objects.link(copy_obj)
            copy_obj.hide_set(True)
    moveToRight(copy_obj)
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = copy_obj.copy()
    duplicate_obj.data = copy_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    enum = bpy.context.scene.qieGeTypeEnum
    if enum == "OP1":
        initCircle()
    if enum == "OP2":
        initPlane()


def backFromQieGe():
    # 将切割提交
    global finish
    if (not finish):
        bpy.ops.object.finishcut('INVOKE_DEFAULT')

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳QieGeLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "QieGeLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)


def register():
    bpy.utils.register_class(Circle_Cut)
    bpy.utils.register_class(Step_Cut)
    bpy.utils.register_class(Finish_Cut)
    bpy.utils.register_class(Reset_Cut)

    # bpy.utils.register_tool(qiegeTool, separator=True, group=False)
    # bpy.utils.register_tool(qiegeTool2, separator=True,
    #                         group=False, after={qiegeTool.bl_idname})


def unregister():
    bpy.utils.unregister_class(Circle_Cut)
    bpy.utils.unregister_class(Step_Cut)
    bpy.utils.unregister_class(Finish_Cut)
    bpy.utils.unregister_class(Reset_Cut)

    # bpy.utils.unregister_tool(qiegeTool)
    # bpy.utils.unregister_tool(qiegeTool2)
