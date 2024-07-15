import bpy
import bmesh
import re
import mathutils
from .tool import *
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
from asyncio import Handle
from venv import create


prev_on_object = False    # 判断鼠标在模型上与否的状态是否改变
prev_on_objectL = False

prev_on_sprue = False     # 判断鼠标在排气孔上与否的状态是否改变
prev_on_sprueL = False

prev_on_sphere = False    #判断鼠标是否在附件球体上
prev_on_sphereL = False

is_on_rotate = False      #是否处于旋转的鼠标状态,用于 附件三维旋转鼠标行为和附件平面旋转拖动鼠标行为之间的切换
is_on_rotateL = False

sprue_info_save = []    #保存已经提交过的sprue信息,用于模块切换时的初始化
sprue_info_saveL = []


def newColor(id, r, g, b, is_transparency, transparency_degree):
    mat = newMaterial(id)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.inputs[0].default_value = (r, g, b, 1)
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


# 判断鼠标是否在物体上,排气孔
def is_mouse_on_sprue(context, event):
    name = bpy.context.scene.leftWindowObj
    name_outer = name + "CylinderOuter"
    name_inside = name + "CylinderInside"
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

# 判断鼠标是否在附件圆球上
def is_mouse_on_sphere(context, event):
    name = bpy.context.scene.leftWindowObj + "SprueSphere"
    obj = bpy.data.objects.get(name)
    if (obj != None):
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


# 判断鼠标状态是否发生改变
def is_changed_sprue(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "CylinderOuter"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_sprue  # 之前鼠标是否在物体上
        global prev_on_sprueL
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
            if (curr_on_object != prev_on_sprue):
                prev_on_sprue = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_sprueL):
                prev_on_sprueL = curr_on_object
                return True
            else:
                return False

    return False


# 判断鼠标状态是否发生改变,圆球
def is_changed_sphere(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "SprueSphere"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_sphere   # 之前鼠标是否在物体上
        global prev_on_sphereL  # 之前鼠标是否在物体上

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
            if (curr_on_object != prev_on_sphere):
                prev_on_sphere = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_sphereL):
                prev_on_sphereL = curr_on_object
                return True
            else:
                return False
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

# 获取鼠标在右耳上的坐标
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


