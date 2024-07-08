from os import dup
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re
from .tool import *

default_plane_size_x = 1  # 记录添加字体后平面的x轴默认尺寸,此时默认字体大小为4
default_plane_size_y = 1  # 记录添加字体后平面的y轴默认尺寸,此时默认字体大小为4
default_plane_size_xL = 1
default_plane_size_yL = 1

prev_on_label = False  # 判断鼠标在字体上与否的状态是否改变
prev_on_labelL = False

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变
prev_on_objectL = False

label_info_save = []    #保存已经提交过的label信息,用于模块切换时的初始化
label_info_saveL = []


def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.3

def initialLabelTransparency():
    mat = newShader("LabelTransparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01


# 判断鼠标是否在物体上,字体
def is_mouse_on_label(context, event):
    name = bpy.context.scene.leftWindowObj
    plane_name = name + "PlaneForLabelActive"
    obj = bpy.data.objects.get(plane_name)
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


# 判断鼠标状态是否发生改变,字体
def is_changed_label(context, event):
    name = bpy.context.scene.leftWindowObj
    obj_name = name + "PlaneForLabelActive"
    obj = bpy.data.objects.get(obj_name)
    if(obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_label  # 之前鼠标是否在物体上
        global prev_on_labelL
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
            if (curr_on_object != prev_on_label):
                prev_on_label = curr_on_object
                return True
            else:
                return False
        elif name == '左耳':
            if (curr_on_object != prev_on_labelL):
                prev_on_labelL = curr_on_object
                return True
            else:
                return False
        # if (curr_on_object != prev_on_object):
        #     prev_on_object = curr_on_object
        #     return True
        # else:
        #     return False
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


def label_fit_rotate(normal,location):
    '''
    将字体移动到位置location并将连界面与向量normal对齐垂直
    '''
    #获取字体平面(字体的父物体)
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
    # 将字体摆正对齐
    if(plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z






'''
该模式下激活物体一直为text文本,因此切换到其他模式时,应该将当前激活物体设置为右耳
该模式下当前激活物体为Panel和Text,其它已经生成的物体则以LabelText开头
'''


def frontToLabel():
    '''
    根据当前激活物体复制出来一份若存在LabelReset,用于该模块的重置操作与模块切换
    '''
    # 若存在LabelReset,则先将其删除
    # 根据当前激活物体,复制一份生成LabelReset
    name = bpy.context.scene.leftWindowObj
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "LabelReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LabelReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    initial()  # 初始化


def frontFromLabel():
    # 根据LabelReset,复制出一份物体替代当前操作物体
    # 删除LabelReset与LabelLast

    #若模型上存在未提交的字体,则记录信息并提交该字体
    labelSubmit()

    #将用于铸造法的立方体删除
    name = bpy.context.scene.leftWindowObj
    label_for_casting_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")     #TODO 正则匹配
    if(label_for_casting_obj != None):
        bpy.data.objects.remove(label_for_casting_obj, do_unlink=True)

    #将右耳还原
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    resetname = name + "LabelReset"
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

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "LabelReset" or selected_obj.name == name + "LabelLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    global label_info_save
    global label_info_saveL
    if name == '右耳':
        for i in range(len(label_info_save)):
            label_info = label_info_save[i]
            print(label_info.text)
    elif name == '左耳':
        for i in range(len(label_info_saveL)):
            label_info = label_info_saveL[i]
            print(label_info.text)

    #调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def backToLabel():
    # 判断是否存在LabelReset
    # 若没有LabelReset,则说明跳过了Label模块,再直接由后面的模块返回该模块。   TODO  根据切割操作的最后状态复制出LabelReset和LabelLast
    # 若存在LabelReset,则直接将LabelReset复制一份用于替换当前操作物体

    # 若添加铸造法之后切换到支撑或者排气孔模块,再由支撑或排气孔模块跳过铸造法模块直接切换回前面的模块,则需要对物体进行特殊的处理
    name = bpy.context.scene.leftWindowObj
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

    #铸造法相关,删除用于铸造法的立方体
    # 将用于铸造法的立方体删除
    name = bpy.context.scene.leftWindowObj
    label_for_casting_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")  # TODO 正则匹配
    if (label_for_casting_obj != None):
        bpy.data.objects.remove(label_for_casting_obj, do_unlink=True)

    # 将后续模块中的reset和last都删除
    casting_reset = bpy.data.objects.get(name + "CastingReset")
    casting_last = bpy.data.objects.get(name + "CastingLast")
    support_reset = bpy.data.objects.get(name + "SupportReset")
    support_last = bpy.data.objects.get(name + "SupportLast")
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
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
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    if (sprue_compare_obj != None):
        bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)


    exist_LabelReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "LabelReset"):
            exist_LabelReset = True
    if (exist_LabelReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "LabelReset"
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
        initial()      #初始化

    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "HandleLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name+"VentCanalLast") != None):
            lastname = name+"VentCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name+"SoundCanalLast") != None):
            lastname = name+"SoundCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name+"MouldLast") != None):
            lastname = name+"MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name+"QieGeLast") != None):
            lastname = name+"QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name+"LocalThickLast") != None):
            lastname = name+"LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = name+"DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
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
        initial()      #初始化


def backFromLabel():
    # 将模型上未初始化的Label提交
    # 将提交之后的模型保存LabelLast,用于模块切换,若存在LabelLast,则先将其删除

    #将模型提交
    saveLabelPlaneForCasting()
    labelSubmit()

    name = bpy.context.scene.leftWindowObj
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "LabelLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LabelLast"
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

#在label提交前会保存label的相关信息
def saveInfo():
    global label_info_save
    global label_info_saveL

    name = bpy.context.scene.leftWindowObj
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    text = None
    depth = None
    size = None
    style = None
    if name == '右耳':
        text = bpy.context.scene.labelText
        depth = bpy.context.scene.deep
        size = bpy.context.scene.fontSize
        style = bpy.context.scene.styleEnum
    elif name == '左耳':
        text = bpy.context.scene.labelTextL
        depth = bpy.context.scene.deepL
        size = bpy.context.scene.fontSizeL
        style = bpy.context.scene.styleEnumL
    l_x = plane_obj.location[0]
    l_y = plane_obj.location[1]
    l_z = plane_obj.location[2]
    r_x = plane_obj.rotation_euler[0]
    r_y = plane_obj.rotation_euler[1]
    r_z = plane_obj.rotation_euler[2]

    label_info = LabelInfoSave(text,depth,size,style,l_x,l_y,l_z,r_x,r_y,r_z)
    if name == '右耳':
        label_info_save.append(label_info)
    elif name == '左耳':
        label_info_saveL.append(label_info)



def initial():
    global label_info_save
    global label_info_saveL
    name = bpy.context.scene.leftWindowObj
    #对于数组中保存的label信息,前n-1个先添加后提交,最后一个添加不提交
    if name == '右耳':
        if (len(label_info_save) > 0):
            for i in range(len(label_info_save) - 1):
                labelInfo = label_info_save[i]
                text = labelInfo.text
                depth = labelInfo.depth
                size = labelInfo.size
                style = labelInfo.style
                print(style)
                l_x = labelInfo.l_x
                l_y = labelInfo.l_y
                l_z = labelInfo.l_z
                r_x = labelInfo.r_x
                r_y = labelInfo.r_y
                r_z = labelInfo.r_z
                # 添加Label并提交
                labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z)
            labelInfo = label_info_save[len(label_info_save) - 1]
            text = labelInfo.text
            depth = labelInfo.depth
            size = labelInfo.size
            style = labelInfo.style
            l_x = labelInfo.l_x
            l_y = labelInfo.l_y
            l_z = labelInfo.l_z
            r_x = labelInfo.r_x
            r_y = labelInfo.r_y
            r_z = labelInfo.r_z
            # 先根据text信息添加一个label,激活鼠标行为
            bpy.ops.object.labeladd('INVOKE_DEFAULT')
            # 更新label的text时,会将之前物体删除并将信息保存到label_info_save中,多余的信息需要删除
            bpy.context.scene.labelText = text
            label_info_save.pop()
            # 获取添加后的label,并根据参数设置其形状大小
            name = bpy.context.scene.leftWindowObj
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.deep = depth
            bpy.context.scene.fontSize = size
            bpy.context.scene.styleEnum = style
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.label_add")
    elif name == '左耳':
        if (len(label_info_saveL) > 0):
            for i in range(len(label_info_saveL) - 1):
                labelInfo = label_info_saveL[i]
                text = labelInfo.text
                depth = labelInfo.depth
                size = labelInfo.size
                style = labelInfo.style
                print(style)
                l_x = labelInfo.l_x
                l_y = labelInfo.l_y
                l_z = labelInfo.l_z
                r_x = labelInfo.r_x
                r_y = labelInfo.r_y
                r_z = labelInfo.r_z
                # 添加Label并提交
                labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z)
            labelInfo = label_info_saveL[len(label_info_saveL) - 1]
            text = labelInfo.text
            depth = labelInfo.depth
            size = labelInfo.size
            style = labelInfo.style
            l_x = labelInfo.l_x
            l_y = labelInfo.l_y
            l_z = labelInfo.l_z
            r_x = labelInfo.r_x
            r_y = labelInfo.r_y
            r_z = labelInfo.r_z
            # 先根据text信息添加一个label,激活鼠标行为
            bpy.ops.object.labeladd('INVOKE_DEFAULT')
            # 更新label的text时,会将之前物体删除并将信息保存到label_info_saveL中,多余的信息需要删除
            bpy.context.scene.labelTextL = text
            label_info_saveL.pop()
            # 获取添加后的label,并根据参数设置其形状大小
            name = bpy.context.scene.leftWindowObj
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.deepL = depth
            bpy.context.scene.fontSizeL = size
            bpy.context.scene.styleEnumL = style
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.label_add")

    # 将旋转中心设置为左右耳模型
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



