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
import datetime
from math import *
import time
from .shell_canal import initial_shellcanal
from ..collision import generate_cubes
from .shell_canal import getObjectDic, updateShellCanal
from ..collision import update_cube_location_rotate, setActiveAndMoveCubeName, resetCubeLocationAndRotation, \
    get_is_collision_finish, set_is_collision_finish
from ...parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running, \
    get_shell_modal_start, set_shell_modal_start, get_point_qiehuan_modal_start, get_drag_curve_modal_start, \
    get_smooth_curve_modal_start
from ..parameters_for_create_mould import get_left_shell_plane_border, get_right_shell_plane_border, \
    get_left_shell_border, get_right_shell_border, set_left_shell_border, set_right_shell_border
from ...create_mould.hard_eardrum.hard_eardrum_cut import convex_hull

bottom_prev_radius = 8.0            #上次底部圆环切割时的直径(交集平面边缘点距离圆环位置的最大距离加上一个偏移值,用于调整圆环直径)
bottom_min_radius = 0               #上次底部圆环切割时的最小直径(交集平面边缘点距离圆环位置的最小距离,用于圆环平面切割后的边缘平滑)
middle_prev_radius = 6.0
middle_min_radius = 0
top_prev_radius = 4.0
top_min_radius = 0
cut_radius = 0
# 切割时的圆环信息（右耳）
bottom_right_last_loc = None
bottom_right_last_radius = None
bottom_right_last_ratation = None
middle_right_last_loc = None
middle_right_last_radius = None
middle_right_last_ratation = None
top_right_last_loc = None
top_right_last_radius = None
top_right_last_ratation = None
# 切割时的圆环信息（左耳）
bottom_left_last_loc = None
bottom_left_last_radius = None
bottom_left_last_ratation = None
middle_left_last_loc = None
middle_left_last_radius = None
middle_left_last_ratation = None
top_left_last_loc = None
top_left_last_radius = None
top_left_last_ratation = None

battery_mouse_press = False

#鼠标左键操控圆环旋转,右键操控圆环移动时,通过event记录相关信息
torus_left_mouse_press = False     # 鼠标左键是否按下
torus_right_mouse_press = False    # 鼠标右键是否按下
torus_initial_rotation_x = None        # 初始x轴旋转角度
torus_initial_rotation_y = None
torus_initial_rotation_z = None
torus_now_mouse_x = None               # 鼠标移动时的位置
torus_now_mouse_y = None
torus_initial_mouse_x = None           # 点击鼠标右键的初始位置
torus_initial_mouse_y = None
torus_is_moving = False
torus_dx = 0
torus_dy = 0



finish = False       # 用于控制modal的运行, True表示modal暂停
soft_modal_start = False


top_mouse_loc = None             # 记录鼠标在圆环上的位置,主要用于判断圆环切割有两个平面时移动到哪一个平面,后期优化未实时鼠标位置
middle_mouse_loc = None
bottom_mouse_loc = None


mouse_index = 0                  # 标志当前处于何种鼠标行为并防止重复调用同一鼠标行为
mouse_indexL = 0


bottom_last_right_offset = 0
bottom_last_left_offset = 0
plane_last_right_offset = 0
plane_last_left_offset = 0

# is_mouseSwitch_modal_start = False         #在启动下一个modal前必须将上一个modal关闭,防止modal开启过多过于卡顿
# is_mouseSwitch_modal_startL = False

def copy_model_for_top_circle_cut():
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    # 根据当前蓝线切割后的模型复制出一份物体用于调整顶部圆环的角度时回退重新切割
    shell_for_top_circle_cut_obj = bpy.data.objects.get(name + "shellObjForTopCircleCut")  # TODO 后期作外壳模块切换时记得将该物体删除
    if (shell_for_top_circle_cut_obj != None):
        bpy.data.objects.remove(shell_for_top_circle_cut_obj, do_unlink=True)
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellObjForTopCircleCut"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)


def copy_model_for_middle_circle_cut():
    name = bpy.context.scene.leftWindowObj
    inner_obj = bpy.data.objects.get(name + "Inner")
    # 复制出一份内壁物体用于中部圆环切割的回退
    shell_for_middle_circle_cut_obj = bpy.data.objects.get(name + "shellObjForMiddleCircleCut")  # TODO 后期作外壳模块切换时记得将该物体删除
    if (shell_for_middle_circle_cut_obj != None):
        bpy.data.objects.remove(shell_for_middle_circle_cut_obj, do_unlink=True)
    duplicate_obj = inner_obj.copy()
    duplicate_obj.data = inner_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + 'shellObjForMiddleCircleCut'
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)


def copy_model_for_collision_detection():
    # 复制出一份内壁物体用于碰撞检测
    name = bpy.context.scene.leftWindowObj
    shell_inner_obj = bpy.data.objects.get(name + "shellInnerObj")
    if (shell_inner_obj != None):
        bpy.data.objects.remove(shell_inner_obj, do_unlink=True)
    inner_obj =  bpy.data.objects.get(name + "shellObjForMiddleCircleCutCopy")
    duplicate_obj = inner_obj.copy()
    duplicate_obj.data = inner_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + 'shellInnerObj'
    bpy.context.scene.collection.objects.link(duplicate_obj)
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.mode_set(mode='EDIT')               # 将内侧模型物体法线反转,使得法线方向朝外,保证碰撞检测的正确性
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.mesh.region_to_loop()
    # bpy.ops.mesh.normals_make_consistent(inside=False)
    # bpy.ops.mesh.select_all(action='DESELECT')         #将内壁底面填充
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.remove_doubles(threshold=1)
    # bpy.ops.mesh.edge_face_add()
    bm = bmesh.from_edit_mesh(duplicate_obj.data)
    verts = [v for v in bm.verts if v.select]
    if len(verts) > 0:
        bpy.ops.mesh.fill()
    # bpy.ops.mesh.subdivide(number_cuts=3)    # 可能回造成闪退
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    newColor('shellInnerObjTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    duplicate_obj.data.materials.clear()
    duplicate_obj.data.materials.append(bpy.data.materials['shellInnerObjTransparency'])
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)


def copy_model_for_bottom_curve():
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    # bpy.ops.mesh.select_all(action='SELECT')
    # cur_obj.vertex_groups.new(name="SmoothVertex")
    # bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 根据上部蓝线切割后的模型复制出一份物体用于调整底部蓝线时回退重新桥接
    shell_for_bottom_curve_obj = bpy.data.objects.get(name + "shellObjForBottomCurve")  # TODO 后期作外壳模块切换时记得将该物体删除
    if (shell_for_bottom_curve_obj != None):
        bpy.data.objects.remove(shell_for_bottom_curve_obj, do_unlink=True)
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellObjForBottomCurve"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)


def init_shell():
    '''
    初始化外壳
    '''

    # 设置外壳的参数
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if bpy.context.scene.KongQiangMianBanTypeEnumR != 'OP2':
            bpy.context.scene.KongQiangMianBanTypeEnumR = 'OP2'
        if not bpy.context.scene.shiFouShangBuQieGeMianBanR:
            bpy.context.scene.shiFouShangBuQieGeMianBanR = True
        if bpy.context.scene.neiBianJiXianR:
            bpy.context.scene.neiBianJiXianR = False
    elif name == '左耳':
        if bpy.context.scene.KongQiangMianBanTypeEnumL != 'OP2':
            bpy.context.scene.KongQiangMianBanTypeEnumL = 'OP2'
        if not bpy.context.scene.shiFouShangBuQieGeMianBanL:
            bpy.context.scene.shiFouShangBuQieGeMianBanL = True
        if bpy.context.scene.neiBianJiXianL:
            bpy.context.scene.neiBianJiXianL = False

    # 复制一份底部切割后的物体
    copy_model_for_bottom_curve()

    # 初始化圆环和环体
    draw_cut_plane()

    #根据空腔面板的类型确定中间圆环的位置
    useMiddleTrous()

    #根据顶部圆环的位置对模型进行切割
    top_circle_cut()

    #根据顶部圆环切割后的模型实体化并分离出内壁
    shell_bottom_fill()

    #根据顶部切割后的顶部边缘
    top_smooth_success = top_circle_smooth()

    #根据中部圆环对实体化后的模型内壁进行切割并平滑
    middle_smooth_success = middle_circle_cut()

    # 合并内外壁
    join_outer_and_inner(top_smooth_success and middle_smooth_success)

    #底部蓝线切割电池仓平面
    shell_battery_plane_cut()

    # 初始化管道
    initial_shellcanal()

    # 初始化立方体组件
    generate_cubes()

    # 启动鼠标行为切换及更新函数
    bpy.ops.object.shell_switch('INVOKE_DEFAULT')


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
    shader.inputs[15].default_value = 0.105
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


def generate_circle_for_cut():
    global bottom_right_last_loc, bottom_right_last_radius, bottom_right_last_ratation, bottom_last_right_offset
    global bottom_left_last_loc, bottom_left_last_radius, bottom_left_last_ratation, bottom_last_left_offset
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        bottom_last_loc = bottom_right_last_loc
        bottom_last_ratation = bottom_right_last_ratation
        # last_radius = bottom_right_last_radius
        offset = bpy.context.scene.xiaFangYangXianPianYiR
        bottom_last_right_offset = offset
    elif name == '左耳':
        bottom_last_loc = bottom_left_last_loc
        bottom_last_ratation = bottom_left_last_ratation
        # last_radius = bottom_left_last_radius
        offset = bpy.context.scene.xiaFangYangXianPianYiL
        bottom_last_left_offset = offset

    # 创建底部圆环和环体
    if bottom_last_loc is None:
        verts = bpy.data.objects.get(name + "OriginForCreateMouldR").data.vertices
        zmax = max([v.co.z for v in verts])
        zmin = min([v.co.z for v in verts])
        initBottomZ = round(zmin + 0.2 * (zmax - zmin), 2)  # 底部圆环的Z坐标
        selected_verts = [v for v in verts if round(  # 选取Z坐标相等的顶点并计算中心点,得到圆环初始位置的X,Y轴坐标
            initBottomZ, 2) + 0.1 > round(v.co.z, 2) > round(initBottomZ, 2) - 0.1]
        center = (0, 0, 0)
        if selected_verts:
            center = sum((v.co for v in selected_verts),Vector()) / len(selected_verts)
        # max_distance = float('-inf')
        # for vertex in selected_verts:
        #     distance = (vertex.co - center).length
        #     max_distance = max(max_distance, distance)
        # bottom_radius = round(max_distance, 2) + 1

        initBottomX = center.x
        initBottomY = center.y
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=(initBottomX, initBottomY, initBottomZ + offset), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        bpy.context.object.name = name + "CutCircle"

    else:
        print('切割后初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=25, fill_type='NGON', calc_uvs=True,
                                          enter_editmode=False,
                                          align='WORLD',
                                          location=(bottom_last_loc.x, bottom_last_loc.y, bottom_last_loc.z + offset),
                                          rotation=(bottom_last_ratation[0], bottom_last_ratation[1],
                                                    bottom_last_ratation[2]),
                                          scale=(1.0, 1.0, 1.0))
        bpy.context.object.name = name + "CutCircle"

    circle = bpy.context.active_object
    circle.hide_set(True)
    if name == '右耳':
        moveToRight(circle)
    elif name == '左耳':
        moveToLeft(circle)
    normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
    if normal.z < 0:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')


def generate_border_curve():
    name = bpy.context.scene.leftWindowObj
    cut_obj_name = name + "CutCircle"
    if bpy.data.objects.get(cut_obj_name) is not None:
        cut_obj = bpy.data.objects.get(cut_obj_name)  # 根据布尔物体复制一份得到交集物体
        cut_obj_copy = cut_obj.copy()
        cut_obj_copy.data = cut_obj.data.copy()
        cut_obj_copy.name = cut_obj.name + "Copy"
        cut_obj_copy.animation_data_clear()
        cut_obj_copy.hide_set(False)
        bpy.context.scene.collection.objects.link(cut_obj_copy)
        if name == '右耳':
            moveToRight(cut_obj_copy)
        elif name == '左耳':
            moveToLeft(cut_obj_copy)

        obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.data.objects[name].vertex_groups.new(name="all")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        cut_obj_copy.select_set(True)
        bpy.ops.object.booltool_auto_difference()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='all')
        # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        # 用于上下桥接的顶点组，只包含当前孔边界
        obj.vertex_groups.new(name="BottomOuterBorderVertex")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        delete_vert_group("all")
        delete_success = delete_lower_part(group_name="BottomOuterBorderVertex")
        if not delete_success:
            raise ValueError("切割上部曲线出错")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.data.objects:
            if o.select_get():
                if o.name != name:
                    border_curve = o
        border_curve.name = name + "BottomRingBorderR"
        obj.select_set(False)
        bpy.context.view_layer.objects.active = border_curve
        border_curve.select_set(True)
        bpy.ops.object.convert(target='CURVE')
        resample_curve(160, border_curve.name)
        convert_to_mesh(name + "BottomRingBorderR", name + "meshBottomRingBorderR", 0.18)


def lower_circle_cut():
    name = bpy.context.scene.leftWindowObj
    cut_obj_name = name + "BottomCircle"
    if bpy.data.objects.get(cut_obj_name) is not None:
        cut_obj = bpy.data.objects.get(cut_obj_name)  # 根据布尔物体复制一份得到交集物体
        cut_obj_copy = cut_obj.copy()
        cut_obj_copy.data = cut_obj.data.copy()
        cut_obj_copy.name = cut_obj.name + "Copy"
        cut_obj_copy.animation_data_clear()
        bpy.context.scene.collection.objects.link(cut_obj_copy)
        if name == '右耳':
            moveToRight(cut_obj_copy)
        elif name == '左耳':
            moveToLeft(cut_obj_copy)
        cut_obj_copy.hide_set(False)
        cut_obj_copy.select_set(True)
        bpy.context.view_layer.objects.active = cut_obj_copy
        normal = cut_obj_copy.matrix_world.to_3x3() @ cut_obj_copy.data.polygons[0].normal
        if normal.z < 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.mode_set(mode='OBJECT')

        shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")
        replace_obj = shell_bool_obj.copy()
        replace_obj.data = shell_bool_obj.data.copy()
        replace_obj.name = shell_bool_obj.name + "Replace"
        replace_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(replace_obj)
        if name == '右耳':
            moveToRight(replace_obj)
        elif name == '左耳':
            moveToLeft(replace_obj)
        bpy.ops.object.select_all(action='DESELECT')
        replace_obj.hide_set(False)
        replace_obj.select_set(True)
        bpy.context.view_layer.objects.active = replace_obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        replace_obj.vertex_groups.new(name="all")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        cut_obj_copy.select_set(True)
        bpy.ops.object.booltool_auto_difference()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='all')
        # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        # 用于上下桥接的顶点组，只包含当前孔边界
        replace_obj.vertex_groups.new(name="BottomOuterCurveVertex")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        delete_vert_group("all")
        delete_success = delete_lower_part(group_name="BottomOuterCurveVertex")
        if not delete_success:
            raise ValueError("切割底部圆环出错")

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.data.objects:
            if o.select_get():
                if o.name != replace_obj.name:
                    border_curve = o
        if bpy.data.objects.get(name + "MiddleBaseCurve") != None:
            bpy.data.objects.remove(bpy.data.objects.get(name + "MiddleBaseCurve"), do_unlink=True)
        border_curve.name = name + "MiddleBaseCurve"
        replace_obj.select_set(False)
        bpy.context.view_layer.objects.active = border_curve
        border_curve.select_set(True)
        bpy.ops.object.convert(target='CURVE')

        bpy.data.objects.remove(bpy.data.objects.get(name), do_unlink=True)
        replace_obj.name = name
        replace_obj.select_set(True)
        bpy.context.view_layer.objects.active = replace_obj
        border_curve.select_set(False)
        border_curve.hide_set(True)


def delete_upper_part(group_name):
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.object
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group=group_name)
    bpy.ops.object.vertex_group_select()

    verts =  [v for v in bm.verts if v.select]
    if len(verts) == 0:
        bpy.ops.object.mode_set(mode='OBJECT')
        return False
    # 补面
    bpy.ops.mesh.fill()

    # 选择循环点
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
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
    bottom_outer_border_vertex = obj.vertex_groups.get(group_name)
    bpy.ops.object.vertex_group_set_active(group=group_name)
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    return True


def delete_lower_part(group_name):
    bpy.ops.object.mode_set(mode='EDIT')
    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group=group_name)
    bpy.ops.object.vertex_group_select()

    verts = [v for v in bm.verts if v.select]
    if len(verts) == 0:
        bpy.ops.object.mode_set(mode='OBJECT')
        return False
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
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = obj.vertex_groups.get(group_name)
    bpy.ops.object.vertex_group_set_active(group=group_name)
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    return True


def judge_if_need_invert():
    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return vert_order_by_z[0].select


