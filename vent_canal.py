import bpy
import bmesh
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
from math import sqrt
from .tool import newShader, moveToRight, moveToLeft, utils_re_color, delete_useless_object, newColor, \
    getOverride, apply_material
import re

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

mouse_index = 0                   #添加传声孔之后,切换其存在的鼠标行为,记录当前在切换到了哪种鼠标行为
mouse_indexL = 0

prev_sphere_number_plane = 0      #记录鼠标在管道中间的红球间切换时,上次位于的红球
prev_sphere_number_planeL = 0

def initialTransparency():
    mat = newColor("Transparency", 1, 0.319, 0.133, 1, 0.4)  # 创建材质
    mat.use_backface_culling = True


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
    copy_curve()
    duplicate_obj = bpy.data.objects[name + 'meshventcanal']
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    # while(bpy.context.active_object.modifiers):
    #     modifer_name = bpy.context.active_object.modifiers[0].name
    #     bpy.ops.object.modifier_apply(modifier = modifer_name)
    bevel_depth = None
    if name == '右耳':
        bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing / 2
    elif name == '左耳':
        bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing_L / 2
    bpy.context.active_object.data.bevel_depth = bevel_depth  # 设置曲线倒角深度
    bpy.context.active_object.data.bevel_resolution = 8  # 管道分辨率
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




