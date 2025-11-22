import bpy
import bmesh
import mathutils
import math
import re
import time
from math import *
from bpy import context
from bpy_extras import view3d_utils
from mathutils import Vector, Euler
from bpy.types import WorkSpaceTool
from ..tool import moveToRight, moveToLeft, newMaterial, getOverride2, is_mouse_on_object, \
    is_mouse_on_which_object, is_changed_stepcut, get_cast_index, get_region_and_space, utils_re_color, \
    set_vert_group, delete_vert_group, apply_material,\
    track_time, reset_time_tracker
from ..parameter import set_switch_time, get_switch_time, set_switch_flag, get_switch_flag, check_modals_running, \
    get_mirror_context, set_mirror_context, get_process_var_list
from ..register_tool import unregister_tools
from ..global_manager import global_manager
from ..back_and_forward import record_state, backup_state, forward_state


############ 侧切、环切公用的全局变量 ############
# qiegeenum = 1  # 当前切割的模式，1为环切，2为侧切
operator_obj = ''  # 当前操作的物体是左耳还是右耳
zmax = 0  # 物体z坐标的最大值，用于初始化
zmin = 0  # 物体z坐标的最小值，用于初始化
finish = False  # 是否点击了完成按钮
finishL = False
############ 环切用到的全局变量 ############
old_radius = 8.0
now_radius = 0
scale_ratio = 1

# 圆环是否在物体上
on_obj = True
# 切割时的圆环信息（右耳）
right_last_loc = None
right_last_radius = None
right_last_ratation = None
# 切割时的圆环信息 （左耳）
left_last_loc = None
left_last_radius = None
left_last_ratation = None

mouse_loc = None  # 记录鼠标在圆环上的位置
max_radius = None  # 记录当前圆环的半径
circle_cut_modal_start = False
############ 侧切用到的全局变量 ############
# 记录右耳4个点的位置
r_old_loc_sphere1 = []
r_old_loc_sphere2 = []
r_old_loc_sphere3 = []
r_old_loc_sphere4 = []

# 记录左耳4个点的位置
l_old_loc_sphere1 = []
l_old_loc_sphere2 = []
l_old_loc_sphere3 = []
l_old_loc_sphere4 = []

loc_spheres_index = []  # 用于保存侧切4个点的index,方便镜像
loc_saved_right = False  # 记录圆球的位置是否被保存(右耳)
loc_saved_left = False  # 记录圆球的位置是否被保存(左耳)
step_cut_modal_start = False

right_last_loc_list = []
right_last_ratation_list = []
left_last_loc_list = []
left_last_ratation_list = []


def register_qiege_globals():
    global right_last_loc_list, right_last_ratation_list, left_last_loc_list, left_last_ratation_list
    global right_last_loc, left_last_loc, right_last_ratation, left_last_ratation, right_last_radius, left_last_radius
    global old_radius
    global finish, finishL
    if right_last_loc is not None:
        right_last_loc_list = right_last_loc[:]
        right_last_ratation_list = right_last_ratation[:]
    if left_last_loc is not None:
        left_last_loc_list = left_last_loc[:]
        left_last_ratation_list = left_last_ratation[:]
    global_manager.register("old_radius", old_radius)
    global_manager.register("right_last_loc_list", right_last_loc_list)
    global_manager.register("right_last_radius", right_last_radius)
    global_manager.register("right_last_ratation_list", right_last_ratation_list)
    global_manager.register("left_last_loc_list", left_last_loc_list)
    global_manager.register("left_last_radius", left_last_radius)
    global_manager.register("left_last_ratation_list", left_last_ratation_list)
    global_manager.register("finish", finish)
    global_manager.register("finishL", finishL)


def load_qiege_globals():
    global right_last_loc_list, right_last_ratation_list, left_last_loc_list, left_last_ratation_list
    global right_last_loc, left_last_loc, right_last_ratation, left_last_ratation
    if len(right_last_loc_list) != 0:
        right_last_loc = Vector(right_last_loc_list)
        right_last_ratation = Euler(right_last_ratation_list, 'XYZ')
    if len(left_last_loc_list) != 0:
        left_last_loc = Vector(left_last_loc_list)
        left_last_ratation = Euler(left_last_ratation_list, 'XYZ')


def qiege_backup():
    backup_state()


def qiege_forward():
    forward_state()


# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    global mouse_loc, operator_obj

    active_obj = bpy.data.objects[operator_obj + 'Torus']
    # print('active',active_obj.name)
    is_on_object = False  # 初始化变量

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    if event.mouse_region_x > region1.width:
        # 获取属性栏高度
        area_prop = [area for area in bpy.context.screen.areas if area.type == 'PROPERTIES']
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y - area_prop[0].height))
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
        if active_obj.mode == 'OBJECT':
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            loc, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                mouse_loc = loc
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


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

        if obj_name == '右耳':
            moveToRight(duplicate_obj)
        elif obj_name == '左耳':
            moveToLeft(duplicate_obj)


# 计算点到平面的距离
def distance_to_plane(plane_normal, plane_point, point):
    return round(abs(plane_normal.dot(point - plane_point)), 4)


# 根据点到平面的距离，计算移动的长度
def displacement(distance, a, b):
    dis = a * (distance - b) * (distance - b)
    return dis


# 计算距离圆环中心的距离，用于限制平滑的范围
def dis_smooth(vert, cir):
    dis = (vert - cir).length
    return dis


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


# 删除多余部分
def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
    bpy.ops.object.vertex_group_select()

    # 补面
    bpy.ops.mesh.fill()

    # 选择循环点
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        # 判断最低点是否被选择
        invert_flag = judge_if_need_invert()

        if invert_flag:
            # 不需要反转，直接删除面即可
            bpy.ops.mesh.delete(type='FACE')
        else:
            # 反转一下，删除顶点
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

    # 最后，删一下边界的直接的面
    name = bpy.context.scene.leftWindowObj
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = bpy.data.objects[name].vertex_groups.get("CircleCutBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')


# 平滑边缘
def apply_circle_cut(obj_name):
    global now_radius, on_obj, max_radius
    track_time("边缘切割开始")
    obj_ori = bpy.data.objects[obj_name + 'huanqiecompare']
    obj_main = bpy.data.objects[obj_name]
    obj_circle = bpy.data.objects[obj_name + 'Circle']
    obj_torus = bpy.data.objects[obj_name + 'Torus']
    if obj_name == '右耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiR
    elif obj_name == '左耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiL
    # 从透明对比物体 获取原始网格数据
    # orime = obj_ori.data
    # oribm = bmesh.new()
    # oribm.from_mesh(orime)
    # # 应用原始网格数据
    # oribm.to_mesh(obj_main.data)
    # oribm.free()
    duplicate_obj = obj_ori.copy()
    duplicate_obj.data = obj_ori.data.copy()
    duplicate_obj.name = obj_ori.name + "huanqiecomparecopy"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)

    if obj_name == '右耳':
        moveToRight(duplicate_obj)
    elif obj_name == '左耳':
        moveToLeft(duplicate_obj)
    bpy.data.objects.remove(obj_main, do_unlink=True)
    duplicate_obj.name = obj_name
    obj_main = duplicate_obj
    apply_material()

    # 不存在，则添加
    # if not obj_main.modifiers:
    #     bool_modifier = obj_main.modifiers.new(
    #         name=obj_name+"Boolean Modifier", type='BOOLEAN')
    #     bool_modifier.operation = 'DIFFERENCE'
    #     bool_modifier.object = obj_circle
    #     bool_modifier.solver = 'EXACT'

    # print('物体',obj_main.name)
    # print('修改器',obj_main.modifiers[0].name)

    # 圆环在物体上，则进行平滑
    if on_obj:
        # 应用修改器
        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = obj_main
        # obj_main.select_set(True)

        # modifier_name = obj_name+"Boolean Modifier"
        # target_modifier = None
        # for modifier in obj_main.modifiers:
        #     if modifier.name == modifier_name:
        #         target_modifier = modifier
        # if (target_modifier != None):
        #     target_modifier.object = obj_circle
        #     bpy.ops.object.modifier_apply(modifier=modifier_name,single_user=True)

        # 存一下原先的顶点
        obj_main.select_set(True)
        bpy.context.view_layer.objects.active = obj_main
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bm = bmesh.from_edit_mesh(obj_main.data)
        ori_border_index = [v.index for v in bm.verts if v.select]
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        set_vert_group("all", ori_border_index)
        cut_success = True

        # 首先用圆环进行切割
        try:
            track_time("开始切割")
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_main
            obj_main.select_set(True)
            cut_obj = obj_circle
            # 该布尔插件会直接删掉切割平面，最好是使用复制去切，以防后续会用到
            duplicate_obj = cut_obj.copy()
            duplicate_obj.data = cut_obj.data.copy()
            duplicate_obj.animation_data_clear()
            bpy.context.collection.objects.link(duplicate_obj)
            duplicate_obj.select_set(True)
            if bpy.context.scene.leftWindowObj == '右耳':
                moveToRight(duplicate_obj)
            else:
                moveToLeft(duplicate_obj)
            # 使用布尔插件
            bpy.ops.object.booltool_auto_difference()

            # 获取下边界顶点
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='all')
            # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')

            bm = bmesh.from_edit_mesh(obj_main.data)
            outer_border_index = [v.index for v in bm.verts if v.select]

            bpy.ops.object.mode_set(mode='OBJECT')

            # 将下边界加入顶点组
            bottom_outer_border_vertex = obj_main.vertex_groups.get("CircleCutBorderVertex")
            if (bottom_outer_border_vertex == None):
                bottom_outer_border_vertex = obj_main.vertex_groups.new(name="CircleCutBorderVertex")
            for vert_index in outer_border_index:
                bottom_outer_border_vertex.add([vert_index], 1, 'ADD')
            delete_vert_group("all")

            delete_useless_part()

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
            bpy.ops.object.vertex_group_select()
            # 将周围的面变成三角面
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
            # bpy.ops.object.vertex_group_select()

            # 补面
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            bpy.ops.mesh.fill()   # todo: 这种填充方式没有网格，待优化
            bpy.ops.mesh.select_all(action='DESELECT')
            # 栅格填充方式
            # bpy.ops.mesh.subdivide(number_cuts=1)
            # bpy.ops.mesh.fill_grid(span=10)
            # bpy.ops.object.vertex_group_remove_from()
            # bpy.ops.mesh.select_mode(type='EDGE')
            # bpy.ops.mesh.region_to_loop()
            # bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
            # utils_re_color(operator_obj, (1, 0.319, 0.133))
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_circle
            obj_circle.select_set(True)
        except:
            cut_success = False
            print('切割失败')
            bpy.ops.object.mode_set(mode='OBJECT')

        # 切割成功时，平滑
        if cut_success:
            # 根据切割完成后的物体复制一份用于回退
            if bpy.data.objects.get(obj_name + 'circlecutpinghuaforreset') != None:
                bpy.data.objects.remove(bpy.data.objects[obj_name + 'circlecutpinghuaforreset'], do_unlink=True)
            duplicate_obj = obj_main.copy()
            duplicate_obj.data = obj_main.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = obj_main.name + "circlecutpinghuaforreset"
            bpy.context.collection.objects.link(duplicate_obj)
            if bpy.context.scene.leftWindowObj == '右耳':
                moveToRight(duplicate_obj)
            else:
                moveToLeft(duplicate_obj)
            duplicate_obj.hide_set(True)
            smooth_circlecut(obj_name, pianyi)
        reset_time_tracker()
        return

        ########## 之前版本的平滑 ##########

        # 圆环平面法向量和平面上一点
        plane_normal = obj_circle.matrix_world.to_3x3(
        ) @ obj_circle.data.polygons[0].normal
        plane_point = obj_circle.location.copy()
        # 舍入偏移参数
        if obj_name == '右耳':
            a = bpy.context.scene.qiegesheRuPianYiR
        elif obj_name == '左耳':
            a = bpy.context.scene.qiegesheRuPianYiL
        # 最大偏移值
        b = round(math.sqrt((now_radius)), 2)

        # print('b',b)
        # print('now_radius',now_radius)
        bpy.context.view_layer.update()

        # 获取圆环的坐标范围
        # cbm = bmesh.new()
        # cbm.from_mesh(obj_torus.data)
        # xmin = float('inf')
        # xmax = float('-inf')
        # for vert in cbm.verts:
        #     xmax = max(vert.co.x, xmax)
        #     xmin = min(vert.co.x, xmin)
        # xmax = obj_torus.location.x + xmax
        # xmin = obj_torus.location.x + xmin
        # print('xmin',xmin)
        # print('xmax',xmax)

        bm = bmesh.new()
        bm.from_mesh(obj_main.data)
        if len(bm.verts) == 0:
            return
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

        # print('平面上的点',len(vert_plane))

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
                    # 点到圆环中心的距离
                    dis = (link_vert.co - obj_torus.location).length
                    # 当前圆环半径
                    r = scale_ratio*old_radius
                    if link_vert not in visited_vert and distance_to_plane(plane_normal, plane_point, link_vert.co) <= b and dis <= sqrt(r*r+b*b) :
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


