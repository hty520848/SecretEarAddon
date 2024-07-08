import bpy
import bmesh
import mathutils
import math
from mathutils import Vector
from bpy_extras import view3d_utils
from math import sqrt
from pynput import mouse
from .tool import newShader, get_region_and_space, moveToRight, moveToLeft, utils_re_color, delete_useless_object, \
    newColor, getOverride, getOverride2
import re
import os

prev_on_sphere = False  # 之前是否位于圆球上
prev_on_sphereL = False
prev_on_object = False  # 之前是否位于左右耳模型上
prev_on_objectL = False
prev_on_soundcanal = False  # 之前是否位于传声孔上
prev_on_soundcanalL = False
number = 0  # 记录圆球和管道控制点的个数
numberL = 0
object_dic = {}  # 记录当前圆球名称以及对应控制点的索引,圆球名称通常为 name + 'soundcanalsphere' + str(sphere_number)
object_dicL = {}  # sphere_number由生成圆球的顺序决定(号角管的比较特殊,固定为100与101,但其信息并未加入到该字典中)
# 每个圆球都对应一个曲线的管道控制点控制管道的生成,控制点索引从管道一段开始到另一端逐渐递增
soundcanal_data = []  # 记录当前控制点的坐标
soundcanal_dataL = []
soundcanal_finish = False  # 传声孔是否提交
soundcanal_finishL = False
soundcanal_shape = 'OP1'  # 传声孔类型
soundcanal_shapeL = 'OP1'
soundcanal_hornpipe_offset = 0  # 号角管偏移量
soundcanal_hornpipe_offsetL = 0

mouse_index = 0  # 添加传声孔之后,切换其存在的鼠标行为,记录当前在切换到了哪种鼠标行为
mouse_indexL = 0

prev_sphere_number_plane = 0  # 记录鼠标在管道中间的红球间切换时,上次位于的红球
prev_sphere_number_planeL = 0

prev_on_rotate_sphere = False  # 判断鼠标是否在传声孔旋转球体上
prev_on_rotate_sphereL = False
is_on_rotate = False  # 是否处于旋转的鼠标状态,用于 附件三维旋转鼠标行为和附件平面旋转拖动鼠标行为之间的切换
is_on_rotateL = False

middle_dis = None  # 进入三维旋转模式之后,记录管道与模型相交处到号角管的距离
last_dis = None  # 进入三维旋转模式之后,记录管道与模型相交处的上一个圆球到号角管的距离


def get_is_on_rotate():
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        return is_on_rotate
    elif name == '左耳':
        return is_on_rotateL
    return is_on_rotate


def set_is_on_rotate(value):
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        is_on_rotate = value
    elif name == '左耳':
        is_on_rotateL = value


def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.use_backface_culling = True
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.4


def initialSoundcanalTransparency():
    mat = newShader("SoundcanalTransparency")  # 创建材质
    mat.use_backface_culling = True
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01


def get_object_dic_index():
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        return object_dic
    elif name == '左耳':
        return object_dicL
    return object_dic


def on_which_shpere(context, event):
    '''
    判断鼠标在哪个圆球上,不在圆球上则返回0
    返回值为200的时候表示鼠标在号角管上, 返回值为100的时候表示鼠标在号角管的控制球上
    其他情况下返回的为圆球名称的尾号索引
    '''
    global object_dic
    global object_dicL
    object_dic_cur = None
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        object_dic_cur = object_dic
    elif name == '左耳':
        object_dic_cur = object_dicL

    if context.area:
        context.area.tag_redraw()
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
    # 鼠标是否在号角管上
    hornpipe_name = name + 'Hornpipe'
    hornpipe_obj = bpy.data.objects.get(hornpipe_name)
    if (hornpipe_obj != None):
        mwi = hornpipe_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if hornpipe_obj.type == 'MESH':
            if (hornpipe_obj.mode == 'OBJECT'):
                mesh = hornpipe_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 200
    # 鼠标是否在号角管控制红球上
    # 号角管的控制球信息没有被添加到object_dic/L中,判断鼠标是否在该红球上
    hornpipe_sphere_name = name + 'soundcanalsphere' + '100'
    hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
    if (hornpipe_sphere_obj != None):
        mwi = hornpipe_sphere_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if hornpipe_sphere_obj.type == 'MESH':
            if (hornpipe_sphere_obj.mode == 'OBJECT'):
                mesh = hornpipe_sphere_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 100
    # 鼠标是否在号角管显示红球上
    # 号角管的控制球信息没有被添加到object_dic/L中,判断鼠标是否在该红球上
    hornpipe_sphere_name = name + 'soundcanalsphere' + '101'
    hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
    if (hornpipe_sphere_obj != None):
        mwi = hornpipe_sphere_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if hornpipe_sphere_obj.type == 'MESH':
            if (hornpipe_sphere_obj.mode == 'OBJECT'):
                mesh = hornpipe_sphere_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 101
    # 鼠标是否在管道的红球上
    for key in object_dic_cur:
        active_obj = bpy.data.objects[key]
        object_index = int(key.replace(name + 'soundcanalsphere', ''))
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
    return 0


def is_mouse_on_object(name, context, event):
    active_obj = bpy.data.objects[name]

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
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


def is_changed(context, event):
    '''
    创建管道前鼠标位置的判断
    鼠标在左右耳模型和空白区域之间切换的判断
    '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    curr_on_object = is_mouse_on_object(name, context, event)  # 当前鼠标在哪个物体上
    global prev_on_object  # 之前鼠标在那个物体上
    global prev_on_objectL
    name = bpy.context.scene.leftWindowObj
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


def is_changed_soundcanal(context, event):
    '''
    创建管道后鼠标位置的判断
    鼠标在管道模型和其他区域之间切换的判断
    '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    curr_on_soundcanal = is_mouse_on_object(name + 'meshsoundcanal', context, event)  # 当前鼠标在哪个物体上
    global prev_on_soundcanal  # 之前鼠标在那个物体上
    global prev_on_soundcanalL
    if name == '右耳':
        if (curr_on_soundcanal != prev_on_soundcanal):
            prev_on_soundcanal = curr_on_soundcanal
            return True
        else:
            return False
    elif name == '左耳':
        if (curr_on_soundcanal != prev_on_soundcanalL):
            prev_on_soundcanalL = curr_on_soundcanal
            return True
        else:
            return False
    return False


def is_changed_shpere(context, event):
    '''
    鼠标在圆球之间切换的判断
    '''
    curr_on_sphere = on_which_shpere(context, event)  # 当前鼠标在哪个物体上
    global prev_on_sphere  # 之前鼠标在那个物体上
    global prev_on_sphereL
    name = bpy.context.scene.leftWindowObj
    if (curr_on_sphere != 0):
        curr_on_sphere = True
    else:
        curr_on_sphere = False
    if name == '右耳':
        if (curr_on_sphere != prev_on_sphere):
            prev_on_sphere = curr_on_sphere
            return True
        else:
            return False
    elif name == '左耳':
        if (curr_on_sphere != prev_on_sphereL):
            prev_on_sphereL = curr_on_sphere
            return True
        else:
            return False
    return False


# 判断鼠标是否在附件圆球上
def is_mouse_on_sphere(context, event):
    name = bpy.context.scene.leftWindowObj + "SoundcanalSphere"
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


# 判断鼠标状态是否发生改变,圆球
def is_changed_sphere(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "SoundcanalSphere"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_rotate_sphere  # 之前鼠标是否在物体上
        global prev_on_rotate_sphereL  # 之前鼠标是否在物体上

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
            if (curr_on_object != prev_on_rotate_sphere):
                prev_on_rotate_sphere = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_rotate_sphereL):
                prev_on_rotate_sphereL = curr_on_object
                return True
            else:
                return False
    return False


