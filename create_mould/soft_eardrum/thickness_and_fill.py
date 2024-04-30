import bpy
from bpy import context
from bpy_extras import view3d_utils
import mathutils
import bmesh
from mathutils import Vector
from bpy.types import WorkSpaceTool
from contextlib import redirect_stdout
import io
from ...tool import *
from ...utils.utils import *
import math
from math import *

from ..local_retop import retopo

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

operator_obj = ''  # 当前操作的物体是左耳还是右耳

mouse_loc = None  # 记录鼠标在圆环上的位置
is_saved = False  # 记录圆球的位置是否被保存


bottom_outer_border_co_for_reset = []              #将原本reset_and_refill()函数中的fill()函数拆分到了两个函数中,该数组用于保存中间结果

# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    global mouse_loc,operator_obj

    active_obj = bpy.data.objects[operator_obj+'Torus']
    is_on_object = False  # 初始化变量
    cast_loc = None

    if context.area:
        context.area.tag_redraw()

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    if event.mouse_region_x > region1.width:
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y))
    else:
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    if event.mouse_region_x > region1.width:
        region = region2
        space = area.spaces.active

    ray_dir = view3d_utils.region_2d_to_vector_3d(
        region,
        space.region_3d,
        mv
    )
    ray_orig = view3d_utils.region_2d_to_origin_3d(
        region,
        space.region_3d,
        mv
    )

    start = ray_orig
    end = ray_orig + ray_dir

    # 确定光线和对象的相交
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start
    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            loc, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                co = loc
                mouse_loc = loc
                # print('loc',loc)
                # if(co.x > 0 and co.y >0):
                #     print('右上')
                # elif(co.x < 0 and co.y > 0):
                #     print('左上')
                # elif(co.x < 0 and co.y < 0):
                #     print('左下')
                # elif(co.x > 0 and co.y < 0):
                #     print('右下')
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


def get_direction(start, end):
    direction = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    len = (direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) ** 0.5

    return (direction[0] / len, direction[1] / len, direction[2] / len)


# 获取截面半径
def getRadius(op):
    global old_radius, scale_ratio, now_radius, on_obj, operator_obj

    # 翻转圆环法线
    obj_torus = bpy.data.objects[operator_obj + 'Torus']
    obj_circle = bpy.data.objects[operator_obj + 'Circle']
    active_obj = bpy.data.objects[operator_obj + 'huanqiecompare']
    for selected_obj in bpy.data.objects:
        if (selected_obj.name == operator_obj + "huanqiecompareintersect"):
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
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect', single_user=True)

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
            distance = (vertex.co - obj_torus.location).length
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
        if op == 'move':
            obj_torus.location = center
            obj_circle.location = center
        scale_ratio = round(radius / old_radius, 3)
        # print('缩放比例', scale_ratio)
        obj_torus.scale = (scale_ratio, scale_ratio, 1)


# 计算点到平面的距离
def distance_to_plane(plane_normal, plane_point, point):
    return round(abs(plane_normal.dot(point - plane_point)), 4)


# 初始化圆环颜色
def initialTorusColor():
    yellow_material = bpy.data.materials.new(name="red")
    yellow_material.use_nodes = True
    bpy.data.materials["red"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1.0, 0.0, 0, 1.0)


