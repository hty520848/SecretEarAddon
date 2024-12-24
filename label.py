from os import dup
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re
import time
from .tool import *
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running,\
    get_mirror_context, set_mirror_context, get_process_var_list

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
label_index = -1 # 数组指针，指向字体状态数组中当前访问状态的附件，用于单步撤回操作
label_indexL = -1

is_labelAdd_modal_start = False         #在启动下一个modal前必须将上一个modal关闭,防止modal开启过多过于卡顿
is_labelAdd_modal_startL = False


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


def initialTransparency():
    newColor("Transparency", 1, 0.319, 0.133, 1, 0.3)  # 创建材质
    # mat = newShader("Transparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.3

def initialLabelTransparency():
    newColor("LabelTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质
    # mat = newShader("LabelTransparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01


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



def label_forward():
    '''
    添加多个字体的时候,向后切换的字体状态
    '''
    global label_index
    global label_indexL
    global label_info_save
    global label_info_saveL
    # bpy.context.scene.var = 0
    name = bpy.context.scene.leftWindowObj
    label_index_cur = None
    label_info_save_cur = None
    size = None
    print("进入label_forward")
    if (name == "右耳"):
        label_index_cur = label_index
        label_info_save_cur = label_info_save
        size = len(label_info_save)
    elif (name == "左耳"):
        label_index_cur = label_indexL
        label_info_save_cur = label_info_saveL
        size = len(label_info_saveL)
    print("当前指针:", label_index_cur)
    print("数组大小:",size)
    if (label_index_cur + 1 < size):
        label_index_cur = label_index_cur +1
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            label_index = label_index + 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            label_indexL = label_indexL + 1
        #将当前激活的左右耳模型使用reset还原
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
        # 存在未提交Label时,删除Text和Plane
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
        # 将用于激活字体的平面删除
        if (plane_for_active_obj != None):
            bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
        # 将用于铸造法的立方体删除
        for obj in bpy.data.objects:
            patternR = r'右耳LabelPlaneForCasting'
            patternL = r'左耳LabelPlaneForCasting'
            if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                label_obj = obj
                bpy.data.objects.remove(label_obj, do_unlink=True)
        #根据label_index_cur重新添加label
        for i in range(label_index_cur):
            labelInfo = label_info_save_cur[i]
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
            # 添加Label并提交
            labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z)
        labelInfo = label_info_save_cur[label_index_cur]
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
        bpy.ops.object.labelbackforwardadd('INVOKE_DEFAULT')
        # 设计问题,点击加号调用bpy.ops.object.labeladd('INVOKE_DEFAULT')添加字体的时候,label_index也会自增加一,但此处调用不需要自增,因此再减一
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            label_index = label_index - 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            label_indexL = label_indexL - 1
        # 更新label的text
        bpy.context.scene.labelText = text
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

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def label_backup():
    '''
    添加多个字体的时候,回退切换字体状态
    '''
    global label_index
    global label_indexL
    global label_info_save
    global label_info_saveL
    # bpy.context.scene.var = 0
    name = bpy.context.scene.leftWindowObj
    label_index_cur = None
    label_info_save_cur = None
    size = None
    print("进入label_backup")
    if (name == "右耳"):
        label_index_cur = label_index
        label_info_save_cur = label_info_save
        size = len(label_info_save)
    elif (name == "左耳"):
        label_index_cur = label_indexL
        label_info_save_cur = label_info_saveL
        size = len(label_info_saveL)
    print("当前指针:", label_index_cur)
    print("数组大小:", size)
    if (label_index_cur > 0):
        label_index_cur = label_index_cur -1
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            label_index = label_index - 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            label_indexL = label_indexL - 1
        # 将当前激活的左右耳模型使用reset还原
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
        # 存在未提交Label时,删除Text和Plane
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
        # 将用于激活字体的平面删除
        if (plane_for_active_obj != None):
            bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
        # 将用于铸造法的立方体删除
        for obj in bpy.data.objects:
            patternR = r'右耳LabelPlaneForCasting'
            patternL = r'左耳LabelPlaneForCasting'
            if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                label_obj = obj
                bpy.data.objects.remove(label_obj, do_unlink=True)
        # 根据label_index_cur重新添加label
        for i in range(label_index_cur):
            labelInfo = label_info_save_cur[i]
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
            # 添加Label并提交
            labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z)
        labelInfo = label_info_save_cur[label_index_cur]
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
        bpy.ops.object.labelbackforwardadd('INVOKE_DEFAULT')
        # 设计问题,点击加号调用bpy.ops.object.labeladd('INVOKE_DEFAULT')添加字体的时候,label_index也会自增加一,但此处调用不需要自增,因此再减一
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            label_index = label_index - 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            label_indexL = label_indexL - 1
        # 更新label的text
        bpy.context.scene.labelText = text
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

        # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

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
    for obj in bpy.data.objects:
        patternR = r'右耳LabelPlaneForCasting'
        patternL = r'左耳LabelPlaneForCasting'
        if re.match(patternR, obj.name) or re.match(patternL, obj.name):
            label_obj = obj
            bpy.data.objects.remove(label_obj, do_unlink=True)

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
    # 若没有LabelReset,则说明跳过了Label模块,再直接由后面的模块返回该模块。
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

    # 将用于铸造法的立方体删除
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

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