def top_circle_cut():
    '''
    根据顶部圆环对模型进行切割
    '''
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    top_circle_obj = bpy.data.objects.get(name + "TopCircle")
    if(top_circle_obj != None):
        duplicate_obj = top_circle_obj.copy()                      #根据顶部圆环复制出一份物体用于布尔切割(布尔工具切割后会自动将该物体删除)
        duplicate_obj.data = top_circle_obj.data.copy()
        duplicate_obj.animation_data_clear()
        bpy.context.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(False)                             #将复制的顶部圆环选中并判断法线是否向上并反转,防止反向切割
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        normal = duplicate_obj.matrix_world.to_3x3() @ duplicate_obj.data.polygons[0].normal
        if normal.z > 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cur_obj
        cur_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        cur_obj.vertex_groups.new(name="Outer")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        duplicate_obj.select_set(True)
        bpy.ops.object.booltool_auto_difference()                     #作布尔差集(切割平面上的顶点作为交集会自动被选中)

        vert_group = cur_obj.vertex_groups.get('TopCutBorderVertex')  #将切割平面顶点保存到对应的顶点组中
        if (vert_group != None):
            bpy.ops.object.vertex_group_set_active(group='TopCutBorderVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='Outer')
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        cur_obj.vertex_groups.new(name="TopCutBorderVertex")
        bpy.ops.object.vertex_group_assign()
        # bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        delete_success = delete_upper_part("TopCutBorderVertex")
        if delete_success:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='TopCutBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.fill()
            bpy.ops.object.mode_set(mode='OBJECT')


def middle_circle_cut():
    '''
    根据中部圆环对实体化填充后的模型进行切割,切割内部
    '''
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
    elif (name == "左耳"):
        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
    cur_obj = bpy.data.objects.get(name)
    middle_circle_obj = bpy.data.objects.get(name + "MiddleCircle")
    if (middle_circle_obj != None and kongQiangMianBanType != 'OP3'):
        # 根据中部圆环复制出一份物体用于布尔切割(布尔工具切割后会自动将该物体删除)
        duplicate_obj = middle_circle_obj.copy()
        duplicate_obj.data = middle_circle_obj.data.copy()
        duplicate_obj.animation_data_clear()
        bpy.context.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(False)  # 将复制的顶部圆环选中并判断法线是否向上并反转,防止反向切割
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        normal = duplicate_obj.matrix_world.to_3x3() @ duplicate_obj.data.polygons[0].normal
        if normal.z > 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.mode_set(mode='OBJECT')

        #将用于回退的中部圆环切割的物体复制一份来作布尔切割
        shell_for_middle_circle_cut_obj = bpy.data.objects.get(name + "shellObjForMiddleCircleCut")
        shell_for_middle_circle_cut_copy_obj = bpy.data.objects.get(name + "shellObjForMiddleCircleCutCopy")
        if (shell_for_middle_circle_cut_copy_obj != None):
            bpy.data.objects.remove(shell_for_middle_circle_cut_copy_obj, do_unlink=True)
        shell_duplicate_for_middle_ciecle_cut_obj = shell_for_middle_circle_cut_obj.copy()
        shell_duplicate_for_middle_ciecle_cut_obj.data = shell_for_middle_circle_cut_obj.data.copy()
        shell_duplicate_for_middle_ciecle_cut_obj.animation_data_clear()
        bpy.context.collection.objects.link(shell_duplicate_for_middle_ciecle_cut_obj)
        if name == '右耳':
            moveToRight(shell_duplicate_for_middle_ciecle_cut_obj)
        elif name == '左耳':
            moveToLeft(shell_duplicate_for_middle_ciecle_cut_obj)
        shell_duplicate_for_middle_ciecle_cut_obj.hide_set(False)
        shell_duplicate_for_middle_ciecle_cut_obj.name = name + "shellObjForMiddleCircleCutCopy"

        # 将模型内壁和中部圆环作布尔差集(切割平面上的顶点作为交集会自动被选中)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = shell_duplicate_for_middle_ciecle_cut_obj
        shell_duplicate_for_middle_ciecle_cut_obj.select_set(True)
        duplicate_obj.select_set(True)
        bpy.ops.object.booltool_auto_difference()
        # bpy.ops.object.mode_set(mode='EDIT')              #由于模型内部不封闭,因此切割后需要补面
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='Inner')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.select_all(action='INVERT')                   #反选后得到切割后形成的边,补面
        # bpy.ops.mesh.edge_face_add()
        # delete_vert_group("TopCutBorderVertex")                    #删除TopCutBorderVertex并为MiddleCutBorderVertex顶点组重新赋值,包含切割边界顶点
        # shell_duplicate_for_middle_ciecle_cut_obj.vertex_groups.new(name="MiddleCutBorderVertex")
        # bpy.ops.object.vertex_group_assign()
        # bpy.ops.mesh.select_all(action='SELECT')                   #为Inner顶点组重新赋值,包含切割后模型内壁的所用顶点
        # bpy.ops.object.vertex_group_set_active(group='Inner')
        # bpy.ops.object.vertex_group_assign()
        # bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='Inner')
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')   # 反选后得到切割后形成的边,补面
        delete_vert_group("TopCutBorderVertex")   # 删除TopCutBorderVertex并为MiddleCutBorderVertex顶点组重新赋值,包含切割边界顶点
        shell_duplicate_for_middle_ciecle_cut_obj.vertex_groups.new(name="MiddleCutBorderVertex")
        bpy.ops.object.vertex_group_assign()
        delete_success = delete_upper_part("MiddleCutBorderVertex")

        if delete_success:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='MiddleCutBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.fill()
            bpy.ops.mesh.select_all(action='SELECT')  # 为Inner顶点组重新赋值,包含切割后模型内壁的所有顶点
            bpy.ops.object.vertex_group_set_active(group='Inner')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

        copy_model_for_collision_detection()

        # 将当前模型复制一份用于平滑失败的回退
        if bpy.data.objects.get(name + 'shellmiddlecutsmoothforreset') != None:
            bpy.data.objects.remove(bpy.data.objects[name + 'shellmiddlecutsmoothforreset'], do_unlink=True)
        duplicate_obj = shell_duplicate_for_middle_ciecle_cut_obj.copy()
        duplicate_obj.data = shell_duplicate_for_middle_ciecle_cut_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "shellmiddlecutsmoothforreset"
        bpy.context.collection.objects.link(duplicate_obj)
        if bpy.context.scene.leftWindowObj == '右耳':
            moveToRight(duplicate_obj)
        else:
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(True)

        # 平滑切割的边缘
        middle_smooth_success = middle_circle_smooth()

        # 合并内外壁
        # join_outer_and_inner()

        return middle_smooth_success