def draw_cut_plane(obj_name):
    global old_radius, scale_ratio, now_radius, last_loc, last_radius, last_ratation
    global zmax, zmin, oridata, init1, init2, operator_obj

    obj_main = bpy.data.objects[obj_name]
    operator_obj = obj_name

    copyModel(obj_name)
    getModelZ(obj_name)

    initZ = round(zmax * 0.5, 2)

    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)
    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
    center = (0, 0, 0)
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

    initX = center.x
    initY = center.y
    # if obj_name == '左耳':
    #     initY = -initY

    # 正常初始化
    if last_loc == None:
        print('正常初始化')
        # 大圆环
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            # location=((-10.4251, 2.3513, 6.7393))
            location=(initX, initY, initZ)

            ,
            rotation=(0.0, 0.0, 0.0)
            # rotation=(-0.1633, 0.1414, -0.1150)
                , scale=(
                1.0, 1.0, 1.0))

        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD',
                                         # location=((-10.4251, 2.3513, 6.7393))
                                        location=(initX, initY, initZ)
                                         ,
                                         rotation=(0.0, 0, 0)
                                        # rotation=(-0.1633, 0.1414, -0.1150)
                                         , major_segments=80, minor_segments=80, major_radius=old_radius,
                                         minor_radius=0.4)



    else:
        print('切割后初始化')
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(
                last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                1.0, 1.0, 1.0))
        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
            last_ratation[0], last_ratation[1], last_ratation[2]), major_segments=80, minor_segments=80,
                                         major_radius=last_radius, minor_radius=0.4)
        old_radius = last_radius

    obj = bpy.context.active_object
    obj.name = obj_name + 'Torus'
    if obj_name == '右耳':
        moveToRight(obj)
    elif obj_name == '左耳':
        moveToLeft(obj)
    # 环体颜色
    initialTorusColor()
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['red'])
    # 选择圆环
    obj_circle = bpy.data.objects['Circle']
    obj_circle.name = obj_name + 'Circle'
    if obj_name == '右耳':
        moveToRight(obj_circle)
    elif obj_name == '左耳':
        moveToLeft(obj_circle)
    # 物体位于右边窗口
    if obj_name == bpy.context.scene.rightWindowObj:
        override2 = getOverride2()
        with bpy.context.temp_override(**override2):
            # 进入编辑模式
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_circle
            obj_circle.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            # 翻转圆环法线
            bpy.ops.mesh.flip_normals(only_clnors=False)
            # 隐藏圆环
            obj_circle.hide_set(True)
            # 返回对象模式
            bpy.ops.object.mode_set(mode='OBJECT')
    else:
        # 进入编辑模式
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_circle
        obj_circle.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # 翻转圆环法线
        bpy.ops.mesh.flip_normals(only_clnors=False)
        # 隐藏圆环
        obj_circle.hide_set(True)
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')


