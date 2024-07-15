import bpy
import bmesh
import os
import mathutils
from .tool import *
from asyncio import Handle
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils

prev_on_handle = False  # 判断鼠标在附件上与否的状态是否改变
prev_on_handleL = False

prev_on_sphere = False  #判断鼠标是否在附件球体上
prev_on_sphereL = False

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变
prev_on_objectL = False

is_on_rotate = False    #是否处于旋转的鼠标状态,用于 附件三维旋转鼠标行为和附件平面旋转拖动鼠标行为之间的切换
is_on_rotateL = False

handle_info_save = []    #保存已经提交过的handle信息,用于模块切换时的初始化
handle_info_saveL = []


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


def initialTransparency():
    newColor("Transparency", 1, 0.319, 0.133, 1, 0.3)  # 创建材质
    # mat = newShader("Transparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.3

def initialHandleTransparency():
    newColor("HandleTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质
    # mat = newShader("HandleTransparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01

# 判断鼠标是否在附件上
def is_mouse_on_handle(context, event):
    name = bpy.context.scene.leftWindowObj + "Cube"
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

# 判断鼠标是否在附件圆球上
def is_mouse_on_sphere(context, event):
    name = bpy.context.scene.leftWindowObj + "HandleSphere"
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

# 判断鼠标是否在上物体上
def is_mouse_on_object(context, event):
    name = bpy.context.scene.leftWindowObj
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

# 判断鼠标状态是否发生改变,附件
def is_changed_handle(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "Cube"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_handle  # 之前鼠标是否在物体上
        global prev_on_handleL  # 之前鼠标是否在物体上

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
            if (curr_on_object != prev_on_handle):
                prev_on_handle = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_handleL):
                prev_on_handleL = curr_on_object
                return True
            else:
                return False
    return False

# 判断鼠标状态是否发生改变,圆球
def is_changed_sphere(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "HandleSphere"
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
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_object  # 之前鼠标是否在物体上
        global prev_on_objectL  # 之前鼠标是否在物体上

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
            if (curr_on_object != prev_on_object):
                prev_on_object = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
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

def handle_fit_rotate(normal,location):
    '''
    将附件移动到位置location并将连界面与向量normal对齐垂直
    '''
    #获取附件平面(附件的父物体)
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
    # 将附件摆正对齐
    if(plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z

def frontToHandle():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        name = bpy.context.scene.leftWindowObj
        if (selected_obj.name == name+"HandleReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "HandleReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    if(name == "右耳"):
        moveToRight(duplicate_obj1)
    elif(name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    initial()


def frontFromHandle():
    # 若模型上存在未提交的附件,则记录信息并提交该字体
    handleSubmit()

    name = bpy.context.scene.leftWindowObj
    handlename = name + "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = name + "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    planename = bpy.context.scene.leftWindowObj + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = bpy.context.scene.leftWindowObj + "HandleSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (handle_compare_obj != None):
        bpy.data.objects.remove(handle_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    if (sphere_obj != None):
        bpy.data.objects.remove(sphere_obj, do_unlink=True)
    #删除附件外壳
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)



    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    resetname = name + "HandleReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if(name == "右耳"):
        moveToRight(duplicate_obj)
    elif(name == "左耳"):
        moveToLeft(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == bpy.context.scene.leftWindowObj + "HandleReset" or selected_obj.name == bpy.context.scene.leftWindowObj + "HandleLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

def backToHandle():
    #若添加铸造法之后切换到支撑或者排气孔模块,再由支撑或排气孔模块跳过铸造法模块直接切换回前面的模块,则需要对物体进行特殊的处理
    name = bpy.context.scene.leftWindowObj
    casting_name = name + "CastingCompare"
    casting_compare_obj = bpy.data.objects.get(casting_name)
    if(casting_compare_obj != None):
        cur_obj = bpy.data.objects.get(name)
        casting_reset_obj = bpy.data.objects.get(name + "CastingReset")
        casting_last_obj = bpy.data.objects.get(name + "CastingLast")
        casting_compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if(cur_obj != None and casting_reset_obj != None and casting_last_obj != None and casting_compare_last_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
            casting_compare_obj.name = name
            bpy.data.objects.remove(casting_reset_obj, do_unlink=True)
            bpy.data.objects.remove(casting_last_obj, do_unlink=True)
            bpy.data.objects.remove(casting_compare_last_obj, do_unlink=True)
    #删除附件和字体外壳
    for obj in bpy.data.objects:
        patternR = r'右耳LabelPlaneForCasting'
        patternL = r'左耳LabelPlaneForCasting'
        if re.match(patternR, obj.name) or re.match(patternL, obj.name):
            label_obj = obj
            bpy.data.objects.remove(label_obj, do_unlink=True)
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
    label_reset = bpy.data.objects.get(name + "LabelReset")
    label_last = bpy.data.objects.get(name + "LabelLast")
    casting_reset = bpy.data.objects.get(name + "CastingReset")
    casting_last = bpy.data.objects.get(name + "CastingLast")
    support_reset = bpy.data.objects.get(name + "SupportReset")
    support_last = bpy.data.objects.get(name + "SupportLast")
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
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

    exist_HandleReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "HandleReset"):
            exist_HandleReset = True
    if (exist_HandleReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "HandleReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if(name == "右耳"):
            moveToRight(duplicate_obj)
        elif(name == "左耳"):
            moveToLeft(duplicate_obj)
        
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        initial()
    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "VentCanalLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "SoundCanalLast") != None):
            lastname = name + "SoundCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
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
            ori_obj.name = name + "HandleReset"
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
            ori_obj.name = name + "HandleReset"
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
            ori_obj.name = name + "HandleReset"
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
            ori_obj.name = name + "HandleReset"
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
        if(name == "右耳"):
            moveToRight(duplicate_obj)
        elif(name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        initial()

def backFromHandle():

    #提交附件并保存附件信息
    handleSubmit()


    name = bpy.context.scene.leftWindowObj
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "HandleLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "HandleLast"
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



def saveInfo():
    '''
    #在handle提交前会保存handle的相关信息
    '''
    global handle_info_save
    global handle_info_saveL

    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    offset = None
    if name == '右耳':
        offset = bpy.context.scene.erMoFuJianOffset
    elif name == '左耳':
        offset = bpy.context.scene.erMoFuJianOffsetL
    l_x = plane_obj.location[0]
    l_y = plane_obj.location[1]
    l_z = plane_obj.location[2]
    r_x = plane_obj.rotation_euler[0]
    r_y = plane_obj.rotation_euler[1]
    r_z = plane_obj.rotation_euler[2]

    handle_info = HandleInfoSave(offset,l_x,l_y,l_z,r_x,r_y,r_z)
    if name == '右耳':
        handle_info_save.append(handle_info)
    elif name == '左耳':
        handle_info_saveL.append(handle_info)


def initial():
    ''''
    切换到附件模块的时候,根据之前保存的字体信息进行初始化,恢复之前添加的字体状态
    '''
    global handle_info_save
    global handle_info_saveL
    name = bpy.context.scene.leftWindowObj
    # 对于数组中保存的handle信息,前n-1个先添加后提交,最后一个添加不提交
    if name == '右耳':
        if (len(handle_info_save) > 0):
            for i in range(len(handle_info_save) - 1):
                handleInfo = handle_info_save[i]
                offset = handleInfo.offset
                l_x = handleInfo.l_x
                l_y = handleInfo.l_y
                l_z = handleInfo.l_z
                r_x = handleInfo.r_x
                r_y = handleInfo.r_y
                r_z = handleInfo.r_z
                # 添加Handle并提交
                handleInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
            handleInfo = handle_info_save[len(handle_info_save) - 1]
            offset = handleInfo.offset
            l_x = handleInfo.l_x
            l_y = handleInfo.l_y
            l_z = handleInfo.l_z
            r_x = handleInfo.r_x
            r_y = handleInfo.r_y
            r_z = handleInfo.r_z
            # 添加一个handle,激活鼠标行为
            bpy.ops.object.handleadd('INVOKE_DEFAULT')
            # 新添加的最后一个附件并未提交,多余的信息需要删除
            handle_info_save.pop()
            # 获取添加后的Handle,并根据参数设置调整offset
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.erMoFuJianOffset = offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.handle_initial")
    elif name == '左耳':
        if (len(handle_info_saveL) > 0):
            for i in range(len(handle_info_saveL) - 1):
                handleInfo = handle_info_saveL[i]
                offset = handleInfo.offset
                l_x = handleInfo.l_x
                l_y = handleInfo.l_y
                l_z = handleInfo.l_z
                r_x = handleInfo.r_x
                r_y = handleInfo.r_y
                r_z = handleInfo.r_z
                # 添加Handle并提交
                handleInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
            handleInfo = handle_info_saveL[len(handle_info_saveL) - 1]
            offset = handleInfo.offset
            l_x = handleInfo.l_x
            l_y = handleInfo.l_y
            l_z = handleInfo.l_z
            r_x = handleInfo.r_x
            r_y = handleInfo.r_y
            r_z = handleInfo.r_z
            # 添加一个handle,激活鼠标行为
            bpy.ops.object.handleadd('INVOKE_DEFAULT')
            # 新添加的最后一个附件并未提交,多余的信息需要删除
            handle_info_saveL.pop()
            # 获取添加后的Handle,并根据参数设置调整offset
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.erMoFuJianOffsetL = offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.handle_initial")

    # 将旋转中心设置为左右耳模型
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



def handleInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z):
    '''
    根据状态数组中保存的信息,生成一个附件
    模块切换时,根据提交时保存的信息,添加handle进行初始化,先根据信息添加handle,之后再将handle提交。与submit函数相比,提交时不必保存handle信息。
    '''

    # 添加一个新的Handle
    addHandle()

    # 获取添加后的handle,并根据参数设置其offset
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    handlename = name + "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = name + "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = name + "HandleSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    if name == '右耳':
        bpy.context.scene.erMoFuJianOffset = offset
    elif name == '左耳':
        bpy.context.scene.erMoFuJianOffsetL = offset
    plane_obj.location[0] = l_x
    plane_obj.location[1] = l_y
    plane_obj.location[2] = l_z
    plane_obj.rotation_euler[0] = r_x
    plane_obj.rotation_euler[1] = r_y
    plane_obj.rotation_euler[2] = r_z


    #创建用于实体化的附件外壳
    createHandleForCasting()

    #将附件与模型Bool合并
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].object = handle_obj
    bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

    #删除原本的附件,附件对比物,三维旋转圆球,父平面
    bpy.data.objects.remove(plane_obj, do_unlink=True)
    bpy.data.objects.remove(sphere_obj, do_unlink=True)
    bpy.data.objects.remove(handle_obj, do_unlink=True)
    bpy.data.objects.remove(handle_compare_obj, do_unlink=True)

    # 合并后Handle会被去除材质,因此需要重置一下模型颜色为黄色
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
    bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    bpy.ops.paint.vertex_color_set()
    bpy.ops.object.mode_set(mode='OBJECT')



def handleReset():
    # 存在未提交Handle时,删除Handle和Plane
    name = bpy.context.scene.leftWindowObj
    handlename = name + "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = name + "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    # handle_for_casting_name = name + "软耳膜附件Casting"
    # handle_for_casting_obj = bpy.data.objects.get(handle_for_casting_name)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = name + "HandleSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    # 存在未提交的Handle,HandleCompare和Plane时
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (handle_compare_obj != None):
        bpy.data.objects.remove(handle_compare_obj, do_unlink=True)
    # if (handle_for_casting_obj != None):
    #     bpy.data.objects.remove(handle_for_casting_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    if(sphere_obj != None):
        bpy.data.objects.remove(sphere_obj, do_unlink=True)

    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    #将面板参数重置
    if name == '右耳':
        bpy.context.scene.erMoFuJianOffset = 0
    elif name == '左耳':
        bpy.context.scene.erMoFuJianOffsetL = 0
    # 将HandleReset复制并替代当前操作模型
    oriname = bpy.context.scene.leftWindowObj
    ori_obj = bpy.data.objects.get(oriname)
    copyname = oriname+ "HandleReset"
    copy_obj = bpy.data.objects.get(copyname)
    if (ori_obj != None and copy_obj != None):
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = copy_obj.copy()
        duplicate_obj.data = copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)
        if (oriname == "右耳"):
            moveToRight(duplicate_obj)
        elif (oriname == "左耳"):
            moveToLeft(duplicate_obj)

def createHandleForCasting():
    '''
    创建用于实体化的附件
    '''
    name = bpy.context.scene.leftWindowObj                                        #用于处理附件的铸造法
    script_dir = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.join(script_dir, "stl\\软耳膜附件Casting.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    handle_for_casting_name = "软耳膜附件Casting"
    handle_for_casting_obj = bpy.data.objects.get(handle_for_casting_name)
    handle_for_casting_obj.name = name + "软耳膜附件Casting"
    if (name == "右耳"):
        moveToRight(handle_for_casting_obj)
    elif (name == "左耳"):
        moveToLeft(handle_for_casting_obj)
    #复制出一份物体作为参照,根据offset移动该附件
    duplicate_obj1 = handle_for_casting_obj.copy()
    duplicate_obj1.data = handle_for_casting_obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "软耳膜附件CastingCompare"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    handlename = name + "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handle_for_casting_compare_name = name + "软耳膜附件CastingCompare"
    handle_for_casting_compare_obj = bpy.data.objects.get(handle_for_casting_compare_name)
    if(handle_for_casting_obj != None and handle_obj != None and plane_obj != None and handle_for_casting_compare_obj != None):
        #为用于铸造法的附件添加材质
        initialTransparency()
        handle_for_casting_obj.data.materials.clear()
        handle_for_casting_obj.data.materials.append(bpy.data.materials['Transparency'])
        #设置附件的位置
        handle_for_casting_obj.location[0] = plane_obj.location[0]
        handle_for_casting_obj.location[1] = plane_obj.location[1]
        handle_for_casting_obj.location[2] = plane_obj.location[2]
        handle_for_casting_obj.rotation_euler[0] = plane_obj.rotation_euler[0]
        handle_for_casting_obj.rotation_euler[1] = plane_obj.rotation_euler[1]
        handle_for_casting_obj.rotation_euler[2] = plane_obj.rotation_euler[2]
        handle_for_casting_compare_obj.location[0] = plane_obj.location[0]
        handle_for_casting_compare_obj.location[1] = plane_obj.location[1]
        handle_for_casting_compare_obj.location[2] = plane_obj.location[2]
        handle_for_casting_compare_obj.rotation_euler[0] = plane_obj.rotation_euler[0]
        handle_for_casting_compare_obj.rotation_euler[1] = plane_obj.rotation_euler[1]
        handle_for_casting_compare_obj.rotation_euler[2] = plane_obj.rotation_euler[2]
        #根据offset参数设置软耳膜附件Casting的偏移位置
        handle_offset = None
        if name == '右耳':
            handle_offset = bpy.context.scene.erMoFuJianOffset
        elif name == '左耳':
            handle_offset = bpy.context.scene.erMoFuJianOffsetL
        if handle_obj.type == 'MESH' and plane_obj.type == 'MESH' and handle_for_casting_compare_obj.type == 'MESH' and handle_for_casting_obj.type == 'MESH':
            me = handle_for_casting_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            ori_handle_me = handle_for_casting_compare_obj.data
            ori_handle_bm = bmesh.new()
            ori_handle_bm.from_mesh(ori_handle_me)
            ori_handle_bm.verts.ensure_lookup_table()

            plane_me = plane_obj.data
            plane_bm = bmesh.new()
            plane_bm.from_mesh(plane_me)
            plane_bm.verts.ensure_lookup_table()

            # 获取平面法向
            plane_vert0 = plane_bm.verts[0]
            plane_vert1 = plane_bm.verts[1]
            plane_vert2 = plane_bm.verts[2]
            point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
            point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
            point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
            # 计算两个向量
            vector1 = point2 - point1
            vector2 = point3 - point1
            # 计算法向量
            normal = vector1.cross(vector2)
            # 根据面板参数设置偏移值
            for vert in bm.verts:
                vert.co = ori_handle_bm.verts[vert.index].co + normal.normalized() * handle_offset
            bm.to_mesh(me)
            bm.free()
            ori_handle_bm.free()
            plane_bm.free()
        #将用于对比的软耳膜附件CastingCompare删除
        if (handle_for_casting_compare_obj != None):
            bpy.data.objects.remove(handle_for_casting_compare_obj, do_unlink=True)
        #将附件隐藏
        handle_for_casting_obj.hide_set(True)



def handleSubmit():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    handlename = name + "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = name + "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    spherename = name + "HandleSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    # 存在未提交的Handle和Plane时
    if (handle_obj != None and plane_obj != None):
        # 先将该Handle的相关信息保存下来,用于模块切换时的初始化。
        saveInfo()

        #创建用于实体化的附件
        createHandleForCasting()

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = handle_obj
        bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(sphere_obj, do_unlink=True)
        bpy.data.objects.remove(handle_obj, do_unlink=True)
        bpy.data.objects.remove(handle_compare_obj, do_unlink=True)

        # 合并后Handle会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')


def addHandle():
    # 添加平面Plane和附件Cube
    script_dir = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.join(script_dir, "stl\\软耳膜附件.stl")
    #导入附件及附件的对比物体
    bpy.ops.wm.stl_import(filepath=relative_path)
    bpy.ops.wm.stl_import(filepath=relative_path)
    #导入附件的父物体平面
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(-100, -100, 0), scale=(4, 1.6, 1))
    #导入附件模块中的圆球,主要用于鼠标模式切换,当三维旋转状态开启的时候,鼠标在圆球上的时候,调用三维旋转鼠标行为,否则调用公共鼠标行为
    bpy.ops.mesh.primitive_uv_sphere_add(segments=30, ring_count=30, radius=10, enter_editmode=False, align='WORLD',
                                         location=(-100, -100, 0), scale=(1, 1, 1))
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    cubename = "软耳膜附件"
    cube_obj = bpy.data.objects[cubename]
    cube_obj.name = name + "Cube"
    cube_obj.location[0] = -100
    cube_obj.location[1] = -100
    if (name == "右耳"):
        moveToRight(cube_obj)
    elif (name == "左耳"):
        moveToLeft(cube_obj)
    cubecomparename = "软耳膜附件.001"
    cube_compare_obj = bpy.data.objects[cubecomparename]
    cube_compare_obj.name = name + "Cube.001"
    cube_compare_obj.location[0] = -100
    cube_compare_obj.location[1] = -100
    if (name == "右耳"):
        moveToRight(cube_compare_obj)
    elif (name == "左耳"):
        moveToLeft(cube_compare_obj)
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]
    plane_obj.name = name + "Plane"
    plane_obj.scale[0] = 4
    plane_obj.scale[1] = 1.6
    if (name == "右耳"):
        moveToRight(plane_obj)
    elif (name == "左耳"):
        moveToLeft(plane_obj)
    spherename = "Sphere"
    sphere_obj = bpy.data.objects[spherename]
    sphere_obj.name = name + "HandleSphere"
    if (name == "右耳"):
        moveToRight(sphere_obj)
    elif (name == "左耳"):
        moveToLeft(sphere_obj)

    # 为附件添加材质
    bpy.context.view_layer.objects.active = cube_obj
    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
    cube_obj.data.materials.clear()
    cube_obj.data.materials.append(red_material)

    # 将作为对比的附件变透明
    bpy.context.view_layer.objects.active = cube_compare_obj
    initialHandleTransparency()
    cube_compare_obj.data.materials.clear()
    cube_compare_obj.data.materials.append(bpy.data.materials['HandleTransparency'])



    # 为平面添加透明效果
    bpy.context.view_layer.objects.active = plane_obj
    initialHandleTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['HandleTransparency'])

    # 为圆球添加透明效果
    bpy.context.view_layer.objects.active = sphere_obj
    initialHandleTransparency()
    sphere_obj.data.materials.clear()
    sphere_obj.data.materials.append(bpy.data.materials['HandleTransparency'])

    #将平面设置为附件的父物体。对父物体平面进行位移和大小缩放操作时，子物体字体会其改变
    bpy.context.view_layer.objects.active = plane_obj
    cube_obj.select_set(True)
    cube_compare_obj.select_set(True)
    sphere_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    cube_obj.select_set(False)
    cube_compare_obj.select_set(False)
    sphere_obj.select_set(False)
    bpy.context.view_layer.objects.active = plane_obj
    plane_obj.select_set(True)

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    # 设置附件初始位置
    plane_obj.location[0] = 10
    plane_obj.location[1] = 10
    plane_obj.location[2] = 10



class HandleInfoSave(object):
    '''
    保存提交前的每个Handle信息
    '''
    def __init__(self,offset,l_x,l_y,l_z,r_x,r_y,r_z):
        self.offset = offset
        self.l_x = l_x
        self.l_y = l_y
        self.l_z = l_z
        self.r_x = r_x
        self.r_y = r_y
        self.r_z = r_z


class HandleReset(bpy.types.Operator):
    bl_idname = "object.handlereset"
    bl_label = "附件重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 13
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_on_rotate
        global is_on_rotateL
        global handle_info_save
        global handle_info_saveL
        name = bpy.context.scene.leftWindowObj
        if(name == '右耳'):
            is_on_rotate = False
            handle_info_save = []
        elif(name == '左耳'):
            is_on_rotateL = False
            handle_info_saveL = []
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        self.execute(context)

        bpy.ops.wm.tool_set_by_id(name="my_tool.handle_initial")
        # 将激活物体设置为左/右耳
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj
        return {'FINISHED'}

    def execute(self, context):
        handleReset()
        return {'FINISHED'}


class HandleAdd(bpy.types.Operator):
    bl_idname = "object.handleadd"
    bl_label = "添加附件"

    def invoke(self, context, event):

        bpy.context.scene.var = 14
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        global handle_info_save
        global handle_info_saveL
        name = bpy.context.scene.leftWindowObj
        handle_info_save_cur = None
        if name == '右耳':
            handle_info_save_cur = handle_info_save
        elif name == '左耳':
            handle_info_save_cur = handle_info_saveL


        # 先将未提交的附件提交
        handleSubmit()
        #双击添加过一个附件之后,才能够继续添加附件
        if (len(handle_info_save_cur) == 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.handle_initial")
            return {'FINISHED'}
        #创建新的Handle
        addHandle()
        # 将Plane激活并选中
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        # 将新创建的字体位置设置未上一个提交的字体位置
        handleInfo = handle_info_save_cur[len(handle_info_save_cur) - 1]
        l_x = handleInfo.l_x
        l_y = handleInfo.l_y
        l_z = handleInfo.l_z
        r_x = handleInfo.r_x
        r_y = handleInfo.r_y
        r_z = handleInfo.r_z
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        is_on_rotate_cur = False
        if(name == '右耳'):
            is_on_rotate_cur = is_on_rotate
        elif(name == '左耳'):
            is_on_rotate_cur = is_on_rotateL
        cubename = name + "Cube"
        handle_obj = bpy.data.objects.get(cubename)
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 14):
            #公共鼠标行为 和 附件平面旋转拖拽鼠标行为之间的切换
            if(not is_on_rotate_cur):
                if (is_mouse_on_object(context, event) and not is_mouse_on_handle(context, event) and (
                        is_changed_handle(context, event) or is_changed(context, event))):
                    #公共鼠标行为加双击移动附件位置,将附件设置为默认颜色
                    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="my_tool.handle_mouse")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
                elif (is_mouse_on_handle(context, event) and (is_changed_handle(context,event) or is_changed(context,event))):
                    # 调用handle的鼠标行为,将附件设置为选中的颜色
                    yellow_material = newColor("HandleYellow", 1, 1, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(yellow_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                    plane_obj.select_set(True)
                    bpy.context.view_layer.objects.active = plane_obj
                    cur_obj.select_set(False)
                elif ((not is_mouse_on_object(context, event)) and (is_changed_handle(context,event) or is_changed(context,event))):
                    # 调用公共鼠标行为,将附件设置为默认颜色
                    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
            # 公共鼠标行为 和 附件三维旋转鼠标行为之间的切换
            elif(is_on_rotate_cur):
                if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                        is_changed_sphere(context, event) or is_changed(context, event))):
                    #公共鼠标行为加双击移动附件位置,将附件设置为默认颜色
                    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="my_tool.handle_mouse")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
                elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                    # 调用handle的三维旋转鼠标行为,将附件设置为选中的颜色
                    yellow_material = newColor("HandleYellow", 1, 1, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(yellow_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                    plane_obj.select_set(True)
                    bpy.context.view_layer.objects.active = plane_obj
                    cur_obj.select_set(False)
                elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                    # 调用公共鼠标行为,将附件设置为默认颜色
                    red_material = bpy.data.materials.new(name="HandleRed")
                    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class HandleInitialAdd(bpy.types.Operator):
    bl_idname = "object.handleinitialadd"
    bl_label = "添加附件"

    def invoke(self, context, event):

        bpy.context.scene.var = 15
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        #添加一个附件
        addHandle()
        # 将Plane激活并选中
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context, event)
        if (co != -1):
            handle_fit_rotate(normal,co)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        is_on_rotate_cur = False
        if(name == '右耳'):
            is_on_rotate_cur = is_on_rotate
        elif(name == '左耳'):
            is_on_rotate_cur = is_on_rotateL
        cubename = name + "Cube"
        handle_obj = bpy.data.objects.get(cubename)
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 15):
            #公共鼠标行为 和 附件平面旋转拖拽鼠标行为之间的切换
            if(not is_on_rotate_cur):
                if (is_mouse_on_object(context, event) and not is_mouse_on_handle(context, event) and (
                        is_changed_handle(context, event) or is_changed(context, event))):
                    #公共鼠标行为加双击移动附件位置,将附件设置为默认颜色
                    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="my_tool.handle_mouse")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
                elif (is_mouse_on_handle(context, event) and (is_changed_handle(context,event) or is_changed(context,event))):
                    # 调用handle的鼠标行为,将附件设置为选中的颜色
                    yellow_material = newColor("HandleYellow", 1, 1, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(yellow_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                    plane_obj.select_set(True)
                    bpy.context.view_layer.objects.active = plane_obj
                    cur_obj.select_set(False)
                elif ((not is_mouse_on_object(context, event)) and (is_changed_handle(context,event) or is_changed(context,event))):
                    # 调用公共鼠标行为,将附件设置为默认颜色
                    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
            # 公共鼠标行为 和 附件三维旋转鼠标行为之间的切换
            elif(is_on_rotate_cur):
                if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                        is_changed_sphere(context, event) or is_changed(context, event))):
                    #公共鼠标行为加双击移动附件位置,将附件设置为默认颜色
                    red_material = newColor("HandleRed", 1, 0, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="my_tool.handle_mouse")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
                elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                    # 调用handle的三维旋转鼠标行为,将附件设置为选中的颜色
                    yellow_material = newColor("HandleYellow", 1, 1, 0, 0, 1)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(yellow_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                    plane_obj.select_set(True)
                    bpy.context.view_layer.objects.active = plane_obj
                    cur_obj.select_set(False)
                elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                    # 调用公共鼠标行为,将附件设置为默认颜色
                    red_material = bpy.data.materials.new(name="HandleRed")
                    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                    handle_obj.data.materials.clear()
                    handle_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class HandleSubmit(bpy.types.Operator):
    bl_idname = "object.handlesubmit"
    bl_label = "附件提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 16
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        handleSubmit()
        return {'FINISHED'}


class HandleDoubleClick(bpy.types.Operator):
    bl_idname = "object.handledoubleclick"
    bl_label = "双击改变附件位置"

    def invoke(self, context, event):
        # 将Plane激活并选中,位置设置为双击的位置
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context, event)
        if (co != -1):
            handle_fit_rotate(normal,co)
            # plane_obj.location = co
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}

