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

is_add_sprue = False  # 是否添加过支撑,只能添加一个支撑

prev_location_x = 0  # 记录通气管位置
prev_location_y = 0
prev_location_z = 0
prev_rotation_x = 0
prev_rotation_y = 0
prev_rotation_z = 0

sprue_offset = 0  # 支撑偏移量


# 判断鼠标是否在物体上
def is_mouse_on_sprue(context, event):
    name_outer = "CylinderOuter"
    name_inside = "CylinderInside"
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
def is_changed(context, event):
    name = "CylinderOuter"
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


# 获取鼠标在右耳上的坐标
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


def frontToSprue():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SprueReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # cur_obj = bpy.data.objects["右耳"]
    # initialTransparency()
    # cur_obj.data.materials.clear()
    # cur_obj.data.materials.append(bpy.data.materials['Transparency'])

    name = "右耳"
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SprueReset"
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.hide_set(True)

    castingname = "CastingCompare"
    casting_obj = bpy.data.objects[castingname]
    duplicate_obj1 = casting_obj.copy()
    duplicate_obj1.data = casting_obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = castingname + "SprueReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    sprueInitial()


def frontFromSprue():

    sprueSaveInfo()

    sprue_inner_obj = bpy.data.objects.get("CylinderInner")
    sprue_outer_obj = bpy.data.objects.get("CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get("CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get("CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get("CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get("CylinderInsideOffsetCompare")
    sprue_compare_obj = bpy.data.objects.get("SprueCompare")
    support_compare_obj = bpy.data.objects.get("ConeCompare")
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
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
    if (sprue_compare_obj != None):
        bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)
    if (support_compare_obj != None):
        bpy.data.objects.remove(support_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)

    name = "右耳"
    obj = bpy.data.objects[name]
    resetname = name + "SprueReset"
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
    castingresetname = castingname + "SprueReset"
    ori_casting_obj = bpy.data.objects[castingresetname]
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
        if (selected_obj.name == "右耳SprueReset"  or selected_obj.name == "CastingCompareSprueReset"
                or selected_obj.name == "右耳SprueLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToSprue():
    exist_SprueReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SprueReset"):
            exist_SprueReset = True
    if (exist_SprueReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "SprueReset"
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

        sprueInitial()
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳SupportLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳CastingLast") != None):
            lastname = "右耳CastingLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LabelLast") != None):
            lastname = "右耳LabelLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳HandleLast") != None):
            lastname = "右耳HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
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

        sprueInitial()


def backFromSprue():
    sprueSaveInfo()
    sprueSubmit()

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SprueLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SprueLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)