def get_fill_plane():
    # 取消选择
    for obj in bpy.data.objects:
        obj.select_set(False)

    # 复制一个模型 用于计算补面用的平面
    cur_obj = bpy.data.objects['右耳']
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "ForGetFillPlane"
    bpy.context.collection.objects.link(duplicate_obj)

    # 下面一段代码用于保证布尔后，选中的顶点就是切割边界
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    circle_obj = bpy.data.objects[operator_obj + "Circle"]
    circle_obj.hide_set(False)
    bpy.context.view_layer.objects.active = circle_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    circle_obj.hide_set(True)

    duplicate_obj.hide_set(True)

    obj_main = bpy.data.objects['右耳ForGetFillPlane']
    bpy.context.view_layer.objects.active = obj_main

    # 为模型添加布尔修改器
    modifier = obj_main.modifiers.new(name="PlaneCut", type='BOOLEAN')
    bpy.context.object.modifiers["PlaneCut"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["PlaneCut"].object = bpy.data.objects[operator_obj + "Circle"]
    bpy.context.object.modifiers["PlaneCut"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="PlaneCut", single_user=True)

    obj_main.hide_set(False)

    bpy.ops.object.mode_set(mode='EDIT')
    # 获取编辑模式的网格数据
    bm = bmesh.from_edit_mesh(obj_main.data)

    before_me = bpy.data.objects['右耳'].data
    before_bm = bmesh.new()
    before_bm.from_mesh(before_me)
    before_bm.verts.ensure_lookup_table()
    before_co = [v.co for v in before_bm.verts]

    select_vert = [v for v in bm.verts if v.co not in before_co]
    for v in select_vert:
        v.select_set(True)

    bmesh.update_edit_mesh(obj_main.data)
    end = bpy.data.objects[operator_obj + "Circle"].location
    plane_border_co = []
    thickness = bpy.context.scene.zongHouDu
    for v in select_vert:
        direction = get_direction(v.co, end)
        setp = -1 * thickness / 2
        plane_border_co.append(
            (v.co[0] + direction[0] * setp, v.co[1] + direction[1] * setp, v.co[2] + direction[2] * setp))

    utils_draw_curve(utils_get_order_border_vert(plane_border_co), "FillPlane", 0)
    # 删除不在需要的物体
    bpy.data.objects.remove(duplicate_obj, do_unlink=True)

    plane_obj = bpy.data.objects["FillPlane"]
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        bpy.ops.mesh.remove_doubles(threshold=0.5)
    del stdout

    bpy.ops.mesh.fill()

    # 如果平面法线方向是向上的，那么反转法向
    if judge_fill_plane_normals():
        bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects["FillPlane"].select_set(False)

def judge_fill_plane_normals():
    cut_plane = bpy.data.objects["FillPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)
    sum = 0
    for v in cut_plane_mesh.verts:
        sum += v.normal[2]
    return sum > 0

def fill():
    obj = bpy.data.objects["右耳"]
    bpy.context.view_layer.objects.active = obj
    # 局部重拓扑
    if not bpy.data.objects.get("RetopoPlane"):
        bpy.data.objects["CutPlane"].name = "RetopoPlane"
        retopo(obj.name,"BottomOuterBorderVertex",0.5)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.2)

    # 记录外边界顶点坐标
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    ndigits = 1
    bottom_outer_border_co = [(round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits)) for v in
                              bm.verts if v.select]

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 首先，根据厚度使用一个实体化修改器
    modifier = obj.modifiers.new(name="Thickness", type='SOLIDIFY')
    bpy.context.object.modifiers["Thickness"].solidify_mode = 'NON_MANIFOLD'
    bpy.context.object.modifiers["Thickness"].thickness = bpy.context.scene.zongHouDu
    bpy.ops.object.modifier_apply(modifier="Thickness", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.mesh.select_all(action='DESELECT')

    # 由于实体化后顶点index会变，所以用坐标存外边界，但也会有些许误差，所以这里舍入两位小数
    bottom_outer_border_index = []
    for v in bm.verts:
        if (round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits)) in bottom_outer_border_co:
            bottom_outer_border_index.append(v.index)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()

    all_border = [v.index for v in bm.verts if v.select]

    bottom_inner_border_index = [i for i in all_border if i not in bottom_outer_border_index]

    bpy.ops.mesh.select_all(action='DESELECT')
    bm.verts.ensure_lookup_table()
    for i in bottom_inner_border_index:
        bm.verts[i].select_set(True)

    # 处理实体化后外边界顶点组多出的顶点
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("BottomInnerBorderVertex", bottom_inner_border_index)

    # 分离出内外壁，用于布尔切割
    main_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_linked(delimit=set())

    mesh = main_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    inner_index = [v.index for v in bm.verts if v.select]

    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Inner", inner_index)
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != "右耳":
                inner_obj = o
                bpy.context.view_layer.objects.active = inner_obj
            else:
                o.select_set(False)

                # 然后使用布尔修改器切割内壁
    utils_bool_difference(inner_obj.name, "FillPlane")

    # 切割完成后，设置切割边界顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = inner_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    cut_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CutBorderVertex", cut_border_index)
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.loop_to_region(select_bigger=True)
    # 删除上部分不要的顶点
    delete_top_part(inner_obj)

    # 对空洞进行填充
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CutBorderVertex')
    bpy.ops.object.vertex_group_select()

    # bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.edge_face_add()

    bpy.ops.mesh.select_all(action='DESELECT')

    # 删除不在需要的物体
    bpy.data.objects.remove(bpy.data.objects["FillPlane"], do_unlink=True)

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')

    smooth_inner_plane(inner_obj)

    # 最后，合并内外壁并桥接底边
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    inner_obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects["RetopoPlane"].hide_set(True)

    # bpy.data.objects.remove(bpy.data.objects["RetopoPlane"], do_unlink=True)


# 计算点到平面的距离
def distance_to_plane(plane_normal, plane_point, point):
    return round(abs(plane_normal.dot(point - plane_point)), 4)


# 根据点到平面的距离，计算移动的长度
def displacement(distance, a, b):
    dis = a * (distance - b) * (distance - b)
    return dis


def smooth_inner_plane(inner_obj):
    global operator_obj
    obj_circle = bpy.data.objects[operator_obj + 'Circle']
    bpy.ops.object.mode_set(mode='EDIT')

    mesh = inner_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.vertex_group_set_active(group='CutBorderVertex')
    bpy.ops.object.vertex_group_select()
    for _ in range(0,3):
        bpy.ops.mesh.select_more()

    select_vert = [v for v in bm.verts if v.select]

    # 圆环平面法向量和平面上一点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()

    smooth_vert = list()
    max_distance = 0
    for v in select_vert:
        dis = distance_to_plane(plane_normal, plane_point, v.co)
        if dis < 1:
            smooth_vert.append(v)
            max_distance = max(dis, max_distance)
    bpy.ops.mesh.select_all(action='DESELECT')


    for v in smooth_vert:
        distance = distance_to_plane(plane_normal, plane_point, v.co)
        move = displacement(distance, 0.5, max_distance)
        center = plane_point.copy()
        to_center = v.co - center
        # 计算径向位移的增量
        movement = to_center.normalized() * move
        v.co -= movement

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