def smooth_circlecut(obj_name, pianyi):
    obj_main = bpy.data.objects[obj_name]
    obj_circle = bpy.data.objects[obj_name + 'Circle']
    # 进行平滑
    try:
        track_time("开始平滑")
        name = obj_name + 'circlecutpinghuaforreset'
        obj = bpy.data.objects[name]
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.name = obj.name + "copy"
        duplicate_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if obj_name == '右耳':
            moveToRight(duplicate_obj)
        else:
            moveToLeft(duplicate_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.hide_set(False)
        duplicate_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.region_to_loop()
        if pianyi > 0:
            global now_radius
            bpy.ops.circle.smooth(width=pianyi, center_border_group_name='CircleCutBorderVertex',
                                  max_smooth_width=3, circle_radius=now_radius)
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
        bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)
        duplicate_obj.name = obj_name
        bpy.ops.object.mode_set(mode='OBJECT')
        # utils_re_color(operator_obj, (1, 0.319, 0.133))

        # if bpy.data.objects.get(obj_name + 'circlecutpinghuaforresetcopy.001'):
        #     bpy.data.objects.remove(bpy.data.objects[obj_name + 'circlecutpinghuaforresetcopy.001'], do_unlink=True)

    except:
        print('平滑失败')
        if bpy.data.objects.get(obj_name + 'circlecutpinghuaforresetcopy'):
            bpy.data.objects.remove(bpy.data.objects[obj_name + 'circlecutpinghuaforresetcopy'], do_unlink=True)
        if bpy.data.objects.get(obj_name + 'circlecutpinghuaforresetcopyBridgeBorder'):
            bpy.data.objects.remove(bpy.data.objects[obj_name + 'circlecutpinghuaforresetcopyBridgeBorder'], do_unlink=True)
        bpy.context.view_layer.objects.active = bpy.data.objects[obj_name]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[obj_name].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_circle
        obj_circle.select_set(True)


