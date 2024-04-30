from asyncio import Handle
from venv import create
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re
from .tool import *

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变

is_add_support = False   #是否添加过支撑,只能添加一个支撑

prev_location_x = 0     #记录支撑位置
prev_location_y = 0
prev_location_z = 0
prev_rotation_x = 0
prev_rotation_y = 0
prev_rotation_z = 0

support_enum = "OP1"           #支撑类型
support_offset = 0             #支撑偏移量

# 判断鼠标是否在物体上
def is_mouse_on_hard_support(context, event):
    name = "Cone"
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
def is_changed_hard_support(context, event):
    name = "Cone"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_object  # 之前鼠标是否在物体上

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
        if (curr_on_object != prev_on_object):
            prev_on_object = curr_on_object
            return True
        else:
            return False
    return False

# 判断鼠标是否在物体上
def is_mouse_on_soft_support(context, event):
    name_outer = "SoftSupportOuter"
    name_inside = "SoftSupportInside"
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


# 判断鼠标状态是否发生改变
def is_changed_soft_support(context, event):
    name = "SoftSupportOuter"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_object  # 之前鼠标是否在物体上

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
        if (curr_on_object != prev_on_object):
            prev_on_object = curr_on_object
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

    active_obj = bpy.data.objects["右耳"]
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

            co, _, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None:
                return co  # 如果发生交叉，返回坐标的值

    return -1

def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.3

def frontToSupport():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # cur_obj = bpy.data.objects["右耳"]
    # initialTransparency()
    # cur_obj.data.materials.clear()
    # cur_obj.data.materials.append(bpy.data.materials['Transparency'])


    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SupportReset"
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.hide_set(True)

    castingname = "CastingCompare"
    casting_obj = bpy.data.objects[castingname]
    duplicate_obj1 = casting_obj.copy()
    duplicate_obj1.data = casting_obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = castingname + "SupportReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)


    supportInitial()

def frontFromSupport():
    supportSaveInfo()
    hard_support_obj = bpy.data.objects.get("Cone")
    hard_support_offset_compare_obj = bpy.data.objects.get("ConeOffsetCompare")
    hard_support_compare_obj = bpy.data.objects.get("ConeCompare")
    soft_support_inner_obj = bpy.data.objects.get("SoftSupportInner")
    soft_support_outer_obj = bpy.data.objects.get("SoftSupportOuter")
    soft_support_inside_obj = bpy.data.objects.get("SoftSupportInside")
    soft_support_inner_offset_compare_obj = bpy.data.objects.get("SoftSupportInnerOffsetCompare")
    soft_support_outer_offset_compare_obj = bpy.data.objects.get("SoftSupportOuterOffsetCompare")
    soft_support_inside_offset_compare_obj = bpy.data.objects.get("SoftSupportInsideOffsetCompare")
    soft_support_compare_obj = bpy.data.objects.get("SoftSupportCompare")
    planename = "Plane"
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
    name = "右耳"  # TODO    根据导入文件名称更改Support
    obj = bpy.data.objects[name]
    resetname = name + "SupportReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    castingname = "CastingCompare"
    casting_obj = bpy.data.objects[castingname]
    castingresetname = castingname + "SupportReset"
    ori_casting_obj = bpy.data.objects.get(castingresetname)
    if (ori_casting_obj == None):
        ori_casting_obj = bpy.data.objects.get("右耳CastingCompareLast")
    bpy.data.objects.remove(casting_obj, do_unlink=True)
    duplicate_obj1 = ori_casting_obj.copy()
    duplicate_obj1.data = ori_casting_obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = castingname
    bpy.context.scene.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.select_set(False)

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportReset" or selected_obj.name == "右耳SupportLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToSupport():
    exist_SupportReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportReset"):
            exist_SupportReset = True
    if (exist_SupportReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "SupportReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        supportInitial()
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳CastingLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LabelLast") != None):
            lastname = "右耳LabelLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳HandleLast") != None):
            lastname = "右耳HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        # cur_obj = bpy.data.objects["右耳"]
        # initialTransparency()
        # cur_obj.data.materials.clear()
        # cur_obj.data.materials.append(bpy.data.materials['Transparency'])

        supportInitial()