def delete_top_part(obj):
    # 判断是否选择的是上半部分
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    # 获取内壁最高点，用于判断需要切割的部分
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    highest_index = vert_order_by_z[0].index
    bm.verts.ensure_lookup_table()

    select_vert_index = [v.index for v in bm.verts if v.select]
    if len(select_vert_index) == len(bm.verts):  # 如果全选了，说明被布尔切掉了，不需要再删除了
        pass
    else:
        if not bm.verts[highest_index].select:
            bpy.ops.mesh.select_all(action='INVERT')

        bpy.ops.object.vertex_group_set_active(group='CutBorderVertex')
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.delete(type='VERT')


def soft_eardrum():
    draw_cut_plane("右耳")
    bpy.ops.object.softeardrumcirclecut('INVOKE_DEFAULT')
    get_fill_plane()
    fill()


# 复制初始模型，并赋予透明材质
def copyModel(obj_name):
    # 获取当前选中的物体
    obj_ori = bpy.data.objects[obj_name]
    # 复制物体用于对比突出加厚的预览效果
    obj_all = bpy.data.objects
    copy_compare = True  # 判断是否复制当前物体作为透明的参照,不存在参照物体时默认会复制一份新的参照物体
    for selected_obj in obj_all:
        if (selected_obj.name == obj_name + "huanqiecompare"):
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
        duplicate_obj.hide_set(True)
        if obj_name == '右耳':
            moveToRight(duplicate_obj)
        elif obj_name == '左耳':
            moveToLeft(duplicate_obj)


# 获取模型的Z坐标范围
def getModelZ(obj_name):
    global zmax, zmin
    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects[obj_name]
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


# 重置回到底部切割完成
def reset_to_after_cut():
    need_to_delete_model_name_list = ["右耳", "FillPlane", "右耳ForGetFillPlane"]
    for obj in bpy.context.view_layer.objects:
        if obj.name in need_to_delete_model_name_list:
            bpy.data.objects.remove(obj, do_unlink=True)
    obj = bpy.data.objects["右耳huanqiecompare"]
    obj.name = "右耳"
    obj.hide_set(False)
    # 重新获取平面并且完成切割填充
    copyModel("右耳")
    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]


def reset_and_refill():
    try:
        # 首先reset到切割完成
        reset_to_after_cut()
        get_fill_plane()
        fill()
        utils_re_color("右耳", (1, 0.319, 0.133))
        utils_re_color("右耳huanqiecompare", (1, 0.319, 0.133))

    except:
        reset_to_after_cut()
        utils_re_color("右耳", (1, 1, 0))
        utils_re_color("右耳huanqiecompare", (1, 1, 0))


#跟新厚度参数时,通过实体化修改器修改厚度   当不存在实体化修改器时,将当前模型恢复为切割后的单层模型,添加圆环的切割平面和实体化修改器
def reset_and_refill_initial():
    global bottom_outer_border_co_for_reset

    reset_to_after_cut()
    get_fill_plane()


    obj = bpy.data.objects["右耳"]
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.2)

    # 记录外边界顶点坐标
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    ndigits = 2
    bottom_outer_border_co_for_reset = [(round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits)) for v in
                              bm.verts if v.select]

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 首先，根据厚度使用一个实体化修改器
    modifier = obj.modifiers.new(name="Thickness", type='SOLIDIFY')
    bpy.context.object.modifiers["Thickness"].solidify_mode = 'NON_MANIFOLD'
    bpy.context.object.modifiers["Thickness"].thickness = bpy.context.scene.zongHouDu