def top_circle_smooth():
    '''
    顶部圆环完成切割后对其边缘进行平滑
    '''
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        pianyi = bpy.context.scene.shangBuQieGeMianBanPianYiR
    elif name == '左耳':
        pianyi = bpy.context.scene.shangBuQieGeMianBanPianYiL

    # pianyi = 1
    cur_obj = bpy.data.objects.get(name)

    duplicate_obj = bpy.data.objects.get(name + 'shelltopcutsmoothforreset')
    # 复制一份物体用于平滑,平滑成功将其替换为当前操作模型,平滑失败则将其删除并回退平滑模型
    if bpy.data.objects.get(name + 'shelltopcutsmoothforresetcopy') != None:
        bpy.data.objects.remove(bpy.data.objects[name + 'shelltopcutsmoothforresetcopy'], do_unlink=True)
    replace_obj = duplicate_obj.copy()
    replace_obj.data = duplicate_obj.data.copy()
    replace_obj.name = duplicate_obj.name + "copy"
    replace_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(replace_obj)
    if name == '右耳':
        moveToRight(replace_obj)
    else:
        moveToLeft(replace_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = replace_obj
    replace_obj.hide_set(False)
    replace_obj.select_set(True)

    top_smooth_success = True
    try:
        # print("顶部平滑调用开始")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')         #选中平滑顶点,将模型内部的切割平面选中并fill,使得整个模型平面中间有边相互连接,提高平滑成功率
        bpy.ops.object.vertex_group_set_active(group='TopCutBorderVertex')
        bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.fill()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.region_to_loop()
        if pianyi > 0:
            global top_min_radius
            # print("顶部平滑调用开始1")
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            bpy.ops.circle.smooth(width=pianyi, center_border_group_name='TopCutBorderVertex',
                                  max_smooth_width=3, circle_radius=top_min_radius)
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(cur_obj, do_unlink=True)
        replace_obj.name = name

        # print("顶部平滑调用执行完成")

    except:
        top_smooth_success = False
        print('外壳顶部切割边缘平滑失败')
        # 回退切割模型并确保处于顶点模式
        if bpy.data.objects.get(duplicate_obj.name + 'copyBridgeBorder'):  # 平滑过程中可能存在的物体,平滑失败需要将其删除
            bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'copyBridgeBorder'], do_unlink=True)
        if (replace_obj != None):
            bpy.data.objects.remove(replace_obj, do_unlink=True)
        if(duplicate_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
            back_obj = duplicate_obj.copy()
            back_obj.data = duplicate_obj.data.copy()
            back_obj.name = name
            back_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(back_obj)
            if name == '右耳':
                moveToRight(back_obj)
            else:
                moveToLeft(back_obj)
            back_obj.hide_set(False)
            bpy.context.view_layer.objects.active = back_obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            # bpy.context.view_layer.objects.active = back_obj
            duplicate_obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

    return top_smooth_success




def middle_circle_smooth():
    '''
    中部圆环完成切割后对其边缘进行平滑
    '''
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        pianyi = bpy.context.scene.KongQiangMianBanSheRuPianYiR
    elif name == '左耳':
        pianyi = bpy.context.scene.KongQiangMianBanSheRuPianYiL

    # pianyi = 1
    #获取模型内壁复制物中部圆环切割后的物体
    cur_obj = bpy.data.objects.get(name + "shellObjForMiddleCircleCutCopy")
    duplicate_obj = bpy.data.objects.get(name + 'shellmiddlecutsmoothforreset')
    # 复制一份物体用于平滑,平滑成功将其替换为当前操作模型,平滑失败则将其删除并回退平滑模型
    if bpy.data.objects.get(name + 'shellmiddlecutsmoothforresetcopy') != None:
        bpy.data.objects.remove(bpy.data.objects[name + 'shellmiddlecutsmoothforresetcopy'], do_unlink=True)
    replace_obj = duplicate_obj.copy()
    replace_obj.data = duplicate_obj.data.copy()
    replace_obj.name = duplicate_obj.name + "copy"
    replace_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(replace_obj)
    if name == '右耳':
        moveToRight(replace_obj)
    else:
        moveToLeft(replace_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = replace_obj
    replace_obj.hide_set(False)
    replace_obj.select_set(True)

    middle_smooth_success = True
    try:
        # print("中部平滑调用开始")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')         #选中平滑顶点,将模型内部的切割平面选中并fill,使得整个模型平面中间有边相互连接,提高平滑成功率
        bpy.ops.object.vertex_group_set_active(group='MiddleCutBorderVertex')
        bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.fill()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.region_to_loop()
        if pianyi > 0:
            global middle_min_radius
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            bpy.ops.circle.smooth(width=pianyi, center_border_group_name='MiddleCutBorderVertex',
                                  max_smooth_width=3, circle_radius=middle_min_radius)
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
        #重新指定Inner顶点组,将平滑后新增的顶点也加入到Inner顶点组
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_set_active(group='Inner')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        #平滑成功后的内壁替换原模型
        bpy.data.objects.remove(cur_obj, do_unlink=True)
        replace_obj.name = name + "shellObjForMiddleCircleCutCopy"
        # print("中部平滑调用结束")

    except:
        middle_smooth_success = False
        print('外壳中部切割边缘平滑失败')
        if bpy.data.objects.get(duplicate_obj.name + 'copyBridgeBorder'):    #平滑过程中可能存在的物体,平滑失败需要将其删除
            bpy.data.objects.remove(bpy.data.objects[duplicate_obj.name + 'copyBridgeBorder'], do_unlink=True)
        if (replace_obj != None):
            bpy.data.objects.remove(replace_obj, do_unlink=True)

        # 回退切割模型并确保处于顶点模式
        if (duplicate_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
            back_obj = duplicate_obj.copy()
            back_obj.data = duplicate_obj.data.copy()
            back_obj.name = name + "shellObjForMiddleCircleCutCopy"
            back_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(back_obj)
            if name == '右耳':
                moveToRight(back_obj)
            else:
                moveToLeft(back_obj)
            back_obj.hide_set(False)
            bpy.context.view_layer.objects.active = back_obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            # bpy.context.view_layer.objects.active = back_obj
            duplicate_obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

    return middle_smooth_success



def resetCircleCutPlane():
    '''
    重置红环位置和电池板相关物体
    '''
    name = bpy.context.scene.leftWindowObj
    #重置圆环位置信息
    resetCircleInfo()

    # 删除原本的切割圆环
    # 删除切割圆环和平面
    need_to_delete_torus_and_circle_name_list = [name + 'TopTorus', name + 'MiddleTorus', name + "BottomTorus",
                                                 name + 'TopCircle', name + 'MiddleCircle', name + "BottomCircle",
                                                 name + "CutCircle"]
    delete_useless_object(need_to_delete_torus_and_circle_name_list)
    # 删除电池仓和电池平面
    need_to_delete_battery_and_batteryPlane_name_list = [name + 'shellBattery', name + 'shellBatteryPlane',
                                                         name + "batteryPlaneSnapCurve" ,name + "ShellOuterCutBatteryPlane"]
    delete_useless_object(need_to_delete_battery_and_batteryPlane_name_list)


def generateShell():
    set_shell_modal_finish(True)
    # 初始化圆环和环体
    draw_cut_plane()
    # 根据空腔面板的类型确定中间圆环的位置
    useMiddleTrous()
    # 根据顶部圆环的位置对模型进行切割
    top_circle_cut()
    # 根据顶部圆环切割后的模型实体化并分离出内壁
    shell_bottom_fill()
    # 根据顶部切割后的顶部边缘
    top_smooth_success = top_circle_smooth()
    # 根据中部圆环对实体化后的模型内壁进行切割
    middle_smooth_success = middle_circle_cut()
    # 合并内外壁
    join_outer_and_inner(top_smooth_success and middle_smooth_success)
    # 底部蓝线切割电池仓平面
    shell_battery_plane_cut()
    # 初始化立方体组件
    generate_cubes()
    set_shell_modal_finish(False)



def submitCircleCutPlane():
    '''
    提交红环切割,删除圆环相关物体和电池板相关物体
    '''
    name = bpy.context.scene.leftWindowObj
    #保存切割红环信息
    # saveCirInfo()   # 保存圆环信息有可能不起作用
    # 删除切割圆环和平面
    need_to_delete_torus_and_circle_name_list = [name + 'TopTorus', name + 'MiddleTorus', name + "BottomTorus",
                                                 name + 'TopCircle', name + 'MiddleCircle', name + "BottomCircle",
                                                 name + "CutCircle"]
    delete_useless_object(need_to_delete_torus_and_circle_name_list)
    # 删除电池仓和电池平面以及切割出的电池仓底面
    need_to_delete_battery_and_batteryPlane_name_list = [name + 'shellBattery', name + 'shellBatteryPlane', name + "batteryPlaneSnapCurve",name + "ShellOuterCutBatteryPlane"]
    delete_useless_object(need_to_delete_battery_and_batteryPlane_name_list)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj = bpy.data.objects.get(name)
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj
    utils_re_color(name, (1, 0.319, 0.133))


def shell_bottom_fill():
    print("开始填充外壳")

    # 首先，根据厚度使用一个实体化修改器
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        thickness = bpy.context.scene.zongHouDuR
    elif name == '左耳':
        thickness = bpy.context.scene.zongHouDuL

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.vertex_groups.new(name="Inner")
    obj.vertex_groups.new(name="BottomInnerCurveVertex")

    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # # bpy.ops.mesh.remove_doubles(threshold=0.2)
    # # 记录外边界顶点坐标
    # mesh = obj.data
    # bm = bmesh.from_edit_mesh(mesh)
    # bottom_outer_border_co = [v.co for v in bm.verts if v.select]
    # first_bottom_vert_co = obj.matrix_world @ bottom_outer_border_co[0]
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')

    #实体化出内壁
    thickness = 1

    modifier = obj.modifiers.new(name="Thickness", type='SOLIDIFY')
    bpy.context.object.modifiers["Thickness"].solidify_mode = 'NON_MANIFOLD'
    bpy.context.object.modifiers["Thickness"].thickness = thickness
    # bpy.context.object.modifiers["Thickness"].use_rim = False
    bpy.context.object.modifiers["Thickness"].nonmanifold_thickness_mode = 'FIXED'  # 防止实体化之后某些顶点出现毛刺过长的现象
    bpy.context.object.modifiers["Thickness"].shell_vertex_group = "Inner"
    bpy.context.object.modifiers["Thickness"].rim_vertex_group = "BottomInnerCurveVertex"
    bpy.ops.object.modifier_apply(modifier="Thickness", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bpy.ops.mesh.select_all(action='DESELECT')
    # 选中内外边界
    bpy.ops.object.vertex_group_set_active(group='BottomInnerCurveVertex')
    bpy.ops.object.vertex_group_select()
    all_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_deselect()
    outer_index = [v.index for v in bm.verts if v.select]
    inner_index = [index for index in all_index if index not in outer_index]
    bpy.ops.object.mode_set(mode='OBJECT')
    delete_vert_group("BottomOuterCurveVertex")
    delete_vert_group("BottomInnerCurveVertex")
    set_vert_group("BottomOuterCurveVertex", outer_index)
    set_vert_group("BottomInnerCurveVertex", inner_index)

    # 使用平滑修改器平滑内壁
    modifier = obj.modifiers.new(name="Smooth", type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].factor = 1
    bpy.context.object.modifiers["Smooth"].iterations = int(round(thickness, 1) * 10)
    bpy.context.object.modifiers["Smooth"].vertex_group = "Inner"
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()

    # 分离出内外壁
    # bpy.ops.object.mode_set(mode='EDIT')
    # bm = bmesh.from_edit_mesh(obj.data)
    # bpy.ops.mesh.select_all(action='DESELECT')
    # # 选中与记录下的顶点坐标最接近的顶点，选中相连元素即为外壁,再反选即为内壁
    # min_dist = float('inf')
    # closest_vertex = None
    # bm.verts.ensure_lookup_table()
    # verts = [v for v in bm.verts if v.is_boundary]
    # for vert in verts:
    #     world_co = obj.matrix_world @ vert.co
    #     dist = (world_co - first_bottom_vert_co).length
    #     if dist < min_dist:
    #         min_dist = dist
    #         closest_vertex = vert
    # 选择最近的顶点
    # if closest_vertex is not None:
    #     closest_vertex.select = True
    # bpy.ops.mesh.select_linked(delimit=set())
    # bpy.ops.mesh.select_all(action='INVERT')

    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.data.objects:
        if o.select_get():
            if o.name != name:
                inner_obj = o
    if bpy.data.objects.get(name + "shellObjForMiddleCircleCut") != None:
        bpy.data.objects.remove(bpy.data.objects.get(name + "shellObjForMiddleCircleCut"), do_unlink=True)
    inner_obj.name = name + "shellObjForMiddleCircleCut"
    inner_obj.hide_set(True)

    # copy_model_for_middle_circle_cut()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # 将当前模型复制一份用于平滑失败的回退
    if bpy.data.objects.get(name + 'shelltopcutsmoothforreset') != None:
        bpy.data.objects.remove(bpy.data.objects[name + 'shelltopcutsmoothforreset'], do_unlink=True)
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shelltopcutsmoothforreset"
    bpy.context.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)

    # 重新设置内外壁顶点组
    # bpy.ops.object.select_all(action='DESELECT')
    # obj.select_set(True)
    # bpy.context.view_layer.objects.active = obj
    # # delete_vert_group('BottomOuterBorderVertex')
    # delete_vert_group('BottomOuterCurveVertex')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bm = bmesh.from_edit_mesh(obj.data)
    # for v in bm.verts:
    #     if v.is_boundary:
    #         v.select_set(True)
    # # obj.vertex_groups.new(name="BottomOuterBorderVertex")
    # obj.vertex_groups.new(name="BottomOuterCurveVertex")
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')

    # bpy.ops.object.select_all(action='DESELECT')
    # inner_obj.select_set(True)
    # bpy.context.view_layer.objects.active = inner_obj
    # # delete_vert_group('BottomOuterBorderVertex')
    # delete_vert_group('BottomOuterCurveVertex')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bm = bmesh.from_edit_mesh(inner_obj.data)
    # for v in bm.verts:
    #     if v.is_boundary:
    #         v.select_set(True)
    # # inner_obj.vertex_groups.new(name="BottomInnerBorderVertex")
    # inner_obj.vertex_groups.new(name="BottomInnerCurveVertex")
    # bpy.ops.object.vertex_group_assign()
    # # 这个顶点组用于寻找内壁切割边界
    # # bpy.ops.mesh.select_all(action='SELECT')
    # # inner_obj.vertex_groups.new(name="Inner")
    # # bpy.ops.object.vertex_group_assign()
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')

    # 使用平滑修改器平滑内壁
    # modifier = inner_obj.modifiers.new(name="Smooth", type='SMOOTH')
    # bpy.context.object.modifiers["Smooth"].factor = 1
    # bpy.context.object.modifiers["Smooth"].iterations = int(round(thickness, 1) * 10)
    # # bpy.context.object.modifiers["Smooth"].vertex_group = 'SmoothVertex'
    # bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)


def join_outer_and_inner(success):
    '''
    将模型内壁与切割后的内壁合并
    '''
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    # 将模型原始内壁删除
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.view_layer.objects.active = cur_obj
    # cur_obj.select_set(True)
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='Inner')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.delete(type='FACE')
    # bpy.ops.object.mode_set(mode='OBJECT')

    # 合并切割和平滑后的内壁
    shell_duplicate_for_middle_circle_cut_obj = bpy.data.objects.get(name + "shellObjForMiddleCircleCutCopy")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cur_obj
    cur_obj.select_set(True)
    shell_duplicate_for_middle_circle_cut_obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)  # 合并后去除位置重叠的顶点
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    if not success:
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        cur_obj.data.materials.clear()
        cur_obj.data.materials.append(bpy.data.materials["error_yellow"])


def useMiddleTrous():
    '''
    是否开启中部圆环切割
    开启中部圆环切割则使用中部红环确定切割平面位置
    不开启中部圆环切割则根据上部切割平面与偏移距离确定切割平面位置
    '''
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
        middle_circle_offset = bpy.context.scene.ShangBuQieGeBanPianYiR
    elif (name == "左耳"):
        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
        middle_circle_offset = bpy.context.scene.ShangBuQieGeBanPianYiL

    name = bpy.context.scene.leftWindowObj
    top_torus_obj = bpy.data.objects.get(name + 'TopTorus')
    top_circle_obj = bpy.data.objects.get(name + 'TopCircle')
    middle_torus_obj = bpy.data.objects.get(name + 'MiddleTorus')
    middle_circle_obj = bpy.data.objects.get(name + 'MiddleCircle')
    if(top_torus_obj != None and top_circle_obj != None and middle_torus_obj != None and middle_circle_obj != None):
        #先将圆环切割平面显示
        top_circle_obj.hide_set(False)
        middle_circle_obj.hide_set(False)
        #使用红环
        if(kongQiangMianBanType == 'OP1'):
            #将中部圆环显示出来
            middle_torus_obj.hide_set(False)
            # 将中部切割圆环设置为中部切割平面的位置
            middle_torus_obj.location = middle_circle_obj.location
            middle_torus_obj.rotation_euler = middle_circle_obj.rotation_euler
        #不使用红环
        elif(kongQiangMianBanType == 'OP2'):
            #将中部圆环隐藏
            middle_torus_obj.hide_set(True)
            #根据顶部切割平面和offset参数大小设置中部切割圆环的位置
            if top_circle_obj.type == 'MESH':
                ori_circle_me = top_circle_obj.data
                ori_circle_bm = bmesh.new()
                ori_circle_bm.from_mesh(ori_circle_me)
                ori_circle_bm.verts.ensure_lookup_table()

                # 获取平面法向
                plane_vert0 = ori_circle_bm.verts[0]
                plane_vert1 = ori_circle_bm.verts[1]
                plane_vert2 = ori_circle_bm.verts[2]
                point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
                point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
                point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
                # 计算两个向量
                vector1 = point2 - point1
                vector2 = point3 - point1
                # 计算法向量
                normal = vector1.cross(vector2)
                if(normal.z > 0):
                    normal = -normal

                top_circle_obj_location = top_circle_obj.location
                middle_circle_obj_location = top_circle_obj_location + normal.normalized() * middle_circle_offset

                ori_circle_bm.free()

                #更新中部切割平面的位置
                middle_circle_obj.location = middle_circle_obj_location
                middle_circle_obj.rotation_euler = top_circle_obj.rotation_euler
        #不使用中部切割
        elif(kongQiangMianBanType == 'OP3'):
            # 将中部圆环隐藏出来
            middle_torus_obj.hide_set(True)
        #将圆环切割平面隐藏
        top_circle_obj.hide_set(True)
        middle_circle_obj.hide_set(True)


def update_middle_circle_offset():
    '''
    不使用中部切割红环时,根据offset参数和顶部切割平面位置确定中部切割平面的位置
    '''
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
        middle_circle_offset = bpy.context.scene.ShangBuQieGeBanPianYiR
    elif (name == "左耳"):
        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
        middle_circle_offset = bpy.context.scene.ShangBuQieGeBanPianYiL


    name = bpy.context.scene.leftWindowObj
    top_circle_obj = bpy.data.objects.get(name + 'TopCircle')
    middle_circle_obj = bpy.data.objects.get(name + 'MiddleCircle')
    if (top_circle_obj != None and middle_circle_obj != None  and kongQiangMianBanType == 'OP2'):
        # 先将圆环切割平面显示
        top_circle_obj.hide_set(False)
        middle_circle_obj.hide_set(False)

        # 根据顶部切割平面和offset参数大小设置中部切割圆环的位置
        if top_circle_obj.type == 'MESH':
            ori_circle_me = top_circle_obj.data
            ori_circle_bm = bmesh.new()
            ori_circle_bm.from_mesh(ori_circle_me)
            ori_circle_bm.verts.ensure_lookup_table()

            # 获取平面法向
            plane_vert0 = ori_circle_bm.verts[0]
            plane_vert1 = ori_circle_bm.verts[1]
            plane_vert2 = ori_circle_bm.verts[2]
            point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
            point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
            point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
            # 计算两个向量
            vector1 = point2 - point1
            vector2 = point3 - point1
            # 计算法向量
            normal = vector1.cross(vector2)
            if (normal.z > 0):
                normal = -normal
            top_circle_obj_location = top_circle_obj.location
            middle_circle_obj_location = top_circle_obj_location + normal.normalized() * middle_circle_offset

            ori_circle_bm.free()

            #更新中部切割平面的位置
            middle_circle_obj.location = middle_circle_obj_location
            middle_circle_obj.rotation_euler = top_circle_obj.rotation_euler

        # 将圆环切割平面隐藏
        top_circle_obj.hide_set(True)
        middle_circle_obj.hide_set(True)


def update_top_circle_cut():
    '''
    每次调整顶部圆环之后都需要根据蓝线切割后的模型使用顶部圆环进行切割,之后再填充模型
    '''
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    top_circle_cut_obj = bpy.data.objects.get(name + "shellObjForTopCircleCut")
    if(cur_obj != None and top_circle_cut_obj != None):
        bpy.data.objects.remove(cur_obj, do_unlink=True)

        duplicate_obj = top_circle_cut_obj.copy()
        duplicate_obj.data = top_circle_cut_obj.data.copy()
        duplicate_obj.animation_data_clear()
        bpy.context.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(False)
        duplicate_obj.name = name

        # 根据顶部圆环的位置对模型进行切割
        top_circle_cut()

        # 根据顶部圆环切割后的模型实体化填充出内壁
        shell_bottom_fill()

        # 根据顶部切割后的顶部边缘
        top_smooth_success = top_circle_smooth()

        # 根据中部圆环对实体化后的模型内壁进行切割
        middle_smooth_success = middle_circle_cut()

        # 合并内外壁
        join_outer_and_inner(top_smooth_success and middle_smooth_success)

        # # 根据中部切割后的顶部边缘
        # middle_circle_smooth()


def update_top_circle_smooth():
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellObjForMiddleCircleCutCopy"
    bpy.context.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    top_smooth_success = top_circle_smooth()
    join_outer_and_inner(top_smooth_success)


def update_middle_circle_smooth():
    name = bpy.context.scene.leftWindowObj
    circle_cut_obj = bpy.data.objects.get(name + 'shellObjForMiddleCircleCut')
    duplicate_obj = circle_cut_obj.copy()
    duplicate_obj.data = circle_cut_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellObjForMiddleCircleCutCopy"
    bpy.context.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(False)
    middle_smooth_success = middle_circle_smooth()
    # 将模型原始内壁删除
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cur_obj
    cur_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    join_outer_and_inner(middle_smooth_success)


def update_middle_circle_cut():
    '''
    每次调整中部圆环之后都需要根据蓝线切割后的模型使用顶部圆环进行切割,之后再填充模型
    '''
    middle_smooth_success = middle_circle_cut()
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cur_obj
    cur_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    # middle_circle_smooth()
    join_outer_and_inner(middle_smooth_success)

def shell_battery_plane_cut():
    '''
    根据外壳中的切割蓝线,对底部电池面板进行切割
    '''
    name = bpy.context.scene.leftWindowObj
    shell_battery_plane_obj = bpy.data.objects.get(name + "shellBatteryPlane")
    loft_obj = bpy.data.objects.get(name + "shellLoftObj")
    if bpy.data.objects.get(name + "ShellOuterCutBatteryPlane") != None:
        bpy.data.objects.remove(bpy.data.objects.get(name + "ShellOuterCutBatteryPlane"), do_unlink=True)
    if (shell_battery_plane_obj != None and loft_obj != None):
        shell_outer_cut_battery_plane_obj = loft_obj.copy()
        shell_outer_cut_battery_plane_obj.data = loft_obj.data.copy()
        shell_outer_cut_battery_plane_obj.animation_data_clear()
        shell_outer_cut_battery_plane_obj.name = name + "ShellOuterCutBatteryPlane"
        bpy.context.collection.objects.link(shell_outer_cut_battery_plane_obj)
        if (name == "右耳"):
            moveToRight(shell_outer_cut_battery_plane_obj)
        elif (name == "左耳"):
            moveToLeft(shell_outer_cut_battery_plane_obj)
        newColor('batteryPlaneCutYellow', 1, 0.319, 0.133, 0, 1)
        shell_outer_cut_battery_plane_obj.data.materials.clear()
        shell_outer_cut_battery_plane_obj.data.materials.append(bpy.data.materials["batteryPlaneCutYellow"])
        #激活用于电池平面切割的物体并延长其底部,保证切割的准确性
        bpy.ops.object.select_all(action='DESELECT')
        shell_outer_cut_battery_plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_outer_cut_battery_plane_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.extrude_context_move(TRANSFORM_OT_translate={"value": (0, 0, -1)})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        #根据电池面板原型复制一份物体用于和上述分离出的物体作布尔交集,得到切割后的电池面板
        duplicate_obj = shell_battery_plane_obj.copy()
        duplicate_obj.data = shell_battery_plane_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "shellBatteryPlaneForCut"
        bpy.context.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(False)
        #作布尔交集得到蓝线切割后的电池面板
        bpy.ops.object.select_all(action='DESELECT')
        duplicate_obj.select_set(True)
        shell_outer_cut_battery_plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = shell_outer_cut_battery_plane_obj
        bpy.ops.object.booltool_auto_intersect()    # TODO: 有可能切割不成功

        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cur_obj
        cur_obj.select_set(True)


def draw_cut_plane():
    '''
    初始化圆圈与圆环
    '''
    global bottom_prev_radius, bottom_min_radius, middle_prev_radius, middle_min_radius, top_prev_radius, top_min_radius
    global bottom_right_last_loc, bottom_right_last_radius, bottom_right_last_ratation, bottom_left_last_loc, bottom_left_last_radius, bottom_left_last_ratation
    global middle_right_last_loc, middle_right_last_radius, middle_right_last_ratation, middle_left_last_loc, middle_left_last_radius, middle_left_last_ratation
    global top_right_last_loc, top_right_last_radius, top_right_last_ratation, top_left_last_loc, top_left_last_radius, top_left_last_ratation

    name = bpy.context.scene.leftWindowObj

    if name == '右耳':
        bottom_last_loc = bottom_right_last_loc
        bottom_last_ratation = bottom_right_last_ratation
        bottom_last_radius = bottom_right_last_radius
        middle_last_loc = middle_right_last_loc
        middle_last_ratation = middle_right_last_ratation
        middle_last_radius = middle_right_last_radius
        top_last_loc = top_right_last_loc
        top_last_ratation = top_right_last_ratation
        top_last_radius = top_right_last_radius
    elif name == '左耳':
        bottom_last_loc = bottom_left_last_loc
        bottom_last_ratation = bottom_left_last_ratation
        bottom_last_radius = bottom_left_last_radius
        middle_last_loc = middle_left_last_loc
        middle_last_ratation = middle_left_last_ratation
        middle_last_radius = middle_left_last_radius
        top_last_loc = top_left_last_loc
        top_last_ratation = top_left_last_ratation
        top_last_radius = top_left_last_radius

    # obj_main = bpy.data.objects[name]
    obj_main = bpy.data.objects.get(name + "OriginForCreateMouldR")

    #复制出一份物体用于布尔交集切割得到切割平面,再根据切割平面动态调整圆环大小
    shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")
    if (shell_bool_obj != None):
        bpy.data.objects.remove(shell_bool_obj, do_unlink=True)
    duplicate_obj = obj_main.copy()
    duplicate_obj.data = obj_main.data.copy()
    duplicate_obj.name = name + "ShellBoolObj"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)


    #获取圆环初始位置initX,initY,initZ和圆环初始大小
    # bpy.ops.object.select_all(action='DESELECT')
    # obj_main.select_set(True)
    # bpy.context.view_layer.objects.active = obj_main
    # bpy.ops.object.mode_set(mode='EDIT')
    #
    # bm = bmesh.from_edit_mesh(obj_main.data)                             #获取模型z轴坐标的最大最小值
    # z_max = float('-inf')
    # z_min = float('inf')
    # for vertex in bm.verts:
    #     z_max = max(z_max, vertex.co.z)
    #     z_min = min(z_min, vertex.co.z)
    # zmax = z_max
    # zmin = z_min

    verts = bpy.data.objects.get(name + "OriginForCreateMouldR").data.vertices
    zmax = max([v.co.z for v in verts])
    zmin = min([v.co.z for v in verts])

    initBottomZ = round(zmin + 0.2 * (zmax - zmin), 2)                  # 底部圆环的Z坐标
    # selected_verts = [v for v in bm.verts if round(                     # 选取Z坐标相等的顶点并计算中心点,得到圆环初始位置的X,Y轴坐标
    #     initBottomZ, 2) + 0.1 > round(v.co.z, 2) > round(initBottomZ, 2) - 0.1]
    selected_verts = [v for v in verts if round(
        initBottomZ, 2) + 0.1 > round(v.co.z, 2) > round(initBottomZ, 2) - 0.1]
    center = (0, 0, 0)
    if selected_verts:
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        print("Geometry Center:", center)
    initBottomX = center.x
    initBottomY = center.y
    max_distance = float('-inf')                                       # 计算底部圆环Z坐标相等的顶点到重新点的最大距离和最小距离
    min_distance = float('inf')
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)
        min_distance = min(min_distance, distance)
    bottom_prev_radius = round(max_distance, 2) + 1
    bottom_min_radius = round(min_distance, 2)

    initMiddleZ = round(zmin + 0.8 * (zmax - zmin), 2)                  # 中部圆环的Z坐标
    # selected_verts = [v for v in bm.verts if round(                     # 选取Z坐标相等的顶点并计算中心点,得到圆环初始位置的X,Y轴坐标
    #     initMiddleZ, 2) + 0.1 > round(v.co.z, 2) > round(initMiddleZ, 2) - 0.1]
    selected_verts = [v for v in verts if round(
        initMiddleZ, 2) + 0.1 > round(v.co.z, 2) > round(initMiddleZ, 2) - 0.1]
    center = (0, 0, 0)
    if selected_verts:
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        print("Geometry Center:", center)
    initMiddleX = center.x
    initMiddleY = center.y
    max_distance = float('-inf')                                       # 计算中部圆环Z坐标相等的顶点到重新点的最大距离和最小距离
    min_distance = float('inf')
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)
        min_distance = min(min_distance, distance)
    middle_prev_radius = round(max_distance, 2) + 1
    middle_min_radius = round(min_distance, 2)

    initTopZ = round(zmin + 0.95 * (zmax - zmin), 2)                    # 顶部圆环的Z坐标
    # selected_verts = [v for v in bm.verts if round(                    # 选取Z坐标相等的顶点并计算中心点,得到圆环初始位置的X,Y轴坐标
    #     initTopZ, 2) + 0.1 > round(v.co.z, 2) > round(initTopZ, 2) - 0.1]
    selected_verts = [v for v in verts if round(
        initTopZ, 2) + 0.1 > round(v.co.z, 2) > round(initTopZ, 2) - 0.1]
    center = (0, 0, 0)
    if selected_verts:
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        print("Geometry Center:", center)
    initTopX = center.x
    initTopY = center.y
    max_distance = float('-inf')                                        # 计算顶部圆环Z坐标相等的顶点到重新点的最大距离和最小距离
    min_distance = float('inf')
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)
        min_distance = min(min_distance, distance)
    top_prev_radius = round(max_distance, 2) + 1
    top_min_radius = round(min_distance, 2)


    # bpy.ops.object.mode_set(mode='OBJECT')



    # 创建底部圆环和环体
    if bottom_last_loc is None:
        print('正常初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=(initBottomX, initBottomY, initBottomZ), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        bottom_circle_obj = bpy.context.active_object
        # 初始化环体,用于显示并调整位置和角度
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(initBottomX, initBottomY, initBottomZ), rotation=(0.0, 0, 0),
                                         major_segments=80, minor_segments=80, major_radius=bottom_prev_radius, minor_radius=0.4)
        bottom_torus_obj = bpy.context.active_object
        bottom_center = (initBottomX, initBottomY, initBottomZ)
        bottom_rotation = (0.0, 0.0, 0.0)
    else:
        print('切割后初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                                          align='WORLD',
                                          location=bottom_last_loc,
                                          rotation=(bottom_last_ratation[0], bottom_last_ratation[1], bottom_last_ratation[2]),
                                          scale=(1.0, 1.0, 1.0))
        bottom_circle_obj = bpy.context.active_object
        # 初始化环体,用于显示并调整位置和角度
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=bottom_last_loc,
                                         rotation=(bottom_last_ratation[0], bottom_last_ratation[1], bottom_last_ratation[2]),
                                         major_segments=80, minor_segments=80, major_radius=bottom_last_radius,
                                         minor_radius=0.4)
        bottom_torus_obj = bpy.context.active_object
        bottom_prev_radius = bottom_last_radius
        bottom_center = bottom_last_loc
        bottom_rotation = (bottom_last_ratation[0], bottom_last_ratation[1], bottom_last_ratation[2])
    #初始化环体颜色
    # bottom_torus_obj = bpy.data.objects.get('Torus')
    newColor("toursRed", 1, 0, 0, 0, 1)
    bottom_torus_obj.data.materials.clear()
    bottom_torus_obj.data.materials.append(bpy.data.materials['toursRed'])
    if name == '右耳':
        moveToRight(bottom_torus_obj)
    elif name == '左耳':
        moveToLeft(bottom_torus_obj)
    #将圆环隐藏并反转法线,保证切割方向的正确性
    # bottom_circle_obj = bpy.data.objects.get('Circle')
    if name == '右耳':
        moveToRight(bottom_circle_obj)
    elif name == '左耳':
        moveToLeft(bottom_circle_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bottom_circle_obj.select_set(True)
    bpy.context.view_layer.objects.active = bottom_circle_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals(only_clnors=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 创建中部圆环和环体
    if middle_last_loc is None:
        print('正常初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=(initMiddleX, initMiddleY, initMiddleZ), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        middle_circle_obj = bpy.context.active_object
        # 初始化环体,用于显示并调整位置和角度
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(initMiddleX, initMiddleY, initMiddleZ), rotation=(0.0, 0, 0),
                                         major_segments=80, minor_segments=80, major_radius=middle_prev_radius,
                                         minor_radius=0.4)
        middle_torus_obj = bpy.context.active_object
    else:
        print('切割后初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                                          align='WORLD',
                                          location=middle_last_loc,
                                          rotation=(middle_last_ratation[0], middle_last_ratation[1], middle_last_ratation[2]),
                                          scale=(1.0, 1.0, 1.0))
        middle_circle_obj = bpy.context.active_object
        # 初始化环体,用于显示并调整位置和角度
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=middle_last_loc,
                                         rotation=(middle_last_ratation[0], middle_last_ratation[1], middle_last_ratation[2]),
                                         major_segments=80, minor_segments=80, major_radius=middle_last_radius,
                                         minor_radius=0.4)
        middle_torus_obj = bpy.context.active_object
        middle_prev_radius = middle_last_radius
    # 初始化环体颜色
    # middle_torus_obj = bpy.data.objects.get('Torus.001')
    newColor("toursRed", 1, 0, 0, 0, 1)
    middle_torus_obj.data.materials.clear()
    middle_torus_obj.data.materials.append(bpy.data.materials['toursRed'])
    if name == '右耳':
        moveToRight(middle_torus_obj)
    elif name == '左耳':
        moveToLeft(middle_torus_obj)
    # 将圆环隐藏并反转法线,保证切割方向的正确性
    # middle_circle_obj = bpy.data.objects.get('Circle.001')
    if name == '右耳':
        moveToRight(middle_circle_obj)
    elif name == '左耳':
        moveToLeft(middle_circle_obj)
    bpy.ops.object.select_all(action='DESELECT')
    middle_circle_obj.select_set(True)
    bpy.context.view_layer.objects.active = middle_circle_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals(only_clnors=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 创建顶部圆环和环体
    if top_last_loc is None:
        print('正常初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(
            vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD',
            location=(initTopX, initTopY, initTopZ), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        top_circle_obj = bpy.context.active_object
        # 初始化环体,用于显示并调整位置和角度
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(initTopX, initTopY, initTopZ), rotation=(0.0, 0, 0),
                                         major_segments=80, minor_segments=80, major_radius=top_prev_radius,
                                         minor_radius=0.4)
        top_torus_obj = bpy.context.active_object
    else:
        print('切割后初始化')
        # 初始化圆环平面,用于布尔切割
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                                          align='WORLD',
                                          location=top_last_loc,
                                          rotation=(top_last_ratation[0], top_last_ratation[1], top_last_ratation[2]),
                                          scale=(1.0, 1.0, 1.0))
        top_circle_obj = bpy.context.active_object
        # 初始化环体,用于显示并调整位置和角度
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=top_last_loc,
                                         rotation=(top_last_ratation[0], top_last_ratation[1], top_last_ratation[2]),
                                         major_segments=80, minor_segments=80, major_radius=top_last_radius,
                                         minor_radius=0.4)
        top_torus_obj = bpy.context.active_object
        top_prev_radius = top_last_radius
    # 初始化环体颜色
    # top_torus_obj = bpy.data.objects.get('Torus.002')
    newColor("toursRed", 1, 0, 0, 0, 1)
    top_torus_obj.data.materials.clear()
    top_torus_obj.data.materials.append(bpy.data.materials['toursRed'])
    if name == '右耳':
        moveToRight(top_torus_obj)
    elif name == '左耳':
        moveToLeft(top_torus_obj)
    # 将圆环隐藏并反转法线,保证切割方向的正确性
    # top_circle_obj = bpy.data.objects.get('Circle.002')
    if name == '右耳':
        moveToRight(top_circle_obj)
    elif name == '左耳':
        moveToLeft(top_circle_obj)
    bpy.ops.object.select_all(action='DESELECT')
    top_circle_obj.select_set(True)
    bpy.context.view_layer.objects.active = top_circle_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals(only_clnors=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    bottom_torus_obj.name = name + "BottomTorus"           #重命名环体和圆环
    bottom_circle_obj.name = name + "BottomCircle"
    middle_torus_obj.name = name + "MiddleTorus"
    middle_circle_obj.name = name + "MiddleCircle"
    top_torus_obj.name = name + "TopTorus"
    top_circle_obj.name = name + "TopCircle"

    bottom_circle_obj.hide_set(True)                       #将圆环隐藏
    middle_circle_obj.hide_set(True)
    top_circle_obj.hide_set(True)

    # create_middle_base_curve()
    createBatteryAndPlane(bottom_center, bottom_rotation)                                #创建电池仓平面和电池仓



def resetCircleInfo():
    '''
    重置切割圆环的位置等信息为初始信息
    '''
    global bottom_prev_radius, middle_prev_radius, top_prev_radius, bottom_min_radius, middle_min_radius, top_min_radius
    global bottom_right_last_loc, bottom_right_last_radius, bottom_right_last_ratation, bottom_left_last_loc, bottom_left_last_radius, bottom_left_last_ratation
    global middle_right_last_loc, middle_right_last_radius, middle_right_last_ratation, middle_left_last_loc, middle_left_last_radius, middle_left_last_ratation
    global top_right_last_loc, top_right_last_radius, top_right_last_ratation, top_left_last_loc, top_left_last_radius, top_left_last_ratation

    bottom_prev_radius = 8.0  # 上次底部圆环切割时的直径(交集平面边缘点距离圆环位置的最大距离加上一个偏移值,用于调整圆环直径)
    bottom_min_radius = 0  # 上次底部圆环切割时的最小直径(交集平面边缘点距离圆环位置的最小距离,用于圆环平面切割后的边缘平滑)
    middle_prev_radius = 6.0
    middle_min_radius = 0
    top_prev_radius = 4.0
    top_min_radius = 0
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        # 切割时的圆环信息（右耳）
        bottom_right_last_loc = None
        bottom_right_last_radius = None
        bottom_right_last_ratation = None
        middle_right_last_loc = None
        middle_right_last_radius = None
        middle_right_last_ratation = None
        top_right_last_loc = None
        top_right_last_radius = None
        top_right_last_ratation = None
    elif name == "左耳":
        # 切割时的圆环信息（左耳）
        bottom_left_last_loc = None
        bottom_left_last_radius = None
        bottom_left_last_ratation = None
        middle_left_last_loc = None
        middle_left_last_radius = None
        middle_left_last_ratation = None
        top_left_last_loc = None
        top_left_last_radius = None
        top_left_last_ratation = None


def saveCirInfo():
    '''
    记录圆环位置和旋转相关信息
    '''

    global bottom_prev_radius, middle_prev_radius, top_prev_radius
    global bottom_right_last_loc, bottom_right_last_radius, bottom_right_last_ratation, bottom_left_last_loc, bottom_left_last_radius, bottom_left_last_ratation
    global middle_right_last_loc, middle_right_last_radius, middle_right_last_ratation, middle_left_last_loc, middle_left_last_radius, middle_left_last_ratation
    global top_right_last_loc, top_right_last_radius, top_right_last_ratation, top_left_last_loc, top_left_last_radius, top_left_last_ratation

    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.context.active_object
    if (active_obj != None):
        if (active_obj.name == name + "TopTorus"):
            obj_torus = bpy.data.objects.get(name + 'TopTorus')
            last_loc = obj_torus.location.copy()
            last_radius = round(top_prev_radius * obj_torus.scale[0], 2)
            last_ratation = obj_torus.rotation_euler.copy()
            if name  == '右耳':
                top_right_last_loc = last_loc
                top_right_last_radius = last_radius
                top_right_last_ratation = last_ratation
            elif name == '左耳':
                top_left_last_loc = last_loc
                top_left_last_radius = last_radius
                top_left_last_ratation = last_ratation
        elif (active_obj.name == name + "MiddleTorus"):
            obj_torus = bpy.data.objects.get(name + 'MiddleTorus')
            last_loc = obj_torus.location.copy()
            last_radius = round(middle_prev_radius * obj_torus.scale[0], 2)
            last_ratation = obj_torus.rotation_euler.copy()
            if name == '右耳':
                middle_right_last_loc = last_loc
                middle_right_last_radius = last_radius
                middle_right_last_ratation = last_ratation
            elif name == '左耳':
                middle_left_last_loc = last_loc
                middle_left_last_radius = last_radius
                middle_left_last_ratation = last_ratation
        elif (active_obj.name == name + "BottomTorus"):
            obj_torus = bpy.data.objects.get(name + 'BottomTorus')
            last_loc = obj_torus.location.copy()
            last_radius = round(bottom_prev_radius * obj_torus.scale[0], 2)
            last_ratation = obj_torus.rotation_euler.copy()
            if name == '右耳':
                bottom_right_last_loc = last_loc
                bottom_right_last_radius = last_radius
                bottom_right_last_ratation = last_ratation
            elif name == '左耳':
                bottom_left_last_loc = last_loc
                bottom_left_last_radius = last_radius
                bottom_left_last_ratation = last_ratation


def reset_after_bottom_curve_change():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name + "shellObjForBottomCurve")
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name + "shellObjForBottomCurveCopy"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.scene.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(False)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    bpy.data.objects.remove(bpy.data.objects.get(name), do_unlink=True)
    duplicate_obj.name = name