def mouse_switch(context,event):
    '''
    鼠标位于不同的物体上时,切换到不同的传声孔鼠标行为
    '''
    global mouse_index
    global mouse_indexL
    name = bpy.context.scene.leftWindowObj
    if(name == '右耳'):
        sphere_number = on_which_shpere(context,event)
        if(sphere_number == 0 and mouse_index != 1):
            mouse_index = 1
            # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
        elif(sphere_number != 0 and mouse_index != 2):
            mouse_index = 2
            print(sphere_number)
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            sphere_name = name + 'ventcanalsphere' + str(sphere_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal3")
    elif(name == '左耳'):
        sphere_number = on_which_shpere(context, event)
        if (sphere_number == 0 and mouse_indexL != 1):
            mouse_indexL = 1
            # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
        elif (sphere_number != 0 and mouse_indexL != 2):
            mouse_indexL = 2
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
    # 若位于管道两端的圆球上,则需要吸附在模型上
    if sphere_number == 1 or sphere_number == 2:
        bpy.context.scene.tool_settings.use_snap = True
        # 左右耳模型是不可选中的,为了让其吸附在模型上,需要将该吸附参数设置为False
        bpy.context.scene.tool_settings.use_snap_selectable = False
    #鼠标位于管道中间的圆球上且在不同的圆球上切换时,删除原有的平面并生成新的平面
    if(sphere_number != 0):
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
    sphere_name = name + 'ventcanalsphere' + str(sphere_number)
    cur_sphere_obj = bpy.data.objects.get(sphere_name)
    cur_obj = bpy.data.objects.get(name)
    if (cur_sphere_obj != None):
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
            previous_co = previous_sphere_obj.location
            next_co = next_sphere_obj.location
            plane_normal = previous_co - next_co
            plane_co = cur_sphere_obj.location
            #根据plane_normal和plane_co生成一个平面并将其摆正对齐
            bpy.ops.mesh.primitive_plane_add(size = 50, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            planename = name + "VentCanalPlane"
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
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            #为平面添加透明材质
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

            #根据平面边界生成红环
            draw_plane_border()
            #将激活物体重新设置为红球
            bpy.ops.object.select_all(action='DESELECT')
            cur_sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_sphere_obj

def draw_plane_border():
    '''
    根据平面边界顶点绘制出一圈红环边界
    '''
    name = bpy.context.scene.leftWindowObj
    planename = name + "VentCanalPlane"
    plane_obj = bpy.data.objects.get(planename)
    if(plane_obj != None):
        #根据平面复制出一份物体用于生成边界红环
        plane_border_curve = plane_obj.copy()
        plane_border_curve.data = plane_obj.data.copy()
        plane_border_curve.animation_data_clear()
        plane_border_curve.name = name + "VentCanalPlaneBorderCurveObject"
        bpy.context.collection.objects.link(plane_border_curve)
        if (name == "右耳"):
            moveToRight(plane_border_curve)
        elif (name == "左耳"):
            moveToLeft(plane_border_curve)
        bpy.ops.object.select_all(action='DESELECT')                    #将边界红环激活
        plane_border_curve.select_set(True)
        bpy.context.view_layer.objects.active = plane_border_curve
        bpy.ops.object.mode_set(mode='EDIT')                            #将平面选中并删除其中的面,只保存边界线将其转化为曲线
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target='CURVE')
        bpy.context.object.data.bevel_depth = 0.02                      #为圆环上色
        soundcanal_plane_border_red_material = bpy.data.materials.new(name="VentCanalPlaneBorderRed")
        soundcanal_plane_border_red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
        plane_border_curve.data.materials.append(soundcanal_plane_border_red_material)
        bpy.ops.object.select_all(action='DESELECT')                    #将平面圆环边界设置为不可选中
        plane_border_curve.hide_select = True


def delete_sphere_snap_plane():
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
    planename = name + "VentCanalPlane"
    plane_obj = bpy.data.objects.get(planename)
    plane_border_name = name + "VentCanalPlaneBorderCurveObject"
    plane_border_obj = bpy.data.objects.get(plane_border_name)
    if(plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    if(plane_border_obj != None):
        bpy.data.objects.remove(plane_border_obj, do_unlink=True)



class TEST_OT_addventcanal(bpy.types.Operator):
    bl_idname = "object.addventcanal"
    bl_label = "addventcanal"
    bl_description = "双击添加管道控制点"

    def excute(self, context, event):

        global number
        global numberL
        name = bpy.context.scene.leftWindowObj
        mesh_name = name + 'meshventcanal'
        number_cur = None
        if (name == "右耳"):
            number_cur = number
        elif (name == "左耳"):
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
                bpy.data.objects[name].data.materials.clear()  # 清除材质
                bpy.data.objects[name].data.materials.append(bpy.data.materials["Transparency"])
                bpy.ops.object.select_all(action='DESELECT')
                # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')

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


class TEST_OT_deleteventcanal(bpy.types.Operator):
    bl_idname = "object.deleteventcanal"
    bl_label = "deleteventcanal"
    bl_description = "双击删除管道控制点"

    def excute(self, context, event):

        global object_dic
        global object_dicL
        sphere_number = on_which_shpere(context, event)
        name = bpy.context.scene.leftWindowObj
        if sphere_number == 0:
            pass

        elif sphere_number == 1 or sphere_number == 2:
            pass

        else:
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
                global number
                count = number - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'ventcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'ventcanalsphere' + str(sphere_number + i)
                        object_dic.update({replace_name: object_dic.pop(old_name)})
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
                global numberL
                count = numberL - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        old_name = name + 'soundcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'soundcanalsphere' + str(sphere_number + i)
                        object_dicL.update({replace_name: object_dicL.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                numberL -= 1
                convert_ventcanal()
                save_ventcanal_info([0, 0, 0])

            # 删除可能存在的圆球平面
            delete_sphere_snap_plane()


    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_ventcanalqiehuan(bpy.types.Operator):
    bl_idname = "object.ventcanalqiehuan"
    bl_label = "ventcanalqiehuan"
    bl_description = "鼠标行为切换"

    __timer = None

    def invoke(self, context, event):  # 初始化
        print('ventcanalqiehuan invoke')
        initialTransparency()
        newColor('red', 1, 0, 0, 0, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)  # 不透明材质
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)  # 透明材质
        if not TEST_OT_ventcanalqiehuan.__timer:
            TEST_OT_ventcanalqiehuan.__timer = context.window_manager.event_timer_add(0.02, window=context.window)
        context.window_manager.modal_handler_add(self)
        bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
        bpy.context.scene.var = 26
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global object_dic
        global object_dicL
        op_cls = TEST_OT_ventcanalqiehuan
        name = bpy.context.scene.leftWindowObj
        object_dic_cur = None

        mouse_x = event.mouse_x
        mouse_y = event.mouse_y
        override1 = getOverride()
        area = override1['area']

        # 鼠标在3D区域内
        if(mouse_x < area.width and area.y < mouse_y < area.y+area.height and bpy.context.scene.var == 26):

            if (name == "右耳"):
                object_dic_cur = object_dic
            elif (name == "左耳"):
                object_dic_cur = object_dicL

            if context.area:
                context.area.tag_redraw()

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
                mouse_switch(context, event)

                # 生成管道中间红球对应的平面
                plane_switch(sphere_number)

                # 鼠标位于管道或圆球上的时候,改变管道的材质,将其亮度调高
                if cal_co(name + 'meshventcanal', context, event) == -1:
                    if is_changed_soundcanal(context, event) == True:
                        bpy.data.objects[name + 'meshventcanal'].data.materials.clear()
                        bpy.data.objects[name + 'meshventcanal'].data.materials.append(bpy.data.materials["grey"])
                elif cal_co(name + 'meshventcanal', context, event) != -1:
                    if is_changed_soundcanal(context, event) == True:
                        bpy.data.objects[name + 'meshventcanal'].data.materials.clear()
                        bpy.data.objects[name + 'meshventcanal'].data.materials.append(bpy.data.materials["grey2"])

                # 实时更新管道控制点的位置,随圆球位置更新而改变
                # 若鼠标不在圆球上
                if sphere_number == 0:
                    return {'PASS_THROUGH'}
                # 鼠标位于其他控制圆球上的时候,管道控制点随着圆球位置的拖动改变而更新
                else:
                    sphere_name = name + 'ventcanalsphere' + str(sphere_number)
                    obj = bpy.data.objects[sphere_name]
                    index = int(object_dic_cur[sphere_name])
                    bpy.data.objects[name + 'ventcanal'].data.splines[0].points[index].co[0:3] = \
                        bpy.data.objects[sphere_name].location
                    bpy.data.objects[name + 'ventcanal'].data.splines[0].points[index].co[3] = 1
                    flag = save_ventcanal_info(obj.location)
                    if flag:
                        convert_ventcanal()
                    return {'PASS_THROUGH'}

            return {'PASS_THROUGH'}

        # 模式切换，结束modal
        elif(bpy.context.scene.var != 26):
            if op_cls.__timer:
                    context.window_manager.event_timer_remove(TEST_OT_ventcanalqiehuan.__timer)
                    op_cls.__timer = None
                    print('ventcanalqiehuan finish')
            return {'FINISHED'}
        
        # 鼠标在区域外
        else:
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


class TEST_OT_finishventcanal(bpy.types.Operator):
    bl_idname = "object.finishventcanal"
    bl_label = "完成操作"
    bl_description = "点击按钮完成管道制作"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 27
        return {'FINISHED'}

    def excute(self, context, event):
        submit_ventcanal()
        global ventcanal_finish
        global ventcanal_finishL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            ventcanal_finish = True
        elif (name == "左耳"):
            ventcanal_finishL = True



class TEST_OT_resetventcanal(bpy.types.Operator):
    bl_idname = "object.resetventcanal"
    bl_label = "重置操作"
    bl_description = "点击按钮重置管道制作"

    def invoke(self, context, event):
        bpy.context.scene.var = 28
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        # 删除多余的物体
        global object_dic
        global object_dicL
        global ventcanal_finish
        global ventcanal_finishL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            if not ventcanal_finish:
                need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                                  name + 'VentCanalPlaneBorderCurveObject', name + 'VentCanalPlane']
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
                bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
        elif (name == "左耳"):
            if not ventcanal_finishL:
                need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                                  name + 'VentCanalPlaneBorderCurveObject', name + 'VentCanalPlane']
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
                bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')



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
    convert_ventcanal()
    save_ventcanal_info(co)
    curve_object.hide_set(True)
    bpy.data.objects[name].hide_select = True
    # bpy.context.view_layer.objects.active = curve_object
    # bpy.ops.object.select_all(action='DESELECT')
    # curve_object.select_set(state=True)
    # bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式
    # bpy.ops.curve.select_all(action='DESELECT')
    # curve_data.splines[0].points[0].select = True
    # curve_data.splines[0].points[1].select = True
    # bpy.ops.curve.subdivide(number_cuts=1)  # 细分次数
    # bpy.ops.object.mode_set(mode='OBJECT')  # 返回对象模式
    # add_sphere(co, 2)
    # temp_co = curve_data.splines[0].points[1].co[0:3]
    # add_sphere(temp_co, 1)
    # convert_ventcanal()
    # save_ventcanal_info(temp_co)


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
        initialTransparency()
        newColor('red', 1, 0, 0, 1, 0.8)
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
            obj.location = bpy.data.objects[name + 'ventcanal'].data.splines[0].points[object_dic_cur[key]].co[0:3]  # 指定的位置坐标

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["Transparency"])
        bpy.data.objects[name].hide_select = True
        convert_ventcanal()
        save_ventcanal_info([0, 0, 0])
        bpy.data.objects[name + 'ventcanal'].hide_set(True)

    elif len(object_dic_cur) == 1:  # 只点击了一次
        newColor('red', 1, 0, 0, 1, 0.8)
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
        obj.location = ventcanal_data_cur[0:3]  # 指定的位置坐标

    else:  # 不存在已保存的圆球位置
        pass

    bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')