def sprue_fit_rotate(normal,location):
    '''
    将排气孔移动到位置location并将连界面与向量normal对齐垂直
    '''
    #获取排气孔平面(排气孔的父物体)
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
    # 将排气孔摆正对齐
    if(plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z

def initialSprueTransparency():
    newColor("SprueTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质
    # mat = newShader("SprueTransparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01


def frontToSprue():
    name = bpy.context.scene.leftWindowObj
    casting_compare_obj = bpy.data.objects.get(name + "CastingCompare")
    if(casting_compare_obj != None):
        all_objs = bpy.data.objects
        name = bpy.context.scene.leftWindowObj
        for selected_obj in all_objs:
            if (selected_obj.name == name + "SprueReset" or selected_obj.name == name + "CastingCompareSprueReset"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)


        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "SprueReset"
        bpy.context.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(True)

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects[castingname]
        duplicate_obj1 = casting_obj.copy()
        duplicate_obj1.data = casting_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = castingname + "SprueReset"
        bpy.context.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)
        duplicate_obj1.hide_set(True)

        initial()



def frontFromSprue():
    name = bpy.context.scene.leftWindowObj
    casting_compare_obj = bpy.data.objects.get(name + "CastingCompare")
    if (casting_compare_obj != None):
        # 若模型上存在未提交的排气孔,则记录信息并提交该字体
        sprueSubmit()


        name = bpy.context.scene.leftWindowObj
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
        soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        spherename = bpy.context.scene.leftWindowObj + "SprueSphere"
        sphere_obj = bpy.data.objects.get(spherename)
        #存在未提交的Sprue和Plane时
        if (sprue_inner_obj != None):
            bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
        if (sprue_outer_obj != None):
            bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
        if (sprue_inside_obj != None):
            bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
        if (sprue_inner_offset_compare_obj != None):
            bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
        if (sprue_outer_offset_compare_obj != None):
            bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
        if (sprue_inside_offset_compare_obj != None):
            bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)
        if (hard_support_compare_obj != None):
            bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
        if (soft_support_compare_obj != None):
            bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
        if (plane_obj != None):
            bpy.data.objects.remove(plane_obj, do_unlink=True)
        if (sphere_obj != None):
            bpy.data.objects.remove(sphere_obj, do_unlink=True)
        # 删除排气孔对比物                                                                     #TODO 之前的各个模块都要修改为删除多个排气孔对比物
        for obj in bpy.data.objects:
            if (name == "右耳"):
                pattern = r'右耳SprueCompare'
                if re.match(pattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            elif (name == "左耳"):
                pattern = r'左耳SprueCompare'
                if re.match(pattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)

        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "SprueReset"
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

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects[castingname]
        castingresetname = castingname + "SprueReset"
        ori_casting_obj = bpy.data.objects[castingresetname]
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
            if (selected_obj.name == name + "SprueReset"  or selected_obj.name == name + "CastingCompareSprueReset"
                    or selected_obj.name == name + "SprueLast"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)


    #调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

def backToSprue():
    # 删除可能存在的排气孔对比物
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    exist_SprueReset = False
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SprueReset"):
            exist_SprueReset = True
    if (exist_SprueReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "SprueReset"
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

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects[castingname]
        castingresetname = castingname + "SprueReset"
        ori_casting_obj = bpy.data.objects[castingresetname]
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

        initial()
    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "SupportLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "CastingLast") != None):
            lastname = name + "CastingLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
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
            ori_obj.name = name + "SprueReset"
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
            ori_obj.name = name + "SprueReset"
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
            ori_obj.name = name + "SprueReset"
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
            ori_obj.name = name + "SprueReset"
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
            ori_obj.name = name + "SprueReset"
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
            ori_obj.name = name + "SprueReset"
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

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects[castingname]
        castingresetname = castingname + "SprueReset"
        ori_casting_obj = bpy.data.objects[castingresetname]
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

        initial()


def backFromSprue():

    # 提交附件并保存附件信息
    sprueSubmit()

    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SprueLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SprueLast"
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





def createSprue():
    #创建半径不同的两个圆柱,使用布尔修改器用小圆柱切割大圆柱创建排气孔
    bpy.ops.mesh.primitive_cylinder_add(vertices=80, radius=1, depth=3.6, enter_editmode=False, align='WORLD',
                                        location=(0, 0, 1.8), scale=(1, 1, 1))
    bpy.ops.mesh.primitive_cylinder_add(vertices=80, radius=0.6, depth=3.8, enter_editmode=False, align='WORLD',
                                        location=(0, 0, 1.8), scale=(1, 1, 1))
    # 导入排气孔的父物体平面
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', scale=(4, 4, 1))
    # 导入排气孔模块中的圆球,主要用于鼠标模式切换,当三维旋转状态开启的时候,鼠标在圆球上的时候,调用三维旋转鼠标行为,否则调用公共鼠标行为
    bpy.ops.mesh.primitive_uv_sphere_add(segments=30, ring_count=30, radius=10, enter_editmode=False, align='WORLD',
                                         location=(0, 0, 1.8), scale=(1, 1, 1))

    name = bpy.context.scene.leftWindowObj
    plane = bpy.data.objects.get("Plane")
    obj = bpy.data.objects.get("Cylinder")                #大圆柱
    obj1 = bpy.data.objects.get("Cylinder.001")           #小圆柱
    sphere_obj = bpy.data.objects["Sphere"]               #排气孔三维旋转圆球

    plane.location[2] = 1                                 #设置平面初始位置

    #将平面切割为与圆柱截面相同的圆形
    plane.select_set(True)
    obj1.select_set(False)
    obj.select_set(False)
    bpy.context.view_layer.objects.active = plane
    modifierPlaneCreate = plane.modifiers.new(name="PlaneCreate", type='BOOLEAN')
    modifierPlaneCreate.object = obj
    modifierPlaneCreate.operation = 'INTERSECT'
    modifierPlaneCreate.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="PlaneCreate")


    #将小圆柱上的顶点全部选中
    plane.select_set(False)
    obj.select_set(False)
    obj1.select_set(True)
    bpy.context.view_layer.objects.active = obj1
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    plane.select_set(False)
    obj1.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    #使用小圆柱切割大圆柱为排气筒 切割后内壁顶点自动被选中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    modifierSprueCreate = obj.modifiers.new(name="SprueCreate", type='BOOLEAN')
    modifierSprueCreate.object = obj1
    modifierSprueCreate.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SprueCreate")

    #排气孔内部被选中后,选择分离将排气孔的内外壁分离
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')

    #重命名
    obj2 = bpy.data.objects.get("Cylinder.002")
    obj.name = name + "CylinderOuter"          #排气孔外壁
    obj1.name = name + "CylinderInside"        #小圆柱作为内芯,提交后将其删除
    obj2.name = name + "CylinderInner"         #排气孔内壁
    plane.name = name + "Plane"
    sphere_obj.name = name + "SprueSphere"

    #为内外壁和内芯添加红色材质
    red_material = newColor("Red", 1, 0, 0, 0, 1)
    bpy.context.view_layer.objects.active = obj
    obj.data.materials.clear()
    obj.data.materials.append(red_material)
    bpy.context.view_layer.objects.active = obj1
    obj1.data.materials.clear()
    obj1.data.materials.append(red_material)
    bpy.context.view_layer.objects.active = obj2
    obj2.data.materials.clear()
    obj2.data.materials.append(red_material)
    #为平面添加透明材质
    bpy.context.view_layer.objects.active = plane
    initialSprueTransparency()
    plane.data.materials.clear()
    plane.data.materials.append(bpy.data.materials['SprueTransparency'])
    # 为圆球添加透明效果
    bpy.context.view_layer.objects.active = sphere_obj
    initialSprueTransparency()
    sphere_obj.data.materials.clear()
    sphere_obj.data.materials.append(bpy.data.materials['SprueTransparency'])

    #将内外壁复制出来一份作为参数offset偏移的对比物
    cylinder_outer_compare_offset_obj = obj.copy()
    cylinder_outer_compare_offset_obj.data = obj.data.copy()
    cylinder_outer_compare_offset_obj.animation_data_clear()
    cylinder_outer_compare_offset_obj.name = name + "CylinderOuterOffsetCompare"
    bpy.context.collection.objects.link(cylinder_outer_compare_offset_obj)
    # cylinder_outer_compare_offset_obj.hide_set(True)
    cylinder_inner_compare_offset_obj = obj2.copy()
    cylinder_inner_compare_offset_obj.data = obj2.data.copy()
    cylinder_inner_compare_offset_obj.animation_data_clear()
    cylinder_inner_compare_offset_obj.name = name + "CylinderInnerOffsetCompare"
    bpy.context.collection.objects.link(cylinder_inner_compare_offset_obj)
    # cylinder_inner_compare_offset_obj.hide_set(True)
    cylinder_inside_compare_offset_obj = obj1.copy()
    cylinder_inside_compare_offset_obj.data = obj1.data.copy()
    cylinder_inside_compare_offset_obj.animation_data_clear()
    cylinder_inside_compare_offset_obj.name = name + "CylinderInsideOffsetCompare"
    bpy.context.collection.objects.link(cylinder_inside_compare_offset_obj)
    # cylinder_inside_compare_offset_obj.hide_set(True)


    #将排气孔内外壁和内芯绑定为一组,外壁作为父物体,提交时统一处理
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj1.select_set(True)
    obj2.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    obj1.select_set(False)
    obj2.select_set(False)

    #将排气孔内外壁,内外壁对比物和平面绑定为一组,平面为父物体,提交时统一处理
    cylinder_outer_compare_offset_obj.select_set(True)
    cylinder_inner_compare_offset_obj.select_set(True)
    cylinder_inside_compare_offset_obj.select_set(True)
    plane.select_set(True)
    obj.select_set(True)
    sphere_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    obj.select_set(False)
    sphere_obj.select_set(False)
    #内外壁对比物隐藏
    cylinder_outer_compare_offset_obj.hide_set(True)
    cylinder_inner_compare_offset_obj.hide_set(True)
    cylinder_inside_compare_offset_obj.hide_set(True)

    if (name == "右耳"):
        moveToRight(plane)
        moveToRight(obj)
        moveToRight(obj1)
        moveToRight(obj2)
        moveToRight(cylinder_outer_compare_offset_obj)
        moveToRight(cylinder_inner_compare_offset_obj)
        moveToRight(cylinder_inside_compare_offset_obj)
        moveToRight(sphere_obj)
    elif (name == "左耳"):
        moveToLeft(plane)
        moveToLeft(obj)
        moveToLeft(obj1)
        moveToLeft(obj2)
        moveToLeft(cylinder_outer_compare_offset_obj)
        moveToLeft(cylinder_inner_compare_offset_obj)
        moveToLeft(cylinder_inside_compare_offset_obj)
        moveToLeft(sphere_obj)


def saveInfo():
    '''
    #在sprue提交前会保存sprue的相关信息
    '''
    global sprue_info_save
    global sprue_info_saveL

    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    offset = None
    if name == '右耳':
        offset = bpy.context.scene.paiQiKongOffset
    elif name == '左耳':
        offset = bpy.context.scene.paiQiKongOffsetL
    l_x = plane_obj.location[0]
    l_y = plane_obj.location[1]
    l_z = plane_obj.location[2]
    r_x = plane_obj.rotation_euler[0]
    r_y = plane_obj.rotation_euler[1]
    r_z = plane_obj.rotation_euler[2]

    sprue_info = SprueInfoSave(offset,l_x,l_y,l_z,r_x,r_y,r_z)
    if name == '右耳':
        sprue_info_save.append(sprue_info)
    elif name == '左耳':
        sprue_info_saveL.append(sprue_info)

def initial():
    ''''
    切换到排气孔模块的时候,根据之前保存的字体信息进行初始化,恢复之前添加的排气孔状态
    '''
    global sprue_info_save
    global sprue_info_saveL
    name = bpy.context.scene.leftWindowObj
    # 对于数组中保存的sprue信息,前n-1个先添加后提交,最后一个添加不提交
    if name == '右耳':
        if (len(sprue_info_save) > 0):
            for i in range(len(sprue_info_save) - 1):
                sprueInfo = sprue_info_save[i]
                offset = sprueInfo.offset
                l_x = sprueInfo.l_x
                l_y = sprueInfo.l_y
                l_z = sprueInfo.l_z
                r_x = sprueInfo.r_x
                r_y = sprueInfo.r_y
                r_z = sprueInfo.r_z
                # 添加Sprue并提交
                sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
            sprueInfo = sprue_info_save[len(sprue_info_save) - 1]
            offset = sprueInfo.offset
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            # 添加一个sprue,激活鼠标行为
            bpy.ops.object.sprueadd('INVOKE_DEFAULT')
            # 新添加的最后一个排气孔并未提交,多余的信息需要删除
            sprue_info_save.pop()
            # 获取添加后的Sprue,并根据参数设置调整offset
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.paiQiKongOffset = offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
    elif name == '左耳':
        if (len(sprue_info_saveL) > 0):
            for i in range(len(sprue_info_saveL) - 1):
                sprueInfo = sprue_info_saveL[i]
                offset = sprueInfo.offset
                l_x = sprueInfo.l_x
                l_y = sprueInfo.l_y
                l_z = sprueInfo.l_z
                r_x = sprueInfo.r_x
                r_y = sprueInfo.r_y
                r_z = sprueInfo.r_z
                # 添加Sprue并提交
                sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
            sprueInfo = sprue_info_saveL[len(sprue_info_saveL) - 1]
            offset = sprueInfo.offset
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            # 添加一个sprue,激活鼠标行为
            bpy.ops.object.sprueadd('INVOKE_DEFAULT')
            # 新添加的最后一个排气孔并未提交,多余的信息需要删除
            sprue_info_saveL.pop()
            # 获取添加后的Sprue,并根据参数设置调整offset
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.paiQiKongOffsetL = offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")

    #将旋转中心设置为左右耳模型
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    spherename = name + "SprueSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    if (sphere_obj != None and name == '右耳' and is_on_rotate):
        sphere_obj.select_set(True)
    if (sphere_obj != None and name == '左耳' and is_on_rotateL):
        sphere_obj.select_set(True)
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



def sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z):
    '''
    根据状态数组中保存的信息,生成一个排气孔
    模块切换时,根据提交时保存的信息,添加sprue进行初始化,先根据信息添加sprue,之后再将sprue提交。与submit函数相比,提交时不必保存sprue信息。
    '''

    # 添加一个新的Sprue
    addSprue()

    name = bpy.context.scene.leftWindowObj
    sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = name + "SprueSphere"
    sphere_obj = bpy.data.objects.get(spherename)

    obj_outer = bpy.data.objects.get(name)
    obj_inner = bpy.data.objects.get(name + "CastingCompare")

    if name == '右耳':
        bpy.context.scene.paiQiKongOffset = offset
    elif name == '左耳':
        bpy.context.scene.paiQiKongOffsetL = offset
    plane_obj.location[0] = l_x
    plane_obj.location[1] = l_y
    plane_obj.location[2] = l_z
    plane_obj.rotation_euler[0] = r_x
    plane_obj.rotation_euler[1] = r_y
    plane_obj.rotation_euler[2] = r_z


    # 将软耳膜支撑的内芯选中与右耳做布尔的差集,内芯插入模型的部分会和右耳合并形成一块内凹的区域,这块顶点处于选中的状态,直接将其删除在右耳上得到一个孔
    # 将铸造法内部物体顶点取消选中
    obj_outer.select_set(False)
    obj_inner.select_set(True)
    bpy.context.view_layer.objects.active = obj_inner
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj_inner.select_set(False)
    # 将软耳膜支撑内芯尺寸缩小一些并将顶点选中
    sprue_inside_obj.select_set(True)
    bpy.context.view_layer.objects.active = sprue_inside_obj
    sprue_inside_obj.scale[0] = 0.9
    sprue_inside_obj.scale[1] = 0.9
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    sprue_inside_obj.select_set(False)
    # 为铸造法内壁添加布尔修改器,与软耳膜支撑内芯做差集
    obj_inner.select_set(True)
    bpy.context.view_layer.objects.active = obj_inner
    modifierSprueDifferenceInside = obj_inner.modifiers.new(name="SprueDifferenceInside", type='BOOLEAN')
    modifierSprueDifferenceInside.object = sprue_inside_obj
    modifierSprueDifferenceInside.operation = 'DIFFERENCE'
    modifierSprueDifferenceInside.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SprueDifferenceInside")
    # 将选中的顶点直接删除在模型上得到软耳膜支撑的孔洞
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_less()
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    obj_inner.select_set(False)
    obj_outer.select_set(True)
    bpy.context.view_layer.objects.active = obj_outer
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj_outer.select_set(False)
    # 将软耳膜支撑内芯尺寸缩小一些并将顶点选中
    sprue_inside_obj.select_set(True)
    bpy.context.view_layer.objects.active = sprue_inside_obj
    sprue_inside_obj.scale[0] = 1
    sprue_inside_obj.scale[1] = 1
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    sprue_inside_obj.select_set(False)
    # 为铸造法内壁添加布尔修改器,与软耳膜支撑内芯做差集
    obj_outer.select_set(True)
    bpy.context.view_layer.objects.active = obj_outer
    modifierSupportDifferenceInside = obj_outer.modifiers.new(name="SupportDifferenceInside", type='BOOLEAN')
    modifierSupportDifferenceInside.object = sprue_inside_obj
    modifierSupportDifferenceInside.operation = 'DIFFERENCE'
    modifierSupportDifferenceInside.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SupportDifferenceInside")
    # 将选中的顶点直接删除在模型上得到软耳膜支撑的孔洞
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_less()
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    obj_inner.select_set(True)
    bpy.context.view_layer.objects.active = obj_inner
    # 为铸造法内壁添加布尔修改器,与排气孔内壁合并
    modifierSprueUnionInner = obj_inner.modifiers.new(name="SprueUnionInner", type='BOOLEAN')
    modifierSprueUnionInner.object = sprue_inner_obj
    modifierSprueUnionInner.operation = 'UNION'
    modifierSprueUnionInner.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SprueUnionInner")

    sprue_outer_obj.select_set(True)
    bpy.context.view_layer.objects.active = sprue_outer_obj
    # 先将排气孔外壁选中,使得其与铸造法外壳合并后被选中分离
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    sprue_outer_obj.select_set(False)

    obj_outer.select_set(True)
    bpy.context.view_layer.objects.active = obj_outer
    # 由于排气孔之前的模块存在布尔操作,会有其他顶点被选中,因此先将模型上选中顶点给取消选中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 为铸造法外壳添加布尔修改器,与排气孔外壳合并
    modifierSprueUnionOuter = obj_outer.modifiers.new(name="SprueUnionOuter", type='BOOLEAN')
    modifierSprueUnionOuter.object = sprue_outer_obj
    modifierSprueUnionOuter.operation = 'UNION'
    modifierSprueUnionOuter.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SprueUnionOuter")
    # 由于排气孔物体和透明的右耳外壳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比,布尔合并后的顶点会被选中,将这些顶点复制一份并分离为独立的物体
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    sprue_compare_obj = bpy.data.objects.get(name + ".001")
    if (sprue_compare_obj != None):
        sprue_compare_obj.name = name + "SprueCompare"
        yellow_material = newColor("yellow", 1, 0.319, 0.133, 0, 1)
        sprue_compare_obj.data.materials.clear()
        sprue_compare_obj.data.materials.append(yellow_material)
        if (name == "右耳"):
            moveToRight(sprue_compare_obj)
        elif (name == "左耳"):
            moveToLeft(sprue_compare_obj)

    bpy.data.objects.remove(plane_obj, do_unlink=True)
    bpy.data.objects.remove(sphere_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)

    bpy.context.view_layer.objects.active = obj_outer

    # 合并后Sprue会被去除材质,因此需要重置一下模型颜色为黄色
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
    bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    bpy.ops.paint.vertex_color_set()
    bpy.ops.object.mode_set(mode='OBJECT')