def backFromSupport():
    support_enum = bpy.context.scene.zhiChengTypeEnum

    supportSaveInfo()
    if support_enum == "OP1":
        hardSupportSubmit()
    elif support_enum == "OP2":
        softSupportSubmit()

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SupportLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)


def createHardMouldSupport():
    '''
        用平面切去圆锥的一角，创建出硬耳膜支撑
    '''
    bpy.ops.mesh.primitive_cone_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.scale[0] = 3
    bpy.context.object.scale[1] = 3
    bpy.context.object.scale[2] = 3

    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, 1), scale=(1, 1, 1))
    bpy.context.object.scale[0] = 3
    bpy.context.object.scale[1] = 3
    bpy.context.object.scale[2] = 3

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    conename = "Cone"
    cone_obj = bpy.data.objects.get(conename)

    #反转平面的法线方向
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')
    #添加修改器,使用平面将圆锥切割成支撑
    bpy.context.view_layer.objects.active = cone_obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["Boolean"].object = plane_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    #减去平面多余的部分
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers["Boolean"].object = cone_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    #将支撑上下翻转，防止其吸附到内壁上
    bpy.context.view_layer.objects.active = cone_obj
    bpy.context.object.rotation_euler[1] = 3.14159
    bpy.context.object.location[2] = 2

    cone_compare_offset_obj = cone_obj.copy()
    cone_compare_offset_obj.data = cone_obj.data.copy()
    cone_compare_offset_obj.animation_data_clear()
    cone_compare_offset_obj.name = conename + "OffsetCompare"
    bpy.context.collection.objects.link(cone_compare_offset_obj)
    moveToRight(plane_obj)
    moveToRight(cone_obj)
    moveToRight(cone_compare_offset_obj)

    # 为硬耳膜支撑添加红色材质
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    cone_obj.select_set(True)
    bpy.context.view_layer.objects.active = cone_obj
    cone_obj.data.materials.clear()
    cone_obj.data.materials.append(red_material)
    # 为平面添加透明材质
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    initialTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['Transparency'])

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
    bpy.ops.wm.stl_import(filepath="C:\\Users\\28712\Desktop\\耳膜附件\\SoftSupportInner.stl")
    bpy.ops.wm.stl_import(filepath="C:\\Users\\28712\Desktop\\耳膜附件\\SoftSupportInside.stl")
    bpy.ops.wm.stl_import(filepath="C:\\Users\\28712\Desktop\\耳膜附件\\SoftSupportOuter.stl")
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', scale=(4, 4, 1))

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    support_inner_name = "SoftSupportInner"
    support_inner_obj = bpy.data.objects[support_inner_name]
    support_inner_obj.location[0] = -100
    support_inner_obj.location[1] = -100
    support_inside_name = "SoftSupportInside"
    support_inside_obj = bpy.data.objects[support_inside_name]
    support_inside_obj.location[0] = -100
    support_inside_obj.location[1] = -100
    support_outer_name = "SoftSupportOuter"
    support_outer_obj = bpy.data.objects[support_outer_name]
    support_outer_obj.location[0] = -100
    support_outer_obj.location[1] = -100
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]

    plane_obj.location[2] = 1                                    # 设置平面初始位置
    plane_obj.location[0] = -100
    plane_obj.location[1] = -100
    plane_obj.scale[0] = 4
    plane_obj.scale[1] = 4

    # 将平面切割为与圆柱截面相同的圆形
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    modifierPlaneCreate = plane_obj.modifiers.new(name="PlaneCreate", type='BOOLEAN')
    modifierPlaneCreate.object = support_outer_obj
    modifierPlaneCreate.operation = 'INTERSECT'
    modifierPlaneCreate.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="PlaneCreate")




    # 为内外壁和内芯添加红色材质
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
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
    initialTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['Transparency'])

    # 将内外壁复制出来一份作为参数offset偏移的对比物
    support_outer_compare_offset_obj = support_outer_obj.copy()
    support_outer_compare_offset_obj.data = support_outer_obj.data.copy()
    support_outer_compare_offset_obj.animation_data_clear()
    support_outer_compare_offset_obj.name = "SoftSupportOuterOffsetCompare"
    bpy.context.collection.objects.link(support_outer_compare_offset_obj)
    # support_outer_compare_offset_obj.hide_set(True)
    support_inner_compare_offset_obj = support_inner_obj.copy()
    support_inner_compare_offset_obj.data = support_inner_obj.data.copy()
    support_inner_compare_offset_obj.animation_data_clear()
    support_inner_compare_offset_obj.name = "SoftSupportInnerOffsetCompare"
    bpy.context.collection.objects.link(support_inner_compare_offset_obj)
    # support_inner_compare_offset_obj.hide_set(True)
    support_inside_compare_offset_obj = support_inside_obj.copy()
    support_inside_compare_offset_obj.data = support_inside_obj.data.copy()
    support_inside_compare_offset_obj.animation_data_clear()
    support_inside_compare_offset_obj.name = "SoftSupportInsideOffsetCompare"
    bpy.context.collection.objects.link(support_inside_compare_offset_obj)
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

    plane_obj.scale[0] = 2
    plane_obj.scale[1] = 2
    plane_obj.scale[2] = 0.5

    moveToRight(plane_obj)
    moveToRight(support_outer_obj)
    moveToRight(support_inner_obj)
    moveToRight(support_inside_obj)
    moveToRight(support_outer_compare_offset_obj)
    moveToRight(support_inner_compare_offset_obj)
    moveToRight(support_inside_compare_offset_obj)