def apply_stepcut(obj_name):
    # step_bool_cut()
    if obj_name == '右耳':
        pianyi = bpy.context.scene.qiegewaiBianYuanR  # 获取偏移值
    elif obj_name == '左耳':
        pianyi = bpy.context.scene.qiegewaiBianYuanL  # 获取偏移值
    obj = bpy.data.objects[obj_name]
    # 复制一份物体并应用布尔修改器用于平滑
    if bpy.data.objects.get(obj_name + 'stepcutpinghua') != None:
        bpy.data.objects.remove(bpy.data.objects[obj_name + 'stepcutpinghua'], do_unlink=True)
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = obj_name + "stepcutpinghua"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if obj_name == '右耳':
        moveToRight(duplicate_obj)
    elif obj_name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj.hide_select = False

    # 复制一份平面用于细分
    # plane_obj = bpy.data.objects[obj_name + 'StepCutplane']
    # subdivide_plane = plane_obj.copy()
    # subdivide_plane.data = plane_obj.data.copy()
    # subdivide_plane.name = obj_name + "StepCutsubplane"
    # subdivide_plane.animation_data_clear()
    # bpy.context.scene.collection.objects.link(subdivide_plane)
    # if obj_name == '右耳':
    #     moveToRight(subdivide_plane)
    # elif obj_name == '左耳':
    #     moveToLeft(subdivide_plane)
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.view_layer.objects.active = subdivide_plane
    # subdivide_plane.hide_set(False)
    # subdivide_plane.select_set(True)
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.subdivide(number_cuts=50)
    # bpy.ops.object.mode_set(mode='OBJECT')

    # 应用修改器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.select_set(True)
    # modifier = duplicate_obj.modifiers[-1]
    # modifier.object = subdivide_plane
    bpy.ops.object.modifier_apply(modifier="step cut", single_user=True)
    # bpy.data.objects.remove(bpy.data.objects[obj_name + 'StepCutsubplane'], do_unlink=True)

    # 选中需要操作的外圈循环边
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_set_active(group='before_cut')
    bpy.ops.object.vertex_group_deselect()
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.region_to_loop()
    if duplicate_obj.vertex_groups.get("StepCutBorderVertex") != None:
        delete_vert_group("StepCutBorderVertex")
    duplicate_obj.vertex_groups.new(name="StepCutBorderVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')
    # utils_re_color(duplicate_obj, (1, 0.319, 0.133))

    # bpy.ops.mesh.separate(type='SELECTED')
    # for obj in bpy.data.objects:
    #     if obj.select_get() and obj != duplicate_obj:
    #         border_obj = obj
    #         break
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # border_obj.select_set(True)
    # bpy.context.view_layer.objects.active = border_obj
    # border_obj.name = obj_name + "侧切平滑边缘"
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bm = bmesh.from_edit_mesh(border_obj.data)
    # edges = [e for e in bm.edges if e.select]
    # bpy.ops.mesh.select_all(action='DESELECT')
    # for e in edges:
    #     if e.is_boundary:
    #         e.select_set(True)
    # bpy.ops.object.mode_set(mode='OBJECT')
    # duplicate_obj.select_set(True)
    # border_obj.select_set(True)
    # bpy.context.view_layer.objects.active = duplicate_obj
    # bpy.ops.object.join()
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.remove_doubles()
    if bpy.data.objects.get(duplicate_obj.name + 'forreset') != None:
        bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'forreset'], do_unlink=True)
    reset_obj = duplicate_obj.copy()
    reset_obj.data = duplicate_obj.data.copy()
    reset_obj.animation_data_clear()
    reset_obj.name = duplicate_obj.name + "forreset"
    bpy.context.collection.objects.link(reset_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(reset_obj)
    else:
        moveToLeft(reset_obj)
    reset_obj.hide_set(True)

    smooth_stepcut(duplicate_obj.name, pianyi)


def smooth_stepcut(obj_name, pianyi):
    name = obj_name + 'forreset'
    obj = bpy.data.objects[name]
    try:
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.name = obj.name + "copy"
        duplicate_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if bpy.context.scene.leftWindowObj == '右耳':
            moveToRight(duplicate_obj)
        else:
            moveToLeft(duplicate_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.hide_set(False)
        duplicate_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='StepCutBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.region_to_loop()
        if pianyi > 0:
            bpy.ops.step.smooth(width=pianyi, center_border_group_name='StepCutBorderVertex')
        else:
            bpy.ops.mesh.select_mode(type='VERT')
        bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)
        duplicate_obj.name = obj_name
        bpy.ops.object.mode_set(mode='OBJECT')
        # utils_re_color(duplicate_obj, (1, 0.319, 0.133))

    except:
        if bpy.data.objects.get(obj_name + 'forresetcopy'):
            bpy.data.objects.remove(bpy.data.objects[obj_name + 'forresetcopy'], do_unlink=True)
        if bpy.data.objects.get(obj_name + 'forresetcopyBridgeBorder'):
            bpy.data.objects.remove(bpy.data.objects[obj_name + 'forresetcopyBridgeBorder'], do_unlink=True)
        bpy.context.view_layer.objects.active = bpy.data.objects[obj_name]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[obj_name].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        print('侧切边缘平滑失败')

    # 隐藏右耳，将平滑后的物体设为展示的物体
    smooth_obj = bpy.data.objects[obj_name]
    ori_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    if not ori_obj.hide_get():
        ori_obj.hide_set(True)
    if smooth_obj.hide_get():
        smooth_obj.hide_set(False)
    smooth_obj.hide_select = True


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


# 获取截面半径
def getRadius(op):
    global old_radius, scale_ratio, now_radius, on_obj, operator_obj, max_radius

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
    if operator_obj == '右耳':
        moveToRight(duplicate_obj)
    elif operator_obj == '左耳':
        moveToLeft(duplicate_obj)

    bpy.context.view_layer.objects.active = duplicate_obj
    # 添加修改器,获取交面

    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate_obj.modifiers.new(name="Boolean Intersect", type='BOOLEAN')
    duplicate_obj.modifiers[0].operation = 'INTERSECT'
    duplicate_obj.modifiers[0].object = obj_circle
    duplicate_obj.modifiers[0].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect', single_user=True)

    # 添加一个修饰器
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.view_layer.objects.active = duplicate_obj
    # duplicate_obj.select_set(True)
    # cut_obj = obj_circle
    # # 该布尔插件会直接删掉切割平面，最好是使用复制去切，以防后续会用到
    # duplicate_obj2 = cut_obj.copy()
    # duplicate_obj2.data = cut_obj.data.copy()
    # duplicate_obj2.animation_data_clear()
    # bpy.context.collection.objects.link(duplicate_obj2)
    # duplicate_obj2.select_set(True)
    # # 使用布尔插件
    # bpy.ops.object.booltool_auto_difference()

    rbm = bmesh.new()
    rbm.from_mesh(duplicate_obj.data)

    # 获取截面上的点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()
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
        max_radius = radius
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


# 新建与RGB颜色相同的材质
def newColor(id, r, g, b, is_transparency, transparency_degree):
    mat = newMaterial(id)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.inputs[0].default_value = (r, g, b, 1)
    shader.inputs[6].default_value = 0.46
    shader.inputs[7].default_value = 0
    shader.inputs[9].default_value = 0.472
    shader.inputs[14].default_value = 1
    shader.inputs[15].default_value = 1
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


# 初始化
def initCircle(obj_name):
    global old_radius, scale_ratio, now_radius, right_last_loc, right_last_radius, right_last_ratation, left_last_loc, left_last_radius, left_last_ratation
    global zmax, zmin, operator_obj

    obj_main = bpy.data.objects[obj_name]
    operator_obj = obj_name

    if obj_name == '右耳':
        last_loc = right_last_loc
        last_ratation = right_last_ratation
        last_radius = right_last_radius
    elif obj_name == '左耳':
        last_loc = left_last_loc
        last_ratation = left_last_ratation
        last_radius = left_last_radius

    copyModel(obj_name)
    getModelZ(obj_name)

    initZ = round(zmax * 0.95, 2)
    # 获取目标物体的编辑模式网格

    # obj_main.data.materials.clear()
    # newColor('yellow', 1.0, 0.319, 0.133, 0, 1)
    apply_material()
    newColor('yellow2', 1.0, 0.319, 0.133, 1, 0.3)
    obj_compare = bpy.data.objects[obj_name + 'huanqiecompare']
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
    else:  # 初始高度没有顶点
        initZ = (zmax + zmin) / 2  # 改变初始高度
        selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
            initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)

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
    # 正常初始化
    if last_loc == None:
        now_radius = round(min_distance, 2)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    # print('当前位置', last_loc)

    initX = center.x
    initY = center.y
    # if obj_name == '左耳':
    #     initY = -initY

    # 若存在原始物体，先删除
    torus = bpy.data.objects.get(obj_name + 'Torus')
    circle = bpy.data.objects.get(obj_name + 'Circle')
    if (torus):
        bpy.data.objects.remove(torus, do_unlink=True)
    if (circle):
        bpy.data.objects.remove(circle, do_unlink=True)

    # 正常初始化
    if last_loc == None:
        print('正常初始化')
        # 大圆环
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD', location=(
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
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=last_loc, rotation=(
                last_ratation[0], last_ratation[1], last_ratation[2]), scale=(
                1.0, 1.0, 1.0))
        # 初始化环体
        # if obj_name == '左耳':
        #     bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(
        #     initX, initY, initZ), rotation=(0.0, 0, 0),major_segments=80, minor_segments=80, major_radius=old_radius, minor_radius=0.4)
        # else:
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=last_loc, rotation=(
            last_ratation[0], last_ratation[1], last_ratation[2]),
            major_segments=80, minor_segments=80, major_radius=last_radius, minor_radius=0.4)
        old_radius = last_radius

    obj = bpy.context.active_object
    obj.name = obj_name + 'Torus'
    if obj_name == '右耳':
        moveToRight(obj)
    elif obj_name == '左耳':
        moveToLeft(obj)
    # 环体颜色
    newColor('red', 1, 0, 0, 0, 1)
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

    if last_loc == None:
        # 初始圆环位置较高，下移
        obj_circle.location.z -= round(zmax * 0.15, 2)
        obj.location.z -= round(zmax * 0.15, 2)
        getRadius('move')

    # 为模型添加布尔修改器
    # obj_main = bpy.data.objects[obj_name]
    # bool_modifier = obj_main.modifiers.new(
    #     name=obj_name+"Boolean Modifier", type='BOOLEAN')
    # # 设置布尔修饰符作用对象
    # bool_modifier.operation = 'DIFFERENCE'
    # bool_modifier.object = obj_circle
    # bool_modifier.solver = 'FAST'

    apply_circle_cut(obj_name)

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
    if name.startswith('右耳'):
        moveToRight(obj)
    elif name.startswith('左耳'):
        moveToLeft(obj)
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
    radius = 0.4  # 半径
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
    if name.startswith('右耳'):
        moveToRight(obj)
    elif name.startswith('左耳'):
        moveToLeft(obj)

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

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bm.edges.ensure_lookup_table()
    bm.edges[2].select = True

    # 更新网格数据
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.transform.edge_bevelweight(value=1, snap=False)
    bpy.ops.mesh.select_mode(type='VERT')

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.hide_set(True)

    # 添加倒角修改器
    bool_modifier = obj.modifiers.new(
        name="smooth", type='BEVEL')
    bool_modifier.segments = 6
    if name.startswith('右耳'):
        width = bpy.context.scene.qiegeneiBianYuanR
    elif name.startswith('左耳'):
        width = bpy.context.scene.qiegeneiBianYuanL
    bool_modifier.width = width
    bool_modifier.limit_method = 'WEIGHT'


def update_plane(obj_name):
    # 获取坐标
    loc = [bpy.data.objects[obj_name + 'StepCutSphere1'].location,
           bpy.data.objects[obj_name + 'StepCutSphere2'].location,
           bpy.data.objects[obj_name + 'StepCutSphere3'].location,
           bpy.data.objects[obj_name + 'StepCutSphere4'].location]

    # 更新位置
    obj = bpy.data.objects[obj_name + 'StepCutplane']
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


# 确定四个圆球的位置
def initsphereloc(obj_name):
    global zmax
    global r_old_loc_sphere1, r_old_loc_sphere2, r_old_loc_sphere3, r_old_loc_sphere4
    global l_old_loc_sphere1, l_old_loc_sphere2, l_old_loc_sphere3, l_old_loc_sphere4
    getModelZ(obj_name)
    initZ = round(zmax * 0.7, 2)
    bm = bmesh.new()
    obj = bpy.data.objects[obj_name]
    objdata = bpy.data.objects[obj_name].data
    bm.from_mesh(objdata)
    selected_verts = [v.co for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]

    # 找到具有最大或最小坐标的顶点
    # if obj_name == '右耳':
    old_loc_sphere1 = min(selected_verts, key=lambda v: v[1])
    # elif obj_name == '左耳':
    #     old_loc_sphere1 = max(selected_verts, key=lambda v: v[1])
    old_loc_sphere2 = min(selected_verts, key=lambda v: v[0])
    old_loc_sphere3 = max(selected_verts, key=lambda v: v[0])

    initx = (old_loc_sphere2[0] + old_loc_sphere3[0]) / 2
    selected_verts2 = [v.co for v in bm.verts if round(v.co.x, 2) < round(
        initx, 2) + 0.1 and round(v.co.x, 2) > round(initx, 2) - 0.1]
    old_loc_sphere4 = max(selected_verts2, key=lambda v: v[2])

    if obj_name == '右耳':
        r_old_loc_sphere1 = old_loc_sphere1
        r_old_loc_sphere2 = old_loc_sphere2
        r_old_loc_sphere3 = old_loc_sphere3
        r_old_loc_sphere4 = old_loc_sphere4
    elif obj_name == '左耳':
        l_old_loc_sphere1 = old_loc_sphere1
        l_old_loc_sphere2 = old_loc_sphere2
        l_old_loc_sphere3 = old_loc_sphere3
        l_old_loc_sphere4 = old_loc_sphere4


