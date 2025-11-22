import bpy
import bmesh
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
from math import sqrt
from .tool import newShader, moveToRight, moveToLeft, utils_re_color, delete_useless_object, newColor, \
    getOverride, apply_material, transform_normal
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running,\
    get_mirror_context, set_mirror_context, get_process_var_list
from .register_tool import unregister_tools
from .global_manager import global_manager
from .back_and_forward import record_state, backup_state, forward_state
import re
import time


prev_on_sphere = False
prev_on_sphereL = False
prev_on_object = False
prev_on_objectL = False
prev_on_ventcanal = False
prev_on_ventcanalL = False
number = 0                       # 记录管道控制点点的个数
numberL = 0
object_dic = {}                  # 记录当前圆球以及对应控制点
object_dicL = {}
ventcanal_data = []              # 记录当前控制点的坐标
ventcanal_dataL = []
ventcanal_finish = False
ventcanal_finishL = False

ventcanal_convert = False            #某些情况下实时更新mesh可能会中断鼠标行为
ventcanal_convertL = False

mouse_index = 0                   #添加传声孔之后,切换其存在的鼠标行为,记录当前在切换到了哪种鼠标行为
mouse_indexL = 0

prev_sphere_number_plane = 0      #记录鼠标在管道中间的红球间切换时,上次位于的红球,主要用于控制点平面的切换
prev_sphere_number_planeL = 0

is_mouseSwitch_modal_start = False         #在启动下一个modal前必须将上一个modal关闭,防止modal开启过多过于卡顿
is_mouseSwitch_modal_startL = False

add_or_delete = False             # 执行添加或删除红球的过程中,暂停qiehuan modal的检测执行
add_or_deleteL = False
vent_canal_press = False

def register_ventcanal_globals():
    global number, numberL
    global object_dic, object_dicL
    global ventcanal_data, ventcanal_dataL
    global ventcanal_finish, ventcanal_finishL
    global_manager.register("number", number)
    global_manager.register("numberL", numberL)
    global_manager.register("object_dic", object_dic)
    global_manager.register("object_dicL", object_dicL)
    global_manager.register("ventcanal_data", ventcanal_data)
    global_manager.register("ventcanal_dataL", ventcanal_dataL)
    global_manager.register("ventcanal_finish", ventcanal_finish)
    global_manager.register("ventcanal_finishL", ventcanal_finishL)


def vent_canal_backup():
    backup_state()
    recover_vent_canal()
        

def vent_canal_forward():
    forward_state()
    recover_vent_canal()


def recover_vent_canal():
    name = bpy.context.scene.leftWindowObj
    canal_obj = bpy.data.objects[name + "ventcanal"]
    for modifier in canal_obj.modifiers:
        if modifier.type == 'HOOK':
            canal_obj.modifiers.remove(modifier)
    # 为管道控制红球添加位置约束,只能在红环平面上移动
    if (name == "右耳"):
        for obj in bpy.data.objects:
            soundCanalPlanePattern = r'右耳VentCanalPlane'
            soundCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
            if re.match(soundCanalPlanePattern, obj.name) and not re.match(soundCanalPlaneBorderPattern, obj.name):
                sphere_number = int(obj.name.replace('右耳VentCanalPlane', ''))
                sphere_name = '右耳ventcanalsphere' + str(sphere_number)
                cur_sphere_obj = bpy.data.objects.get(sphere_name)
                if (cur_sphere_obj != None):
                    limit_location_constraint = None
                    for constraint in cur_sphere_obj.constraints:
                        if (constraint.type == 'LIMIT_LOCATION'):
                            limit_location_constraint = constraint
                            break
                    if (limit_location_constraint == None):
                        limit_location_constraint = cur_sphere_obj.constraints.new(type='LIMIT_LOCATION')
                    limit_location_constraint.use_min_z = True
                    limit_location_constraint.min_z = 0
                    limit_location_constraint.use_max_z = True
                    limit_location_constraint.max_z = 0
                    limit_location_constraint.owner_space = 'CUSTOM'
                    limit_location_constraint.space_object = obj
    elif (name == "左耳"):
        for obj in bpy.data.objects:
            soundCanalPlanePattern = r'左耳VentCanalPlane'
            soundCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
            if re.match(soundCanalPlanePattern, obj.name) and not re.match(soundCanalPlaneBorderPattern, obj.name):
                sphere_number = int(obj.name.replace('左耳VentCanalPlane', ''))
                sphere_name = '左耳ventcanalsphere' + str(sphere_number)
                cur_sphere_obj = bpy.data.objects.get(sphere_name)
                if (cur_sphere_obj != None):
                    limit_location_constraint = None
                    for constraint in cur_sphere_obj.constraints:
                        if (constraint.type == 'LIMIT_LOCATION'):
                            limit_location_constraint = constraint
                            break
                    if (limit_location_constraint == None):
                        limit_location_constraint = cur_sphere_obj.constraints.new(type='LIMIT_LOCATION')
                    limit_location_constraint.use_min_z = True
                    limit_location_constraint.min_z = 0
                    limit_location_constraint.use_max_z = True
                    limit_location_constraint.max_z = 0
                    limit_location_constraint.owner_space = 'CUSTOM'
                    limit_location_constraint.space_object = obj

    # 重新将曲线控制点勾挂到管道控制红球上
    hook_curve_point_to_sphere()


def initialPlaneTransparency():
    mat = newColor("PlaneTransparency", 1, 0.319, 0.133, 1, 0.4)  # 创建材质
    mat.use_backface_culling = False


def get_region_and_space(context, area_type, region_type, space_type):
    ''' 获得当前区域的信息 '''
    region = None
    area = None
    space = None

    # 获取指定区域的信息
    for a in context.screen.areas:
        if a.type == area_type:
            area = a
            break
    else:
        return (None, None)
    # 获取指定区域的信息
    for r in area.regions:
        if r.type == region_type:
            region = r
            break
    # 获取指定区域的信息
    for s in area.spaces:
        if s.type == space_type:
            space = s
            break

    return (region, space)