def cal_co(name, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param name: 要检测物体的名字
    :return: 相交的坐标
    '''

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

            co, _, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None:
                return co  # 如果发生交叉，返回坐标的值

    return -1


def select_nearest_point(co):
    '''
    选择曲线上离坐标位置最近的两个点
    :param co: 坐标的值
    :return: 最近两个点的坐标以及要插入的下标
    '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects[name + 'soundcanal']
    # 获取曲线的数据
    curve_data = curve_obj.data
    # 遍历曲线的所有点
    min_dis = float('inf')
    min_dis_index = -1

    length = len(curve_data.splines[0].points)

    for spline in curve_data.splines:
        for point_index, point in enumerate(spline.points):
            # 计算点与给定点之间的距离
            distance_vector = Vector(point.co[0:3]) - co
            distance = distance_vector.dot(distance_vector)
            # 更新最小距离和对应的点索引
            if distance < min_dis:
                min_dis = distance
                min_dis_index = point_index

    if min_dis_index == 0:
        return (Vector(curve_data.splines[0].points[0].co[0:3]),
                Vector(curve_data.splines[0].points[1].co[0:3]), 1)

    elif min_dis_index == length - 1:
        return (Vector(curve_data.splines[0].points[length - 2].co[0:3]),
                Vector(curve_data.splines[0].points[length - 1].co[0:3]), length - 1)

    min_co = Vector(curve_data.splines[0].points[min_dis_index].co[0:3])
    secondmin_co = Vector(curve_data.splines[0].points[min_dis_index - 1].co[0:3])
    dis_vector1 = Vector(secondmin_co - co)
    dis_vector2 = Vector(min_co - co)
    if dis_vector1.dot(dis_vector2) < 0:
        insert_index = min_dis_index
    else:
        secondmin_co = Vector(curve_data.splines[0].points[min_dis_index + 1].co[0:3])
        insert_index = min_dis_index + 1
    return (min_co, secondmin_co, insert_index)


def copy_curve():
    ''' 复制曲线数据 '''
    # 选择要复制数据的源曲线对象
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    source_curve = bpy.data.objects[name + 'soundcanal']
    target_curve = new_curve(name + 'meshsoundcanal')
    # 复制源曲线的数据到新曲线
    target_curve.data.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = target_curve.data.splines.new(spline.type)
        new_spline.points.add(len(spline.points) - 1)
        new_spline.order_u = 2
        new_spline.use_smooth = True
        # new_spline.use_endpoint_u = True
        # new_spline.use_cyclic_u = True
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def convert_soundcanal():
    '''
    根据曲线控制点生成管道(更新曲线控制点之后重新生成管道)
    '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    if (bpy.data.objects.get(name + 'meshsoundcanal')):
        bpy.data.objects.remove(bpy.data.objects[name + 'meshsoundcanal'], do_unlink=True)  # 删除原有网格
    copy_curve()
    duplicate_obj = bpy.data.objects[name + 'meshsoundcanal']
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    bevel_depth = None
    if name == '右耳':
        bevel_depth = bpy.context.scene.chuanShenGuanDaoZhiJing / 2
    elif name == '左耳':
        bevel_depth = bpy.context.scene.chuanShenGuanDaoZhiJing_L / 2
    bpy.context.active_object.data.bevel_depth = bevel_depth  # 设置曲线倒角深度
    bpy.context.active_object.data.bevel_resolution = 16
    bpy.context.active_object.data.use_fill_caps = True  # 封盖
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    duplicate_obj.hide_select = True
    duplicate_obj.data.materials.clear()
    duplicate_obj.data.materials.append(bpy.data.materials["grey"])


def add_sphere(co, index):
    '''
    在指定位置生成圆球用于控制管道曲线的移动
    :param co:指定的坐标
    :param index:指定要钩挂的控制点的下标
    '''
    global number
    global numberL
    name = bpy.context.scene.leftWindowObj
    mesh = None
    name1 = None
    if name == '右耳':
        number += 1
        # 创建一个新的网格
        mesh = bpy.data.meshes.new(name + "soundcanalsphere")
        name1 = name + 'soundcanalsphere' + str(number)
    elif name == '左耳':
        numberL += 1
        # 创建一个新的网格
        mesh = bpy.data.meshes.new(name + "soundcanalsphere")
        name1 = name + 'soundcanalsphere' + str(numberL)

    obj = bpy.data.objects.new(name1, mesh)
    bpy.context.collection.objects.link(obj)
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        moveToRight(obj)
    elif name == '左耳':
        moveToLeft(obj)
    # 切换到编辑模式
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
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
    obj.data.materials.append(bpy.data.materials['red'])

    # 设置圆球的位置
    obj.location = co  # 指定的位置坐标
    hooktoobject(index)  # 绑定到指定下标


def mouse_switch(context, event):
    '''
    鼠标位于不同的物体上时,切换到不同的传声孔鼠标行为
    '''
    global mouse_index
    global mouse_indexL
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    is_on_rotate_cur = False
    if (name == '右耳'):
        is_on_rotate_cur = is_on_rotate
    elif (name == '左耳'):
        is_on_rotate_cur = is_on_rotateL
    if (not is_on_rotate_cur):
        if (name == '右耳'):
            sphere_number = on_which_shpere(context, event)
            if (sphere_number == 200 and mouse_index != 1):
                mouse_index = 1
                # update_hornpipe_rotate_finish()  # TODO
                # 号角管显示圆球颜色设置为红色
                sphere_name = name + 'soundcanalsphere' + '101'
                hornpipe_sphere_obj = bpy.data.objects.get(sphere_name)
                if (hornpipe_sphere_obj != None):
                    hornpipe_sphere_obj.data.materials.clear()
                    hornpipe_sphere_obj.data.materials.append(bpy.data.materials["red"])
                # 鼠标位于号角管上的时候,调用左键旋转的鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_circle")
                hornpipe_name = name + 'Hornpipe'
                hornpipe_obj = bpy.data.objects.get(hornpipe_name)
                hornpipe_obj.hide_select = False
                bpy.ops.object.select_all(action='DESELECT')
                hornpipe_obj.select_set(True)
                bpy.context.view_layer.objects.active = hornpipe_obj
            elif (sphere_number == 0 and mouse_index != 2):
                mouse_index = 2
                # update_hornpipe_rotate_finish()  # TODO
                # 号角管显示圆球颜色设置为红色
                sphere_name = name + 'soundcanalsphere' + '101'
                hornpipe_sphere_obj = bpy.data.objects.get(sphere_name)
                if (hornpipe_sphere_obj != None):
                    hornpipe_sphere_obj.data.materials.clear()
                    hornpipe_sphere_obj.data.materials.append(bpy.data.materials["red"])
                # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
                hornpipe_name = name + 'Hornpipe'
                hornpipe_obj = bpy.data.objects.get(hornpipe_name)
                if (hornpipe_obj != None):
                    hornpipe_obj.hide_select = True
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                bpy.data.objects[name].select_set(True)
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")
            elif (sphere_number != 200 and sphere_number != 0 and mouse_index != 3):
                mouse_index = 3
                # update_hornpipe_rotate_finish()  # TODO
                # 激活号角管圆球的时,号角管显示圆球颜色设置为黄色
                if (sphere_number == 100 or sphere_number == 101):
                    newColor('yellow', 1, 1, 0, 1, 0.8)
                    sphere_name = name + 'soundcanalsphere' + '101'
                    hornpipe_sphere_obj = bpy.data.objects[sphere_name]
                    hornpipe_sphere_obj.data.materials.clear()
                    hornpipe_sphere_obj.data.materials.append(bpy.data.materials["yellow"])
                # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
                hornpipe_name = name + 'Hornpipe'
                hornpipe_obj = bpy.data.objects.get(hornpipe_name)
                sphere_name = name + 'soundcanalsphere' + str(sphere_number)
                sphere_obj = bpy.data.objects.get(sphere_name)
                if (hornpipe_obj != None):
                    hornpipe_obj.hide_select = True
                bpy.ops.object.select_all(action='DESELECT')
                sphere_obj.select_set(True)
                bpy.context.view_layer.objects.active = sphere_obj
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal3")
        elif (name == '左耳'):
            sphere_number = on_which_shpere(context, event)
            if (sphere_number == 200 and mouse_indexL != 1):
                mouse_indexL = 1
                # update_hornpipe_rotate_finish()  # TODO
                # 号角管显示圆球颜色设置为红色
                sphere_name = name + 'soundcanalsphere' + '101'
                hornpipe_sphere_obj = bpy.data.objects.get(sphere_name)
                if (hornpipe_sphere_obj != None):
                    hornpipe_sphere_obj.data.materials.clear()
                    hornpipe_sphere_obj.data.materials.append(bpy.data.materials["red"])
                # 鼠标位于号角管上的时候,调用左键旋转的鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_circle")
                hornpipe_name = name + 'Hornpipe'
                hornpipe_obj = bpy.data.objects.get(hornpipe_name)
                hornpipe_obj.hide_select = False
                bpy.ops.object.select_all(action='DESELECT')
                hornpipe_obj.select_set(True)
                bpy.context.view_layer.objects.active = hornpipe_obj
            elif (sphere_number == 0 and mouse_indexL != 2):
                mouse_indexL = 2
                # update_hornpipe_rotate_finish()  # TODO
                # 号角管显示圆球颜色设置为红色
                sphere_name = name + 'soundcanalsphere' + '101'
                hornpipe_sphere_obj = bpy.data.objects.get(sphere_name)
                if (hornpipe_sphere_obj != None):
                    hornpipe_sphere_obj.data.materials.clear()
                    hornpipe_sphere_obj.data.materials.append(bpy.data.materials["red"])
                # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
                hornpipe_name = name + 'Hornpipe'
                hornpipe_obj = bpy.data.objects.get(hornpipe_name)
                if (hornpipe_obj != None):
                    hornpipe_obj.hide_select = True
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                bpy.data.objects[name].select_set(True)
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")
            elif (sphere_number != 200 and sphere_number != 0 and mouse_indexL != 3):
                mouse_indexL = 3
                # update_hornpipe_rotate_finish()  # TODO
                # 激活号角管圆球时,号角管显示圆球颜色设置为黄色
                if (sphere_number == 100 or sphere_number == 101):
                    newColor('yellow', 1, 1, 0, 1, 0.8)
                    sphere_name = name + 'soundcanalsphere' + '101'
                    hornpipe_sphere_obj = bpy.data.objects[sphere_name]
                    hornpipe_sphere_obj.data.materials.clear()
                    hornpipe_sphere_obj.data.materials.append(bpy.data.materials["yellow"])
                # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
                hornpipe_name = name + 'Hornpipe'
                hornpipe_obj = bpy.data.objects.get(hornpipe_name)
                sphere_name = name + 'soundcanalsphere' + str(sphere_number)
                sphere_obj = bpy.data.objects.get(sphere_name)
                if (hornpipe_obj != None):
                    hornpipe_obj.hide_select = True
                bpy.ops.object.select_all(action='DESELECT')
                sphere_obj.select_set(True)
                bpy.context.view_layer.objects.active = sphere_obj
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal3")
    elif (is_on_rotate_cur):  # TODO    调整三维旋转状态下的鼠标切换
        if (name == '右耳'):
            if (is_mouse_on_sphere(context, event) and mouse_index != 4):
                mouse_index = 4
                print("鼠标行为1")
                # 切换到三维旋转的模式
                # update_hornpipe_rotate_initial()  # TODO
                plane_name = name + 'HornpipePlane'
                plane_obj = bpy.data.objects.get(plane_name)
                bpy.ops.object.select_all(action='DESELECT')
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                bpy.context.scene.transform_orientation_slots[2].type = 'NORMAL'
            elif (not is_mouse_on_sphere(context, event) and mouse_index != 5):
                mouse_index = 5
                print("鼠标行为2")
                # 鼠标不再圆球上的时候，调用传声孔的鼠标行为,公共鼠标行为 双击添加圆球
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                bpy.data.objects[name].select_set(True)
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")
        elif (name == '左耳'):
            if (is_mouse_on_sphere(context, event) and mouse_index != 4):
                mouse_indexL = 4
                # 切换到三维旋转的模式
                # update_hornpipe_rotate_initial()  # TODO
                plane_name = name + 'HornpipePlane'
                plane_obj = bpy.data.objects.get(plane_name)
                bpy.ops.object.select_all(action='DESELECT')
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                bpy.context.scene.transform_orientation_slots[2].type = 'NORMAL'
            elif (not is_mouse_on_sphere(context, event) and mouse_index != 5):
                mouse_indexL = 5
                # 鼠标不在圆球上的时候，调用传声孔的鼠标行为,公共鼠标行为 双击添加圆球
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                bpy.data.objects[name].select_set(True)
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")


def plane_switch(sphere_number):
    '''
    鼠标在管道中的圆球中切换时,更新生成平面
    '''
    global prev_sphere_number_plane
    global prev_sphere_number_planeL
    name = bpy.context.scene.leftWindowObj
    # 若位于管道两端的圆球上,则需要吸附在模型上
    if sphere_number == 1 or sphere_number == 2:
        bpy.context.scene.tool_settings.use_snap = True
        # 左右耳模型是不可选中的,为了让其吸附在模型上,需要将该吸附参数设置为False
        bpy.context.scene.tool_settings.use_snap_selectable = False
    # 鼠标位于管道中间的圆球上且在不同的圆球上切换时,删除原有的平面并生成新的平面
    if (sphere_number != 0 and sphere_number != 1 and sphere_number != 2 and sphere_number != 100 and sphere_number != 101 and sphere_number != 200):
        bpy.context.scene.tool_settings.use_snap = True
        # 左右耳模型是不可选中的,平面是可选中的,设置该参数使其只能吸附在平面上
        bpy.context.scene.tool_settings.use_snap_selectable = True
        if (name == "右耳"):
            if (sphere_number != prev_sphere_number_plane):
                delete_sphere_snap_plane()
                create_sphere_snap_plane(sphere_number)
            prev_sphere_number_plane = sphere_number
        elif (name == "左耳"):
            if (sphere_number != prev_sphere_number_planeL):
                delete_sphere_snap_plane()
                create_sphere_snap_plane(sphere_number)
            prev_sphere_number_planeL = sphere_number


class TEST_OT_addsoundcanal(bpy.types.Operator):
    bl_idname = "object.addsoundcanal"
    bl_label = "addsoundcanal"
    bl_description = "双击添加管道控制点"

    def excute(self, context, event):

        global number
        global numberL
        number_cur = None
        # 主窗口物体
        name = bpy.context.scene.leftWindowObj
        mesh_name = name + 'meshsoundcanal'
        if name == '右耳':
            number_cur = number
        elif name == '左耳':
            number_cur = numberL
        if number_cur == 0:  # 如果number等于0，初始化
            co = cal_co(name, context, event)
            if co != -1:
                generate_canal(co)
                # 设置旋转中心
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects.get(name)

        elif number_cur == 1:  # 如果number等于1双击完成管道
            co = cal_co(name, context, event)
            if co != -1:
                finish_canal(co)
                # 将左右耳模型变透明
                bpy.data.objects[name].data.materials.clear()  # 清除材质
                bpy.data.objects[name].data.materials.append(bpy.data.materials["Transparency"])
                bpy.ops.object.select_all(action='DESELECT')
                # bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')

        else:  # 如果number大于1，双击添加控制点
            co = cal_co(mesh_name, context, event)
            if co != -1:
                min_index, secondmin_index, insert_index = select_nearest_point(co)
                add_canal(min_index, secondmin_index, co, insert_index)

            # 重新更新管道中间圆球生成的平面
            delete_sphere_snap_plane()
            create_sphere_snap_plane(number_cur)

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_deletesoundcanal(bpy.types.Operator):
    bl_idname = "object.deletesoundcanal"
    bl_label = "deletesoundcanal"
    bl_description = "双击删除管道控制点"

    def excute(self, context, event):

        global object_dic
        global object_dicL
        name = bpy.context.scene.leftWindowObj
        sphere_number = on_which_shpere(context, event)

        if sphere_number == 0:
            pass

        elif sphere_number == 1 or sphere_number == 2 or sphere_number == 100 or sphere_number == 101:
            pass

        else:
            if (name == "右耳"):
                # 主窗口物体
                name = bpy.context.scene.leftWindowObj
                sphere_name = name + 'soundcanalsphere' + str(sphere_number)
                index = object_dic[sphere_name]
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[name + 'soundcanal'].hide_set(False)
                bpy.context.view_layer.objects.active = bpy.data.objects[name + 'soundcanal']
                bpy.data.objects[name + 'soundcanal'].select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式删除点
                bpy.ops.curve.select_all(action='DESELECT')
                bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.data.objects[name + 'soundcanal'].select_set(False)
                bpy.data.objects[name + 'soundcanal'].hide_set(True)

                # 更新
                bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
                for key in object_dic:
                    if object_dic[key] > index:
                        object_dic[key] -= 1
                del object_dic[sphere_name]
                global number
                count = number - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'soundcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'soundcanalsphere' + str(sphere_number + i)
                        object_dic.update({replace_name: object_dic.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                number -= 1
                convert_soundcanal()
                save_soundcanal_info([0, 0, 0])
            elif (name == "左耳"):
                # 主窗口物体
                name = bpy.context.scene.leftWindowObj
                sphere_name = name + 'soundcanalsphere' + str(sphere_number)
                index = object_dicL[sphere_name]
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[name + 'soundcanal'].hide_set(False)
                bpy.context.view_layer.objects.active = bpy.data.objects[name + 'soundcanal']
                bpy.data.objects[name + 'soundcanal'].select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式删除点
                bpy.ops.curve.select_all(action='DESELECT')
                bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.data.objects[name + 'soundcanal'].select_set(False)
                bpy.data.objects[name + 'soundcanal'].hide_set(True)

                # 更新
                bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
                for key in object_dicL:
                    if object_dicL[key] > index:
                        object_dicL[key] -= 1
                del object_dicL[sphere_name]
                global numberL
                count = numberL - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'soundcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'soundcanalsphere' + str(sphere_number + i)
                        object_dicL.update({replace_name: object_dicL.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                numberL -= 1
                convert_soundcanal()
                save_soundcanal_info([0, 0, 0])

            # 更新号角管位置
            update_hornpipe_location()
            # 删除可能存在的圆球平面
            delete_sphere_snap_plane()

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_soundcanalqiehuan(bpy.types.Operator):
    bl_idname = "object.soundcanalqiehuan"
    bl_label = "soundcanalqiehuan"
    bl_description = "鼠标行为切换"

    __timer = None  # 定时器,设定一个固定的时间检测状态,更新状态,切换鼠标行为(若不设置定时器,一直处于检测状态则无法进行数据更新和鼠标切换)

    __mouse_listener = None
    __left_mouse_press = None
    __mouse_x = 0
    __mouse_y = 0
    __mouse_x_y_flag = False
    __start_update = False

    def invoke(self, context, event):  # 初始化
        op_cls = TEST_OT_soundcanalqiehuan
        print('soundcanalqiehuan invoke')
        initialTransparency()
        newColor('red', 1, 0, 0, 0, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)  # 不透明材质
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)  # 透明材质
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.1, window=context.window)
        if not op_cls.__mouse_listener:
            op_cls.__mouse_listener = mouse.Listener(
                on_click=self.on_click
            )
            # 启动监听器
            op_cls.__mouse_listener.start()

        bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")
        bpy.context.scene.var = 23
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global object_dic
        global object_dicL
        global is_on_rotate
        global is_on_rotateL

        mouse_x = event.mouse_x
        mouse_y = event.mouse_y
        override1 = getOverride()
        area = override1['area']
        op_cls = TEST_OT_soundcanalqiehuan

        # 鼠标在3D区域内
        if (mouse_x < area.width and area.y < mouse_y < area.y + area.height and bpy.context.scene.var == 23):
            object_dic_cur = None
            is_on_rotate_cur = None
            name = bpy.context.scene.leftWindowObj
            if (name == "右耳"):
                object_dic_cur = object_dic
                is_on_rotate_cur = is_on_rotate
            elif (name == "左耳"):
                object_dic_cur = object_dicL
                is_on_rotate_cur = is_on_rotateL

            # 不存在管道,在公共鼠标行为和双击添加控制点鼠标行为之间切换(公共鼠标行为功能始终存在)
            if len(object_dic_cur) < 2:
                # 切换到传声孔的鼠标行为之一, 公共鼠标行为 加 在模型上双击添加红点
                if cal_co(name, context, event) != -1 and is_changed(context, event) == True:
                    bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")
                # 切换到公共鼠标行为
                elif cal_co(name, context, event) == -1 and is_changed(context, event) == True:
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = bpy.data.objects[name]
                    bpy.data.objects[name].select_set(True)

            # 存在管道,在传声孔之间的鼠标行为见切花  在管道上双击添加控制点或者拖动红球控制点
            if len(object_dic_cur) >= 2:

                # 判断是否位于红球上,存在则返回其索引,不存在则返回0
                sphere_number = on_which_shpere(context, event)

                # 根据鼠标位于模型的种类,切换到不同的鼠标行为
                if not self.__left_mouse_press:
                    mouse_switch(context, event)

                # 实时更新管道控制点的位置,随圆球位置更新而改变
                # 未进入三维旋转状态的时候,拖动号角管控制圆球后更新管道
                if (not is_on_rotate_cur):

                    # 生成管道中间红球对应的平面
                    plane_switch(sphere_number)

                    # 鼠标位于管道或圆球上的时候,改变管道的材质,将其亮度调高
                    if cal_co(name + 'meshsoundcanal', context, event) == -1:
                        if is_changed_soundcanal(context, event) == True:
                            bpy.data.objects[name + 'meshsoundcanal'].data.materials.clear()
                            bpy.data.objects[name + 'meshsoundcanal'].data.materials.append(bpy.data.materials["grey"])
                    elif cal_co(name + 'meshsoundcanal', context, event) != -1:
                        if is_changed_soundcanal(context, event) == True:
                            bpy.data.objects[name + 'meshsoundcanal'].data.materials.clear()
                            bpy.data.objects[name + 'meshsoundcanal'].data.materials.append(bpy.data.materials["grey2"])

                    # 若鼠标不在圆球上
                    if sphere_number == 0 or sphere_number == 200:
                        return {'PASS_THROUGH'}
                    # 鼠标位于号角管的控制球上时,更新管道控制点的位置信息,管道的控制点随着圆球的移动而改变,同时摆正对齐号角管
                    elif (sphere_number == 100 or sphere_number == 101):
                        # 更新号角管位置信息,摆正对齐
                        update_hornpipe_location()
                        return {'PASS_THROUGH'}
                    # 鼠标位于其他控制圆球上的时候,管道控制点随着圆球位置的拖动改变而更新
                    else:
                        sphere_name = name + 'soundcanalsphere' + str(sphere_number)
                        obj = bpy.data.objects[sphere_name]
                        index = int(object_dic_cur[sphere_name])
                        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[0:3] = \
                            bpy.data.objects[
                                sphere_name].location
                        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[3] = 1
                        flag = save_soundcanal_info(obj.location)
                        if flag:
                            convert_soundcanal()
                        # 更新号角管位置信息,摆正对齐
                        update_hornpipe_location()
                        return {'PASS_THROUGH'}

                # 进入三维旋转状态的时候,旋转拖动号角管后更新管道
                elif (is_on_rotate_cur and is_mouse_on_sphere(context, event)):
                    if (self.__left_mouse_press):
                        if (self.__mouse_x_y_flag):
                            self.__mouse_x = event.mouse_x
                            self.__mouse_y = event.mouse_y
                            self.__mouse_x_y_flag = False
                    mouse_x = event.mouse_x
                    mouse_y = event.mouse_y
                    dis = math.sqrt(math.fabs(self.__mouse_x - mouse_x) ** 2 + math.fabs(
                        self.__mouse_y - mouse_y) ** 2)

                    # TODO： 距离（dis)的调整
                    if not self.__start_update and  self.__left_mouse_press == True and dis > 5:
                        self.__start_update = True

                    if (event.type == 'TIMER' and self.__left_mouse_press == True and self.__start_update and dis > 1):
                        update_hornpipe_rotate()  # TODO     三维鼠标旋转状态下实时更新管道

                    return {'PASS_THROUGH'}

            return {'PASS_THROUGH'}

        # 模式切换结束modal
        elif (bpy.context.scene.var != 23):
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
                print('soundcanalqiehuan finish')
            if op_cls.__mouse_listener:
                # 关闭监听器
                op_cls.__mouse_listener.stop()
                op_cls.__mouse_listener = None
            return {'FINISHED'}

        # 鼠标在3D区域外
        else:
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}

    def on_click(self, x, y, button, pressed):
        # 鼠标点击事件处理函数
        if button == mouse.Button.left and pressed:
            self.__left_mouse_press = True
            self.__mouse_x_y_flag = True
        elif button == mouse.Button.left and not pressed:
            self.__left_mouse_press = False
            self.__mouse_x_y_flag = False
            self.__start_update = False

class TEST_OT_finishsoundcanal(bpy.types.Operator):
    bl_idname = "object.finishsoundcanal"
    bl_label = "完成操作"
    bl_description = "点击按钮完成管道制作"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 24
        return {'FINISHED'}

    def excute(self, context, event):
        submit_soundcanal()
        global soundcanal_finish
        global soundcanal_finishL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            soundcanal_finish = True
        elif (name == "左耳"):
            soundcanal_finishL = True


class TEST_OT_resetsoundcanal(bpy.types.Operator):
    bl_idname = "object.resetsoundcanal"
    bl_label = "重置操作"
    bl_description = "点击按钮重置管道制作"

    def invoke(self, context, event):
        bpy.context.scene.var = 25
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        # 删除多余的物体
        global object_dic
        global object_dicL
        global soundcanal_finish
        global soundcanal_finishL
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            if not soundcanal_finish:
                is_on_rotate = False
                # 主窗口物体
                name = bpy.context.scene.leftWindowObj
                # 删除管道
                need_to_delete_model_name_list = [name + 'meshsoundcanal', name + 'soundcanal', name + 'HornpipePlane',
                                                  name + 'Hornpipe', name + 'soundcanalsphere' + '100',
                                                  name + 'soundcanalsphere' + '101',
                                                  name + 'SoundCanalPlaneBorderCurveObject', name + 'SoundCanalPlane',
                                                  name + 'SoundcanalSphere']
                # 删除圆球
                for key in object_dic:
                    bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
                delete_useless_object(need_to_delete_model_name_list)
                # 圆球字典置空
                object_dic.clear()
                # 将SoundCanalReset复制并替代当前操作模型
                oriname = name
                ori_obj = bpy.data.objects.get(oriname)
                copyname = name + "SoundCanalReset"
                copy_obj = bpy.data.objects.get(copyname)
                if (ori_obj != None and copy_obj != None):
                    bpy.data.objects.remove(ori_obj, do_unlink=True)
                    duplicate_obj = copy_obj.copy()
                    duplicate_obj.data = copy_obj.data.copy()
                    duplicate_obj.animation_data_clear()
                    duplicate_obj.name = oriname
                    bpy.context.collection.objects.link(duplicate_obj)
                    if name == '右耳':
                        moveToRight(duplicate_obj)
                    elif name == '左耳':
                        moveToLeft(duplicate_obj)
                global number
                global soundcanal_shape
                global soundcanal_hornpipe_offset
                global prev_sphere_number_plane
                number = 0
                soundcanal_shape = bpy.context.scene.soundcancalShapeEnum
                soundcanal_hornpipe_offset = bpy.context.scene.chuanShenKongOffset
                prev_sphere_number_plane = 0
                bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')
        elif name == '左耳':
            if not soundcanal_finishL:
                is_on_rotateL = False
                # 主窗口物体
                name = bpy.context.scene.leftWindowObj
                need_to_delete_model_name_list = [name + 'meshsoundcanal', name + 'soundcanal', name + 'HornpipePlane',
                                                  name + 'Hornpipe', name + 'soundcanalsphere' + '100',
                                                  name + 'soundcanalsphere' + '101',
                                                  name + 'SoundCanalPlaneBorderCurveObject', name + 'SoundCanalPlane',
                                                  name + 'SoundcanalSphere']
                for key in object_dicL:
                    bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
                delete_useless_object(need_to_delete_model_name_list)
                object_dicL.clear()
                # 将SoundCanalReset复制并替代当前操作模型
                oriname = name
                ori_obj = bpy.data.objects.get(oriname)
                copyname = name + "SoundCanalReset"
                copy_obj = bpy.data.objects.get(copyname)
                if (ori_obj != None and copy_obj != None):
                    bpy.data.objects.remove(ori_obj, do_unlink=True)
                    duplicate_obj = copy_obj.copy()
                    duplicate_obj.data = copy_obj.data.copy()
                    duplicate_obj.animation_data_clear()
                    duplicate_obj.name = oriname
                    bpy.context.collection.objects.link(duplicate_obj)
                    if name == '右耳':
                        moveToRight(duplicate_obj)
                    elif name == '左耳':
                        moveToLeft(duplicate_obj)
                global numberL
                global soundcanal_shapeL
                global soundcanal_hornpipe_offsetL
                global prev_sphere_number_planeL
                numberL = 0
                soundcanal_shapeL = bpy.context.scene.soundcancalShapeEnum_L
                soundcanal_hornpipe_offsetL = bpy.context.scene.chuanShenKongOffset_L
                prev_sphere_number_planeL = 0
                bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')


class TEST_OT_soundcanalrotate(bpy.types.Operator):
    bl_idname = "object.soundcanalrotate"
    bl_label = "鼠标的三维旋转状态"

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        plane_name = name + 'HornpipePlane'
        plane_obj = bpy.data.objects.get(plane_name)
        spherename = name + "SoundcanalSphere"
        sphere_obj = bpy.data.objects.get(spherename)
        if (plane_obj != None and sphere_obj != None):
            print("三维鼠标旋转按钮")
            # # 切换到三维旋转的模式
            # update_hornpipe_rotate_initial()
            # # 鼠标位于号角管上的时候,调用左键旋转的鼠标行为
            # plane_name = name + 'HornpipePlane'
            # plane_obj = bpy.data.objects.get(plane_name)
            # bpy.ops.object.select_all(action='DESELECT')
            # plane_obj.select_set(True)
            # bpy.context.view_layer.objects.active = plane_obj
            # bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
            if (name == '右耳'):
                is_on_rotate = not is_on_rotate
                if (is_on_rotate == True):
                    print("按钮三维旋转")
                    sphere_obj.hide_select = False
                    sphere_obj.select_set(True)
                    update_hornpipe_rotate_initial()
                else:
                    print("按钮非三维旋转")
                    # 当切换到非三维旋转模式的时候,将圆球设置为不可选中状态,防止拖动管道圆球上的时候圆球吸附到sphere_obj上而非红环平面上
                    sphere_obj.hide_select = False
                    sphere_obj.select_set(False)
                    sphere_obj.hide_select = True
                    update_hornpipe_rotate_finish()
            elif (name == '左耳'):
                is_on_rotateL = not is_on_rotateL
                if (is_on_rotateL == True):
                    sphere_obj.hide_select = False
                    sphere_obj.select_set(True)
                    update_hornpipe_rotate_initial()
                else:
                    sphere_obj.hide_select = False
                    sphere_obj.select_set(False)
                    sphere_obj.hide_select = True
                    update_hornpipe_rotate_finish()
        return {'FINISHED'}


def new_curve(curve_name):
    ''' 创建并返回一个新的曲线对象 '''
    curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
    curve_data.dimensions = '3D'
    obj = bpy.data.objects.new(curve_name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    bevel_depth = None
    if name == '右耳':
        bevel_depth = bpy.context.scene.chuanShenGuanDaoZhiJing / 2
        moveToRight(obj)
    elif name == '左耳':
        bevel_depth = bpy.context.scene.chuanShenGuanDaoZhiJing_L / 2
        moveToLeft(obj)
    obj.data.bevel_depth = bevel_depth  # 管道孔径
    obj.data.bevel_resolution = 16
    obj.data.use_fill_caps = True  # 封盖
    return obj


def generate_canal(co):
    ''' 初始化管道,添加第一个圆球并保存信息,创建曲线(此时还不可见)'''
    global number
    global numberL
    number_cur = None
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        number_cur = number
    elif name == '左耳':
        number_cur = numberL
    obj = new_curve(name + 'soundcanal')
    obj.data.materials.append(bpy.data.materials["grey"])
    # 添加一个曲线样条
    spline = obj.data.splines.new(type='NURBS')
    spline.order_u = 2
    spline.use_smooth = True
    spline.points[number_cur].co[0:3] = co
    spline.points[number_cur].co[3] = 1
    # spline.use_cyclic_u = True
    # spline.use_endpoint_u = True

    # 开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    # 在指定位置添加一个圆球并将其索引0记录到字典中
    add_sphere(co, 0)
    # 将管道控制点(圆球)位置信息保存到字典中
    save_soundcanal_info(co)


def project_point_on_line(point, line_point1, line_point2):
    line_vec = line_point2 - line_point1
    line_vec.normalize()
    point_vec = point - line_point1
    projection = line_vec.dot(point_vec) * line_vec
    projected_point = line_point1 + projection
    return projected_point


def add_canal(min_co, secondmin_co, co, insert_index):
    ''' 在管道上增加控制点 '''

    projected_point = project_point_on_line(co, min_co, secondmin_co)  # 计算目标点在向量上的投影点
    add_point(insert_index, projected_point)
    add_sphere(projected_point, insert_index)


def add_point(index, co):
    global number
    global numberL
    global object_dic
    global object_dicL
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        curve_object = bpy.data.objects[name + 'soundcanal']
        curve_data = curve_object.data
        new_curve_data = new_curve(name + 'newcurve').data
        # 在曲线上插入新的控制点
        new_curve_data.splines.clear()
        spline = new_curve_data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        new_curve_data.splines[0].points.add(count=number)

        # 设置新控制点的坐标
        for i, point in enumerate(curve_data.splines[0].points):
            if i < index:
                spline.points[i].co = point.co

        spline.points[index].co[0:3] = co
        spline.points[index].co[3] = 1

        for i, point in enumerate(curve_data.splines[0].points):
            if i >= index:
                spline.points[i + 1].co = point.co

        bpy.data.objects.remove(curve_object, do_unlink=True)
        bpy.data.objects[name + 'newcurve'].name = name + 'soundcanal'
        bpy.data.objects[name + 'soundcanal'].hide_set(True)

        for key in object_dic:
            if object_dic[key] >= index:
                object_dic[key] += 1
    elif name == '左耳':
        curve_object = bpy.data.objects[name + 'soundcanal']
        curve_data = curve_object.data
        new_curve_data = new_curve(name + 'newcurve').data
        # 在曲线上插入新的控制点
        new_curve_data.splines.clear()
        spline = new_curve_data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        new_curve_data.splines[0].points.add(count=numberL)

        # 设置新控制点的坐标
        for i, point in enumerate(curve_data.splines[0].points):
            if i < index:
                spline.points[i].co = point.co

        spline.points[index].co[0:3] = co
        spline.points[index].co[3] = 1

        for i, point in enumerate(curve_data.splines[0].points):
            if i >= index:
                spline.points[i + 1].co = point.co

        bpy.data.objects.remove(curve_object, do_unlink=True)
        bpy.data.objects[name + 'newcurve'].name = name + 'soundcanal'
        bpy.data.objects[name + 'soundcanal'].hide_set(True)

        for key in object_dicL:
            if object_dicL[key] >= index:
                object_dicL[key] += 1


def finish_canal(co):
    ''' 完成管道的初始化。存在一个圆球的情况加,再添加一个新的圆球  管道会初始化显示出来'''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    global soundcanal_shape
    global soundcanal_shapeL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    soundcanal_enum_cur = None
    soundcanal_hornpipe_offset_cur = 0
    if name == '右耳':
        soundcanal_enum_cur = soundcanal_shape
        bpy.context.scene.soundcancalShapeEnum = soundcanal_shape
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offset
        bpy.context.scene.chuanShenKongOffset = soundcanal_hornpipe_offset
    elif name == '左耳':
        soundcanal_enum_cur = soundcanal_shapeL
        bpy.context.scene.soundcancalShapeEnum_L = soundcanal_shapeL
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offsetL
        bpy.context.scene.chuanShenKongOffset_L = soundcanal_hornpipe_offsetL
    curve_object = bpy.data.objects[name + 'soundcanal']
    curve_data = curve_object.data
    obj = bpy.data.objects[name]
    # 根据管道中的第一个控制点信息和当前双击顶点位置, 获取管道首尾两个圆球中间第三个圆球的位置
    first_co = Vector(curve_data.splines[0].points[0].co[0:3])
    _, _, normal, _ = obj.closest_point_on_mesh(first_co)
    reverse_normal = (-normal[0], -normal[1], -normal[2])
    reverse_normal = Vector(reverse_normal)
    reverse_normal.normalize()
    point_vec = co - first_co
    projection = reverse_normal.dot(point_vec) * reverse_normal
    projected_point = first_co + projection
    # 为曲线添加两个新的控制点,其位置分别为参数中的co和得到的投影点
    curve_data.splines[0].points.add(count=2)
    curve_data.splines[0].points[1].co[0:3] = projected_point
    curve_data.splines[0].points[1].co[3] = 1
    curve_data.splines[0].points[2].co[0:3] = co
    curve_data.splines[0].points[2].co[3] = 1
    # 添加两个圆球并将索引信息保存到字典中
    add_sphere(co, 2)
    add_sphere(projected_point, 1)
    convert_soundcanal()
    save_soundcanal_info(co)
    curve_object.hide_set(True)
    bpy.data.objects[name].hide_select = True
    if (soundcanal_enum_cur == 'OP2'):
        # 将管道末端控制点隐藏
        last_sphere_name = name + 'soundcanalsphere' + '2'
        last_sphere_obj = bpy.data.objects.get(last_sphere_name)
        last_sphere_obj.hide_set(True)
        # 在管道末端初始化添加一个号角管
        initial_hornpipe()
        # 根据面板offset参数设置号角管偏移位置
        update_hornpipe_offset_location_normal()


def hooktoobject(index):
    ''' 建立指定下标的控制点到圆球的字典 '''
    global number
    global numberL
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        sphere_name = name + 'soundcanalsphere' + str(number)
        object_dic.update({sphere_name: index})
    elif name == '左耳':
        sphere_name = name + 'soundcanalsphere' + str(numberL)
        object_dicL.update({sphere_name: index})


def horn_fit_rotate(normal, location):
    '''
    将号角管移动到位置location并将号角管连界面与向量normal对齐垂直
    '''
    # 获取号角管平面(号角管的父物体)
    name = bpy.context.scene.leftWindowObj
    planename = name + "HornpipePlane"
    plane_obj = bpy.data.objects.get(planename)
    # 新建一个空物体根据向量normal建立一个局部坐标系
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
    # 将号角管摆正对齐
    if (plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z


def initial_hornpipe():
    '''
    生成管道后,在管道末端的位置添加一个号角管并摆正
    '''
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    if (name == "右耳"):
        object_dic_cur = object_dic
    elif (name == "左耳"):
        object_dic_cur = object_dicL
    # 导入号角管及其对应的控制红球
    script_dir = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.join(script_dir, "stl\\Hornpipe.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    hornpipe_name = "Hornpipe"
    hornpipe_obj = bpy.data.objects.get(hornpipe_name)
    hornpipe_obj.name = name + "Hornpipe"
    # 为号角管添加灰色材质
    newColor('grey', 0.8, 0.8, 0.8, 0, 1)  # 灰色不透明材质
    hornpipe_obj.data.materials.append(bpy.data.materials["grey"])
    # 导入传声孔模块中的圆球,主要用于鼠标模式切换,当三维旋转状态开启的时候,鼠标在圆球上的时候,调用三维旋转鼠标行为,否则调用公共鼠标行为
    bpy.ops.mesh.primitive_uv_sphere_add(segments=30, ring_count=30, radius=15, enter_editmode=False, align='WORLD',
                                         location=(0, -4.8, 4.5), scale=(1, 1, 1))
    spherename = "Sphere"
    sphere_obj = bpy.data.objects[spherename]
    sphere_obj.name = name + "SoundcanalSphere"
    initialSoundcanalTransparency()
    sphere_obj.data.materials.clear()
    sphere_obj.data.materials.append(bpy.data.materials['SoundcanalTransparency'])
    # 创建一个平面作为号角管的父物体,用于将号角管的位置摆正对齐
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, -4.8, 4.5), scale=(1, 1, 1))
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_obj.name = name + "HornpipePlane"
    initialSoundcanalTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['SoundcanalTransparency'])
    bpy.ops.object.select_all(action='DESELECT')
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    hornpipe_obj.select_set(True)
    sphere_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    hornpipe_obj.select_set(False)
    sphere_obj.select_set(False)
    # 将圆球设置为不可选中防止吸附到圆球上
    sphere_obj.hide_select = True
    # 获取管道末端控制点 和 与其相连的管道控制点 得到二者法线
    last_sphere_name = name + 'soundcanalsphere' + str(2)
    last_sphere_obj = bpy.data.objects.get(last_sphere_name)
    co = last_sphere_obj.location
    last_index = int(object_dic_cur[last_sphere_name])
    middle_index = last_index - 1  # 管道末端控制点相连的控制点红球索引比其小1
    middle_sphere_obj = None
    for key in object_dic_cur:
        key_obj = bpy.data.objects[key]
        key_index = int(object_dic_cur[key])
        if (key_index == middle_index):
            middle_sphere_obj = key_obj
            break
    middle_co = middle_sphere_obj.location
    # 更新号角管的位置并将其对齐
    normal = Vector(middle_co[0:3]) - Vector(co[0:3])
    horn_fit_rotate(normal, co)
    # 获取号角管控制点的位置
    step = 10
    hornpipe_point = (
    co[0] - normal.normalized()[0] * step, co[1] - normal.normalized()[1] * step, co[2] - normal.normalized()[2] * step)
    # 添加号角管控制圆球,鼠标激活拖动的是该圆球
    mesh = bpy.data.meshes.new(name + "soundcanalsphere")
    name1 = name + 'soundcanalsphere' + '100'  # 号角管控制圆球位置信息相对于号角管固定,因此其位置信息不会被保存,也不会将索引保存在object_dic中
    obj = bpy.data.objects.new(name1, mesh)  # 圆球名称为  右/左soundcanalsphere100 末尾数字下标固定为100
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    radius = 0.64
    segments = 32
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    newColor('hornpipeSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    obj.data.materials.append(bpy.data.materials['hornpipeSphereTransparency'])
    obj.location = hornpipe_point
    # 添加用于显示的号角管圆球,鼠标激活拖动号角管控制圆球的时候,该
    mesh = bpy.data.meshes.new(name + "soundcanalsphere")
    name1 = name + 'soundcanalsphere' + '101'  # 号角管控制圆球位置信息相对于号角管固定,因此其位置信息不会被保存,也不会将索引保存在object_dic中
    obj1 = bpy.data.objects.new(name1, mesh)  # 圆球名称为  右/左soundcanalsphere100 末尾数字下标固定为101
    bpy.context.collection.objects.link(obj1)
    bpy.context.view_layer.objects.active = obj1
    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj1.data)
    radius = 0.4
    segments = 32
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
    bmesh.update_edit_mesh(obj1.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj1.data.materials.append(bpy.data.materials['red'])
    obj1.select_set(False)
    obj1.location = hornpipe_point
    # 将添加的物体移动到集合中
    if name == '右耳':
        moveToRight(hornpipe_obj)
        moveToRight(sphere_obj)
        moveToRight(plane_obj)
        moveToRight(obj)
        moveToRight(obj1)
    elif name == '左耳':
        moveToLeft(hornpipe_obj)
        moveToLeft(sphere_obj)
        moveToLeft(plane_obj)
        moveToLeft(obj)
        moveToLeft(obj1)

    # 将号角管原点设置为平面的原点(父物体与子物体之间会有一条黑色的连线,将其隐藏)
    bpy.ops.object.select_all(action='DESELECT')
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.view3d.snap_cursor_to_selected()  # 将游标设置为平面的原点
    bpy.ops.object.select_all(action='DESELECT')
    hornpipe_obj.select_set(True)
    bpy.context.view_layer.objects.active = hornpipe_obj
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')  # 将原点设置为游标的位置

    # 设置旋转中心
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)


def update_hornpipe_offset_location_normal():
    '''
    根据面板的offset参数控制号角管的
    '''
    global object_dic
    global object_dicL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    soundcanal_hornpipe_offset_cur = 0
    if (name == "右耳"):
        object_dic_cur = object_dic
        soundcanal_hornpipe_offset_cur = bpy.context.scene.chuanShenKongOffset
        soundcanal_hornpipe_offset = bpy.context.scene.chuanShenKongOffset
    elif (name == "左耳"):
        object_dic_cur = object_dicL
        soundcanal_hornpipe_offset_cur = bpy.context.scene.chuanShenKongOffset_L
        soundcanal_hornpipe_offsetL = bpy.context.scene.chuanShenKongOffset_L
    # 根据与管道末端控制点相连的控制点红球和管道末端控制点红球位置获取对应法线
    last_sphere_name = name + 'soundcanalsphere' + str(2)
    last_sphere_obj = bpy.data.objects.get(last_sphere_name)
    hornpipe_sphere_name = name + 'soundcanalsphere' + str(100)  # 号角管控制红球
    hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
    hornpipe_sphere_name1 = name + 'soundcanalsphere' + str(101)  # 号角管显示红球
    hornpipe_sphere_obj1 = bpy.data.objects.get(hornpipe_sphere_name1)
    if (last_sphere_obj != None and hornpipe_sphere_obj != None and hornpipe_sphere_obj1 != None):
        last_co = last_sphere_obj.location
        last_index = int(object_dic_cur[last_sphere_name])
        middle_index = last_index - 1  # 管道末端控制点相连的控制点红球索引比其小1
        middle_sphere_obj = None
        for key in object_dic_cur:
            key_obj = bpy.data.objects[key]
            key_index = int(object_dic_cur[key])
            if (key_index == middle_index):
                middle_sphere_obj = key_obj
                break
        middle_co = middle_sphere_obj.location
        normal = Vector(middle_co[0:3]) - Vector(last_co[0:3])
        step = soundcanal_hornpipe_offset_cur
        offset_co = (last_co[0] - normal.normalized()[0] * step, last_co[1] - normal.normalized()[1] * step,
                     last_co[2] - normal.normalized()[2] * step)
        # 管道末端长度随着offset偏移
        index = int(object_dic_cur[last_sphere_name])
        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[0:3] = offset_co
        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[3] = 1
        flag = save_soundcanal_info(offset_co)
        if flag:
            convert_soundcanal()
        # 号角管的位置随offset偏移并摆正
        horn_fit_rotate(normal, offset_co)
        # 更新号角管控制红球的位置
        step = 10
        hornpipe_point = (offset_co[0] - normal.normalized()[0] * step, offset_co[1] - normal.normalized()[1] * step,
                          offset_co[2] - normal.normalized()[2] * step)
        hornpipe_sphere_obj.location = hornpipe_point
        hornpipe_sphere_obj1.location = hornpipe_point


def update_hornpipe_location():
    '''
    存在号角管的情况下,改变其他红球位置的时候,同步更新号角管的位置
    '''
    global object_dic
    global object_dicL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    soundcanal_hornpipe_offset_cur = 0
    if (name == "右耳"):
        object_dic_cur = object_dic
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offset
    elif (name == "左耳"):
        object_dic_cur = object_dicL
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offsetL
    cur_obj = bpy.data.objects[name]
    hornpipe_sphere_name = name + 'soundcanalsphere' + str(100)  # 号角管控制圆球
    hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
    hornpipe_sphere_name1 = name + 'soundcanalsphere' + str(101)  # 号角管显示圆球
    hornpipe_sphere_obj1 = bpy.data.objects.get(hornpipe_sphere_name1)
    hornpipe_name = name + 'Hornpipe'
    hornpipe_obj = bpy.data.objects.get(hornpipe_name)
    # 存在号角管的时候,更新号角管的位置和角度
    if (hornpipe_obj != None and hornpipe_sphere_obj != None and hornpipe_sphere_obj1 != None):
        cur_co = hornpipe_sphere_obj.location
        # 根据与管道末端控制点相连的控制点红球和号角管红球当前位置获取对应法线
        last_sphere_name = name + 'soundcanalsphere' + str(2)
        last_index = int(object_dic_cur[last_sphere_name])
        middle_index = last_index - 1  # 管道末端控制点相连的控制点红球索引比其小1
        middle_sphere_obj = None
        for key in object_dic_cur:
            key_obj = bpy.data.objects[key]
            key_index = int(object_dic_cur[key])
            if (key_index == middle_index):
                middle_sphere_obj = key_obj
                break
        middle_co = middle_sphere_obj.location
        normal = Vector(middle_co[0:3]) - Vector(cur_co[0:3])
        # 根据法线得到与模型的交点
        hit, loc, normal, index = cur_obj.ray_cast(cur_co, normal)
        # 将管道末端红球和其对应的管道控制点位置设置为交点位置,同步更新号角管的位置
        if (hit):
            # 更新管道末端控制点及对应红球的位置信息
            last_sphere_name = name + 'soundcanalsphere' + str(2)
            last_sphere_obj = bpy.data.objects[last_sphere_name]
            last_sphere_obj.location = loc
            step = soundcanal_hornpipe_offset_cur
            normal = Vector(middle_co[0:3]) - Vector(loc[0:3])
            offset_co = (loc[0] - normal.normalized()[0] * step, loc[1] - normal.normalized()[1] * step,
                         loc[2] - normal.normalized()[2] * step)
            # 管道末端长度随着offset偏移
            index = int(object_dic_cur[last_sphere_name])
            bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[0:3] = offset_co
            bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[3] = 1
            flag = save_soundcanal_info(offset_co)
            if flag:
                convert_soundcanal()
            # 更新号角管的位置并将其摆正对齐
            horn_fit_rotate(normal, offset_co)
            # 更新号角管红球位置
            step = 10
            hornpipe_point = (
            offset_co[0] - normal.normalized()[0] * step, offset_co[1] - normal.normalized()[1] * step,
            offset_co[2] - normal.normalized()[2] * step)
            hornpipe_sphere_obj.location = hornpipe_point
            hornpipe_sphere_obj1.location = hornpipe_point


def update_hornpipe_rotate_initial():
    '''
    使用鼠标三维旋转号角管的时候,需要更新管道控制点的位置随其旋转,在此之前做一些初始化的操作
    将圆球和红环平面隐藏,得到管道末端及其上一个控制点到号角管的距离
    '''
    name = bpy.context.scene.leftWindowObj
    global middle_dis
    global last_dis
    object_dic_cur = None
    if (name == "右耳"):
        object_dic_cur = object_dic
    elif (name == "左耳"):
        object_dic_cur = object_dicL
    # 找到与号角管相连的管道控制点a的上一个控制点b,记录二者之间的距离dis和此时的offset参数,更改offset的时候,更新dis,根据控制点b的位置更新号角管
    plane_name = name + 'HornpipePlane'
    plane_obj = bpy.data.objects.get(plane_name)
    plane_co = plane_obj.location
    last_sphere_name = name + 'soundcanalsphere' + str(2)
    last_sphere_obj = bpy.data.objects.get(last_sphere_name)
    last_co = last_sphere_obj.location
    last_index = int(object_dic_cur[last_sphere_name])
    middle_index = last_index - 1  # 管道末端控制点相连的控制点红球索引比其小1
    middle_sphere_obj = None
    for key in object_dic_cur:
        key_obj = bpy.data.objects[key]
        key_index = int(object_dic_cur[key])
        if (key_index == middle_index):
            middle_sphere_obj = key_obj
            break
    middle_co = middle_sphere_obj.location
    middle_dis = sqrt((plane_co[0] - middle_co[0]) ** 2 + (plane_co[1] - middle_co[1]) ** 2 + (
            plane_co[2] - middle_co[2]) ** 2)
    last_dis = sqrt((plane_co[0] - last_co[0]) ** 2 + (plane_co[1] - last_co[1]) ** 2 + (
            plane_co[2] - last_co[2]) ** 2)
    # 将管道上的所有圆球控制点隐藏
    for key in object_dic_cur:
        sphere_obj = bpy.data.objects.get(key)
        if (sphere_obj != None):
            sphere_obj.hide_set(True)
    hornpipe_sphere_name = name + 'soundcanalsphere' + str(100)  # 号角管控制圆球
    hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
    hornpipe_sphere_name1 = name + 'soundcanalsphere' + str(101)  # 号角管显示圆球
    hornpipe_sphere_obj1 = bpy.data.objects.get(hornpipe_sphere_name1)
    if (hornpipe_sphere_obj != None):
        hornpipe_sphere_obj.hide_set(True)
    if (hornpipe_sphere_obj1 != None):
        hornpipe_sphere_obj1.hide_set(True)
    # 将可能存在的管道圆球红环删除
    delete_sphere_snap_plane()

    curve_obj = bpy.data.objects[name + 'soundcanal']
    mesh_obj = bpy.data.objects[name + 'meshsoundcanal']
    curve_obj.hide_set(False)
    mesh_obj.hide_set(True)


def update_hornpipe_rotate():
    '''
    使用鼠标三维旋转号角管的时候,实时更新管道控制点的位置
    '''
    global middle_dis
    global last_dis
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    soundcanal_hornpipe_offset_cur = 0
    if (name == "右耳"):
        object_dic_cur = object_dic
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offset
    elif (name == "左耳"):
        object_dic_cur = object_dicL
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offsetL
    if (middle_dis != None and last_dis != None):
        # 根据号角管平面的位置和法线方向,得到管道控制点中与号角管相连的末端控制点及其上一个控制点
        plane_name = name + 'HornpipePlane'
        plane_obj = bpy.data.objects.get(plane_name)
        # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True, isolate_users=True)
        plane_co = plane_obj.location
        world_matrix = plane_obj.matrix_world
        plane_vert0 = world_matrix @ plane_obj.data.vertices[0].co
        plane_vert1 = world_matrix @ plane_obj.data.vertices[1].co
        plane_vert2 = world_matrix @ plane_obj.data.vertices[2].co
        point1 = mathutils.Vector((plane_vert0[0], plane_vert0[1], plane_vert0[2]))
        point2 = mathutils.Vector((plane_vert1[0], plane_vert1[1], plane_vert1[2]))
        point3 = mathutils.Vector((plane_vert2[0], plane_vert2[1], plane_vert2[2]))
        # 计算两个向量
        vector1 = point2 - point1
        vector2 = point3 - point1
        # 计算法向量
        plane_normal = vector1.cross(vector2)

        last_dis_offset = last_dis - soundcanal_hornpipe_offset_cur
        last_co = (
            plane_co[0] + plane_normal.normalized()[0] * last_dis_offset,
            plane_co[1] + plane_normal.normalized()[1] * last_dis_offset,
            plane_co[2] + plane_normal.normalized()[2] * last_dis_offset)
        middle_co = (plane_co[0] + plane_normal.normalized()[0] * middle_dis,
                     plane_co[1] + plane_normal.normalized()[1] * middle_dis,
                     plane_co[2] + plane_normal.normalized()[2] * middle_dis)

        last_sphere_name = name + 'soundcanalsphere' + str(2)
        last_sphere_obj = bpy.data.objects.get(last_sphere_name)
        last_sphere_obj.hide_set(False)
        middle_sphere_name = name + 'soundcanalsphere' + str(3)
        middle_sphere_obj = bpy.data.objects.get(middle_sphere_name)
        last_sphere_obj.location = last_co
        middle_sphere_obj.location = middle_co

        # 根据跟新后的控制点的位置,重新绘制管道
        last_sphere_name = name + 'soundcanalsphere' + str(2)
        last_index = int(object_dic_cur[last_sphere_name])
        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[last_index].co[0:3] = last_co
        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[last_index].co[3] = 1
        middle_index = last_index - 1
        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[middle_index].co[0:3] = middle_co
        bpy.data.objects[name + 'soundcanal'].data.splines[0].points[middle_index].co[3] = 1
        save_soundcanal_info(middle_co)
        # plane_obj = bpy.data.objects.get(name + 'HornpipePlane')
        # bpy.ops.object.select_all(action='DESELECT')
        # plane_obj.select_set(True)
        # bpy.context.view_layer.objects.active = plane_obj



def update_hornpipe_rotate_finish():
    '''
       使用鼠标三维旋转号角管的时候,需要更新管道控制点的位置随其旋转
       旋转操作完成之后,需要将三维旋转初始化时所做的操作还原
    '''
    global object_dic
    global object_dicL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    # 将管道上的所有圆球控制点显示出来
    name = bpy.context.scene.leftWindowObj
    soundcanal_hornpipe_offset_cur = 0
    object_dic_cur = None
    if (name == "右耳"):
        object_dic_cur = object_dic
        soundcanal_hornpipe_offset_cur = bpy.context.scene.chuanShenKongOffset
    elif (name == "左耳"):
        object_dic_cur = object_dicL
        soundcanal_hornpipe_offset_cur = bpy.context.scene.chuanShenKongOffset_L

    hornpipe_sphere_name = name + 'soundcanalsphere' + str(100)  # 号角管控制红球
    hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
    hornpipe_sphere_name1 = name + 'soundcanalsphere' + str(101)  # 号角管显示红球
    hornpipe_sphere_obj1 = bpy.data.objects.get(hornpipe_sphere_name1)
    for key in object_dic_cur:
        sphere_obj = bpy.data.objects.get(key)
        if (sphere_obj != None):
            sphere_obj.hide_set(False)
    if (hornpipe_sphere_obj != None):
        hornpipe_sphere_obj.hide_set(False)
    if (hornpipe_sphere_obj1 != None):
        hornpipe_sphere_obj1.hide_set(False)

    # 更新管道红球的位置,将红球位置同步更新到 旋转后得到的新管道的对应管道控制点的位置
    # 根据与管道末端控制点相连的控制点红球和管道末端控制点红球位置获取对应法线
    last_sphere_name = name + 'soundcanalsphere' + str(2)
    last_sphere_obj = bpy.data.objects.get(last_sphere_name)
    if (last_sphere_obj != None and hornpipe_sphere_obj != None and hornpipe_sphere_obj1 != None):
        last_co = last_sphere_obj.location
        last_index = int(object_dic_cur[last_sphere_name])
        middle_index = last_index - 1  # 管道末端控制点相连的控制点红球索引比其小1
        middle_sphere_obj = None
        for key in object_dic_cur:
            key_obj = bpy.data.objects[key]
            key_index = int(object_dic_cur[key])
            if (key_index == middle_index):
                middle_sphere_obj = key_obj
                break
        middle_co = middle_sphere_obj.location
        normal = Vector(middle_co[0:3]) - Vector(last_co[0:3])

        # 更新号角管控制红球的位置
        step = 10
        hornpipe_point = (last_co[0] - normal.normalized()[0] * step, last_co[1] - normal.normalized()[1] * step,
                          last_co[2] - normal.normalized()[2] * step)
        hornpipe_sphere_obj.location = hornpipe_point
        hornpipe_sphere_obj1.location = hornpipe_point

    # 更新号角管最后一个点的位置，以防切换到非三维旋转时号角管位置重新调整
    # cur_obj = bpy.data.objects[name]
    # hornpipe_name = name + 'Hornpipe'
    # hornpipe_obj = bpy.data.objects.get(hornpipe_name)
    # # 存在号角管的时候,更新号角管的位置和角度
    # if (hornpipe_obj != None and hornpipe_sphere_obj != None and hornpipe_sphere_obj1 != None):
    #     cur_co = hornpipe_sphere_obj.location
    #     # 根据与管道末端控制点相连的控制点红球和号角管红球当前位置获取对应法线
    #     last_sphere_name = name + 'soundcanalsphere' + str(2)
    #     last_index = int(object_dic_cur[last_sphere_name])
    #     middle_index = last_index - 1  # 管道末端控制点相连的控制点红球索引比其小1
    #     middle_sphere_obj = None
    #     for key in object_dic_cur:
    #         key_obj = bpy.data.objects[key]
    #         key_index = int(object_dic_cur[key])
    #         if (key_index == middle_index):
    #             middle_sphere_obj = key_obj
    #             break
    #     middle_co = middle_sphere_obj.location
    #     normal = Vector(middle_co[0:3]) - Vector(cur_co[0:3])
    #     # 根据法线得到与模型的交点
    #     hit, loc, normal, index = cur_obj.ray_cast(cur_co, normal)
    #     # 将管道末端红球和其对应的管道控制点位置设置为交点位置,同步更新号角管的位置
    #     if (hit):
    #         # 更新管道末端控制点及对应红球的位置信息
    #         last_sphere_name = name + 'soundcanalsphere' + str(2)
    #         last_sphere_obj = bpy.data.objects[last_sphere_name]
    #         last_sphere_obj.location = loc
    #         step = soundcanal_hornpipe_offset_cur
    #         normal = Vector(middle_co[0:3]) - Vector(loc[0:3])
    #         offset_co = (loc[0] - normal.normalized()[0] * step, loc[1] - normal.normalized()[1] * step,
    #                      loc[2] - normal.normalized()[2] * step)
    #         # 管道末端长度随着offset偏移
    #         index = int(object_dic_cur[last_sphere_name])
    #         bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[0:3] = offset_co
    #         bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[3] = 1
    #         flag = save_soundcanal_info(offset_co)
    #         if flag:
    #             convert_soundcanal()
    #
    #         # 更新号角管的位置并将其摆正对齐
    #         horn_fit_rotate(normal, offset_co)

    convert_soundcanal()
    curve_obj = bpy.data.objects[name + 'soundcanal']
    mesh_obj = bpy.data.objects[name + 'meshsoundcanal']
    curve_obj.hide_set(True)
    mesh_obj.hide_set(False)


def create_sphere_snap_plane(sphere_number):
    '''
        对于管道中间的圆球,激活后在红球位置location会创建一个与管道法线normal垂直的平面用于红球的吸附
    '''
    global object_dic
    global object_dicL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    if (name == "右耳"):
        object_dic_cur = object_dic
    elif (name == "左耳"):
        object_dic_cur = object_dicL
    sphere_name = name + 'soundcanalsphere' + str(sphere_number)
    cur_sphere_obj = bpy.data.objects.get(sphere_name)
    cur_obj = bpy.data.objects.get(name)
    if (cur_sphere_obj != None):
        # 先获取管道中与该圆球相连的上一个圆球和下一个圆球,进而得到二者构成的法线
        cur_index = int(object_dic_cur[sphere_name])
        previous_index = cur_index - 1
        next_index = cur_index + 1
        previous_sphere_obj = None
        next_sphere_obj = None
        for key in object_dic_cur:
            key_obj = bpy.data.objects[key]
            key_index = int(object_dic_cur[key])
            if (key_index == previous_index):
                previous_sphere_obj = key_obj
            elif (key_index == next_index):
                next_sphere_obj = key_obj
        if (previous_sphere_obj != None and next_sphere_obj != None):
            previous_co = previous_sphere_obj.location
            next_co = next_sphere_obj.location
            plane_normal = previous_co - next_co
            plane_co = cur_sphere_obj.location
            # 根据plane_normal和plane_co生成一个平面并将其摆正对齐
            bpy.ops.mesh.primitive_plane_add(size=50, enter_editmode=False, align='WORLD', location=(0, 0, 0),
                                             scale=(1, 1, 1))
            planename = name + "SoundCanalPlane"
            plane_obj = bpy.data.objects.get("Plane")
            plane_obj.name = planename
            if (name == "右耳"):
                moveToRight(plane_obj)
            elif (name == "左耳"):
                moveToLeft(plane_obj)
            empty = bpy.data.objects.new("CoordinateSystem", None)  # 新建一个空物体根据向量normal建立一个局部坐标系
            bpy.context.collection.objects.link(empty)
            empty.location = (0, 0, 0)
            rotation_matrix = plane_normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()  # 将法线作为局部坐标系的z轴
            empty.matrix_world = rotation_matrix
            empty_rotation_x = empty.rotation_euler[0]  # 记录该局部坐标系在全局坐标系中的角度并将该空物体删除
            empty_rotation_y = empty.rotation_euler[1]
            empty_rotation_z = empty.rotation_euler[2]
            bpy.data.objects.remove(empty, do_unlink=True)
            plane_obj.location = plane_co  # 将平面摆正对齐
            plane_obj.rotation_euler[0] = empty_rotation_x
            plane_obj.rotation_euler[1] = empty_rotation_y
            plane_obj.rotation_euler[2] = empty_rotation_z
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            # 为平面添加透明材质
            initialTransparency()
            plane_obj.data.materials.clear()
            plane_obj.data.materials.append(bpy.data.materials["Transparency"])
            # 将平面设置为激活物体,执行布尔交集操作将平面切割为符合的形状
            bpy.ops.object.select_all(action='DESELECT')
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers["Boolean"].operation = 'INTERSECT'
            bpy.context.object.modifiers["Boolean"].solver = 'EXACT'
            bpy.context.object.modifiers["Boolean"].object = cur_obj
            bpy.ops.object.modifier_apply(modifier="Boolean")

            # 分离出选中的平面
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(plane_obj.data)
            select_vert = [v for v in bm.verts if v.select]
            if len(select_vert) > 0:
                bpy.ops.mesh.separate(type='SELECTED')
                for o in bpy.context.selected_objects:
                    if o.select_get() and o.name != planename:
                        temp_plane_obj = o
                bpy.ops.object.mode_set(mode='OBJECT')
                # 删除plane_obj
                bpy.data.objects.remove(plane_obj, do_unlink=True)
                # 将temp_plane_obj设置为plane_obj
                bpy.ops.object.select_all(action='DESELECT')
                plane_obj = temp_plane_obj
                plane_obj.name = planename
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj

            # 根据平面边界生成红环
            draw_plane_border()
            # 将激活物体重新设置为红球
            bpy.ops.object.select_all(action='DESELECT')
            cur_sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_sphere_obj


def draw_plane_border():
    '''
    根据平面边界顶点绘制出一圈红环边界
    '''
    name = bpy.context.scene.leftWindowObj
    planename = name + "SoundCanalPlane"
    plane_obj = bpy.data.objects.get(planename)
    if (plane_obj != None):
        # 根据平面复制出一份物体用于生成边界红环
        plane_border_curve = plane_obj.copy()
        plane_border_curve.data = plane_obj.data.copy()
        plane_border_curve.animation_data_clear()
        plane_border_curve.name = name + "SoundCanalPlaneBorderCurveObject"
        bpy.context.collection.objects.link(plane_border_curve)
        if (name == "右耳"):
            moveToRight(plane_border_curve)
        elif (name == "左耳"):
            moveToLeft(plane_border_curve)
        bpy.ops.object.select_all(action='DESELECT')  # 将边界红环激活
        plane_border_curve.select_set(True)
        bpy.context.view_layer.objects.active = plane_border_curve
        bpy.ops.object.mode_set(mode='EDIT')  # 将平面选中并删除其中的面,只保存边界线将其转化为曲线
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target='CURVE')
        bpy.context.object.data.bevel_depth = 0.02  # 为圆环上色
        soundcanal_plane_border_red_material = bpy.data.materials.new(name="SoundCanalPlaneBorderRed")
        soundcanal_plane_border_red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
        plane_border_curve.data.materials.append(soundcanal_plane_border_red_material)
        bpy.ops.object.select_all(action='DESELECT')  # 将平面圆环边界设置为不可选中
        plane_border_curve.hide_select = True


def delete_sphere_snap_plane():
    '''
    删除激活管道中间圆球时生成的用于吸附的平面
    '''
    global prev_sphere_number_plane
    global prev_sphere_number_planeL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        prev_sphere_number_plane = 0
    elif (name == "左耳"):
        prev_sphere_number_planeL = 0
    planename = name + "SoundCanalPlane"
    plane_obj = bpy.data.objects.get(planename)
    plane_border_name = name + "SoundCanalPlaneBorderCurveObject"
    plane_border_obj = bpy.data.objects.get(plane_border_name)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    if (plane_border_obj != None):
        bpy.data.objects.remove(plane_border_obj, do_unlink=True)


def save_soundcanal_info(co):
    '''
    将管道中所有控制点的信息保存到列表中
    '''
    global soundcanal_data
    global soundcanal_dataL
    cox = round(co[0], 3)
    coy = round(co[1], 3)
    coz = round(co[2], 3)
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if (cox not in soundcanal_data) or (coy not in soundcanal_data) or (coz not in soundcanal_data):
            for object in bpy.data.objects:
                if object.name == name + 'soundcanal':
                    soundcanal_data = []
                    curve_data = object.data
                    for point in curve_data.splines[0].points:
                        soundcanal_data.append(round(point.co[0], 3))
                        soundcanal_data.append(round(point.co[1], 3))
                        soundcanal_data.append(round(point.co[2], 3))
            return True
        return False
    elif name == '左耳':
        if (cox not in soundcanal_dataL) or (coy not in soundcanal_dataL) or (coz not in soundcanal_dataL):
            for object in bpy.data.objects:
                if object.name == name + 'soundcanal':
                    soundcanal_dataL = []
                    curve_data = object.data
                    for point in curve_data.splines[0].points:
                        soundcanal_dataL.append(round(point.co[0], 3))
                        soundcanal_dataL.append(round(point.co[1], 3))
                        soundcanal_dataL.append(round(point.co[2], 3))
            return True
        return False
    return False


def initial_soundcanal():
    # 初始化
    global object_dic
    global object_dicL
    global soundcanal_data
    global soundcanal_dataL
    global soundcanal_finish
    global soundcanal_finishL
    global soundcanal_shape
    global soundcanal_shapeL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    global prev_sphere_number_plane
    global prev_sphere_number_planeL
    global is_on_rotate
    global is_on_rotateL
    object_dic_cur = None
    soundcanal_data_cur = None
    soundcanal_enum_cur = None
    soundcanal_hornpipe_offset_cur = 0
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        soundcanal_finish = False
        object_dic_cur = object_dic
        soundcanal_data_cur = soundcanal_data
        soundcanal_enum_cur = soundcanal_shape
        bpy.context.scene.soundcancalShapeEnum = soundcanal_shape
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offset
        bpy.context.scene.chuanShenKongOffset = soundcanal_hornpipe_offset
        prev_sphere_number_plane = 0
    elif name == '左耳':
        soundcanal_finishL = False
        object_dic_cur = object_dicL
        soundcanal_data_cur = soundcanal_dataL
        soundcanal_enum_cur = soundcanal_shapeL
        bpy.context.scene.soundcancalShapeEnum_L = soundcanal_shapeL
        soundcanal_hornpipe_offset_cur = soundcanal_hornpipe_offsetL
        bpy.context.scene.chuanShenKongOffset_L = soundcanal_hornpipe_offsetL
        prev_sphere_number_planeL = 0

    # 主窗口物体
    if len(object_dic_cur) >= 2:  # 存在已保存的圆球位置,复原原有的管道
        initialTransparency()
        newColor('red', 1, 0, 0, 1, 0.8)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)
        obj = new_curve(name + 'soundcanal')
        obj.data.materials.append(bpy.data.materials["grey"])

        # 添加一个曲线样条
        spline = obj.data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points.add(count=len(object_dic_cur) - 1)
        for i, point in enumerate(spline.points):
            point.co = (soundcanal_data_cur[3 * i], soundcanal_data_cur[3 * i + 1], soundcanal_data_cur[3 * i + 2], 1)

        # 生成圆球
        for key in object_dic_cur:
            mesh = bpy.data.meshes.new(name + "soundcanalsphere")
            obj = bpy.data.objects.new(key, mesh)
            bpy.context.collection.objects.link(obj)
            if name == '右耳':
                moveToRight(obj)
            elif name == '左耳':
                moveToLeft(obj)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(obj.data)
            # 设置圆球的参数
            radius = 0.4  # 半径
            segments = 32  # 分段数
            # 在指定位置生成圆球
            bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
            bmesh.update_edit_mesh(obj.data)  # 更新网格数据
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.data.materials.append(bpy.data.materials['red'])
            obj.location = bpy.data.objects[name + 'soundcanal'].data.splines[0].points[object_dic_cur[key]].co[
                           0:3]  # 指定的位置坐标

        if (soundcanal_enum_cur == 'OP2'):
            # 将管道末端控制点隐藏
            last_sphere_name = name + 'soundcanalsphere' + '2'
            last_sphere_obj = bpy.data.objects.get(last_sphere_name)
            last_sphere_obj.hide_set(True)
            # 在管道末端初始化添加一个号角管
            initial_hornpipe()
            # 根据面板offset参数设置号角管偏移位置
            update_hornpipe_offset_location_normal()

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["Transparency"])
        bpy.data.objects[name].hide_select = True
        convert_soundcanal()
        bpy.data.objects[name + 'soundcanal'].hide_set(True)
        save_soundcanal_info([0, 0, 0])
        bpy.data.objects[name + 'soundcanal'].hide_set(True)

    elif len(object_dic_cur) == 1:  # 只点击了一次
        newColor('red', 1, 0, 0, 1, 0.8)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        obj = new_curve(name + 'soundcanal')
        obj.data.materials.append(bpy.data.materials["grey"])
        # 添加一个曲线样条
        spline = obj.data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points[0].co[0:3] = soundcanal_data_cur[0:3]
        spline.points[0].co[3] = 1
        # spline.use_cyclic_u = True
        # spline.use_endpoint_u = True

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        mesh = bpy.data.meshes.new(name + "soundcanalsphere")
        obj = bpy.data.objects.new(name + "soundcanalsphere1", mesh)
        bpy.context.collection.objects.link(obj)
        if name == '右耳':
            moveToRight(obj)
        elif name == '左耳':
            moveToLeft(obj)

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(state=True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        # 设置圆球的参数
        radius = 0.4  # 半径
        segments = 32  # 分段数

        # 在指定位置生成圆球
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                                  radius=radius * 2)
        bmesh.update_edit_mesh(obj.data)  # 更新网格数据

        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.materials.append(bpy.data.materials['red'])
        obj.location = soundcanal_data_cur[0:3]  # 指定的位置坐标

    else:  # 不存在已保存的圆球位置
        pass

    spherename = name + "SoundcanalSphere"
    sphere_obj = bpy.data.objects.get(spherename)
    if (sphere_obj != None and name == '右耳' and is_on_rotate):
        sphere_obj.select_set(True)
    if (sphere_obj != None and name == '左耳' and is_on_rotateL):
        sphere_obj.select_set(True)

    bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')


def submit_soundcanal():
    # 应用布尔修改器，删除多余的物体
    global object_dic
    global object_dicL
    global soundcanal_finish
    global soundcanal_finishL
    global soundcanal_shape
    global soundcanal_shapeL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        if len(object_dic) > 0 and soundcanal_finish == False:
            adjustpoint()
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            # 存在号角管时
            soundcanal_shape = bpy.context.scene.soundcancalShapeEnum
            soundcanal_hornpipe_offset = bpy.context.scene.chuanShenKongOffset
            if (soundcanal_shape == 'OP2'):
                bool_modifier = bpy.context.active_object.modifiers.new(
                    name="Soundcanal Boolean Modifier", type='BOOLEAN')
                bool_modifier.operation = 'DIFFERENCE'
                bool_modifier.object = bpy.data.objects[name + 'Hornpipe']
                bpy.ops.object.modifier_apply(modifier="Soundcanal Boolean Modifier", single_user=True)
            bool_modifier = bpy.context.active_object.modifiers.new(
                name="Soundcanal Boolean Modifier", type='BOOLEAN')
            bool_modifier.operation = 'DIFFERENCE'
            bool_modifier.object = bpy.data.objects[name + 'meshsoundcanal']
            bpy.ops.object.modifier_apply(modifier="Soundcanal Boolean Modifier", single_user=True)
            need_to_delete_model_name_list = [name + 'meshsoundcanal', name + 'soundcanal', name + 'HornpipePlane',
                                              name + 'Hornpipe', name + 'soundcanalsphere' + '100',
                                              name + 'soundcanalsphere' + '101',
                                              name + 'SoundCanalPlaneBorderCurveObject', name + 'SoundCanalPlane',
                                              name + 'SoundcanalSphere']
            for key in object_dic:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            bpy.context.active_object.data.materials.clear()
            bpy.context.active_object.data.materials.append(bpy.data.materials['Yellow'])
            utils_re_color(name, (1, 0.319, 0.133))
            bpy.context.active_object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 0.9
            bpy.data.objects[name].hide_select = False
    elif name == '左耳':
        if len(object_dicL) > 0 and soundcanal_finishL == False:
            adjustpoint()
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            # 存在号角管时
            soundcanal_shapeL = bpy.context.scene.soundcancalShapeEnum_L
            soundcanal_hornpipe_offsetL = bpy.context.scene.chuanShenKongOffset_L
            if (soundcanal_shapeL == 'OP2'):
                bool_modifier = bpy.context.active_object.modifiers.new(
                    name="Soundcanal Boolean Modifier", type='BOOLEAN')
                bool_modifier.operation = 'DIFFERENCE'
                bool_modifier.object = bpy.data.objects[name + 'Hornpipe']
                bpy.ops.object.modifier_apply(modifier="Soundcanal Boolean Modifier", single_user=True)
            bool_modifier = bpy.context.active_object.modifiers.new(
                name="Soundcanal Boolean Modifier", type='BOOLEAN')
            bool_modifier.operation = 'DIFFERENCE'
            bool_modifier.object = bpy.data.objects[name + 'meshsoundcanal']
            bpy.ops.object.modifier_apply(modifier="Soundcanal Boolean Modifier", single_user=True)
            need_to_delete_model_name_list = [name + 'meshsoundcanal', name + 'soundcanal', name + 'HornpipePlane',
                                              name + 'Hornpipe', name + 'soundcanalsphere' + '100',
                                              name + 'soundcanalsphere' + '101',
                                              name + 'SoundCanalPlaneBorderCurveObject', name + 'SoundCanalPlane',
                                              name + 'SoundcanalSphere']
            for key in object_dicL:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            bpy.context.active_object.data.materials.clear()
            bpy.context.active_object.data.materials.append(bpy.data.materials['Yellow'])
            utils_re_color(name, (1, 0.319, 0.133))
            bpy.context.active_object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 0.9
            bpy.data.objects[name].hide_select = False


def adjustpoint():
    '''
    让管道两端(第一个点和最后一个点)向外移动一些,防止管道布尔切割失败
    '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    curve_object = bpy.data.objects[name + 'soundcanal']
    curve_data = curve_object.data
    last_index = len(curve_data.splines[0].points) - 1
    first_point = curve_data.splines[0].points[0]
    last_point = curve_data.splines[0].points[last_index]
    step = 5
    normal = Vector(first_point.co[0:3]) - Vector(curve_data.splines[0].points[1].co[0:3])
    first_point.co = (
    first_point.co[0] + normal.normalized()[0] * step, first_point.co[1] + normal.normalized()[1] * step,
    first_point.co[2] + normal.normalized()[2] * step, 1)
    normal = Vector(last_point.co[0:3]) - Vector(curve_data.splines[0].points[last_index - 1].co[0:3])
    last_point.co = (last_point.co[0] + normal.normalized()[0] * step, last_point.co[1] + normal.normalized()[1] * step,
                     last_point.co[2] + normal.normalized()[2] * step, 1)
    convert_soundcanal()


def checkposition():
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    object = bpy.data.objects[name + 'meshsoundcanal']
    target_object = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(object.data)  # 获取网格数据
    bm.verts.ensure_lookup_table()
    color_lay = bm.verts.layers.float_color["Color"]
    for vert in bm.verts:
        _, co, normal, _ = target_object.closest_point_on_mesh(vert.co)
        flag = (vert.co - co).dot(normal)
        colorvert = vert[color_lay]
        if (flag > 0):
            colorvert.x = 0.8
            colorvert.y = 0.8
            colorvert.z = 0.8
        else:
            colorvert.x = 1
            colorvert.y = 0
            colorvert.z = 0
    bm.to_mesh(object.data)
    bm.free()


def frontToSoundCanal():
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SoundCanalReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SoundCanalReset"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)

    initial_soundcanal()


def frontFromSoundCanal():
    # 主窗口物体
    global object_dic
    global object_dicL
    global soundcanal_shape
    global soundcanal_shapeL
    global soundcanal_hornpipe_offset
    global soundcanal_hornpipe_offsetL
    name = bpy.context.scene.leftWindowObj
    save_soundcanal_info([0, 0, 0])
    need_to_delete_model_name_list = [name + 'meshsoundcanal', name + 'soundcanal', name + 'HornpipePlane',
                                      name + 'Hornpipe', name + 'soundcanalsphere' + '100',
                                      name + 'soundcanalsphere' + '101', name + 'SoundCanalPlaneBorderCurveObject',
                                      name + 'SoundCanalPlane', name + 'SoundcanalSphere']
    if name == '右耳':
        soundcanal_shape = bpy.context.scene.soundcancalShapeEnum
        soundcanal_hornpipe_offset = bpy.context.scene.chuanShenKongOffset
        for key in object_dic:
            need_to_delete_model_name_list.append(key)
    elif name == '左耳':
        soundcanal_shapeL = bpy.context.scene.soundcancalShapeEnum_L
        soundcanal_hornpipe_offsetL = bpy.context.scene.chuanShenKongOffset_L
        for key in object_dicL:
            need_to_delete_model_name_list.append(key)
    delete_useless_object(need_to_delete_model_name_list)
    obj = bpy.data.objects[name]
    resetname = name + "SoundCanalReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SoundCanalReset" or selected_obj.name == name + "SoundCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

    set_is_on_rotate(False)


def backToSoundCanal():
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

    # 后面模块切换到传声孔的时候,判断是否存在用于铸造法的 软耳膜附件Casting  和  用于字体附件的 LabelPlaneForCasting 若存在则将其删除
    handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (label_obj != None):
        bpy.data.objects.remove(label_obj, do_unlink=True)

    # 将后续模块中的reset和last都删除
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

    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    exist_SoundCanalReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SoundCanalReset"):
            exist_SoundCanalReset = True
    if (exist_SoundCanalReset):
        obj = bpy.data.objects[name]
        resetname = name + "SoundCanalReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        initial_soundcanal()
    else:
        obj = bpy.data.objects[name]
        lastname = name + "MouldLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
        elif (bpy.data.objects.get(name + "QieGeLast") != None):
            lastname = name + "QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
        elif (bpy.data.objects.get(name + "LocalThickLast") != None):
            lastname = name + "LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
        else:
            lastname = name + "DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
        if name == '右耳':
            moveToRight(ori_obj)
        elif name == '左耳':
            moveToLeft(ori_obj)
        ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        initial_soundcanal()


def backFromSoundCanal():
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    save_soundcanal_info([0, 0, 0])
    submit_soundcanal()
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SoundCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    obj.hide_select = False
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SoundCanalLast"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

    set_is_on_rotate(False)


class addsoundcanal_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addsoundcanal2"
    bl_label = "传声孔添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作"
    )
    bl_icon = "ops.curves.sculpt_smooth"
    bl_widget = None
    bl_keymap = (
        ("object.addsoundcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class addsoundcanal_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addsoundcanal3"
    bl_label = "传声孔对圆球操作"
    bl_description = (
        "传声孔对圆球移动、双击操作"
    )
    bl_icon = "ops.curves.sculpt_pinch"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, None),
        ("object.deletesoundcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class finishsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishsoundcanal"
    bl_label = "传声孔完成"
    bl_description = (
        "完成管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_puff"
    bl_widget = None
    bl_keymap = (
        ("object.finishsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetsoundcanal"
    bl_label = "传声孔重置"
    bl_description = (
        "重置管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_slide"
    bl_widget = None
    bl_keymap = (
        ("object.resetsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class rotatesoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.soundcanal_rotate"
    bl_label = "号角管旋转"
    bl_description = (
        "添加号角管后,调用号角管三维旋转鼠标行为"
    )
    bl_icon = "brush.paint_texture.masklort"
    bl_widget = None
    bl_keymap = (
        ("object.soundcanalrotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrorsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrorsoundcanal"
    bl_label = "传声孔镜像"
    bl_description = (
        "点击镜像传声孔"
    )
    bl_icon = "ops.curve.pen"
    bl_widget = None
    bl_keymap = (
        ("object.mirrorsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


_classes = [
    TEST_OT_addsoundcanal,
    TEST_OT_deletesoundcanal,
    TEST_OT_soundcanalqiehuan,
    TEST_OT_finishsoundcanal,
    TEST_OT_resetsoundcanal,
    TEST_OT_soundcanalrotate
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_tool(resetsoundcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishsoundcanal_MyTool, separator=True, group=False,
                            after={resetsoundcanal_MyTool.bl_idname})
    bpy.utils.register_tool(rotatesoundcanal_MyTool, separator=True, group=False,
                            after={finishsoundcanal_MyTool.bl_idname})
    bpy.utils.register_tool(mirrorsoundcanal_MyTool, separator=True, group=False,
                            after={rotatesoundcanal_MyTool.bl_idname})

    bpy.utils.register_tool(addsoundcanal_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(addsoundcanal_MyTool3, separator=True, group=False)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)

    bpy.utils.unregister_tool(resetsoundcanal_MyTool)
    bpy.utils.unregister_tool(finishsoundcanal_MyTool)
    bpy.utils.unregister_tool(rotatesoundcanal_MyTool)
    bpy.utils.unregister_tool(mirrorsoundcanal_MyTool)

    bpy.utils.unregister_tool(addsoundcanal_MyTool2)
    bpy.utils.unregister_tool(addsoundcanal_MyTool3)