class HandleRotate(bpy.types.Operator):
    bl_idname = "object.handlerotate"
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
        spherename = name + "HandleSphere"
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

class MyTool_Handle1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_reset"
    bl_label = "附件重置"
    bl_description = (
        "重置模型,清除模型上的所有附件"
    )
    bl_icon = "ops.pose.breakdowner"
    bl_widget = None
    bl_keymap = (
        ("object.handlereset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_add"
    bl_label = "附件添加"
    bl_description = (
        "在模型的上一个附件的位置上添加一个附件"
    )
    bl_icon = "ops.pose.relax"
    bl_widget = None
    bl_keymap = (
        ("object.handleadd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.handleadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_submit"
    bl_label = "附件提交"
    bl_description = (
        "对于模型上所有附件提交实体化"
    )
    bl_icon = "ops.pose.push"
    bl_widget = None
    bl_keymap = (
        ("object.handlesubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Handle_Rotate(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_rotate"
    bl_label = "附件旋转"
    bl_description = (
        "添加附件后,调用附件三维旋转鼠标行为"
    )
    bl_icon = "brush.gpencil_draw.draw"
    bl_widget = None
    bl_keymap = (
        ("object.handlerotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Handle_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_mirror"
    bl_label = "附件镜像"
    bl_description = (
        "点击镜像附件"
    )
    bl_icon = "brush.gpencil_draw.erase"
    bl_widget = None
    bl_keymap = (
        ("object.handlemirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Handle_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_mouse"
    bl_label = "双击改变附件位置"
    bl_description = (
        "添加附件后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.uv_sculpt.grab"
    bl_widget = None
    bl_keymap = (
        ("object.handledoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_HandleInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_initial"
    bl_label = "附件添加初始化"
    bl_description = (
        "刚进入附件模块的时,在模型上双击位置处添加一个附件"
    )
    bl_icon = "brush.sculpt.topology"
    bl_widget = None
    bl_keymap = (
        ("object.handleinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    HandleReset,
    HandleAdd,
    HandleInitialAdd,
    HandleSubmit,
    HandleDoubleClick,
    HandleRotate
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Handle1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Handle2, separator=True, group=False, after={MyTool_Handle1.bl_idname})
    bpy.utils.register_tool(MyTool_Handle3, separator=True, group=False, after={MyTool_Handle2.bl_idname})
    bpy.utils.register_tool(MyTool_Handle_Rotate, separator=True, group=False, after={MyTool_Handle3.bl_idname})
    bpy.utils.register_tool(MyTool_Handle_Mirror, separator=True, group=False, after={MyTool_Handle_Rotate.bl_idname})
    bpy.utils.register_tool(MyTool_Handle_Mouse, separator=True, group=False, after={MyTool_Handle_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_HandleInitial, separator=True, group=False, after={MyTool_Handle_Mouse.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Handle1)
    bpy.utils.unregister_tool(MyTool_Handle2)
    bpy.utils.unregister_tool(MyTool_Handle3)
    bpy.utils.unregister_tool(MyTool_Handle_Rotate)
    bpy.utils.unregister_tool(MyTool_Handle_Mirror)
    bpy.utils.unregister_tool(MyTool_Handle_Mouse)
    bpy.utils.unregister_tool(MyTool_HandleInitial)