# 模块切换时,根据提交时保存的信息,添加label进行初始化,先根据信息添加label,之后再将label提交。与submit函数相比,提交时不必保存label信息。
def labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z):

    # 先根据text信息添加一个label
    addLabel(text)

    # 获取添加后的label,并根据参数设置其形状大小
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_for_active_name = name + "PlaneForLabelActive"
    plane_for_active_obj = bpy.data.objects.get(plane_for_active_name)
    if name == '右耳':
        bpy.context.scene.deep = depth
        bpy.context.scene.fontSize = size
        bpy.context.scene.styleEnum = style
    elif name == '左耳':
        bpy.context.scene.deepL = depth
        bpy.context.scene.fontSizeL = size
        bpy.context.scene.styleEnumL = style
    plane_obj.location[0] = l_x
    plane_obj.location[1] = l_y
    plane_obj.location[2] = l_z
    plane_obj.rotation_euler[0] = r_x
    plane_obj.rotation_euler[1] = r_y
    plane_obj.rotation_euler[2] = r_z

    # 应用Label的晶格形变修改器
    text_modifier_name = "Lattice"
    target_modifier = None
    for modifier in text_obj.modifiers:
        if modifier.name == text_modifier_name:
            target_modifier = modifier
    if (target_modifier != None):
        bpy.ops.object.modifier_apply(modifier="Lattice", single_user=True)
    # 应用Panel的缩裹修改器
    panel_modifier_name = "Shrinkwrap"
    target_modifier = None
    for modifier in plane_obj.modifiers:
        if modifier.name == panel_modifier_name:
            target_modifier = modifier
    if (target_modifier != None):
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap", single_user=True)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'

    # 将模型与Label根据style进行合并
    enum = None
    if name == '右耳':
        enum = bpy.types.Scene.styleEnum
    elif name == '左耳':
        enum = bpy.types.Scene.styleEnumL
    if enum == "OP1":
        bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    if enum == "OP2":
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].object = text_obj
    bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)
    bpy.context.object.data.use_auto_smooth = True

    # 删除平面和字体
    bpy.data.objects.remove(plane_obj, do_unlink=True)
    bpy.data.objects.remove(text_obj, do_unlink=True)
    bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)

    # 合并后Label会被去除材质,因此需要重置一下模型颜色为黄色
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
    bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    bpy.ops.paint.vertex_color_set()
    bpy.ops.object.mode_set(mode='OBJECT')