# 初始化侧切模块中用于切割的平面
def initPlane(obj_name):
    global r_old_loc_sphere1, r_old_loc_sphere2, r_old_loc_sphere3, r_old_loc_sphere4
    global l_old_loc_sphere1, l_old_loc_sphere2, l_old_loc_sphere3, l_old_loc_sphere4
    global operator_obj
    global loc_saved_right, loc_saved_left

    operator_obj = obj_name

    if not loc_saved_right and obj_name == '右耳':
        # 初始化4个点位置
        initsphereloc(obj_name)
    elif not loc_saved_left and obj_name == '左耳':
        initsphereloc(obj_name)

    if obj_name == '右耳':
        old_loc_sphere1 = r_old_loc_sphere1
        old_loc_sphere2 = r_old_loc_sphere2
        old_loc_sphere3 = r_old_loc_sphere3
        old_loc_sphere4 = r_old_loc_sphere4
    elif obj_name == '左耳':
        old_loc_sphere1 = l_old_loc_sphere1
        old_loc_sphere2 = l_old_loc_sphere2
        old_loc_sphere3 = l_old_loc_sphere3
        old_loc_sphere4 = l_old_loc_sphere4

    # 新建圆球
    new_sphere(obj_name + 'StepCutSphere1', old_loc_sphere1)
    new_sphere(obj_name + 'StepCutSphere2', old_loc_sphere2)
    new_sphere(obj_name + 'StepCutSphere3', old_loc_sphere3)
    new_sphere(obj_name + 'StepCutSphere4', old_loc_sphere4)
    saveStep(obj_name)
    new_plane(obj_name + 'StepCutplane')

    newColor('red', 1, 0, 0, 0, 1)
    red_material = bpy.data.materials['red']
    bpy.data.objects[obj_name + 'StepCutSphere1'].data.materials.append(red_material)
    bpy.data.objects[obj_name + 'StepCutSphere2'].data.materials.append(red_material)
    bpy.data.objects[obj_name + 'StepCutSphere3'].data.materials.append(red_material)
    bpy.data.objects[obj_name + 'StepCutSphere4'].data.materials.append(red_material)

    # 开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'VERTEX'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    obj = bpy.data.objects[obj_name]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    apply_material()

    # 设置顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    all_vert = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("before_cut", all_vert)

    if not bpy.data.objects.get(obj_name + 'ceqieCompare'):
        obj_copy = obj.copy()
        obj_copy.name = obj.name + 'ceqieCompare'
        obj_copy.data = obj.data.copy()
        obj_copy.animation_data_clear()
        scene = bpy.context.scene
        scene.collection.objects.link(obj_copy)
        if obj_name == '右耳':
            moveToRight(obj)
            moveToRight(obj_copy)
        elif obj_name == '左耳':
            moveToLeft(obj)
            moveToLeft(obj_copy)
        obj.hide_select = True
        obj_copy.hide_select = True

    # newColor('yellow', 1.0, 0.319, 0.133, 0, 1)
    newColor('yellow2', 1.0, 0.319, 0.133, 1, 0.3)

    bpy.data.objects[obj_name + 'ceqieCompare'].data.materials.clear()
    bpy.data.objects[obj_name + 'ceqieCompare'].data.materials.append(
        bpy.data.materials['yellow2'])

    # todo: 优化切割方式
    bool_modifier = obj.modifiers.new(
        name="step cut", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    plane = bpy.data.objects[obj_name + 'StepCutplane']
    bool_modifier.object = plane

    update_plane(operator_obj)
    apply_stepcut(operator_obj)

    # override = getOverride()
    # with bpy.context.temp_override(**override):
    bpy.ops.object.stepcut('INVOKE_DEFAULT')


def step_bool_cut():
    global operator_obj
    reset_obj = bpy.data.objects[operator_obj + 'ceqieCompare']
    duplicate_obj = reset_obj.copy()
    duplicate_obj.data = reset_obj.data.copy()
    duplicate_obj.animation_data_clear()
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.data.materials.clear()
    if operator_obj == '右耳':
        moveToRight(duplicate_obj)
        duplicate_obj.data.materials.append(bpy.data.materials['YellowR'])
    elif operator_obj == '左耳':
        moveToLeft(duplicate_obj)
        duplicate_obj.data.materials.append(bpy.data.materials['YellowL'])

    cut_obj = bpy.data.objects[operator_obj + 'StepCutplane']
    duplicate_plane_obj = cut_obj.copy()
    duplicate_plane_obj.data = cut_obj.data.copy()
    duplicate_plane_obj.animation_data_clear()
    bpy.context.collection.objects.link(duplicate_plane_obj)
    if operator_obj == '右耳':
        moveToRight(duplicate_plane_obj)
    elif operator_obj == '左耳':
        moveToLeft(duplicate_plane_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_plane_obj
    duplicate_plane_obj.select_set(True)
    # bpy.ops.object.modifier_apply(modifier="smooth", single_user=True)
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.normals_make_consistent(inside=False)
    # bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.hide_select = False
    duplicate_obj.select_set(True)
    duplicate_plane_obj.select_set(True)
    bpy.ops.object.booltool_auto_difference()
    bpy.data.objects.remove(bpy.data.objects[operator_obj], do_unlink=True)
    duplicate_obj.name = operator_obj
    duplicate_obj.hide_select = True


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
    global old_radius, right_last_loc, right_last_radius, right_last_ratation, left_last_loc, left_last_radius, left_last_ratation, operator_obj
    obj_torus = bpy.data.objects.get(operator_obj + 'Torus')
    if(obj_torus != None):
        last_loc = obj_torus.location.copy()
        last_radius = round(old_radius * obj_torus.scale[0], 2)
        last_ratation = obj_torus.rotation_euler.copy()
        if operator_obj == '右耳':
            right_last_loc = last_loc
            right_last_radius = last_radius
            right_last_ratation = last_ratation
        else:
            left_last_loc = last_loc
            left_last_radius = last_radius
            left_last_ratation = last_ratation
        # print('当前位置',last_loc)
        # print('当前半径',last_radius)
        # print('当前角度',last_ratation)


# 获取距离位置最近的顶点
def getClosestVert(co):
    main_obj = bpy.context.scene.leftWindowObj
    right_obj = bpy.data.objects[main_obj]
    _, _, _, fidx = right_obj.closest_point_on_mesh(co)
    bm = bmesh.new()
    bm.from_mesh(right_obj.data)
    bm.faces.ensure_lookup_table()
    min = float('inf')
    for v in bm.faces[fidx].verts:
        vec = v.co - co
        between = vec.dot(vec)
        if (between <= min):
            min = between
            index = v.index
    bm.verts.ensure_lookup_table()
    print('co', bm.verts[index].co)
    return index


def saveStep(obj_name):
    global r_old_loc_sphere1, r_old_loc_sphere2, r_old_loc_sphere3, r_old_loc_sphere4
    global l_old_loc_sphere1, l_old_loc_sphere2, l_old_loc_sphere3, l_old_loc_sphere4
    global loc_spheres_index

    old_loc_sphere1 = []
    old_loc_sphere1.append(round(bpy.data.objects[obj_name + 'StepCutSphere1'].location.x, 3))
    old_loc_sphere1.append(round(bpy.data.objects[obj_name + 'StepCutSphere1'].location.y, 3))
    old_loc_sphere1.append(round(bpy.data.objects[obj_name + 'StepCutSphere1'].location.z, 3))
    old_loc_sphere2 = []
    old_loc_sphere2.append(round(bpy.data.objects[obj_name + 'StepCutSphere2'].location.x, 3))
    old_loc_sphere2.append(round(bpy.data.objects[obj_name + 'StepCutSphere2'].location.y, 3))
    old_loc_sphere2.append(round(bpy.data.objects[obj_name + 'StepCutSphere2'].location.z, 3))
    old_loc_sphere3 = []
    old_loc_sphere3.append(round(bpy.data.objects[obj_name + 'StepCutSphere3'].location.x, 3))
    old_loc_sphere3.append(round(bpy.data.objects[obj_name + 'StepCutSphere3'].location.y, 3))
    old_loc_sphere3.append(round(bpy.data.objects[obj_name + 'StepCutSphere3'].location.z, 3))
    old_loc_sphere4 = []
    old_loc_sphere4.append(round(bpy.data.objects[obj_name + 'StepCutSphere4'].location.x, 3))
    old_loc_sphere4.append(round(bpy.data.objects[obj_name + 'StepCutSphere4'].location.y, 3))
    old_loc_sphere4.append(round(bpy.data.objects[obj_name + 'StepCutSphere4'].location.z, 3))

    # print('圆球的坐标为')
    # print(old_loc_sphere1)
    # print(old_loc_sphere2)
    # print(old_loc_sphere3)
    # print(old_loc_sphere4)

    if obj_name == '右耳':
        r_old_loc_sphere1 = old_loc_sphere1
        r_old_loc_sphere2 = old_loc_sphere2
        r_old_loc_sphere3 = old_loc_sphere3
        r_old_loc_sphere4 = old_loc_sphere4
    elif obj_name == '左耳':
        l_old_loc_sphere1 = old_loc_sphere1
        l_old_loc_sphere2 = old_loc_sphere2
        l_old_loc_sphere3 = old_loc_sphere3
        l_old_loc_sphere4 = old_loc_sphere4

    main_obj = bpy.data.objects[obj_name]
    loc_array = []
    loc_spheres_index = []

    loc_array.append(old_loc_sphere1)
    loc_array.append(old_loc_sphere2)
    loc_array.append(old_loc_sphere3)
    loc_array.append(old_loc_sphere4)
    bm = bmesh.new()
    bm.from_mesh(main_obj.data)
    bm.verts.ensure_lookup_table()

    # for loc in loc_array:
    #     for v in bm.verts:
    #         if [round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3)] == loc:
    #             print('co1',v.co)
    #             loc_spheres_index.append(v.index)
    # 4个球的最小z坐标
    min_z = float('inf')
    for loc in loc_array:
        if loc[2] < min_z:
            min_z = loc[2]
    # print('最低点z',min_z)
    selected_verts = [v for v in bm.verts if v.co.z >= min_z - 2]
    # 求距离最近的点
    for loc in loc_array:
        min_dist = float('inf')
        closest_vert_index = None
        loc = Vector(loc)
        for vert in selected_verts:
            dist = (vert.co - loc).length
            if dist < min_dist:
                min_dist = dist
                closest_vert_index = vert.index
        bm.verts.ensure_lookup_table()
        # print('co',bm.verts[closest_vert_index].co)
        loc_spheres_index.append(closest_vert_index)

    bm.to_mesh(main_obj.data)
    bm.free()
    # print('index num',len(loc_spheres_index))


# 退出操作
def quitCut(obj_name):
    global finish, finishL, operator_obj

    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        finish_cur = finish
    elif name == '左耳':
        finish_cur = finishL

    # 切割未完成
    if finish_cur == False:
        # print('quitcut', obj_name)
        del_objs = [obj_name + 'Circle', obj_name + 'Torus', obj_name, obj_name + 'circlecutpinghuaforreset']

        for obj in del_objs:
            if (bpy.data.objects.get(obj)):
                obj1 = bpy.data.objects[obj]
                bpy.data.objects.remove(obj1, do_unlink=True)
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=False)
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects[obj_name + "huanqiecompare"]
        # obj.hide_set(False)
        bpy.context.view_layer.objects.active = obj
        # delete_vert_group("CircleCutBorderVertex")
        obj.name = obj_name


def quitStepCut(obj_name):
    global finish, finishL
    global loc_saved_left, loc_saved_right

    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        finish_cur = finish
    elif name == '左耳':
        finish_cur = finishL

    # 切割未完成
    if finish_cur == False:
        saveStep(obj_name)
        if obj_name == '右耳':
            loc_saved_right = True
        elif obj_name == '左耳':
            loc_saved_left = True

        # bpy.ops.object.modifier_remove(modifier='step cut', report=False)
        del_objs = [obj_name, obj_name + 'StepCutSphere1', obj_name + 'StepCutSphere2', obj_name + 'StepCutSphere3',
                    obj_name + 'StepCutSphere4', obj_name + 'StepCutplane', obj_name + 'stepcutpinghua',
                    obj_name + 'stepcutpinghuaforreset']
        for obj in del_objs:
            if (bpy.data.objects.get(obj)):
                obj1 = bpy.data.objects[obj]
                bpy.data.objects.remove(obj1, do_unlink=True)
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=False)

        bpy.ops.object.select_all(action='DESELECT')
        main_obj = bpy.data.objects.get(obj_name + "ceqieCompare")
        if main_obj:
            main_obj.hide_select = False
            main_obj.hide_set(False)
            bpy.context.view_layer.objects.active = main_obj
            main_obj.select_set(state=True)
            # 删除创建的顶点组
            step_cut_vertex_group = main_obj.vertex_groups.get("before_cut")
            if (step_cut_vertex_group != None):
                main_obj.vertex_groups.remove(step_cut_vertex_group)
            # step_cut_smooth_vertex_group = main_obj.vertex_groups.get("StepCutBorderVertex")
            # if (step_cut_smooth_vertex_group != None):
            #     main_obj.vertex_groups.remove(step_cut_smooth_vertex_group)

        bpy.context.view_layer.objects.active = main_obj
        main_obj.name = obj_name