def submit_ventcanal():
    # 应用修改器，删除多余的物体
    global object_dic
    global object_dicL
    global ventcanal_finish
    global ventcanal_finishL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        if len(object_dic) > 0 and ventcanal_finish == False:
            adjustpoint()
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bool_modifier = bpy.context.active_object.modifiers.new(
                name="Ventcanal Boolean Modifier", type='BOOLEAN')
            bool_modifier.operation = 'DIFFERENCE'
            bool_modifier.object = bpy.data.objects[name + 'meshventcanal']
            bpy.ops.object.modifier_apply(modifier="Ventcanal Boolean Modifier", single_user=True)
            need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                              name + 'VentCanalPlaneBorderCurveObject', name + 'VentCanalPlane']
            for key in object_dic:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            apply_material()
            utils_re_color(name, (1, 0.319, 0.133))
            bpy.context.active_object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 0.9
            bpy.data.objects[name].hide_select = False
    elif (name == "左耳"):
        if len(object_dicL) > 0 and ventcanal_finishL == False:
            adjustpoint()
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bool_modifier = bpy.context.active_object.modifiers.new(
                name="Ventcanal Boolean Modifier", type='BOOLEAN')
            bool_modifier.operation = 'DIFFERENCE'
            bool_modifier.object = bpy.data.objects[name + 'meshventcanal']
            bpy.ops.object.modifier_apply(modifier="Ventcanal Boolean Modifier", single_user=True)
            need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                              name + 'VentCanalPlaneBorderCurveObject', name + 'VentCanalPlane']
            for key in object_dicL:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            apply_material()
            utils_re_color(name, (1, 0.319, 0.133))
            bpy.context.active_object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 0.9
            bpy.data.objects[name].hide_select = False



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