def addLabel(text):
    '''
    根据text生成一个新的Label标签,生成的Label名称默认为Text,平面名称默认为Plane。添加的表面形变修改器和缩裹修改器需要在提交的时候应用
    '''
    global default_plane_size_x
    global default_plane_size_y
    global default_plane_size_xL
    global default_plane_size_yL

    name = bpy.context.scene.leftWindowObj
    enum = None
    if name == '右耳':
        enum = bpy.context.scene.styleEnum
        bpy.context.scene.deep = 1
        bpy.context.scene.fontSize = 4
    elif name == '左耳':
        enum = bpy.context.scene.styleEnumL
        bpy.context.scene.deepL = 1
        bpy.context.scene.fontSizeL = 4
    # 添加字体,字体名称默认为Text
    bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(-16, 8, 4), scale=(1, 1, 1))
    bpy.context.object.data.align_x = 'CENTER'
    bpy.context.object.data.align_y = 'CENTER'
    # 加载中文字体,并将该字体应用到文本中
    bpy.ops.font.open(filepath="C:\\Windows\\Fonts\\Deng.ttf", relative_path=True)  # TODO    字体文件位置
    text_object = bpy.data.objects.get("Text")
    font_data = bpy.data.fonts.get("DengXian Regular")
    if text_object and text_object.type == 'FONT' and font_data is not None:
        text_object.data.font = font_data
    bpy.context.object.data.extrude = 0.4
    textname = "Text"
    text_obj = bpy.data.objects[textname]
    text_obj.name = name + "Text"
    if (name == "右耳"):
        moveToRight(text_obj)
    elif (name == "左耳"):
        moveToLeft(text_obj)
    bpy.context.view_layer.objects.active = text_obj
    # 将文本复制到剪贴板
    text_to_paste = text
    bpy.context.window_manager.clipboard = text_to_paste
    # 切换到编辑模式,选中现有内容并删除,再将文本内容替换为粘贴板中内容
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.font.select_all()
    bpy.ops.font.text_paste()
    # 切换到物体模式,将字体网格化
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.convert(target='MESH')

    # 添加晶格,晶格名称默认为Lattice        #TODO  后期更换字体吸附方案,将平面Plane更改为晶格Lattice,为方便更改,Label模块中的所又名为Plane的物体实际都为晶格Lattice
    bpy.ops.object.add(type='LATTICE', enter_editmode=False, align='WORLD', location=(-16, 8, 4), scale=(1, 0.4, 1))
    planename = "Lattice"
    plane_obj = bpy.data.objects[planename]
    plane_obj.name = name + "Plane"
    if (name == "右耳"):
        moveToRight(plane_obj)
    elif (name == "左耳"):
        moveToLeft(plane_obj)

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    textname = name + "Text"
    text_obj = bpy.data.objects[textname]
    planename = name + "Plane"
    plane_obj = bpy.data.objects[planename]

    # 将平面大小尺寸设置为文本的平面大小尺寸
    text_x = text_obj.dimensions.x
    text_y = text_obj.dimensions.y
    plane_x = plane_obj.dimensions.x
    plane_y = plane_obj.dimensions.y
    scale_x = text_x / plane_x
    scale_y = text_y / plane_y
    plane_obj.scale[0] = scale_x
    plane_obj.scale[1] = scale_y
    if name == '右耳':
        default_plane_size_x = scale_x
        default_plane_size_y = scale_y
    elif name == '左耳':
        default_plane_size_xL = scale_x
        default_plane_size_yL = scale_y

    if enum == "OP1":
        # 为字体添加红色材质
        bpy.context.view_layer.objects.active = text_obj
        red_material = bpy.data.materials.new(name="Red")
        red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
        text_obj.data.materials.clear()
        text_obj.data.materials.append(red_material)
    elif enum == "OP2":
        # 为字体添加青色材质
        bpy.context.view_layer.objects.active = text_obj
        red_material = bpy.data.materials.new(name="Red")
        red_material.diffuse_color = (0, 0.4, 1.0, 1.0)
        text_obj.data.materials.clear()
        text_obj.data.materials.append(red_material)
    # 为字体添加细分修改器并应用。对字体添加表面形变修改器，将目标绑定为平面
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'
    bpy.context.object.modifiers["Subdivision"].levels = 1
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    #对字体添加晶格修改器，将目标绑定为晶格
    bpy.ops.object.modifier_add(type='LATTICE')
    bpy.context.object.modifiers["Lattice"].object = plane_obj
    bpy.context.object.modifiers["Lattice"].strength = 1
    # 将晶格修改器的强度设置为1之后字体的y轴会被拉伸,因此也需要将x轴伸缩扩大使字体整体比例更加协调
    text_obj.scale[1] = 1.5
    # 为晶格添加缩裹修改器,将目标绑定为右耳
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
    bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ON_SURFACE'
    bpy.context.object.modifiers["Shrinkwrap"].target = obj



    #添加一个平面将其设置为透明,主要用于判断鼠标是否位于字体上并将字体激活(晶格平面比较难以)
    plane_for_active_name = name + "PlaneForLabelActive"
    plane_for_active_obj = bpy.data.objects.get(plane_for_active_name)
    if (plane_for_active_obj != None):
        bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(-16, 8, 4), scale=(1, 0.4, 1))
    plane_for_label_active_obj = bpy.context.active_object
    plane_for_label_active_obj.name = name + "PlaneForLabelActive"
    if (name == "右耳"):
        moveToRight(plane_for_label_active_obj)
    elif (name == "左耳"):
        moveToLeft(plane_for_label_active_obj)
    #为平面添加缩裹修改器
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
    bpy.context.object.modifiers["Shrinkwrap"].use_positive_direction = False
    bpy.context.object.modifiers["Shrinkwrap"].cull_face = 'BACK'
    bpy.context.object.modifiers["Shrinkwrap"].target = obj
    #将铸造法平面大小设置为字体大小
    text_x = plane_obj.dimensions.x
    text_y = plane_obj.dimensions.y
    plane_x = plane_for_label_active_obj.dimensions.x
    plane_y = plane_for_label_active_obj.dimensions.y
    scale_x = text_x / plane_x
    scale_y = text_y / plane_y
    plane_for_label_active_obj.scale[0] = scale_x
    plane_for_label_active_obj.scale[1] = scale_y
    #为该平面添加透明材质
    initialLabelTransparency()
    plane_for_label_active_obj.data.materials.clear()
    plane_for_label_active_obj.data.materials.append(bpy.data.materials['LabelTransparency'])


    # 将平面设置为字体的父物体。对父物体平面进行位移和大小缩放操作时，子物体字体会其改变
    bpy.context.view_layer.objects.active = plane_obj
    text_obj.select_set(True)
    plane_for_label_active_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    text_obj.select_set(False)
    plane_for_label_active_obj.select_set(False)

    # 设置字体初始位置
    plane_obj.location[0] = -9.7
    plane_obj.location[1] = -6.0
    plane_obj.location[2] = 3.2