def supportSaveInfo():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global support_enum
    global support_offset

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    #记录附件位置信息
    if(plane_obj != None):
        prev_location_x = plane_obj.location[0]
        prev_location_y = plane_obj.location[1]
        prev_location_z = plane_obj.location[2]
        prev_rotation_x = plane_obj.rotation_euler[0]
        prev_rotation_y = plane_obj.rotation_euler[1]
        prev_rotation_z = plane_obj.rotation_euler[2]
    support_enum = bpy.context.scene.zhiChengTypeEnum
    support_offset = bpy.context.scene.zhiChengOffset


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

    if(is_add_support == True):
        addSupport()
        # 将Plane激活并选中
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        plane_obj.location[0] = prev_location_x
        plane_obj.location[1] = prev_location_y
        plane_obj.location[2] = prev_location_z
        plane_obj.rotation_euler[0] = prev_rotation_x
        plane_obj.rotation_euler[1] = prev_rotation_y
        plane_obj.rotation_euler[2] = prev_rotation_z
        bpy.context.scene.zhiChengOffset = support_offset
        bpy.ops.object.supportadd('INVOKE_DEFAULT')
    else:
        bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")






def supportReset():
    # 存在未提交支撑时,删除支撑相关物体
    hard_support_obj = bpy.data.objects.get("Cone")
    hard_support_offset_compare_obj = bpy.data.objects.get("ConeOffsetCompare")
    hard_support_compare_obj = bpy.data.objects.get("ConeCompare")
    soft_support_inner_obj = bpy.data.objects.get("SoftSupportInner")
    soft_support_outer_obj = bpy.data.objects.get("SoftSupportOuter")
    soft_support_inside_obj = bpy.data.objects.get("SoftSupportInside")
    soft_support_inner_offset_compare_obj = bpy.data.objects.get("SoftSupportInnerOffsetCompare")
    soft_support_outer_offset_compare_obj = bpy.data.objects.get("SoftSupportOuterOffsetCompare")
    soft_support_inside_offset_compare_obj = bpy.data.objects.get("SoftSupportInsideOffsetCompare")
    soft_support_compare_obj = bpy.data.objects.get("SoftSupportCompare")
    planename = "Plane"
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
    oriname = "右耳"  # TODO    右耳最终需要替换为导入时的文件名  右耳SupportReset同理
    ori_obj = bpy.data.objects.get(oriname)
    copyname = "右耳SupportReset"
    copy_obj = bpy.data.objects.get(copyname)
    if (ori_obj != None and copy_obj != None):
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = copy_obj.copy()
        duplicate_obj.data = copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj
    # 将SupportReset复制并替代CastingCompare
    castingname = "CastingCompare"
    casting_obj = bpy.data.objects[castingname]
    castingresetname = castingname + "SupportReset"
    ori_casting_obj = bpy.data.objects.get(castingresetname)
    if(ori_casting_obj == None):
        ori_casting_obj = bpy.data.objects.get( "右耳CastingCompareLast")
    if(casting_obj != None and ori_casting_obj != None):
        bpy.data.objects.remove(casting_obj, do_unlink=True)
        duplicate_obj1 = ori_casting_obj.copy()
        duplicate_obj1.data = ori_casting_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = castingname
        bpy.context.scene.collection.objects.link(duplicate_obj1)
        moveToRight(duplicate_obj1)
        duplicate_obj1.select_set(False)