def sprueReset():
    # 存在未提交排气孔时
    name = bpy.context.scene.leftWindowObj
    sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    # sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = name + "SprueSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    # 存在未提交的Sprue,SprueCompare和Plane时
    if (sprue_inner_obj != None):
        bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
    if (sprue_outer_obj != None):
        bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
    if (sprue_inside_obj != None):
        bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
    if (sprue_inner_offset_compare_obj != None):
        bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
    if (sprue_outer_offset_compare_obj != None):
        bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
    if (sprue_inside_offset_compare_obj != None):
        bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)
    # if (sprue_compare_obj != None):
    #     bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    if (sphere_obj != None):
        bpy.data.objects.remove(sphere_obj, do_unlink=True)
    # 删除排气孔对比物
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    # 将SprueReset复制并替代当前操作模型,将CastingCompareSprueReset复制并替代CastingCompare
    oriname = bpy.context.scene.leftWindowObj
    ori_obj = bpy.data.objects.get(oriname)                   #右耳
    oricastingname= name + "CastingCompare"
    ori_casting_obj = bpy.data.objects.get(oricastingname)    #铸造法内层物体
    copyname = name + "SprueReset"
    ori_copy_obj = bpy.data.objects.get(copyname)             #右耳reset物体
    castingcopyname = name + "CastingCompareSprueReset"                   #铸造法内层reset物体
    ori_casting_copy_obj = bpy.data.objects.get(castingcopyname)
    if (ori_obj != None and ori_casting_obj != None and ori_copy_obj != None and ori_casting_copy_obj != None):
        #将CastingCompare还原
        bpy.data.objects.remove(ori_casting_obj, do_unlink=True)
        duplicate_obj1 = ori_casting_copy_obj.copy()
        duplicate_obj1.data = ori_casting_copy_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = oricastingname
        bpy.context.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)

        #将右耳还原
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = ori_copy_obj.copy()
        duplicate_obj.data = ori_copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj



def sprueSubmit():
    #  sprue_obj为排气孔物体,  sprue_offset_compare为隐藏的排气孔物体,用于偏移量参照,创建排气孔时一同创建   sprue_compare则作为对比,因为sprue_obj在提交后会变透明

    name = bpy.context.scene.leftWindowObj
    sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = name + "SprueSphere"
    sphere_obj = bpy.data.objects.get(spherename)

    obj_outer = bpy.data.objects.get(name)
    obj_inner = bpy.data.objects.get(name + "CastingCompare")


    # 存在未提交的Sprue,SprueCompare和Plane时
    if (sprue_inner_obj != None and sprue_outer_obj != None and  sprue_inside_obj != None and plane_obj != None
            and  sprue_inner_offset_compare_obj != None and sprue_outer_offset_compare_obj != None
            and sprue_inside_offset_compare_obj != None and  obj_outer != None and obj_inner != None):

        # 先将该Sprue的相关信息保存下来,用于模块切换时的初始化。
        saveInfo()

        # 将软耳膜支撑的内芯选中与右耳做布尔的差集,内芯插入模型的部分会和右耳合并形成一块内凹的区域,这块顶点处于选中的状态,直接将其删除在右耳上得到一个孔
        # 将铸造法内部物体顶点取消选中
        obj_outer.select_set(False)
        obj_inner.select_set(True)
        bpy.context.view_layer.objects.active = obj_inner
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        obj_inner.select_set(False)
        # 将软耳膜支撑内芯尺寸缩小一些并将顶点选中
        sprue_inside_obj.select_set(True)
        bpy.context.view_layer.objects.active = sprue_inside_obj
        sprue_inside_obj.scale[0] = 0.9
        sprue_inside_obj.scale[1] = 0.9
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        sprue_inside_obj.select_set(False)
        # 为铸造法内壁添加布尔修改器,与软耳膜支撑内芯做差集
        obj_inner.select_set(True)
        bpy.context.view_layer.objects.active = obj_inner
        modifierSprueDifferenceInside = obj_inner.modifiers.new(name="SprueDifferenceInside", type='BOOLEAN')
        modifierSprueDifferenceInside.object = sprue_inside_obj
        modifierSprueDifferenceInside.operation = 'DIFFERENCE'
        modifierSprueDifferenceInside.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier="SprueDifferenceInside")
        # 将选中的顶点直接删除在模型上得到软耳膜支撑的孔洞
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_less()
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')

        obj_inner.select_set(False)
        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        obj_outer.select_set(False)
        # 将软耳膜支撑内芯尺寸缩小一些并将顶点选中
        sprue_inside_obj.select_set(True)
        bpy.context.view_layer.objects.active = sprue_inside_obj
        sprue_inside_obj.scale[0] = 1
        sprue_inside_obj.scale[1] = 1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        sprue_inside_obj.select_set(False)
        # 为铸造法内壁添加布尔修改器,与软耳膜支撑内芯做差集
        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer
        modifierSupportDifferenceInside = obj_outer.modifiers.new(name="SupportDifferenceInside", type='BOOLEAN')
        modifierSupportDifferenceInside.object = sprue_inside_obj
        modifierSupportDifferenceInside.operation = 'DIFFERENCE'
        modifierSupportDifferenceInside.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier="SupportDifferenceInside")
        # 将选中的顶点直接删除在模型上得到软耳膜支撑的孔洞
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_less()
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')


        obj_inner.select_set(True)
        bpy.context.view_layer.objects.active = obj_inner
        # 为铸造法内壁添加布尔修改器,与排气孔内壁合并
        modifierSprueUnionInner = obj_inner.modifiers.new(name="SprueUnionInner", type='BOOLEAN')
        modifierSprueUnionInner.object = sprue_inner_obj
        modifierSprueUnionInner.operation = 'UNION'
        modifierSprueUnionInner.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier="SprueUnionInner")

        sprue_outer_obj.select_set(True)
        bpy.context.view_layer.objects.active = sprue_outer_obj
        # 先将排气孔外壁选中,使得其与铸造法外壳合并后被选中分离
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        sprue_outer_obj.select_set(False)

        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer
        # 由于排气孔之前的模块存在布尔操作,会有其他顶点被选中,因此先将模型上选中顶点给取消选中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        #为铸造法外壳添加布尔修改器,与排气孔外壳合并
        modifierSprueUnionOuter = obj_outer.modifiers.new(name="SprueUnionOuter", type='BOOLEAN')
        modifierSprueUnionOuter.object = sprue_outer_obj
        modifierSprueUnionOuter.operation = 'UNION'
        modifierSprueUnionOuter.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier="SprueUnionOuter")
        # 由于排气孔物体和透明的右耳外壳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比,布尔合并后的顶点会被选中,将这些顶点复制一份并分离为独立的物体
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        sprue_compare_obj = bpy.data.objects.get(name + ".001")
        if (sprue_compare_obj != None):
            sprue_compare_obj.name = name + "SprueCompare"
            yellow_material = newColor("yellow", 1, 0.319, 0.133, 0, 1)
            sprue_compare_obj.data.materials.clear()
            sprue_compare_obj.data.materials.append(yellow_material)
            if (name == "右耳"):
                moveToRight(sprue_compare_obj)
            elif (name == "左耳"):
                moveToLeft(sprue_compare_obj)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(sphere_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)

        bpy.context.view_layer.objects.active = obj_outer

        # 合并后Sprue会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 将当前激活物体设置为右耳,并将其他物体取消选中
        for selected_obj in bpy.data.objects:
            if (selected_obj.name == name ):
                bpy.context.view_layer.objects.active = selected_obj
                selected_obj.select_set(True)
            else:
                selected_obj.select_set(False)