def labelDepthUpdate(depth):
    '''
    根据面板深度参数设置字体高度
    '''
    name = bpy.context.scene.leftWindowObj
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 先将平面和字体移到模型之外,在调整字体高度,避免字体变形
    if (plane_obj != None):
        plane_obj_location_x = plane_obj.location[0]
        plane_obj_location_y = plane_obj.location[1]
        plane_obj_location_z = plane_obj.location[2]
        plane_obj.location[0] = -100000
        plane_obj.location[1] = -100000
        plane_obj.location[2] = -100000
        # 设置字体厚度
        if (text_obj != None):
            text_obj.scale[2] = depth
        plane_obj.location[0] = plane_obj_location_x
        plane_obj.location[1] = plane_obj_location_y
        plane_obj.location[2] = plane_obj_location_z


def labelSizeUpdate(size):
    '''
    根据面板字体尺寸参数设置字体大小
    '''
    # 字体大小以4为基准,大一号字体,扩大1.25倍,小一号字体,缩小0.8倍
    global default_plane_size_x
    global default_plane_size_y
    global default_plane_size_xL
    global default_plane_size_yL
    scale_x = None
    scale_y = None
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        scale_x = default_plane_size_x
        scale_y = default_plane_size_y
    elif name == '左耳':
        scale_x = default_plane_size_xL
        scale_y = default_plane_size_yL
    if (size >= 4):
        scale_x = scale_x * (1.25 ** (size - 4))
        scale_y = scale_y * (1.25 ** (size - 4))
    else:
        scale_x = scale_x * (0.8 ** (4 - size))
        scale_y = scale_y * (0.8 ** (4 - size))
    # 更改plane的尺寸,作为其子物体的text也会随之改变
    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (plane_obj != None):
        plane_obj.scale[0] = scale_x
        plane_obj.scale[1] = scale_y


