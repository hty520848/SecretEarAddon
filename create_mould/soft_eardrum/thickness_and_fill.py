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

operator_obj = '' # 当前操作的物体是左耳还是右耳


def get_direction(start, end):
    direction = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    len = (direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) ** 0.5

    return (direction[0] / len, direction[1] / len, direction[2] / len)


# 获取截面半径
def getRadius(op):
    global old_radius, scale_ratio, now_radius, on_obj,operator_obj

    # 翻转圆环法线
    obj_torus = bpy.data.objects[operator_obj+'Torus']
    obj_circle = bpy.data.objects[operator_obj+'Circle']
    active_obj = bpy.data.objects[operator_obj+'huanqiecompare']
    for selected_obj in bpy.data.objects:
        if (selected_obj.name == operator_obj+"huanqiecompareintersect"):
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
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect',single_user=True)

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
        radius = radius+0.5
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
            vertices=32, radius=12, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD', location=(
                initX, initY, initZ), rotation=(
                0.0, 0.0, 0.0), scale=(
                1.0, 1.0, 1.0))

        # 初始化环体
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(
            initX, initY, initZ), rotation=(0.0, 0, 0), major_segments=80, minor_segments=80, major_radius=old_radius,
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
    for v in select_vert:
        direction = get_direction(v.co, end)
        setp = 0.05
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
    bpy.ops.object.mode_set(mode='OBJECT')


def fill():
    obj = bpy.data.objects["右耳"]
    bpy.context.view_layer.objects.active = obj
    # 首先，根据厚度使用一个实体化修改器
    modifier = obj.modifiers.new(name="Thickness", type='SOLIDIFY')
    bpy.context.object.modifiers["Thickness"].solidify_mode = 'NON_MANIFOLD'
    bpy.context.object.modifiers["Thickness"].thickness = bpy.context.scene.zongHouDu
    bpy.context.object.modifiers["Thickness"].nonmanifold_merge_threshold = 0.35
    bpy.ops.object.modifier_apply(modifier="Thickness", single_user=True)

    # 然后使用布尔修改器切割内壁
    modifier = obj.modifiers.new(name="InsideCut", type='BOOLEAN')
    bpy.context.object.modifiers["InsideCut"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["InsideCut"].object = bpy.data.objects["FillPlane"]
    bpy.context.object.modifiers["InsideCut"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="InsideCut", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    # 这里存一下边界点坐标，用于最后补面
    select_vert_co = [v.co for v in bm.verts if v.select]

    # 删除多余的边角
    bpy.ops.mesh.delete(type='FACE')

    select_vert = []
    for v in bm.verts:
        if v.co in select_vert_co:
            v.select_set(True)
            select_vert.append(v)
    for v in select_vert:
        for edge in v.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in select_vert and edge.verts[1] in select_vert:
                edge.select_set(True)

    bpy.ops.mesh.loop_to_region(select_bigger=True)
    bpy.ops.mesh.select_all(action='INVERT')
    # 删除
    bpy.ops.mesh.delete(type='VERT')

    # # 最后，对空洞进行填充
    for v in select_vert:
        v.select_set(True)

    for v in select_vert:
        for edge in v.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in select_vert and edge.verts[1] in select_vert:
                edge.select_set(True)

    # 删除不在需要的物体
    bpy.ops.mesh.fill()

    # # 删除不在需要的物体
    bpy.data.objects.remove(bpy.data.objects["FillPlane"], do_unlink=True)

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


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
        if (selected_obj.name == obj_name+"huanqiecompare"):
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


def set_finish(is_finish):
    global finish
    finish = is_finish


def saveCir():
    global old_radius, last_loc, last_radius, last_ratation, operator_obj
    obj_torus = bpy.data.objects[operator_obj+'Torus']
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
        global scale_ratio, zmax, zmin, on_obj, operator_obj
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

                obj_torus = bpy.data.objects[operator_obj + 'Torus']
                active_obj = bpy.data.objects[operator_obj + 'Circle']
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj_torus
                obj_torus.select_set(True)

            # 鼠标是否在圆环上
            if (mould_type == "OP1" and is_mouse_on_object(context, event)):
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
                        op_cls.__initial_rotation_z = obj_torus.rotation_euler[2]
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y

                        region, space = get_region_and_space(
                            context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
                        )
                        coord = (op_cls.__initial_mouse_x, op_cls.__initial_mouse_y)

                        hit, face_location, face_normal, face_index, face_object, face_matrix = self.cast_ray(context,
                                                                                                              event)
                        if hit:
                            if face_object.type == 'MESH':
                                ori_x = obj_torus.location.x
                                ori_y = obj_torus.location.y

                                # 判断鼠标位置在圆环的哪个方位
                                co = face_location
                                op_cls.__dx = round(co.x - ori_x, 2)
                                op_cls.__dy = round(co.y - ori_y, 2)

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
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 2)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 2)

                        # 旋转角度
                        rotate_angle_x = (
                                                 event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px
                        rotate_angle_y = (
                                                 event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py
                        rotate_angle_z = (
                                                 event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005
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
                        getRadius('move')
                        return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}
                # return {'RUNNING_MODAL'}

            elif (mould_type != "OP1"):
                return {'FINISHED'}

            else:
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
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 2)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy), 2)
                        # print('px',px)
                        # print('py',py)

                        # 旋转角度
                        rotate_angle_x = (
                                                 event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px
                        rotate_angle_y = (
                                                 event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py
                        rotate_angle_z = (
                                                 event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005
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
                        getRadius('move')
                        return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}

        else:
            return {'PASS_THROUGH'}


def register():
    bpy.utils.register_class(Soft_Eardrum_Circle_Cut)


def unregister():
    bpy.utils.unregister_class(Soft_Eardrum_Circle_Cut)