#将实体化修改器提交,根据圆环确定的切割平面添加布尔修改器进行切割
def refill_submit():
    global bottom_outer_border_co_for_reset

    bpy.ops.object.modifier_apply(modifier="Thickness", single_user=True)


    obj = bpy.data.objects["右耳"]
    bpy.context.view_layer.objects.active = obj
    mesh = obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    ndigits = 2
    # bottom_outer_border_co = [(round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits)) for v in
    #                           bm.verts if v.select]




    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.mesh.select_all(action='DESELECT')

    # 由于实体化后顶点index会变，所以用坐标存外边界，但也会有些许误差，所以这里舍入两位小数
    bottom_outer_border_index = []
    for v in bm.verts:
        if (round(v.co[0], ndigits), round(v.co[1], ndigits), round(v.co[2], ndigits)) in bottom_outer_border_co_for_reset:
            bottom_outer_border_index.append(v.index)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()

    all_border = [v.index for v in bm.verts if v.select]

    bottom_inner_border_index = [i for i in all_border if i not in bottom_outer_border_index]

    bpy.ops.mesh.select_all(action='DESELECT')
    bm.verts.ensure_lookup_table()
    for i in bottom_inner_border_index:
        bm.verts[i].select_set(True)

    # 处理实体化后外边界顶点组多出的顶点
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("BottomInnerBorderVertex", bottom_inner_border_index)

    # 分离出内外壁，用于布尔切割
    main_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_linked(delimit=set())

    mesh = main_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    inner_index = [v.index for v in bm.verts if v.select]

    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Inner", inner_index)
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != "右耳":
                inner_obj = o
                bpy.context.view_layer.objects.active = inner_obj
            else:
                o.select_set(False)

                # 然后使用布尔修改器切割内壁
    modifier = inner_obj.modifiers.new(name="InsideCut", type='BOOLEAN')
    bpy.context.object.modifiers["InsideCut"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["InsideCut"].object = bpy.data.objects["FillPlane"]
    bpy.context.object.modifiers["InsideCut"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="InsideCut", single_user=True)

    # 切割完成后，设置切割边界顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = inner_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    cut_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CutBorderVertex", cut_border_index)
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.loop_to_region(select_bigger=True)
    # 删除上部分不要的顶点
    delete_top_part(inner_obj)

    # 对空洞进行填充
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CutBorderVertex')
    bpy.ops.object.vertex_group_select()

    # bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.edge_face_add()

    bpy.ops.mesh.select_all(action='DESELECT')

    # 删除不在需要的物体
    bpy.data.objects.remove(bpy.data.objects["FillPlane"], do_unlink=True)

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 最后，合并内外壁并桥接底边
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    inner_obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.object.mode_set(mode='OBJECT')

def soft_eardrum_smooth_initial():

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    cur_obj_name = "右耳"
    cur_obj = bpy.data.objects.get(cur_obj_name)

    if (cur_obj != None):
        soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
        soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
        if(soft_eardrum_bottom_outer_vertex != None and soft_eardrum_bottom_inner_vertex != None):
            bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerVertex")
            if (soft_eardrum_outer_vertex == None):
                soft_eardrum_outer_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumInnerVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.loop_to_region()
            bpy.ops.mesh.loop_to_region(select_bigger=False)
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterVertex")
            if (soft_eardrum_inner_vertex == None):
                soft_eardrum_inner_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumOuterVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')



            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.subdivide()
            bpy.ops.mesh.subdivide(number_cuts=2)
            bpy.ops.mesh.remove_doubles(threshold=0.15)
            bpy.ops.object.mode_set(mode='OBJECT')

            bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
            bottom_innner_border_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
            if (bottom_outer_border_vertex != None and bottom_innner_border_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.mode_set(mode='OBJECT')

                # 将选中的顶点范围扩大
                bpy.ops.object.mode_set(mode='EDIT')
                for i in range(6):
                    bpy.ops.mesh.select_more()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='OBJECT')
                soft_eardrum_select_vertex = cur_obj.vertex_groups.get("SoftEarDrumSelectVertex")
                if (soft_eardrum_select_vertex == None):
                    soft_eardrum_select_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumSelectVertex")
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                # 添加平滑修改器
                modifier_name = "SoftEarDrumOuterSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "BottomOuterBorderVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumOuterSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].factor = 1.6
                bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].iterations = 2

                modifier_name = "SoftEarDrumInnerSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "BottomInnerBorderVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumInnerSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].factor = 1.6
                bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].iterations = 2

                modifier_name = "SoftEarDrumAllInnerSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "SoftEarDrumInnerVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumAllInnerSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumAllInnerSmoothModifier"].factor = 0.8
                bpy.context.object.modifiers["SoftEarDrumAllInnerSmoothModifier"].iterations = 16



def set_finish(is_finish):
    global finish
    finish = is_finish


def saveCir():
    global old_radius, last_loc, last_radius, last_ratation, operator_obj
    obj_torus = bpy.data.objects[operator_obj + 'Torus']
    last_loc = obj_torus.location.copy()
    last_radius = round(old_radius * obj_torus.scale[0], 2)
    last_ratation = obj_torus.rotation_euler.copy()