class Circle_Cut(bpy.types.Operator):
    bl_idname = "object.circlecut"
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
    __dx = 0
    __dy = 0
    # __area = None

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

        op_cls = Circle_Cut
        op_cls.__initial_rotation_x = None
        op_cls.__initial_rotation_y = None
        op_cls.__initial_rotation_z = None
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None

        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 55
        global circle_cut_modal_start
        if not circle_cut_modal_start:
            circle_cut_modal_start = True
            context.window_manager.modal_handler_add(self)
            print('invokeCir')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global operator_obj, mouse_loc
        global circle_cut_modal_start
        op_cls = Circle_Cut

        if get_mirror_context():
            print('退出环切')
            circle_cut_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        # 未切割时起效
        if bpy.context.scene.var == 55:
            operator_obj = context.scene.leftWindowObj

            # mouse_x = event.mouse_x
            # mouse_y = event.mouse_y
            # override1 = getOverride()
            # area = override1['area']
            # override2 = getOverride2()
            # area2 = override2['area']
            # op_cls.__area = area
            # workspace = bpy.context.window.workspace.name

            # 双窗口模式下
            # if workspace == '布局.001':
            #     # 根据鼠标位置判断当前操作窗口
            #     if (event.mouse_x > area.width and event.mouse_y > area2.y):
            #         # print('右窗口')
            #         op_cls.__area = area2
            #         operator_obj = context.scene.rightWindowObj
            #     else:
            #         # print('左窗口')
            #         op_cls.__area = area
            #         operator_obj = context.scene.leftWindowObj
            # elif workspace == '布局':
            #     operator_obj = context.scene.leftWindowObj
            #     op_cls.__area = area

            obj_torus = bpy.data.objects.get(operator_obj + 'Torus')
            active_obj = bpy.data.objects.get(operator_obj + 'Circle')

            if obj_torus == None or active_obj == None:
                return {'PASS_THROUGH'}

            # 鼠标是否在圆环上
            if is_mouse_on_object(context, event):
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

                        # print('鼠标坐标',mouse_loc)
                        op_cls.__dx = round(mouse_loc.x, 2)
                        op_cls.__dy = round(mouse_loc.y, 2)
                        # print('dx',op_cls.__dx)
                        # print('dy',op_cls.__dy)

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
                        apply_circle_cut(operator_obj)
                        saveCir()
                        record_state()
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
                        apply_circle_cut(operator_obj)
                        saveCir()
                        record_state()
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
                            symx = -1
                        else:
                            symx = 1

                        if (op_cls.__dx > 0):
                            symy = -1
                        else:
                            symy = 1

                        # print('symx',symx)
                        # print('symy',symy)

                        # x,y轴旋转比例
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                    4)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                    4)
                        # print('px',px)
                        # print('py',py)

                        # 旋转角度
                        rotate_angle_x = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                        rotate_angle_y = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                        rotate_angle_z = round((event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)
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
                        # print('距离',dis)
                        obj_circle.location -= normal * dis * 0.05
                        obj_torus.location -= normal * dis * 0.05
                        getRadius('move')
                        return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}

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
                    apply_circle_cut(operator_obj)
                    saveCir()
                    record_state()
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
                            symx = -1
                        else:
                            symx = 1

                        if (op_cls.__dx > 0):
                            symy = -1
                        else:
                            symy = 1

                        # print('symx',symx)
                        # print('symy',symy)

                        #  x,y轴旋转比例
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                    4)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                    4)
                        # print('px',px)
                        # print('py',py)

                        # 旋转角度
                        rotate_angle_x = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                        rotate_angle_y = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                        rotate_angle_z = round((event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)
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
                        # dis = 0.5
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal
                        dis = event.mouse_region_y - op_cls.__initial_mouse_y
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        # print('距离',dis)
                        obj_circle.location -= normal * dis * 0.05
                        obj_torus.location -= normal * dis * 0.05
                        getRadius('move')
                        return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}

        else:
            print('退出环切')
            circle_cut_modal_start = False
            return {'FINISHED'}