def labelTextUpdate(text):
    '''
    根据面板标签名称参数设置字体内容
    '''
    # 先删除当前的label,并记录当前Label的位置
    name = bpy.context.scene.leftWindowObj
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_for_active_name = name + "PlaneForLabelActive"
    plane_for_active_obj = bpy.data.objects.get(plane_for_active_name)
    plane_obj_location_x = 0
    plane_obj_location_y = 0
    plane_obj_location_z = 0
    if (plane_for_active_obj != None):
        bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
    if (text_obj != None):
        bpy.data.objects.remove(text_obj, do_unlink=True)
    if (plane_obj != None):
        plane_obj_location_x = plane_obj.location[0]
        plane_obj_location_y = plane_obj.location[1]
        plane_obj_location_z = plane_obj.location[2]
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        # 将属性面板中的text属性值读取到剪切板中生成新的label
    addLabel(text)
    # 将Plane激活并选中,将其位置设置为名称更改前的上一个Label的位置
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (plane_obj_location_x != 0 and plane_obj_location_y != 0 and plane_obj_location_z != 0):
        plane_obj.location[0] = plane_obj_location_x
        plane_obj.location[1] = plane_obj_location_y
        plane_obj.location[2] = plane_obj_location_z
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj


def labelSubmit():
    '''
    提交操作,保存信息,应用修改器,将Plane删除并将Text实体化
    '''
    enum = None
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        enum = bpy.context.scene.styleEnum
    elif name == '左耳':
        enum = bpy.context.scene.styleEnumL
    obj = bpy.data.objects.get(name)
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_for_active_name = name + "PlaneForLabelActive"
    plane_for_active_obj = bpy.data.objects.get(plane_for_active_name)
    label_for_casting_name = name + "LabelPlaneForCasting"
    label_for_casting_obj = bpy.data.objects.get(label_for_casting_name)
    if(plane_for_active_obj != None):
        bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
    # 存在未提交的Label和Plane时
    if (text_obj != None and plane_obj != None):
        #先将该Label的相关信息保存下来,用于模块切换时的初始化。
        saveInfo()

        # 应用Label的表面形变修改器
        text_modifier_name = "Lattice"
        target_modifier = None
        for modifier in text_obj.modifiers:
            if modifier.name == text_modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="Lattice",single_user=True)
        # 应用Panel的缩裹修改器
        panel_modifier_name = "Shrinkwrap"
        target_modifier = None
        for modifier in plane_obj.modifiers:
            if modifier.name == panel_modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="Shrinkwrap",single_user=True)

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        #将模型与Label根据style进行合并
        if enum == "OP1":
            bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
        if enum == "OP2":
            bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = text_obj
        bpy.ops.object.modifier_apply(modifier="Boolean",single_user=True)
        #开启自动平滑功能
        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.data.auto_smooth_angle = 0.9

        #记录平面位置,将用于铸造法的平面位置设置为其位置
        location_x = plane_obj.location[0]
        location_y = plane_obj.location[1]
        location_z = plane_obj.location[2]
        rotate_x = plane_obj.rotation_euler[0]
        rotate_y = plane_obj.rotation_euler[1]
        rotate_z = plane_obj.rotation_euler[2]
        text_x = text_obj.dimensions.x
        text_y = text_obj.dimensions.y

        #删除平面和字体
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(text_obj, do_unlink=True)

        # 设置用于铸造法的平面的位置,角度,大小
        if (label_for_casting_obj != None):
            label_for_casting_obj.location[0] = location_x
            label_for_casting_obj.location[1] = location_y
            label_for_casting_obj.location[2] = location_z
            label_for_casting_obj.rotation_euler[0] = rotate_x
            label_for_casting_obj.rotation_euler[1] = rotate_y
            label_for_casting_obj.rotation_euler[2] = rotate_z
            label_for_casting_obj.dimensions.x = text_x * 1.2
            label_for_casting_obj.dimensions.y = text_y * 1.2


        #合并后Label会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')