def bridge_and_refill():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        offset = bpy.context.scene.mianBanPianYiR
    elif name == '左耳':
        offset = bpy.context.scene.mianBanPianYiL
    if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
        bridge_bottom_curve()
    else:
        lower_circle_cut()
        extrude_and_generate_loft_obj(offset)
        create_bottom_base_curve()

    top_circle_cut()
    shell_bottom_fill()
    top_smooth_success = top_circle_smooth()
    middle_smooth_success = middle_circle_cut()
    join_outer_and_inner(top_smooth_success and middle_smooth_success)
    shell_battery_plane_cut()


def update_smooth_factor():
    reset_after_bottom_curve_change()
    bevel_loft_part()
    top_circle_cut()
    shell_bottom_fill()
    top_smooth_success = top_circle_smooth()
    middle_smooth_success = middle_circle_cut()
    join_outer_and_inner(top_smooth_success and middle_smooth_success)
    shell_battery_plane_cut()


def update_xiafangxian():
    global cut_radius
    global bottom_last_right_offset, bottom_last_left_offset
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        offset = bpy.context.scene.xiaFangYangXianPianYiR
        before_offset = bottom_last_right_offset
        set_right_shell_border([])
    elif name == '左耳':
        offset = bpy.context.scene.xiaFangYangXianPianYiL
        before_offset = bottom_last_left_offset
        set_left_shell_border([])
    if not bpy.data.objects.get(name + "meshBottomRingBorderR").hide_get():
        bpy.data.objects.get(name + "meshBottomRingBorderR").hide_set(True)

    move_distance = offset - before_offset
    cut_circle = bpy.data.objects.get(name + "CutCircle")
    cut_circle.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cut_circle
    cut_circle.select_set(True)
    bpy.ops.transform.translate(value=(0, 0, move_distance), orient_type='LOCAL',
                                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL',
                                constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False,
                                proportional_edit_falloff='SMOOTH', proportional_size=1,
                                use_proportional_connected=False, use_proportional_projected=False, snap=False,
                                snap_elements={'FACE'}, use_snap_project=False, snap_target='CENTER',
                                use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True,
                                use_snap_selectable=False)
    if name == '右耳':
        bottom_last_right_offset = bpy.context.scene.xiaFangYangXianPianYiR
    elif name == '左耳':
        bottom_last_left_offset = bpy.context.scene.xiaFangYangXianPianYiL

    shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")
    intersect_obj = shell_bool_obj.copy()
    intersect_obj.data = shell_bool_obj.data.copy()
    intersect_obj.name = shell_bool_obj.name + "Intersect"
    intersect_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(intersect_obj)
    if name == '右耳':
        moveToRight(intersect_obj)
    elif name == '左耳':
        moveToLeft(intersect_obj)
    bpy.ops.object.select_all(action='DESELECT')
    intersect_obj.select_set(True)
    bpy.context.view_layer.objects.active = intersect_obj
    bool_modifier = intersect_obj.modifiers.new(name="ShellCirCleIntersectBooleanModifier",
                                                type='BOOLEAN')  # 将布尔物体复制出的物体与圆环作差集得到交集平面
    bool_modifier.operation = 'INTERSECT'
    bool_modifier.solver = 'FAST'
    bool_modifier.object = cut_circle
    bpy.ops.object.modifier_apply(modifier="ShellCirCleIntersectBooleanModifier", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    rbm = bmesh.from_edit_mesh(intersect_obj.data)
    circle_plane_normal = cut_circle.matrix_world.to_3x3() @ cut_circle.data.polygons[0].normal
    circle_plane_loc = cut_circle.location.copy()
    plane_verts = [v for v in rbm.verts if round(abs(circle_plane_normal.dot(v.co - circle_plane_loc)),
                                                 4) == 0]  # 获取布尔交集物体中与圆环平行的顶点
    if (len(plane_verts) == 0):
        on_obj = False
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(intersect_obj, do_unlink=True)
    else:
        on_obj = True
    if on_obj:  # 当圆环在模型上与模型有交集时,调整圆环的位置和大小
        for v in plane_verts:
            v.select = True
        for edge in rbm.edges:
            if edge.verts[0].select and edge.verts[1].select:
                edge.select_set(True)
        bpy.ops.mesh.separate(type='SELECTED')  # 根据交集物体复制出一份临时物体主要用于处理当圆环与模型的交集有连个非连通平面时处理圆环中心位于哪个平面交集
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.select_get():
                if obj.name != intersect_obj.name:
                    temp_plane_obj = obj
        if name == "右耳":
            moveToRight(temp_plane_obj)
        elif name == "左耳":
            moveToLeft(temp_plane_obj)
        bpy.context.view_layer.objects.active = temp_plane_obj
        intersect_obj.select_set(False)
        temp_plane_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(temp_plane_obj.data)
        verts = [v for v in bm.verts]
        verts[0].select = True
        bpy.ops.mesh.select_linked(delimit=set())
        select_verts = [v for v in bm.verts if v.select]  # 选中交集平面中第一个连通区域
        unselect_verts = [v for v in bm.verts if not v.select]  # 交集平面中剩余连通区域

        if len(select_verts) == len(verts):  # 只存在一个交集平面
            max_distance = float('-inf')
            min_distance = float('inf')
            for vertex in verts:
                distance = (vertex.co - cut_circle.location).length
                max_distance = max(max_distance, distance)
                min_distance = min(min_distance, distance)
            cut_radius = round(max_distance, 2) + 0.5

        else:  # 有两个交集平面
            bottom_circle = bpy.data.objects.get(name + "BottomCircle")
            center1 = sum((v.co for v in select_verts), Vector()) / len(select_verts)
            center2 = sum((v.co for v in unselect_verts), Vector()) / len(unselect_verts)
            if (bottom_circle.location - center1).length < (bottom_circle.location - center2).length:
                verts = select_verts
                bpy.ops.mesh.select_all(action='DESELECT')
                for v in unselect_verts:
                    v.select = True
                bpy.ops.mesh.delete(type='VERT')
            else:
                verts = unselect_verts
                bpy.ops.mesh.delete(type='VERT')
            max_distance = float('-inf')
            min_distance = float('inf')
            for vertex in verts:
                distance = (vertex.co - cut_circle.location).length
                max_distance = max(max_distance, distance)
                min_distance = min(min_distance, distance)
            cut_radius = round(max_distance, 2) + 0.5
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.convert(target='CURVE')
        if bpy.data.objects.get(name + "BottomRingBorderR") != None:
            bpy.data.objects.remove(bpy.data.objects.get(name + "BottomRingBorderR"), do_unlink=True)
        temp_plane_obj.name = name + "BottomRingBorderR"
        temp_plane_obj.data.bevel_depth = 0.18
        temp_plane_obj.data.materials.append(bpy.data.materials['blue'])
        bpy.data.objects.remove(intersect_obj, do_unlink=True)
        cut_circle.hide_set(True)
        update_plane_and_curve()


def update_mianban():
    global plane_last_right_offset, plane_last_left_offset
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        offset = bpy.context.scene.mianBanPianYiR
        before_offset = plane_last_right_offset
    elif name == '左耳':
        offset = bpy.context.scene.mianBanPianYiL
        before_offset = plane_last_left_offset

    if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
        if not bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_get():
            bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_set(True)

    move_distance = offset - before_offset
    battery_obj = bpy.data.objects.get(name + "shellBattery")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = battery_obj
    battery_obj.select_set(True)
    bpy.ops.transform.translate(value=(0, 0, -move_distance), orient_type='LOCAL',
                                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='LOCAL',
                                constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False,
                                proportional_edit_falloff='SMOOTH', proportional_size=1,
                                use_proportional_connected=False, use_proportional_projected=False, snap=False,
                                snap_elements={'FACE'}, use_snap_project=False, snap_target='CENTER',
                                use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True,
                                use_snap_selectable=False)
    if name == '右耳':
        plane_last_right_offset = bpy.context.scene.mianBanPianYiR
    elif name == '左耳':
        plane_last_left_offset = bpy.context.scene.mianBanPianYiL

    bpy.context.object.constraints["Limit Location"].max_z = -(0.58 + offset)
    bpy.context.object.constraints["Limit Location"].min_z = -(0.58 + offset)
    create_bottom_base_curve()
    update_plane_and_curve()


def update_plane_and_curve():
    name = bpy.context.scene.leftWindowObj
    if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
        if bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_get():
            curve_obj = bpy.data.objects.get(name + "PlaneBorderCurve")
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = curve_obj
            curve_obj.select_set(True)
            bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True,
                                           isolate_users=True)
            convert_to_mesh(name + "PlaneBorderCurve", name + "meshPlaneBorderCurve", 0.18)
            battery_obj = bpy.data.objects.get(name + "shellBattery")
            child_of_constraint = curve_obj.constraints.new(type='CHILD_OF')
            child_of_constraint.target = battery_obj

            plane_obj = bpy.data.objects.get(name + "batteryPlaneSnapCurve")
            bpy.ops.object.select_all(action='DESELECT')
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True,
                                           isolate_users=True)
            child_of_constraint = plane_obj.constraints.new(type='CHILD_OF')
            child_of_constraint.target = battery_obj
            bpy.ops.object.select_all(action='DESELECT')
            battery_obj.select_set(True)
            bpy.context.view_layer.objects.active = battery_obj

    else:
        plane_obj = bpy.data.objects.get(name + "batteryPlaneSnapCurve")
        bpy.ops.object.select_all(action='DESELECT')
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True,
                                       isolate_users=True)
        child_of_constraint = plane_obj.constraints.new(type='CHILD_OF')
        battery_obj = bpy.data.objects.get(name + "shellBattery")
        child_of_constraint.target = battery_obj
        bpy.ops.object.select_all(action='DESELECT')
        battery_obj.select_set(True)
        bpy.context.view_layer.objects.active = battery_obj


    if bpy.data.objects.get(name + "meshBottomRingBorderR") != None:
        if bpy.data.objects.get(name + "meshBottomRingBorderR").hide_get():
            cut_circle = bpy.data.objects.get(name + "CutCircle")
            global cut_radius
            bpy.ops.mesh.primitive_circle_add(
                vertices=32, radius=cut_radius, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                align='WORLD', location=cut_circle.location,
                rotation=cut_circle.rotation_euler,
                scale=(1.0, 1.0, 1.0))
            circle = bpy.context.active_object
            circle.name = name + "CutCircleFit"
            normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
            if normal.z < 0:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.flip_normals()
                bpy.ops.object.mode_set(mode='OBJECT')

            shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")  # 根据布尔物体复制一份用于切割
            replace_obj = bpy.data.objects.get(name + "ShellBoolObjCopy")
            if (replace_obj != None):
                bpy.data.objects.remove(replace_obj, do_unlink=True)
            replace_obj = shell_bool_obj.copy()
            replace_obj.data = shell_bool_obj.data.copy()
            replace_obj.name = shell_bool_obj.name + "Copy"
            replace_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(replace_obj)
            if name == '右耳':
                moveToRight(replace_obj)
            elif name == '左耳':
                moveToLeft(replace_obj)
            bpy.ops.object.select_all(action='DESELECT')
            replace_obj.select_set(True)
            bpy.context.view_layer.objects.active = replace_obj
            try:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                replace_obj.vertex_groups.new(name="all")
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')
                circle.select_set(True)
                bpy.ops.object.booltool_auto_difference()
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group='all')
                # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
                bpy.ops.object.vertex_group_remove_from()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.select_all(action='INVERT')
                # 用于上下桥接的顶点组，只包含当前孔边界
                replace_obj.vertex_groups.new(name="BottomOuterBorderVertex")
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')
                delete_vert_group("all")
                delete_lower_part(group_name="BottomOuterBorderVertex")
                bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
                replace_obj.name = name
                copy_model_for_bottom_curve()
                resample_curve(160, name + "BottomRingBorderR")
                convert_to_mesh(name + "BottomRingBorderR", name + "meshBottomRingBorderR", 0.18)
                bridge_and_refill()
            except:
                if bpy.data.objects.get(name + "CutCircleFit"):
                    bpy.data.objects.remove(bpy.data.objects[name + "CutCircleFit"], do_unlink=True)
                if bpy.data.objects.get(name + "ShellBoolObjCopy"):
                    bpy.data.objects.remove(bpy.data.objects[name + "ShellBoolObjCopy"], do_unlink=True)
                shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")   # 获得原始物体
                origin_obj = bpy.data.objects.get(name + "ShellBoolObjOrigin")
                if (origin_obj != None):
                    bpy.data.objects.remove(origin_obj, do_unlink=True)
                origin_obj = shell_bool_obj.copy()
                origin_obj.data = shell_bool_obj.data.copy()
                origin_obj.name = shell_bool_obj.name + "Origin"
                origin_obj.animation_data_clear()
                bpy.context.scene.collection.objects.link(origin_obj)
                if name == '右耳':
                    moveToRight(origin_obj)
                elif name == '左耳':
                    moveToLeft(origin_obj)
                bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
                bpy.ops.object.select_all(action='DESELECT')
                origin_obj.select_set(True)
                bpy.context.view_layer.objects.active = origin_obj
                origin_obj.name = name
                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                origin_obj.data.materials.clear()
                origin_obj.data.materials.append(bpy.data.materials["error_yellow"])

        else:
            reset_after_bottom_curve_change()
            bridge_and_refill()