# def saveInfo():
#     '''
#     #在label提交前会保存label的相关信息
#     '''
#     global label_info_save
#     global label_info_saveL
#
#     name = bpy.context.scene.leftWindowObj
#     textname = name + "Text"
#     text_obj = bpy.data.objects.get(textname)
#     planename = name + "Plane"
#     plane_obj = bpy.data.objects.get(planename)
#     text = None
#     depth = None
#     size = None
#     style = None
#     if name == '右耳':
#         text = bpy.context.scene.labelText
#         depth = bpy.context.scene.deep
#         size = bpy.context.scene.fontSize
#         style = bpy.context.scene.styleEnum
#     elif name == '左耳':
#         text = bpy.context.scene.labelTextL
#         depth = bpy.context.scene.deepL
#         size = bpy.context.scene.fontSizeL
#         style = bpy.context.scene.styleEnumL
#     l_x = plane_obj.location[0]
#     l_y = plane_obj.location[1]
#     l_z = plane_obj.location[2]
#     r_x = plane_obj.rotation_euler[0]
#     r_y = plane_obj.rotation_euler[1]
#     r_z = plane_obj.rotation_euler[2]
#
#     label_info = LabelInfoSave(text,depth,size,style,l_x,l_y,l_z,r_x,r_y,r_z)
#     if name == '右耳':
#         label_info_save.append(label_info)
#     elif name == '左耳':
#         label_info_saveL.append(label_info)

def updateInfo():
    '''
     #单步撤回过程中若更改过字体位置信息,则在数组中更新该信息,若未添加过该字体信息,则将该字体信息保存
    '''
    global label_index
    global label_indexL
    global label_info_save
    global label_info_saveL

    name = bpy.context.scene.leftWindowObj
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if(plane_obj != None):
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
            if (label_index < len(label_info_save)):
                label_info_save[label_index] = label_info
            elif (label_index == len(label_info_save)):
                label_info_save.append(label_info)
        elif name == '左耳':
            if (label_indexL < len(label_info_saveL)):
                label_info_saveL[label_indexL] = label_info
            elif (label_indexL == len(label_info_saveL)):
                label_info_saveL.append(label_info)


def initial():
    ''''
    切换到字体模块的时候,根据之前保存的字体信息进行初始化,恢复之前添加的字体状态
    '''
    global label_index
    global label_indexL
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
            bpy.ops.object.labelswitch('INVOKE_DEFAULT')
            bpy.ops.object.labelbackforwardadd('INVOKE_DEFAULT')
            # 更新label的text
            bpy.context.scene.labelText = text
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
            # 将字体数组指针置为末尾
            label_index = len(label_info_save) - 1
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
    elif name == '左耳':
        if (len(label_info_saveL) > 0):
            for i in range(len(label_info_saveL) - 1):
                labelInfo = label_info_saveL[i]
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
            bpy.ops.object.labelswitch('INVOKE_DEFAULT')
            bpy.ops.object.labelbackforwardadd('INVOKE_DEFAULT')
            # 更新label的text
            bpy.context.scene.labelTextL = text
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
            # 将字体数组指针置为末尾
            label_indexL = len(label_info_saveL) - 1
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")

    # 将旋转中心设置为左右耳模型
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



def labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z):
    '''
    根据状态数组中保存的信息,生成一个字体
    模块切换时,根据提交时保存的信息,添加label进行初始化,先根据信息添加label,之后再将label提交。与submit函数相比,提交时不必保存label信息。
    '''

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

    #为外凸字体创建用于实体化的外壳
    saveLabelPlaneForCasting()

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

    #将字体与模型合并
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # bpy.ops.object.modifier_add(type='BOOLEAN')
    # bpy.context.object.modifiers["Boolean"].solver = 'FAST'

    # 将模型与Label根据style进行合并
    enum = None
    if name == '右耳':
        enum = bpy.context.scene.styleEnum
    elif name == '左耳':
        enum = bpy.context.scene.styleEnumL
    if enum == "OP1":
        # bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
        bpy.ops.object.booltool_auto_difference()
    if enum == "OP2":
        # bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.ops.object.booltool_auto_union()
    # bpy.context.object.modifiers["Boolean"].object = text_obj
    # bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

    bpy.context.object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = 3.14159

    # 删除平面和字体
    bpy.data.objects.remove(plane_obj, do_unlink=True)
    # bpy.data.objects.remove(text_obj, do_unlink=True)
    bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)

    # 合并后Label会被去除材质,因此需要重置一下模型颜色为黄色
    utils_re_color(name, (1, 0.319, 0.133))
    # bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    # bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
    # bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    # bpy.ops.paint.vertex_color_set()
    # bpy.ops.object.mode_set(mode='OBJECT')




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
    bpy.ops.font.open(filepath="C:\\Windows\\Fonts\\Deng.ttf", relative_path=True)
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
    plane_obj.data.points_u = 4
    plane_obj.data.points_v = 4
    plane_obj.data.points_w = 1
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
        red_material = newColor("LabelRed", 1, 0, 0, 0, 1)
        text_obj.data.materials.clear()
        text_obj.data.materials.append(red_material)
    elif enum == "OP2":
        # 为字体添加青色材质
        bpy.context.view_layer.objects.active = text_obj
        green_material = newColor("LabelBlue", 0, 0.4, 1, 0, 1)
        text_obj.data.materials.clear()
        text_obj.data.materials.append(green_material)
    #减小字体表面的顶点数
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    #对字体添加晶格修改器，将目标绑定为晶格
    bpy.ops.object.modifier_add(type='LATTICE')
    bpy.context.object.modifiers["Lattice"].object = plane_obj
    bpy.context.object.modifiers["Lattice"].strength = 1
    # 将晶格修改器的强度设置为1之后字体的y轴会被拉伸,因此也需要将x轴伸缩扩大使字体整体比例更加协调
    text_obj.scale[1] = 1.5
    # 为晶格添加缩裹修改器,将目标绑定为右耳
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
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
    #记录字体删除之前的尺寸大小
    name = bpy.context.scene.leftWindowObj
    size = None
    deep = None
    if name == '右耳':
        size = bpy.context.scene.fontSize
        depth = bpy.context.scene.deep
    elif name == '左耳':
        size = bpy.context.scene.fontSizeL
        depth = bpy.context.scene.deepL
    # 先删除当前的label,并记录当前Label的位置
    textname = name + "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_for_active_name = name + "PlaneForLabelActive"
    plane_for_active_obj = bpy.data.objects.get(plane_for_active_name)
    plane_obj_location_x = 0
    plane_obj_location_y = 0
    plane_obj_location_z = 0
    plane_obj_rotation_x = 0
    plane_obj_rotation_y = 0
    plane_obj_rotation_z = 0
    if (plane_for_active_obj != None):
        bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)
    if (text_obj != None):
        bpy.data.objects.remove(text_obj, do_unlink=True)
    if (plane_obj != None):
        plane_obj_location_x = plane_obj.location[0]
        plane_obj_location_y = plane_obj.location[1]
        plane_obj_location_z = plane_obj.location[2]
        plane_obj_rotation_x = plane_obj.rotation_euler[0]
        plane_obj_rotation_y = plane_obj.rotation_euler[1]
        plane_obj_rotation_z = plane_obj.rotation_euler[2]
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        # 将属性面板中的text属性值读取到剪切板中生成新的label
    addLabel(text)
    # 将Plane激活并选中,将其位置,大小,深度设置为名称更改前的上一个Label的位置,大小,深度
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (plane_obj_location_x != 0 and plane_obj_location_y != 0 and plane_obj_location_z != 0):
        plane_obj.location[0] = plane_obj_location_x
        plane_obj.location[1] = plane_obj_location_y
        plane_obj.location[2] = plane_obj_location_z
        plane_obj.rotation_euler[0] = plane_obj_rotation_x
        plane_obj.rotation_euler[1] = plane_obj_rotation_y
        plane_obj.rotation_euler[2] = plane_obj_rotation_z
        if name == '右耳':
            bpy.context.scene.fontSize = size
            bpy.context.scene.deep = depth
        elif name == '左耳':
            bpy.context.scene.fontSizeL = size
            bpy.context.scene.deepL = depth
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
    # 存在未提交的Label和Plane时
    if (text_obj != None and plane_obj != None and plane_for_active_obj != None):
        #先将该Label的相关信息保存下来,用于模块切换时的初始化。
        # saveInfo()

        #将字体合并之前的物体复制一份用于合并之后的光滑处理
        name = bpy.context.scene.leftWindowObj
        before_submit_obj_name = name + "LabelBeforeSubmit"
        before_submit_obj = bpy.data.objects.get(before_submit_obj_name)
        if (before_submit_obj != None):
            bpy.data.objects.remove(before_submit_obj, do_unlink=True)
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.name = obj.name + "LabelBeforeSubmit"
        duplicate_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if bpy.context.scene.leftWindowObj == '右耳':
            moveToRight(duplicate_obj)
        else:
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(True)

        #为外凸字体创建用于实体化的外壳
        saveLabelPlaneForCasting()

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

        #将字体与模型合并
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        text_obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # bpy.ops.object.modifier_add(type='BOOLEAN')
        # bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        #将模型与Label根据style进行合并
        if enum == "OP1":
            bpy.ops.object.booltool_auto_difference()
            # bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
        if enum == "OP2":
            bpy.ops.object.booltool_auto_union()
            # bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        # bpy.context.object.modifiers["Boolean"].object = text_obj
        # bpy.ops.object.modifier_apply(modifier="Boolean",single_user=True)

        #开启自动平滑功能
        # bpy.context.object.data.use_auto_smooth = True
        # bpy.context.object.data.auto_smooth_angle = 3.14159
        #对合并完成后的字体边缘进行平滑
        labelEdgeSmooth()

        #删除平面和字体
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        # bpy.data.objects.remove(text_obj, do_unlink=True)
        bpy.data.objects.remove(plane_for_active_obj, do_unlink=True)


        #合并后Label会被去除材质,因此需要重置一下模型颜色为黄色
        utils_re_color(name, (1, 0.319, 0.133))
        # bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        # bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        # bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        # bpy.ops.paint.vertex_color_set()
        # bpy.ops.object.mode_set(mode='OBJECT')

