from asyncio import Handle
from venv import create
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re
import os
import time
from .tool import *
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running,\
    get_mirror_context, set_mirror_context, get_process_var_list
from .register_tool import unregister_tools
from .global_manager import global_manager
import math
from .back_and_forward import record_state, backup_state, forward_state

prev_on_hard_support = False  # 判断鼠标在模型上与否的状态是否改变
prev_on_hard_supportL = False

prev_on_soft_support = False  # 判断鼠标在模型上与否的状态是否改变
prev_on_soft_supportL = False

prev_on_sphere = False        #判断鼠标是否在附件球体上
prev_on_sphereL = False

prev_on_object = False        #判断鼠标在模型上与否的状态是否改变
prev_on_objectL = False

is_add_support = False        #是否添加过支撑,只能添加一个支撑
is_add_supportL = False
is_on_rotate = False          #是否处于旋转的鼠标状态,用于 附件三维旋转鼠标行为和附件平面旋转拖动鼠标行为之间的切换
is_on_rotateL = False

prev_location_x = 0           #记录支撑位置
prev_location_y = 0
prev_location_z = 0
prev_rotation_x = 0
prev_rotation_y = 0
prev_rotation_z = 0

prev_location_xL = 0
prev_location_yL = 0
prev_location_zL = 0
prev_rotation_xL = 0
prev_rotation_yL = 0
prev_rotation_zL = 0

support_enum = "OP1"           #支撑类型
support_enumL = "OP1"
support_offset = 0             #支撑偏移量
support_offsetL = 0

is_supportAdd_modal_start = False
is_supportAdd_modal_startL = False


def register_support_globals():
    global is_add_support, is_add_supportL
    global is_on_rotate, is_on_rotateL
    global prev_location_x, prev_location_y, prev_location_z
    global prev_rotation_x, prev_rotation_y, prev_rotation_z
    global prev_location_xL, prev_location_yL, prev_location_zL
    global prev_rotation_xL, prev_rotation_yL, prev_rotation_zL
    global support_enum, support_enumL, support_offset, support_offsetL
    global_manager.register("is_add_support", is_add_support)
    global_manager.register("is_add_supportL", is_add_supportL)
    global_manager.register("is_on_rotate", is_on_rotate)
    global_manager.register("is_on_rotateL", is_on_rotateL)
    global_manager.register("prev_location_x", prev_location_x)
    global_manager.register("prev_location_y", prev_location_y)
    global_manager.register("prev_location_z", prev_location_z)
    global_manager.register("prev_rotation_x", prev_rotation_x)
    global_manager.register("prev_rotation_y", prev_rotation_y)
    global_manager.register("prev_rotation_z", prev_rotation_z)
    global_manager.register("prev_location_xL", prev_location_xL)
    global_manager.register("prev_location_yL", prev_location_yL)
    global_manager.register("prev_location_zL", prev_location_zL)
    global_manager.register("prev_rotation_xL", prev_rotation_xL)
    global_manager.register("prev_rotation_yL", prev_rotation_yL)
    global_manager.register("prev_rotation_zL", prev_rotation_zL)
    global_manager.register("support_enum", support_enum)
    global_manager.register("support_enumL", support_enumL)
    global_manager.register("support_offset", support_offset)
    global_manager.register("support_offsetL", support_offsetL)


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


# 判断鼠标是否在物体上,硬耳膜支撑
def is_mouse_on_hard_support(context, event):
    name = bpy.context.scene.leftWindowObj + "Cone"
    obj = bpy.data.objects.get(name)
    if(obj != None):
        is_on_object = False  # 初始化变量

        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
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

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    is_on_object = True  # 如果发生交叉，将变量设为True
        return is_on_object
    return False


# 判断鼠标状态是否发生改变,硬耳膜支撑
def is_changed_hard_support(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "Cone"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_hard_support  # 之前鼠标是否在物体上
        global prev_on_hard_supportL
        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
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

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    curr_on_object = True  # 如果发生交叉，将变量设为True
        if ori_name == '右耳':
            if (curr_on_object != prev_on_hard_support):
                prev_on_hard_support = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_hard_supportL):
                prev_on_hard_supportL = curr_on_object
                return True
            else:
                return False

    return False

# 判断鼠标是否在物体上,软耳膜支撑
def is_mouse_on_soft_support(context, event):
    name = bpy.context.scene.leftWindowObj
    name_outer = name + "SoftSupportOuter"
    name_inside = name + "SoftSupportInside"
    cylinder_outer_obj = bpy.data.objects.get(name_outer)
    cylinder_inside_obj = bpy.data.objects.get(name_inside)
    if (cylinder_outer_obj != None and cylinder_inside_obj != None):
        is_on_object = False  # 初始化变量

        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
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

        # 确定光线和对象的相交
        mwi = cylinder_outer_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        # 确定光线和对象的相交
        mwi1 = cylinder_inside_obj.matrix_world.inverted()
        mwi_start1 = mwi1 @ start
        mwi_end1 = mwi1 @ end
        mwi_dir1 = mwi_end1 - mwi_start1

        if cylinder_outer_obj.type == 'MESH' and cylinder_inside_obj.type == 'MESH':
                mesh = cylinder_outer_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                mesh1 = cylinder_inside_obj.data
                bm1 = bmesh.new()
                bm1.from_mesh(mesh1)
                tree1 = mathutils.bvhtree.BVHTree.FromBMesh(bm1)

                _, _, fidx1, _ = tree1.ray_cast(mwi_start1, mwi_dir1, 2000.0)

                if (fidx is not None) or (fidx1 is not None):
                    is_on_object = True  # 如果发生交叉，将变量设为True
        return is_on_object
    return False


# 判断鼠标状态是否发生改变,软耳膜支撑
def is_changed_soft_support(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "SoftSupportOuter"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_soft_support  # 之前鼠标是否在物体上
        global prev_on_soft_supportL
        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
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

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    curr_on_object = True  # 如果发生交叉，将变量设为True
        if ori_name == '右耳':
            if (curr_on_object != prev_on_soft_support):
                prev_on_soft_support = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_soft_supportL):
                prev_on_soft_supportL = curr_on_object
                return True
            else:
                return False

    return False

# 判断鼠标是否在支撑旋转圆球上
def is_mouse_on_sphere(context, event):
    name = bpy.context.scene.leftWindowObj
    plane_name = name + 'Plane'
    plane_obj = bpy.data.objects.get(plane_name)
    if (plane_obj != None):
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        region, space = get_region_and_space(
            context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
        )
        rv3d = space.region_3d
        coord_3d = plane_obj.location
        # 将三维坐标转换为二维坐标
        coord_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, coord_3d)
        if (coord_2d != None):
            plane_x, plane_y = coord_2d
            dis = math.sqrt(math.fabs(plane_x - mouse_x) ** 2 + math.fabs(plane_y - mouse_y) ** 2)
            if (dis <= 372):
                return True
            else:
                return False
    return False


# 判断鼠标状态是否发生改变,圆球
def is_changed_sphere(context, event):
    global prev_on_sphere   # 之前鼠标是否在物体上
    global prev_on_sphereL  # 之前鼠标是否在物体上

    name = bpy.context.scene.leftWindowObj
    curr_on_object = is_mouse_on_sphere(context, event)

    if name == '右耳':
        if (curr_on_object != prev_on_sphere):
            prev_on_sphere = curr_on_object
            return True
        else:
            return False
    elif name == '左耳':
        if (curr_on_object != prev_on_sphereL):
            prev_on_sphereL = curr_on_object
            return True
        else:
            return False

# 判断鼠标是否在物体上,模型
def is_mouse_on_object(context, event):
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    if(obj != None):
        is_on_object = False  # 初始化变量

        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
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

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    is_on_object = True  # 如果发生交叉，将变量设为True
        return is_on_object
    return False