def createBatteryAndPlane(loc, rot):
    '''
    导入stl文件生成电池仓平面和电池
    '''
    global plane_last_right_offset, plane_last_left_offset
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        offset = bpy.context.scene.mianBanPianYiR
        plane_last_right_offset = offset
    elif name == '左耳':
        offset = bpy.context.scene.mianBanPianYiL
        plane_last_left_offset = offset

    bpy.ops.object.select_all(action='DESELECT')
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    relative_path = os.path.join(script_dir, "stl\\battery.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    battery_name = "battery"
    battery_obj = bpy.data.objects.get(battery_name)
    battery_obj.name = name + "shellBattery"
    newColor('shellBatteryGrey', 0.8, 0.8, 0.8, 0, 1)
    battery_obj.data.materials.clear()
    battery_obj.data.materials.append(bpy.data.materials["shellBatteryGrey"])
    battery_obj.location = (loc[0], loc[1], loc[2]  - 0.58 - offset)
    battery_obj.rotation_euler = rot

    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    relative_path = os.path.join(script_dir, "stl\\batteryPlane.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    battery_plane_name = "batteryPlane"
    battery_plane_obj = bpy.data.objects.get(battery_plane_name)
    battery_plane_obj.name = name + "shellBatteryPlane"
    newColor('shellBatteryPlaneYellow', 1, 0.319, 0.133, 1, 0.01)
    battery_plane_obj.data.materials.clear()
    battery_plane_obj.data.materials.append(bpy.data.materials["shellBatteryPlaneYellow"])
    battery_plane_obj.location = (loc[0], loc[1], loc[2] - 0.58 - offset)
    battery_plane_obj.rotation_euler = rot

    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    relative_path = os.path.join(script_dir, "stl\\batteryPlaneSnapCurve.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    battery_plane_snap_curve_name = "batteryPlaneSnapCurve"
    battery_plane_snap_curve_obj = bpy.data.objects.get(battery_plane_snap_curve_name)
    battery_plane_snap_curve_obj.name = name + "batteryPlaneSnapCurve"
    newColor('batteryPlaneSnapCurveYellow', 1, 0.319, 0.133, 1, 0.01)
    battery_plane_snap_curve_obj.data.materials.clear()
    battery_plane_snap_curve_obj.data.materials.append(bpy.data.materials["batteryPlaneSnapCurveYellow"])
    battery_plane_snap_curve_obj.location = (loc[0], loc[1], loc[2] - 0.58 * 2 - offset)
    battery_plane_snap_curve_obj.rotation_euler = rot
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)
    if (name == "右耳"):
        moveToRight(battery_obj)
        moveToRight(battery_plane_obj)
        moveToRight(battery_plane_snap_curve_obj)
    elif (name == "左耳"):
        moveToLeft(battery_obj)
        moveToLeft(battery_plane_obj)
        moveToLeft(battery_plane_snap_curve_obj)


    child_of_constraint = battery_plane_obj.constraints.new(type='CHILD_OF')             # 为电池仓平面添加子集约束,设置为为电池的子物体
    child_of_constraint.target = battery_obj
    child_of_constraint = battery_plane_snap_curve_obj.constraints.new(type='CHILD_OF')  # 为用于切割蓝线吸附的电池仓平面添加子集约束,设置为为电池的子物体
    child_of_constraint.target = battery_obj


    obj_circle = bpy.data.objects.get(name + 'BottomCircle')                     # 为电池仓添加位置约束,使得电池只能在底部圆环平面移动
    bpy.ops.object.select_all(action='DESELECT')
    obj_circle.select_set(True)
    bpy.context.view_layer.objects.active = obj_circle
    obj_circle.hide_set(False)
    bpy.ops.transform.create_orientation(name="shellBottomCircle", use=False, overwrite=True)
    obj_circle.hide_set(True)

    limit_location_constraint = battery_obj.constraints.new(type='LIMIT_LOCATION')
    limit_location_constraint.use_min_z = True
    limit_location_constraint.min_z = -(0.58 + offset)
    limit_location_constraint.use_max_z = True
    limit_location_constraint.max_z = -(0.58 + offset)
    limit_location_constraint.owner_space = 'CUSTOM'
    limit_location_constraint.space_object = obj_circle
    create_bottom_curve(loc, rot)    # 生成底部蓝线


def create_bottom_curve(loc, rot):
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        offset = bpy.context.scene.mianBanPianYiR
        plane_shell_border = get_right_shell_plane_border()
    elif name == '左耳':
        offset = bpy.context.scene.mianBanPianYiL
        plane_shell_border = get_left_shell_plane_border()
    if len(plane_shell_border) == 0:
        # TODO: 底部蓝线的初始样式
        lower_circle_cut()
        extrude_and_generate_loft_obj(offset)
        create_bottom_base_curve()
        # 生成圆环作为底部蓝线
        # bpy.ops.mesh.primitive_circle_add(vertices=32, radius=8, enter_editmode=False, align='WORLD',
        #                                   location=(loc[0], loc[1], loc[2] - 0.58 * 2 - offset),
        #                                   rotation= rot,
        #                                   scale=(1, 1, 1))
        # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)
        # curve_obj = bpy.context.active_object
        # curve_obj.name = name + "PlaneBorderCurve"
        # if name == '右耳':
        #     moveToRight(curve_obj)
        # elif name == '左耳':
        #     moveToLeft(curve_obj)
        # bpy.ops.object.convert(target='CURVE')
        # curve_obj.data.bevel_depth = 0.18

        # 根据圆环进行切割, 将切割的边界作为底部蓝线
        # bpy.ops.mesh.primitive_circle_add(vertices=32, radius=25, enter_editmode=False, align='WORLD', fill_type='NGON',
        #                                   location=(loc[0], loc[1], loc[2] - 0.58 * 2 - offset),
        #                                   rotation= rot,
        #                                   scale=(1, 1, 1))
        #
        # cut_circle = bpy.context.active_object
        # shell_bool_obj = bpy.data.objects.get(name + "OriginForCreateMouldR")
        # intersect_obj = shell_bool_obj.copy()
        # intersect_obj.data = shell_bool_obj.data.copy()
        # intersect_obj.name = shell_bool_obj.name + "OriginForCreateMouldRCopy"
        # intersect_obj.animation_data_clear()
        # bpy.context.scene.collection.objects.link(intersect_obj)
        # if name == '右耳':
        #     moveToRight(intersect_obj)
        # elif name == '左耳':
        #     moveToLeft(intersect_obj)
        # bpy.ops.object.select_all(action='DESELECT')
        # intersect_obj.select_set(True)
        # bpy.context.view_layer.objects.active = intersect_obj
        # bool_modifier = intersect_obj.modifiers.new(name="ShellCirCleIntersectBooleanModifier",
        #                                             type='BOOLEAN')  # 将布尔物体复制出的物体与圆环作差集得到交集平面
        # bool_modifier.operation = 'INTERSECT'
        # bool_modifier.solver = 'FAST'
        # bool_modifier.object = cut_circle
        # bpy.ops.object.modifier_apply(modifier="ShellCirCleIntersectBooleanModifier", single_user=True)
        #
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='DESELECT')
        # rbm = bmesh.from_edit_mesh(intersect_obj.data)
        # circle_plane_normal = cut_circle.matrix_world.to_3x3() @ cut_circle.data.polygons[0].normal
        # circle_plane_loc = cut_circle.location.copy()
        # plane_verts = [v for v in rbm.verts if round(abs(circle_plane_normal.dot(v.co - circle_plane_loc)),
        #                                              4) == 0]  # 获取布尔交集物体中与圆环平行的顶点
        # if (len(plane_verts) == 0):
        #     on_obj = False
        #     bpy.ops.object.mode_set(mode='OBJECT')
        #     bpy.data.objects.remove(intersect_obj, do_unlink=True)
        # else:
        #     on_obj = True
        # if on_obj:  # 当圆环在模型上与模型有交集时,调整圆环的位置和大小
        #     for v in plane_verts:
        #         v.select = True
        #     for edge in rbm.edges:
        #         if edge.verts[0].select and edge.verts[1].select:
        #             edge.select_set(True)
        #     bpy.ops.mesh.separate(type='SELECTED')  # 根据交集物体复制出一份临时物体主要用于处理当圆环与模型的交集有连个非连通平面时处理圆环中心位于哪个平面交集
        #     bpy.ops.object.mode_set(mode='OBJECT')
        #     for obj in bpy.data.objects:
        #         if obj.select_get():
        #             if obj.name != intersect_obj.name:
        #                 curve_obj = obj
        #     if name == "右耳":
        #         moveToRight(curve_obj)
        #     elif name == "左耳":
        #         moveToLeft(curve_obj)
        #     bpy.context.view_layer.objects.active = curve_obj
        #     intersect_obj.select_set(False)
        #     curve_obj.select_set(True)
        #     bpy.ops.object.mode_set(mode='EDIT')
        #     bpy.ops.mesh.select_all(action='DESELECT')
        #     bm = bmesh.from_edit_mesh(curve_obj.data)
        #     verts = [v for v in bm.verts]
        #     verts[0].select = True
        #     bpy.ops.mesh.select_linked(delimit=set())
        #     select_verts = [v for v in bm.verts if v.select]  # 选中交集平面中第一个连通区域
        #     unselect_verts = [v for v in bm.verts if not v.select]  # 交集平面中剩余连通区域
        #
        #     if len(select_verts) == len(verts):  # 只存在一个交集平面
        #        pass
        #
        #     else:  # 有两个交集平面
        #         bottom_circle = bpy.data.objects.get(name + "BottomCircle")
        #         center1 = sum((v.co for v in select_verts), Vector()) / len(select_verts)
        #         center2 = sum((v.co for v in unselect_verts), Vector()) / len(unselect_verts)
        #         if (bottom_circle.location - center1).length < (bottom_circle.location - center2).length:
        #             bpy.ops.mesh.select_all(action='DESELECT')
        #             for v in unselect_verts:
        #                 v.select = True
        #             bpy.ops.mesh.delete(type='VERT')
        #         else:
        #             bpy.ops.mesh.delete(type='VERT')
        #
        #     bpy.ops.mesh.select_all(action='SELECT')
        #     # 根据底部蓝线向里走一段距离
        #     bpy.ops.mesh.duplicate()
        #     # bpy.ops.mesh.offset_edges(geometry_mode='move', width=-2, follow_face=True, caches_valid=False)
        #     select_verts = [v for v in bm.verts if v.select]
        #     center = sum((v.co for v in select_verts), Vector()) / len(select_verts)
        #     for v in select_verts:
        #         v.co -= (v.co - center) * 0.25
        #     bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
        #
        #     # 根据外轮廓生成底部蓝线的初始坐标
        #     # select_verts = [v.co[0:3] for v in bm.verts if v.select]
        #     # border_co = convex_hull(select_verts)
        #     # order_border_co = utils_get_order_border_vert(border_co)
        #     # center = sum((Vector(co) for co in order_border_co), Vector()) / len(order_border_co)
        #     # scale_co = []
        #     # for co in order_border_co:
        #     #     scale_vector = Vector(co) - (Vector(co) - center) * 0.25
        #     #     scale_co.append(scale_vector[0:3])
        #
        #     # 分离出切割边界作为基准蓝线
        #     bpy.ops.mesh.select_all(action='INVERT')
        #     bpy.ops.mesh.separate(type='SELECTED')
        #     bpy.ops.object.mode_set(mode='OBJECT')
        #     bpy.data.objects.remove(intersect_obj, do_unlink=True)
        #     bpy.data.objects.remove(cut_circle, do_unlink=True)
        #
        #     for o in bpy.data.objects:
        #         if o.select_get():
        #             if o.name != curve_obj.name:
        #                 bottom_base_curve = o
        #     bpy.ops.object.select_all(action='DESELECT')
        #     bottom_base_curve.select_set(True)
        #     bpy.context.view_layer.objects.active = bottom_base_curve
        #     bottom_base_curve.name = name + "BottomBaseCurve"
        #     bpy.ops.object.convert(target='CURVE')
        #     bottom_base_curve.hide_set(True)
        #
        #     # utils_draw_curve(scale_co, name + "PlaneBorderCurve", 0.18)
        #     # curve_obj = bpy.data.objects.get(name + "PlaneBorderCurve")
        #     bpy.ops.object.select_all(action='DESELECT')
        #     curve_obj.select_set(True)
        #     bpy.context.view_layer.objects.active = curve_obj
        #     bpy.ops.object.convert(target='CURVE')
        #     curve_obj.name = name + "PlaneBorderCurve"
        #     resample_curve(100, name + "PlaneBorderCurve")

    else:
        utils_draw_curve(plane_shell_border, name + "PlaneBorderCurve", 0.18)
        curve_obj = bpy.data.objects.get(name + "PlaneBorderCurve")
        curve_obj.data.materials.clear()
        mat = newColor('blue', 0, 0, 1, 1, 1)
        curve_obj.data.materials.append(mat)

        convert_to_mesh(name + "PlaneBorderCurve", name + "meshPlaneBorderCurve", 0.18)
        battery_obj = bpy.data.objects.get(name + "shellBattery")
        child_of_constraint = curve_obj.constraints.new(type='CHILD_OF')  # 设置为为电池的子物体
        child_of_constraint.target = battery_obj
        bridge_bottom_curve()                            # 桥接两个蓝线之间的面


def copy_curve_and_resample(curve_name, resample_number, vertex_group_name):
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(curve_name)
    curve_obj = obj.copy()
    curve_obj.data = obj.data.copy()
    curve_obj.animation_data_clear()
    curve_obj.name = curve_name + "Copy"
    curve_obj.hide_set(False)
    bpy.context.collection.objects.link(curve_obj)

    if (name == "右耳"):
        moveToRight(curve_obj)
    elif (name == "左耳"):
        moveToLeft(curve_obj)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = curve_obj
    curve_obj.select_set(True)
    curve_obj.data.bevel_depth = 0

    modifier = curve_obj.modifiers.new(name="Resample", type='NODES')
    bpy.ops.node.new_geometry_node_group_assign()
    node_tree = bpy.data.node_groups[0]
    node_links = node_tree.links
    input_node = node_tree.nodes[0]
    output_node = node_tree.nodes[1]
    resample_node = node_tree.nodes.new("GeometryNodeResampleCurve")
    resample_node.inputs[2].default_value = resample_number
    node_links.new(input_node.outputs[0], resample_node.inputs[0])
    node_links.new(resample_node.outputs[0], output_node.inputs[0])
    bpy.ops.object.convert(target='MESH')
    bpy.data.node_groups.remove(node_tree)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(curve_obj.data)

    bpy.ops.mesh.select_all(action='SELECT')
    curve_obj.vertex_groups.new(name=vertex_group_name)
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')
    return curve_obj


def create_middle_base_curve():
    name = bpy.context.scene.leftWindowObj
    bottom_circle = bpy.data.objects.get(name + "BottomCircle")
    bottom_circle.hide_set(False)

    shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")
    intersect_obj = shell_bool_obj.copy()
    intersect_obj.data = shell_bool_obj.data.copy()
    intersect_obj.name = shell_bool_obj.name + "Intersect"
    intersect_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(intersect_obj)
    if name == '右耳':
        moveToRight(intersect_obj)
    elif name == '左耳':
        moveToLeft(intersect_obj)
    bpy.ops.object.select_all(action='DESELECT')
    intersect_obj.select_set(True)
    bpy.context.view_layer.objects.active = intersect_obj
    bool_modifier = intersect_obj.modifiers.new(name="ShellCirCleIntersectBooleanModifier",
                                                type='BOOLEAN')  # 将布尔物体复制出的物体与圆环作差集得到交集平面
    bool_modifier.operation = 'INTERSECT'
    bool_modifier.solver = 'FAST'
    bool_modifier.object = bottom_circle
    bpy.ops.object.modifier_apply(modifier="ShellCirCleIntersectBooleanModifier", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    rbm = bmesh.from_edit_mesh(intersect_obj.data)
    circle_plane_normal = bottom_circle.matrix_world.to_3x3() @ bottom_circle.data.polygons[0].normal
    circle_plane_loc = bottom_circle.location.copy()
    plane_verts = [v for v in rbm.verts if round(abs(circle_plane_normal.dot(v.co - circle_plane_loc)),
                                                 4) == 0]  # 获取布尔交集物体中与圆环平行的顶点
    if (len(plane_verts) == 0):
        on_obj = False
        bpy.ops.object.mode_set(mode='OBJECT')
        bottom_circle.hide_set(True)
        bpy.data.objects.remove(intersect_obj, do_unlink=True)
    else:
        on_obj = True
    if on_obj:  # 当圆环在模型上与模型有交集时,调整圆环的位置和大小
        for v in plane_verts:
            v.select = True
        for edge in rbm.edges:
            if edge.verts[0].select and edge.verts[1].select:
                edge.select_set(True)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.select_get():
                if obj.name != intersect_obj.name:
                    temp_plane_obj = obj
        if name == "右耳":
            moveToRight(temp_plane_obj)
        elif name == "左耳":
            moveToLeft(temp_plane_obj)

        if bpy.data.objects.get(name + "MiddleBaseCurve") != None:
            bpy.data.objects.remove(bpy.data.objects.get(name + "MiddleBaseCurve"), do_unlink=True)
        temp_plane_obj.name = name + "MiddleBaseCurve"
        bpy.context.view_layer.objects.active = temp_plane_obj
        intersect_obj.select_set(False)
        bpy.data.objects.remove(intersect_obj, do_unlink=True)
        temp_plane_obj.select_set(True)
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.delete(type='FACE')
        # bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target='CURVE')
        temp_plane_obj.hide_set(True)
        bottom_circle.hide_set(True)


def create_bottom_base_curve():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        offset = bpy.context.scene.mianBanPianYiR
    elif name == '左耳':
        offset = bpy.context.scene.mianBanPianYiL
    bottom_circle = bpy.data.objects.get(name + "BottomCircle")
    loc = bottom_circle.location
    rot = bottom_circle.rotation_euler
    # 根据圆环进行切割, 将切割的边界作为底部蓝线
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=25, enter_editmode=False, align='WORLD', fill_type='NGON',
                                      location=(loc[0], loc[1], loc[2] - 0.58 * 2 - offset),
                                      rotation=rot,
                                      scale=(1, 1, 1))

    circle = bpy.context.active_object
    shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")
    intersect_obj = shell_bool_obj.copy()
    intersect_obj.data = shell_bool_obj.data.copy()
    intersect_obj.name = shell_bool_obj.name + "Intersect"
    intersect_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(intersect_obj)
    if name == '右耳':
        moveToRight(intersect_obj)
    elif name == '左耳':
        moveToLeft(intersect_obj)
    bpy.ops.object.select_all(action='DESELECT')
    intersect_obj.select_set(True)
    bpy.context.view_layer.objects.active = intersect_obj
    bool_modifier = intersect_obj.modifiers.new(name="ShellCirCleIntersectBooleanModifier",
                                                type='BOOLEAN')  # 将布尔物体复制出的物体与圆环作差集得到交集平面
    bool_modifier.operation = 'INTERSECT'
    bool_modifier.solver = 'FAST'
    bool_modifier.object = circle
    bpy.ops.object.modifier_apply(modifier="ShellCirCleIntersectBooleanModifier", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    rbm = bmesh.from_edit_mesh(intersect_obj.data)
    circle_plane_normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
    circle_plane_loc = circle.location.copy()
    plane_verts = [v for v in rbm.verts if round(abs(circle_plane_normal.dot(v.co - circle_plane_loc)),
                                                 4) == 0]  # 获取布尔交集物体中与圆环平行的顶点

    if (len(plane_verts) == 0):
        on_obj = False
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(circle, do_unlink=True)
        bpy.data.objects.remove(intersect_obj, do_unlink=True)
    else:
        on_obj = True
    if on_obj:  # 当圆环在模型上与模型有交集时,调整圆环的位置和大小
        for v in plane_verts:
            v.select = True
        for edge in rbm.edges:
            if edge.verts[0].select and edge.verts[1].select:
                edge.select_set(True)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in bpy.data.objects:
            if obj.select_get():
                if obj.name != intersect_obj.name:
                    temp_plane_obj = obj
        if name == "右耳":
            moveToRight(temp_plane_obj)
        elif name == "左耳":
            moveToLeft(temp_plane_obj)

        if bpy.data.objects.get(name + "BottomBaseCurve") != None:
            bpy.data.objects.remove(bpy.data.objects.get(name + "BottomBaseCurve"), do_unlink=True)
        temp_plane_obj.name = name + "BottomBaseCurve"
        bpy.context.view_layer.objects.active = temp_plane_obj
        intersect_obj.select_set(False)
        bpy.data.objects.remove(intersect_obj, do_unlink=True)
        bpy.data.objects.remove(circle, do_unlink=True)
        temp_plane_obj.select_set(True)
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.delete(type='FACE')
        # bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target='CURVE')
        temp_plane_obj.hide_set(True)


def extrude_and_generate_loft_obj(offset):
    name = bpy.context.scene.leftWindowObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, - offset - 0.58 * 2),
                                                             "orient_type": 'LOCAL'})
    bpy.ops.object.vertex_group_remove_from()
    bpy.context.active_object.vertex_groups.new(name="ExtrudeVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_more()

    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != name:
                loft_obj = obj
    if name == "右耳":
        moveToRight(loft_obj)
    elif name == "左耳":
        moveToLeft(loft_obj)

    if bpy.data.objects.get(name + "shellLoftObj") != None:
        bpy.data.objects.remove(bpy.data.objects.get(name + "shellLoftObj"), do_unlink=True)
    loft_obj.name = name + "shellLoftObj"
    bpy.data.objects.get(name).select_set(False)
    loft_obj.select_set(True)
    bpy.context.view_layer.objects.active = loft_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.subdivide(number_cuts=int(offset / 0.2))
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.object.vertex_group_set_active(group='ExtrudeVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_remove()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='ExtrudeVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_remove()
    bm = bmesh.from_edit_mesh(loft_obj.data)
    verts_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group('BottomOuterCurveVertex', verts_index)
    loft_obj.hide_set(True)

    copy_model_for_top_circle_cut()


def bridge_bottom_curve():
    name = bpy.context.scene.leftWindowObj
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bm = bmesh.from_edit_mesh(bpy.data.objects.get(name).data)
    resample_number = len([v for v in bm.verts if v.select])
    bpy.ops.object.mode_set(mode='OBJECT')

    plane_curve = copy_curve_and_resample(name + "PlaneBorderCurve", resample_number, "BottomOuterCurveVertex")
    middle_curve = copy_curve_and_resample(name + "MiddleBaseCurve", resample_number, "MiddleCurveVertex")
    bottom_curve = copy_curve_and_resample(name + "BottomBaseCurve", resample_number, "BottomCurveVertex")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)
    plane_curve.select_set(True)
    middle_curve.select_set(True)
    bottom_curve.select_set(True)
    bpy.ops.object.join()

    # 首先根据两条蓝线桥接，并根据红环的位置切割出中间的用于收缩或扩大的循环边
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.data.objects.get(name).vertex_groups.new(name="LoftVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    circle = bpy.data.objects.get(name + "BottomCircle")
    bpy.ops.mesh.bisect(plane_co=circle.location,
                        plane_no=circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal)
    bpy.data.objects.get(name).vertex_groups.new(name="BridgeMiddleCurveVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_more()
    bpy.data.objects.get(name).vertex_groups.new(name="OriginBridgeVertex")
    bpy.ops.object.vertex_group_assign()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BridgeMiddleCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='MiddleCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='LoftVertex')
    bpy.ops.object.vertex_group_select()
    # 分离出一份物体用于调整平滑度
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != name:
                loft_obj = obj
    if name == "右耳":
        moveToRight(loft_obj)
    elif name == "左耳":
        moveToLeft(loft_obj)
    if bpy.data.objects.get(name + "LoftObjForSmooth") != None:
        bpy.data.objects.remove(bpy.data.objects.get(name + "LoftObjForSmooth"), do_unlink=True)
    loft_obj.name = name + "LoftObjForSmooth"
    loft_obj.hide_set(True)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)

    # 根据参数对桥接部分进行倒角平滑
    bevel_loft_part()

    # 细分桥接出的部分并向外挤出
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # offset = mianban_offset + xiaFangYangXian_offset
    # subdivide_number = int(offset/0.2)
    # bpy.ops.mesh.bridge_edge_loops(number_cuts=subdivide_number, interpolation='LINEAR')
    # # bpy.ops.mesh.bridge_edge_loops(number_cuts=subdivide_number, interpolation='SURFACE',smoothness=xiaSheRuYinZi / 100,
    # #                                profile_shape_factor=0)
    # smooth_vertex(subdivide_number)
    # copy_model_for_top_circle_cut()


def smooth_vertex(subdivide_number):
    name = bpy.context.scene.leftWindowObj
    main_obj = bpy.data.objects.get(name)
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != name:
                loft_obj = obj
    bpy.context.view_layer.objects.active = loft_obj
    loft_obj.select_set(True)
    main_obj.select_set(False)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.select_mode(type='EDGE')
    # bpy.ops.mesh.region_to_loop()
    # bpy.ops.mesh.select_all(action='INVERT')
    # bpy.ops.mesh.subdivide(number_cuts=6, ngon=False, quadcorner='INNERVERT')
    # bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.object.vertex_group_set_active(group='SmoothVertex')
    # bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='SELECT')
    extrude_vertex(subdivide_number)
    bpy.ops.mesh.vertices_smooth(factor=1, repeat=5)
    bpy.ops.object.mode_set(mode='OBJECT')
    copy_loft_obj_for_battery_plane_cut(loft_obj)

    # 合并回原物体
    loft_obj.select_set(False)
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    loft_obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def extrude_vertex(subdivide_number):
    prev_vertex_index = []  # 记录选中内圈时已经选中过的顶点
    new_vertex_index = []  # 记录新选中的内圈顶点,当无新选中的内圈顶点时,说明底部平面的所有内圈顶点都已经被选中的,结束循环
    cur_vertex_index = []  # 记录扩散区域后当前选中的顶点
    inner_circle_index = -1  # 判断当前选中顶点的圈数,根据圈数确定往里走的距离
    index_normal_dict = dict()  # 由于移动一圈顶点后，剩下的顶点的法向会变，导致突出方向出现问题，所以需要存一下初始的方向

    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for vert in bm.verts:
        if vert.select:
            index_normal_dict[vert.index] = vert.normal[0:3]

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    for vert in bm.verts:
        if vert.select:
            prev_vertex_index.append(vert.index)

    # 初始化集合使得其能够进入while循环
    new_vertex_index.append(0)
    while len(new_vertex_index) != 0 and inner_circle_index <= subdivide_number - 2:
        inner_circle_index += 1
        # 根据当前选中顶点扩散得到新选中的顶点
        bpy.ops.mesh.select_more()
        # 根据之前记录的选中顶点数组将之前顶点取消选中,使得只有新增的内圈顶点被选中
        cur_vertex_index.clear()
        cur_vertex_index = [vert.index for vert in bm.verts if vert.select]
        bpy.ops.mesh.select_all(action='DESELECT')
        result = [x for x in cur_vertex_index if x not in prev_vertex_index]
        # 将集合new_vertex_index_set清空并将新选中的内圈顶点保存到集合中
        new_vertex_index.clear()
        new_vertex_index = result

        # 假设底部细分参数为6,中间有6圈,则第0,1,2,3圈step依次增加,第4,5圈再依次降低
        if inner_circle_index <= int(subdivide_number/2):
            step = (1 - 0.9 ** (inner_circle_index + 1)) * 3
        else:
            step = (1 - 0.9 ** (2 * int(subdivide_number/2) + 1 - inner_circle_index)) * 3
        # 根据面板参数设置偏移值
        for vert_index in new_vertex_index:
            dir = index_normal_dict[vert_index]
            vert = bm.verts[vert_index]
            vert.select_set(True)
            vert.co[0] += dir[0] * step
            vert.co[1] += dir[1] * step
            vert.co[2] += dir[2] * step
        # 更新集合prev_vertex_index_set
        prev_vertex_index.extend(new_vertex_index)


def bevel_loft_part():
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        xiaFangYangXian_offset = bpy.context.scene.xiaFangYangXianPianYiR
        mianban_offset = bpy.context.scene.mianBanPianYiR
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiR
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiR
    elif (name == "左耳"):
        xiaFangYangXian_offset = bpy.context.scene.xiaFangYangXianPianYiL
        mianban_offset = bpy.context.scene.mianBanPianYiL
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiL
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiL

    origin_loft_obj = bpy.data.objects.get(name + "LoftObjForSmooth")
    if origin_loft_obj:
        smooth_loft_obj = origin_loft_obj.copy()
        smooth_loft_obj.data = origin_loft_obj.data.copy()
        smooth_loft_obj.name = origin_loft_obj.name + "Copy"
        smooth_loft_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(smooth_loft_obj)
        if name == '右耳':
            moveToRight(smooth_loft_obj)
        else:
            moveToLeft(smooth_loft_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = smooth_loft_obj
        smooth_loft_obj.hide_set(False)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(smooth_loft_obj.data)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='OriginBridgeVertex')
        bpy.ops.object.vertex_group_select()
        verts = [v.index for v in bm.verts if v.select]
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BridgeMiddleCurveVertex')
        bpy.ops.object.vertex_group_select()
        selected_verts = [v for v in bm.verts if v.select]
        for v in selected_verts:
            for edge in v.link_edges:
                if edge.other_vert(v) not in verts:
                    other_vert = edge.other_vert(v)
                    v.co += (other_vert.co - v.co) * xiaSheRuYinZi / 100

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
        bpy.ops.object.vertex_group_select()
        selected_verts = [v for v in bm.verts if v.select]
        for v in selected_verts:
            for edge in v.link_edges:
                if edge.other_vert(v) not in verts:
                    other_vert = edge.other_vert(v)
                    v.co += (other_vert.co - v.co) * shangSheRuYinZi / 100

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='MiddleCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='VERT')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BridgeMiddleCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=80,
                           segments=int((xiaFangYangXian_offset + mianban_offset) / 0.2), release_confirm=True)
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.object.mode_set(mode='OBJECT')
        copy_loft_obj_for_battery_plane_cut(smooth_loft_obj)

        main_obj = bpy.data.objects.get(name)
        bpy.context.view_layer.objects.active = main_obj
        main_obj.select_set(True)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        copy_model_for_top_circle_cut()


def copy_loft_obj_for_battery_plane_cut(loft_obj):
    # 根据当前两条蓝线桥接后的模型复制出一份物体用于电池面板的切割
    name = bpy.context.scene.leftWindowObj
    loft_obj_for_battery_plane_cut = bpy.data.objects.get(name + "shellLoftObj")  # TODO 后期作外壳模块切换时记得将该物体删除
    if (loft_obj_for_battery_plane_cut != None):
        bpy.data.objects.remove(loft_obj_for_battery_plane_cut, do_unlink=True)
    duplicate_obj = loft_obj.copy()
    duplicate_obj.data = loft_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellLoftObj"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)




def updateBatteryLocationAndRotation():
    '''
    底部圆环位置和角度调整时候,电池的角度和位置随之而改变
    '''
    name = bpy.context.scene.leftWindowObj
    obj_circle = bpy.data.objects.get(name + 'BottomCircle')
    battery_obj = bpy.data.objects.get(name + "shellBattery")
    if(obj_circle != None and battery_obj != None):
        battery_obj.location = obj_circle.location
        battery_obj.rotation_euler = obj_circle.rotation_euler

def updateTorusAndCircleRadius(op):
    '''
    根据圆环与模型的布尔交集确定圆环的直径大小,若op为move,还需要更新圆环的中心位置
    '''


    global bottom_prev_radius, bottom_min_radius
    global middle_prev_radius, middle_min_radius
    global top_prev_radius, top_min_radius
    global top_mouse_loc, middle_mouse_loc, bottom_mouse_loc
    global cut_radius

    name = bpy.context.scene.leftWindowObj
    # print("进入更新")

    active_obj = bpy.context.active_object
    obj_torus = None
    obj_circle = None
    if(active_obj != None):
        # print("更新存在激活物体")
        if(active_obj.name == name + "TopTorus"):
            obj_torus = bpy.data.objects.get(name + 'TopTorus')
            obj_circle = bpy.data.objects.get(name + 'TopCircle')
            prev_radius = top_prev_radius
            mouse_loc_cur = top_mouse_loc
        elif(active_obj.name == name + "MiddleTorus"):
            obj_torus = bpy.data.objects.get(name + 'MiddleTorus')
            obj_circle = bpy.data.objects.get(name + 'MiddleCircle')
            prev_radius = middle_prev_radius
            mouse_loc_cur = middle_mouse_loc
        elif (active_obj.name == name + "BottomTorus"):
            obj_torus = bpy.data.objects.get(name + 'BottomTorus')
            obj_circle = bpy.data.objects.get(name + 'BottomCircle')
            prev_radius = bottom_prev_radius
            mouse_loc_cur = bottom_mouse_loc
        if(obj_torus != None and obj_circle != None):
            # 根据用于布尔的物体复制一份物体,该物体与圆环作交集得到交集平面
            shell_bool_obj = bpy.data.objects.get(name + "ShellBoolObj")                                                #根据布尔物体复制一份得到交集物体
            shell_bool_intersect_obj = bpy.data.objects.get(name + "ShellBoolObjIntersect")
            if (shell_bool_intersect_obj != None):
                bpy.data.objects.remove(shell_bool_intersect_obj, do_unlink=True)
            intersect_obj = shell_bool_obj.copy()
            intersect_obj.data = shell_bool_obj.data.copy()
            intersect_obj.name = shell_bool_obj.name + "Intersect"
            intersect_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(intersect_obj)
            if name == '右耳':
                moveToRight(intersect_obj)
            elif name == '左耳':
                moveToLeft(intersect_obj)
            bpy.ops.object.select_all(action='DESELECT')
            intersect_obj.select_set(True)
            bpy.context.view_layer.objects.active = intersect_obj
            bool_modifier = intersect_obj.modifiers.new(name="ShellCirCleIntersectBooleanModifier", type='BOOLEAN')     #将布尔物体复制出的物体与圆环作差集得到交集平面
            bool_modifier.operation = 'INTERSECT'
            bool_modifier.solver = 'FAST'
            bool_modifier.object = obj_circle
            bpy.ops.object.modifier_apply(modifier="ShellCirCleIntersectBooleanModifier", single_user=True)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            rbm = bmesh.from_edit_mesh(intersect_obj.data)
            circle_plane_normal = obj_circle.matrix_world.to_3x3() @ obj_circle.data.polygons[0].normal
            circle_plane_loc = obj_circle.location.copy()
            plane_verts = [v for v in rbm.verts if round(abs(circle_plane_normal.dot(v.co - circle_plane_loc)), 4) == 0]   #获取布尔交集物体中与圆环平行的顶点
            if (len(plane_verts) == 0):
                on_obj = False
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.data.objects.remove(intersect_obj, do_unlink=True)
                print("没有交集")
            else:
                on_obj = True
            if on_obj:                                                       #当圆环在模型上与模型有交集时,调整圆环的位置和大小
                for v in plane_verts:
                    v.select = True
                for edge in rbm.edges:
                    if edge.verts[0].select and edge.verts[1].select:
                        edge.select_set(True)
                bpy.ops.mesh.separate(type='SELECTED')                       #根据交集物体复制出一份临时物体主要用于处理当圆环与模型的交集有连个非连通平面时处理圆环中心位于哪个平面交集
                bpy.ops.object.mode_set(mode='OBJECT')
                for obj in bpy.data.objects:
                    if obj.select_get():
                        if obj.name != intersect_obj.name:
                            temp_plane_obj = obj
                bpy.context.view_layer.objects.active = temp_plane_obj
                intersect_obj.select_set(False)
                temp_plane_obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bm = bmesh.from_edit_mesh(temp_plane_obj.data)
                verts = [v for v in bm.verts]
                verts[0].select = True
                bpy.ops.mesh.select_linked(delimit=set())
                select_verts = [v for v in bm.verts if v.select]                           #选中交集平面中第一个连通区域
                unselect_verts = [v for v in bm.verts if not v.select]                     #交集平面中剩余连通区域

                if len(select_verts) == len(verts):                                            #只存在一个交集平面

                    # print("选中的顶点数和平面上的顶点数一致")
                    center = sum((v.co for v in verts), Vector()) / len(verts)
                    max_distance = float('-inf')
                    min_distance = float('inf')
                    for vertex in verts:
                        distance = (vertex.co - obj_torus.location).length
                        max_distance = max(max_distance, distance)
                        min_distance = min(min_distance, distance)
                    radius = round(max_distance, 2) + 0.5
                    # print('最大半径',radius)
                    # print('最小半径',min_distance)
                    if (obj_torus.name == name + "TopTorus"):
                        top_min_radius = round(min_distance, 2)
                    elif (obj_torus.name == name + "MiddleTorus"):
                        middle_min_radius = round(min_distance, 2)
                    elif (obj_torus.name == name + "BottomTorus"):
                        bottom_min_radius = round(min_distance, 2)

                else:                                                                      #有两个交集平面
                    # print("选中的顶点数和平面上的顶点数不一致")
                    center1 = sum((v.co for v in select_verts), Vector()) / len(select_verts)
                    center2 = sum((v.co for v in unselect_verts), Vector()) / len(unselect_verts)
                    if (mouse_loc_cur - center1).length < (mouse_loc_cur - center2).length:
                        center = center1
                        verts = select_verts
                    else:
                        center = center2
                        verts = unselect_verts
                    max_distance = float('-inf')
                    min_distance = float('inf')
                    for vertex in verts:
                        distance = (vertex.co - obj_torus.location).length
                        max_distance = max(max_distance, distance)
                        min_distance = min(min_distance, distance)
                    radius = round(max_distance, 2) + 0.5
                    # print('最大半径',radius)
                    # print('最小半径',min_distance)
                    if (obj_torus.name == name + "TopTorus"):
                        top_min_radius = round(min_distance, 2)
                    elif (obj_torus.name == name + "MiddleTorus"):
                        middle_min_radius = round(min_distance, 2)
                    elif (obj_torus.name == name + "BottomTorus"):
                        bottom_min_radius = round(min_distance, 2)

                # center = sum((v.co for v in plane_verts), Vector()) / len(plane_verts)
                #
                # # 初始化最大距离为负无穷大
                # max_distance = float('-inf')
                # min_distance = float('inf')
                #
                # # 遍历的每个顶点并计算距离
                # for vertex in plane_verts:
                #     distance = (vertex.co - obj_torus.location).length
                #     max_distance = max(max_distance, distance)
                #     min_distance = min(min_distance, distance)
                #
                # radius = round(max_distance, 2) + 0.5
                # if (obj_torus.name == name + "TopTorus"):
                #     top_min_radius = round(min_distance, 2)
                # elif (obj_torus.name == name + "MiddleTorus"):
                #     middle_min_radius = round(min_distance, 2)
                # elif (obj_torus.name == name + "BottomTorus"):
                #     bottom_min_radius = round(min_distance, 2)

                bpy.ops.object.mode_set(mode='OBJECT')

                # bpy.ops.object.select_all(action='DESELECT')
                # bpy.context.view_layer.objects.active = obj_torus
                # obj_torus.select_set(True)
                if op == 'move':                                             #调整圆环和环体的位置
                    obj_torus.location[0] = center.x
                    obj_torus.location[1] = center.y
                    obj_circle.location[0] = center.x
                    obj_circle.location[1] = center.y
                scale_ratio = round(radius / prev_radius, 3)                  #调整圆环和环体的大小
                obj_torus.scale = (scale_ratio, scale_ratio, 1)
                # print("更新半径:",radius)
                # print("上次的半径:",prev_radius)
                # print("比例:",scale_ratio)

                bpy.data.objects.remove(intersect_obj, do_unlink=True)  # 删除布尔交集平面和分离出的顶点物体
                bpy.data.objects.remove(temp_plane_obj, do_unlink=True)

                if (obj_circle.name == name + 'BottomCircle' and on_obj and
                        bpy.data.objects.get(name + "meshBottomRingBorderR").hide_get()):
                    cut_circle = bpy.data.objects.get(name + 'CutCircle')
                    intersect_obj = shell_bool_obj.copy()
                    intersect_obj.data = shell_bool_obj.data.copy()
                    intersect_obj.name = shell_bool_obj.name + "Intersect"
                    intersect_obj.animation_data_clear()
                    bpy.context.scene.collection.objects.link(intersect_obj)
                    if name == '右耳':
                        moveToRight(intersect_obj)
                    elif name == '左耳':
                        moveToLeft(intersect_obj)
                    bpy.ops.object.select_all(action='DESELECT')
                    intersect_obj.select_set(True)
                    bpy.context.view_layer.objects.active = intersect_obj
                    bool_modifier = intersect_obj.modifiers.new(name="ShellCirCleIntersectBooleanModifier",
                                                                type='BOOLEAN')  # 将布尔物体复制出的物体与圆环作差集得到交集平面
                    bool_modifier.operation = 'INTERSECT'
                    bool_modifier.solver = 'FAST'
                    bool_modifier.object = cut_circle
                    bpy.ops.object.modifier_apply(modifier="ShellCirCleIntersectBooleanModifier", single_user=True)

                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    rbm = bmesh.from_edit_mesh(intersect_obj.data)
                    circle_plane_normal = cut_circle.matrix_world.to_3x3() @ cut_circle.data.polygons[0].normal
                    circle_plane_loc = cut_circle.location.copy()
                    plane_verts = [v for v in rbm.verts if round(abs(circle_plane_normal.dot(v.co - circle_plane_loc)),
                                                                 4) == 0]  # 获取布尔交集物体中与圆环平行的顶点
                    # center = sum((v.co for v in plane_verts), Vector()) / len(plane_verts)

                    if (len(plane_verts) == 0):
                        on_obj = False
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.data.objects.remove(intersect_obj, do_unlink=True)
                        print("没有交集")
                    else:
                        on_obj = True
                    if on_obj:  # 当圆环在模型上与模型有交集时,调整圆环的位置和大小
                        for v in plane_verts:
                            v.select = True
                        for edge in rbm.edges:
                            if edge.verts[0].select and edge.verts[1].select:
                                edge.select_set(True)
                        bpy.ops.mesh.separate(type='SELECTED')  # 根据交集物体复制出一份临时物体主要用于处理当圆环与模型的交集有连个非连通平面时处理圆环中心位于哪个平面交集
                        bpy.ops.object.mode_set(mode='OBJECT')
                        for obj in bpy.data.objects:
                            if obj.select_get():
                                if obj.name != intersect_obj.name:
                                    temp_plane_obj = obj
                        if name == "右耳":
                            moveToRight(temp_plane_obj)
                        elif name == "左耳":
                            moveToLeft(temp_plane_obj)
                        bpy.context.view_layer.objects.active = temp_plane_obj
                        intersect_obj.select_set(False)
                        temp_plane_obj.select_set(True)
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bm = bmesh.from_edit_mesh(temp_plane_obj.data)
                        verts = [v for v in bm.verts]
                        verts[0].select = True
                        bpy.ops.mesh.select_linked(delimit=set())
                        select_verts = [v for v in bm.verts if v.select]  # 选中交集平面中第一个连通区域
                        unselect_verts = [v for v in bm.verts if not v.select]  # 交集平面中剩余连通区域

                        if len(select_verts) == len(verts):  # 只存在一个交集平面
                            center = sum((v.co for v in verts), Vector()) / len(verts)
                            max_distance = float('-inf')
                            min_distance = float('inf')
                            for vertex in verts:
                                distance = (vertex.co - cut_circle.location).length
                                max_distance = max(max_distance, distance)
                                min_distance = min(min_distance, distance)
                            cut_radius = round(max_distance, 2) + 0.5

                        else:  # 有两个交集平面
                            center1 = sum((v.co for v in select_verts), Vector()) / len(select_verts)
                            center2 = sum((v.co for v in unselect_verts), Vector()) / len(unselect_verts)
                            if (mouse_loc_cur - center1).length < (mouse_loc_cur - center2).length:
                                center = center1
                                verts = select_verts
                                bpy.ops.mesh.select_all(action='DESELECT')
                                for v in unselect_verts:
                                    v.select = True
                                bpy.ops.mesh.delete(type='VERT')
                            else:
                                center = center2
                                verts = unselect_verts
                                bpy.ops.mesh.delete(type='VERT')
                            max_distance = float('-inf')
                            min_distance = float('inf')
                            for vertex in verts:
                                distance = (vertex.co - cut_circle.location).length
                                max_distance = max(max_distance, distance)
                                min_distance = min(min_distance, distance)
                            cut_radius = round(max_distance, 2) + 0.5
                        bpy.ops.object.mode_set(mode='OBJECT')

                        bpy.ops.object.convert(target='CURVE')
                        if bpy.data.objects.get(name + "BottomRingBorderR") != None:
                            bpy.data.objects.remove(bpy.data.objects.get(name + "BottomRingBorderR"), do_unlink=True)
                        temp_plane_obj.name = name + "BottomRingBorderR"
                        temp_plane_obj.data.bevel_depth = 0.18
                        temp_plane_obj.data.materials.append(bpy.data.materials['blue'])
                        bpy.data.objects.remove(intersect_obj, do_unlink=True)
                        if op == 'move':  # 调整圆环的位置
                            cut_circle.location[0] = center.x
                            cut_circle.location[1] = center.y

        bpy.ops.object.select_all(action='DESELECT')                         #重新将该物体激活
        active_obj.select_set(True)
        bpy.context.view_layer.objects.active = active_obj

        # obj_circle.location[0] = obj_torus.location[0]
        # obj_circle.location[1] = obj_torus.location[1]
        # obj_circle.location[2] = obj_torus.location[2]
        # obj_circle.rotation_euler[0] = obj_torus.rotation_euler[0]
        # obj_circle.rotation_euler[1] = obj_torus.rotation_euler[1]
        # obj_circle.rotation_euler[2] = obj_torus.rotation_euler[2]


        # updateBatteryLocationAndRotation()             //使用select_box等按钮控制圆环鼠标行为时,需要使用该函数更新电池的位置;使用event操作鼠标行为则再操作过程中就更新了电池位置,不需要调用该函数



def cutBatteryPlane():
    '''
    根据底部蓝线切割后的模型底部边界切割电池面板
    '''
    pass






def onWhichObject(context,event):
    '''
    判断鼠标在哪种物体上,切换到对应的鼠标行为
    鼠标在电池仓上返回501
    鼠标在红环上返回40x
    鼠标在立方体上返回30x
    鼠标在管道红球上返回20x
    鼠标在外管道上时返回101
    鼠标在曲线上时返回60x
    其他情况下返回0,此时对应管道鼠标行为或公共鼠标行为
    '''
    global top_mouse_loc, middle_mouse_loc, bottom_mouse_loc
    name = bpy.context.scene.leftWindowObj

    object_dic_cur = getObjectDic()

    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )
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

    # 在显示红球字典中添加对应的透明红球名称
    sphere_name_list = []
    for key in object_dic_cur:
        sphere_name = key
        object_index = int(key.replace(name + 'shellcanalsphere', ''))
        transparency_sphere_name = name + 'shellcanalsphere' + str(200 + object_index)
        # sphere_name_list.append(sphere_name)
        sphere_name_list.append(transparency_sphere_name)
    # 鼠标是否在管道的红球上
    for key in sphere_name_list:
        active_obj = bpy.data.objects.get(key)
        if (active_obj != None):
            object_index = int(key.replace(name + 'shellcanalsphere', ''))
            mwi = active_obj.matrix_world.inverted()
            mwi_start = mwi @ start
            mwi_end = mwi @ end
            mwi_dir = mwi_end - mwi_start
            if active_obj.type == 'MESH':
                if (active_obj.mode == 'OBJECT'):
                    mesh = active_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                    _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                    if fidx is not None:
                        return object_index


    #鼠标在外壳外管道上时,切换到管道红球添加鼠标行为
    mesh_shell_outercanal_name = name + 'meshshelloutercanal'
    mesh_shell_outercanal_obj = bpy.data.objects.get(mesh_shell_outercanal_name)
    if(mesh_shell_outercanal_obj != None):
        active_obj = mesh_shell_outercanal_obj
        if (active_obj != None):
            mwi = active_obj.matrix_world.inverted()
            mwi_start = mwi @ start
            mwi_end = mwi @ end
            mwi_dir = mwi_end - mwi_start
            if active_obj.type == 'MESH':
                if (active_obj.mode == 'OBJECT'):
                    mesh = active_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                    loc, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                    if fidx is not None:
                        return 101


    tours_obj_list = [name + "TopTorus", name + "MiddleTorus", name + "BottomTorus"]
    for key in tours_obj_list:
        active_obj = bpy.data.objects.get(key)
        if(active_obj != None):
            mwi = active_obj.matrix_world.inverted()
            mwi_start = mwi @ start
            mwi_end = mwi @ end
            mwi_dir = mwi_end - mwi_start
            if active_obj.type == 'MESH':
                if (active_obj.mode == 'OBJECT'):
                    mesh = active_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                    loc, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                    if fidx is not None:
                        if(active_obj.name == name + "TopTorus"):
                            top_mouse_loc = loc
                            return 401
                        elif(active_obj.name == name + "MiddleTorus"):
                            middle_mouse_loc = loc
                            return 402
                        elif (active_obj.name == name + "BottomTorus"):
                            bottom_mouse_loc = loc
                            return 403

    # 判断鼠标是否在曲线或底部面板上
    cubes_obj_list = [name + "meshPlaneBorderCurve", name + "meshBottomRingBorderR", name + "ShellOuterCutBatteryPlane"]
    for key in cubes_obj_list:
        active_obj = bpy.data.objects.get(key)
        if (active_obj != None):
            mwi = active_obj.matrix_world.inverted()
            mwi_start = mwi @ start
            mwi_end = mwi @ end
            mwi_dir = mwi_end - mwi_start
            if active_obj.type == 'MESH':
                if (active_obj.mode == 'OBJECT'):
                    mesh = active_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                    _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                    if fidx is not None:
                        if (active_obj.name == name + "meshPlaneBorderCurve"):
                            return 601
                        elif (active_obj.name == name + "meshBottomRingBorderR"):
                            return 602
                        elif (active_obj.name == name + "ShellOuterCutBatteryPlane" and
                              not bpy.data.objects.get(name + "meshPlaneBorderCurve")):
                            return 603

    # 判断鼠标是否在电池仓上
    active_obj = bpy.data.objects.get(name + "shellBattery")
    if (active_obj != None):
        mwi = active_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if active_obj.type == 'MESH':
            if (active_obj.mode == 'OBJECT'):
                mesh = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 501


    #判断模型是否在接收器上
    active_obj = bpy.data.objects.get(name + "receiver")
    if (active_obj != None):
        mwi = active_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if active_obj.type == 'MESH':
            if (active_obj.mode == 'OBJECT'):
                mesh = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 304
    #判断鼠标是否在立方体上
    cubes_obj_list = [name + "move_cube3", name + "move_cube2", name + "move_cube1"]
    for key in cubes_obj_list:
        active_obj = bpy.data.objects.get(key)
        if(active_obj != None):
            object_index = int(key.replace(name + 'move_cube', ''))
            mwi = active_obj.matrix_world.inverted()
            mwi_start = mwi @ start
            mwi_end = mwi @ end
            mwi_dir = mwi_end - mwi_start
            if active_obj.type == 'MESH':
                if (active_obj.mode == 'OBJECT'):
                    mesh = active_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                    _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                    if fidx is not None:
                        return 300 + object_index

    return 0