def createSprue():
    #创建半径不同的两个圆柱,使用布尔修改器用小圆柱切割大圆柱创建排气孔
    bpy.ops.mesh.primitive_cylinder_add(vertices=300, radius=1, depth=3.6, enter_editmode=False, align='WORLD',
                                        location=(0, 0, 1.8), scale=(1, 1, 1))
    bpy.ops.mesh.primitive_cylinder_add(vertices=300, radius=0.6, depth=3.8, enter_editmode=False, align='WORLD',
                                        location=(0, 0, 1.8), scale=(1, 1, 1))
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', scale=(4, 4, 1))

    plane = bpy.data.objects.get("Plane")
    obj = bpy.data.objects.get("Cylinder")                #大圆柱
    obj1 = bpy.data.objects.get("Cylinder.001")           #小圆柱

    plane.location[2] = 1                                 #设置平面初始位置

    #将平面切割为与圆柱截面相同的圆形
    plane.select_set(True)
    obj1.select_set(False)
    obj.select_set(False)
    bpy.context.view_layer.objects.active = plane
    modifierPlaneCreate = plane.modifiers.new(name="PlaneCreate", type='BOOLEAN')
    modifierPlaneCreate.object = obj
    modifierPlaneCreate.operation = 'INTERSECT'
    modifierPlaneCreate.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="PlaneCreate")

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
    obj.name = "CylinderOuter"          #排气孔外壁
    obj1.name = "CylinderInside"        #小圆柱作为内芯,提交后将其删除
    obj2.name = "CylinderInner"         #排气孔内壁


    #为内外壁和内芯添加红色材质
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
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
    initialTransparency()
    plane.data.materials.clear()
    plane.data.materials.append(bpy.data.materials['Transparency'])

    #将内外壁复制出来一份作为参数offset偏移的对比物
    cylinder_outer_compare_offset_obj = obj.copy()
    cylinder_outer_compare_offset_obj.data = obj.data.copy()
    cylinder_outer_compare_offset_obj.animation_data_clear()
    cylinder_outer_compare_offset_obj.name = "CylinderOuterOffsetCompare"
    bpy.context.collection.objects.link(cylinder_outer_compare_offset_obj)
    # cylinder_outer_compare_offset_obj.hide_set(True)
    cylinder_inner_compare_offset_obj = obj2.copy()
    cylinder_inner_compare_offset_obj.data = obj2.data.copy()
    cylinder_inner_compare_offset_obj.animation_data_clear()
    cylinder_inner_compare_offset_obj.name = "CylinderInnerOffsetCompare"
    bpy.context.collection.objects.link(cylinder_inner_compare_offset_obj)
    # cylinder_inner_compare_offset_obj.hide_set(True)
    cylinder_inside_compare_offset_obj = obj1.copy()
    cylinder_inside_compare_offset_obj.data = obj1.data.copy()
    cylinder_inside_compare_offset_obj.animation_data_clear()
    cylinder_inside_compare_offset_obj.name = "CylinderInsideOffsetCompare"
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
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    obj.select_set(False)
    #内外壁对比物隐藏
    cylinder_outer_compare_offset_obj.hide_set(True)
    cylinder_inner_compare_offset_obj.hide_set(True)
    cylinder_inside_compare_offset_obj.hide_set(True)

    moveToRight(plane)
    moveToRight(obj)
    moveToRight(obj1)
    moveToRight(obj2)
    moveToRight(cylinder_outer_compare_offset_obj)
    moveToRight(cylinder_inner_compare_offset_obj)
    moveToRight(cylinder_inside_compare_offset_obj)




def sprueSaveInfo():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global sprue_offset

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 记录附件位置信息
    if (plane_obj != None):
        prev_location_x = plane_obj.location[0]
        prev_location_y = plane_obj.location[1]
        prev_location_z = plane_obj.location[2]
        prev_rotation_x = plane_obj.rotation_euler[0]
        prev_rotation_y = plane_obj.rotation_euler[1]
        prev_rotation_z = plane_obj.rotation_euler[2]
    sprue_offset = bpy.context.scene.paiQiKongOffset


def sprueInitial():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global sprue_offset
    global is_add_sprue

    if (is_add_sprue == True):
        addSprue()
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
        bpy.context.scene.paiQiKongOffset = sprue_offset
        bpy.ops.object.sprueadd('INVOKE_DEFAULT')
    else:
        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_add")