class Step_Cut(bpy.types.Operator):
    bl_idname = "object.stepcut"
    bl_label = "阶梯切割"

    __left_mouse_down = False
    __timer = None
    __smooth = True
    __mouse_x = 0  # 记录鼠标按下的位置
    __mouse_y = 0
    __mouse_x_y_flag = False
    __start_update = False
    # __area = None

    def invoke(self, context, event):
        if not Step_Cut.__timer:
            Step_Cut.__timer = context.window_manager.event_timer_add(0.5, window=context.window)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        bpy.context.scene.var = 56
        global step_cut_modal_start
        if not step_cut_modal_start:
            step_cut_modal_start = True
            context.window_manager.modal_handler_add(self)
            print('invokeStep')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global operator_obj
        global step_cut_modal_start
        op_cls = Step_Cut

        if get_mirror_context():
            if Step_Cut.__timer:
                context.window_manager.event_timer_remove(Step_Cut.__timer)
                Step_Cut.__timer = None
                print('timer remove')
            print("退出侧切")
            step_cut_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        # 未切割时起效
        if bpy.context.scene.var == 56:
            operator_obj = context.scene.leftWindowObj

            # mouse_x = event.mouse_x
            # mouse_y = event.mouse_y
            # override1 = getOverride()
            # area = override1['area']
            # override2 = getOverride2()
            # area2 = override2['area']
            # op_cls.__area = area
            # workspace = bpy.context.window.workspace.name

            # 双窗口模式下
            # if workspace == '布局.001':
            #     # 根据鼠标位置判断当前操作窗口
            #     if (event.mouse_x > area.width and event.mouse_y > area2.y):
            #         # print('右窗口')
            #         op_cls.__area = area2
            #         operator_obj = context.scene.rightWindowObj
            #     else:
            #         # print('左窗口')
            #         op_cls.__area = area
            #         operator_obj = context.scene.leftWindowObj
            # elif workspace == '布局':
            #     operator_obj = context.scene.leftWindowObj

            if bpy.data.objects.get(operator_obj + 'StepCutSphere1'):
                if event.type == 'LEFTMOUSE':  # 监听左键
                    if event.value == 'PRESS':  # 按下
                        op_cls.__left_mouse_down = True
                    return {'PASS_THROUGH'}

                elif event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    return {'PASS_THROUGH'}

                # 鼠标在圆球上
                if is_mouse_on_which_object(operator_obj, context, event) != 5:
                    if is_changed_stepcut(operator_obj, context, event):
                        bpy.ops.wm.tool_set_by_id(name="builtin.select")
                        if bpy.data.objects[operator_obj].hide_get():
                            bpy.data.objects[operator_obj].hide_set(False)
                            bpy.data.objects[operator_obj + 'stepcutpinghua'].hide_set(True)

                    if op_cls.__left_mouse_down:
                        if not op_cls.__mouse_x_y_flag:
                            op_cls.__mouse_x = event.mouse_x
                            op_cls.__mouse_y = event.mouse_y
                            op_cls.__mouse_x_y_flag = True

                    dis = int(math.sqrt(math.fabs(op_cls.__mouse_x - event.mouse_x) ** 2 + math.fabs(
                        op_cls.__mouse_y - event.mouse_y) ** 2))

                    # 当鼠标左键按下并且使用调整移动一段距离之后,再进行实时切割的响应
                    if not op_cls.__start_update and op_cls.__left_mouse_down and dis > 4:
                        op_cls.__start_update = True

                    if event.type == 'TIMER' and op_cls.__left_mouse_down and op_cls.__start_update and dis > 2:
                        op_cls.__smooth = False
                        update_plane(operator_obj)
                        # step_bool_cut()
                        # 每次移动保存各个点坐标
                        saveStep(operator_obj)

                else:
                    if is_changed_stepcut(operator_obj, context, event) and not op_cls.__left_mouse_down:
                        # 鼠标不在圆球上时，将右耳设置为active
                        active_obj = bpy.data.objects[operator_obj]
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = active_obj
                        active_obj.select_set(True)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                        if not op_cls.__smooth:
                            op_cls.__smooth = True
                            update_plane(operator_obj)
                            apply_stepcut(operator_obj)
                            if not bpy.data.objects[operator_obj].hide_get():
                                bpy.data.objects[operator_obj].hide_set(True)
                                bpy.data.objects[operator_obj + 'stepcutpinghua'].hide_set(False)

                return {'PASS_THROUGH'}

            return {'PASS_THROUGH'}

        else:
            if Step_Cut.__timer:
                context.window_manager.event_timer_remove(Step_Cut.__timer)
                Step_Cut.__timer = None
                print('timer remove')
            print("退出侧切")
            step_cut_modal_start = False
            return {'FINISHED'}