def labelEdgeSmooth():
    '''
    对字体边缘进行平滑
    '''
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    before_submit_obj_name = name + "LabelBeforeSubmit"
    before_submit_obj = bpy.data.objects.get(before_submit_obj_name)
    if (before_submit_obj != None):
        #布尔后产生的新的字体顶点组
        label_vertex = obj.vertex_groups.get('LabelVertex')
        if (label_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='LabelVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        label_vertex = obj.vertex_groups.new(name='LabelVertex')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_set_active(group='LabelVertex')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        #字体顶点附近用于平滑的顶点组
        smooth_vertex = obj.vertex_groups.get('SmoothVertex')
        if (smooth_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SmoothVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        smooth_vertex = obj.vertex_groups.new(name='SmoothVertex')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()
        bpy.ops.object.vertex_group_set_active(group='LabelVertex')
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.vertex_group_set_active(group='SmoothVertex')
        bpy.ops.object.vertex_group_assign()

        bm = bmesh.from_edit_mesh(obj.data)
        transform_index = [v.index for v in bm.verts if v.select]
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        transform_obj_name = before_submit_obj_name
        transform_normal(transform_obj_name, transform_index)

        bpy.ops.object.mode_set(mode='OBJECT')
        return

        #添加数据传递修改器,只调整字体附近的法线,对附近作光滑
        modifier_name = "LabelSmoothDataTransfer"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_remove(modifier="LabelSmoothDataTransfer")
        labelSmoothDataTransfer = obj.modifiers.new(name="LabelSmoothDataTransfer", type='DATA_TRANSFER')
        labelSmoothDataTransfer.object = before_submit_obj
        labelSmoothDataTransfer.vertex_group = "SmoothVertex"
        labelSmoothDataTransfer.use_loop_data = True
        labelSmoothDataTransfer.data_types_loops = {'CUSTOM_NORMAL'}
        labelSmoothDataTransfer.loop_mapping = 'POLYINTERP_NEAREST'
        bpy.ops.object.modifier_apply(modifier="LabelSmoothDataTransfer")

        #将模型上的顶点取消选中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        #删除用于传递数据的字体提交之前的物体
        bpy.data.objects.remove(before_submit_obj, do_unlink=True)

def saveLabelPlaneForCasting():
    '''
        若添加了外凸字体,在提交时则需要保存平面信息,在铸造法模块将该区域鼓起
    '''

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    text_obj = bpy.data.objects.get(name + "Text")
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
    if(obj != None and text_obj != None and plane_obj != None and plane_for_active_obj != None):
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
            bpy.ops.object.select_all(action='DESELECT')
            label_plane_for_casting_obj.select_set(True)
            bpy.context.view_layer.objects.active = label_plane_for_casting_obj

            #应用平面的缩裹修改器
            panel_modifier_name = "Shrinkwrap"
            target_modifier = None
            for modifier in label_plane_for_casting_obj.modifiers:
                if modifier.name == panel_modifier_name:
                    target_modifier = modifier
            if (target_modifier != None):
                bpy.ops.object.modifier_apply(modifier="Shrinkwrap", single_user=True)

            #为用于铸造法的物体添加材质
            label_plane_for_casting_obj.data.materials.clear()
            if name == '右耳':
                label_plane_for_casting_obj.data.materials.append(bpy.data.materials["YellowR"])
            elif name == '左耳':
                label_plane_for_casting_obj.data.materials.append(bpy.data.materials["YellowL"])

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
            label_plane_for_casting_obj.data.materials.append(bpy.data.materials['Transparency'])

            # 记录平面位置,将用于铸造法的平面位置设置为其位置
            text_x = text_obj.dimensions.x
            text_y = text_obj.dimensions.y
            label_plane_for_casting_obj.location[0] = plane_obj.location[0]
            label_plane_for_casting_obj.location[1] = plane_obj.location[1]
            label_plane_for_casting_obj.location[2] = plane_obj.location[2]
            label_plane_for_casting_obj.rotation_euler[0] = plane_obj.rotation_euler[0]
            label_plane_for_casting_obj.rotation_euler[1] = plane_obj.rotation_euler[1]
            label_plane_for_casting_obj.rotation_euler[2] = plane_obj.rotation_euler[2]
            label_plane_for_casting_obj.dimensions.x = text_x * 1.2
            label_plane_for_casting_obj.dimensions.y = text_y * 1.2

            #将该物体隐藏并将平面设置为当前激活物体
            label_plane_for_casting_obj.select_set(False)
            label_plane_for_casting_obj.hide_set(True)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj



class LabelInfoSave(object):
    '''
    保存提交前的每个Label信息
    '''
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

        bpy.context.scene.var = 40
        name = bpy.context.scene.leftWindowObj
        global label_index
        global label_indexL
        global label_info_save
        global label_info_saveL
        if name == '右耳':
            label_index = -1
            label_info_save = []
        elif name == '左耳':
            label_indexL = -1
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
        for obj in bpy.data.objects:
            patternR = r'右耳LabelPlaneForCasting'
            patternL = r'左耳LabelPlaneForCasting'
            if re.match(patternR, obj.name) or re.match(patternL, obj.name):
                label_obj = obj
                bpy.data.objects.remove(label_obj, do_unlink=True)
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
        bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
        # 将激活物体设置为左/右耳
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj
        return {'FINISHED'}

class LabelBackForwardAdd(bpy.types.Operator):
    bl_idname = "object.labelbackforwardadd"
    bl_label = "单步撤回过程中添加字体"

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        #
        # name = bpy.context.scene.leftWindowObj
        # global label_index
        # global label_indexL
        # global label_info_save
        # global label_info_saveL
        # labelText = None
        # label_info_save_cur = None
        # if name == '右耳':
        #     labelText = bpy.context.scene.labelText
        #     label_info_save_cur = label_info_save
        # elif name == '左耳':
        #     labelText = bpy.context.scene.labelTextL
        #     label_info_save_cur = label_info_saveL
        # # 若模型上存在未提交的Label,则先将其提交
        # labelSubmit()
        #
        # # 双击添加过一个字体之后,才能够继续添加字体
        # if (len(label_info_save_cur) == 0):
        #     bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
        #     return {'FINISHED'}
        # # 创建新的Label
        # addLabel(labelText)
        # # 将Plane激活并选中
        # planename = name + "Plane"
        # plane_obj = bpy.data.objects.get(planename)
        # plane_obj.select_set(True)
        # bpy.context.view_layer.objects.active = plane_obj
        # #将新创建的字体位置设置未上一个提交的字体位置
        # labelInfo = label_info_save_cur[len(label_info_save_cur) - 1]
        # if name == '右耳':
        #     label_index = label_index + 1
        #     print("添加字体后:",label_index)
        # elif name == '左耳':
        #     label_indexL = label_indexL + 1
        #     print("添加字体后:", label_indexL)
        # l_x = labelInfo.l_x
        # l_y = labelInfo.l_y
        # l_z = labelInfo.l_z
        # r_x = labelInfo.r_x
        # r_y = labelInfo.r_y
        # r_z = labelInfo.r_z
        # plane_obj.location[0] = l_x
        # plane_obj.location[1] = l_y
        # plane_obj.location[2] = l_z
        # plane_obj.rotation_euler[0] = r_x
        # plane_obj.rotation_euler[1] = r_y
        # plane_obj.rotation_euler[2] = r_z
        #
        # if bpy.context.scene.var != 44:
        #     bpy.context.scene.var = 44
        #     context.window_manager.modal_handler_add(self)
        #     print("labelbackforwordadd_modal_invoke")
        # return {'RUNNING_MODAL'}

    def execute(self, context):
        name = bpy.context.scene.leftWindowObj
        global label_index
        global label_indexL
        global label_info_save
        global label_info_saveL
        labelText = None
        label_info_save_cur = None
        if name == '右耳':
            labelText = bpy.context.scene.labelText
            label_info_save_cur = label_info_save
        elif name == '左耳':
            labelText = bpy.context.scene.labelTextL
            label_info_save_cur = label_info_saveL
        # 若模型上存在未提交的Label,则先将其提交
        labelSubmit()

        # 双击添加过一个字体之后,才能够继续添加字体
        if (len(label_info_save_cur) == 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
            return {'FINISHED'}
        # 创建新的Label
        addLabel(labelText)
        # 将Plane激活并选中
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        #将新创建的字体位置设置未上一个提交的字体位置
        labelInfo = label_info_save_cur[len(label_info_save_cur) - 1]
        if name == '右耳':
            label_index = label_index + 1
            print("添加字体后:",label_index)
        elif name == '左耳':
            label_indexL = label_indexL + 1
            print("添加字体后:", label_indexL)
        l_x = labelInfo.l_x
        l_y = labelInfo.l_y
        l_z = labelInfo.l_z
        r_x = labelInfo.r_x
        r_y = labelInfo.r_y
        r_z = labelInfo.r_z
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z

    # def modal(self, context, event):
    #     name = bpy.context.scene.leftWindowObj
    #     cubename = name + "Text"
    #     label_obj = bpy.data.objects.get(cubename)
    #     planename = name + "Plane"
    #     plane_obj = bpy.data.objects.get(planename)
    #     cur_obj_name = bpy.context.scene.leftWindowObj
    #     cur_obj = bpy.data.objects.get(cur_obj_name)
    #     if bpy.context.screen.areas[0].spaces.active.context == 'MODIFIER':
    #         if (bpy.context.scene.var == 44):
    #             # 在数组中更新附件的信息
    #             updateInfo()
    #             if (is_mouse_on_object(context, event) and not is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 # 公共鼠标行为加双击移动附件位置
    #                 bpy.ops.wm.tool_set_by_id(name="my_tool.label_mouse")
    #                 cur_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = cur_obj
    #                 plane_obj.select_set(False)
    #             elif (is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                 plane_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = plane_obj
    #                 cur_obj.select_set(False)
    #             elif ((not is_mouse_on_object(context, event)) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                 cur_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = cur_obj
    #                 plane_obj.select_set(False)
    #             return {'PASS_THROUGH'}
    #         else:
    #             print("labelbackforwordadd_modal_finished")
    #             return {'FINISHED'}
    #
    #     else:
    #         if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
    #             print("labelbackforwordadd_modal_finished")
    #             set_switch_time(None)
    #             now_context = bpy.context.screen.areas[0].spaces.active.context
    #             if not check_modals_running(bpy.context.scene.var, now_context):
    #                 bpy.context.scene.var = 0
    #             return {'FINISHED'}
    #         return {'PASS_THROUGH'}


class LabelAddInvoke(bpy.types.Operator):
    bl_idname = "object.labeladdinvoke"
    bl_label = "调用labeladd操作类,添加字体(在上一个modal结束后再调用新的modal,防止modal开启过多造成卡顿)"

    def invoke(self, context, event):

        bpy.context.scene.var = 45
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_labelAdd_modal_start
        global is_labelAdd_modal_startL
        name = bpy.context.scene.leftWindowObj
        if (name == '右耳'):
            if (not is_labelAdd_modal_start):
                is_labelAdd_modal_start = True
                bpy.ops.object.labeladd('INVOKE_DEFAULT')
                return {'FINISHED'}
        elif (name == '左耳'):
            if (not is_labelAdd_modal_startL):
                is_labelAdd_modal_startL = True
                bpy.ops.object.labeladd('INVOKE_DEFAULT')
                return {'FINISHED'}
        return {'PASS_THROUGH'}





class LabelAdd(bpy.types.Operator):
    bl_idname = "object.labeladd"
    bl_label = "点击加号按钮添加字体"

    def invoke(self, context, event):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        #
        # name = bpy.context.scene.leftWindowObj
        # global label_index
        # global label_indexL
        # global label_info_save
        # global label_info_saveL
        # global is_labelAdd_modal_start
        # global is_labelAdd_modal_startL
        # labelText = None
        # label_index_cur = None
        # label_info_save_cur = None
        # if name == '右耳':
        #     labelText = bpy.context.scene.labelText
        #     label_index_cur = label_index
        #     label_info_save_cur = label_info_save
        #     is_labelAdd_modal_start = True
        # elif name == '左耳':
        #     labelText = bpy.context.scene.labelTextL
        #     label_index_cur = label_indexL
        #     label_info_save_cur = label_info_saveL
        #     is_labelAdd_modal_startL = True
        # # 若模型上存在未提交的Label,则先将其提交
        # labelSubmit()
        #
        # # 双击添加过一个字体之后,才能够继续添加字体
        # if (len(label_info_save_cur) == 0):
        #     bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
        #     if (name == "右耳"):
        #         is_labelAdd_modal_start = False
        #     elif (name == "左耳"):
        #         is_labelAdd_modal_startL = False
        #     return {'FINISHED'}
        # if(label_index_cur == len(label_info_save_cur) -1):
        #     # 创建新的Label
        #     addLabel(labelText)
        #     # 将Plane激活并选中
        #     planename = name + "Plane"
        #     plane_obj = bpy.data.objects.get(planename)
        #     plane_obj.select_set(True)
        #     bpy.context.view_layer.objects.active = plane_obj
        #     #将新创建的字体位置设置未上一个提交的字体位置
        #     labelInfo = label_info_save_cur[len(label_info_save_cur) - 1]
        #     if name == '右耳':
        #         label_index = label_index + 1
        #         print("添加字体后:",label_index)
        #     elif name == '左耳':
        #         label_indexL = label_indexL + 1
        #         print("添加字体后:", label_indexL)
        #     l_x = labelInfo.l_x
        #     l_y = labelInfo.l_y
        #     l_z = labelInfo.l_z
        #     r_x = labelInfo.r_x
        #     r_y = labelInfo.r_y
        #     r_z = labelInfo.r_z
        #     plane_obj.location[0] = l_x
        #     plane_obj.location[1] = l_y
        #     plane_obj.location[2] = l_z
        #     plane_obj.rotation_euler[0] = r_x
        #     plane_obj.rotation_euler[1] = r_y
        #     plane_obj.rotation_euler[2] = r_z
        #
        #     if bpy.context.scene.var != 41:
        #         bpy.context.scene.var = 41
        #         context.window_manager.modal_handler_add(self)
        #         print("labeladd_modal_invoke")
        #     return {'RUNNING_MODAL'}

    def execute(self, context):
        name = bpy.context.scene.leftWindowObj
        global label_index
        global label_indexL
        global label_info_save
        global label_info_saveL
        global is_labelAdd_modal_start
        global is_labelAdd_modal_startL
        labelText = None
        label_index_cur = None
        label_info_save_cur = None
        if name == '右耳':
            labelText = bpy.context.scene.labelText
            label_index_cur = label_index
            label_info_save_cur = label_info_save
            # is_labelAdd_modal_start = True
        elif name == '左耳':
            labelText = bpy.context.scene.labelTextL
            label_index_cur = label_indexL
            label_info_save_cur = label_info_saveL
            # is_labelAdd_modal_startL = True
        # 若模型上存在未提交的Label,则先将其提交
        labelSubmit()

        # 双击添加过一个字体之后,才能够继续添加字体
        if (len(label_info_save_cur) == 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
            if (name == "右耳"):
                is_labelAdd_modal_start = False
            elif (name == "左耳"):
                is_labelAdd_modal_startL = False
            return {'FINISHED'}
        if(label_index_cur == len(label_info_save_cur) -1):
            # 创建新的Label
            addLabel(labelText)
            # 将Plane激活并选中
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            #将新创建的字体位置设置未上一个提交的字体位置
            labelInfo = label_info_save_cur[len(label_info_save_cur) - 1]
            if name == '右耳':
                label_index = label_index + 1
                print("添加字体后:",label_index)
            elif name == '左耳':
                label_indexL = label_indexL + 1
                print("添加字体后:", label_indexL)
            l_x = labelInfo.l_x
            l_y = labelInfo.l_y
            l_z = labelInfo.l_z
            r_x = labelInfo.r_x
            r_y = labelInfo.r_y
            r_z = labelInfo.r_z
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
            if context.scene.var != 41:
                bpy.ops.object.labelswitch('INVOKE_DEFAULT')

    # def modal(self, context, event):
    #     global is_labelAdd_modal_start
    #     global is_labelAdd_modal_startL
    #     name = bpy.context.scene.leftWindowObj
    #     cubename = name + "Text"
    #     label_obj = bpy.data.objects.get(cubename)
    #     planename = name + "Plane"
    #     plane_obj = bpy.data.objects.get(planename)
    #     cur_obj_name = bpy.context.scene.leftWindowObj
    #     cur_obj = bpy.data.objects.get(cur_obj_name)
    #     if bpy.context.screen.areas[0].spaces.active.context == 'MODIFIER':
    #         if (bpy.context.scene.var == 41):
    #             # 在数组中更新附件的信息
    #             updateInfo()
    #             if (is_mouse_on_object(context, event) and not is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 # 公共鼠标行为加双击移动附件位置
    #                 bpy.ops.wm.tool_set_by_id(name="my_tool.label_mouse")
    #                 cur_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = cur_obj
    #                 plane_obj.select_set(False)
    #             elif (is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                 plane_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = plane_obj
    #                 cur_obj.select_set(False)
    #             elif ((not is_mouse_on_object(context, event)) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                 cur_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = cur_obj
    #                 plane_obj.select_set(False)
    #             return {'PASS_THROUGH'}
    #         else:
    #             print("labeladd_modal_finished")
    #             if (name == "右耳"):
    #                 is_labelAdd_modal_start = False
    #             elif (name == "左耳"):
    #                 is_labelAdd_modal_startL = False
    #             return {'FINISHED'}
    #
    #     else:
    #         if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
    #             print("labeladd_modal_finished")
    #             if (name == "右耳"):
    #                 is_labelAdd_modal_start = False
    #             elif (name == "左耳"):
    #                 is_labelAdd_modal_startL = False
    #             set_switch_time(None)
    #             now_context = bpy.context.screen.areas[0].spaces.active.context
    #             if not check_modals_running(bpy.context.scene.var, now_context):
    #                 bpy.context.scene.var = 0
    #             return {'FINISHED'}
    #         return {'PASS_THROUGH'}


class LabelInitialAdd(bpy.types.Operator):
    bl_idname = "object.labelinitialadd"
    bl_label = "进入附件模块初始化双击添加字体"

    def invoke(self, context, event):
        self.add_label(context, event)
        return {'FINISHED'}

        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        # global label_index
        # global label_indexL
        # name = bpy.context.scene.leftWindowObj
        # # 创建新的Label
        # labelText = None
        # if name == '右耳':
        #     labelText = bpy.context.scene.labelText
        # elif name == '左耳':
        #     labelText = bpy.context.scene.labelTextL
        # addLabel(labelText)
        # # 将Plane激活并选中
        # planename = name + "Plane"
        # plane_obj = bpy.data.objects.get(planename)
        # plane_obj.select_set(True)
        # bpy.context.view_layer.objects.active = plane_obj
        # co, normal = cal_co(context,event)
        # if(co != -1):
        #     # plane_obj.location = co
        #     label_fit_rotate(normal,co)
        # # 添加完最初的一个附件之后,将指针置为0
        # if (name == '右耳'):
        #     label_index = 0
        #     print("初始化添加后的指针:", label_index)
        # elif (name == '左耳'):
        #     label_indexL = 0
        #     print("初始化添加后的指针:", label_indexL)
        #
        # if bpy.context.scene.var != 42:
        #     bpy.context.scene.var = 42
        #     context.window_manager.modal_handler_add(self)
        #     print("labelinitialadd_modal_invoke")
        # return {'RUNNING_MODAL'}

    def add_label(self, context, event):
        global label_index
        global label_indexL
        name = bpy.context.scene.leftWindowObj
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
        # 添加完最初的一个附件之后,将指针置为0
        if (name == '右耳'):
            label_index = 0
            print("初始化添加后的指针:", label_index)
        elif (name == '左耳'):
            label_indexL = 0
            print("初始化添加后的指针:", label_indexL)
        bpy.ops.object.labelswitch('INVOKE_DEFAULT')

    # def modal(self, context, event):
    #     name = bpy.context.scene.leftWindowObj
    #     cubename = name + "Text"
    #     label_obj = bpy.data.objects.get(cubename)
    #     planename = name + "Plane"
    #     plane_obj = bpy.data.objects.get(planename)
    #     cur_obj_name = bpy.context.scene.leftWindowObj
    #     cur_obj = bpy.data.objects.get(cur_obj_name)
    #     if bpy.context.screen.areas[0].spaces.active.context == 'MODIFIER':
    #         if (bpy.context.scene.var == 42):
    #             # 在数组中更新附件的信息
    #             updateInfo()
    #             if (is_mouse_on_object(context, event) and not is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 # 公共鼠标行为加双击移动附件位置
    #                 bpy.ops.wm.tool_set_by_id(name="my_tool.label_mouse")
    #                 cur_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = cur_obj
    #                 plane_obj.select_set(False)
    #             elif (is_mouse_on_label(context, event) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                 plane_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = plane_obj
    #                 cur_obj.select_set(False)
    #             elif ((not is_mouse_on_object(context, event)) and (is_changed_label(context, event) or is_changed(context, event))):
    #                 bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                 cur_obj.select_set(True)
    #                 bpy.context.view_layer.objects.active = cur_obj
    #                 plane_obj.select_set(False)
    #             return {'PASS_THROUGH'}
    #         else:
    #             print("labelinitialadd_modal_finished")
    #             return {'FINISHED'}
    #
    #     else:
    #         if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
    #             print("labelinitialadd_modal_finished")
    #             set_switch_time(None)
    #             now_context = bpy.context.screen.areas[0].spaces.active.context
    #             if not check_modals_running(bpy.context.scene.var, now_context):
    #                 bpy.context.scene.var = 0
    #             return {'FINISHED'}
    #         return {'PASS_THROUGH'}


class LabelSwitch(bpy.types.Operator):
    bl_idname = "object.labelswitch"
    bl_label = "字体鼠标行为"

    def invoke(self, context, event):
        global is_labelAdd_modal_start, is_labelAdd_modal_startL
        bpy.context.scene.var = 41
        # if not is_labelAdd_modal_start and not is_labelAdd_modal_startL:
        #     name = bpy.context.scene.leftWindowObj
        #     if name == '右耳':
        #         is_labelAdd_modal_start = True
        #     elif name == '左耳':
        #         is_labelAdd_modal_startL = True
        #     context.window_manager.modal_handler_add(self)
        #     print("labelswitch_modal_invoke")
        if not is_labelAdd_modal_start:
            is_labelAdd_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("labelswitch_modal_invoke")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        override1 = getOverride()
        area = override1['area']

        global is_labelAdd_modal_start, is_labelAdd_modal_startL
        name = bpy.context.scene.leftWindowObj
        cubename = name + "Text"
        label_obj = bpy.data.objects.get(cubename)
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = bpy.context.scene.leftWindowObj
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if bpy.context.screen.areas[0].spaces.active.context == 'MODIFIER':
            if get_mirror_context():
                print('labelswitch_modal_finished')
                is_labelAdd_modal_start = False
                set_mirror_context(False)
                return {'FINISHED'}
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 41):
                if cur_obj != None and plane_obj != None:
                    if event.type == 'WHEELUPMOUSE':
                        if name == '右耳':
                            bpy.context.scene.deep += 0.05
                        else:
                            bpy.context.scene.deepL += 0.05
                        return {'RUNNING_MODAL'}
                    elif event.type == 'WHEELDOWNMOUSE':
                        if name == '右耳':
                            bpy.context.scene.deep -= 0.05
                        else:
                            bpy.context.scene.deepLL -= 0.05
                        return {'RUNNING_MODAL'}

                    # 在数组中更新附件的信息
                    updateInfo()
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
                    return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 41 and bpy.context.scene.var in get_process_var_list("编号"):
                print("labelswitch_modal_finished")
                is_labelAdd_modal_start = False
                # if (name == "右耳"):
                #     is_labelAdd_modal_start = False
                # elif (name == "左耳"):
                #     is_labelAdd_modal_startL = False
                return {'FINISHED'}

            else:
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                print("labelswitch_modal_finished")
                is_labelAdd_modal_start = False
                # if (name == "右耳"):
                #     is_labelAdd_modal_start = False
                # elif (name == "左耳"):
                #     is_labelAdd_modal_startL = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class LabelSubmit(bpy.types.Operator):
    bl_idname = "object.labelsubmit"
    bl_label = "标签提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 43
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
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


class LabelMirror(bpy.types.Operator):
    bl_idname = 'object.labelmirror'
    bl_label = '标签镜像'

    def invoke(self, context, event):
        print('进入镜像了')
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global label_info_saveL, label_info_save
        global label_indexL, label_index

        left_obj = bpy.data.objects.get(context.scene.leftWindowObj)
        right_obj = bpy.data.objects.get(context.scene.rightWindowObj)

        # 只操作一个耳朵时，不执行镜像
        if left_obj == None or right_obj == None:
            return {'FINISHED'}

        tar_obj_name = bpy.context.scene.leftWindowObj
        tar_obj = bpy.data.objects[tar_obj_name]

        if tar_obj_name == '左耳' and label_indexL != -1:
            return {'FINISHED'}
        elif tar_obj_name == '右耳' and label_index != -1:
            return {'FINISHED'}

        workspace = context.window.workspace.name

        if tar_obj_name == '左耳':
            ori_label_info = label_info_save
            tar_label_info = label_info_saveL
        else:
            ori_label_info = label_info_saveL
            tar_label_info = label_info_save

        # 只在双窗口下执行镜像
        if len(ori_label_info) != 0 and len(tar_label_info) == 0:
            tar_info = ori_label_info[0]
            text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z = tar_info.text, tar_info.depth, tar_info.size, tar_info.style, tar_info.l_x, -tar_info.l_y, tar_info.l_z, tar_info.r_x, tar_info.r_y, tar_info.r_z
            # 将附件数组指针置为末尾
            if tar_obj_name == '左耳':
                label_indexL = -1
            else:
                label_index = -1

            # 创建新的Label
            labelText = None
            if tar_obj_name == '右耳':
                labelText = bpy.context.scene.labelTextL
            elif tar_obj_name == '左耳':
                labelText = bpy.context.scene.labelText
            addLabel(labelText)
            # 将Plane激活并选中
            planename = tar_obj_name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj

            # 添加完最初的一个附件之后,将指针置为0
            if (tar_obj_name == '右耳'):
                label_index = 0
                print("初始化添加后的指针:", label_index)
            elif (tar_obj_name == '左耳'):
                label_indexL = 0
                print("初始化添加后的指针:", label_indexL)



            # 获取添加后的Handle,并根据参数设置调整offset
            planename = tar_obj_name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            if plane_obj is not None:
                plane_obj.location[0] = l_x
                plane_obj.location[1] = l_y
                plane_obj.location[2] = l_z
                plane_obj.rotation_euler[0] = r_x
                plane_obj.rotation_euler[1] = r_y
                plane_obj.rotation_euler[2] = r_z

                bm = bmesh.new()
                bm.from_mesh(tar_obj.data)

                closest_vertex = None
                min_distance = float('inf')
                target_point = mathutils.Vector((l_x,l_y,l_z))

                for vert in bm.verts:
                    # 将顶点坐标转换到世界坐标系
                    vertex_world = tar_obj.matrix_world @ vert.co
                    distance = (vertex_world - target_point).length
                    if distance < min_distance:
                        min_distance = distance
                        closest_vertex = vert
                closest_vertex_world = tar_obj.matrix_world @ closest_vertex.co
                closest_vertex_normal = tar_obj.matrix_world.to_3x3() @ closest_vertex.normal

                label_fit_rotate(closest_vertex_normal, closest_vertex_world)
                if tar_obj_name == '左耳':
                    bpy.context.scene.labelTextL = text
                    bpy.context.scene.deepL = depth
                    bpy.context.scene.fontSizeL = size
                    bpy.context.scene.styleEnumL = style
                else:
                    bpy.context.scene.labelText = text
                    bpy.context.scene.deep = depth
                    bpy.context.scene.fontSize = size
                    bpy.context.scene.styleEnum = style
                bm.free()

        if context.scene.var != 41:
            bpy.ops.object.labelswitch('INVOKE_DEFAULT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")



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
        "在模型中上一个标签的位置处添加一个标签"
    )
    bl_icon = "ops.mesh.primitive_torus_add_gizmo"
    bl_widget = None
    bl_keymap = (
        ("object.labeladd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.labeladdinvoke", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.labeladd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
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
        "添加字体后,公共鼠标行为的各种操作,在模型上双击,附件移动到双击位置"
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

class MyTool_LabelInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_initial"
    bl_label = "标签添加初始化"
    bl_description = (
        "刚进入Label模块的时,在模型上双击位置处添加一个标签"
    )
    bl_icon = "brush.sculpt.thumb"
    bl_widget = None
    bl_keymap = (
        ("object.labelinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass

# 注册类
_classes = [
    LabelReset,
    LabelBackForwardAdd,
    LabelAddInvoke,
    LabelAdd,
    LabelInitialAdd,
    LabelSubmit,
    LabelDoubleClick,
    LabelMirror,
    LabelSwitch
]


def register_label_tools():
    bpy.utils.register_tool(MyTool_Label1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Label2, separator=True, group=False, after={MyTool_Label1.bl_idname})
    bpy.utils.register_tool(MyTool_Label3, separator=True, group=False, after={MyTool_Label2.bl_idname})
    bpy.utils.register_tool(MyTool_Label_Mirror, separator=True, group=False, after={MyTool_Label3.bl_idname})
    bpy.utils.register_tool(MyTool_Label_Mouse, separator=True, group=False, after={MyTool_Label_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_LabelInitial, separator=True, group=False, after={MyTool_Label_Mouse.bl_idname})


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_Label1, separator=True, group=False)
    # bpy.utils.register_tool(MyTool_Label2, separator=True, group=False, after={MyTool_Label1.bl_idname})
    # bpy.utils.register_tool(MyTool_Label3, separator=True, group=False, after={MyTool_Label2.bl_idname})
    # bpy.utils.register_tool(MyTool_Label_Mirror, separator=True, group=False, after={MyTool_Label3.bl_idname})
    # bpy.utils.register_tool(MyTool_Label_Mouse, separator=True, group=False, after={MyTool_Label_Mirror.bl_idname})
    # bpy.utils.register_tool(MyTool_LabelInitial, separator=True, group=False, after={MyTool_Label_Mouse.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Label1)
    bpy.utils.unregister_tool(MyTool_Label2)
    bpy.utils.unregister_tool(MyTool_Label3)
    bpy.utils.unregister_tool(MyTool_Label_Mirror)
    bpy.utils.unregister_tool(MyTool_Label_Mouse)
    bpy.utils.unregister_tool(MyTool_LabelInitial)