def sprueReset():
    # 存在未提交排气孔时
    sprue_inner_obj = bpy.data.objects.get("CylinderInner")
    sprue_outer_obj = bpy.data.objects.get("CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get("CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get("CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get("CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get("CylinderInsideOffsetCompare")
    sprue_compare_obj = bpy.data.objects.get("SprueCompare")
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
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
    if (sprue_compare_obj != None):
        bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    # 将SprueReset复制并替代当前操作模型,将CastingCompareSprueReset复制并替代CastingCompare
    oriname = "右耳"
    ori_obj = bpy.data.objects.get(oriname)                   #右耳
    oricastingname= "CastingCompare"
    ori_casting_obj = bpy.data.objects.get(oricastingname)    #铸造法内层物体
    copyname = "右耳SprueReset"
    ori_copy_obj = bpy.data.objects.get(copyname)             #右耳reset物体
    castingcopyname = "CastingCompareSprueReset"                   #铸造法内层reset物体
    ori_casting_copy_obj = bpy.data.objects.get(castingcopyname)
    if (ori_obj != None and ori_casting_obj != None and ori_copy_obj != None and ori_casting_copy_obj != None):
        #将CastingCompare还原
        bpy.data.objects.remove(ori_casting_obj, do_unlink=True)
        duplicate_obj1 = ori_casting_copy_obj.copy()
        duplicate_obj1.data = ori_casting_copy_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = oricastingname
        bpy.context.collection.objects.link(duplicate_obj1)
        moveToRight(duplicate_obj1)

        #将右耳还原
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = ori_copy_obj.copy()
        duplicate_obj.data = ori_copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj



def submitSprue():
    obj_outer = bpy.data.objects.get("右耳")
    obj_inner = bpy.data.objects.get("CastingCompare")

    cylinderOuter = bpy.data.objects.get("CylinderOuter")
    cylinderInner = bpy.data.objects.get("CylinderInner")
    cylinderInside = bpy.data.objects.get("CylinderInside")
    cylinderOuterOffsetCompare = bpy.data.objects.get("CylinderOuterOffsetCompare")
    cylinderInnerOffsetCompare = bpy.data.objects.get("CylinderInnerOffsetCompare")
    plane = bpy.data.objects.get("Plane")


    obj_inner.select_set(True)
    bpy.context.view_layer.objects.active = obj_inner
    modifierSprueUnionInner = obj_inner.modifiers.new(name="SprueUnionInner", type='BOOLEAN')
    modifierSprueUnionInner.object = cylinderInner
    modifierSprueUnionInner.operation = 'UNION'
    modifierSprueUnionInner.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SprueUnionInner")

    obj_outer.select_set(True)
    bpy.context.view_layer.objects.active = obj_outer
    modifierSprueUnionOuter = obj_outer.modifiers.new(name="SprueUnionOuter", type='BOOLEAN')
    modifierSprueUnionOuter.object = cylinderOuter
    modifierSprueUnionOuter.operation = 'UNION'
    modifierSprueUnionOuter.solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="SprueUnionOuter")

    bpy.data.objects.remove(plane, do_unlink=True)
    bpy.data.objects.remove(cylinderOuter, do_unlink=True)
    bpy.data.objects.remove(cylinderInner, do_unlink=True)
    bpy.data.objects.remove(cylinderInside, do_unlink=True)
    bpy.data.objects.remove(cylinderOuterOffsetCompare, do_unlink=True)
    bpy.data.objects.remove(cylinderInnerOffsetCompare, do_unlink=True)

def sprueSubmit():
    #  sprue_obj为排气孔物体,  sprue_offset_compare为隐藏的排气孔物体,用于偏移量参照,创建排气孔时一同创建   sprue_compare则作为对比,因为sprue_obj在提交后会变透明

    sprue_inner_obj = bpy.data.objects.get("CylinderInner")
    sprue_outer_obj = bpy.data.objects.get("CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get("CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get("CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get("CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get("CylinderInsideOffsetCompare")
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)

    obj_outer = bpy.data.objects.get("右耳")
    obj_inner = bpy.data.objects.get("CastingCompare")


    # 存在未提交的Sprue,SprueCompare和Plane时
    if (sprue_inner_obj != None and sprue_outer_obj != None and  sprue_inside_obj != None and plane_obj != None
            and  sprue_inner_offset_compare_obj != None and sprue_outer_offset_compare_obj != None
            and sprue_inside_offset_compare_obj != None and  obj_outer != None and obj_inner != None):


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
        sprue_compare_obj = bpy.data.objects.get("右耳.001")
        if (sprue_compare_obj != None):
            sprue_compare_obj.name = "SprueCompare"
            yellow_material = bpy.data.materials.new(name="Yellow")
            yellow_material.diffuse_color = (1.0, 0.319, 0.133, 1.0)
            sprue_compare_obj.data.materials.clear()
            sprue_compare_obj.data.materials.append(yellow_material)
            moveToRight(sprue_compare_obj)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
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
            if (selected_obj.name == "右耳"):
                bpy.context.view_layer.objects.active = selected_obj
                selected_obj.select_set(True)
            else:
                selected_obj.select_set(False)


def addSprue():

    createSprue()

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
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


class SprueTest(bpy.types.Operator):
    bl_idname = "object.spruetestfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):

        return {'FINISHED'}




class SprueReset(bpy.types.Operator):
    bl_idname = "object.spruereset"
    bl_label = "排气孔重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 16
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_add_sprue
        is_add_sprue = False
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        sprueSaveInfo()
        sprueReset()
        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_add")
        return {'FINISHED'}


class SprueAdd(bpy.types.Operator):
    bl_idname = "object.sprueadd"
    bl_label = "添加排气孔"

    def invoke(self, context, event):

        bpy.context.scene.var = 17
        global is_add_sprue
        global sprue_offset
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if (not is_add_sprue):
            is_add_sprue = True
            addSprue()
            bpy.context.scene.paiQiKongOffset = sprue_offset
            # 将Plane激活并选中
            planename = "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            co = cal_co(context, event)
            if (co != -1):
                plane_obj.location = co

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        sprue_inner_obj = bpy.data.objects.get("CylinderInner")
        sprue_outer_obj = bpy.data.objects.get("CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get("CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get("CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get("CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get("CylinderInsideOffsetCompare")
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = "右耳"
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 17):
            if (is_mouse_on_sprue(context, event) and is_changed(context, event)):
                # 调用sprue的鼠标行为
                yellow_material = bpy.data.materials.new(name="Yellow")
                yellow_material.diffuse_color = (1.0, 1.0, 0.0, 1.0)
                sprue_inner_obj.select_set(True)
                bpy.context.view_layer.objects.active = sprue_inner_obj
                sprue_inner_obj.data.materials.clear()
                sprue_inner_obj.data.materials.append(yellow_material)
                sprue_outer_obj.select_set(True)
                bpy.context.view_layer.objects.active = sprue_outer_obj
                sprue_outer_obj.data.materials.clear()
                sprue_outer_obj.data.materials.append(yellow_material)
                sprue_inside_obj.select_set(True)
                bpy.context.view_layer.objects.active = sprue_inside_obj
                sprue_inside_obj.data.materials.clear()
                sprue_inside_obj.data.materials.append(yellow_material)
                bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                cur_obj.select_set(False)
                sprue_inner_obj.select_set(False)
                sprue_outer_obj.select_set(False)
                sprue_inside_obj.select_set(False)
            elif ((not is_mouse_on_sprue(context, event)) and is_changed(context, event)):
                # 调用公共鼠标行为
                red_material = bpy.data.materials.new(name="Red")
                red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                sprue_inner_obj.select_set(True)
                bpy.context.view_layer.objects.active = sprue_inner_obj
                sprue_inner_obj.data.materials.clear()
                sprue_inner_obj.data.materials.append(red_material)
                sprue_outer_obj.select_set(True)
                bpy.context.view_layer.objects.active = sprue_outer_obj
                sprue_outer_obj.data.materials.clear()
                sprue_outer_obj.data.materials.append(red_material)
                sprue_inside_obj.select_set(True)
                bpy.context.view_layer.objects.active = sprue_inside_obj
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
        bpy.context.scene.var = 18
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        sprueSaveInfo()
        sprueSubmit()
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
        "在模型上添加一个排气孔"
    )
    bl_icon = "brush.sculpt.boundary"
    bl_widget = None
    bl_keymap = (
        ("object.sprueadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
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


# 注册类
_classes = [
    SprueReset,
    SprueAdd,
    SprueSubmit,
    SprueTest
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Sprue1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Sprue2, separator=True, group=False, after={MyTool_Sprue1.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue3, separator=True, group=False, after={MyTool_Sprue2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Sprue1)
    bpy.utils.unregister_tool(MyTool_Sprue2)
    bpy.utils.unregister_tool(MyTool_Sprue3)