class Soft_Eardrum_Circle_Cut(bpy.types.Operator):
    bl_idname = "object.softeardrumcirclecut"
    bl_label = "圆环切割"

    __initial_rotation_x = None  # 初始x轴旋转角度
    __initial_rotation_y = None
    __initial_rotation_z = None
    __left_mouse_down = False  # 按下右键未松开时，旋转圆环角度
    __right_mouse_down = False  # 按下右键未松开时，圆环上下移动
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __is_moving = False
    __dx = 0;
    __dy = 0;

    def cast_ray(self, context, event):

        # cast ray from mouse location, return data from ray
        scene = context.scene
        #   region = context.region
        #   rv3d = context.region_data

        # 左边窗口区域
        override1 = getOverride()
        override2 = getOverride2()
        region1 = override1['region']
        region2 = override2['region']
        area1 = override1['area']
        area2 = override2['area']
        if (event.mouse_region_x > region1.width):
            #   print('右窗口')
            coord = event.mouse_region_x - region1.width, event.mouse_region_y
            region = region2
            rv3d = area2.spaces.active.region_3d
        else:
            #   print('左窗口')
            coord = event.mouse_region_x, event.mouse_region_y
            region = region1
            rv3d = area1.spaces.active.region_3d
        viewlayer = context.view_layer.depsgraph
        # get the ray from the viewport and mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        hit, location, normal, index, object, matrix = scene.ray_cast(viewlayer, ray_origin, view_vector)
        return hit, location, normal, index, object, matrix

    def invoke(self, context, event):

        op_cls = Soft_Eardrum_Circle_Cut

        print('invokeCir')

        op_cls.__initial_rotation_x = None
        op_cls.__initial_rotation_y = None
        op_cls.__initial_rotation_z = None
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
        global scale_ratio, zmax, zmin, on_obj, operator_obj,mouse_loc,last_ratation
        op_cls = Soft_Eardrum_Circle_Cut
        mould_type = bpy.context.scene.muJuTypeEnum

        if context.area:
            context.area.tag_redraw()
        # 未切割时起效
        if finish == False:
            if mould_type == "OP1":
                mouse_x = event.mouse_x
                mouse_y = event.mouse_y
                override1 = getOverride()
                area = override1['area']
                override2 = getOverride2()
                area2 = override2['area']

                workspace = bpy.context.window.workspace.name
                # 双窗口模式下
                if workspace == '布局.001':
                    # 根据鼠标位置判断当前操作窗口
                    if (mouse_x > area.width and mouse_y > area2.y):
                        # print('右窗口')
                        operator_obj = context.scene.rightWindowObj
                    else:
                        # print('左窗口')
                        operator_obj = context.scene.leftWindowObj

                obj_torus = bpy.data.objects.get(operator_obj + 'Torus')
                if obj_torus == None:
                    # 正常初始化
                    if last_loc == None:
                        # 初始化环体
                        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(
                            0, 0, 0), rotation=(0.0, 0, 0), major_segments=80, minor_segments=80,
                                                         major_radius=old_radius,
                                                         minor_radius=0.4)

                    else:
                        # 初始化环体
                        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
                            last_ratation[0], last_ratation[1], last_ratation[2]), major_segments=80, minor_segments=80,
                                                         major_radius=last_radius, minor_radius=0.4)
                        old_radius = last_radius

                    obj = bpy.context.active_object
                    obj.name = operator_obj + 'Torus'
                    if operator_obj == '右耳':
                        moveToRight(obj)
                    elif operator_obj == '左耳':
                        moveToLeft(obj)
                    # 环体颜色
                    initialTorusColor()
                    obj.data.materials.clear()
                    obj.data.materials.append(bpy.data.materials['red'])
                    obj_torus = bpy.data.objects.get(operator_obj + 'Torus')

                active_obj = bpy.data.objects.get(operator_obj + 'Circle')
                if active_obj == None:
                    # 正常初始化
                    if last_loc == None:
                        # 大圆环
                        bpy.ops.mesh.primitive_circle_add(
                            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                            align='WORLD', location=(
                                0, 0, 0), rotation=(
                                0.0, 0.0, 0.0), scale=(
                                1.0, 1.0, 1.0))
                    else:
                        bpy.ops.mesh.primitive_circle_add(
                            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                            align='WORLD',
                            location=last_loc, rotation=(
                                last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                                1.0, 1.0, 1.0))
                        old_radius = last_radius
                    obj = bpy.context.active_object
                    obj.name = operator_obj + 'Circle'
                    obj.hide_set(True)
                    if operator_obj == '右耳':
                        moveToRight(obj)
                    elif operator_obj == '左耳':
                        moveToLeft(obj)
                    active_obj = bpy.data.objects.get(operator_obj + 'Circle')

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj_torus
                obj_torus.select_set(True)

            # 鼠标是否在圆环上
            if (mould_type == "OP1" and is_mouse_on_object(context, event)):
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj_torus
                obj_torus.select_set(True)

                if event.type == 'LEFTMOUSE':
                    if event.value == 'PRESS':
                        op_cls.__is_moving = True
                        op_cls.__left_mouse_down = True
                        op_cls.__initial_rotation_x = obj_torus.rotation_euler[0]
                        op_cls.__initial_rotation_y = obj_torus.rotation_euler[1]
                        op_cls.__initial_rotation_z = obj_torus.rotation_euler[2]
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y

                        op_cls.__dx = round(mouse_loc.x, 2)
                        op_cls.__dy = round(mouse_loc.y, 2)

                    # 取消
                    elif event.value == 'RELEASE':
                        normal = active_obj.matrix_world.to_3x3(
                        ) @ active_obj.data.polygons[0].normal
                        if normal.z > 0:
                            print('圆环法线', normal)
                            print('反转法线')
                            override1 = getOverride()
                            override2 = getOverride2()
                            region1 = override1['region']
                            region2 = override2['region']
                            if event.mouse_region_x > region1.width:
                                with bpy.context.temp_override(**override2):
                                    active_obj.hide_set(False)
                                    bpy.context.view_layer.objects.active = active_obj
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    bpy.ops.mesh.select_all(action='SELECT')
                                    # 翻转圆环法线
                                    # bpy.ops.mesh.flip_normals(only_clnors=False)
                                    bpy.ops.mesh.flip_normals()
                                    # bpy.ops.mesh.normals_make_consistent(inside=True)
                                    # 隐藏圆环
                                    active_obj.hide_set(True)
                                    # 返回对象模式
                                    bpy.ops.object.mode_set(mode='OBJECT')
                                    print('反转后法线', active_obj.matrix_world.to_3x3(
                                    ) @ active_obj.data.polygons[0].normal)
                            else:
                                active_obj.hide_set(False)
                                bpy.context.view_layer.objects.active = active_obj
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.select_all(action='SELECT')
                                # 翻转圆环法线
                                # bpy.ops.mesh.flip_normals(only_clnors=False)
                                bpy.ops.mesh.flip_normals()
                                # bpy.ops.mesh.normals_make_consistent(inside=True)
                                # 隐藏圆环
                                active_obj.hide_set(True)
                                # 返回对象模式
                                bpy.ops.object.mode_set(mode='OBJECT')
                                print('反转后法线', active_obj.matrix_world.to_3x3(
                                ) @ active_obj.data.polygons[0].normal)
                        reset_and_refill()
                        # soft_eardrum_smooth_initial()
                        # bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()
                        saveCir()
                        op_cls.__is_moving = False
                        op_cls.__left_mouse_down = False
                        op_cls.__initial_rotation_x = None
                        op_cls.__initial_rotation_y = None
                        op_cls.__initial_rotation_z = None
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
                        reset_and_refill()
                        # soft_eardrum_smooth_initial()
                        # bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()
                        op_cls.__is_moving = False
                        op_cls.__right_mouse_down = False
                        op_cls.__initial_mouse_x = None
                        op_cls.__initial_mouse_y = None

                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # 旋转角度正负号
                        if (op_cls.__dy < 0):
                            symx = -1;
                        else:
                            symx = 1;

                        if (op_cls.__dx > 0):
                            symy = -1;
                        else:
                            symy = 1;

                        # x,y轴旋转比例
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 4)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 4)

                        # 旋转角度
                        rotate_angle_x = round((
                                                       event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                        rotate_angle_y = round((
                                                       event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                        rotate_angle_z = round((
                                                       event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)

                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                       rotate_angle_x * symx
                        active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                       rotate_angle_y * symy
                        active_obj.rotation_euler[2] = op_cls.__initial_rotation_z + \
                                                       rotate_angle_z

                        obj_torus.rotation_euler[0] = active_obj.rotation_euler[0]
                        obj_torus.rotation_euler[1] = active_obj.rotation_euler[1]
                        obj_torus.rotation_euler[2] = active_obj.rotation_euler[2]

                        getRadius('rotate')
                        return {'RUNNING_MODAL'}
                    elif op_cls.__right_mouse_down:
                        obj_circle = bpy.data.objects[operator_obj + 'Circle']
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal

                        dis = event.mouse_region_y - op_cls.__initial_mouse_y
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        print('距离', dis)
                        obj_circle.location -= normal * dis * 0.05
                        obj_torus.location -= normal * dis * 0.05

                        getRadius('move')
                        return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}
                # return {'RUNNING_MODAL'}

            elif (mould_type != "OP1"):
                return {'FINISHED'}

            else:
                tar_obj = bpy.data.objects[operator_obj]
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = tar_obj
                tar_obj.select_set(True)
                # print('不在圆环上')
                # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                obj_torus = bpy.data.objects[operator_obj + 'Torus']
                active_obj = bpy.data.objects[operator_obj + 'Circle']
                if event.value == 'RELEASE' and op_cls.__is_moving:
                    normal = active_obj.matrix_world.to_3x3(
                    ) @ active_obj.data.polygons[0].normal
                    if normal.z > 0:
                        print('圆环法线', normal)
                        print('反转法线')
                        override1 = getOverride()
                        override2 = getOverride2()
                        region1 = override1['region']
                        region2 = override2['region']
                        # 右窗口
                        if event.mouse_region_x > region1.width:
                            with bpy.context.temp_override(**override2):
                                active_obj.hide_set(False)
                                bpy.context.view_layer.objects.active = active_obj
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.select_all(action='SELECT')
                                # 翻转圆环法线
                                # bpy.ops.mesh.flip_normals(only_clnors=False)
                                bpy.ops.mesh.flip_normals()
                                # bpy.ops.mesh.normals_make_consistent(inside=True)
                                # 隐藏圆环
                                active_obj.hide_set(True)
                                # 返回对象模式
                                bpy.ops.object.mode_set(mode='OBJECT')
                                print('反转后法线', active_obj.matrix_world.to_3x3(
                                ) @ active_obj.data.polygons[0].normal)
                        else:
                            active_obj.hide_set(False)
                            bpy.context.view_layer.objects.active = active_obj
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='SELECT')
                            # 翻转圆环法线
                            # bpy.ops.mesh.flip_normals(only_clnors=False)
                            bpy.ops.mesh.flip_normals()
                            # bpy.ops.mesh.normals_make_consistent(inside=True)
                            # 隐藏圆环
                            active_obj.hide_set(True)
                            # 返回对象模式
                            bpy.ops.object.mode_set(mode='OBJECT')
                            print('反转后法线', active_obj.matrix_world.to_3x3(
                            ) @ active_obj.data.polygons[0].normal)
                    reset_and_refill()
                    # soft_eardrum_smooth_initial()
                    # bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()
                    saveCir()
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__right_mouse_down = False
                    op_cls.__initial_rotation_x = None
                    op_cls.__initial_rotation_y = None
                    op_cls.__initial_rotation_z = None
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None

                if event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # 旋转正负号
                        if (op_cls.__dy < 0):
                            symx = -1;
                        else:
                            symx = 1;

                        if (op_cls.__dx > 0):
                            symy = -1;
                        else:
                            symy = 1;

                        # print('symx',symx)
                        # print('symy',symy)

                        #  x,y轴旋转比例
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 4)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 4)
                        # print('px',px)
                        # print('py',py)

                        # 旋转角度
                        rotate_angle_x = round((
                                                       event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                        rotate_angle_y = round((
                                                       event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                        rotate_angle_z = round((
                                                       event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)

                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                       rotate_angle_x * symx
                        active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                       rotate_angle_y * symy
                        active_obj.rotation_euler[2] = op_cls.__initial_rotation_z + \
                                                       rotate_angle_z
                        obj_torus.rotation_euler[0] = active_obj.rotation_euler[0]
                        obj_torus.rotation_euler[1] = active_obj.rotation_euler[1]
                        obj_torus.rotation_euler[2] = active_obj.rotation_euler[2]

                        getRadius('rotate')
                        return {'RUNNING_MODAL'}

                    elif op_cls.__right_mouse_down:
                        obj_circle = bpy.data.objects[operator_obj + 'Circle']
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal

                        dis = event.mouse_region_y - op_cls.__initial_mouse_y
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        print('距离', dis)
                        obj_circle.location -= normal * dis * 0.05
                        obj_torus.location -= normal * dis * 0.05
                        getRadius('move')
                        return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}

        else:
            return {'PASS_THROUGH'}


def register():
    bpy.utils.register_class(Soft_Eardrum_Circle_Cut)


def unregister():
    bpy.utils.unregister_class(Soft_Eardrum_Circle_Cut)