def hardSupportSubmit():
    #  support_obj为支撑物体,  support_offset_compare为隐藏的支撑物体,用于偏移量参照,创建支撑时一同创建   support_compare则作为对比,因此support_obj在提交后会变透明
    name = "右耳"
    obj = bpy.data.objects.get(name)
    support_name = "Cone"
    support_offset_compare_name = "ConeOffsetCompare"
    support_obj = bpy.data.objects.get(support_name)
    support_offset_compare_obj = bpy.data.objects.get(support_offset_compare_name)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)

    #提交前保存参数
    supportSaveInfo()

    # 存在未提交的Support,SupportCompare和Plane时
    if (support_obj != None and plane_obj != None and support_offset_compare_obj != None):

        bpy.context.view_layer.objects.active = obj

        #由于支撑之前的模块存在布尔操作,会有其他顶点被选中,因此先将模型上选中顶点给取消选中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        #将支撑与当前模型合并
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = support_obj
        bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(support_obj, do_unlink=True)

        # 由于支撑物体和透明的右耳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比
        bpy.ops.object.mode_set(mode='EDIT')
        #布尔合并后的顶点会被选中,将这些顶点复制一份并分离为独立的物体
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        support_compare_obj = bpy.data.objects.get("右耳.001")
        if(support_compare_obj != None):
            support_compare_obj.name = "ConeCompare"
            yellow_material = bpy.data.materials.new(name="Yellow")
            yellow_material.diffuse_color = (1.0, 0.319, 0.133, 1.0)
            support_compare_obj.data.materials.clear()
            support_compare_obj.data.materials.append(yellow_material)

        bpy.data.objects.remove(support_offset_compare_obj, do_unlink=True)

        # 合并后Support会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')

        #将当前激活物体设置为右耳,并将其他物体取消选中
        for selected_obj in  bpy.data.objects:
            if (selected_obj.name == "右耳"):
                bpy.context.view_layer.objects.active = selected_obj
                selected_obj.select_set(True)
            else:
                selected_obj.select_set(False)