def saveLabelPlaneForCasting():
    '''
        若添加了外凸字体,在提交时则需要保存平面信息,在铸造法模块将该区域鼓起
    '''

    all_objects = bpy.data.objects
    for obj in bpy.data.objects:
        obj.select_set(False)

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    plane_obj = bpy.data.objects.get(name + "Plane")
    plane_for_active_obj = bpy.data.objects.get(name + "PlaneForLabelActive")
    label_enum = None
    depth = None
    if name == '右耳':
        label_enum = bpy.context.scene.styleEnum
        depth = bpy.context.scene.deep
    elif name == '左耳':
        label_enum = bpy.context.scene.styleEnumL
        depth = bpy.context.scene.deepL
    if(obj != None and plane_for_active_obj != None):
        if(label_enum == "OP2"):
            label_plane_for_casting_obj = plane_for_active_obj.copy()
            label_plane_for_casting_obj.data = plane_for_active_obj.data.copy()
            label_plane_for_casting_obj.animation_data_clear()
            label_plane_for_casting_obj.name = name + "LabelPlaneForCasting"
            bpy.context.collection.objects.link(label_plane_for_casting_obj)
            if (name == "右耳"):
                moveToRight(label_plane_for_casting_obj)
            elif (name == "左耳"):
                moveToLeft(label_plane_for_casting_obj)

            #扩大平面
            prev_scale0 = label_plane_for_casting_obj.scale[0]
            prev_scale1 = label_plane_for_casting_obj.scale[1]
            label_plane_for_casting_obj.scale[0] = prev_scale0 * 1.2
            label_plane_for_casting_obj.scale[1] = prev_scale1 * 1.2

            # 将平面设置为激活物体
            label_plane_for_casting_obj.select_set(True)
            bpy.context.view_layer.objects.active = label_plane_for_casting_obj

            panel_modifier_name = "Shrinkwrap"
            target_modifier = None
            for modifier in label_plane_for_casting_obj.modifiers:
                if modifier.name == panel_modifier_name:
                    target_modifier = modifier
            if (target_modifier != None):
                bpy.ops.object.modifier_apply(modifier="Shrinkwrap", single_user=True)

            #为用于铸造法的物体添加材质
            yellow_material = bpy.data.materials.new(name="Yellow")
            yellow_material.diffuse_color = (1.0, 0.319, 0.133, 1.0)
            label_plane_for_casting_obj.data.materials.clear()
            label_plane_for_casting_obj.data.materials.append(yellow_material)

            #将平面细分并沿法线挤出形成凸起
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            # bpy.ops.mesh.subdivide(number_cuts=10)
            bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":depth/2, "use_even_offset":False, "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.object.mode_set(mode='OBJECT')


            #为平面凸起形成的立方体添加倒角修改器,平滑其边缘
            modifierLabelPlaneBevelForCasting = label_plane_for_casting_obj.modifiers.new(name="LabelPlaneBevelForCasting", type='BEVEL')
            modifierLabelPlaneBevelForCasting.width = 0.32
            modifierLabelPlaneBevelForCasting.segments = 21
            bpy.ops.object.modifier_apply(modifier="LabelPlaneBevelForCasting", single_user=True)


            #为立方体添加黄色透明材质
            initialTransparency()
            label_plane_for_casting_obj.data.materials.clear()
            bpy.ops.geometry.color_attribute_add(name="Color", color=(1, 0.319, 0.133, 1))
            label_plane_for_casting_obj.data.materials.append(bpy.data.materials['Transparency'])

            #将该物体隐藏并将平面设置为当前激活物体
            label_plane_for_casting_obj.select_set(False)
            label_plane_for_casting_obj.hide_set(True)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj




class LabelTest(bpy.types.Operator):
    bl_idname = "object.labeltestfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):
        addLabel("HDU")


        return {'FINISHED'}



#保存提交前的每个Label信息
class LabelInfoSave(object):
    def __init__(self,text,depth,size,style,l_x,l_y,l_z,r_x,r_y,r_z):
        self.text = text
        self.depth = depth
        self.size = size
        self.style = style
        self.l_x = l_x
        self.l_y = l_y
        self.l_z = l_z
        self.r_x = r_x
        self.r_y = r_y
        self.r_z = r_z





class LabelReset(bpy.types.Operator):
    bl_idname = "object.labelreset"
    bl_label = "标签重置"

    def invoke(self, context, event):

        bpy.context.scene.var = 10
        name = bpy.context.scene.leftWindowObj
        global label_info_save
        global label_info_saveL
        if name == '右耳':
            label_info_save = []
        elif name == '左耳':
            label_info_saveL = []

        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):

        # 存在未提交Label时,删除Text和Plane
        name = bpy.context.scene.leftWindowObj
        textname = name + "Text"
        text_obj = bpy.data.objects.get(textname)
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_for_active_name = name + "PlaneForLabelActive"
        plane_for_active_obj = bpy.data.objects.get(plane_for_active_name)
        # 存在未提交的Label和Plane时
        if (text_obj != None):
            bpy.data.objects.remove(text_obj, do_unlink=True)
        if (plane_obj != None):
            bpy.data.objects.remove(plane_obj, do_unlink=True)
        #将用于激活字体的平面删除
        if (plane_for_active_obj != None):
            bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
        # 将用于铸造法的立方体删除
        label_for_casting_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")  # TODO 正则匹配
        if (label_for_casting_obj != None):
            bpy.data.objects.remove(label_for_casting_obj, do_unlink=True)
        # 将LabelReset复制并替代当前操作模型
        oriname = bpy.context.scene.leftWindowObj
        ori_obj = bpy.data.objects.get(oriname)
        copyname = oriname + "LabelReset"
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
        bpy.ops.wm.tool_set_by_id(name="my_tool.label_add")
        return {'FINISHED'}