def frontFromVentCanal():
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    save_ventcanal_info([0, 0, 0])
    need_to_delete_model_name_list = [name + 'meshventcanal', name + 'ventcanal',
                                      name + 'VentCanalPlaneBorderCurveObject', name + 'VentCanalPlane']
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
    handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (label_obj != None):
        bpy.data.objects.remove(label_obj, do_unlink=True)
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


def backFromVentCanal():
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


class addventcanal_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addventcanal2"
    bl_label = "通气孔添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作"
    )
    bl_icon = "ops.curve.extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("object.addventcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class addventcanal_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addventcanal3"
    bl_label = "通气孔对圆球操作"
    bl_description = (
        "通气孔对圆球移动、双击操作"
    )
    bl_icon = "ops.curve.draw"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, None),
        ("object.deleteventcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class finishventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishventcanal"
    bl_label = "通气孔完成"
    bl_description = (
        "完成管道的绘制"
    )
    bl_icon = "ops.curve.extrude_move"
    bl_widget = None
    bl_keymap = (
        ("object.finishventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetventcanal"
    bl_label = "通气孔重置"
    bl_description = (
        "重置管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_snake_hook"
    bl_widget = None
    bl_keymap = (
        ("object.resetventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrorventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrorventcanal"
    bl_label = "通气孔镜像"
    bl_description = (
        "点击镜像通气孔"
    )
    bl_icon = "ops.curve.radius"
    bl_widget = None
    bl_keymap = (
        ("object.mirrorventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


_classes = [
    TEST_OT_addventcanal,
    TEST_OT_deleteventcanal,
    TEST_OT_ventcanalqiehuan,
    TEST_OT_finishventcanal,
    TEST_OT_resetventcanal
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_tool(resetventcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishventcanal_MyTool, separator=True, group=False,
                            after={resetventcanal_MyTool.bl_idname})
    bpy.utils.register_tool(mirrorventcanal_MyTool, separator=True, group=False,
                            after={finishventcanal_MyTool.bl_idname})

    bpy.utils.register_tool(addventcanal_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(addventcanal_MyTool3, separator=True, group=False)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)

    bpy.utils.unregister_tool(resetventcanal_MyTool)
    bpy.utils.unregister_tool(finishventcanal_MyTool)
    bpy.utils.unregister_tool(mirrorventcanal_MyTool)

    bpy.utils.unregister_tool(addventcanal_MyTool2)
    bpy.utils.unregister_tool(addventcanal_MyTool3)