def addSprue():

    createSprue()

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
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


class SprueInfoSave(object):
    '''
    保存提交前的每个Sprue信息
    '''
    def __init__(self,offset,l_x,l_y,l_z,r_x,r_y,r_z):
        self.offset = offset
        self.l_x = l_x
        self.l_y = l_y
        self.l_z = l_z
        self.r_x = r_x
        self.r_y = r_y
        self.r_z = r_z


class SprueReset(bpy.types.Operator):
    bl_idname = "object.spruereset"
    bl_label = "排气孔重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 16
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # global is_add_sprue
        # global is_add_sprueL
        global is_on_rotate
        global is_on_rotateL
        global sprue_info_save
        global sprue_info_saveL
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            # is_add_sprue = False
            is_on_rotate = False
            sprue_info_save = []
        elif name == '左耳':
            # is_add_sprueL = False
            is_on_rotateL = False
            sprue_info_saveL = []

        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        # sprueSaveInfo()
        sprueReset()
        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
        return {'FINISHED'}


class SprueAdd(bpy.types.Operator):
    bl_idname = "object.sprueadd"
    bl_label = "添加排气孔"

    def invoke(self, context, event):

        bpy.context.scene.var = 17
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        global sprue_info_save
        global sprue_info_saveL
        name = bpy.context.scene.leftWindowObj
        sprue_info_save_cur = None
        if name == '右耳':
            sprue_info_save_cur = sprue_info_save
        elif name == '左耳':
            sprue_info_save_cur = sprue_info_saveL


        #将可能存在的排气孔先提交
        sprueSubmit()
        # 双击添加过一个排气孔之后,才能够继续添加排气孔
        if (len(sprue_info_save_cur) == 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
            return {'FINISHED'}
        #添加排气孔
        addSprue()
        # 将Plane激活并选中
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        #将排气孔位置设置为上一个排气孔的位置
        sprueInfo = sprue_info_save_cur[len(sprue_info_save_cur) - 1]
        l_x = sprueInfo.l_x
        l_y = sprueInfo.l_y
        l_z = sprueInfo.l_z
        r_x = sprueInfo.r_x
        r_y = sprueInfo.r_y
        r_z = sprueInfo.r_z
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z
        #设置旋转中心
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        is_on_rotate_cur = False
        if (name == '右耳'):
            is_on_rotate_cur = is_on_rotate
        elif (name == '左耳'):
            is_on_rotate_cur = is_on_rotateL
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 17):
            if(not is_on_rotate_cur):
                if(sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                    if (is_mouse_on_object(context, event) and not is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                        # 公共鼠标行为加双击移动附件位置
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                    elif (is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                        # 调用sprue的鼠标行为
                        yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(yellow_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(yellow_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(yellow_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                        plane_obj.select_set(True)
                        bpy.context.view_layer.objects.active = plane_obj
                        cur_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
                    elif ((not is_mouse_on_object(context, event)) and (is_changed_sprue(context, event) or is_changed(context, event))):
                        # 调用公共鼠标行为
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
            elif(is_on_rotate_cur):
                if (sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                    if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                            is_changed_sphere(context, event) or is_changed(context, event))):
                        # 公共鼠标行为加双击移动附件位置
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                    elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                        # 调用sprue的三维旋转鼠标行为
                        yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(yellow_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(yellow_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(yellow_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                        plane_obj.select_set(True)
                        bpy.context.view_layer.objects.active = plane_obj
                        cur_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
                    elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                        # 调用公共鼠标行为
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class SprueInitialAdd(bpy.types.Operator):
    bl_idname = "object.sprueinitialadd"
    bl_label = "添加排气孔"

    def invoke(self, context, event):

        bpy.context.scene.var = 18
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


        #添加排气孔
        addSprue()
        # 将Plane激活并选中
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        #将添加的排气孔位置设置未双击的位置
        co, normal = cal_co(context, event)
        if (co != -1):
            sprue_fit_rotate(normal, co)
        #设置旋转中心
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        is_on_rotate_cur = False
        if (name == '右耳'):
            is_on_rotate_cur = is_on_rotate
        elif (name == '左耳'):
            is_on_rotate_cur = is_on_rotateL
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 18):
            if(not is_on_rotate_cur):
                if(sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                    if (is_mouse_on_object(context, event) and not is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                        # 公共鼠标行为加双击移动附件位置
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                    elif (is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                        # 调用sprue的鼠标行为
                        yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(yellow_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(yellow_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(yellow_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                        plane_obj.select_set(True)
                        bpy.context.view_layer.objects.active = plane_obj
                        cur_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
                    elif ((not is_mouse_on_object(context, event)) and (is_changed_sprue(context, event) or is_changed(context, event))):
                        # 调用公共鼠标行为
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
            elif(is_on_rotate_cur):
                if (sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                    if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                            is_changed_sphere(context, event) or is_changed(context, event))):
                        # 公共鼠标行为加双击移动附件位置
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                    elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                        # 调用sprue的三维旋转鼠标行为
                        yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(yellow_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(yellow_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(yellow_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                        plane_obj.select_set(True)
                        bpy.context.view_layer.objects.active = plane_obj
                        cur_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
                    elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                        # 调用公共鼠标行为
                        red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                        # sprue_inner_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inner_obj
                        sprue_inner_obj.data.materials.clear()
                        sprue_inner_obj.data.materials.append(red_material)
                        # sprue_outer_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_outer_obj
                        sprue_outer_obj.data.materials.clear()
                        sprue_outer_obj.data.materials.append(red_material)
                        # sprue_inside_obj.select_set(True)
                        # bpy.context.view_layer.objects.active = sprue_inside_obj
                        sprue_inside_obj.data.materials.clear()
                        sprue_inside_obj.data.materials.append(red_material)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        plane_obj.select_set(False)
                        sprue_inner_obj.select_set(False)
                        sprue_outer_obj.select_set(False)
                        sprue_inside_obj.select_set(False)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}

class SprueSubmit(bpy.types.Operator):
    bl_idname = "object.spruesubmit"
    bl_label = "排气孔提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 19
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        # sprueSaveInfo()
        sprueSubmit()
        return {'FINISHED'}

class SprueRotate(bpy.types.Operator):
    bl_idname = "object.spruerotate"
    bl_label = "鼠标的三维旋转状态"

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        spherename = name + "SprueSphere"
        sphere_obj = bpy.data.objects.get(spherename)
        if (plane_obj != None and sphere_obj != None):
            if(name == '右耳'):
                is_on_rotate = not is_on_rotate
                if(is_on_rotate == True):
                    sphere_obj.select_set(True)
                else:
                    sphere_obj.select_set(False)
            elif(name == '左耳'):
                is_on_rotateL = not is_on_rotateL
                if (is_on_rotateL == True):
                    sphere_obj.select_set(True)
                else:
                    sphere_obj.select_set(False)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

class SprueDoubleClick(bpy.types.Operator):
    bl_idname = "object.spruedoubleclick"
    bl_label = "双击改变排气管位置"

    def invoke(self, context, event):
        # 将Plane激活并选中,位置设置为双击的位置
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context, event)
        if (co != -1):
            sprue_fit_rotate(normal,co)
            # plane_obj.location = co
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}

class MyTool_Sprue1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_reset"
    bl_label = "排气孔重置"
    bl_description = (
        "重置模型,清除模型上的所有排气孔"
    )
    bl_icon = "brush.sculpt.clay"
    bl_widget = None
    bl_keymap = (
        ("object.spruereset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_add"
    bl_label = "排气孔添加"
    bl_description = (
        "在模型上上一个排气孔的位置处添加一个排气孔"
    )
    bl_icon = "brush.sculpt.boundary"
    bl_widget = None
    bl_keymap = (
        ("object.sprueadd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.sprueadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_submit"
    bl_label = "排气孔提交"
    bl_description = (
        "对于模型上所有排气孔提交实体化"
    )
    bl_icon = "brush.sculpt.blob"
    bl_widget = None
    bl_keymap = (
        ("object.spruesubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Sprue_Rotate(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_rotate"
    bl_label = "排气孔旋转"
    bl_description = (
        "添加排气孔后,调用排气孔三维旋转鼠标行为"
    )
    bl_icon = "brush.paint_texture.draw"
    bl_widget = None
    bl_keymap = (
        ("object.spruerotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Sprue_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_mirror"
    bl_label = "排气孔镜像"
    bl_description = (
        "点击镜像排气孔"
    )
    bl_icon = "brush.paint_texture.fill"
    bl_widget = None
    bl_keymap = (
        ("object.spruemirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Sprue_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_mouse"
    bl_label = "双击改变排气管位置"
    bl_description = (
        "添加排气管后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.paint_texture.mask"
    bl_widget = None
    bl_keymap = (
        ("object.spruedoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_SprueInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_initial"
    bl_label = "排气孔添加初始化"
    bl_description = (
        "刚进入排气孔模块的时,在模型上双击位置处添加一个排气孔"
    )
    bl_icon = "brush.sculpt.snake_hook"
    bl_widget = None
    bl_keymap = (
        ("object.sprueinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    SprueReset,
    SprueAdd,
    SprueInitialAdd,
    SprueSubmit,
    SprueDoubleClick,
    SprueRotate,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Sprue1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Sprue2, separator=True, group=False, after={MyTool_Sprue1.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue3, separator=True, group=False, after={MyTool_Sprue2.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Rotate, separator=True, group=False, after={MyTool_Sprue3.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Mirror, separator=True, group=False, after={MyTool_Sprue_Rotate.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Mouse, separator=True, group=False, after={MyTool_Sprue_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_SprueInitial, separator=True, group=False, after={MyTool_Sprue_Mouse.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Sprue1)
    bpy.utils.unregister_tool(MyTool_Sprue2)
    bpy.utils.unregister_tool(MyTool_Sprue3)
    bpy.utils.unregister_tool(MyTool_Sprue_Rotate)
    bpy.utils.unregister_tool(MyTool_Sprue_Mirror)
    bpy.utils.unregister_tool(MyTool_Sprue_Mouse)
    bpy.utils.unregister_tool(MyTool_SprueInitial)