def softSupportSubmit():
    #  support_obj为排气孔物体,  support_offset_compare为隐藏的排气孔物体,用于偏移量参照,创建排气孔时一同创建   support_compare则作为对比,因为sprue_obj在提交后会变透明

    support_inner_obj = bpy.data.objects.get("SoftSupportInner")
    support_outer_obj = bpy.data.objects.get("SoftSupportOuter")
    support_inside_obj = bpy.data.objects.get("SoftSupportInside")
    support_inner_offset_compare_obj = bpy.data.objects.get("SoftSupportInnerOffsetCompare")
    support_outer_offset_compare_obj = bpy.data.objects.get("SoftSupportOuterOffsetCompare")
    support_inside_offset_compare_obj = bpy.data.objects.get("SoftSupportInsideOffsetCompare")
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)

    obj_outer = bpy.data.objects.get("右耳")
    obj_inner = bpy.data.objects.get("CastingCompare")


    # 存在未提交的SoftSupport,SoftSupportCompare和Plane时
    if (support_inner_obj != None and support_outer_obj != None and  support_inside_obj != None and plane_obj != None
            and  support_inner_offset_compare_obj != None and support_outer_offset_compare_obj != None
            and support_inside_offset_compare_obj != None and  obj_outer != None and obj_inner != None):


        obj_inner.select_set(True)
        bpy.context.view_layer.objects.active = obj_inner
        # 为铸造法内壁添加布尔修改器,与排气孔内壁合并
        modifierSprueUnionInner = obj_inner.modifiers.new(name="SupportUnionInner", type='BOOLEAN')
        modifierSprueUnionInner.object = support_inner_obj
        modifierSprueUnionInner.operation = 'UNION'
        modifierSprueUnionInner.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier="SupportUnionInner")

        support_outer_obj.select_set(True)
        bpy.context.view_layer.objects.active = support_outer_obj
        # 先将排气孔外壁选中,使得其与铸造法外壳合并后被选中分离
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        support_outer_obj.select_set(False)

        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer
        # 由于排气孔之前的模块存在布尔操作,会有其他顶点被选中,因此先将模型上选中顶点给取消选中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        #为铸造法外壳添加布尔修改器,与排气孔外壳合并
        modifierSprueUnionOuter = obj_outer.modifiers.new(name="SupportUnionOuter", type='BOOLEAN')
        modifierSprueUnionOuter.object = support_outer_obj
        modifierSprueUnionOuter.operation = 'UNION'
        modifierSprueUnionOuter.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier="SupportUnionOuter")
        # 由于排气孔物体和透明的右耳外壳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比,布尔合并后的顶点会被选中,将这些顶点复制一份并分离为独立的物体
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        sprue_compare_obj = bpy.data.objects.get("右耳.001")
        if (sprue_compare_obj != None):
            sprue_compare_obj.name = "SoftSupportCompare"
            yellow_material = bpy.data.materials.new(name="Yellow")
            yellow_material.diffuse_color = (1.0, 0.319, 0.133, 1.0)
            sprue_compare_obj.data.materials.clear()
            sprue_compare_obj.data.materials.append(yellow_material)
            moveToRight(sprue_compare_obj)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(support_inner_obj, do_unlink=True)
        bpy.data.objects.remove(support_outer_obj, do_unlink=True)
        bpy.data.objects.remove(support_inside_obj, do_unlink=True)
        bpy.data.objects.remove(support_inner_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(support_outer_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(support_inside_offset_compare_obj, do_unlink=True)

        bpy.context.view_layer.objects.active = obj_outer

        # 合并后Support会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 将当前激活物体设置为右耳,并将其他物体取消选中
        for selected_obj in bpy.data.objects:
            if (selected_obj.name == "右耳"):
                bpy.context.view_layer.objects.active = selected_obj
                selected_obj.select_set(True)
            else:
                selected_obj.select_set(False)


def addSupport():
    # 添加平面Plane和支撑Support
    support_enum = bpy.context.scene.zhiChengTypeEnum
    if support_enum == "OP1":
        createHardMouldSupport()
    elif support_enum == "OP2":
        createSoftMouldSupport()

    planename = "Plane"
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
        bpy.context.scene.var = 16
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_add_support
        is_add_support = False
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        supportSaveInfo()
        supportReset()
        bpy.ops.wm.tool_set_by_id(name="my_tool.support_add")
        return {'FINISHED'}


class SupportAdd(bpy.types.Operator):
    bl_idname = "object.supportadd"
    bl_label = "添加支撑"

    def invoke(self, context, event):

        bpy.context.scene.var = 17
        global is_add_support
        global support_offset
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if (not is_add_support):
            is_add_support = True
            addSupport()
            bpy.context.scene.zhiChengOffset = support_offset
            # 将Plane激活并选中
            planename = "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            co = cal_co(context, event)
            if(co != -1):
                plane_obj.location = co

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        support_enum = bpy.context.scene.zhiChengTypeEnum
        hard_support_name = "Cone"
        hard_support_obj = bpy.data.objects.get(hard_support_name)
        soft_support_inner_obj = bpy.data.objects.get("SoftSupportInner")
        soft_support_outer_obj = bpy.data.objects.get("SoftSupportOuter")
        soft_support_inside_obj = bpy.data.objects.get("SoftSupportInside")
        soft_support_inner_offset_compare_obj = bpy.data.objects.get("SoftSupportInnerOffsetCompare")
        soft_support_outer_offset_compare_obj = bpy.data.objects.get("SoftSupportOuterOffsetCompare")
        soft_support_inside_offset_compare_obj = bpy.data.objects.get("SoftSupportInsideOffsetCompare")
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = "右耳"
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 17):
            if support_enum == "OP1":
                if (is_mouse_on_hard_support(context, event) and is_changed_hard_support(context, event)):
                    # 调用hardSupport的鼠标行为
                    yellow_material = bpy.data.materials.new(name="Yellow")
                    yellow_material.diffuse_color = (1.0, 1.0, 0.0, 1.0)
                    hard_support_obj.data.materials.clear()
                    hard_support_obj.data.materials.append(yellow_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                    plane_obj.select_set(True)
                    bpy.context.view_layer.objects.active = plane_obj
                    cur_obj.select_set(False)
                elif ((not is_mouse_on_hard_support(context, event)) and is_changed_hard_support(context, event)):
                    # 调用公共鼠标行为
                    red_material = bpy.data.materials.new(name="Red")
                    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                    hard_support_obj.data.materials.clear()
                    hard_support_obj.data.materials.append(red_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    cur_obj.select_set(True)
                    bpy.context.view_layer.objects.active = cur_obj
                    plane_obj.select_set(False)
            elif support_enum == "OP2":
                if (is_mouse_on_soft_support(context, event) and is_changed_soft_support(context, event)):
                    # 调用softSupport的鼠标行为
                    yellow_material = bpy.data.materials.new(name="Yellow")
                    yellow_material.diffuse_color = (1.0, 1.0, 0.0, 1.0)
                    soft_support_inner_obj.select_set(True)
                    bpy.context.view_layer.objects.active = soft_support_inner_obj
                    soft_support_inner_obj.data.materials.clear()
                    soft_support_inner_obj.data.materials.append(yellow_material)
                    soft_support_outer_obj.select_set(True)
                    bpy.context.view_layer.objects.active = soft_support_outer_obj
                    soft_support_outer_obj.data.materials.clear()
                    soft_support_outer_obj.data.materials.append(yellow_material)
                    soft_support_inside_obj.select_set(True)
                    bpy.context.view_layer.objects.active = soft_support_inside_obj
                    soft_support_inside_obj.data.materials.clear()
                    soft_support_inside_obj.data.materials.append(yellow_material)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                    plane_obj.select_set(True)
                    bpy.context.view_layer.objects.active = plane_obj
                    cur_obj.select_set(False)
                    soft_support_inner_obj.select_set(False)
                    soft_support_outer_obj.select_set(False)
                    soft_support_inside_obj.select_set(False)
                elif ((not is_mouse_on_soft_support(context, event)) and is_changed_soft_support(context, event)):
                    # 调用公共鼠标行为
                    red_material = bpy.data.materials.new(name="Red")
                    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                    soft_support_inner_obj.select_set(True)
                    bpy.context.view_layer.objects.active = soft_support_inner_obj
                    soft_support_inner_obj.data.materials.clear()
                    soft_support_inner_obj.data.materials.append(red_material)
                    soft_support_outer_obj.select_set(True)
                    bpy.context.view_layer.objects.active = soft_support_outer_obj
                    soft_support_outer_obj.data.materials.clear()
                    soft_support_outer_obj.data.materials.append(red_material)
                    soft_support_inside_obj.select_set(True)
                    bpy.context.view_layer.objects.active = soft_support_inside_obj
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
            return {'FINISHED'}


class SupportSubmit(bpy.types.Operator):
    bl_idname = "object.supportsubmit"
    bl_label = "支撑提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 18
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        support_enum = bpy.context.scene.zhiChengTypeEnum
        supportSaveInfo()
        if support_enum == "OP1":
            hardSupportSubmit()
        elif support_enum == "OP2":
            softSupportSubmit()
        return {'FINISHED'}


class MyTool_Support1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_reset"
    bl_label = "支撑重置"
    bl_description = (
        "重置模型,清除模型上的所有支撑"
    )
    bl_icon = "ops.transform.bone_envelope"
    bl_widget = None
    bl_keymap = (
        ("object.supportreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Support2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_add"
    bl_label = "支撑添加"
    bl_description = (
        "在模型上添加一个支撑"
    )
    bl_icon = "ops.transform.bone_size"
    bl_widget = None
    bl_keymap = (
        # ("object.supportadd", {"type": 'MOUSEMOVE', "value": 'ANY'},
        #  {}),
        ("object.supportadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Support3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_submit"
    bl_label = "支撑提交"
    bl_description = (
        "对于模型上所有支撑提交实体化"
    )
    bl_icon = "ops.transform.edge_slide"
    bl_widget = None
    bl_keymap = (
        ("object.supportsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    SupportReset,
    SupportAdd,
    SupportSubmit,
    SupportTest,
    SupportTest1
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Support1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Support2, separator=True, group=False, after={MyTool_Support1.bl_idname})
    bpy.utils.register_tool(MyTool_Support3, separator=True, group=False, after={MyTool_Support2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Support1)
    bpy.utils.unregister_tool(MyTool_Support2)
    bpy.utils.unregister_tool(MyTool_Support3)