# 判断鼠标状态是否发生改变,模型
def is_changed(context, event):
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    if(obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_object  # 之前鼠标是否在物体上
        global prev_on_objectL
        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
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

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    curr_on_object = True  # 如果发生交叉，将变量设为True
        if name == '右耳':
            if (curr_on_object != prev_on_object):
                prev_on_object = curr_on_object
                return True
            else:
                return False
        elif name == '左耳':
            if (curr_on_object != prev_on_objectL):
                prev_on_objectL = curr_on_object
                return True
            else:
                return False
    return False




#获取鼠标在右耳上的坐标
def cal_co(context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :return: 相交的坐标
    '''

    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]
    co = []

    # 获取鼠标光标的区域坐标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
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

            co, normal, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None and normal is not None:
                return co, normal  # 如果发生交叉，返回坐标的值

    return -1, -1

def recover_hard_support():
    name = bpy.context.scene.leftWindowObj
    hard_support_obj = bpy.data.objects.get(name + "Cone")
    cone_compare_offset_obj = bpy.data.objects.get(name + "ConeOffsetCompare")
    cone_compare_offset_obj.hide_set(False)
    plane_obj = bpy.data.objects.get(name + "Plane")
    plane_obj.location = (0, 0, 1)
    plane_obj.rotation_euler = (0, 0, 0)
    bpy.ops.object.select_all(action='DESELECT')
    hard_support_obj.select_set(True)
    cone_compare_offset_obj.select_set(True)
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    hard_support_obj.select_set(False)
    cone_compare_offset_obj.select_set(False)
    cone_compare_offset_obj.hide_set(True)


def recover_soft_support():
    name = bpy.context.scene.leftWindowObj
    soft_support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
    soft_support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
    soft_support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
    soft_support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
    soft_support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
    soft_support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
    bpy.ops.object.select_all(action='DESELECT')
    soft_support_inner_obj.select_set(True)
    soft_support_inside_obj.select_set(True)
    soft_support_outer_obj.select_set(True)
    bpy.context.view_layer.objects.active = soft_support_outer_obj
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    # soft_support_inner_obj.select_set(False)
    # soft_support_inside_obj.select_set(False)

    # 将排气孔内外壁,内外壁对比物和平面绑定为一组,平面为父物体,提交时统一处理
    plane_obj = bpy.data.objects.get(name + "Plane")
    plane_obj.location = (-100, -100, 1)
    plane_obj.rotation_euler = (0, 0, 0)
    soft_support_inner_offset_compare_obj.hide_set(False)
    soft_support_outer_offset_compare_obj.hide_set(False)
    soft_support_inside_offset_compare_obj.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    soft_support_outer_offset_compare_obj.select_set(True)
    soft_support_inner_offset_compare_obj.select_set(True)
    soft_support_inside_offset_compare_obj.select_set(True)
    soft_support_outer_obj.select_set(True)
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    soft_support_outer_obj.select_set(False)
    soft_support_outer_offset_compare_obj.select_set(False)
    soft_support_inner_offset_compare_obj.select_set(False)
    soft_support_inside_offset_compare_obj.select_set(False)
    # 内外壁对比物隐藏
    soft_support_outer_offset_compare_obj.hide_set(True)
    soft_support_inner_offset_compare_obj.hide_set(True)
    soft_support_inside_offset_compare_obj.hide_set(True)
     

def recover_support():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global support_enum
    global support_offset
    global is_add_support
    global prev_location_xL
    global prev_location_yL
    global prev_location_zL
    global prev_rotation_xL
    global prev_rotation_yL
    global prev_rotation_zL
    global support_enumL
    global support_offsetL
    global is_add_supportL
    global is_on_rotate
    global is_on_rotateL
   
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if (is_add_support == True):
            if support_enum == "OP1":
                recover_hard_support()
            elif support_enum == "OP2":
               recover_soft_support()
            plane_obj = bpy.data.objects.get(name + "Plane")
            plane_obj.location[0] = prev_location_x
            plane_obj.location[1] = prev_location_y
            plane_obj.location[2] = prev_location_z
            plane_obj.rotation_euler[0] = prev_rotation_x
            plane_obj.rotation_euler[1] = prev_rotation_y
            plane_obj.rotation_euler[2] = prev_rotation_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")
    elif name == '左耳':
        if (is_add_supportL == True):
            if support_enumL == "OP1":
                recover_hard_support()
            elif support_enumL == "OP2":
                recover_soft_support()
            plane_obj = bpy.data.objects.get(name + "Plane")
            plane_obj.location[0] = prev_location_xL
            plane_obj.location[1] = prev_location_yL
            plane_obj.location[2] = prev_location_zL
            plane_obj.rotation_euler[0] = prev_rotation_xL
            plane_obj.rotation_euler[1] = prev_rotation_yL
            plane_obj.rotation_euler[2] = prev_rotation_zL
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")


def support_forward():
    forward_state()
    recover_support()


def support_backup():
    backup_state()
    recover_support()


def support_fit_rotate(normal,location):
    '''
    将支撑移动到位置location并将连界面与向量normal对齐垂直
    '''
    #获取支撑平面(支撑的父物体)
    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    #新建一个空物体根据向量normal建立一个局部坐标系
    empty = bpy.data.objects.new("CoordinateSystem", None)
    bpy.context.collection.objects.link(empty)
    empty.location = (0, 0, 0)
    rotation_matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()  # 将法线作为局部坐标系的z轴
    empty.matrix_world = rotation_matrix
    # 记录该局部坐标系在全局坐标系中的角度并将该空物体删除
    empty_rotation_x = empty.rotation_euler[0]
    empty_rotation_y = empty.rotation_euler[1]
    empty_rotation_z = empty.rotation_euler[2]
    bpy.data.objects.remove(empty, do_unlink=True)
    # 将支撑摆正对齐
    if(plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z

def initialSupportTransparency():
    newColor("SupportTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质
    # mat = newShader("SupportTransparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01

def frontToSupport():
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_on_rotate = False
    elif (name == "左耳"):
        is_on_rotateL = False

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        name = bpy.context.scene.leftWindowObj
        castingname = name + "CastingCompare"
        if (selected_obj.name == name + "SupportReset" or selected_obj.name == castingname + "SupportReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)



    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SupportReset"
    bpy.context.collection.objects.link(duplicate_obj)
    if (name == "右耳"):
        moveToRight(duplicate_obj)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)


    #若当前模型为软耳膜经过铸造法之后,复制出一份模型用于还原铸造法内壁
    castingname = name + "CastingCompare"
    casting_obj = bpy.data.objects.get(castingname)
    if(casting_obj != None):
        duplicate_obj1 = casting_obj.copy()
        duplicate_obj1.data = casting_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = castingname + "SupportReset"
        bpy.context.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)
        duplicate_obj1.hide_set(True)


    supportInitial()

def frontFromSupport():
    supportSaveInfo()
    name = bpy.context.scene.leftWindowObj
    hard_support_obj = bpy.data.objects.get(name + "Cone")
    hard_support_offset_compare_obj = bpy.data.objects.get(name + "ConeOffsetCompare")
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    soft_support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
    soft_support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
    soft_support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
    soft_support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
    soft_support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
    soft_support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (hard_support_obj != None):
        bpy.data.objects.remove(hard_support_obj, do_unlink=True)
    if (hard_support_offset_compare_obj != None):
        bpy.data.objects.remove(hard_support_offset_compare_obj, do_unlink=True)
    if (hard_support_compare_obj != None):
        bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
    if (soft_support_inner_obj != None):
        bpy.data.objects.remove(soft_support_inner_obj, do_unlink=True)
    if (soft_support_outer_obj != None):
        bpy.data.objects.remove(soft_support_outer_obj, do_unlink=True)
    if (soft_support_inside_obj != None):
        bpy.data.objects.remove(soft_support_inside_obj, do_unlink=True)
    if (soft_support_inner_offset_compare_obj != None):
        bpy.data.objects.remove(soft_support_inner_offset_compare_obj, do_unlink=True)
    if (soft_support_outer_offset_compare_obj != None):
        bpy.data.objects.remove(soft_support_outer_offset_compare_obj, do_unlink=True)
    if (soft_support_inside_offset_compare_obj != None):
        bpy.data.objects.remove(soft_support_inside_offset_compare_obj, do_unlink=True)
    if (soft_support_compare_obj != None):
        bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    resetname = name + "SupportReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if (name == "右耳"):
        moveToRight(duplicate_obj)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    # 若当前模型为软耳膜经过铸造法之后,通过进入模块时复制出一份模型还原铸造法内壁
    castingname = name + "CastingCompare"
    casting_obj = bpy.data.objects.get(castingname)
    if(casting_obj != None):
        castingresetname = castingname + "SupportReset"
        ori_casting_obj = bpy.data.objects.get(castingresetname)
        if (ori_casting_obj == None):
            ori_casting_obj = bpy.data.objects.get(name + "CastingCompareLast")
        bpy.data.objects.remove(casting_obj, do_unlink=True)
        duplicate_obj1 = ori_casting_obj.copy()
        duplicate_obj1.data = ori_casting_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = castingname
        bpy.context.scene.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)
        duplicate_obj1.select_set(False)

        all_objs = bpy.data.objects
        for selected_obj in all_objs:
            if (selected_obj.name == name + "SupportReset" or selected_obj.name == name + "SupportLast"
                    or selected_obj.name == castingname + "SupportReset" or selected_obj.name == castingname + "SupportLast"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

def backToSupport():
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_on_rotate = False
    elif (name == "左耳"):
        is_on_rotateL = False
    # 将后续模块中的reset和last都删除
    name = bpy.context.scene.leftWindowObj
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
    if (sprue_reset != None):
        bpy.data.objects.remove(sprue_reset, do_unlink=True)
    if (sprue_last != None):
        bpy.data.objects.remove(sprue_last, do_unlink=True)
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
    #将右耳模型重置  若存在铸造法,则将铸造法中的内部红色对比物也重置
    exist_SupportReset = False
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SupportReset"):
            exist_SupportReset = True
    if (exist_SupportReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "SupportReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        # 若当前模型为软耳膜经过铸造法之后,通过进入模块时复制出一份模型还原铸造法内壁
        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects.get(castingname)
        if (casting_obj != None):
            castingresetname = castingname + "SupportReset"
            ori_casting_obj = bpy.data.objects.get(castingresetname)
            if (ori_casting_obj == None):
                ori_casting_obj = bpy.data.objects.get(name + "CastingCompareLast")
            if(ori_casting_obj != None):
                bpy.data.objects.remove(casting_obj, do_unlink=True)
                duplicate_obj1 = ori_casting_obj.copy()
                duplicate_obj1.data = ori_casting_obj.data.copy()
                duplicate_obj1.animation_data_clear()
                duplicate_obj1.name = castingname
                bpy.context.scene.collection.objects.link(duplicate_obj1)
                if (name == "右耳"):
                    moveToRight(duplicate_obj1)
                elif (name == "左耳"):
                    moveToLeft(duplicate_obj1)
                duplicate_obj1.select_set(False)

        supportInitial()
    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "CastingLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "LabelLast") != None):
            lastname = name + "LabelLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "HandleLast") != None):
            lastname = name + "HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "MouldLast") != None):
            lastname = name + "MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "QieGeLast") != None):
            lastname = name + "QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "LocalThickLast") != None):
            lastname = name + "LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = name + "DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        # 若当前模型为软耳膜经过铸造法之后,通过进入模块时复制出一份模型还原铸造法内壁
        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects.get(castingname)
        if (casting_obj != None):
            castingresetname = castingname + "SupportReset"
            ori_casting_obj = bpy.data.objects.get(castingresetname)
            if (ori_casting_obj == None):
                ori_casting_obj = bpy.data.objects.get(name + "CastingCompareLast")
            if (ori_casting_obj != None):
                bpy.data.objects.remove(casting_obj, do_unlink=True)
                duplicate_obj1 = ori_casting_obj.copy()
                duplicate_obj1.data = ori_casting_obj.data.copy()
                duplicate_obj1.animation_data_clear()
                duplicate_obj1.name = castingname
                bpy.context.scene.collection.objects.link(duplicate_obj1)
                if (name == "右耳"):
                    moveToRight(duplicate_obj1)
                elif (name == "左耳"):
                    moveToLeft(duplicate_obj1)
                duplicate_obj1.select_set(False)



        supportInitial()

def backFromSupport():
    support_enum = bpy.context.scene.zhiChengTypeEnum
    support_enumL = bpy.context.scene.zhiChengTypeEnumL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        supportSaveInfo()
        if support_enum == "OP1":
            hardSupportSubmit()
        elif support_enum == "OP2":
            softSupportSubmit()
    elif name == '左耳':
        supportSaveInfo()
        if support_enumL == "OP1":
            hardSupportSubmit()
        elif support_enumL == "OP2":
            softSupportSubmit()


    #根据当前物体复制一份用于生成SupportLast
    name = bpy.context.scene.leftWindowObj
    support_last_obj = bpy.data.objects.get(name + "SupportLast")
    if(support_last_obj != None):
        bpy.data.objects.remove(support_last_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SupportLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    # 根据当前物体复制一份用于生成CastingCompareSupportLast
    name = bpy.context.scene.leftWindowObj
    casting_compare_name = name + "CastingCompare"
    casting_obj = bpy.data.objects.get(casting_compare_name)
    if(casting_obj != None):
        casting_last_obj = bpy.data.objects.get(name + "CastingCompareSupportLast")
        if (casting_last_obj != None):
            bpy.data.objects.remove(casting_last_obj, do_unlink=True)
        name = bpy.context.scene.leftWindowObj
        duplicate_obj1 = casting_obj.copy()
        duplicate_obj1.data = casting_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = casting_compare_name + "SupportLast"
        bpy.context.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)
        duplicate_obj1.hide_set(True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def createHardMouldSupport():
    '''
        用平面切去圆锥的一角，创建出硬耳膜支撑
    '''
    # 导入硬耳膜支撑模型
    script_dir = os.path.dirname(os.path.realpath(__file__))
    relative_path1 = os.path.join(script_dir, "stl\\HardSupport.stl")
    relative_path2 = os.path.join(script_dir, "stl\\HardSupport.stl")
    bpy.ops.wm.stl_import(filepath=relative_path1)
    bpy.ops.wm.stl_import(filepath=relative_path2)
    #添加支撑的父物体平面
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 1), scale=(1, 1, 1))


    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get("Plane")
    plane_obj.name = planename
    conename = name + "Cone"
    cone_obj = bpy.data.objects.get("HardSupport")
    cone_obj.name = conename
    coneoffsetname = conename + "OffsetCompare"
    cone_compare_offset_obj = bpy.data.objects.get("HardSupport.001")
    cone_compare_offset_obj.name = coneoffsetname
    if (name == "右耳"):
        moveToRight(plane_obj)
        moveToRight(cone_obj)
        moveToRight(cone_compare_offset_obj)
    elif (name == "左耳"):
        moveToLeft(plane_obj)
        moveToLeft(cone_obj)
        moveToLeft(cone_compare_offset_obj)

    # 为硬耳膜支撑添加红色材质
    red_material = newColor("Red", 1, 0, 0, 0, 1)
    cone_obj.select_set(True)
    bpy.context.view_layer.objects.active = cone_obj
    cone_obj.data.materials.clear()
    cone_obj.data.materials.append(red_material)
    # 为平面添加透明材质
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    initialSupportTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['SupportTransparency'])

    # 将硬耳膜支撑和硬耳膜支撑对比物绑定到平面上
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    cone_obj.select_set(True)
    cone_compare_offset_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    cone_obj.select_set(False)
    cone_compare_offset_obj.select_set(False)

    #将硬耳膜对比物隐藏
    cone_compare_offset_obj.hide_set(True)


def createSoftMouldSupport():
    '''
        导入模型,创建出软耳膜支撑
    '''
    #导入软耳膜支撑模型
    script_dir = os.path.dirname(os.path.realpath(__file__))
    relative_path1 = os.path.join(script_dir, "stl\\SoftSupportInner.stl")
    relative_path2 = os.path.join(script_dir, "stl\\SoftSupportInside.stl")
    relative_path3 = os.path.join(script_dir, "stl\\SoftSupportOuter.stl")
    bpy.ops.wm.stl_import(filepath=relative_path1)
    bpy.ops.wm.stl_import(filepath=relative_path2)
    bpy.ops.wm.stl_import(filepath=relative_path3)
    # 添加支撑的父物体平面
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', scale=(4, 4, 1))

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    support_inner_name = "SoftSupportInner"
    support_inner_obj = bpy.data.objects[support_inner_name]
    support_inner_obj.name = name + "SoftSupportInner"
    support_inner_obj.location[0] = -100
    support_inner_obj.location[1] = -100
    if (name == "右耳"):
        moveToRight(support_inner_obj)
    elif (name == "左耳"):
        moveToLeft(support_inner_obj)
    support_inside_name = "SoftSupportInside"
    support_inside_obj = bpy.data.objects[support_inside_name]
    support_inside_obj.name = name + "SoftSupportInside"
    support_inside_obj.location[0] = -100
    support_inside_obj.location[1] = -100
    if (name == "右耳"):
        moveToRight(support_inside_obj)
    elif (name == "左耳"):
        moveToLeft(support_inside_obj)
    support_outer_name = "SoftSupportOuter"
    support_outer_obj = bpy.data.objects[support_outer_name]
    support_outer_obj.name = name + "SoftSupportOuter"
    support_outer_obj.location[0] = -100
    support_outer_obj.location[1] = -100
    if (name == "右耳"):
        moveToRight(support_outer_obj)
    elif (name == "左耳"):
        moveToLeft(support_outer_obj)
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]
    plane_obj.name = name + "Plane"
    if (name == "右耳"):
        moveToRight(plane_obj)
    elif (name == "左耳"):
        moveToLeft(plane_obj)

    plane_obj.location[2] = 1                                    # 设置平面初始位置
    plane_obj.location[0] = -100
    plane_obj.location[1] = -100
    plane_obj.scale[0] = 4
    plane_obj.scale[1] = 4

    # 将软耳膜支撑外壁复制出一份用于后续操作(使用Bool Tool将字体铸造法和模型合并之后,字体铸造法模型会被自动删除)
    support_outer_name = support_outer_obj.name
    support_outer_obj_temp = support_outer_obj.copy()
    support_outer_obj_temp.data = support_outer_obj.data.copy()
    support_outer_obj_temp.animation_data_clear()
    bpy.context.collection.objects.link(support_outer_obj_temp)
    if (name == "右耳"):
        moveToRight(support_outer_obj_temp)
    elif (name == "左耳"):
        moveToLeft(support_outer_obj_temp)
    # 将平面切割为与圆柱截面相同的圆形
    bpy.ops.object.select_all(action='DESELECT')
    support_outer_obj.select_set(True)
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.booltool_auto_intersect()
    support_outer_obj_temp.name = support_outer_name
    support_outer_obj = support_outer_obj_temp
    # modifierPlaneCreate = plane_obj.modifiers.new(name="PlaneCreate", type='BOOLEAN')
    # modifierPlaneCreate.object = support_outer_obj
    # modifierPlaneCreate.operation = 'INTERSECT'
    # modifierPlaneCreate.solver = 'FAST'
    # bpy.ops.object.modifier_apply(modifier="PlaneCreate")




    # 为内外壁和内芯添加红色材质
    red_material = newColor("Red", 1, 0, 0, 0, 1)
    support_outer_obj.select_set(True)
    bpy.context.view_layer.objects.active = support_outer_obj
    support_outer_obj.data.materials.clear()
    support_outer_obj.data.materials.append(red_material)
    support_inside_obj.select_set(True)
    bpy.context.view_layer.objects.active = support_inside_obj
    support_inside_obj.data.materials.clear()
    support_inside_obj.data.materials.append(red_material)
    support_inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = support_inner_obj
    support_inner_obj.data.materials.clear()
    support_inner_obj.data.materials.append(red_material)
    # 为平面添加透明材质
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    initialSupportTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['SupportTransparency'])


    # 将内外壁复制出来一份作为参数offset偏移的对比物
    support_outer_compare_offset_obj = support_outer_obj.copy()
    support_outer_compare_offset_obj.data = support_outer_obj.data.copy()
    support_outer_compare_offset_obj.animation_data_clear()
    support_outer_compare_offset_obj.name = name + "SoftSupportOuterOffsetCompare"
    bpy.context.collection.objects.link(support_outer_compare_offset_obj)
    if (name == "右耳"):
        moveToRight(support_outer_compare_offset_obj)
    elif (name == "左耳"):
        moveToLeft(support_outer_compare_offset_obj)
    # support_outer_compare_offset_obj.hide_set(True)
    support_inner_compare_offset_obj = support_inner_obj.copy()
    support_inner_compare_offset_obj.data = support_inner_obj.data.copy()
    support_inner_compare_offset_obj.animation_data_clear()
    support_inner_compare_offset_obj.name = name + "SoftSupportInnerOffsetCompare"
    bpy.context.collection.objects.link(support_inner_compare_offset_obj)
    if (name == "右耳"):
        moveToRight(support_inner_compare_offset_obj)
    elif (name == "左耳"):
        moveToLeft(support_inner_compare_offset_obj)
    # support_inner_compare_offset_obj.hide_set(True)
    support_inside_compare_offset_obj = support_inside_obj.copy()
    support_inside_compare_offset_obj.data = support_inside_obj.data.copy()
    support_inside_compare_offset_obj.animation_data_clear()
    support_inside_compare_offset_obj.name = name + "SoftSupportInsideOffsetCompare"
    bpy.context.collection.objects.link(support_inside_compare_offset_obj)
    if (name == "右耳"):
        moveToRight(support_inside_compare_offset_obj)
    elif (name == "左耳"):
        moveToLeft(support_inside_compare_offset_obj)
    # support_inside_compare_offset_obj.hide_set(True)

    # 将排气孔内外壁和内芯绑定为一组,外壁作为父物体,提交时统一处理
    plane_obj.select_set(False)
    support_outer_obj.select_set(True)
    bpy.context.view_layer.objects.active = support_outer_obj
    support_inner_obj.select_set(True)
    support_inside_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    support_inner_obj.select_set(False)
    support_inside_obj.select_set(False)

    # 将排气孔内外壁,内外壁对比物和平面绑定为一组,平面为父物体,提交时统一处理
    support_outer_compare_offset_obj.select_set(True)
    support_inner_compare_offset_obj.select_set(True)
    support_inside_compare_offset_obj.select_set(True)
    support_outer_obj.select_set(True)
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    support_outer_obj.select_set(False)
    # 内外壁对比物隐藏
    support_outer_compare_offset_obj.hide_set(True)
    support_inner_compare_offset_obj.hide_set(True)
    support_inside_compare_offset_obj.hide_set(True)




def supportSaveInfo():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global support_enum
    global support_offset
    global prev_location_xL
    global prev_location_yL
    global prev_location_zL
    global prev_rotation_xL
    global prev_rotation_yL
    global prev_rotation_zL
    global support_enumL
    global support_offsetL

    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)

    # Helper: compare floats safely
    def _floats_different(a, b, tol=1e-6):
        try:
            return not math.isclose(a, b, rel_tol=0, abs_tol=tol)
        except Exception:
            return True

    if name == '右耳':
        # 仅在位置/旋转 发生变化时才更新并记录状态，避免重复写入
        cur_lx = cur_ly = cur_lz = cur_rx = cur_ry = cur_rz = None
        if plane_obj is not None:
            cur_lx = plane_obj.location[0]
            cur_ly = plane_obj.location[1]
            cur_lz = plane_obj.location[2]
            cur_rx = plane_obj.rotation_euler[0]
            cur_ry = plane_obj.rotation_euler[1]
            cur_rz = plane_obj.rotation_euler[2]
        cur_enum = bpy.context.scene.zhiChengTypeEnum
        cur_offset = bpy.context.scene.zhiChengOffset

        changed = False
        if plane_obj is not None:
            if _floats_different(prev_location_x, cur_lx) or _floats_different(prev_location_y, cur_ly) or _floats_different(prev_location_z, cur_lz):
                prev_location_x = cur_lx
                prev_location_y = cur_ly
                prev_location_z = cur_lz
                changed = True
            if _floats_different(prev_rotation_x, cur_rx) or _floats_different(prev_rotation_y, cur_ry) or _floats_different(prev_rotation_z, cur_rz):
                prev_rotation_x = cur_rx
                prev_rotation_y = cur_ry
                prev_rotation_z = cur_rz
                changed = True
            # if support_enum != cur_enum:
            #     support_enum = cur_enum
            #     changed = True
            # if _floats_different(support_offset, cur_offset):
            #     support_offset = cur_offset
            #     changed = True

        if changed:
            record_state()

    elif name == '左耳':
        cur_lx = cur_ly = cur_lz = cur_rx = cur_ry = cur_rz = None
        if (plane_obj != None):
            cur_lx = plane_obj.location[0]
            cur_ly = plane_obj.location[1]
            cur_lz = plane_obj.location[2]
            cur_rx = plane_obj.rotation_euler[0]
            cur_ry = plane_obj.rotation_euler[1]
            cur_rz = plane_obj.rotation_euler[2]
        cur_enum = bpy.context.scene.zhiChengTypeEnumL
        cur_offset = bpy.context.scene.zhiChengOffsetL

        changed = False
        if plane_obj is None:
            if support_enumL != cur_enum:
                support_enumL = cur_enum
                changed = True
            if _floats_different(support_offsetL, cur_offset):
                support_offsetL = cur_offset
                changed = True
        else:
            if _floats_different(prev_location_xL, cur_lx) or _floats_different(prev_location_yL, cur_ly) or _floats_different(prev_location_zL, cur_lz):
                prev_location_xL = cur_lx
                prev_location_yL = cur_ly
                prev_location_zL = cur_lz
                changed = True
            if _floats_different(prev_rotation_xL, cur_rx) or _floats_different(prev_rotation_yL, cur_ry) or _floats_different(prev_rotation_zL, cur_rz):
                prev_rotation_xL = cur_rx
                prev_rotation_yL = cur_ry
                prev_rotation_zL = cur_rz
                changed = True
            # if support_enumL != cur_enum:
            #     support_enumL = cur_enum
            #     changed = True
            # if _floats_different(support_offsetL, cur_offset):
            #     support_offsetL = cur_offset
            #     changed = True

        if changed:
            record_state()



def supportInitial():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global support_enum
    global support_offset
    global is_add_support
    global prev_location_xL
    global prev_location_yL
    global prev_location_zL
    global prev_rotation_xL
    global prev_rotation_yL
    global prev_rotation_zL
    global support_enumL
    global support_offsetL
    global is_add_supportL
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj

    if name == '右耳':
        if (is_add_support == True):
            addSupport()
            # 将Plane激活并选中
            name = bpy.context.scene.leftWindowObj
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            plane_obj.location[0] = prev_location_x
            plane_obj.location[1] = prev_location_y
            plane_obj.location[2] = prev_location_z
            plane_obj.rotation_euler[0] = prev_rotation_x
            plane_obj.rotation_euler[1] = prev_rotation_y
            plane_obj.rotation_euler[2] = prev_rotation_z
            bpy.context.scene.needrecord = False
            bpy.context.scene.zhiChengOffset = support_offset
            bpy.context.scene.needrecord = True
            bpy.ops.object.supportswitch('INVOKE_DEFAULT')
            bpy.ops.object.supportadd('INVOKE_DEFAULT')
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")
    elif name == '左耳':
        if (is_add_supportL == True):
            addSupport()
            # 将Plane激活并选中
            name = bpy.context.scene.leftWindowObj
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            plane_obj.location[0] = prev_location_xL
            plane_obj.location[1] = prev_location_yL
            plane_obj.location[2] = prev_location_zL
            plane_obj.rotation_euler[0] = prev_rotation_xL
            plane_obj.rotation_euler[1] = prev_rotation_yL
            plane_obj.rotation_euler[2] = prev_rotation_zL
            bpy.context.scene.needrecord = False
            bpy.context.scene.zhiChengOffsetL= support_offsetL
            bpy.context.scene.needrecord = True
            bpy.ops.object.supportswitch('INVOKE_DEFAULT')
            bpy.ops.object.supportadd('INVOKE_DEFAULT')
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")

    #将旋转中心设置为左右耳模型
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj







def supportReset():
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_on_rotate = False
    elif (name == "左耳"):
        is_on_rotateL = False
    # 存在未提交支撑时,删除支撑相关物体
    name = bpy.context.scene.leftWindowObj
    hard_support_obj = bpy.data.objects.get(name + "Cone")
    hard_support_offset_compare_obj = bpy.data.objects.get(name + "ConeOffsetCompare")
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    soft_support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
    soft_support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
    soft_support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
    soft_support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
    soft_support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
    soft_support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (hard_support_obj != None):
        bpy.data.objects.remove(hard_support_obj, do_unlink=True)
    if (hard_support_offset_compare_obj != None):
        bpy.data.objects.remove(hard_support_offset_compare_obj, do_unlink=True)
    if (hard_support_compare_obj != None):
        bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
    if (soft_support_inner_obj != None):
        bpy.data.objects.remove(soft_support_inner_obj, do_unlink=True)
    if (soft_support_outer_obj != None):
        bpy.data.objects.remove(soft_support_outer_obj, do_unlink=True)
    if (soft_support_inside_obj != None):
        bpy.data.objects.remove(soft_support_inside_obj, do_unlink=True)
    if (soft_support_inner_offset_compare_obj != None):
        bpy.data.objects.remove(soft_support_inner_offset_compare_obj, do_unlink=True)
    if (soft_support_outer_offset_compare_obj != None):
        bpy.data.objects.remove(soft_support_outer_offset_compare_obj, do_unlink=True)
    if (soft_support_inside_offset_compare_obj != None):
        bpy.data.objects.remove(soft_support_inside_offset_compare_obj, do_unlink=True)
    if (soft_support_compare_obj != None):
        bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    # 将SupportReset复制并替代当前操作模型
    name  = bpy.context.scene.leftWindowObj
    oriname = bpy.context.scene.leftWindowObj
    ori_obj = bpy.data.objects.get(oriname)
    copyname = oriname + "SupportReset"
    copy_obj = bpy.data.objects.get(copyname)
    if (ori_obj != None and copy_obj != None):
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = copy_obj.copy()
        duplicate_obj.data = copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj
    # 若当前模型为软耳膜经过铸造法之后,通过进入模块时复制出一份模型还原铸造法内壁
    castingname = name + "CastingCompare"
    casting_obj = bpy.data.objects.get(castingname)
    if(casting_obj != None):
        castingresetname = castingname + "SupportReset"
        ori_casting_obj = bpy.data.objects.get(castingresetname)
        if(ori_casting_obj == None):
            ori_casting_obj = bpy.data.objects.get( name + "CastingCompareLast")
        if(casting_obj != None and ori_casting_obj != None):
            bpy.data.objects.remove(casting_obj, do_unlink=True)
            duplicate_obj1 = ori_casting_obj.copy()
            duplicate_obj1.data = ori_casting_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = castingname
            bpy.context.scene.collection.objects.link(duplicate_obj1)
            if (name == "右耳"):
                moveToRight(duplicate_obj1)
            elif (name == "左耳"):
                moveToLeft(duplicate_obj1)
            duplicate_obj1.select_set(False)

def hardSupportSubmit():
    #  support_obj为支撑物体,  support_offset_compare为隐藏的支撑物体,用于偏移量参照,创建支撑时一同创建   support_compare则作为对比,因此support_obj在提交后会变透明
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    support_name = name + "Cone"
    support_offset_compare_name = name + "ConeOffsetCompare"
    support_obj = bpy.data.objects.get(support_name)
    support_offset_compare_obj = bpy.data.objects.get(support_offset_compare_name)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)

    #提交前保存参数
    supportSaveInfo()

    # 存在未提交的Support,SupportCompare和Plane时
    if (support_obj != None and plane_obj != None and support_offset_compare_obj != None):

        # bpy.context.view_layer.objects.active = obj

        # #由于支撑之前的模块存在布尔操作,会有其他顶点被选中,因此先将模型上选中顶点给取消选中
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.mode_set(mode='OBJECT')

        # # 将硬耳膜支撑与右耳模型做差集,得到硬耳膜支撑的对比物体。 # 由于硬耳膜支撑物体和透明的右耳外壳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比
        # # 将硬耳膜支撑复制一份用于布尔生成对比物
        # support_compare_name = name + "ConeCompare"
        # support_compare_obj = support_obj.copy()
        # support_compare_obj.data = support_obj.data.copy()
        # support_compare_obj.animation_data_clear()
        # bpy.context.collection.objects.link(support_compare_obj)
        # support_compare_obj.name = support_compare_name
        # if (name == "右耳"):
        #     moveToRight(support_compare_obj)
        # elif (name == "左耳"):
        #     moveToLeft(support_compare_obj)
        # # 将硬耳膜支撑对比物的位置移动到与硬耳膜支撑外壁的位置相同(由于硬耳膜支撑相关物体都在父物体平面下随着父物体的位置改变而改变,因此其位置信息仍为导入时的为位置,不能直接通过location设置其位置)
        # me = support_compare_obj.data
        # bm = bmesh.new()
        # bm.from_mesh(me)
        # bm.verts.ensure_lookup_table()
        # ori_sprue_me = support_obj.data
        # ori_sprue_bm = bmesh.new()
        # ori_sprue_bm.from_mesh(ori_sprue_me)
        # ori_sprue_bm.verts.ensure_lookup_table()
        # for vert in bm.verts:
        #     vert.co = ori_sprue_bm.verts[vert.index].co
        # bm.to_mesh(me)
        # bm.free()
        # ori_sprue_bm.free()
        # # 将复制出来的软耳膜支撑外壁对比物与右耳做布尔差集,将其切割为所需的形状
        # bpy.ops.object.select_all(action='DESELECT')
        # support_obj.select_set(True)
        # bpy.context.view_layer.objects.active = support_obj
        # modifierSprueCompareDifference = support_obj.modifiers.new(name="SupportCompareDifference",type='BOOLEAN')
        # modifierSprueCompareDifference.object = obj
        # modifierSprueCompareDifference.operation = 'DIFFERENCE'
        # modifierSprueCompareDifference.solver = 'FAST'
        # bpy.ops.object.modifier_apply(modifier="SupportCompareDifference",single_user=True)



        #将支撑与当前模型合并
        bpy.ops.object.select_all(action='DESELECT')
        # support_obj.select_set(True)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # bpy.ops.object.booltool_auto_union()
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = support_obj
        bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

        # bpy.data.objects.remove(plane_obj, do_unlink=True)
        # bpy.data.objects.remove(sphere_obj, do_unlink=True)
        # bpy.data.objects.remove(support_obj, do_unlink=True)

        # # 由于支撑物体和透明的右耳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比
        # bpy.ops.object.mode_set(mode='EDIT')
        # #布尔合并后的顶点会被选中,将这些顶点复制一份并分离为独立的物体
        # bpy.ops.mesh.duplicate()
        # bpy.ops.mesh.separate(type='SELECTED')
        # bpy.ops.object.mode_set(mode='OBJECT')
        # support_compare_obj = bpy.data.objects.get(name + ".001")
        # if(support_compare_obj != None):
        #     support_compare_obj.name = name + "ConeCompare"
        #     yellow_material = newColor("SupportCompare", 1, 0.319, 0.133, 0, 1)
        #     support_compare_obj.data.materials.clear()
        #     support_compare_obj.data.materials.append(yellow_material)
        #     if (name == "右耳"):
        #         moveToRight(support_compare_obj)
        #     elif (name == "左耳"):
        #         moveToLeft(support_compare_obj)

        # # 删除父物体平面之后,硬耳膜支撑对比物体会恢复到初始位置,需要保存为位置信息
        # bpy.ops.object.select_all(action='DESELECT')
        # plane_obj.select_set(True)
        # bpy.context.view_layer.objects.active = plane_obj
        # bpy.ops.view3d.snap_cursor_to_active()                            # 将3D游标位置设置为激活物体的原点位置
        # bpy.ops.object.select_all(action='DESELECT')
        # support_compare_obj.select_set(True)
        # bpy.context.view_layer.objects.active = support_compare_obj
        # bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')  # 将硬耳膜支撑对比物的原点位置设置为游标位置,即平面的原点位置
        # support_compare_obj.location = plane_obj.location                 # 将硬耳膜支撑对比物体位置信息设置为平面位置信息
        # support_compare_obj.rotation_euler = plane_obj.rotation_euler
        # support_compare_obj.rotation_euler[0] += math.pi
        # bpy.ops.view3d.snap_cursor_to_center()                             # 将游标位置恢复为世界中心
        # support_compare_yellow_material = newColor("SupportCompareYellow", 1, 0.319, 0.133, 1,0.4)  # 将硬耳膜支撑对比物设置为模型的颜色
        # support_compare_obj.data.materials.clear()
        # support_compare_obj.data.materials.append(support_compare_yellow_material)


        #删除硬耳膜支撑相关物体
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(support_obj, do_unlink=True)
        bpy.data.objects.remove(support_offset_compare_obj, do_unlink=True)

        # 将旋转中心设置为右耳
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # 合并后Support会被去除材质,因此需要重置一下模型颜色为黄色
        utils_re_color(name, (1, 0.319, 0.133))
        if obj.vertex_groups.get('TransformBorder') != None:
            transform_obj_name = bpy.context.scene.leftWindowObj + "SupportReset"
            transform_normal(transform_obj_name, [])




def softSupportSubmit():
    #  support_obj为排气孔物体,  support_offset_compare为隐藏的排气孔物体,用于偏移量参照,创建排气孔时一同创建   support_compare则作为对比,因为sprue_obj在提交后会变透明

    name = bpy.context.scene.leftWindowObj
    support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
    support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
    support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
    support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
    support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
    support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)

    obj_outer = bpy.data.objects.get(name)
    obj_inner = bpy.data.objects.get(name + "CastingCompare")


    # 存在未提交的SoftSupport,SoftSupportCompare和Plane时
    if (support_inner_obj != None and support_outer_obj != None and  support_inside_obj != None and plane_obj != None
            and  support_inner_offset_compare_obj != None and support_outer_offset_compare_obj != None
            and support_inside_offset_compare_obj != None and  obj_outer != None and obj_inner != None):


        #为软耳膜外部支撑添加顶点组保存 软耳膜外部支撑的边缘顶点
        #选中这些顶点补面,用于后续的布尔切割合并
        bpy.ops.object.select_all(action='DESELECT')
        support_outer_obj.select_set(True)
        bpy.context.view_layer.objects.active = support_outer_obj
        soft_support_outer_top_edge_vertex = support_outer_obj.vertex_groups.get("SoftSupportOuterTopEdge")
        if (soft_support_outer_top_edge_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="SoftSupportOuterTopEdge")
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_support_outer_top_edge_vertex = support_outer_obj.vertex_groups.new(name="SoftSupportOuterTopEdge")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.object.vertex_group_set_active(group="SoftSupportOuterTopEdge")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.edge_face_add()                        #选中这些顶点补面,将软耳膜外部支撑变为封闭物体用于后续的布尔切割合并
        bpy.ops.object.mode_set(mode='OBJECT')
        #为软耳膜内部支撑添加顶点组保存 软耳膜内部支撑的边缘顶点
        # 选中这些顶点补面,用于后续的布尔切割合并
        bpy.ops.object.select_all(action='DESELECT')
        support_inner_obj.select_set(True)
        bpy.context.view_layer.objects.active = support_inner_obj
        soft_support_inner_top_edge_vertex = support_inner_obj.vertex_groups.get("SoftSupportInnerTopEdge")
        if (soft_support_inner_top_edge_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="SoftSupportInnerTopEdge")
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_support_inner_top_edge_vertex = support_inner_obj.vertex_groups.new(name="SoftSupportInnerTopEdge")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.object.vertex_group_set_active(group="SoftSupportInnerTopEdge")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.edge_face_add()                        # 选中这些顶点补面,将软耳膜外部支撑变为封闭物体用于后续的布尔切割合并
        bpy.ops.object.mode_set(mode='OBJECT')


        #将软耳膜外部支撑与左右耳合并
        bpy.ops.object.select_all(action='DESELECT')
        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer
        bpy.ops.object.mode_set(mode='EDIT')                  #将模型上的顶点全部取消选中
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bool_modifier = obj_outer.modifiers.new(name="SoftSupportOuterUnionBooleanModifier", type='BOOLEAN')
        bool_modifier.operation = 'UNION'
        bool_modifier.solver = 'FAST'
        bool_modifier.object = support_outer_obj
        bpy.ops.object.modifier_apply(modifier="SoftSupportOuterUnionBooleanModifier", single_user=True)
        bpy.ops.object.mode_set(mode='EDIT')                  #布尔合并前左右耳模型上没有顶点被选中,支撑外壁上边缘被选中
        bpy.ops.mesh.delete(type='ONLY_FACE')                 #布尔合并后支撑外壁边缘顶点被选中,将面删除
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        #将软耳膜内部支撑与左右耳Casting合并
        bpy.ops.object.select_all(action='DESELECT')
        obj_inner.select_set(True)
        bpy.context.view_layer.objects.active = obj_inner
        bpy.ops.object.mode_set(mode='EDIT')                  #将模型上的顶点全部取消选中
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bool_modifier = obj_inner.modifiers.new(name="SoftSupportInnerUnionBooleanModifier", type='BOOLEAN')
        bool_modifier.operation = 'UNION'
        bool_modifier.solver = 'FAST'
        bool_modifier.object = support_inner_obj
        bpy.ops.object.modifier_apply(modifier="SoftSupportInnerUnionBooleanModifier", single_user=True)
        bpy.ops.object.mode_set(mode='EDIT')                  #布尔合并前左右耳模型上没有顶点被选中,支撑内壁上边缘被选中
        bpy.ops.mesh.delete(type='ONLY_FACE')                 #布尔合并后支撑内壁边缘顶点被选中,将面删除
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')



        # 删除软耳膜支撑相关物体
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(support_inner_obj, do_unlink=True)
        bpy.data.objects.remove(support_outer_obj, do_unlink=True)
        bpy.data.objects.remove(support_inside_obj, do_unlink=True)
        bpy.data.objects.remove(support_inner_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(support_outer_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(support_inside_offset_compare_obj, do_unlink=True)


        #将旋转中心设置为右耳
        bpy.ops.object.select_all(action='DESELECT')
        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer

        # 合并后Support会被去除材质,因此需要重置一下模型颜色为黄色
        utils_re_color(name, (1, 0.319, 0.133))



def addSupport():
    # 添加平面Plane和支撑Support
    support_enum = bpy.context.scene.zhiChengTypeEnum
    support_enumL = bpy.context.scene.zhiChengTypeEnumL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if support_enum == "OP1":
            createHardMouldSupport()
        elif support_enum == "OP2":
            createSoftMouldSupport()
    elif name == '左耳':
        if support_enumL == "OP1":
            createHardMouldSupport()
        elif support_enumL == "OP2":
            createSoftMouldSupport()


    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects[planename]

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    # 设置附件初始位置
    plane_obj.location[0] = 10
    plane_obj.location[1] = 10
    plane_obj.location[2] = 10



class SupportTest(bpy.types.Operator):
    bl_idname = "object.supporttestfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):
        createHardMouldSupport()
        return {'FINISHED'}

class SupportTest1(bpy.types.Operator):
    bl_idname = "object.supporttestfunc1"
    bl_label = "功能测试"

    def invoke(self, context, event):
        createSoftMouldSupport()
        return {'FINISHED'}

class SupportReset(bpy.types.Operator):
    bl_idname = "object.supportreset"
    bl_label = "支撑重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 76
        name = bpy.context.scene.leftWindowObj
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_add_support
        global is_add_supportL
        global is_on_rotate
        global is_on_rotateL
        if name == '右耳':
            is_add_support = False
            is_on_rotate = False
        elif name == '左耳':
            is_add_supportL = False
            is_on_rotateL = False

        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        supportSaveInfo()
        supportReset()
        bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")


class SupportAdd(bpy.types.Operator):
    bl_idname = "object.supportadd"
    bl_label = "添加支撑"

    def invoke(self, context, event):
        self.add_support(context, event)
        return {'FINISHED'}

        # name = bpy.context.scene.leftWindowObj
        # global is_add_support
        # global support_offset
        # global is_add_supportL
        # global support_offsetL
        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        #
        # if name == '右耳':
        #     if (not is_add_support):
        #         is_add_support = True
        #         addSupport()
        #         bpy.context.scene.zhiChengOffset = support_offset
        #         # 将Plane激活并选中
        #         name = bpy.context.scene.leftWindowObj
        #         planename = name + "Plane"
        #         plane_obj = bpy.data.objects.get(planename)
        #         cur_obj = bpy.data.objects.get(name)
        #         bpy.ops.object.select_all(action='DESELECT')
        #         plane_obj.select_set(True)
        #         bpy.context.view_layer.objects.active = plane_obj
        #         co, normal = cal_co(context, event)
        #         if (co != -1):
        #             support_fit_rotate(normal,co)
        #             # plane_obj.location = co
        #         bpy.ops.object.select_all(action='DESELECT')
        #         cur_obj.select_set(True)
        #         bpy.context.view_layer.objects.active = cur_obj
        # elif name == '左耳':
        #     if (not is_add_supportL):
        #         is_add_supportL = True
        #         addSupport()
        #         bpy.context.scene.zhiChengOffsetL = support_offsetL
        #         # 将Plane激活并选中
        #         name = bpy.context.scene.leftWindowObj
        #         planename = name + "Plane"
        #         plane_obj = bpy.data.objects.get(planename)
        #         cur_obj = bpy.data.objects.get(name)
        #         bpy.ops.object.select_all(action='DESELECT')
        #         plane_obj.select_set(True)
        #         bpy.context.view_layer.objects.active = plane_obj
        #         co, normal = cal_co(context, event)
        #         if (co != -1):
        #             support_fit_rotate(normal, co)
        #             # plane_obj.location = co
        #         bpy.ops.object.select_all(action='DESELECT')
        #         cur_obj.select_set(True)
        #         bpy.context.view_layer.objects.active = cur_obj
        #
        # if bpy.context.scene.var != 77:
        #     bpy.context.scene.var = 77
        #     context.window_manager.modal_handler_add(self)
        #     print("supportadd_modal_invoke")
        # return {'RUNNING_MODAL'}

    def add_support(self, context, event):
        name = bpy.context.scene.leftWindowObj
        global is_add_support
        global support_offset
        global is_add_supportL
        global support_offsetL

        if name == '右耳':
            if (not is_add_support):
                is_add_support = True
                addSupport()
                bpy.context.scene.needrecord = False
                bpy.context.scene.zhiChengOffset = support_offset
                bpy.context.scene.needrecord = True
                # 将Plane激活并选中
                name = bpy.context.scene.leftWindowObj
                planename = name + "Plane"
                plane_obj = bpy.data.objects.get(planename)
                cur_obj = bpy.data.objects.get(name)
                bpy.ops.object.select_all(action='DESELECT')
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                co, normal = cal_co(context, event)
                if (co != -1):
                    support_fit_rotate(normal, co)
                    # plane_obj.location = co
                bpy.ops.object.select_all(action='DESELECT')
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
        elif name == '左耳':
            if (not is_add_supportL):
                is_add_supportL = True
                addSupport()
                bpy.context.scene.needrecord = False
                bpy.context.scene.zhiChengOffsetL = support_offsetL
                bpy.context.scene.needrecord = True
                # 将Plane激活并选中
                name = bpy.context.scene.leftWindowObj
                planename = name + "Plane"
                plane_obj = bpy.data.objects.get(planename)
                cur_obj = bpy.data.objects.get(name)
                bpy.ops.object.select_all(action='DESELECT')
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                co, normal = cal_co(context, event)
                if (co != -1):
                    support_fit_rotate(normal, co)
                    # plane_obj.location = co
                bpy.ops.object.select_all(action='DESELECT')
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
        bpy.ops.object.supportswitch('INVOKE_DEFAULT')


    # def modal(self, context, event):
    #     global is_on_rotate
    #     global is_on_rotateL
    #     support_enum = bpy.context.scene.zhiChengTypeEnum
    #     support_enumL = bpy.context.scene.zhiChengTypeEnumL
    #     name = bpy.context.scene.leftWindowObj
    #     hard_support_name = name + "Cone"
    #     hard_support_obj = bpy.data.objects.get(hard_support_name)
    #     soft_support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
    #     soft_support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
    #     soft_support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
    #     soft_support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
    #     soft_support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
    #     soft_support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
    #     planename = name + "Plane"
    #     plane_obj = bpy.data.objects.get(planename)
    #     cur_obj_name = name
    #     cur_obj = bpy.data.objects.get(cur_obj_name)
    #     support_enum_cur = "OP1"
    #     is_on_rotate_cur = False
    #     if name == '右耳':
    #         support_enum_cur = support_enum
    #         is_on_rotate_cur = is_on_rotate
    #     elif name == '左耳':
    #         support_enum_cur = support_enumL
    #         is_on_rotate_cur = is_on_rotateL
    #     if bpy.context.scene.var == 77:
    #         if(not is_on_rotate_cur):
    #             if support_enum_cur == "OP1":
    #                 if(hard_support_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_hard_support(context, event) and (is_changed_hard_support(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         hard_support_obj.data.materials.clear()
    #                         hard_support_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_hard_support(context, event) and (is_changed(context, event) or is_changed_hard_support(context,event))):
    #                         # 调用hardSupport的鼠标行为
    #                         yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
    #                         hard_support_obj.data.materials.clear()
    #                         hard_support_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                     elif ((not is_mouse_on_object(context, event)) and (is_changed(context, event) or is_changed_hard_support(context,event))):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         hard_support_obj.data.materials.clear()
    #                         hard_support_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #             elif support_enum_cur == "OP2":
    #                 if(soft_support_inner_obj != None and soft_support_outer_obj != None and soft_support_inside_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_soft_support(context, event) and (is_changed_soft_support(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         # soft_support_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inner_obj
    #                         soft_support_inner_obj.data.materials.clear()
    #                         soft_support_inner_obj.data.materials.append(red_material)
    #                         # soft_support_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_outer_obj
    #                         soft_support_outer_obj.data.materials.clear()
    #                         soft_support_outer_obj.data.materials.append(red_material)
    #                         # soft_support_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inside_obj
    #                         soft_support_inside_obj.data.materials.clear()
    #                         soft_support_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_soft_support(context, event) and (is_changed_soft_support(context, event) or is_changed(context, event))):
    #                         # 调用softSupport的鼠标行为
    #                         yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
    #                         # soft_support_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inner_obj
    #                         soft_support_inner_obj.data.materials.clear()
    #                         soft_support_inner_obj.data.materials.append(yellow_material)
    #                         # soft_support_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_outer_obj
    #                         soft_support_outer_obj.data.materials.clear()
    #                         soft_support_outer_obj.data.materials.append(yellow_material)
    #                         # soft_support_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inside_obj
    #                         soft_support_inside_obj.data.materials.clear()
    #                         soft_support_inside_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                         soft_support_inner_obj.select_set(False)
    #                         soft_support_outer_obj.select_set(False)
    #                         soft_support_inside_obj.select_set(False)
    #                     elif ((not is_mouse_on_object(context, event)) and (is_changed_soft_support(context, event) or is_changed(context, event))):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         # soft_support_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inner_obj
    #                         soft_support_inner_obj.data.materials.clear()
    #                         soft_support_inner_obj.data.materials.append(red_material)
    #                         # soft_support_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_outer_obj
    #                         soft_support_outer_obj.data.materials.clear()
    #                         soft_support_outer_obj.data.materials.append(red_material)
    #                         # soft_support_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inside_obj
    #                         soft_support_inside_obj.data.materials.clear()
    #                         soft_support_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                         soft_support_inner_obj.select_set(False)
    #                         soft_support_outer_obj.select_set(False)
    #                         soft_support_inside_obj.select_set(False)
    #         if(is_on_rotate_cur):
    #             if support_enum_cur == "OP1":
    #                 if(hard_support_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
    #                             is_changed_sphere(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         hard_support_obj.data.materials.clear()
    #                         hard_support_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用hardSupport的三维旋转鼠标行为
    #                         yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
    #                         hard_support_obj.data.materials.clear()
    #                         hard_support_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                     elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         hard_support_obj.data.materials.clear()
    #                         hard_support_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #             elif support_enum_cur == "OP2":
    #                 if(soft_support_inner_obj != None and soft_support_outer_obj != None and soft_support_inside_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
    #                             is_changed_sphere(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         # soft_support_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inner_obj
    #                         soft_support_inner_obj.data.materials.clear()
    #                         soft_support_inner_obj.data.materials.append(red_material)
    #                         # soft_support_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_outer_obj
    #                         soft_support_outer_obj.data.materials.clear()
    #                         soft_support_outer_obj.data.materials.append(red_material)
    #                         # soft_support_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inside_obj
    #                         soft_support_inside_obj.data.materials.clear()
    #                         soft_support_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用softSupport的鼠标行为
    #                         yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
    #                         # soft_support_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inner_obj
    #                         soft_support_inner_obj.data.materials.clear()
    #                         soft_support_inner_obj.data.materials.append(yellow_material)
    #                         # soft_support_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_outer_obj
    #                         soft_support_outer_obj.data.materials.clear()
    #                         soft_support_outer_obj.data.materials.append(yellow_material)
    #                         # soft_support_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inside_obj
    #                         soft_support_inside_obj.data.materials.clear()
    #                         soft_support_inside_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                         soft_support_inner_obj.select_set(False)
    #                         soft_support_outer_obj.select_set(False)
    #                         soft_support_inside_obj.select_set(False)
    #                     elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("Red", 1, 0, 0, 0, 1)
    #                         # soft_support_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inner_obj
    #                         soft_support_inner_obj.data.materials.clear()
    #                         soft_support_inner_obj.data.materials.append(red_material)
    #                         # soft_support_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_outer_obj
    #                         soft_support_outer_obj.data.materials.clear()
    #                         soft_support_outer_obj.data.materials.append(red_material)
    #                         # soft_support_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = soft_support_inside_obj
    #                         soft_support_inside_obj.data.materials.clear()
    #                         soft_support_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                         soft_support_inner_obj.select_set(False)
    #                         soft_support_outer_obj.select_set(False)
    #                         soft_support_inside_obj.select_set(False)
    #         return {'PASS_THROUGH'}
    #     else:
    #         print("supportadd_modal_finished")
    #         return {'FINISHED'}


class SupportSwitch(bpy.types.Operator):
    bl_idname = "object.supportswitch"
    bl_label = "支撑鼠标行为"

    def invoke(self, context, event):
        global is_supportAdd_modal_start, is_supportAdd_modal_startL
        bpy.context.scene.var = 77
        # if not is_supportAdd_modal_start and not is_supportAdd_modal_startL:
        #     name = bpy.context.scene.leftWindowObj
        #     if name == '右耳':
        #         is_supportAdd_modal_start = True
        #     elif name == '左耳':
        #         is_supportAdd_modal_startL = True
        #     context.window_manager.modal_handler_add(self)
        #     print("supportswitch_modal_invoke")
        if not is_supportAdd_modal_start:
            is_supportAdd_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("supportswitch_modal_invoke")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        override1 = getOverride()
        area = override1['area']

        global is_on_rotate
        global is_on_rotateL
        global is_supportAdd_modal_start, is_supportAdd_modal_startL
        support_enum = bpy.context.scene.zhiChengTypeEnum
        support_enumL = bpy.context.scene.zhiChengTypeEnumL
        name = bpy.context.scene.leftWindowObj
        hard_support_name = name + "Cone"
        hard_support_obj = bpy.data.objects.get(hard_support_name)
        soft_support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
        soft_support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
        soft_support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
        soft_support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
        soft_support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
        soft_support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        support_enum_cur = "OP1"
        is_on_rotate_cur = False
        if name == '右耳':
            support_enum_cur = support_enum
            is_on_rotate_cur = is_on_rotate
        elif name == '左耳':
            support_enum_cur = support_enumL
            is_on_rotate_cur = is_on_rotateL

        if get_mirror_context():
            print('supportswitch_modal_finished')
            is_supportAdd_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        if bpy.context.scene.var == 77:
            if event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height:
                if event.type == 'WHEELUPMOUSE':
                    if name == '右耳':
                        bpy.context.scene.zhiChengOffset += 0.05
                    else:
                        bpy.context.scene.zhiChengOffsetL += 0.05
                    return {'RUNNING_MODAL'}
                elif event.type == 'WHEELDOWNMOUSE':
                    if name == '右耳':
                        bpy.context.scene.zhiChengOffset -= 0.05
                    else:
                        bpy.context.scene.zhiChengOffsetL -= 0.05
                    return {'RUNNING_MODAL'}
            supportSaveInfo()
            if (not is_on_rotate_cur):
                if support_enum_cur == "OP1":
                    if (hard_support_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_hard_support(context,event) and (
                                is_changed_hard_support(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            hard_support_obj.data.materials.clear()
                            hard_support_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_hard_support(context, event) and (
                                is_changed(context, event) or is_changed_hard_support(context, event))):
                            # 调用hardSupport的鼠标行为
                            yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
                            hard_support_obj.data.materials.clear()
                            hard_support_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                        elif ((not is_mouse_on_object(context, event)) and (
                                is_changed(context, event) or is_changed_hard_support(context, event))):
                            # 调用公共鼠标行为
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            hard_support_obj.data.materials.clear()
                            hard_support_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                elif support_enum_cur == "OP2":
                    if (soft_support_inner_obj != None and soft_support_outer_obj != None and soft_support_inside_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_soft_support(context,event) and (
                                is_changed_soft_support(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            # soft_support_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inner_obj
                            soft_support_inner_obj.data.materials.clear()
                            soft_support_inner_obj.data.materials.append(red_material)
                            # soft_support_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_outer_obj
                            soft_support_outer_obj.data.materials.clear()
                            soft_support_outer_obj.data.materials.append(red_material)
                            # soft_support_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inside_obj
                            soft_support_inside_obj.data.materials.clear()
                            soft_support_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_soft_support(context, event) and (
                                is_changed_soft_support(context, event) or is_changed(context, event))):
                            # 调用softSupport的鼠标行为
                            yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
                            # soft_support_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inner_obj
                            soft_support_inner_obj.data.materials.clear()
                            soft_support_inner_obj.data.materials.append(yellow_material)
                            # soft_support_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_outer_obj
                            soft_support_outer_obj.data.materials.clear()
                            soft_support_outer_obj.data.materials.append(yellow_material)
                            # soft_support_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inside_obj
                            soft_support_inside_obj.data.materials.clear()
                            soft_support_inside_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                            soft_support_inner_obj.select_set(False)
                            soft_support_outer_obj.select_set(False)
                            soft_support_inside_obj.select_set(False)
                        elif ((not is_mouse_on_object(context, event)) and (
                                is_changed_soft_support(context, event) or is_changed(context, event))):
                            # 调用公共鼠标行为
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            # soft_support_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inner_obj
                            soft_support_inner_obj.data.materials.clear()
                            soft_support_inner_obj.data.materials.append(red_material)
                            # soft_support_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_outer_obj
                            soft_support_outer_obj.data.materials.clear()
                            soft_support_outer_obj.data.materials.append(red_material)
                            # soft_support_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inside_obj
                            soft_support_inside_obj.data.materials.clear()
                            soft_support_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                            soft_support_inner_obj.select_set(False)
                            soft_support_outer_obj.select_set(False)
                            soft_support_inside_obj.select_set(False)
            if (is_on_rotate_cur):
                if support_enum_cur == "OP1":
                    if (hard_support_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                                is_changed_sphere(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            hard_support_obj.data.materials.clear()
                            hard_support_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用hardSupport的三维旋转鼠标行为
                            yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
                            hard_support_obj.data.materials.clear()
                            hard_support_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                        elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用公共鼠标行为
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            hard_support_obj.data.materials.clear()
                            hard_support_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                elif support_enum_cur == "OP2":
                    if (soft_support_inner_obj != None and soft_support_outer_obj != None and soft_support_inside_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                                is_changed_sphere(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            # soft_support_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inner_obj
                            soft_support_inner_obj.data.materials.clear()
                            soft_support_inner_obj.data.materials.append(red_material)
                            # soft_support_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_outer_obj
                            soft_support_outer_obj.data.materials.clear()
                            soft_support_outer_obj.data.materials.append(red_material)
                            # soft_support_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inside_obj
                            soft_support_inside_obj.data.materials.clear()
                            soft_support_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.support_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用softSupport的鼠标行为
                            yellow_material = newColor("yellow", 1, 1, 0, 0, 1)
                            # soft_support_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inner_obj
                            soft_support_inner_obj.data.materials.clear()
                            soft_support_inner_obj.data.materials.append(yellow_material)
                            # soft_support_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_outer_obj
                            soft_support_outer_obj.data.materials.clear()
                            soft_support_outer_obj.data.materials.append(yellow_material)
                            # soft_support_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inside_obj
                            soft_support_inside_obj.data.materials.clear()
                            soft_support_inside_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                            soft_support_inner_obj.select_set(False)
                            soft_support_outer_obj.select_set(False)
                            soft_support_inside_obj.select_set(False)
                        elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用公共鼠标行为
                            red_material = newColor("Red", 1, 0, 0, 0, 1)
                            # soft_support_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inner_obj
                            soft_support_inner_obj.data.materials.clear()
                            soft_support_inner_obj.data.materials.append(red_material)
                            # soft_support_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_outer_obj
                            soft_support_outer_obj.data.materials.clear()
                            soft_support_outer_obj.data.materials.append(red_material)
                            # soft_support_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = soft_support_inside_obj
                            soft_support_inside_obj.data.materials.clear()
                            soft_support_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                            soft_support_inner_obj.select_set(False)
                            soft_support_outer_obj.select_set(False)
                            soft_support_inside_obj.select_set(False)
            return {'PASS_THROUGH'}

        else:
            print("supportswitch_modal_finished")
            is_supportAdd_modal_start = False
            # if (name == "右耳"):
            #     is_supportAdd_modal_start = False
            # elif (name == "左耳"):
            #     is_supportAdd_modal_startL = False
            return {'FINISHED'}


class SupportSubmit(bpy.types.Operator):
    bl_idname = "object.supportsubmit"
    bl_label = "支撑提交"

    def invoke(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            is_on_rotate = False
        elif (name == "左耳"):
            is_on_rotateL = False
        bpy.context.scene.var = 78
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        support_enum = bpy.context.scene.zhiChengTypeEnum
        support_enumL = bpy.context.scene.zhiChengTypeEnumL

        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            supportSaveInfo()
            if support_enum == "OP1":
                hardSupportSubmit()
            elif support_enum == "OP2":
                softSupportSubmit()
        elif name == '左耳':
            supportSaveInfo()
            if support_enumL == "OP1":
                hardSupportSubmit()
            elif support_enumL == "OP2":
                softSupportSubmit()

        if not bpy.context.scene.pressfinish:
            unregister_tools()
            bpy.context.scene.pressfinish = True


class SupportRotate(bpy.types.Operator):
    bl_idname = "object.supportrotate"
    bl_label = "鼠标的三维旋转状态"

    def invoke(self, context, event):
        self.execute(context)
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        if (plane_obj != None ):
            if(name == '右耳'):
                is_on_rotate = not is_on_rotate
            elif(name == '左耳'):
                is_on_rotateL = not is_on_rotateL
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


class SupportDoubleClick(bpy.types.Operator):
    bl_idname = "object.supportdoubleclick"
    bl_label = "双击改变支撑位置"

    def invoke(self, context, event):
        # 将Plane激活并选中,位置设置为双击的位置
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context, event)
        if (co != -1):
            support_fit_rotate(normal,co)
            # plane_obj.location = co
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}


class SupportMirror(bpy.types.Operator):
    bl_idname = 'object.supportmirror'
    bl_label = '支撑镜像'

    def invoke(self, context, event):
        print('进入镜像了')
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):

        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")          #TODO  支撑模块不需要镜像
        return {'FINISHED'}


        global support_enum,support_enumL,support_offset,support_offsetL
        global is_add_supportL,is_add_support

        left_obj = bpy.data.objects.get(context.scene.leftWindowObj)
        right_obj = bpy.data.objects.get(context.scene.rightWindowObj)

        # 只操作一个耳朵时，不执行镜像
        if left_obj == None or right_obj == None:
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}

        tar_obj_name = bpy.context.scene.leftWindowObj
        tar_obj = bpy.data.objects[tar_obj_name]

        workspace = context.window.workspace.name

        if tar_obj_name == '左耳':
            planename = '右耳' + "Plane"
        elif tar_obj_name == '右耳':
            planename = '左耳' + "Plane"
        plane_obj = bpy.data.objects.get(planename)

        # 只在双窗口下执行镜像
        # if workspace == '布局.001':
        # if tar_obj_name == '左耳':
        #     support_offsetL = support_offset
        #     support_enumL = support_enum
        # else:
        #     support_offset = support_offsetL
        #     support_enum = support_enumL

        if tar_obj_name == '左耳' and not is_add_supportL:
            is_add_supportL = True
            addSupport()
        elif tar_obj_name == '右耳' and not is_add_support:
            is_add_support = True
            addSupport()


        # 获取添加后的支撑,并根据参数设置调整offset
        planename = tar_obj_name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        if plane_obj is not None:
            bm = bmesh.new()
            bm.from_mesh(tar_obj.data)
            ori_loc = plane_obj.location
            x = ori_loc.x
            y = -ori_loc.y
            z = ori_loc.z

            closest_vertex = None
            min_distance = float('inf')
            target_point = mathutils.Vector((x, y, z))

            for vert in bm.verts:
                # 将顶点坐标转换到世界坐标系
                vertex_world = tar_obj.matrix_world @ vert.co
                distance = (vertex_world - target_point).length
                if distance < min_distance:
                    min_distance = distance
                    closest_vertex = vert
            closest_vertex_world = tar_obj.matrix_world @ closest_vertex.co
            closest_vertex_normal = tar_obj.matrix_world.to_3x3() @ closest_vertex.normal

            support_fit_rotate(closest_vertex_normal, closest_vertex_world)

            if tar_obj_name == '左耳':
                bpy.context.scene.zhiChengTypeEnumL = bpy.context.scene.zhiChengTypeEnum
                bpy.context.scene.zhiChengOffsetL = bpy.context.scene.zhiChengOffset
            elif tar_obj_name == '右耳':
                bpy.context.scene.zhiChengTypeEnum = bpy.context.scene.zhiChengTypeEnumL
                bpy.context.scene.zhiChengOffset = bpy.context.scene.zhiChengOffsetL

            bm.free()

        if context.scene.var != 77:
            bpy.ops.object.supportswitch('INVOKE_DEFAULT')


        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


# 注册类
_classes = [
    SupportReset,
    SupportAdd,
    SupportSubmit,
    SupportTest,
    SupportDoubleClick,
    SupportTest1,
    SupportRotate,
    SupportMirror,
    SupportSwitch
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