def on_which_shpere(context, event):
    '''
    返回值与 判断鼠标在哪个物体上的先后顺序有关
    判断鼠标在哪个圆球上,不在圆球上则返回0
    返回值为201的时候表示鼠标在管道上方末端的透明控制圆球上, 返回值为202的时候表示鼠标在管道下方末端的透明控制圆球上
    返回值3-number的时候表示鼠标在管道中间的控制红球上
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
    # 鼠标是否在管道两端透明控制圆球上
    sphere_name1 = name + 'ventcanalsphere' + '201'  # 传声孔管道红球ventcanalsphere1 对应的 透明控制圆球
    sphere_obj1 = bpy.data.objects.get(sphere_name1)
    if (sphere_obj1 != None):
        mwi = sphere_obj1.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if sphere_obj1.type == 'MESH':
            if (sphere_obj1.mode == 'OBJECT'):
                mesh = sphere_obj1.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 201
    sphere_name2 = name + 'ventcanalsphere' + '202'  # 传声孔管道红球ventcanalsphere2 对应的 透明控制圆球
    sphere_obj2 = bpy.data.objects.get(sphere_name2)
    if (sphere_obj2 != None):
        mwi = sphere_obj2.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if sphere_obj2.type == 'MESH':
            if (sphere_obj2.mode == 'OBJECT'):
                mesh = sphere_obj2.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 202
    # 鼠标是否在管道的红球上
    for key in object_dic_cur:
        active_obj = bpy.data.objects[key]
        object_index = int(key.replace(name + 'ventcanalsphere', ''))
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


def is_changed_ventcanal(context, event):
    '''
     创建管道后鼠标位置的判断
     鼠标在管道模型和其他区域之间切换的判断
     '''
    # 主窗口物体
    name = bpy.context.scene.leftWindowObj
    curr_on_ventcanal = is_mouse_on_object(name + 'meshventcanal', context, event)  # 当前鼠标在哪个物体上
    global prev_on_ventcanal  # 之前鼠标在那个物体上
    global prev_on_ventcanalL
    if name == '右耳':
        if (curr_on_ventcanal != prev_on_ventcanal):
            prev_on_ventcanal = curr_on_ventcanal
            return True
        else:
            return False
    elif name == '左耳':
        if (curr_on_ventcanal != prev_on_ventcanalL):
            prev_on_ventcanalL = curr_on_ventcanal
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
    if(curr_on_sphere != 0):
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
    # 获取当前选择的曲线对象
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects[name + 'ventcanal']
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
    name = bpy.context.scene.leftWindowObj
    source_curve = bpy.data.objects[name + 'ventcanal']
    target_curve = new_curve(name + 'meshventcanal')
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


def convert_ventcanal():
    name = bpy.context.scene.leftWindowObj
    if (bpy.data.objects.get(name + 'meshventcanal')):
        bpy.data.objects.remove(bpy.data.objects[name + 'meshventcanal'], do_unlink=True)  # 删除原有网格
    # copy_curve()
    # duplicate_obj = bpy.data.objects[name + 'meshventcanal']
    # bpy.context.view_layer.objects.active = duplicate_obj
    # bpy.ops.object.select_all(action='DESELECT')
    # duplicate_obj.select_set(state=True)
    # 根据源曲线复制生成一份用于转化为网格的曲线
    source_curve = bpy.data.objects[name + 'ventcanal']
    target_curve = source_curve.copy()
    target_curve.data = source_curve.data.copy()
    target_curve.animation_data_clear()
    target_curve.name = name + 'meshventcanal'
    bpy.context.collection.objects.link(target_curve)
    if name == '右耳':
        moveToRight(target_curve)
    elif name == '左耳':
        moveToLeft(target_curve)
    # # 将用于转化为网格的曲线激活并应用其修改器
    bpy.ops.object.select_all(action='DESELECT')
    target_curve.hide_set(False)
    target_curve.hide_select = False
    target_curve.select_set(state=True)
    bpy.context.view_layer.objects.active = target_curve
    # for modifier in target_curve.modifiers:
    #     bpy.ops.object.modifier_apply(modifier=modifier.name, single_user=True)
    bevel_depth = None
    if name == '右耳':
        bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing / 2
    elif name == '左耳':
        bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing_L / 2
    bpy.context.active_object.data.bevel_depth = bevel_depth  # 设置曲线倒角深度
    bpy.context.active_object.data.bevel_resolution = 8  # 管道分辨率
    bpy.context.active_object.data.use_fill_caps = True  # 封盖
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    target_curve.hide_select = True
    target_curve.data.materials.clear()
    target_curve.data.materials.append(bpy.data.materials["grey"])


def add_sphere(co, index):
    '''
    在指定位置生成圆球用于控制管道曲线的移动
    :param co:指定的坐标
    :param index:指定要钩挂的控制点的下标
    '''
    global number
    global numberL
    mesh = None
    name1  = None

    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        number += 1
        mesh = bpy.data.meshes.new(name + "ventcanalsphere")
        name1 = name + 'ventcanalsphere' + str(number)
    elif (name == "左耳"):
        numberL += 1
        mesh = bpy.data.meshes.new(name + "ventcanalsphere")
        name1 = name + 'ventcanalsphere' + str(numberL)

    obj = bpy.data.objects.new(name1, mesh)
    bpy.context.collection.objects.link(obj)
    if name == '右耳':
        moveToRight(obj)
    elif name == '左耳':
        moveToLeft(obj)
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # 设置圆球的参数
    radius = 0.4  # 半径
    segments = 32  # 分段数
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
    bm.to_mesh(me)
    bm.free()
    obj.data.materials.append(bpy.data.materials['red'])

    # 设置圆球的位置
    obj.location = co  # 指定的位置坐标
    hooktoobject(index)  # 绑定到指定下标




def mouse_switch(sphere_number):
    '''
    鼠标位于不同的物体上时,切换到不同的传声孔鼠标行为
    '''
    global mouse_index
    global mouse_indexL
    name = bpy.context.scene.leftWindowObj
    if(name == '右耳'):
        # sphere_number = on_which_shpere(context,event)
        if(sphere_number == 0 and mouse_index != 1):
            mouse_index = 1
            # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
        elif(sphere_number != 0 and mouse_index != 2):
            mouse_index = 2
            #管道末端控制圆球索引为201与202
            if (sphere_number == 1):
                sphere_number = 201
            elif (sphere_number == 2):
                sphere_number = 202
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            sphere_name = name + 'ventcanalsphere' + str(sphere_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal3")
    elif(name == '左耳'):
        # sphere_number = on_which_shpere(context, event)
        if (sphere_number == 0 and mouse_indexL != 1):
            mouse_indexL = 1
            # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
        elif (sphere_number != 0 and mouse_indexL != 2):
            mouse_indexL = 2
            # 管道末端控制圆球索引为201与202
            if (sphere_number == 1):
                sphere_number = 201
            elif (sphere_number == 2):
                sphere_number = 202
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            sphere_name = name + 'ventcanalsphere' + str(sphere_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal3")


def plane_switch(sphere_number):
    '''
    鼠标在管道中的圆球中切换时,更新生成平面
    '''
    global prev_sphere_number_plane
    global prev_sphere_number_planeL
    name = bpy.context.scene.leftWindowObj
    planename = name + "VentCanalPlane" + str(sphere_number)
    plane_obj = bpy.data.objects.get(planename)
    plane_border_name = name + "VentCanalPlaneBorderCurveObject" + str(sphere_number)
    plane_border_obj = bpy.data.objects.get(plane_border_name)
    # 若位于管道两端的圆球上,则需要吸附在模型上
    if sphere_number == 201 or sphere_number == 202 or sphere_number == 1 or sphere_number == 2:
        bpy.context.scene.tool_settings.use_snap = True
        # # 左右耳模型是不可选中的,为了让其吸附在模型上,需要将该吸附参数设置为False
        # bpy.context.scene.tool_settings.use_snap_selectable = False
    #鼠标位于管道中间的圆球上且在不同的圆球上切换时,删除原有的平面并生成新的平面
    if(plane_obj != None and plane_border_obj != None and sphere_number != 0 and sphere_number != 1 and sphere_number != 2 and sphere_number != 201 and sphere_number != 202):
        bpy.context.scene.tool_settings.use_snap = False
        # # 左右耳模型是不可选中的,平面是可选中的,设置该参数使其只能吸附在平面上
        # bpy.context.scene.tool_settings.use_snap_selectable = True
        if (name == "右耳"):
            if (sphere_number != prev_sphere_number_plane):
                for obj in bpy.data.objects:
                    ventCanalPlanePattern = r'右耳VentCanalPlane'
                    ventCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
                    if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                        obj.hide_set(True)
                plane_obj.hide_set(False)
                plane_border_obj.hide_set(False)
                # delete_sphere_snap_plane()
                # create_sphere_snap_plane(sphere_number)
            prev_sphere_number_plane = sphere_number
        elif (name == "左耳"):
            if (sphere_number != prev_sphere_number_planeL):
                for obj in bpy.data.objects:
                    ventCanalPlanePattern = r'左耳VentCanalPlane'
                    ventCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
                    if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                        obj.hide_set(True)
                plane_obj.hide_set(False)
                plane_border_obj.hide_set(False)
                # delete_sphere_snap_plane()
                # create_sphere_snap_plane(sphere_number)
            prev_sphere_number_planeL = sphere_number




def create_sphere_snap_plane(sphere_number):
    '''
        对于管道中间的圆球,激活后在红球位置location会创建一个与管道法线normal垂直的平面用于红球的吸附
    '''
    global object_dic
    global object_dicL

    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    if (name == "右耳"):
        object_dic_cur = object_dic
    elif (name == "左耳"):
        object_dic_cur = object_dicL
    sphere_name = name + 'ventcanalsphere' + str(sphere_number)
    cur_sphere_obj = bpy.data.objects.get(sphere_name)
    cur_obj = bpy.data.objects.get(name)
    if (cur_sphere_obj != None and sphere_number != 0 and sphere_number != 1 and sphere_number != 2):
        #先获取管道中与该圆球相连的上一个圆球和下一个圆球,进而得到二者构成的法线
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
        if(previous_sphere_obj != None and next_sphere_obj != None):
            # 先将其他平面和边界隐藏
            if (name == "右耳"):
                for obj in bpy.data.objects:
                    ventCanalPlanePattern = r'右耳VentCanalPlane'
                    ventCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
                    if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                        obj.hide_set(True)
            elif (name == "左耳"):
                for obj in bpy.data.objects:
                    ventCanalPlanePattern = r'左耳VentCanalPlane'
                    ventCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
                    if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                        obj.hide_set(True)
            # 生成新的平面和边界之前,先将可能存在的平面和边界删除
            planename = name + "VentCanalPlane" + str(sphere_number)
            plane_obj = bpy.data.objects.get(planename)
            planebordername = name + "VentCanalPlaneBorderCurveObject" + str(sphere_number)
            plane_border_obj = bpy.data.objects.get(planebordername)
            if (plane_obj != None):
                bpy.data.objects.remove(plane_obj, do_unlink=True)
            if (plane_border_obj != None):
                bpy.data.objects.remove(plane_border_obj, do_unlink=True)
            # 生成新的平面与边界
            previous_co = previous_sphere_obj.location
            next_co = next_sphere_obj.location
            plane_normal = previous_co - next_co
            plane_co = cur_sphere_obj.location
            #根据plane_normal和plane_co生成一个平面并将其摆正对齐
            bpy.ops.mesh.primitive_plane_add(size = 50, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            planename = name + "VentCanalPlane" + str(sphere_number)
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
            empty_rotation_x = empty.rotation_euler[0]                                   # 记录该局部坐标系在全局坐标系中的角度并将该空物体删除
            empty_rotation_y = empty.rotation_euler[1]
            empty_rotation_z = empty.rotation_euler[2]
            bpy.data.objects.remove(empty, do_unlink=True)
            plane_obj.location = plane_co                                                 # 将平面摆正对齐
            plane_obj.rotation_euler[0] = empty_rotation_x
            plane_obj.rotation_euler[1] = empty_rotation_y
            plane_obj.rotation_euler[2] = empty_rotation_z
            # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            #为平面添加透明材质
            initialPlaneTransparency()
            plane_obj.data.materials.clear()
            plane_obj.data.materials.append(bpy.data.materials["PlaneTransparency"])
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
                draw_plane_border(sphere_number)
            bpy.ops.object.mode_set(mode='OBJECT')

            # 为对应的红球添加位置约束,限定红球只能在平面上移动
            limit_location_constraint = None
            for constraint in cur_sphere_obj.constraints:
                if (constraint.type == 'LIMIT_LOCATION'):
                    limit_location_constraint = constraint
                    break
            if (limit_location_constraint == None):
                limit_location_constraint = cur_sphere_obj.constraints.new(type='LIMIT_LOCATION')
            limit_location_constraint.use_min_z = True
            limit_location_constraint.min_z = 0
            limit_location_constraint.use_max_z = True
            limit_location_constraint.max_z = 0
            limit_location_constraint.owner_space = 'CUSTOM'
            limit_location_constraint.space_object = plane_obj

            # 将平面位置锁定,防止该平面被拖动到该平面之外
            plane_obj.lock_location[0] = True
            plane_obj.lock_location[1] = True
            plane_obj.lock_location[2] = True
            #将激活物体重新设置为红球
            bpy.ops.object.select_all(action='DESELECT')
            cur_sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_sphere_obj

def draw_plane_border(sphere_number):
    '''
    根据平面边界顶点绘制出一圈红环边界
    '''
    name = bpy.context.scene.leftWindowObj
    planename = name + "VentCanalPlane" + str(sphere_number)
    plane_obj = bpy.data.objects.get(planename)
    if(plane_obj != None):
        #根据平面复制出一份物体用于生成边界红环
        plane_border_curve = plane_obj.copy()
        plane_border_curve.data = plane_obj.data.copy()
        plane_border_curve.animation_data_clear()
        plane_border_curve.name = name + "VentCanalPlaneBorderCurveObject" + str(sphere_number)
        bpy.context.collection.objects.link(plane_border_curve)
        if (name == "右耳"):
            moveToRight(plane_border_curve)
        elif (name == "左耳"):
            moveToLeft(plane_border_curve)
        bpy.ops.object.select_all(action='DESELECT')                    #将边界红环激活
        plane_border_curve.select_set(True)
        bpy.context.view_layer.objects.active = plane_border_curve
        if (len(plane_border_curve.data.vertices) > 0):  # 若平面布尔出现问题导致没有顶点,则将其转化为曲线并设置粗细为0.02的时候可能会弹出错误
            bpy.ops.object.mode_set(mode='EDIT')  # 将平面选中并删除其中的面,只保存边界线将其转化为曲线
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.convert(target='CURVE')
            plane_border_curve.data.bevel_depth = 0.02
        ventcanal_plane_border_red_material = newColor("VentCanalPlaneBorderRed", 1, 0, 0, 0, 1)
        plane_border_curve.data.materials.append(ventcanal_plane_border_red_material)
        bpy.ops.object.select_all(action='DESELECT')                    #将平面圆环边界设置为不可选中
        plane_border_curve.hide_select = True


def delete_sphere_snap_plane(sphere_number):
    '''
    删除激活管道中间圆球时生成的用于吸附的平面
    '''
    global prev_sphere_number_plane
    global prev_sphere_number_planeL
    name = bpy.context.scene.leftWindowObj
    if(name == "右耳"):
        prev_sphere_number_plane = 0
    elif(name == "左耳"):
        prev_sphere_number_planeL = 0
    if (sphere_number != 0 and sphere_number != 1 and sphere_number != 2):
        planename = name + "VentCanalPlane" + str(sphere_number)
        plane_obj = bpy.data.objects.get(planename)
        plane_border_name = name + "VentCanalPlaneBorderCurveObject" + str(sphere_number)
        plane_border_obj = bpy.data.objects.get(plane_border_name)
        if(plane_obj != None):
            bpy.data.objects.remove(plane_obj, do_unlink=True)
        if(plane_border_obj != None):
            bpy.data.objects.remove(plane_border_obj, do_unlink=True)



def hook_curve_point_to_sphere():
    '''
    将曲线对应的控制点绑定到管道控制红球上,通过控制红球进而控制曲线形状,进而控制管道形状
    '''
    global object_dic
    global object_dicL
    global ventcanal_convert
    global ventcanal_convertL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        object_dic_cur = object_dic
        ventcanal_convert_cur = ventcanal_convert
    elif (name == "左耳"):
        object_dic_cur = object_dicL
        ventcanal_convert_cur = ventcanal_convertL
    curve_obj = bpy.data.objects.get(name + 'ventcanal')
    mesh_curve_obj = bpy.data.objects.get(name + 'meshventcanal')
    if(curve_obj != None):
        # 将所有的曲线控制点重新勾挂到对应的红球上
        for key in object_dic_cur:
            sphere_name = key
            index = int(object_dic_cur[sphere_name])
            sphere_obj = bpy.data.objects.get(sphere_name)
            if(sphere_obj != None):
                #物体没有被隐藏时才将其勾挂
                if (not sphere_obj.hide_get()):
                    for point in curve_obj.data.splines[0].points:
                        point.select = False
                    curve_obj.data.splines[0].points[index].select = True
                    bpy.ops.object.select_all(action='DESELECT')
                    curve_obj.hide_set(False)
                    curve_obj.select_set(True)
                    sphere_obj.select_set(True)
                    bpy.context.view_layer.objects.active = curve_obj
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.object.hook_add_selob(use_bone=False)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    if(mesh_curve_obj != None):
                        if(ventcanal_convert_cur):
                            curve_obj.hide_set(False)
                            mesh_curve_obj.hide_set(True)
                        else:
                            curve_obj.hide_set(True)
                            mesh_curve_obj.hide_set(False)


def apply_hook_modifies():
    '''
    将曲线控制点的勾挂修改器全部应用,防止读取曲线控制点位置信息出现偏差
    '''
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects.get(name + 'ventcanal')
    if (curve_obj != None):
        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.hide_set(False)
        curve_obj.select_set(True)
        bpy.context.view_layer.objects.active = curve_obj
        # 应用曲线上的所有勾挂修改器
        for modifier in curve_obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name, single_user=True)



class TEST_OT_addventcanal(bpy.types.Operator):
    bl_idname = "object.addventcanal"
    bl_label = "addventcanal"
    bl_description = "双击添加管道控制点"

    def addsphere(self, context, event):

        global number
        global numberL
        global add_or_delete
        global add_or_deleteL
        name = bpy.context.scene.leftWindowObj
        mesh_name = name + 'meshventcanal'
        number_cur = None
        if (name == "右耳"):
            number_cur = number
            add_or_delete = True
        elif (name == "左耳"):
            number_cur = numberL
            add_or_deleteL = True

        # 将曲线控制点的勾挂修改器全部应用
        apply_hook_modifies()

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
                # bpy.data.objects[name].data.materials.clear()  # 清除材质
                # bpy.data.objects[name].data.materials.append(bpy.data.materials["Transparency"])
                if name == '右耳':
                    bpy.context.scene.transparent3EnumR = 'OP3'
                    # bpy.context.scene.transparentper3EnumR = '0.6'
                elif name == '左耳':
                    bpy.context.scene.transparent3EnumL = 'OP3'
                    # bpy.context.scene.transparentper3EnumR = '0.6'
                bpy.ops.object.select_all(action='DESELECT')
                # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
                # 为新生成的红球控制点添加平面
                create_sphere_snap_plane(3)
                convert_ventcanal()
                save_ventcanal_info([0, 0, 0])

        else:  # 如果number大于1，双击添加控制点
            co = cal_co(mesh_name, context, event)
            if co != -1:
                min_index, secondmin_index, insert_index = select_nearest_point(co)
                add_canal(min_index, secondmin_index, co, insert_index)

                # 重新更新管道中间圆球生成的平面
                # delete_sphere_snap_plane()
                create_sphere_snap_plane(number_cur + 1)
                convert_ventcanal()
                save_ventcanal_info([0, 0, 0])

        # 重新将曲线控制点勾挂到管道控制红球上
        hook_curve_point_to_sphere()
        record_state()

        if name == '右耳':
            add_or_delete = False
        elif name == '左耳':
            add_or_deleteL = False

    def invoke(self, context, event):
        self.addsphere(context, event)
        return {'FINISHED'}


class TEST_OT_deleteventcanal(bpy.types.Operator):
    bl_idname = "object.deleteventcanal"
    bl_label = "deleteventcanal"
    bl_description = "双击删除管道控制点"

    def deletesphere(self, context, event):

        global object_dic
        global object_dicL
        global add_or_delete
        global add_or_deleteL
        sphere_number = on_which_shpere(context, event)
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            add_or_delete = True
        elif name == '左耳':
            add_or_deleteL = True
        if sphere_number == 0 or sphere_number == 1 or sphere_number == 2 or sphere_number == 201 or sphere_number == 202:
            pass

        else:

            # 将曲线控制点的勾挂修改器全部应用
            apply_hook_modifies()

            if (name == "右耳"):
                sphere_name = name + 'ventcanalsphere' + str(sphere_number)
                index = object_dic[sphere_name]
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[name + 'ventcanal'].hide_set(False)
                bpy.context.view_layer.objects.active = bpy.data.objects[name + 'ventcanal']
                bpy.data.objects[name + 'ventcanal'].select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式删除点
                bpy.ops.curve.select_all(action='DESELECT')
                bpy.data.objects[name + 'ventcanal'].data.splines[0].points[index].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.data.objects[name + 'ventcanal'].select_set(False)
                bpy.data.objects[name + 'ventcanal'].hide_set(True)

                # 更新
                bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
                for key in object_dic:
                    if object_dic[key] > index:
                        object_dic[key] -= 1
                del object_dic[sphere_name]
                # 删除可能存在的圆球平面
                delete_sphere_snap_plane(sphere_number)
                global number
                count = number - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'ventcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'ventcanalsphere' + str(sphere_number + i)
                        object_dic.update({replace_name: object_dic.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                # 更新该红球的后续红球的红球平面及边界名称(红球平面与边界和红球一一对应)
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'VentCanalPlane' + str(sphere_number + i + 1)
                        replace_name = name + 'VentCanalPlane' + str(sphere_number + i)
                        bpy.data.objects[old_name].name = replace_name
                        old_name = name + 'VentCanalPlaneBorderCurveObject' + str(sphere_number + i + 1)
                        replace_name = name + 'VentCanalPlaneBorderCurveObject' + str(sphere_number + i)
                        bpy.data.objects[old_name].name = replace_name
                number -= 1
                convert_ventcanal()
                save_ventcanal_info([0, 0, 0])
            elif (name == "左耳"):
                sphere_name = name + 'ventcanalsphere' + str(sphere_number)
                index = object_dicL[sphere_name]
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[name + 'ventcanal'].hide_set(False)
                bpy.context.view_layer.objects.active = bpy.data.objects[name + 'ventcanal']
                bpy.data.objects[name + 'ventcanal'].select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式删除点
                bpy.ops.curve.select_all(action='DESELECT')
                bpy.data.objects[name + 'ventcanal'].data.splines[0].points[index].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.data.objects[name + 'ventcanal'].select_set(False)
                bpy.data.objects[name + 'ventcanal'].hide_set(True)

                # 更新
                bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
                for key in object_dicL:
                    if object_dicL[key] > index:
                        object_dicL[key] -= 1
                del object_dicL[sphere_name]
                # 删除可能存在的圆球平面
                delete_sphere_snap_plane(sphere_number)
                global numberL
                count = numberL - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'ventcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'ventcanalsphere' + str(sphere_number + i)
                        object_dicL.update({replace_name: object_dicL.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                # 更新该红球的后续红球的红球平面及边界名称(红球平面与边界和红球一一对应)
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'VentCanalPlane' + str(sphere_number + i + 1)
                        replace_name = name + 'VentCanalPlane' + str(sphere_number + i)
                        bpy.data.objects[old_name].name = replace_name
                        old_name = name + 'VentCanalPlaneBorderCurveObject' + str(sphere_number + i + 1)
                        replace_name = name + 'VentCanalPlaneBorderCurveObject' + str(sphere_number + i)
                        bpy.data.objects[old_name].name = replace_name
                numberL -= 1
                convert_ventcanal()
                save_ventcanal_info([0, 0, 0])

            # 重新将曲线控制点勾挂到管道控制红球上
            hook_curve_point_to_sphere()
            record_state()

        if name == '右耳':
            add_or_delete = False
        elif name == '左耳':
            add_or_deleteL = False

    def invoke(self, context, event):
        self.deletesphere(context, event)
        return {'FINISHED'}


class TEST_OT_ventcanalqiehuan(bpy.types.Operator):
    bl_idname = "object.ventcanalqiehuan"
    bl_label = "ventcanalqiehuan"
    bl_description = "鼠标行为切换"

    __left_mouse_down = False
    __timer = None              #添加定时器

    update_sphere_number = 0    #记录管道正在更新时的类型  更新管道两端,更新管道中间点,更新号角管位置

    def invoke(self, context, event):  # 初始化
        # initialTransparency()
        newColor('red', 1, 0, 0, 0, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)  # 不透明材质
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)  # 透明材质
        if not TEST_OT_ventcanalqiehuan.__timer:
            TEST_OT_ventcanalqiehuan.__timer = context.window_manager.event_timer_add(0.1, window=context.window)

        bpy.context.scene.var = 26
        global is_mouseSwitch_modal_start
        global is_mouseSwitch_modal_startL
        if not is_mouseSwitch_modal_start:
            is_mouseSwitch_modal_start = True
            context.window_manager.modal_handler_add(self)
            print('ventcanalqiehuan invoke')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global object_dic
        global object_dicL
        global ventcanal_convert
        global ventcanal_convertL
        global add_or_delete
        global add_or_deleteL
        global is_mouseSwitch_modal_start
        global is_mouseSwitch_modal_startL
        global mouse_index
        global mouse_indexL
        global vent_canal_press

        op_cls = TEST_OT_ventcanalqiehuan
        name = bpy.context.scene.leftWindowObj
        object_dic_cur = None
        add_or_delete_cur = False

        mouse_x = event.mouse_x
        mouse_y = event.mouse_y

        if get_mirror_context():
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print('ventcanalqiehuan finish')
            is_mouseSwitch_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        if bpy.context.scene.var == 26:
            if event.type == 'LEFTMOUSE':  # 监听左键
                if event.value == 'PRESS':  # 按下
                    op_cls.__left_mouse_down = True
                return {'PASS_THROUGH'}

            elif event.type == 'MOUSEMOVE':
                if op_cls.__left_mouse_down:
                    op_cls.__left_mouse_down = False
                return {'PASS_THROUGH'}

            if (name == "右耳"):
                object_dic_cur = object_dic
                add_or_delete_cur = add_or_delete
                ventcanal_convert_cur = ventcanal_convert
            elif (name == "左耳"):
                object_dic_cur = object_dicL
                add_or_delete_cur = add_or_deleteL
                ventcanal_convert_cur = ventcanal_convertL

            if(not add_or_delete_cur):
                # 若没有将曲线管道转化为网格管道,则根据曲线管道复制出一份转化为网格管道并显示(防止convert_ventcanal执行过程中切换模式中断鼠标行为)
                if (name == "右耳"):
                    if (ventcanal_convert and not op_cls.__left_mouse_down):
                        op_cls.update_sphere_number = 0
                        ventcanal_convert = False
                        ventcanal_convert_cur = ventcanal_convert
                        # 将曲线控制点的勾挂修改器全部应用
                        apply_hook_modifies()
                        # 保存曲线控制点信息
                        save_ventcanal_info([0, 0, 0])
                        # 根据曲线管道更新mesh管道信息
                        convert_ventcanal()
                        # 将曲线管道显示出来,mesh管道隐藏
                        bpy.data.objects[name + 'ventcanal'].hide_set(True)
                        bpy.data.objects[name + 'meshventcanal'].hide_set(False)
                        # 重新将曲线控制点勾挂到管道控制红球上
                        hook_curve_point_to_sphere()
                elif (name == "左耳"):
                    if (ventcanal_convertL and not op_cls.__left_mouse_down):
                        op_cls.update_sphere_number = 0
                        ventcanal_convertL = False
                        ventcanal_convert_cur = ventcanal_convertL
                        # 将曲线控制点的勾挂修改器全部应用
                        apply_hook_modifies()
                        # 保存曲线控制点信息
                        save_ventcanal_info([0, 0, 0])
                        # 根据曲线管道更新mesh管道信息
                        convert_ventcanal()
                        # 将曲线管道显示出来,mesh管道隐藏
                        bpy.data.objects[name + 'ventcanal'].hide_set(True)
                        bpy.data.objects[name + 'meshventcanal'].hide_set(False)
                        # 重新将曲线控制点勾挂到管道控制红球上
                        hook_curve_point_to_sphere()


                if len(object_dic_cur) < 2:
                    if cal_co(name, context, event) != -1 and is_changed(context, event) == True:
                        bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
                    elif cal_co(name, context, event) == -1 and is_changed(context, event) == True:
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = bpy.data.objects[name]
                        bpy.data.objects[name].select_set(True)

                elif len(object_dic_cur) >= 2:

                    # 判断是否位于红球上,存在则返回其索引,不存在则返回0
                    sphere_number = on_which_shpere(context, event)

                    # 根据鼠标位于模型的种类,切换到不同的鼠标行为
                    if (not op_cls.__left_mouse_down):
                        mouse_switch(sphere_number)
                        # 生成管道中间红球对应的平面
                        plane_switch(sphere_number)
                        if vent_canal_press:
                            vent_canal_press = False
                            record_state()

                        # 鼠标位于管道或圆球上的时候,改变管道的材质,将其亮度调高
                        if cal_co(name + 'meshventcanal', context, event) == -1:
                                bpy.data.objects[name + 'meshventcanal'].data.materials.clear()
                                bpy.data.objects[name + 'meshventcanal'].data.materials.append(bpy.data.materials["grey"])
                        elif cal_co(name + 'meshventcanal', context, event) != -1:
                                bpy.data.objects[name + 'meshventcanal'].data.materials.clear()
                                bpy.data.objects[name + 'meshventcanal'].data.materials.append(bpy.data.materials["grey2"])
                    
                    if (name == "右耳"):
                        mouse_index_cur = mouse_index
                    elif (name == "左耳"):
                        mouse_index_cur = mouse_indexL
                    
                    if mouse_index_cur == 2 and op_cls.__left_mouse_down:
                        vent_canal_press = True

                    # 激活相关鼠标行为开始相关更新后,便不再根据sphere_number判断,而是使用保持更新
                    if (op_cls.__left_mouse_down and ventcanal_convert_cur and op_cls.update_sphere_number != 0):
                        if (op_cls.update_sphere_number == 201 or op_cls.update_sphere_number == 202):
                            loc = cal_co(name, context, event)
                            sphere_number = op_cls.update_sphere_number
                            sphere_number1 = op_cls.update_sphere_number
                            if (sphere_number == 201):
                                sphere_number1 = 1
                            elif (sphere_number == 202):
                                sphere_number1 = 2
                            # 管道末端透明控制圆球
                            sphere_name = name + 'ventcanalsphere' + str(sphere_number)
                            obj = bpy.data.objects[sphere_name]
                            # 管道末端显示红球
                            sphere_name1 = name + 'ventcanalsphere' + str(sphere_number1)
                            obj1 = bpy.data.objects[sphere_name1]
                            if (loc != -1 and op_cls.__left_mouse_down):
                                obj1.location = loc
                        return {'PASS_THROUGH'}
                    # 各种更新的入口,根据sphere_number判断激活何种类型的更新(管道两端更新,管道中间点更新,号角管更新)
                    # 设置op_cls.update_sphere_number值用于进入保持更新部分时进行何种类型的保持更新
                    # 因为进入更新后,若依然根据sphere_number保持更新,可能存在更新过程中将鼠标移动到其他物体上sphere_                                obj.location = obj1.locationnumber改变而切换到了其他类型的更新
                    else:
                        # 若鼠标不在圆球上
                        if sphere_number == 0:
                            return {'PASS_THROUGH'}
                        # 对于管道两端的控制点,操控调整的时候,限制其不能拖出模型之外
                        elif (sphere_number == 201 or sphere_number == 202 or sphere_number == 1 or sphere_number == 2):
                            op_cls.update_sphere_number = sphere_number
                            active_object = bpy.context.active_object
                            if (active_object != None):
                                active_object_name = active_object.name
                                if (active_object_name in [name + 'ventcanalsphere201', name + 'ventcanalsphere202']):
                                    active_object_index = int(active_object_name.replace(name + 'ventcanalsphere', ''))
                                    loc = cal_co(name, context, event)
                                    sphere_number = active_object_index
                                    sphere_number1 = active_object_index
                                    # 鼠标左键按下的时候,虽然不会发生鼠标行为的切换,但当我们操作管道末端透明控制红球的时候,若将鼠标同时移动到另外一端的透明控制红球的时候,
                                    # 会将该透明圆球吸附到鼠标位置上,等于同时操控了两个圆球,为了避免这种现象,我们使用当前激活物体来限制确认操作的圆球物体,并非单纯根据鼠标在哪个物体上
                                    if (active_object_index == 201):
                                        sphere_number1 = 1
                                    elif (active_object_index == 202):
                                        sphere_number1 = 2
                                    # 管道末端透明控制圆球
                                    sphere_name = name + 'ventcanalsphere' + str(sphere_number)
                                    obj = bpy.data.objects[sphere_name]
                                    # 管道末端显示红球
                                    sphere_name1 = name + 'ventcanalsphere' + str(sphere_number1)
                                    obj1 = bpy.data.objects[sphere_name1]
                                    obj.location = obj1.location
                                    if (loc != -1 and op_cls.__left_mouse_down):
                                        obj1.location = loc
                                        # index = int(object_dic_cur[sphere_name1])
                                        # bpy.data.objects[name + 'ventcanal'].data.splines[0].points[index].co[0:3] = obj1.location
                                        # bpy.data.objects[name + 'ventcanal'].data.splines[0].points[index].co[3] = 1
                                        # 操控管道两端控制点期间,为了不影响鼠标操作,不实时的将曲线转化为网格(转化曲线函数会切换模式,影响鼠标行为);将曲线管道显示出来,mesh管道隐藏
                                        if (name == "右耳"):
                                            if (not ventcanal_convert):
                                                ventcanal_convert = True
                                                bpy.data.objects[name + 'ventcanal'].hide_set(False)
                                                bpy.data.objects[name + 'meshventcanal'].hide_set(True)
                                        elif (name == "左耳"):
                                            if (not ventcanal_convertL):
                                                ventcanal_convertL = True
                                                bpy.data.objects[name + 'ventcanal'].hide_set(False)
                                                bpy.data.objects[name + 'meshventcanal'].hide_set(True)
                            return {'PASS_THROUGH'}
                        # 鼠标位于其他控制圆球上的时候,管道控制点随着圆球位置的拖动改变而更新
                        else:
                            op_cls.update_sphere_number = sphere_number
                            sphere_name = name + 'ventcanalsphere' + str(sphere_number)
                            index = int(object_dic_cur[sphere_name])
                            if(index < len(bpy.data.objects[name + 'ventcanal'].data.splines[0].points) and op_cls.__left_mouse_down):
                                if (name == "右耳"):
                                    if (not ventcanal_convert):
                                        ventcanal_convert = True
                                        bpy.data.objects[name + 'ventcanal'].hide_set(False)
                                        bpy.data.objects[name + 'meshventcanal'].hide_set(True)
                                elif (name == "左耳"):
                                    if (not ventcanal_convertL):
                                        ventcanal_convertL = True
                                        bpy.data.objects[name + 'ventcanal'].hide_set(False)
                                        bpy.data.objects[name + 'meshventcanal'].hide_set(True)
                        return {'PASS_THROUGH'}

            return {'PASS_THROUGH'}

        # 模式切换，结束modal
        else:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(TEST_OT_ventcanalqiehuan.__timer)
                op_cls.__timer = None
            # if (name == "右耳"):
            #     is_mouseSwitch_modal_start = False
            # elif (name == "左耳"):
            #     is_mouseSwitch_modal_startL = False
            is_mouseSwitch_modal_start = False
            print('ventcanalqiehuan finish')
            return {'FINISHED'}


class TEST_OT_finishventcanal(bpy.types.Operator):
    bl_idname = "object.finishventcanal"
    bl_label = "完成操作"
    bl_description = "点击按钮完成管道制作"

    def invoke(self, context, event):
        bpy.context.scene.var = 27
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        submit_ventcanal()
        global ventcanal_finish
        global ventcanal_finishL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            ventcanal_finish = True
        elif (name == "左耳"):
            ventcanal_finishL = True

        if not bpy.context.scene.pressfinish:
            unregister_tools()
            bpy.context.scene.pressfinish = True



class TEST_OT_resetventcanal(bpy.types.Operator):
    bl_idname = "object.resetventcanal"
    bl_label = "重置操作"
    bl_description = "点击按钮重置管道制作"

    def invoke(self, context, event):
        bpy.context.scene.var = 28
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        # 删除多余的物体
        global object_dic
        global object_dicL
        global ventcanal_finish
        global ventcanal_finishL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            if not ventcanal_finish:
                need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                                  name + 'ventcanalsphere' + '201', name + 'ventcanalsphere' + '202']
                # 删除红球平面与平面边界
                for obj in bpy.data.objects:
                    ventCanalPlanePattern = r'右耳VentCanalPlane'
                    ventCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
                    if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                        bpy.data.objects.remove(obj, do_unlink=True)
                for key in object_dic:
                    bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
                delete_useless_object(need_to_delete_model_name_list)
                object_dic.clear()
                # 将VentCanalReset复制并替代当前操作模型
                oriname = bpy.context.scene.leftWindowObj
                ori_obj = bpy.data.objects.get(oriname)
                copyname = oriname + "VentCanalReset"
                copy_obj = bpy.data.objects.get(copyname)
                if (ori_obj != None and copy_obj != None):
                    bpy.data.objects.remove(ori_obj, do_unlink=True)
                    duplicate_obj = copy_obj.copy()
                    duplicate_obj.data = copy_obj.data.copy()
                    duplicate_obj.animation_data_clear()
                    duplicate_obj.name = oriname
                    bpy.context.collection.objects.link(duplicate_obj)
                    if oriname == '右耳':
                        moveToRight(duplicate_obj)
                    elif oriname == '左耳':
                        moveToLeft(duplicate_obj)
                global number
                global prev_sphere_number_plane
                number = 0
                prev_sphere_number_plane = 0
                bpy.context.scene.transparent3EnumR = 'OP1'
                record_state()
                # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        elif (name == "左耳"):
            if not ventcanal_finishL:
                need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                                  name + 'ventcanalsphere' + '201', name + 'ventcanalsphere' + '202']
                # 删除红球平面与平面边界
                for obj in bpy.data.objects:
                    ventCanalPlanePattern = r'左耳VentCanalPlane'
                    ventCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
                    if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                        bpy.data.objects.remove(obj, do_unlink=True)
                for key in object_dicL:
                    bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
                delete_useless_object(need_to_delete_model_name_list)
                object_dicL.clear()
                # 将VentCanalReset复制并替代当前操作模型
                oriname = bpy.context.scene.leftWindowObj
                ori_obj = bpy.data.objects.get(oriname)
                copyname = oriname + "VentCanalReset"
                copy_obj = bpy.data.objects.get(copyname)
                if (ori_obj != None and copy_obj != None):
                    bpy.data.objects.remove(ori_obj, do_unlink=True)
                    duplicate_obj = copy_obj.copy()
                    duplicate_obj.data = copy_obj.data.copy()
                    duplicate_obj.animation_data_clear()
                    duplicate_obj.name = oriname
                    bpy.context.collection.objects.link(duplicate_obj)
                    if oriname == '右耳':
                        moveToRight(duplicate_obj)
                    elif oriname == '左耳':
                        moveToLeft(duplicate_obj)
                global numberL
                global prev_sphere_number_planeL
                numberL = 0
                prev_sphere_number_planeL = 0
                bpy.context.scene.transparent3EnumL = 'OP1'
                record_state()
                # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}


        return {'FINISHED'}


    def modal(self, context, event):
        global is_mouseSwitch_modal_start
        global is_mouseSwitch_modal_startL
        # name = bpy.context.scene.leftWindowObj
        # if (name == '右耳'):
        #     if(not is_mouseSwitch_modal_start):
        #         is_mouseSwitch_modal_start = True
        #         bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
        #         return {'FINISHED'}
        # elif (name == '左耳'):
        #     if (not is_mouseSwitch_modal_startL):
        #         is_mouseSwitch_modal_startL = True
        #         bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
        #         return {'FINISHED'}
        if (not is_mouseSwitch_modal_start):
            # is_mouseSwitch_modal_start = True
            bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
            return {'FINISHED'}

        return {'PASS_THROUGH'}


class TEST_OT_mirrorventcanal(bpy.types.Operator):
    bl_idname = 'object.mirrorventcanal'
    bl_label = '通气孔镜像'

    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        global object_dic, object_dicL
        global ventcanal_dataL, ventcanal_data
        global number, numberL
        global ventcanal_finish, ventcanal_finishL

        left_obj = bpy.data.objects.get(context.scene.leftWindowObj)
        right_obj = bpy.data.objects.get(context.scene.rightWindowObj)

        # 只操作一个耳朵时，不执行镜像
        if left_obj == None or right_obj == None:
            return {'FINISHED'}

        tar_obj_name = bpy.context.scene.leftWindowObj
        tar_obj = bpy.data.objects[tar_obj_name]

        workspace = context.window.workspace.name

        if tar_obj_name == '左耳':
            ventcanal_data_cur = ventcanal_data
            ventcanal_finish_cur = ventcanal_finishL
        elif tar_obj_name == '右耳':
            ventcanal_data_cur = ventcanal_dataL
            ventcanal_finish_cur = ventcanal_finish

        # 只在双窗口下执行镜像
        # if workspace == '布局.001':
        if ventcanal_data_cur and not ventcanal_finish_cur:
            if tar_obj_name == '左耳':
                # ori_spheres = [obj for obj in bpy.context.scene.objects if
                #                obj.name.startswith('右耳ventcanalsphere') and not (
                #                            obj.name.endswith('100') or obj.name.endswith('101') or obj.name.endswith('201') or obj.name.endswith('202'))]
                new_spheres = [obj for obj in bpy.context.scene.objects if obj.name.startswith('左耳ventcanalsphere')]

                tar_ventcanal_data = ventcanal_dataL
                ori_ventcanal_data = ventcanal_data

                tar_object_dic = object_dicL
                ori_object_dic = object_dic

            else:
                # ori_spheres = [obj for obj in bpy.context.scene.objects if
                #                obj.name.startswith('左耳ventcanalsphere') and not (
                #                            obj.name.endswith('100') or obj.name.endswith('101') or obj.name.endswith('201') or obj.name.endswith('202'))]
                new_spheres = [obj for obj in bpy.context.scene.objects if obj.name.startswith('右耳ventcanalsphere')]

                tar_ventcanal_data = ventcanal_data
                ori_ventcanal_data = ventcanal_dataL

                tar_object_dic = object_dic
                ori_object_dic = object_dicL

            # 删除原有的所有圆球，清空曲线控制点坐标信息和字典
            for obj in new_spheres:
                bpy.data.objects.remove(obj, do_unlink=True)
            tar_ventcanal_data.clear()
            tar_object_dic.clear()
            # 删除原有曲线及其网格
            for obj in bpy.data.objects:
                if obj.name == tar_obj_name + "ventcanal":
                    bpy.data.objects.remove(obj, do_unlink=True)
                elif obj.name == tar_obj_name + "meshventcanal":
                    bpy.data.objects.remove(obj, do_unlink=True)

            # # 镜像创建各个圆球
            # if len(new_spheres) == 0:
            #     i = 1
            #     for obj in ori_spheres:
            #         ori_obj_name = obj.name
            #         # 获取原始对象
            #         ori_obj = bpy.data.objects.get(ori_obj_name)
            #         new_obj_data = ori_obj.data.copy()
            #
            #         new_name = ''
            #         if tar_obj_name == '左耳':
            #             new_name = f"左耳ventcanalsphere{i}"
            #         else:
            #             new_name = f"右耳ventcanalsphere{i}"
            #         i += 1
            #
            #         new_obj = bpy.data.objects.new(name=new_name, object_data=new_obj_data)
            #
            #         # 设置新对象的位置为原始对象的位置
            #         new_obj.location = ori_obj.location.copy()
            #         # 将新对象的Y坐标置反
            #         new_obj.location.y = -new_obj.location.y
            #         # 圆球放到相应的集合中
            #         if tar_obj_name == '左耳':
            #             bpy.data.collections['Left'].objects.link(new_obj)
            #         else:
            #             bpy.data.collections['Right'].objects.link(new_obj)
            #
            #         if i != 2:
            #             new_spheres.append(new_obj)

            # 将字典复制并改变键值
            if tar_obj_name == '左耳':
                tar_object_dic = {key.replace('右', '左'): value for key, value in ori_object_dic.items()}
                numberL = len(tar_object_dic)
                sphere_number = number
            else:
                tar_object_dic = {key.replace('左', '右'): value for key, value in ori_object_dic.items()}
                number = len(tar_object_dic)
                sphere_number = numberL

            # 复制ventcanal_data
            # for i in range(len(ori_spheres)):
            for i in range(sphere_number):
                tar_ventcanal_data.append(ori_ventcanal_data[3 * i])
                tar_ventcanal_data.append(-1 * ori_ventcanal_data[3 * i + 1])
                tar_ventcanal_data.append(ori_ventcanal_data[3 * i + 2])

                for key in tar_object_dic:
                    if tar_object_dic[key] == i:
                        sphere_name = key
                mesh = bpy.data.meshes.new(sphere_name)
                new_obj = bpy.data.objects.new(name=sphere_name, object_data=mesh)
                bpy.context.scene.collection.objects.link(new_obj)
                if tar_obj_name == '左耳':
                    moveToLeft(new_obj)
                else:
                    moveToRight(new_obj)
                me = new_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                # 设置圆球的参数
                radius = 0.4  # 半径
                segments = 32  # 分段数
                bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
                bm.to_mesh(me)
                bm.free()
                newColor('red', 1, 0, 0, 0, 1)
                new_obj.data.materials.append(bpy.data.materials['red'])
                new_obj.location = (tar_ventcanal_data[3 * i], tar_ventcanal_data[3 * i + 1],
                                    tar_ventcanal_data[3 * i + 2])

            if tar_obj_name == '左耳':
                ventcanal_dataL = tar_ventcanal_data
                object_dicL = tar_object_dic
            else:
                ventcanal_data = tar_ventcanal_data
                object_dic = tar_object_dic

            print("当前场景存在的所有对象：")
            for i in bpy.data.objects:
                print(i.name)


            if len(tar_object_dic) >= 2:
                sphere_name1 = tar_obj_name + 'ventcanalsphere' + '1'
                sphere_obj1 = bpy.data.objects.get(sphere_name1)
                duplicate_obj1 = sphere_obj1.copy()
                duplicate_obj1.data = sphere_obj1.data.copy()
                duplicate_obj1.animation_data_clear()
                duplicate_obj1.name = tar_obj_name + 'ventcanalsphere' + '201'
                bpy.context.scene.collection.objects.link(duplicate_obj1)
                newColor('ventcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
                # newColor('ventcanalSphereTransparency', 0, 1, 1, 1, 0.9)
                duplicate_obj1.data.materials.clear()
                duplicate_obj1.data.materials.append(bpy.data.materials['ventcanalSphereTransparency'])
                duplicate_obj1.scale[0] = 1.5
                duplicate_obj1.scale[1] = 1.5
                duplicate_obj1.scale[2] = 1.5
                sphere_name2 = tar_obj_name + 'ventcanalsphere' + '2'
                sphere_obj2 = bpy.data.objects.get(sphere_name2)
                duplicate_obj2 = sphere_obj2.copy()
                duplicate_obj2.data = sphere_obj2.data.copy()
                duplicate_obj2.animation_data_clear()
                duplicate_obj2.name = tar_obj_name + 'ventcanalsphere' + '202'
                bpy.context.scene.collection.objects.link(duplicate_obj2)
                newColor('ventcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
                # newColor('ventcanalSphereTransparency', 0, 1, 1, 1, 0.9)
                duplicate_obj2.data.materials.clear()
                duplicate_obj2.data.materials.append(bpy.data.materials['ventcanalSphereTransparency'])
                duplicate_obj2.scale[0] = 1.5
                duplicate_obj2.scale[1] = 1.5
                duplicate_obj2.scale[2] = 1.5
                if tar_obj_name == '右耳':
                    moveToRight(duplicate_obj1)
                    moveToRight(duplicate_obj2)
                elif tar_obj_name == '左耳':
                    moveToLeft(duplicate_obj1)
                    moveToLeft(duplicate_obj2)


            if len(tar_object_dic) <= 1:  # 如果只有一个红球，不进行镜像，直接删除相关数据
                if tar_obj_name == '左耳':
                    numberL = 0
                else:
                    number = 0
                tar_ventcanal_data.clear()
                tar_object_dic.clear()

            elif len(tar_object_dic) > 1:  # 如果有两个及以上个红球，生成管道
                # initialTransparency()
                # tar_obj.data.materials.clear()
                # tar_obj.data.materials.append(bpy.data.materials['Transparency'])
                name = bpy.context.scene.leftWindowObj
                if name == '右耳':
                    bpy.context.scene.transparent3EnumR = 'OP3'
                    # bpy.context.scene.transparentper3EnumR = '0.6'
                elif name == '左耳':
                    bpy.context.scene.transparent3EnumL = 'OP3'
                    # bpy.context.scene.transparentper3EnumR = '0.6'

                newColor('grey', 0.8, 0.8, 0.8, 0, 1)
                newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)
                obj = new_curve(tar_obj_name + 'ventcanal')
                obj.data.materials.append(bpy.data.materials["grey"])
                # 添加一个曲线样条
                spline = obj.data.splines.new(type='NURBS')
                spline.order_u = 2
                spline.use_smooth = True
                spline.points.add(count=len(tar_object_dic) - 1)
                for i, point in enumerate(spline.points):
                    point.co = (
                    tar_ventcanal_data[3 * i], tar_ventcanal_data[3 * i + 1], tar_ventcanal_data[3 * i + 2], 1)

                # 重新将曲线控制点勾挂到管道控制红球上
                hook_curve_point_to_sphere()

                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.duplicate()
                duplicated_curve_obj = bpy.context.view_layer.objects.active
                duplicated_curve_obj.name = f"{tar_obj_name}meshventcanal"
                bpy.ops.object.convert(target='MESH')
                obj.hide_set(True)

            if tar_obj_name == '左耳':
                for i in range(number):
                    if i != 0 and i != 1:
                        create_sphere_snap_plane(i + 1)
            else:
                for i in range(numberL):
                    if i != 0 and i != 1:
                        create_sphere_snap_plane(i + 1)

            tar_obj.hide_select = True
            if tar_obj_name == '左耳':
                bpy.context.scene.tongQiGuanDaoZhiJing_L = bpy.context.scene.tongQiGuanDaoZhiJing
            else:
                bpy.context.scene.tongQiGuanDaoZhiJing = bpy.context.scene.tongQiGuanDaoZhiJing_L
        # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')


def new_curve(curve_name):
    ''' 创建并返回一个新的曲线对象 '''
    name = bpy.context.scene.leftWindowObj
    curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
    curve_data.dimensions = '3D'
    obj = bpy.data.objects.new(curve_name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bevel_depth = None
    if name == '右耳':
        bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing / 2
        moveToRight(obj)
    elif name == '左耳':
        bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing_L / 2
        moveToLeft(obj)
    obj.data.bevel_depth = bevel_depth  # 管道孔径
    obj.data.bevel_resolution = 8  # 管道分辨率
    obj.data.use_fill_caps = True  # 封盖
    return obj


def generate_canal(co):
    ''' 初始化管道 '''
    global number
    global numberL
    name = bpy.context.scene.leftWindowObj
    number_cur = None
    if (name == "右耳"):
        number_cur = number
    elif (name == "左耳"):
        number_cur = numberL
    obj = new_curve(name + 'ventcanal')
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

    add_sphere(co, 0)
    save_ventcanal_info(co)


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
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        curve_object = bpy.data.objects[name + 'ventcanal']
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
        bpy.data.objects[name + 'newcurve'].name = name + 'ventcanal'
        bpy.data.objects[name + 'ventcanal'].hide_set(True)

        for key in object_dic:
            if object_dic[key] >= index:
                object_dic[key] += 1
    elif (name == "左耳"):
        curve_object = bpy.data.objects[name + 'ventcanal']
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
        bpy.data.objects[name + 'newcurve'].name = name + 'ventcanal'
        bpy.data.objects[name + 'ventcanal'].hide_set(True)

        for key in object_dicL:
            if object_dicL[key] >= index:
                object_dicL[key] += 1



def finish_canal(co):
    ''' 完成管道的初始化 '''
    name = bpy.context.scene.leftWindowObj
    curve_object = bpy.data.objects[name + 'ventcanal']
    curve_data = curve_object.data
    obj = bpy.data.objects[name]
    first_co = Vector(curve_data.splines[0].points[0].co[0:3])
    _, _, normal, _ = obj.closest_point_on_mesh(first_co)
    reverse_normal = (-normal[0], -normal[1], -normal[2])
    reverse_normal = Vector(reverse_normal)
    reverse_normal.normalize()
    point_vec = co - first_co
    projection = reverse_normal.dot(point_vec) * reverse_normal
    projected_point = first_co + projection
    curve_data.splines[0].points.add(count=2)
    curve_data.splines[0].points[1].co[0:3] = projected_point
    curve_data.splines[0].points[1].co[3] = 1
    curve_data.splines[0].points[2].co[0:3] = co
    curve_data.splines[0].points[2].co[3] = 1
    add_sphere(co, 2)
    add_sphere(projected_point, 1)
    # 根据管道两端的红球复制出两个透明圆球,操作管道两端的时候,每次激活的都是这两个透明圆球,用于限制实际的两端管道红球和管道控制点在左右耳模型上
    sphere_name1 = name + 'ventcanalsphere' + '1'
    sphere_obj1 = bpy.data.objects.get(sphere_name1)
    duplicate_obj1 = sphere_obj1.copy()
    duplicate_obj1.data = sphere_obj1.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + 'ventcanalsphere' + '201'
    bpy.context.scene.collection.objects.link(duplicate_obj1)
    newColor('ventcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    # newColor('ventcanalSphereTransparency', 0, 1, 1, 1, 0.9)
    duplicate_obj1.data.materials.clear()
    duplicate_obj1.data.materials.append(bpy.data.materials['ventcanalSphereTransparency'])
    duplicate_obj1.scale[0] = 1.5
    duplicate_obj1.scale[1] = 1.5
    duplicate_obj1.scale[2] = 1.5
    sphere_name2 = name + 'ventcanalsphere' + '2'
    sphere_obj2 = bpy.data.objects.get(sphere_name2)
    duplicate_obj2 = sphere_obj2.copy()
    duplicate_obj2.data = sphere_obj2.data.copy()
    duplicate_obj2.animation_data_clear()
    duplicate_obj2.name = name + 'ventcanalsphere' + '202'
    bpy.context.scene.collection.objects.link(duplicate_obj2)
    newColor('ventcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    # newColor('ventcanalSphereTransparency', 0, 1, 1, 1, 0.9)
    duplicate_obj2.data.materials.clear()
    duplicate_obj2.data.materials.append(bpy.data.materials['ventcanalSphereTransparency'])
    duplicate_obj2.scale[0] = 1.5
    duplicate_obj2.scale[1] = 1.5
    duplicate_obj2.scale[2] = 1.5
    if name == '右耳':
        moveToRight(duplicate_obj1)
        moveToRight(duplicate_obj2)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)
        moveToLeft(duplicate_obj2)
    convert_ventcanal()
    save_ventcanal_info(co)
    curve_object.hide_set(True)
    bpy.data.objects[name].hide_select = True


def hooktoobject(index):
    ''' 建立指定下标的控制点到圆球的字典 '''
    global number
    global numberL
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        sphere_name = name + 'ventcanalsphere' + str(number)
        object_dic.update({sphere_name: index})
    elif (name == "左耳"):
        sphere_name = name + 'ventcanalsphere' + str(numberL)
        object_dicL.update({sphere_name: index})



def save_ventcanal_info(co):
    global ventcanal_data
    global ventcanal_dataL
    name = bpy.context.scene.leftWindowObj
    cox = round(co[0], 3)
    coy = round(co[1], 3)
    coz = round(co[2], 3)
    if (name == "右耳"):
        if (cox not in ventcanal_data) or (coy not in ventcanal_data) or (coz not in ventcanal_data):
            for object in bpy.data.objects:
                if object.name == name + 'ventcanal':
                    ventcanal_data = []
                    curve_data = object.data
                    for point in curve_data.splines[0].points:
                        ventcanal_data.append(round(point.co[0], 3))
                        ventcanal_data.append(round(point.co[1], 3))
                        ventcanal_data.append(round(point.co[2], 3))
            return True
        return False
    elif (name == "左耳"):
        if (cox not in ventcanal_dataL) or (coy not in ventcanal_dataL) or (coz not in ventcanal_dataL):
            for object in bpy.data.objects:
                if object.name == name + 'ventcanal':
                    ventcanal_dataL = []
                    curve_data = object.data
                    for point in curve_data.splines[0].points:
                        ventcanal_dataL.append(round(point.co[0], 3))
                        ventcanal_dataL.append(round(point.co[1], 3))
                        ventcanal_dataL.append(round(point.co[2], 3))
            return True
        return False
    return False


def initial_ventcanal():
    # 初始化
    global object_dic
    global object_dicL
    global ventcanal_data
    global ventcanal_dataL
    global ventcanal_finish
    global ventcanal_finishL
    global prev_sphere_number_plane
    global prev_sphere_number_planeL
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    ventcanal_data_cur = None
    if (name == "右耳"):
        ventcanal_finish = False
        object_dic_cur = object_dic
        ventcanal_data_cur = ventcanal_data
        prev_sphere_number_plane = 0
    elif (name == "左耳"):
        ventcanal_finishL = False
        object_dic_cur = object_dicL
        ventcanal_data_cur = ventcanal_dataL
        prev_sphere_number_planeL = 0
    if len(object_dic_cur) >= 2:  # 存在已保存的圆球位置,复原原有的管道
        # initialTransparency()
        newColor('red', 1, 0, 0, 1, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)
        obj = new_curve(name + 'ventcanal')
        obj.data.materials.append(bpy.data.materials["grey"])

        # 添加一个曲线样条
        spline = obj.data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points.add(count=len(object_dic_cur) - 1)
        for i, point in enumerate(spline.points):
            point.co = (ventcanal_data_cur[3 * i], ventcanal_data_cur[3 * i + 1], ventcanal_data_cur[3 * i + 2], 1)

        # 生成圆球
        for key in object_dic_cur:
            mesh = bpy.data.meshes.new(name + "ventcanalsphere")
            obj = bpy.data.objects.new(key, mesh)
            bpy.context.collection.objects.link(obj)
            if name == '右耳':
                moveToRight(obj)
            elif name == '左耳':
                moveToLeft(obj)

            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            # 设置圆球的参数
            radius = 0.4  # 半径
            segments = 32  # 分段数
            bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
            bm.to_mesh(me)
            bm.free()
            obj.data.materials.append(bpy.data.materials['red'])
            obj.location = bpy.data.objects[name + 'ventcanal'].data.splines[0].points[object_dic_cur[key]].co[0:3]  # 指定的位置坐标

        # 根据管道两端的红球复制出两个透明圆球,操作管道两端的时候,每次激活的都是这两个透明圆球,用于限制实际的两端管道红球和管道控制点在左右耳模型上
        sphere_name1 = name + 'ventcanalsphere' + '1'
        sphere_obj1 = bpy.data.objects.get(sphere_name1)
        duplicate_obj1 = sphere_obj1.copy()
        duplicate_obj1.data = sphere_obj1.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = name + 'ventcanalsphere' + '201'
        bpy.context.scene.collection.objects.link(duplicate_obj1)
        # newColor('ventcanalSphereTransparency', 0, 1, 1, 1, 0.9)
        newColor('ventcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
        duplicate_obj1.data.materials.clear()
        duplicate_obj1.data.materials.append(bpy.data.materials['ventcanalSphereTransparency'])
        duplicate_obj1.scale[0] = 1.5
        duplicate_obj1.scale[1] = 1.5
        duplicate_obj1.scale[2] = 1.5
        sphere_name2 = name + 'ventcanalsphere' + '2'
        sphere_obj2 = bpy.data.objects.get(sphere_name2)
        duplicate_obj2 = sphere_obj2.copy()
        duplicate_obj2.data = sphere_obj2.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + 'ventcanalsphere' + '202'
        bpy.context.scene.collection.objects.link(duplicate_obj2)
        newColor('ventcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
        # newColor('ventcanalSphereTransparency', 0, 1, 1, 1, 0.9)
        duplicate_obj2.data.materials.clear()
        duplicate_obj2.data.materials.append(bpy.data.materials['ventcanalSphereTransparency'])
        duplicate_obj2.scale[0] = 1.5
        duplicate_obj2.scale[1] = 1.5
        duplicate_obj2.scale[2] = 1.5
        if name == '右耳':
            moveToRight(duplicate_obj1)
            moveToRight(duplicate_obj2)
        elif name == '左耳':
            moveToLeft(duplicate_obj1)
            moveToLeft(duplicate_obj2)

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        # bpy.data.objects[name].data.materials.clear()
        # bpy.data.objects[name].data.materials.append(bpy.data.materials["Transparency"])
        if name == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP3'
            # bpy.context.scene.transparentper3EnumR = '0.6'
        elif name == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP3'
            # bpy.context.scene.transparentper3EnumR = '0.6'
        bpy.data.objects[name].hide_select = True
        convert_ventcanal()
        save_ventcanal_info([0, 0, 0])
        bpy.data.objects[name + 'ventcanal'].hide_set(True)

    elif len(object_dic_cur) == 1:  # 只点击了一次
        newColor('red', 1, 0, 0, 1, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        obj = new_curve(name + 'ventcanal')
        obj.data.materials.append(bpy.data.materials["grey"])
        # 添加一个曲线样条
        spline = obj.data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points[0].co[0:3] = ventcanal_data_cur[0:3]
        spline.points[0].co[3] = 1
        # spline.use_cyclic_u = True
        # spline.use_endpoint_u = True

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True
        bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')

        mesh = bpy.data.meshes.new(name + "ventcanalsphere")
        obj = bpy.data.objects.new(name + "ventcanalsphere1", mesh)
        bpy.context.collection.objects.link(obj)
        if name == '右耳':
            moveToRight(obj)
        elif name == '左耳':
            moveToLeft(obj)

        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        # 设置圆球的参数
        radius = 0.4  # 半径
        segments = 32  # 分段数
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
        bm.to_mesh(me)
        bm.free()
        obj.data.materials.append(bpy.data.materials['red'])
        obj.location = ventcanal_data_cur[0:3]  # 指定的位置坐标

    else:  # 不存在已保存的圆球位置
        pass



    # 为管道控制红球添加位置约束,只能在红环平面上移动
    if (name == "右耳"):
        for obj in bpy.data.objects:
            soundCanalPlanePattern = r'右耳VentCanalPlane'
            soundCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
            if re.match(soundCanalPlanePattern, obj.name) and not re.match(soundCanalPlaneBorderPattern, obj.name):
                sphere_number = int(obj.name.replace('右耳VentCanalPlane', ''))
                sphere_name = '右耳ventcanalsphere' + str(sphere_number)
                cur_sphere_obj = bpy.data.objects.get(sphere_name)
                if (cur_sphere_obj != None):
                    limit_location_constraint = None
                    for constraint in cur_sphere_obj.constraints:
                        if (constraint.type == 'LIMIT_LOCATION'):
                            limit_location_constraint = constraint
                            break
                    if (limit_location_constraint == None):
                        limit_location_constraint = cur_sphere_obj.constraints.new(type='LIMIT_LOCATION')
                    limit_location_constraint.use_min_z = True
                    limit_location_constraint.min_z = 0
                    limit_location_constraint.use_max_z = True
                    limit_location_constraint.max_z = 0
                    limit_location_constraint.owner_space = 'CUSTOM'
                    limit_location_constraint.space_object = obj
    elif (name == "左耳"):
        for obj in bpy.data.objects:
            soundCanalPlanePattern = r'左耳VentCanalPlane'
            soundCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
            if re.match(soundCanalPlanePattern, obj.name) and not re.match(soundCanalPlaneBorderPattern, obj.name):
                sphere_number = int(obj.name.replace('左耳VentCanalPlane', ''))
                sphere_name = '左耳ventcanalsphere' + str(sphere_number)
                cur_sphere_obj = bpy.data.objects.get(sphere_name)
                if (cur_sphere_obj != None):
                    limit_location_constraint = None
                    for constraint in cur_sphere_obj.constraints:
                        if (constraint.type == 'LIMIT_LOCATION'):
                            limit_location_constraint = constraint
                            break
                    if (limit_location_constraint == None):
                        limit_location_constraint = cur_sphere_obj.constraints.new(type='LIMIT_LOCATION')
                    limit_location_constraint.use_min_z = True
                    limit_location_constraint.min_z = 0
                    limit_location_constraint.use_max_z = True
                    limit_location_constraint.max_z = 0
                    limit_location_constraint.owner_space = 'CUSTOM'
                    limit_location_constraint.space_object = obj



    # 重新将曲线控制点勾挂到管道控制红球上
    hook_curve_point_to_sphere()

    bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')


def submit_ventcanal():
    # 应用修改器，删除多余的物体
    global object_dic
    global object_dicL
    global ventcanal_finish
    global ventcanal_finishL
    name = bpy.context.scene.leftWindowObj
    apply_hook_modifies()
    if (name == "右耳"):
        if len(object_dic) > 0 and ventcanal_finish == False:
            if len(object_dic) >= 2:
                adjustpoint()
                bpy.ops.object.select_all(action='DESELECT')
                # 将通气孔上的顶点选中
                vent_canal_obj = bpy.data.objects.get(name + 'meshventcanal')
                vent_canal_obj.select_set(True)
                bpy.context.view_layer.objects.active = vent_canal_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                # 将左右耳模型设置为当前激活物体,将顶点取消选中
                bpy.ops.object.select_all(action='DESELECT')
                cur_obj = bpy.data.objects.get(name)
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bool_modifier = bpy.context.active_object.modifiers.new(
                    name="Ventcanal Boolean Modifier", type='BOOLEAN')
                bool_modifier.operation = 'DIFFERENCE'
                bool_modifier.object = bpy.data.objects[name + 'meshventcanal']
                bpy.ops.object.modifier_apply(modifier="Ventcanal Boolean Modifier", single_user=True)
                #根据切割后的物体复制一份用于平滑失败的回退
                ventcanal_smooth_reset_obj = bpy.data.objects.get(name + "VentCanalSmoothReset")
                if (ventcanal_smooth_reset_obj != None):
                    bpy.data.objects.remove(ventcanal_smooth_reset_obj, do_unlink=True)
                duplicate_obj = cur_obj.copy()
                duplicate_obj.data = cur_obj.data.copy()
                duplicate_obj.animation_data_clear()
                duplicate_obj.name = name + "VentCanalSmoothReset"
                bpy.context.collection.objects.link(duplicate_obj)
                if name == '右耳':
                    moveToRight(duplicate_obj)
                elif name == '左耳':
                    moveToLeft(duplicate_obj)
                duplicate_obj.hide_set(True)
                try:
                    # 布尔后管道产生的新顶点被选中,根据选中的顶点找出其边界轮廓线,offset_cut后进行倒角
                    offset_cut = bpy.context.scene.tongQiGuanDaoZhiJing * 0.3  # 管道直径默认值为1,对应的offset_cut宽度为0.3
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.region_to_loop()
                    bpy.ops.huier.offset_cut(width=offset_cut, shade_smooth=True, mark_sharp=False, all_cyclic=True)
                    bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=80, segments=5, release_confirm=True)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    print("管道平滑失败回退")
                    #平滑失败则将当前左右耳物体删除并用平滑回退物体将其替换
                    ventcanal_smooth_reset_obj = bpy.data.objects.get(name + "VentCanalSmoothReset")
                    if(ventcanal_smooth_reset_obj != None):
                        bpy.data.objects.remove(cur_obj, do_unlink=True)
                        ventcanal_smooth_reset_obj.name = name
                        bpy.ops.object.select_all(action='DESELECT')
                        ventcanal_smooth_reset_obj.hide_set(False)
                        ventcanal_smooth_reset_obj.select_set(True)
                        bpy.context.view_layer.objects.active = ventcanal_smooth_reset_obj
                #若平滑成功未执行回退,则将平滑回退物体删除
                ventcanal_smooth_reset_obj = bpy.data.objects.get(name + "VentCanalSmoothReset")
                if (ventcanal_smooth_reset_obj != None):
                    bpy.data.objects.remove(ventcanal_smooth_reset_obj, do_unlink=True)
            need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                              name + 'ventcanalsphere' + '201', name + 'ventcanalsphere' + '202']
            # 隐藏红球平面与平面边界          #TODO 正常情况下应该时删除这些平面和边界,但是为了防止重新进入该模块生成的平面过多时过于卡顿,因此此处将其隐藏
            for obj in bpy.data.objects:
                ventCanalPlanePattern = r'右耳VentCanalPlane'
                ventCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
                if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                    obj.hide_set(True)
            for key in object_dic:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj = bpy.data.objects.get(name)
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            # apply_material()
            bpy.context.scene.transparent3EnumR = 'OP1'
            utils_re_color(name, (1, 0.319, 0.133))
            # bpy.context.active_object.data.use_auto_smooth = True
            # bpy.context.object.data.auto_smooth_angle = 0.8
            bpy.data.objects[name].hide_select = False
            if cur_obj.vertex_groups.get('TransformBorder') != None:
                transform_obj_name = bpy.context.scene.leftWindowObj + "VentCanalReset"
                transform_normal(transform_obj_name, [])
    elif (name == "左耳"):
        if len(object_dicL) > 0 and ventcanal_finishL == False:
            if len(object_dicL) >= 2:
                adjustpoint()
                bpy.ops.object.select_all(action='DESELECT')
                # 将通气孔上的顶点选中
                vent_canal_obj = bpy.data.objects.get(name + 'meshventcanal')
                vent_canal_obj.select_set(True)
                bpy.context.view_layer.objects.active = vent_canal_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                # 将左右耳模型设置为当前激活物体,将顶点取消选中
                bpy.ops.object.select_all(action='DESELECT')
                cur_obj = bpy.data.objects.get(name)
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bool_modifier = bpy.context.active_object.modifiers.new(
                    name="Ventcanal Boolean Modifier", type='BOOLEAN')
                bool_modifier.operation = 'DIFFERENCE'
                bool_modifier.object = bpy.data.objects[name + 'meshventcanal']
                bpy.ops.object.modifier_apply(modifier="Ventcanal Boolean Modifier", single_user=True)
                # 根据切割后的物体复制一份用于平滑失败的回退
                ventcanal_smooth_reset_obj = bpy.data.objects.get(name + "VentCanalSmoothReset")
                if (ventcanal_smooth_reset_obj != None):
                    bpy.data.objects.remove(ventcanal_smooth_reset_obj, do_unlink=True)
                duplicate_obj = cur_obj.copy()
                duplicate_obj.data = cur_obj.data.copy()
                duplicate_obj.animation_data_clear()
                duplicate_obj.name = name + "VentCanalSmoothReset"
                bpy.context.collection.objects.link(duplicate_obj)
                if name == '右耳':
                    moveToRight(duplicate_obj)
                elif name == '左耳':
                    moveToLeft(duplicate_obj)
                duplicate_obj.hide_set(True)
                try:
                    # 布尔后管道产生的新顶点被选中,根据选中的顶点找出其边界轮廓线,offset_cut后进行倒角
                    offset_cut = bpy.context.scene.tongQiGuanDaoZhiJing_L * 0.3  # 管道直径默认值为1,对应的offset_cut宽度为0.3
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.region_to_loop()
                    bpy.ops.huier.offset_cut(width=offset_cut, shade_smooth=True, mark_sharp=False, all_cyclic=True)
                    bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=80, segments=5, release_confirm=True)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    print("管道平滑失败回退")
                    # 平滑失败则将当前左右耳物体删除并用平滑回退物体将其替换
                    ventcanal_smooth_reset_obj = bpy.data.objects.get(name + "VentCanalSmoothReset")
                    if (ventcanal_smooth_reset_obj != None):
                        bpy.data.objects.remove(cur_obj, do_unlink=True)
                        ventcanal_smooth_reset_obj.name = name
                        bpy.ops.object.select_all(action='DESELECT')
                        ventcanal_smooth_reset_obj.hide_set(False)
                        ventcanal_smooth_reset_obj.select_set(True)
                        bpy.context.view_layer.objects.active = ventcanal_smooth_reset_obj
                # 若平滑成功未执行回退,则将平滑回退物体删除
                ventcanal_smooth_reset_obj = bpy.data.objects.get(name + "VentCanalSmoothReset")
                if (ventcanal_smooth_reset_obj != None):
                    bpy.data.objects.remove(ventcanal_smooth_reset_obj, do_unlink=True)
            need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                              name + 'ventcanalsphere' + '201', name + 'ventcanalsphere' + '202']
            # 隐藏红球平面与平面边界          #TODO 正常情况下应该时删除这些平面和边界,但是为了防止重新进入该模块生成的平面过多时过于卡顿,因此此处将其隐藏
            for obj in bpy.data.objects:
                ventCanalPlanePattern = r'左耳VentCanalPlane'
                ventCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
                if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                    obj.hide_set(True)
            for key in object_dicL:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj = bpy.data.objects.get(name)
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            # apply_material()
            bpy.context.scene.transparent3EnumL = 'OP1'
            utils_re_color(name, (1, 0.319, 0.133))
            # bpy.context.active_object.data.use_auto_smooth = True
            # bpy.context.object.data.auto_smooth_angle = 0.8
            bpy.data.objects[name].hide_select = False
            if cur_obj.vertex_groups.get('TransformBorder') != None:
                transform_obj_name = bpy.context.scene.leftWindowObj + "SoundCanalReset"
                transform_normal(transform_obj_name, [])


def adjustpoint():
    name = bpy.context.scene.leftWindowObj
    curve_object = bpy.data.objects[name + 'ventcanal']
    curve_data = curve_object.data
    last_index = len(curve_data.splines[0].points) - 1
    first_point = curve_data.splines[0].points[0]
    last_point = curve_data.splines[0].points[last_index]
    step = 0.3
    normal = Vector(first_point.co[0:3]) - Vector(curve_data.splines[0].points[1].co[0:3])
    first_point.co = (first_point.co[0] + normal[0] * step, first_point.co[1] + normal[1] * step,
                      first_point.co[2] + normal[2] * step, 1)
    normal = Vector(last_point.co[0:3]) - Vector(curve_data.splines[0].points[last_index - 1].co[0:3])
    last_point.co = (last_point.co[0] + normal[0] * step, last_point.co[1] + normal[1] * step,
                     last_point.co[2] + normal[2] * step, 1)
    convert_ventcanal()


def checkposition():
    name = bpy.context.scene.leftWindowObj
    object = bpy.data.objects[name + 'meshventcanal']
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


def frontToVentCanal():
    name = bpy.context.scene.leftWindowObj
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "VentCanalReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "VentCanalReset"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)
    initial_ventcanal()

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def frontFromVentCanal():
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    apply_hook_modifies()
    save_ventcanal_info([0, 0, 0])
    need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                      name + 'ventcanalsphere' + '201', name + 'ventcanalsphere' + '202']
    # 隐藏红球平面与平面边界          #TODO 正常情况下应该时删除这些平面和边界,但是为了防止重新进入该模块生成的平面过多时过于卡顿,因此此处将其隐藏
    if (name == "右耳"):
        for obj in bpy.data.objects:
            ventCanalPlanePattern = r'右耳VentCanalPlane'
            ventCanalPlaneBorderPattern = r'右耳VentCanalPlaneBorderCurveObject'
            if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                obj.hide_set(True)
    elif (name == "左耳"):
        for obj in bpy.data.objects:
            ventCanalPlanePattern = r'左耳VentCanalPlane'
            ventCanalPlaneBorderPattern = r'左耳VentCanalPlaneBorderCurveObject'
            if re.match(ventCanalPlanePattern, obj.name) or re.match(ventCanalPlaneBorderPattern, obj.name):
                obj.hide_set(True)
    if name == '右耳':
        for key in object_dic:
            need_to_delete_model_name_list.append(key)
    elif name == '左耳':
        for key in object_dicL:
            need_to_delete_model_name_list.append(key)
    delete_useless_object(need_to_delete_model_name_list)
    obj = bpy.data.objects[name]
    resetname = name + "VentCanalReset"
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
        if (selected_obj.name == name + "VentCanalReset" or selected_obj.name == name + "VentCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def backToVentCanal():
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

    exist_VentCanalReset = False
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "VentCanalReset"):
            exist_VentCanalReset = True
    if (exist_VentCanalReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "VentCanalReset"
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

        initial_ventcanal()
    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "SoundCanalLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            if name == '右耳':
                moveToRight(ori_obj)
            elif name == '左耳':
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "MouldLast") != None):
            lastname = name + "MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            if name == '右耳':
                moveToRight(ori_obj)
            elif name == '左耳':
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "QieGeLast") != None):
            lastname = name + "QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            if name == '右耳':
                moveToRight(ori_obj)
            elif name == '左耳':
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "LocalThickLast") != None):
            lastname = name + "LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            if name == '右耳':
                moveToRight(ori_obj)
            elif name == '左耳':
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = name + "DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
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

        initial_ventcanal()

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def backFromVentCanal():
    apply_hook_modifies()
    save_ventcanal_info([0, 0, 0])
    submit_ventcanal()
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "VentCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    obj.hide_select = False
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "VentCanalLast"
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


_classes = [
    TEST_OT_addventcanal,
    TEST_OT_deleteventcanal,
    TEST_OT_ventcanalqiehuan,
    TEST_OT_finishventcanal,
    TEST_OT_resetventcanal,
    TEST_OT_mirrorventcanal
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