def objectMouseSwitch(object_number):
    '''
    鼠标位于不同的物体上时,切换到不同的鼠标行为
    '''
    global mouse_index
    global mouse_indexL
    name = bpy.context.scene.leftWindowObj
    if (name == '右耳'):
        if (object_number == 0 and mouse_index != 1):
            mouse_index = 1
            # 鼠标不在其他物体上时(除左右耳物体),切换到公共鼠标行为
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            mesh_shell_outercanal_obj = bpy.data.objects.get(name + 'meshshelloutercanal')
            if (mesh_shell_outercanal_obj != None):
                # 存在外壳管道后,只有鼠标在管道上时才调用管道红球添加鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            else:
                # 不存在外壳管道时,需要先调用管道红球添加鼠标行为,添加两个红球生成管道
                bpy.ops.wm.tool_set_by_id(name="my_tool.public_add_shellcanal")
            print("切换到公共鼠标行为")
        elif((object_number == 301 or object_number == 302 or object_number == 303 or object_number == 304) and mouse_index != 2):
            mouse_index = 2
            #激活碰撞检测中的立方体,切换到立方体拖拽旋转鼠标行为
            setActiveAndMoveCubeName(object_number - 300)
            if (object_number == 304):
                # 鼠标在接受器上时激活其父物体接收器平面
                bpy.context.scene.tool_settings.use_snap = True
                cube_name = name + "ReceiverPlane"
            else:
                bpy.context.scene.tool_settings.use_snap = False
                cube_name = name + "move_cube" + str(object_number - 300)
            cube_object = bpy.data.objects.get(cube_name)
            bpy.ops.object.select_all(action='DESELECT')
            cube_object.select_set(True)
            bpy.context.view_layer.objects.active = cube_object
            bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
            print("切换到Cube鼠标行为")
        elif ((object_number > 200 and object_number < 300 ) and mouse_index != 3):
            mouse_index = 3
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            bpy.context.scene.tool_settings.use_snap = True
            sphere_name = name + 'shellcanalsphere' + str(object_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.delete_drag_shellcanal")
            print("切换到管道鼠标行为")
        elif ((object_number == 401 or object_number == 402 or object_number == 403) and mouse_index != 4):
            mouse_index = 4
            bpy.context.scene.tool_settings.use_snap = False
            if(object_number == 401):
                tours_name = name + "TopTorus"
            elif(object_number == 402):
                tours_name = name + "MiddleTorus"
            elif (object_number == 403):
                tours_name = name + "BottomTorus"
            tours_obj = bpy.data.objects.get(tours_name)
            bpy.ops.object.select_all(action='DESELECT')
            tours_obj.select_set(True)
            bpy.context.view_layer.objects.active = tours_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            print("切换到圆环鼠标行为")
        elif (object_number == 501 and mouse_index != 5):
            mouse_index = 5
            bpy.context.scene.tool_settings.use_snap = False
            battery_obj = bpy.data.objects.get(name + "shellBattery")
            bpy.ops.object.select_all(action='DESELECT')
            battery_obj.select_set(True)
            bpy.context.view_layer.objects.active = battery_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
            print("切换到电池仓鼠标行为")
        elif (object_number == 101 and mouse_index != 6):
            mouse_index = 6
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.public_add_shellcanal")
            print("切换到管道添加红球鼠标行为")
        elif ((object_number == 601 or object_number == 602 or object_number == 603) and mouse_index != 7 and
              bpy.context.scene.var == 19):
            mouse_index = 7
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")
            print("切换到蓝线点加鼠标行为")


    elif (name == '左耳'):
        if (object_number == 0 and mouse_indexL != 1):
            mouse_indexL = 1
            # 鼠标不在其他物体上时(除左右耳物体),切换到公共鼠标行为
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            mesh_shell_outercanal_obj = bpy.data.objects.get(name + 'meshshelloutercanal')
            if (mesh_shell_outercanal_obj != None):
                # 存在外壳管道后,只有鼠标在管道上时才调用管道红球添加鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            else:
                # 不存在外壳管道时,需要先调用管道红球添加鼠标行为,添加两个红球生成管道
                bpy.ops.wm.tool_set_by_id(name="my_tool.public_add_shellcanal")
        elif ((object_number == 301 or object_number == 302 or object_number == 303 or object_number == 304) and mouse_indexL != 2):
            mouse_indexL = 2
            # 激活碰撞检测中的立方体,切换到立方体拖拽旋转鼠标行为
            setActiveAndMoveCubeName(object_number - 300)
            if (object_number == 304):
                # 鼠标在接受器上时激活其父物体接收器平面
                bpy.context.scene.tool_settings.use_snap = True
                cube_name = name + "ReceiverPlane"
            else:
                bpy.context.scene.tool_settings.use_snap = False
                cube_name = name + "move_cube" + str(object_number - 300)
            cube_object = bpy.data.objects.get(cube_name)
            bpy.ops.object.select_all(action='DESELECT')
            cube_object.select_set(True)
            bpy.context.view_layer.objects.active = cube_object
            bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
        elif ((object_number > 200 and object_number < 300) and mouse_indexL != 3):
            mouse_indexL = 3
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            bpy.context.scene.tool_settings.use_snap = True
            sphere_name = name + 'shellcanalsphere' + str(object_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.delete_drag_shellcanal")
        elif ((object_number == 401 or object_number == 402 or object_number == 403) and mouse_indexL != 4):
            mouse_indexL = 4
            bpy.context.scene.tool_settings.use_snap = False
            if(object_number == 401):
                tours_name = name + "TopTorus"
            elif(object_number == 402):
                tours_name = name + "MiddleTorus"
            elif (object_number == 403):
                tours_name = name + "BottomTorus"
            tours_obj = bpy.data.objects.get(tours_name)
            bpy.ops.object.select_all(action='DESELECT')
            tours_obj.select_set(True)
            bpy.context.view_layer.objects.active = tours_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        elif (object_number == 501 and mouse_indexL != 5):
            mouse_indexL = 5
            bpy.context.scene.tool_settings.use_snap = False
            battery_obj = bpy.data.objects.get(name + "shellBattery")
            bpy.ops.object.select_all(action='DESELECT')
            battery_obj.select_set(True)
            bpy.context.view_layer.objects.active = battery_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
        elif (object_number == 101 and mouse_indexL != 6):
            mouse_indexL = 6
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.public_add_shellcanal")
            print("切换到管道添加红球鼠标行为")
        elif ((object_number == 601 or object_number == 602 or object_number == 603) and mouse_indexL != 7 and
              bpy.context.scene.var == 19):
            mouse_indexL = 7
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")
            print("切换到蓝线点加鼠标行为")


def set_shell_modal_finish(value):
    global finish
    finish = value


class TEST_OT_shell_switch(bpy.types.Operator):
    bl_idname = "object.shell_switch"
    bl_label = "shell_switch"
    bl_description = "鼠标行为切换"

    __left_mouse_down = False
    __right_mouse_down = False
    __timer = None              #添加定时器

    def invoke(self, context, event):  # 初始化
        # newColor('red', 1, 0, 0, 0, 1)
        # newColor('grey', 0.8, 0.8, 0.8, 0, 1)  # 不透明材质
        # newColor('grey1', 0.8, 0.8, 0.8, 1, 0.4)  # 透明材质
        # 设置吸附相关参数
        name = bpy.context.scene.leftWindowObj
        cur_obj = bpy.data.objects.get(name)
        mould_reset = bpy.data.objects.get(name + 'MouldReset')
        cur_obj.hide_select = False
        mould_reset.hide_select = True
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.use_snap_selectable = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True
        bpy.context.scene.tool_settings.use_snap = False
        if not TEST_OT_shell_switch.__timer:
            TEST_OT_shell_switch.__timer = context.window_manager.event_timer_add(0.01, window=context.window)

        if not get_shell_modal_start():
            set_shell_modal_start(True)
            context.window_manager.modal_handler_add(self)
            print('shellcanalqiehuan invoke')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global mouse_index
        global mouse_indexL
        global top_mouse_loc, middle_mouse_loc, bottom_mouse_loc

        global torus_left_mouse_press, torus_right_mouse_press
        global battery_mouse_press
        global torus_initial_rotation_x, torus_initial_rotation_y, torus_initial_rotation_z
        global torus_now_mouse_x, torus_now_mouse_y, torus_initial_mouse_x, torus_initial_mouse_y
        global torus_is_moving, torus_dx, torus_dy
        global finish

        op_cls = TEST_OT_shell_switch
        name = bpy.context.scene.leftWindowObj

        mouse_x = event.mouse_x
        mouse_y = event.mouse_y
        override1 = getOverride()
        area = override1['area']

        if bpy.context.screen.areas[0].spaces.active.context == 'SCENE':

            # 处在蓝线操作的状态时，不执行此modal的操作
            if bpy.data.objects.get(name + "selectcurve") or bpy.data.objects.get(name + "point"):
                return {'PASS_THROUGH'}

            # 物体处在报错状态下, 将暂停的状态取消
            if bpy.data.objects[context.scene.leftWindowObj].data.materials[0].name == "error_yellow" and \
                    context.mode == 'OBJECT' and finish:
                finish = False

            # 鼠标在3D区域内
            if mouse_x < area.width and area.y < mouse_y < area.y+area.height and bpy.context.scene.muJuTypeEnum == "OP3" and not finish:
                if event.type == 'LEFTMOUSE':  # 监听左键
                    if event.value == 'PRESS':  # 按下
                        op_cls.__left_mouse_down = True

                elif event.type == 'RIGHTMOUSE':  # 监听右键
                    if event.value == 'PRESS':  # 按下
                        op_cls.__right_mouse_down = True

                elif event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    elif op_cls.__right_mouse_down:
                        op_cls.__right_mouse_down = False

                #根据鼠标所在鼠标位置切换到不同的鼠标行为
                object_number = onWhichObject(context,event)
                if (not op_cls.__left_mouse_down and not op_cls.__right_mouse_down
                        and not torus_right_mouse_press and not torus_left_mouse_press
                        and not battery_mouse_press):
                    objectMouseSwitch(object_number)
                if (name == "右耳"):
                    mouse_index_cur = mouse_index
                elif (name == "左耳"):
                    mouse_index_cur = mouse_indexL

                if (mouse_index_cur == 1):
                    resetCubeLocationAndRotation()
                elif(mouse_index_cur == 2):
                    update_cube_location_rotate(op_cls.__right_mouse_down)
                elif(mouse_index_cur == 3):
                    updateShellCanal(context,event,op_cls.__left_mouse_down)
                elif(mouse_index_cur == 4):

                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.context.active_object
                    obj_torus = None
                    obj_circle = None
                    if (active_obj != None):
                        battery_obj = bpy.data.objects.get(name + 'shellBattery')
                        cut_circle = bpy.data.objects.get(name + "CutCircle")
                        if (active_obj.name == name + "TopTorus"):
                            obj_torus = bpy.data.objects.get(name + 'TopTorus')
                            obj_circle = bpy.data.objects.get(name + 'TopCircle')
                            torus_index = 401
                            mouse_loc_cur = top_mouse_loc
                        elif (active_obj.name == name + "MiddleTorus"):
                            obj_torus = bpy.data.objects.get(name + 'MiddleTorus')
                            obj_circle = bpy.data.objects.get(name + 'MiddleCircle')
                            torus_index = 402
                            mouse_loc_cur = middle_mouse_loc
                        elif (active_obj.name == name + "BottomTorus"):
                            obj_torus = bpy.data.objects.get(name + 'BottomTorus')
                            obj_circle = bpy.data.objects.get(name + 'BottomCircle')
                            torus_index = 403
                            mouse_loc_cur = bottom_mouse_loc
                        if (obj_torus != None and obj_circle != None):
                            # 鼠标是否在圆环上
                            if (onWhichObject(context, event) == torus_index):
                                bpy.ops.object.select_all(action='DESELECT')
                                bpy.context.view_layer.objects.active = obj_torus
                                obj_torus.select_set(True)

                                if (active_obj.name == name + "TopTorus"):
                                    mouse_loc_cur = top_mouse_loc
                                elif (active_obj.name == name + "MiddleTorus"):
                                    mouse_loc_cur = middle_mouse_loc
                                elif (active_obj.name == name + "BottomTorus"):
                                    mouse_loc_cur = bottom_mouse_loc

                                if event.type == 'LEFTMOUSE':
                                    if event.value == 'PRESS':
                                        torus_is_moving = True
                                        torus_left_mouse_press = True
                                        torus_initial_rotation_x = obj_torus.rotation_euler[0]
                                        torus_initial_rotation_y = obj_torus.rotation_euler[1]
                                        torus_initial_rotation_z = obj_torus.rotation_euler[2]
                                        torus_initial_mouse_x = event.mouse_region_x
                                        torus_initial_mouse_y = event.mouse_region_y

                                        torus_dx = round(mouse_loc_cur.x, 2)
                                        torus_dy = round(mouse_loc_cur.y, 2)

                                        if (torus_index == 403):
                                            if name == '右耳':
                                                shell_border = get_right_shell_border()
                                            elif name == '左耳':
                                                shell_border = get_left_shell_border()

                                            if (bpy.data.objects.get(name + "meshBottomRingBorderR") != None
                                                    and len(shell_border) == 0):
                                                if not bpy.data.objects.get(name + "meshBottomRingBorderR").hide_get():
                                                    bpy.data.objects.get(name + "meshBottomRingBorderR").hide_set(True)
                                                # if not bpy.data.objects.get(name + "BottomRingBorderR").hide_get():
                                                #     bpy.data.objects.get(name + "BottomRingBorderR").hide_set(True)
                                            if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
                                                if not bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_get():
                                                    bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_set(True)
                                    elif event.value == 'RELEASE':
                                        normal = obj_circle.matrix_world.to_3x3(
                                        ) @ obj_circle.data.polygons[0].normal
                                        if normal.z > 0:  # 反转法线
                                            obj_circle.hide_set(False)
                                            bpy.context.view_layer.objects.active = obj_circle
                                            bpy.ops.object.mode_set(mode='EDIT')
                                            bpy.ops.mesh.select_all(action='SELECT')
                                            bpy.ops.mesh.flip_normals()
                                            obj_circle.hide_set(True)
                                            bpy.ops.object.mode_set(mode='OBJECT')

                                        saveCirInfo()                 # 保存数据 圆环位置,旋转,尺寸大小
                                        # 不使用中部切割红环时,根据offset参数更新中部切割平面的位置
                                        update_middle_circle_offset()
                                        if(torus_index == 401):       # 重新补面填充
                                            update_top_circle_cut()
                                        elif(torus_index == 402):
                                            update_middle_circle_cut()
                                        elif(torus_index == 403):
                                            create_middle_base_curve()
                                            create_bottom_base_curve()
                                            update_plane_and_curve()

                                        torus_is_moving = False
                                        torus_left_mouse_press = False
                                        torus_initial_rotation_x = None
                                        torus_initial_rotation_y = None
                                        torus_initial_rotation_z = None
                                        torus_initial_mouse_x = None
                                        torus_initial_mouse_y = None

                                        # 将激活物体恢复为操作的圆环
                                        bpy.ops.object.select_all(action='DESELECT')
                                        bpy.context.view_layer.objects.active = active_obj
                                        active_obj.select_set(True)

                                    return {'RUNNING_MODAL'}

                                elif event.type == 'RIGHTMOUSE':
                                    if event.value == 'PRESS':
                                        torus_is_moving = True
                                        torus_right_mouse_press = True
                                        torus_initial_mouse_x = event.mouse_region_x
                                        torus_initial_mouse_y = event.mouse_region_y

                                        if name == '右耳':
                                            shell_border = get_right_shell_border()
                                        elif name == '左耳':
                                            shell_border = get_left_shell_border()

                                        if (torus_index == 403):
                                            if (bpy.data.objects.get(name + "meshBottomRingBorderR") != None
                                                    and len(shell_border) == 0):
                                                if not bpy.data.objects.get(name + "meshBottomRingBorderR").hide_get():
                                                    bpy.data.objects.get(name + "meshBottomRingBorderR").hide_set(True)
                                                # if not bpy.data.objects.get(name + "BottomRingBorderR").hide_get():
                                                #     bpy.data.objects.get(name + "BottomRingBorderR").hide_set(True)
                                            if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
                                                if not bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_get():
                                                    bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_set(True)
                                    elif event.value == 'RELEASE':
                                        saveCirInfo()                    #保存数据 圆环位置,旋转,尺寸大小
                                        # 不使用中部切割红环时,根据offset参数更新中部切割平面的位置
                                        update_middle_circle_offset()
                                        if (torus_index == 401):         # 重新补面填充
                                            update_top_circle_cut()
                                        elif (torus_index == 402):
                                            update_middle_circle_cut()
                                        elif (torus_index == 403):
                                            create_middle_base_curve()
                                            create_bottom_base_curve()
                                            update_plane_and_curve()

                                        torus_is_moving = False
                                        torus_right_mouse_press = False
                                        torus_initial_mouse_x = None
                                        torus_initial_mouse_y = None

                                        # 将激活物体恢复为操作的圆环
                                        bpy.ops.object.select_all(action='DESELECT')
                                        bpy.context.view_layer.objects.active = active_obj
                                        active_obj.select_set(True)

                                    return {'RUNNING_MODAL'}

                                elif event.type == 'MOUSEMOVE':
                                    # 左键按住旋转: 左键移动根据位置计算旋转角度并旋转圆环,调用getRadius函数调整圆环尺寸大小
                                    if torus_left_mouse_press:
                                        # 旋转角度正负号
                                        if (torus_dy < 0):
                                            symx = -1
                                        else:
                                            symx = 1
                                        if (torus_dx > 0):
                                            symy = -1
                                        else:
                                            symy = 1

                                        # x,y轴旋转比例
                                        px = round(abs(torus_dy) / sqrt(
                                            torus_dx * torus_dx + torus_dy * torus_dy), 4)
                                        py = round(abs(torus_dx) / sqrt(
                                            torus_dx * torus_dx + torus_dy * torus_dy), 4)

                                        # 旋转角度
                                        rotate_angle_x = round(
                                            (event.mouse_region_y - torus_initial_mouse_y) * 0.01 * px, 4)
                                        rotate_angle_y = round(
                                            (event.mouse_region_y - torus_initial_mouse_y) * 0.01 * py, 4)
                                        rotate_angle_z = round(
                                            (event.mouse_region_x - torus_initial_mouse_x) * 0.005, 4)

                                        obj_circle.rotation_euler[0] = torus_initial_rotation_x + \
                                                                       rotate_angle_x * symx
                                        obj_circle.rotation_euler[1] = torus_initial_rotation_y + \
                                                                       rotate_angle_y * symy
                                        obj_circle.rotation_euler[2] = torus_initial_rotation_z + \
                                                                       rotate_angle_z

                                        obj_torus.rotation_euler[0] = obj_circle.rotation_euler[0]
                                        obj_torus.rotation_euler[1] = obj_circle.rotation_euler[1]
                                        obj_torus.rotation_euler[2] = obj_circle.rotation_euler[2]
                                        if (torus_index == 403):
                                            battery_obj.rotation_euler[0] = obj_circle.rotation_euler[0]
                                            battery_obj.rotation_euler[1] = obj_circle.rotation_euler[1]
                                            battery_obj.rotation_euler[2] = obj_circle.rotation_euler[2]
                                            cut_circle.rotation_euler = obj_circle.rotation_euler

                                        updateTorusAndCircleRadius('rotate')

                                        return {'RUNNING_MODAL'}

                                    # 右键移动根据位置计算法线平移距离并移动圆环,调用getRadius函数调整圆环尺寸大小
                                    elif torus_right_mouse_press:
                                        # 平面法线方向
                                        normal = obj_circle.matrix_world.to_3x3(
                                        ) @ obj_circle.data.polygons[0].normal

                                        dis = event.mouse_region_y - torus_initial_mouse_y
                                        torus_initial_mouse_x = event.mouse_region_x
                                        torus_initial_mouse_y = event.mouse_region_y

                                        obj_circle.location -= normal * dis * 0.05
                                        obj_torus.location -= normal * dis * 0.05
                                        if (torus_index == 403):
                                            battery_obj.location -= normal * dis * 0.05
                                            cut_circle.location -= normal * dis * 0.05

                                        updateTorusAndCircleRadius('move')

                                        return {'RUNNING_MODAL'}

                                return {'PASS_THROUGH'}


                            else:
                                # tar_obj = bpy.data.objects[name]
                                # bpy.ops.object.select_all(action='DESELECT')
                                # bpy.context.view_layer.objects.active = tar_obj
                                # tar_obj.select_set(True)
                                # print('不在圆环上')
                                if event.value == 'RELEASE' and torus_is_moving:
                                    normal = obj_circle.matrix_world.to_3x3(
                                    ) @ obj_circle.data.polygons[0].normal
                                    if normal.z > 0:
                                        obj_circle.hide_set(False)
                                        bpy.context.view_layer.objects.active = obj_circle
                                        bpy.ops.object.mode_set(mode='EDIT')
                                        bpy.ops.mesh.select_all(action='SELECT')
                                        bpy.ops.mesh.flip_normals()
                                        obj_circle.hide_set(True)
                                        bpy.ops.object.mode_set(mode='OBJECT')


                                    saveCirInfo()                   # 保存数据 圆环位置,旋转,尺寸大小
                                    # 不使用中部切割红环时,根据offset参数更新中部切割平面的位置
                                    update_middle_circle_offset()
                                    if (torus_index == 401):        # 重新补面填充
                                        update_top_circle_cut()
                                    elif (torus_index == 402):
                                        update_middle_circle_cut()
                                    elif (torus_index == 403):
                                        create_middle_base_curve()
                                        create_bottom_base_curve()
                                        update_plane_and_curve()

                                    torus_is_moving = False
                                    torus_left_mouse_press = False
                                    torus_right_mouse_press = False
                                    torus_initial_rotation_x = None
                                    torus_initial_rotation_y = None
                                    torus_initial_rotation_z = None
                                    torus_initial_mouse_x = None
                                    torus_initial_mouse_y = None

                                    # 将激活物体恢复为操作的圆环
                                    bpy.ops.object.select_all(action='DESELECT')
                                    bpy.context.view_layer.objects.active = active_obj
                                    active_obj.select_set(True)

                                if event.type == 'MOUSEMOVE':
                                    # 左键按住旋转
                                    if torus_left_mouse_press:
                                        # 旋转正负号
                                        if (torus_dy < 0):
                                            symx = -1
                                        else:
                                            symx = 1
                                        if (torus_dx > 0):
                                            symy = -1
                                        else:
                                            symy = 1

                                        #  x,y轴旋转比例
                                        px = round(abs(torus_dy) / sqrt(
                                            torus_dx * torus_dx + torus_dy * torus_dy), 4)
                                        py = round(abs(torus_dx) / sqrt(
                                            torus_dx * torus_dx + torus_dy * torus_dy), 4)

                                        # 旋转角度
                                        rotate_angle_x = round(
                                            (event.mouse_region_y - torus_initial_mouse_y) * 0.01 * px, 4)
                                        rotate_angle_y = round(
                                            (event.mouse_region_y - torus_initial_mouse_y) * 0.01 * py, 4)
                                        rotate_angle_z = round(
                                            (event.mouse_region_x - torus_initial_mouse_x) * 0.005, 4)
                                        obj_circle.rotation_euler[0] = torus_initial_rotation_x + \
                                                                       rotate_angle_x * symx
                                        obj_circle.rotation_euler[1] = torus_initial_rotation_y + \
                                                                       rotate_angle_y * symy
                                        obj_circle.rotation_euler[2] = torus_initial_rotation_z + \
                                                                       rotate_angle_z

                                        obj_torus.rotation_euler[0] = obj_circle.rotation_euler[0]
                                        obj_torus.rotation_euler[1] = obj_circle.rotation_euler[1]
                                        obj_torus.rotation_euler[2] = obj_circle.rotation_euler[2]

                                        if (torus_index == 403):
                                            battery_obj.rotation_euler[0] = obj_circle.rotation_euler[0]
                                            battery_obj.rotation_euler[1] = obj_circle.rotation_euler[1]
                                            battery_obj.rotation_euler[2] = obj_circle.rotation_euler[2]
                                            cut_circle.rotation_euler = obj_circle.rotation_euler

                                        updateTorusAndCircleRadius('rotate')


                                        return {'RUNNING_MODAL'}

                                    elif torus_right_mouse_press:
                                        # 平面法线方向
                                        normal = obj_circle.matrix_world.to_3x3(
                                        ) @ obj_circle.data.polygons[0].normal

                                        dis = event.mouse_region_y - torus_initial_mouse_y
                                        torus_initial_mouse_x = event.mouse_region_x
                                        torus_initial_mouse_y = event.mouse_region_y

                                        obj_circle.location -= normal * dis * 0.05
                                        obj_torus.location -= normal * dis * 0.05
                                        if (torus_index == 403):
                                            battery_obj.location -= normal * dis * 0.05
                                            cut_circle.location -= normal * dis * 0.05

                                        updateTorusAndCircleRadius('move')


                                        return {'RUNNING_MODAL'}
                                return {'PASS_THROUGH'}

                elif (mouse_index_cur == 5):
                    if op_cls.__left_mouse_down or op_cls.__right_mouse_down:
                        battery_mouse_press = True
                        if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
                            if not bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_get():
                                bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_set(True)
                    else:
                        if bpy.data.objects.get(name + "meshPlaneBorderCurve") != None:
                            if bpy.data.objects.get(name + "meshPlaneBorderCurve").hide_get() and battery_mouse_press:
                                curve_obj = bpy.data.objects.get(name + "PlaneBorderCurve")
                                bpy.ops.object.select_all(action='DESELECT')
                                bpy.context.view_layer.objects.active = curve_obj
                                curve_obj.select_set(True)
                                bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True,
                                                               isolate_users=True)
                                convert_to_mesh(name + "PlaneBorderCurve", name + "meshPlaneBorderCurve", 0.18)
                                battery_obj = bpy.data.objects.get(name + "shellBattery")
                                child_of_constraint = curve_obj.constraints.new(type='CHILD_OF')
                                child_of_constraint.target = battery_obj

                                plane_obj = bpy.data.objects.get(name + "batteryPlaneSnapCurve")
                                bpy.ops.object.select_all(action='DESELECT')
                                plane_obj.select_set(True)
                                bpy.context.view_layer.objects.active = plane_obj
                                bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True,
                                                               isolate_users=True)
                                child_of_constraint = plane_obj.constraints.new(type='CHILD_OF')
                                child_of_constraint.target = battery_obj
                                reset_after_bottom_curve_change()
                                bridge_and_refill()
                                bpy.ops.object.select_all(action='DESELECT')
                                battery_obj.select_set(True)
                                bpy.context.view_layer.objects.active = battery_obj
                                battery_mouse_press = False
                        else:
                            if battery_mouse_press:
                                plane_obj = bpy.data.objects.get(name + "batteryPlaneSnapCurve")
                                bpy.ops.object.select_all(action='DESELECT')
                                plane_obj.select_set(True)
                                bpy.context.view_layer.objects.active = plane_obj
                                bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True,
                                                               isolate_users=True)
                                child_of_constraint = plane_obj.constraints.new(type='CHILD_OF')
                                battery_obj = bpy.data.objects.get(name + "shellBattery")
                                child_of_constraint.target = battery_obj
                                bpy.ops.object.select_all(action='DESELECT')
                                battery_obj.select_set(True)
                                bpy.context.view_layer.objects.active = battery_obj
                                battery_mouse_press = False

                return {'PASS_THROUGH'}

            # 模式切换，结束modal
            elif(bpy.context.scene.muJuTypeEnum != "OP3"):
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(TEST_OT_shell_switch.__timer)
                    op_cls.__timer = None
                set_shell_modal_start(False)
                if not get_is_collision_finish():
                    set_is_collision_finish(True)
                print('shellcanalqiehuan finish')
                return {'FINISHED'}

            # 鼠标在区域外
            else:
                if (name == '右耳' and mouse_index != -1):
                    mouse_index = -1
                if (name == '左耳' and mouse_indexL != -1):
                    mouse_indexL = -1
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(TEST_OT_shell_switch.__timer)
                    op_cls.__timer = None
                set_shell_modal_start(False)
                if not get_is_collision_finish():
                    set_is_collision_finish(True)
                if (not get_point_qiehuan_modal_start() and not get_drag_curve_modal_start()
                        and not get_smooth_curve_modal_start()):
                    set_switch_time(None)
                print('shellcanalqiehuan finish')
                return {'FINISHED'}
            return {'PASS_THROUGH'}


_classes = [
    TEST_OT_shell_switch
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)



def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)