class Finish_Cut(bpy.types.Operator):
    bl_idname = "object.finishcut"
    bl_label = "完成切割"

    def invoke(self, context, event):
        # 完成切割
        bpy.context.scene.var = 57
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if not bpy.context.scene.pressfinish:
            unregister_tools()
            bpy.context.scene.pressfinish = True
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        global finish, finishL, operator_obj
        qieGeTypeEnum = None
        if bpy.context.scene.leftWindowObj == "右耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumR
            finish = True
        elif bpy.context.scene.leftWindowObj == "左耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumL
            finishL = True

        if qieGeTypeEnum == 'OP1':
            # 保存圆环信息
            saveCir()
            del_objs = [operator_obj + 'Circle', operator_obj + 'Torus', operator_obj + 'huanqiecompare',
                        operator_obj + 'circlecutpinghuaforreset']

            for obj in del_objs:
                if bpy.data.objects.get(obj):
                    obj1 = bpy.data.objects[obj]
                    bpy.data.objects.remove(obj1, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
            obj = bpy.data.objects[operator_obj]
            bpy.context.view_layer.objects.active = obj
            utils_re_color(operator_obj, (1, 0.319, 0.133))
            apply_material()
            # delete_vert_group("CircleCutBorderVertex")

        if qieGeTypeEnum == 'OP2':
            saveStep(operator_obj)
            global loc_saved_left, loc_saved_right
            if operator_obj == '右耳':
                loc_saved_right = True
            elif operator_obj == '左耳':
                loc_saved_left = True
            # for i in bpy.context.visible_objects:
            #     if i.name == operator_obj:
            #         i.hide_select = False
            #         bpy.context.view_layer.objects.active = i
            #         bpy.ops.object.modifier_apply(modifier="step cut",single_user=True)
            # for i in bpy.context.visible_objects:
            #     if i.name == operator_obj+"StepCutplane":
            #         i.hide_set(False)
            #         bpy.context.view_layer.objects.active = i
            #         bpy.ops.object.modifier_apply(modifier="smooth",single_user=True)
            del_objs = [operator_obj, operator_obj + 'StepCutSphere1', operator_obj + 'StepCutSphere2',
                        operator_obj + 'StepCutSphere3', operator_obj + 'StepCutSphere4', operator_obj + 'StepCutplane',
                        operator_obj + 'ceqieCompare', operator_obj + 'stepcutpinghuaforreset']
            for obj in del_objs:
                if bpy.data.objects.get(obj):
                    obj1 = bpy.data.objects[obj]
                    bpy.data.objects.remove(obj1, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
            replace_name = operator_obj + 'stepcutpinghua'
            replace_obj = bpy.data.objects[replace_name]
            replace_obj.name = operator_obj

        name = operator_obj
        obj = bpy.data.objects[name]
        obj.hide_select = False
        # 删除创建的顶点组
        step_cut_vertex_group = obj.vertex_groups.get("before_cut")
        if (step_cut_vertex_group != None):
            obj.vertex_groups.remove(step_cut_vertex_group)
        # step_cut_smooth_vertex_group = obj.vertex_groups.get("StepCutBorderVertex")
        # if (step_cut_smooth_vertex_group != None):
        #     obj.vertex_groups.remove(step_cut_smooth_vertex_group)
        bpy.context.view_layer.objects.active = obj
        utils_re_color(operator_obj, (1, 0.319, 0.133))
        apply_material()


class Reset_Cut(bpy.types.Operator):
    bl_idname = "object.resetcut"
    bl_label = "重置切割"

    def invoke(self, context, event):
        global finish, finishL
        global loc_saved_right, loc_saved_left
        print('qiegereset invoke')

        name = bpy.context.scene.leftWindowObj
        qieGeTypeEnum = None
        if name == "右耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumR
        elif name == "左耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumL
        if qieGeTypeEnum == 'OP1':
            if name == '右耳':
                finish_cur = finish
            elif name == '左耳':
                finish_cur = finishL
        elif qieGeTypeEnum == 'OP2':
            if name == '右耳':
                finish_cur = loc_saved_right
            elif name == '左耳':
                finish_cur = loc_saved_left

        if finish_cur == False:
            print('unfinish')
            bpy.context.scene.var = 58
            self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        global operator_obj, right_last_loc, left_last_loc
        qieGeTypeEnum = None
        if bpy.context.scene.leftWindowObj == "右耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumR
        elif bpy.context.scene.leftWindowObj == "左耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumL

        if qieGeTypeEnum == 'OP1':
            del_objs = [operator_obj + 'Circle', operator_obj + 'Torus', operator_obj]
            for obj in del_objs:
                if (bpy.data.objects.get(obj)):
                    obj1 = bpy.data.objects[obj]
                    bpy.data.objects.remove(obj1, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
            bpy.ops.object.select_all(action='DESELECT')
            obj = bpy.data.objects[operator_obj + "huanqiecompare"]
            obj.hide_set(False)
            bpy.context.view_layer.objects.active = obj
            obj.name = operator_obj
            obj.data.materials.clear()
            # 删除保存的圆环位置信息
            last_loc = None
            if operator_obj == '右耳':
                right_last_loc = last_loc
            else:
                left_last_loc = last_loc
            # 重新初始化
            initCircle(operator_obj)

        if qieGeTypeEnum == 'OP2':
            name = bpy.context.scene.leftWindowObj
            # 重置前，将主物体设置为可选
            main_obj = bpy.data.objects.get(name)
            if main_obj:
                main_obj.hide_set(False)
                bpy.context.view_layer.objects.active = main_obj
            # 回到原来的位置
            global r_old_loc_sphere1, r_old_loc_sphere2, r_old_loc_sphere3, r_old_loc_sphere4
            global l_old_loc_sphere1, l_old_loc_sphere2, l_old_loc_sphere3, l_old_loc_sphere4
            initsphereloc(operator_obj)
            global loc_saved_right, loc_saved_left
            if operator_obj == '右耳':
                loc_saved_right = False
                old_loc_sphere1 = r_old_loc_sphere1
                old_loc_sphere2 = r_old_loc_sphere2
                old_loc_sphere3 = r_old_loc_sphere3
                old_loc_sphere4 = r_old_loc_sphere4
            elif operator_obj == '左耳':
                loc_saved_left = False
                old_loc_sphere1 = l_old_loc_sphere1
                old_loc_sphere2 = l_old_loc_sphere2
                old_loc_sphere3 = l_old_loc_sphere3
                old_loc_sphere4 = l_old_loc_sphere4
            # 回到原来的位置
            bpy.data.objects[operator_obj + 'StepCutSphere1'].location = old_loc_sphere1
            bpy.data.objects[operator_obj + 'StepCutSphere2'].location = old_loc_sphere2
            bpy.data.objects[operator_obj + 'StepCutSphere3'].location = old_loc_sphere3
            bpy.data.objects[operator_obj + 'StepCutSphere4'].location = old_loc_sphere4
            update_plane(operator_obj)
            apply_stepcut(operator_obj)
            bpy.ops.object.stepcut('INVOKE_DEFAULT')


class Mirror_Cut(bpy.types.Operator):
    bl_idname = "object.mirrorcut"
    bl_label = "切割镜像"

    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        global old_radius, operator_obj
        global finish, finishL, loc_saved_right, loc_saved_left
        global left_last_loc, right_last_loc, left_last_ratation, right_last_ratation
        global r_old_loc_sphere1, r_old_loc_sphere2, r_old_loc_sphere3, r_old_loc_sphere4
        global l_old_loc_sphere1, l_old_loc_sphere2, l_old_loc_sphere3, l_old_loc_sphere4

        workspace = context.window.workspace.name
        left_obj = bpy.data.objects.get(context.scene.leftWindowObj)
        right_obj = bpy.data.objects.get(context.scene.rightWindowObj)

        # 只操作一个耳朵时，不执行镜像
        if left_obj == None or right_obj == None:
            return {'FINISHED'}

        # 目标物体
        tar_obj = context.scene.leftWindowObj
        ori_obj = context.scene.rightWindowObj
        print('镜像目标', tar_obj)
        print('镜像来源', ori_obj)
        operator_obj = tar_obj

        qieGeTypeEnum = None
        if bpy.context.scene.leftWindowObj == "右耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumR
        elif bpy.context.scene.leftWindowObj == "左耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumL

        # 只有在双窗口下执行镜像
        # if workspace == '布局.001':
        # 环切镜像
        if qieGeTypeEnum == 'OP1':
            if tar_obj == '右耳':
                last_loc = left_last_loc
                last_ratation = left_last_ratation
                is_finish = finish
            elif tar_obj == '左耳':
                last_loc = right_last_loc
                last_ratation = right_last_ratation
                is_finish = finishL
            if last_loc != None and not is_finish:
                # print('开始镜像')
                # ori_torus = bpy.data.objects[ori_obj + 'Torus']
                tar_torus = bpy.data.objects[tar_obj + 'Torus']
                tar_circle = bpy.data.objects[tar_obj + 'Circle']
                # ori_radius = round(old_radius * ori_torus.scale[0], 2)
                # obj_main = bpy.data.objects[tar_obj]
                # loc = ori_torus.location.copy()
                # rot = ori_torus.rotation_euler.copy()
                tar_torus.location = Vector((last_loc[0], -last_loc[1], last_loc[2]))
                tar_torus.rotation_euler = mathutils.Euler((-last_ratation[0], last_ratation[1], -last_ratation[2]))
                tar_circle.location = Vector((last_loc[0], -last_loc[1], last_loc[2]))
                tar_circle.rotation_euler = mathutils.Euler((-last_ratation[0], last_ratation[1], -last_ratation[2]))

                getRadius("rotate")
                saveCir()
                apply_circle_cut(operator_obj)
                # 参数对应
                if bpy.context.scene.leftWindowObj == '右耳':
                    bpy.context.scene.qiegesheRuPianYiR =  bpy.context.scene.qiegesheRuPianYiL
                elif bpy.context.scene.leftWindowObj == '左耳':
                    bpy.context.scene.qiegesheRuPianYiL = bpy.context.scene.qiegesheRuPianYiR

        # 侧切镜像
        elif qieGeTypeEnum == 'OP2':
            if tar_obj == '右耳':
                loc = l_old_loc_sphere1
                loc_list = [l_old_loc_sphere1, l_old_loc_sphere2, l_old_loc_sphere3, l_old_loc_sphere4]
                is_loc_saved = loc_saved_right
            elif tar_obj == '左耳':
                loc = r_old_loc_sphere1
                loc_list = [r_old_loc_sphere1, r_old_loc_sphere2, r_old_loc_sphere3, r_old_loc_sphere4]
                is_loc_saved = loc_saved_left
            if loc and not is_loc_saved:
                left_bm = bmesh.new()
                left_me = bpy.data.objects[tar_obj].data
                left_bm.from_mesh(left_me)
                for i, loc in enumerate(loc_list):
                    x = loc[0]
                    y = -loc[1]
                    z = loc[2]

                    closest_location = None
                    min_distance = float('inf')
                    target_point = mathutils.Vector((x, y, z))
                    for vert in left_bm.verts:
                        # 将顶点坐标转换到世界坐标系
                        vertex_world = bpy.data.objects[tar_obj].matrix_world @ vert.co
                        distance = (vertex_world - target_point).length
                        if distance < min_distance:
                            min_distance = distance
                            closest_location = vertex_world
                    bpy.data.objects[tar_obj + 'StepCutSphere' + str(i+1)].location = closest_location

                # 投射的办法
                # 镜像投射点
                # cast_vertex_index = []
                # 右边是镜像来源
                # obj_right = bpy.data.objects[ori_obj]
                # 左边是镜像目标
                # obj_left = bpy.data.objects[tar_obj]
                # # 获取投射后的顶点index
                # cast_vertex_index = get_cast_index(tar_obj, loc_spheres_index)
                # left_bm = bmesh.new()
                # left_me = obj_left.data
                # left_bm.from_mesh(left_me)
                # left_bm.verts.ensure_lookup_table()
                # # 再依次移动位置
                # bpy.data.objects[tar_obj + 'StepCutSphere1'].location = left_bm.verts[cast_vertex_index[3]].co
                # bpy.data.objects[tar_obj + 'StepCutSphere2'].location = left_bm.verts[cast_vertex_index[1]].co
                # bpy.data.objects[tar_obj + 'StepCutSphere3'].location = left_bm.verts[cast_vertex_index[2]].co
                # bpy.data.objects[tar_obj + 'StepCutSphere4'].location = left_bm.verts[cast_vertex_index[0]].co
                # left_bm.to_mesh(left_me)
                # left_bm.free()

                # 更新平面
                update_plane(tar_obj)
                # 参数对应
                if bpy.context.scene.leftWindowObj == '右耳':
                    bpy.context.scene.qiegewaiBianYuanR = bpy.context.scene.qiegewaiBianYuanL
                    bpy.context.scene.qiegeneiBianYuanR = bpy.context.scene.qiegeneiBianYuanL
                elif bpy.context.scene.leftWindowObj == '左耳':
                    bpy.context.scene.qiegewaiBianYuanL = bpy.context.scene.qiegewaiBianYuanR
                    bpy.context.scene.qiegeneiBianYuanL = bpy.context.scene.qiegeneiBianYuanR
                # apply_stepcut(tar_obj)


def frontToQieGe():
    global finish, finishL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        finish = False
    elif name == '左耳':
        finishL = False
    # 将当前激活物体复制一份保存,用于切割之后的模块回到切割时还原
    # 当前物体
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "QieGeCopy"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "QieGeCopy"
    bpy.context.collection.objects.link(duplicate_obj1)
    if name == '右耳':
        moveToRight(duplicate_obj1)
        enum = bpy.context.scene.qieGeTypeEnumR
    elif name == '左耳':
        moveToLeft(duplicate_obj1)
        enum = bpy.context.scene.qieGeTypeEnumL
    duplicate_obj1.hide_set(True)
    duplicate_obj1.hide_set(False)
    duplicate_obj1.hide_set(True)

    # enum = bpy.context.scene.qieGeTypeEnum
    if enum == "OP1":
        initCircle(name)
        # workspace = bpy.context.window.workspace.name
        # if workspace == '布局.001':
        #     initCircle(bpy.context.scene.rightWindowObj)
    if enum == "OP2":
        initPlane(name)
        # workspace = bpy.context.window.workspace.name
        # if workspace == '布局.001':
        #     initPlane(bpy.context.scene.rightWindowObj)


def frontFromQieGe():
    # 当前物体
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        enum = bpy.context.scene.qieGeTypeEnumR
    elif name == '左耳':
        enum = bpy.context.scene.qieGeTypeEnumL
    if enum == "OP1":
        quitCut(name)
        utils_re_color(operator_obj, (1, 0.319, 0.133))
        apply_material()
    if enum == "OP2":
        quitStepCut(name)
        utils_re_color(operator_obj, (1, 0.319, 0.133))
        apply_material()

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(state=True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def backToQieGe():
    global finish, finishL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        finish = False
    elif name == '左耳':
        finishL = False

    # 若添加铸造法之后切换到支撑或者排气孔模块,再由支撑或排气孔模块跳过铸造法模块直接切换回前面的模块,则需要对物体进行特殊的处理
    casting_name = name + "CastingCompare"
    casting_compare_obj = bpy.data.objects.get(casting_name)
    if (casting_compare_obj != None):
        cur_obj = bpy.data.objects.get(name)
        casting_reset_obj = bpy.data.objects.get(name + "CastingReset")
        casting_last_obj = bpy.data.objects.get(name + "CastingLast")
        casting_compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if (cur_obj != None and casting_reset_obj != None and casting_last_obj != None and casting_compare_last_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
            casting_compare_obj.name = name
            bpy.data.objects.remove(casting_reset_obj, do_unlink=True)
            bpy.data.objects.remove(casting_last_obj, do_unlink=True)
            bpy.data.objects.remove(casting_compare_last_obj, do_unlink=True)
    # 后面模块切换到传声孔的时候,判断是否存在用于铸造法的 软耳膜附件Casting  和  用于字体附件的 LabelPlaneForCasting 若存在则将其删除
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    # 将后续模块中的reset和last都删除
    mould_reset = bpy.data.objects.get(name + "MouldReset")
    mould_last = bpy.data.objects.get(name + "MouldLast")
    sound_reset = bpy.data.objects.get(name + "SoundCanalReset")
    sound_last = bpy.data.objects.get(name + "SoundCanalLast")
    vent_reset = bpy.data.objects.get(name + "VentCanalReset")
    vent_last = bpy.data.objects.get(name + "VentCanalLast")
    handle_reset = bpy.data.objects.get(name + "HandleReset")
    handle_last = bpy.data.objects.get(name + "HandleLast")
    label_reset = bpy.data.objects.get(name + "LabelReset")
    label_last = bpy.data.objects.get(name + "LabelLast")
    casting_reset = bpy.data.objects.get(name + "CastingReset")
    casting_last = bpy.data.objects.get(name + "CastingLast")
    support_reset = bpy.data.objects.get(name + "SupportReset")
    support_last = bpy.data.objects.get(name + "SupportLast")
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
    if (mould_reset != None):
        bpy.data.objects.remove(mould_reset, do_unlink=True)
    if (mould_last != None):
        bpy.data.objects.remove(mould_last, do_unlink=True)
    if (sound_reset != None):
        bpy.data.objects.remove(sound_reset, do_unlink=True)
    if (sound_last != None):
        bpy.data.objects.remove(sound_last, do_unlink=True)
    if (vent_reset != None):
        bpy.data.objects.remove(vent_reset, do_unlink=True)
    if (vent_last != None):
        bpy.data.objects.remove(vent_last, do_unlink=True)
    if (handle_reset != None):
        bpy.data.objects.remove(handle_reset, do_unlink=True)
    if (handle_last != None):
        bpy.data.objects.remove(handle_last, do_unlink=True)
    if (label_reset != None):
        bpy.data.objects.remove(label_reset, do_unlink=True)
    if (label_last != None):
        bpy.data.objects.remove(label_last, do_unlink=True)
    if (casting_reset != None):
        bpy.data.objects.remove(casting_reset, do_unlink=True)
    if (casting_last != None):
        bpy.data.objects.remove(casting_last, do_unlink=True)
    if (support_reset != None):
        bpy.data.objects.remove(support_reset, do_unlink=True)
    if (support_last != None):
        bpy.data.objects.remove(support_last, do_unlink=True)
    if (sprue_reset != None):
        bpy.data.objects.remove(sprue_reset, do_unlink=True)
    if (sprue_last != None):
        bpy.data.objects.remove(sprue_last, do_unlink=True)
    support_casting_reset = bpy.data.objects.get(name + "CastingCompareSupportReset")
    support_casting_last = bpy.data.objects.get(name + "CastingCompareSupportLast")
    if (support_casting_reset != None):
        bpy.data.objects.remove(support_casting_reset, do_unlink=True)
    if (support_casting_last != None):
        bpy.data.objects.remove(support_casting_last, do_unlink=True)

    # 删除支撑和排气孔中可能存在的对比物体
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (soft_support_compare_obj != None):
        bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    if (hard_support_compare_obj != None):
        bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    # 根据切割中保存的物体,将其复制一份替换当前激活物体
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    copyname = name + "QieGeCopy"
    copy_obj = bpy.data.objects.get(copyname)
    # 当不存在QieGeCopy时，说明不是顺序执行的，直接跳过了切割这一步，
    if (copy_obj == None):
        lastname = name + "LocalThickLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            copy_obj = last_obj.copy()
            copy_obj.data = last_obj.data.copy()
            copy_obj.animation_data_clear()
            copy_obj.name = name + "QieGeCopy"
            bpy.context.collection.objects.link(copy_obj)
            copy_obj.hide_set(True)
        else:
            lastname = name + "DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            copy_obj = last_obj.copy()
            copy_obj.data = last_obj.data.copy()
            copy_obj.animation_data_clear()
            copy_obj.name = name + "QieGeCopy"
            bpy.context.collection.objects.link(copy_obj)
            copy_obj.hide_set(True)
    if name == '右耳':
        moveToRight(copy_obj)
    elif name == '左耳':
        moveToLeft(copy_obj)
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = copy_obj.copy()
    duplicate_obj.data = copy_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
        enum = bpy.context.scene.qieGeTypeEnumR
    elif name == '左耳':
        moveToLeft(duplicate_obj)
        enum = bpy.context.scene.qieGeTypeEnumL
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    if enum == "OP1":
        initCircle(name)
    if enum == "OP2":
        initPlane(name)


def backFromQieGe():
    # 将切割提交
    global finish, finishL

    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        finish_cur = finish
    elif name == '左耳':
        finish_cur = finishL

    if (not finish_cur):
        global operator_obj
        qieGeTypeEnum = None
        if bpy.context.scene.leftWindowObj == "右耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumR
        elif bpy.context.scene.leftWindowObj == "左耳":
            qieGeTypeEnum = bpy.context.scene.qieGeTypeEnumL

        if qieGeTypeEnum == 'OP1':
            saveCir()   # 保存圆环信息
            del_objs = [operator_obj + 'Circle', operator_obj + 'Torus', operator_obj + 'huanqiecompare',
                        operator_obj + 'circlecutpinghuaforreset']

            for obj in del_objs:
                if (bpy.data.objects.get(obj)):
                    obj1 = bpy.data.objects[obj]
                    bpy.data.objects.remove(obj1, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
            obj = bpy.data.objects[operator_obj]
            bpy.context.view_layer.objects.active = obj
            utils_re_color(operator_obj, (1, 0.319, 0.133))
            apply_material()
            # delete_vert_group("CircleCutBorderVertex")

        elif qieGeTypeEnum == 'OP2':
            saveStep(operator_obj)
            global loc_saved_left, loc_saved_right
            if operator_obj == '右耳':
                loc_saved_right = True
            elif operator_obj == '左耳':
                loc_saved_left = True
            # for i in bpy.context.visible_objects:
            #     if i.name == operator_obj:
            #         i.hide_select = False
            #         bpy.context.view_layer.objects.active = i
            #         bpy.ops.object.modifier_apply(modifier="step cut",single_user=True)
            # for i in bpy.context.visible_objects:
            #     if i.name == operator_obj+"StepCutplane":
            #         i.hide_set(False)
            #         bpy.context.view_layer.objects.active = i
            #         bpy.ops.object.modifier_apply(modifier="smooth",single_user=True)
            del_objs = [operator_obj, operator_obj + 'StepCutSphere1', operator_obj + 'StepCutSphere2',
                        operator_obj + 'StepCutSphere3', operator_obj + 'StepCutSphere4', operator_obj + 'StepCutplane',
                        operator_obj + 'ceqieCompare', operator_obj + 'stepcutpinghuaforreset']
            for obj in del_objs:
                if (bpy.data.objects.get(obj)):
                    obj1 = bpy.data.objects[obj]
                    bpy.data.objects.remove(obj1, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
            replace_name = operator_obj + 'stepcutpinghua'
            replace_obj = bpy.data.objects[replace_name]
            replace_obj.name = operator_obj

            name = operator_obj
            obj = bpy.data.objects[name]
            obj.hide_select = False
            # 删除创建的顶点组
            step_cut_vertex_group = obj.vertex_groups.get("before_cut")
            if (step_cut_vertex_group != None):
                obj.vertex_groups.remove(step_cut_vertex_group)
            # step_cut_smooth_vertex_group = obj.vertex_groups.get("StepCutBorderVertex")
            # if (step_cut_smooth_vertex_group != None):
            #     obj.vertex_groups.remove(step_cut_smooth_vertex_group)
            bpy.context.view_layer.objects.active = obj
            utils_re_color(operator_obj, (1, 0.319, 0.133))
            apply_material()

    # 当前主窗口物体
    name = bpy.context.scene.leftWindowObj
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "QieGeLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "QieGeLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    if name == '右耳':
        moveToRight(duplicate_obj1)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    utils_re_color(name, (1, 0.319, 0.133))

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(state=True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def register():
    bpy.utils.register_class(Circle_Cut)
    bpy.utils.register_class(Step_Cut)
    bpy.utils.register_class(Finish_Cut)
    bpy.utils.register_class(Reset_Cut)
    bpy.utils.register_class(Mirror_Cut)


def unregister():
    bpy.utils.unregister_class(Circle_Cut)
    bpy.utils.unregister_class(Step_Cut)
    bpy.utils.unregister_class(Finish_Cut)
    bpy.utils.unregister_class(Reset_Cut)
    bpy.utils.unregister_class(Mirror_Cut)