class LabelAdd(bpy.types.Operator):
    bl_idname = "object.labeladd"
    bl_label = "添加标签"

    def invoke(self, context, event):

        bpy.context.scene.var = 11
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        name = bpy.context.scene.leftWindowObj
        # 若模型上存在未提交的Label,则先将其提交
        labelSubmit()
        # 创建新的Label
        labelText = None
        if name == '右耳':
            labelText = bpy.context.scene.labelText
        elif name == '左耳':
            labelText = bpy.context.scene.labelTextL
        addLabel(labelText)
        # 将Plane激活并选中
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context,event)
        if(co != -1):
            # plane_obj.location = co
            label_fit_rotate(normal,co)


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        name = bpy.context.scene.leftWindowObj
        cubename = name + "Text"
        label_obj = bpy.data.objects.get(cubename)
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = bpy.context.scene.leftWindowObj
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 11):
            if (is_mouse_on_object(context, event) and not is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
                # 公共鼠标行为加双击移动附件位置
                bpy.ops.wm.tool_set_by_id(name="my_tool.label_mouse")
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                plane_obj.select_set(False)
            elif (is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
                bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                cur_obj.select_set(False)
            elif ((not is_mouse_on_object(context, event)) and (is_changed_label(context, event) or is_changed(context, event))):
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                plane_obj.select_set(False)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class LabelSubmit(bpy.types.Operator):
    bl_idname = "object.labelsubmit"
    bl_label = "标签提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 12
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        saveLabelPlaneForCasting()
        labelSubmit()
        return {'FINISHED'}

class LabelDoubleClick(bpy.types.Operator):
    bl_idname = "object.labeldoubleclick"
    bl_label = "双击改变字体位置"

    def invoke(self, context, event):
        # 将Plane激活并选中,位置设置为双击的位置
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context, event)
        if (co != -1):
            label_fit_rotate(normal,co)
            # plane_obj.location = co
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}


class MyTool_Label1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_reset"
    bl_label = "标签重置"
    bl_description = (
        "重置模型,清除模型上的所有标签"
    )
    bl_icon = "ops.mesh.polybuild_hover"
    bl_widget = None
    bl_keymap = (
        ("object.labelreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Label2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_add"
    bl_label = "标签添加"
    bl_description = (
        "在模型上添加一个标签"
    )
    bl_icon = "ops.mesh.primitive_torus_add_gizmo"
    bl_widget = None
    bl_keymap = (
        ("object.labeladd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Label3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_submit"
    bl_label = "标签提交"
    bl_description = (
        "对于模型上所有标签提交实体化"
    )
    bl_icon = "ops.mesh.primitive_cone_add_gizmo"
    bl_widget = None
    bl_keymap = (
        ("object.labelsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Label_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_mirror"
    bl_label = "字体镜像"
    bl_description = (
        "点击镜像字体"
    )
    bl_icon = "brush.gpencil_draw.fill"
    bl_widget = None
    bl_keymap = (
        ("object.labelmirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Label_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_mouse"
    bl_label = "双击改变字体位置"
    bl_description = (
        "添加字体后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.uv_sculpt.pinch"
    bl_widget = None
    bl_keymap = (
        ("object.labeldoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass

# 注册类
_classes = [
    LabelReset,
    LabelAdd,
    LabelSubmit,
    LabelDoubleClick,
    LabelTest,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Label1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Label2, separator=True, group=False, after={MyTool_Label1.bl_idname})
    bpy.utils.register_tool(MyTool_Label3, separator=True, group=False, after={MyTool_Label2.bl_idname})
    bpy.utils.register_tool(MyTool_Label_Mirror, separator=True, group=False, after={MyTool_Label3.bl_idname})
    bpy.utils.register_tool(MyTool_Label_Mouse, separator=True, group=False, after={MyTool_Label_Mirror.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Label1)
    bpy.utils.unregister_tool(MyTool_Label2)
    bpy.utils.unregister_tool(MyTool_Label3)
    bpy.utils.unregister_tool(MyTool_Label_Mirror)
    bpy.utils.unregister_tool(MyTool_Label_Mouse)
