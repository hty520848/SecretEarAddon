import bpy
import bmesh
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
from math import sqrt
from ... tool import newShader, moveToRight, moveToLeft, utils_re_color, delete_useless_object, newColor, \
    getOverride, apply_material, transform_normal, newMaterial
from ... parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running
import re
import os
import time
from ..collision import update_cube_location_rotate, setActiveAndMoveCubeName, resetCubeLocationAndRotation

prev_on_sphere = False
prev_on_sphereL = False
prev_on_object = False
prev_on_objectL = False
number = 0                       # 记录管道控制点点的个数
numberL = 0
object_dic = {}                  # 记录当前圆球以及对应控制骨骼平面
object_dicL = {}
shellcanal_data = []             # 记录当前显示红球的坐标
shellcanal_dataL = []
shellcanal_finish = False
shellcanal_finishL = False


# mouse_index = 0                   #添加传声孔之后,切换其存在的鼠标行为,记录当前在切换到了哪种鼠标行为
# mouse_indexL = 0


# is_mouseSwitch_modal_start = False         #在启动下一个modal前必须将上一个modal关闭,防止modal开启过多过于卡顿
# is_mouseSwitch_modal_startL = False

add_or_delete = False             # 执行添加或删除红球的过程中,暂停qiehuan modal的检测执行
add_or_deleteL = False


# 新建与RGB颜色相同的材质
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


def initialPlaneTransparency():
    mat = newColor("PlaneTransparency", 1, 0.319, 0.133, 1, 0.4)  # 创建材质
    mat.use_backface_culling = False


def getObjectDic():
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        return object_dic
    elif name == '左耳':
        return object_dicL


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
    #在显示红球字典中添加对应的透明红球名称
    sphere_name_list = []
    for key in object_dic_cur:
        sphere_name = key
        object_index = int(key.replace(name + 'shellcanalsphere', ''))
        transparency_sphere_name = name + 'shellcanalsphere' + str(200 + object_index)
        sphere_name_list.append(sphere_name)
        sphere_name_list.append(transparency_sphere_name)
    # 鼠标是否在管道的红球上
    for key in sphere_name_list:
        active_obj = bpy.data.objects[key]
        object_index = int(key.replace(name + 'shellcanalsphere', ''))
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
    :return: 相交的坐标与法线方向
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

            co, normal, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None:
                return co,-normal  # 如果发生交叉，返回坐标的值和法线方向

    return -1,-1


def select_nearest_point(co):
    '''
    选择曲线上离坐标位置最近的两个点
    :param co: 坐标的值
    :return: 最近两个点的坐标以及要插入的下标
    '''
    global number
    global numberL
    name = bpy.context.scene.leftWindowObj
    number_cur = None
    if (name == "右耳"):
        number_cur = number
    elif (name == "左耳"):
        number_cur = numberL
    min_dis = float('inf')
    min_dis_index = -1                #骨骼控制点平面名称的后缀
    #获取距离当前位置最近的控制平面的索引
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                distance_vector = Vector(obj.location[0:3]) - co
                distance = distance_vector.dot(distance_vector)
                # 更新最小距离和对应的点索引
                if distance < min_dis:
                    min_dis = distance
                    min_dis_index = plane_index
        elif (name == "左耳"):
            pattern = r'左耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                distance_vector = Vector(obj.location[0:3]) - co
                distance = distance_vector.dot(distance_vector)
                # 更新最小距离和对应的点索引
                if distance < min_dis:
                    min_dis = distance
                    min_dis_index = plane_index
    #获取相关控制平面
    shell_canal_armature_plane_min_co_name = name + 'shellCanalArmaturePlane' + str(min_dis_index)
    shell_canal_armature_plane_minco_obj = bpy.data.objects.get(shell_canal_armature_plane_min_co_name)
    shell_canal_armature_plane_prev_min_co_name = name + 'shellCanalArmaturePlane' + str(min_dis_index - 1)
    shell_canal_armature_plane_prev_min_co_obj = bpy.data.objects.get(shell_canal_armature_plane_prev_min_co_name)



    if min_dis_index == 1:
        return  2

    elif min_dis_index == number_cur:
        return  number_cur

    min_co = shell_canal_armature_plane_minco_obj.location                    #距离插入位置最近控制点的坐标
    secondmin_co = shell_canal_armature_plane_prev_min_co_obj.location        #距离插入位置最近控制点的上一个控制点的坐标
    dis_vector1 = Vector(secondmin_co - co)
    dis_vector2 = Vector(min_co - co)
    #点积小于0则说明插入位置位于 最近控制点与上一个控制点之间,反之则位于最近控制点与下一个控制点之间
    if dis_vector1.dot(dis_vector2) < 0:
        insert_index = min_dis_index
    else:
        insert_index = min_dis_index + 1
    return insert_index


def hooktoobject(index):
    ''' 建立红球名称到骨骼控制平面后缀索引的字典 '''
    global number
    global numberL
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        sphere_name = name + 'shellcanalsphere' + str(number)
        object_dic.update({sphere_name: index})
    elif (name == "左耳"):
        sphere_name = name + 'shellcanalsphere' + str(numberL)
        object_dicL.update({sphere_name: index})



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
        mesh = bpy.data.meshes.new(name + "shellcanalsphere")
        name1 = name + 'shellcanalsphere' + str(number)
    elif (name == "左耳"):
        numberL += 1
        mesh = bpy.data.meshes.new(name + "shellcanalsphere")
        name1 = name + 'shellcanalsphere' + str(numberL)

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
    radius = 0.25  # 半径
    segments = 32  # 分段数
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
    bm.to_mesh(me)
    bm.free()
    newColor('shellcanalSphereRed', 1, 0, 0, 0, 1)
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['shellcanalSphereRed'])

    # 设置圆球的位置
    obj.location = co  # 指定的位置坐标
    hooktoobject(index)  # 绑定到指定下标


def save_shellcanal_info():
    global number
    global numberL
    global object_dic
    global object_dicL
    global shellcanal_data
    global shellcanal_dataL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        shellcanal_data = []
        for index in range(number):
            shell_canal_sphere_name = name + "shellcanalsphere" + str(index + 1)
            shell_canal_sphere_obj = bpy.data.objects.get(shell_canal_sphere_name)
            point_co = shell_canal_sphere_obj.location
            shellcanal_data.append(round(point_co[0], 3))
            shellcanal_data.append(round(point_co[1], 3))
            shellcanal_data.append(round(point_co[2], 3))
    elif (name == "左耳"):
        shellcanal_dataL = []
        for index in range(numberL):
                shell_canal_sphere_name = name + "shellcanalsphere" + str(index + 1)
                shell_canal_sphere_obj = bpy.data.objects.get(shell_canal_sphere_name)
                point_co = shell_canal_sphere_obj.location
                shellcanal_dataL.append(round(point_co[0], 3))
                shellcanal_dataL.append(round(point_co[1], 3))
                shellcanal_dataL.append(round(point_co[2], 3))



def mouse_switch(sphere_number):
    '''
    鼠标位于不同的物体上时,切换到不同的传声孔鼠标行为
    '''
    global mouse_index
    global mouse_indexL
    name = bpy.context.scene.leftWindowObj
    if(name == '右耳'):
        if(sphere_number == 0 and mouse_index != 1):
            mouse_index = 1
            # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.public_add_shellcanal")
        elif(sphere_number != 0 and mouse_index != 2):
            mouse_index = 2
            #将显示红球映射为透明红球
            if(sphere_number < 100):
                sphere_number = 200 + sphere_number
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            sphere_name = name + 'shellcanalsphere' + str(sphere_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.delete_drag_shellcanal")
    elif(name == '左耳'):
        if (sphere_number == 0 and mouse_indexL != 1):
            mouse_indexL = 1
            # 鼠标不再圆球上的时候，调用传声孔的鼠标行为1,公共鼠标行为 双击添加圆球
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[name]
            bpy.data.objects[name].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="my_tool.public_add_shellcanal")
        elif (sphere_number != 0 and mouse_indexL != 2):
            mouse_indexL = 2
            # 将显示红球映射为透明红球
            if (sphere_number < 100):
                sphere_number = 200 + sphere_number
            # 鼠标位于管道圆球上的时候,调用传声孔的鼠标行为2,双击删除圆球，左键按下激活并拖动圆球
            sphere_name = name + 'shellcanalsphere' + str(sphere_number)
            sphere_obj = bpy.data.objects.get(sphere_name)
            bpy.ops.object.select_all(action='DESELECT')
            sphere_obj.select_set(True)
            bpy.context.view_layer.objects.active = sphere_obj
            bpy.ops.wm.tool_set_by_id(name="my_tool.delete_drag_shellcanal")


def updateshellCanalState():
    name = bpy.context.scene.leftWindowObj
    useShellCanal = True
    if (name == "右耳"):
        useShellCanal = bpy.context.scene.useShellCanalR
        sphere_pattern = r'右耳shellcanalsphere'
        plane_pattern = r'右耳shellCanalArmaturePlane'
        for obj in bpy.data.objects:
            if re.match(sphere_pattern, obj.name) or re.match(plane_pattern, obj.name):
                obj.hide_set(not useShellCanal)
    elif (name == "左耳"):
        useShellCanal = bpy.context.scene.useShellCanalL
        sphere_pattern = r'左耳shellcanalsphere'
        plane_pattern = r'左耳shellCanalArmaturePlane'
        for obj in bpy.data.objects:
            if re.match(sphere_pattern, obj.name) or re.match(plane_pattern, obj.name):
                obj.hide_set(not useShellCanal)

    armature_name = name + "shellCanalArmature"
    armature_obj = bpy.data.objects.get(armature_name)
    shellinnercanal = bpy.data.objects.get(name + 'shellinnercanal')
    shelloutercanal = bpy.data.objects.get(name + 'shelloutercanal')
    meshshelloutercanal = bpy.data.objects.get(name + 'meshshelloutercanal')
    if(armature_obj != None):
        armature_obj.hide_set(not useShellCanal)
    if (shellinnercanal != None):
        shellinnercanal.hide_set(not useShellCanal)
    if (shelloutercanal != None):
        shelloutercanal.hide_set(not useShellCanal)
    if(meshshelloutercanal != None):
        meshshelloutercanal.hide_set(not useShellCanal)


def updateshellCanalDiameter():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        diameter = bpy.context.scene.shellCanalDiameterR / 2
        thickness = bpy.context.scene.shellCanalThicknessR / 2
    elif name == '左耳':
        diameter = bpy.context.scene.shellCanalDiameterL / 2
        thickness = bpy.context.scene.shellCanalThicknessL / 2
    shell_inner_name = name + "shellinnercanal"
    shell_inner_obj = bpy.data.objects.get(shell_inner_name)
    shell_outer_name = name + "shelloutercanal"
    shell_outer_obj = bpy.data.objects.get(shell_outer_name)
    if(shell_inner_obj != None and shell_outer_obj != None):
        # 重置骨骼平面控制点的位置,将管道恢复为原始状态
        for obj in bpy.data.objects:
            if (name == "右耳"):
                pattern = r'右耳shellCanalArmaturePlane'
                if re.match(pattern, obj.name):
                    plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                    obj.rotation_euler[0] = 0
                    obj.rotation_euler[1] = 0
                    obj.rotation_euler[2] = 0
                    obj.location[0] = 0
                    obj.location[1] = 0
                    obj.location[2] = 0.1 + (plane_index - 1) * 5.2
            elif (name == "左耳"):
                pattern = r'左耳shellCanalArmaturePlane'
                if re.match(pattern, obj.name):
                    plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                    obj.rotation_euler[0] = 0
                    obj.rotation_euler[1] = 0
                    obj.rotation_euler[2] = 0
                    obj.location[0] = 0
                    obj.location[1] = 0
                    obj.location[2] = 0.1 + (plane_index - 1) * 5.2
        #更新内外管道的直径
        shell_inner_obj.scale[0] = diameter
        shell_inner_obj.scale[1] = diameter
        shell_outer_obj.scale[0] = diameter + thickness
        shell_outer_obj.scale[1] = diameter + thickness
        # 更新管道控制平面的位置
        updateArmaturePlaneLocationAndNormal()
        updateMeshOutShellCanal()



def updateshellCanalThickness():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        diameter = bpy.context.scene.shellCanalDiameterR / 2
        thickness = bpy.context.scene.shellCanalThicknessR / 2
    elif name == '左耳':
        diameter = bpy.context.scene.shellCanalDiameterL / 2
        thickness = bpy.context.scene.shellCanalThicknessL / 2
    shell_outer_name = name + "shelloutercanal"
    shell_outer_obj = bpy.data.objects.get(shell_outer_name)
    if (shell_outer_obj != None):
        # 重置骨骼平面控制点的位置,将管道恢复为原始状态
        for obj in bpy.data.objects:
            if (name == "右耳"):
                pattern = r'右耳shellCanalArmaturePlane'
                if re.match(pattern, obj.name):
                    plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                    obj.rotation_euler[0] = 0
                    obj.rotation_euler[1] = 0
                    obj.rotation_euler[2] = 0
                    obj.location[0] = 0
                    obj.location[1] = 0
                    obj.location[2] = 0.1 + (plane_index - 1) * 5.2
            elif (name == "左耳"):
                pattern = r'左耳shellCanalArmaturePlane'
                if re.match(pattern, obj.name):
                    plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                    obj.rotation_euler[0] = 0
                    obj.rotation_euler[1] = 0
                    obj.rotation_euler[2] = 0
                    obj.location[0] = 0
                    obj.location[1] = 0
                    obj.location[2] = 0.1 + (plane_index - 1) * 5.2
        #调整外管道直径
        shell_outer_obj.scale[0] = diameter + thickness
        shell_outer_obj.scale[1] = diameter + thickness
        #更新管道控制平面的位置
        updateArmaturePlaneLocationAndNormal()
        updateMeshOutShellCanal()



def updateshellCanalOffset():
    updateArmaturePlaneLocationAndNormal()
    updateMeshOutShellCanal()




def updateArmaturePlaneLocationAndNormal():
    '''
    根据红球位置和面板offset参数计算骨骼控制点的位置,并将骨骼控制平面的位置设置为骨骼控制点的位置
    根据当前红球控制平面的上一个平面或者下一个平面的位置调整当前平面的角度
    '''
    global number
    global numberL
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        shellcanal_offset = bpy.context.scene.shellCanalOffsetR
    else:
        shellcanal_offset = bpy.context.scene.shellCanalOffsetL
    cur_obj = bpy.data.objects.get(name)
    #更新管道控制平面位置
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                for key in object_dic:
                    if(object_dic[key] == plane_index):
                        sphere_name = key
                        break
                sphere_obj = bpy.data.objects.get(sphere_name)
                if(sphere_obj != None):
                    sphere_co = sphere_obj.location
                    _, _, normal, _ = cur_obj.closest_point_on_mesh(sphere_co)
                    if (plane_index == 1 or plane_index == number):
                        plane_co = sphere_co
                    else:
                        plane_co = sphere_co - normal.normalized() * shellcanal_offset
                    obj.location = plane_co
        elif (name == "左耳"):
            pattern = r'左耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                for key in object_dicL:
                    if (object_dicL[key] == plane_index):
                        sphere_name = key
                        break
                sphere_obj = bpy.data.objects.get(sphere_name)
                if (sphere_obj != None):
                    sphere_co = sphere_obj.location
                    _, _, normal, _ = cur_obj.closest_point_on_mesh(sphere_co)
                    if (plane_index == 1 or plane_index == numberL):
                        plane_co = sphere_co
                    else:
                        plane_co = sphere_co - normal.normalized() * shellcanal_offset
                    obj.location = plane_co
    # 更新管道控制平面旋转角度
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                if (plane_index == 1):
                    next_plane_name = name + 'shellCanalArmaturePlane' + str(2)
                    next_plane_obj = bpy.data.objects.get(next_plane_name)
                    normal = (next_plane_obj.location - obj.location).normalized()
                elif(plane_index == number):
                    prev_plane_name = name + 'shellCanalArmaturePlane' + str(number - 1)
                    prev_plane_obj = bpy.data.objects.get(prev_plane_name)
                    normal = (obj.location - prev_plane_obj.location).normalized()
                else:
                    prev_plane_name = name + 'shellCanalArmaturePlane' + str(plane_index - 1)
                    prev_plane_obj = bpy.data.objects.get(prev_plane_name)
                    next_plane_name = name + 'shellCanalArmaturePlane' + str(plane_index + 1)
                    next_plane_obj = bpy.data.objects.get(next_plane_name)
                    normal = (next_plane_obj.location - prev_plane_obj.location).normalized()
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
                # 将控制平面摆正为法线方向
                obj.rotation_euler[0] = empty_rotation_x
                obj.rotation_euler[1] = empty_rotation_y
                obj.rotation_euler[2] = empty_rotation_z
        elif (name == "左耳"):
            pattern = r'左耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                if (plane_index == 1):
                    next_plane_name = name + 'shellCanalArmaturePlane' + str(2)
                    next_plane_obj = bpy.data.objects.get(next_plane_name)
                    normal = (next_plane_obj.location - obj.location).normalized()
                elif (plane_index == numberL):
                    prev_plane_name = name + 'shellCanalArmaturePlane' + str(numberL - 1)
                    prev_plane_obj = bpy.data.objects.get(prev_plane_name)
                    normal = (obj.location - prev_plane_obj.location).normalized()
                else:
                    prev_plane_name = name + 'shellCanalArmaturePlane' + str(plane_index - 1)
                    prev_plane_obj = bpy.data.objects.get(prev_plane_name)
                    next_plane_name = name + 'shellCanalArmaturePlane' + str(plane_index + 1)
                    next_plane_obj = bpy.data.objects.get(next_plane_name)
                    normal = (next_plane_obj.location - prev_plane_obj.location).normalized()
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
                # 将控制平面摆正为法线方向
                obj.rotation_euler[0] = empty_rotation_x
                obj.rotation_euler[1] = empty_rotation_y
                obj.rotation_euler[2] = empty_rotation_z

def updateMeshOutShellCanal():
    '''
    更新网格外壳外管道物体(外壳外管道需要使用骨骼修改器随骨骼位置改变而形变,未应用骨骼修改器之前其顶点位置并未改变)
    '''
    name = bpy.context.scene.leftWindowObj
    shell_outer_canal_obj = bpy.data.objects.get(name + 'shelloutercanal')
    if(shell_outer_canal_obj != None):
        mesh_outer_shellcanal_obj = bpy.data.objects.get(name + 'meshshelloutercanal')
        if(mesh_outer_shellcanal_obj != None):
            bpy.data.objects.remove(mesh_outer_shellcanal_obj, do_unlink=True)
        mesh_outer_shellcanal_obj = shell_outer_canal_obj.copy()
        mesh_outer_shellcanal_obj.data = shell_outer_canal_obj.data.copy()
        mesh_outer_shellcanal_obj.animation_data_clear()
        mesh_outer_shellcanal_obj.name = name + 'meshshelloutercanal'
        newColor('shellMeshOutercanalTransparency', 0.8, 0.8, 0.8, 1, 0.03)
        mesh_outer_shellcanal_obj.data.materials.clear()
        mesh_outer_shellcanal_obj.data.materials.append(bpy.data.materials['shellMeshOutercanalTransparency'])
        bpy.context.scene.collection.objects.link(mesh_outer_shellcanal_obj)
        if name == '右耳':
            moveToRight(mesh_outer_shellcanal_obj)
        elif name == '左耳':
            moveToLeft(mesh_outer_shellcanal_obj)
        # 应用复制出的网格管道的骨骼修改器
        active_obj = bpy.context.active_object
        mesh_outer_shellcanal_obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_outer_shellcanal_obj
        bpy.ops.object.modifier_apply(modifier="Armature", single_user=True)
        if(active_obj != None):
            active_obj.select_set(True)
            bpy.context.view_layer.objects.active = active_obj
            mesh_outer_shellcanal_obj.select_set(False)



def createArmature():
    '''
    创建有number个控制结点的柔性骨骼,number是红球的数量
    '''
    global number
    global numberL
    name = bpy.context.scene.leftWindowObj
    number_cur = None
    if (name == "右耳"):
        number_cur = number
    elif (name == "左耳"):
        number_cur = numberL
    #将原先存在的骨骼和骨骼结点控制平面删除
    armature_name = name + "shellCanalArmature"
    armature_obj = bpy.data.objects.get(armature_name)
    if(armature_obj != None):
        bpy.data.objects.remove(armature_obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    #添加骨架控制结点绑定的平面,将骨骼结点与平面绑定,使得在物体模式下能够通过控制平面的位置与旋转方向控制骨骼控制点,进而控制骨骼姿态
    newColor('shellCanalArmaturePlaneTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    for i in range(number_cur):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        plane_obj = bpy.context.active_object
        plane_obj.name = name + "shellCanalArmaturePlane" + str(i+1)
        plane_obj.location[2] = 0.1 + i * (5.2)           #骨骼控制点的高低为0.2,0.1为其高度的一半,5.2则是骨骼控制点与骨骼体的总高度
        plane_obj.data.materials.clear()
        plane_obj.data.materials.append(bpy.data.materials["shellCanalArmaturePlaneTransparency"])
        if (name == "右耳"):
            moveToRight(plane_obj)
        elif (name == "左耳"):
            moveToLeft(plane_obj)
    #添加一个骨架,初始高度为0.2
    bpy.ops.object.armature_add(radius=0.2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    armature_name = "Armature"
    armature_obj = bpy.data.objects.get(armature_name)
    if (name == "右耳"):
        moveToRight(armature_obj)
    elif (name == "左耳"):
        moveToLeft(armature_obj)
    if armature_obj and armature_obj.type == 'ARMATURE':
        #number_cur-1个骨骼结点和骨骼体并为其重命名(骨骼结点高度为0.2,骨骼体高度为5),通过后续设置可使得骨骼体随骨骼结点位置和旋转信息的改变而改变
        bpy.ops.object.mode_set(mode='EDIT')
        for i in range(number_cur -1):
            bpy.ops.armature.extrude_move(TRANSFORM_OT_translate={"value": (0, 0, 5)})
            bpy.ops.armature.extrude_move(TRANSFORM_OT_translate={"value": (0, 0, 0.2)})
        bpy.ops.object.mode_set(mode='OBJECT')

        # 为骨架和骨骼控制点重名名
        armature_obj.name = name + "shellCanalArmature"
        boneCTR = armature_obj.data.bones.get("Bone")       #第一个骨骼控制点
        boneCTR.name = name + "shellCanalArmatureCTR1"
        for bone in armature_obj.data.bones:
            bone_name = bone.name
            if (bone_name != name + "shellCanalArmatureCTR1"):
                if re.match(r'Bone.00', bone.name):                    #前10个骨骼结点名称或骨骼结点数量小于10
                    index = int(bone_name.replace('Bone.00', ''))
                else:                                                  #骨骼结点数量大于10个时,后续的默认骨骼结点名称,如Bone.012的index为12
                    index = int(bone_name.replace('Bone.0', ''))
                if (index % 2 == 0):
                    bone.name = name + "shellCanalArmatureCTR" + str(int(index / 2) + 1)
                else:
                    bone.name = name + "shellCanalArmatureBody" + str(int((index + 1) / 2))


        #切换到柔性骨骼模式,清空骨骼结点的父级并将骨骼体端数设置为32
        bpy.ops.object.select_all(action='DESELECT')
        armature_obj.select_set(True)
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.object.data.display_type = 'BBONE'
        for bone in armature_obj.data.edit_bones:
            if (name == "右耳"):
                patternCTR = r'右耳shellCanalArmatureCTR'
                patternBody = r'右耳shellCanalArmatureBody'
                if re.match(patternCTR, bone.name):
                    bpy.ops.armature.select_all(action='DESELECT')
                    bone.select = True
                    armature_obj.data.edit_bones.active = bone
                    bpy.ops.armature.parent_clear(type='CLEAR') #清空所有的骨骼结点的父级
                    bpy.context.active_bone.use_deform = False  #将骨骼控制点的形变属性设置为False
                elif re.match(patternBody, bone.name):
                    body_index = int(bone.name.replace(name + 'shellCanalArmatureBody', ''))
                    prev_armatrue_CTR_name = name + "shellCanalArmatureCTR" + str(body_index)
                    prev_armatrue_CTR = armature_obj.data.edit_bones.get(prev_armatrue_CTR_name)
                    next_armatrue_CTR_name = name + "shellCanalArmatureCTR" + str(body_index + 1)
                    next_armatrue_CTR = armature_obj.data.edit_bones.get(next_armatrue_CTR_name)
                    bone.bbone_segments = 32                    #将骨骼体段数设置为32
                    bone.bbone_handle_type_start = 'ABSOLUTE'   #为骨骼体添加起始与结束控制柄
                    bone.bbone_custom_handle_start = prev_armatrue_CTR
                    bone.bbone_handle_type_end = 'ABSOLUTE'
                    bone.bbone_custom_handle_end = next_armatrue_CTR
            elif (name == "左耳"):
                patternCTR = r'左耳shellCanalArmatureCTR'
                patternBody = r'左耳shellCanalArmatureBody'
                if re.match(patternCTR, bone.name):
                    bpy.ops.armature.select_all(action='DESELECT')
                    bone.select = True
                    armature_obj.data.edit_bones.active = bone
                    bpy.ops.armature.parent_clear(type='CLEAR')  #清空所有的骨骼结点的父级
                    bpy.context.active_bone.use_deform = False   #将骨骼控制点的形变属性设置为False
                elif re.match(patternBody, bone.name):
                    body_index = int(bone.name.replace(name + 'shellCanalArmatureBody', ''))
                    prev_armatrue_CTR_name = name + "shellCanalArmatureCTR" + str(body_index)
                    prev_armatrue_CTR = armature_obj.data.edit_bones.get(prev_armatrue_CTR_name)
                    next_armatrue_CTR_name = name + "shellCanalArmatureCTR" + str(body_index + 1)
                    next_armatrue_CTR = armature_obj.data.edit_bones.get(next_armatrue_CTR_name)
                    bone.bbone_segments = 32                     #将骨骼体段数设置为32
                    bone.bbone_handle_type_start = 'ABSOLUTE'    #为骨骼体添加起始与结束控制柄
                    bone.bbone_custom_handle_start = prev_armatrue_CTR
                    bone.bbone_handle_type_end = 'ABSOLUTE'
                    bone.bbone_custom_handle_end = next_armatrue_CTR
            bpy.ops.armature.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')


        #为骨骼体添加拉伸约束并将体积变化值设置为0,维持体积属性设置为无
        #为骨骼控制点添加子级约束将其与对应的控制点平面绑定
        bpy.ops.object.mode_set(mode='POSE')
        for bone in armature_obj.pose.bones:
            if (name == "右耳"):
                patternCTR = r'右耳shellCanalArmatureCTR'
                patternBody = r'右耳shellCanalArmatureBody'
                if re.match(patternCTR, bone.name):
                    CTR_index = int(bone.name.replace(name + 'shellCanalArmatureCTR', ''))
                    armatrue_plane_name = name + "shellCanalArmaturePlane" + str(CTR_index)
                    armatrue_plane_obj = bpy.data.objects.get(armatrue_plane_name)
                    child_of_constraint = bone.constraints.new(type='CHILD_OF')      #添加子级约束,将骨骼控制点设置为目标的子集
                    child_of_constraint.target = armatrue_plane_obj
                elif re.match(patternBody, bone.name):
                    body_index = int(bone.name.replace(name + 'shellCanalArmatureBody', ''))
                    next_armature_CTR_name = name + "shellCanalArmatureCTR" + str(body_index + 1)
                    stretch_to_constraint = bone.constraints.new(type='STRETCH_TO')    #添加拉伸约束
                    stretch_to_constraint.target = armature_obj
                    stretch_to_constraint.subtarget = next_armature_CTR_name
                    stretch_to_constraint.bulge = 0
                    stretch_to_constraint.volume = 'NO_VOLUME'

            elif (name == "左耳"):
                patternCTR = r'左耳shellCanalArmatureCTR'
                patternBody = r'左耳shellCanalArmatureBody'
                if re.match(patternCTR, bone.name):
                    CTR_index = int(bone.name.replace(name + 'shellCanalArmatureCTR', ''))
                    armatrue_plane_name = name + "shellCanalArmaturePlane" + str(CTR_index)
                    armatrue_plane_obj = bpy.data.objects.get(armatrue_plane_name)
                    child_of_constraint = bone.constraints.new(type='CHILD_OF')        #添加子级约束,将骨骼控制点设置为目标的子集
                    child_of_constraint.target = armatrue_plane_obj
                elif re.match(patternBody, bone.name):
                    body_index = int(bone.name.replace(name + 'shellCanalArmatureBody', ''))
                    next_armature_CTR_name = name + "shellCanalArmatureCTR" + str(body_index + 1)
                    stretch_to_constraint = bone.constraints.new(type='STRETCH_TO')     #添加拉伸约束
                    stretch_to_constraint.target = armature_obj
                    stretch_to_constraint.subtarget = next_armature_CTR_name
                    stretch_to_constraint.bulge = 0
                    stretch_to_constraint.volume = 'NO_VOLUME'
        bpy.ops.object.mode_set(mode='OBJECT')




def createShellCanal():
    '''
    根据当前面板管道直径和厚度参数的大小创建外壳内外管道并将其与骨骼绑定
    '''
    global number
    global numberL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        number_cur = number
        diameter = bpy.context.scene.shellCanalDiameterR / 2
        thickness = bpy.context.scene.shellCanalThicknessR / 2
    elif name == '左耳':
        number_cur = numberL
        diameter = bpy.context.scene.shellCanalDiameterL / 2
        thickness = bpy.context.scene.shellCanalThicknessL / 2
    depth = (0.1 + (number_cur - 1) * (5.2) )/21                             #圆柱管道初始高度为21,对应4段骨骼体,5个骨骼控制结点
    armature_name = name + "shellCanalArmature"
    armature_obj = bpy.data.objects.get(armature_name)
    shell_outer_name = name + "shelloutercanal"
    shell_outer_obj = bpy.data.objects.get(shell_outer_name)
    shell_inner_name = name + "shellinnercanal"
    shell_inner_obj = bpy.data.objects.get(shell_inner_name)
    # 删除原先存在的外壳管道
    if (shell_outer_obj != None):
        bpy.data.objects.remove(shell_outer_obj, do_unlink=True)
    if (shell_inner_obj != None):
        bpy.data.objects.remove(shell_inner_obj, do_unlink=True)
    #创建外壳外管道
    bpy.ops.object.select_all(action='DESELECT')
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))     #脚本文件目录是该文件的爷爷目录
    relative_path = os.path.join(script_dir, "stl\\shellcanal.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    shell_outer_canal_name = "shellcanal"
    shell_outer_canal_obj = bpy.data.objects.get(shell_outer_canal_name)
    shell_outer_canal_obj.scale[0] = diameter + thickness
    shell_outer_canal_obj.scale[1] = diameter + thickness
    shell_outer_canal_obj.scale[2] = depth
    shell_outer_canal_obj.name = name + "shelloutercanal"
    newColor('shellOuterCanalGrey', 0.8, 0.8, 0.8, 1, 0.4)
    shell_outer_canal_obj.data.materials.clear()
    shell_outer_canal_obj.data.materials.append(bpy.data.materials["shellOuterCanalGrey"])
    #创建外壳内管道
    bpy.ops.object.select_all(action='DESELECT')
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))  # 脚本文件目录是该文件的爷爷目录
    relative_path = os.path.join(script_dir, "stl\\shellcanal.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    shell_inner_canal_name = "shellcanal"
    shell_inner_canal_obj = bpy.data.objects.get(shell_inner_canal_name)
    shell_inner_canal_obj.scale[0] = diameter
    shell_inner_canal_obj.scale[1] = diameter
    shell_inner_canal_obj.scale[2] = depth
    shell_inner_canal_obj.name = name + "shellinnercanal"
    newColor('shellInnerCanalGrey', 0.8, 0.8, 0.8, 0, 1)
    shell_inner_canal_obj.data.materials.clear()
    shell_inner_canal_obj.data.materials.append(bpy.data.materials["shellInnerCanalGrey"])
    if (name == "右耳"):
        moveToRight(shell_outer_canal_obj)
        moveToRight(shell_inner_canal_obj)
    elif (name == "左耳"):
        moveToLeft(shell_outer_canal_obj)
        moveToLeft(shell_inner_canal_obj)
    #重置骨骼平面控制点的位置,将管道恢复为原始状态
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                obj.rotation_euler[0] = 0
                obj.rotation_euler[1] = 0
                obj.rotation_euler[2] = 0
                obj.location[0] = 0
                obj.location[1] = 0
                obj.location[2] = 0.1 + (plane_index - 1) * 5.2
        elif (name == "左耳"):
            pattern = r'左耳shellCanalArmaturePlane'
            if re.match(pattern, obj.name):
                plane_index = int(obj.name.replace(name + 'shellCanalArmaturePlane', ''))
                obj.rotation_euler[0] = 0
                obj.rotation_euler[1] = 0
                obj.rotation_euler[2] = 0
                obj.location[0] = 0
                obj.location[1] = 0
                obj.location[2] = 0.1 + (plane_index - 1) * 5.2
    #将管道设置为骨骼的子集并设置为自动权重,使管道随着骨骼的形变而形变
    bpy.ops.object.select_all(action='DESELECT')
    shell_outer_canal_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    bpy.ops.object.select_all(action='DESELECT')
    shell_inner_canal_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # shell_outer_armaturemodifier = shell_outer_canal_obj.modifiers.get("Armature")     #TODO  管道的骨骼修改器未被应用的情况下如何判断鼠标是否在管道上
    # shell_outer_armaturemodifier.show_in_editmode = True
    # shell_outer_armaturemodifier.show_on_cage = True
    # shell_inner_armaturemodifier = shell_inner_canal_obj.modifiers.get("Armature")
    # shell_inner_armaturemodifier.show_in_editmode = True
    # shell_inner_armaturemodifier.show_on_cage = True


def generate_canal(co):
    ''' 添加第一个红球 '''
    # 开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    # 添加红球并保存其位置信息
    add_sphere(co, 1)
    save_shellcanal_info()

    # 根据管道两端的红球复制出两个透明圆球,操作管道两端的时候,每次激活的都是这两个透明圆球,用于限制实际的两端管道红球和管道控制点在左右耳模型上
    name = bpy.context.scene.leftWindowObj
    sphere_name1 = name + 'shellcanalsphere' + '1'
    sphere_obj1 = bpy.data.objects.get(sphere_name1)
    duplicate_obj1 = sphere_obj1.copy()
    duplicate_obj1.data = sphere_obj1.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + 'shellcanalsphere' + '201'
    bpy.context.scene.collection.objects.link(duplicate_obj1)
    newColor('shellcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    duplicate_obj1.data.materials.clear()
    duplicate_obj1.data.materials.append(bpy.data.materials['shellcanalSphereTransparency'])
    duplicate_obj1.scale[0] = 1.5
    duplicate_obj1.scale[1] = 1.5
    duplicate_obj1.scale[2] = 1.5
    if name == '右耳':
        moveToRight(duplicate_obj1)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)




def add_canal(object_co, insert_index):
    '''
    在point_co处添加一个管道控制点,对应索引的insert_index
    在object_co添加红球控制点
    '''
    global number
    global numberL
    global object_dic
    global object_dicL
    name = bpy.context.scene.leftWindowObj

    # 更新后续红球的字典映射
    if name == '右耳':
        for key in object_dic:
            if object_dic[key] >= insert_index:
                object_dic[key] += 1
    elif name == '左耳':
        for key in object_dicL:
            if object_dicL[key] >= insert_index:
                object_dicL[key] += 1

    #添加红球
    add_sphere(object_co, insert_index)

    # 重新创建骨骼和外壳管道
    createArmature()
    createShellCanal()
    # 根据红球位置和面板offset参数更新骨骼控制点位置
    updateArmaturePlaneLocationAndNormal()
    # 更新外壳外管道网格物体,用于检测鼠标是否在外管道上
    updateMeshOutShellCanal()
    # 保存管道控制点相关信息
    save_shellcanal_info()


    # 根据管道红球复制出透明圆球,操作管道红球的时候,每次激活的都是这个透明圆球,用于限制实际的管道红球和管道控制点在左右耳模型上
    number_cur = None
    if name == '右耳':
        number_cur = number
    elif name == '左耳':
        number_cur = numberL
    sphere_name1 = name + 'shellcanalsphere' + str(number_cur)
    sphere_obj1 = bpy.data.objects.get(sphere_name1)
    duplicate_obj1 = sphere_obj1.copy()
    duplicate_obj1.data = sphere_obj1.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + 'shellcanalsphere' + str(200 + number_cur)
    bpy.context.scene.collection.objects.link(duplicate_obj1)
    newColor('shellcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    duplicate_obj1.data.materials.clear()
    duplicate_obj1.data.materials.append(bpy.data.materials['shellcanalSphereTransparency'])
    duplicate_obj1.scale[0] = 1.5
    duplicate_obj1.scale[1] = 1.5
    duplicate_obj1.scale[2] = 1.5
    if name == '右耳':
        moveToRight(duplicate_obj1)
    elif name == '左耳':
        moveToLeft(duplicate_obj1)





def finish_canal(co):
    '''
    在co处添加第二个红球,创建骨骼和外壳管道完成管道的初始化
    '''
    name = bpy.context.scene.leftWindowObj

    #在对应位置上添加红球
    add_sphere(co, 2)

    #根据管道两端的红球复制出两个透明圆球,操作管道两端的时候,每次激活的都是这两个透明圆球,用于限制实际的两端管道红球和管道控制点在左右耳模型上
    sphere_name2 = name + 'shellcanalsphere' + '2'
    sphere_obj2 = bpy.data.objects.get(sphere_name2)
    duplicate_obj2 = sphere_obj2.copy()
    duplicate_obj2.data = sphere_obj2.data.copy()
    duplicate_obj2.animation_data_clear()
    duplicate_obj2.name = name + 'shellcanalsphere' + '202'
    bpy.context.scene.collection.objects.link(duplicate_obj2)
    newColor('shellcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    duplicate_obj2.data.materials.clear()
    duplicate_obj2.data.materials.append(bpy.data.materials['shellcanalSphereTransparency'])
    duplicate_obj2.scale[0] = 1.5
    duplicate_obj2.scale[1] = 1.5
    duplicate_obj2.scale[2] = 1.5
    if name == '右耳':
        moveToRight(duplicate_obj2)
    elif name == '左耳':
        moveToLeft(duplicate_obj2)

    #将左右耳模型设置为不可选中,防止误操作将其旋转或移动
    bpy.data.objects[name].hide_select = True


    #创建骨骼和外壳管道
    createArmature()
    createShellCanal()
    #根据红球位置和面板offset参数更新骨骼控制点位置
    updateArmaturePlaneLocationAndNormal()
    #更新外壳外管道网格物体,用于检测鼠标是否在外管道上
    updateMeshOutShellCanal()
    # 保存管道控制点相关信息
    save_shellcanal_info()




def initial_shellcanal():
    # 初始化
    global object_dic
    global object_dicL
    global shellcanal_data
    global shellcanal_dataL
    global shellcanal_finish
    global shellcanal_finishL
    name = bpy.context.scene.leftWindowObj
    object_dic_cur = None
    shellcanal_data_cur = None
    cur_obj = bpy.data.objects.get(name)
    if (name == "右耳"):
        shellcanal_finish = False
        object_dic_cur = object_dic
        shellcanal_data_cur = shellcanal_data
    elif (name == "左耳"):
        shellcanal_finishL = False
        object_dic_cur = object_dicL
        shellcanal_data_cur = shellcanal_dataL
    if len(object_dic_cur) >= 2:  # 存在已保存的圆球位置,复原原有的管道
        newColor('shellcanalSphereRed', 1, 0, 0, 1, 1)

        # 生成显示圆球
        for key in object_dic_cur:
            mesh = bpy.data.meshes.new(name + "shellcanalsphere")
            obj = bpy.data.objects.new(key, mesh)
            bpy.context.collection.objects.link(obj)
            if name == '右耳':
                moveToRight(obj)
            elif name == '左耳':
                moveToLeft(obj)
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            radius = 0.25  # 半径
            segments = 32  # 分段数
            bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
            bm.to_mesh(me)
            bm.free()
            obj.data.materials.clear()
            obj.data.materials.append(bpy.data.materials['shellcanalSphereRed'])
            sphere_index = int(key.replace(name + 'shellcanalsphere', ''))
            sphere_co = Vector(shellcanal_data_cur[3 * (sphere_index - 1) : 3 * (sphere_index - 1) + 3])
            obj.location = sphere_co

        #生成用于控制的透明红球
        for key in object_dic_cur:
            sphere_obj = bpy.data.objects.get(key)
            object_number = int(key.replace(name + 'shellcanalsphere', ''))
            duplicate_obj1 = sphere_obj.copy()
            duplicate_obj1.data = sphere_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = name + 'shellcanalsphere' + str(200 + object_number)
            bpy.context.scene.collection.objects.link(duplicate_obj1)
            newColor('shellcanalSphereTransparency', 0.8, 0.8, 0.8, 1, 0.03)
            duplicate_obj1.data.materials.clear()
            duplicate_obj1.data.materials.append(bpy.data.materials['shellcanalSphereTransparency'])
            duplicate_obj1.scale[0] = 1.5
            duplicate_obj1.scale[1] = 1.5
            duplicate_obj1.scale[2] = 1.5
            if name == '右耳':
                moveToRight(duplicate_obj1)
            elif name == '左耳':
                moveToLeft(duplicate_obj1)

        #创建骨骼和外壳管道
        createArmature()
        createShellCanal()
        updateArmaturePlaneLocationAndNormal()
        updateMeshOutShellCanal()

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        if name == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP3'
        elif name == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP3'
        bpy.data.objects[name].hide_select = True

    elif len(object_dic_cur) == 1:  # 只点击了一次
        newColor('shellcanalSphereRed', 1, 0, 0, 1, 1)

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        mesh = bpy.data.meshes.new(name + "shellcanalsphere")
        obj = bpy.data.objects.new(name + "shellcanalsphere1", mesh)
        bpy.context.collection.objects.link(obj)
        if name == '右耳':
            moveToRight(obj)
        elif name == '左耳':
            moveToLeft(obj)
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        radius = 0.4  # 半径
        segments = 32  # 分段数
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius * 2)
        bm.to_mesh(me)
        bm.free()
        obj.data.materials.clear()
        obj.data.materials.append(bpy.data.materials['shellcanalSphereRed'])
        sphere_co = Vector(shellcanal_data_cur[0:3])
        obj.location = sphere_co


    else:  # 不存在已保存的圆球位置
        pass

    # bpy.ops.object.shellcanalqiehuan('INVOKE_DEFAULT')

def saveInfoAndDeleteShellCanal():
    '''
    记录红球信息并删除管道相关物体
    '''
    global object_dic
    global object_dicL
    global shellcanal_finish
    global shellcanal_finishL
    name = bpy.context.scene.leftWindowObj

    if (name == "右耳"):
        # 更新记录红球信息
        if (not shellcanal_finish):
            save_shellcanal_info()

        # 删除内外管道
        need_to_delete_model_name_list = [name + 'meshshelloutercanal', name + 'shelloutercanal', name + 'shellinnercanal', name + "shellCanalArmature"]
        # 删除透明红球
        for obj in bpy.data.objects:
            shellTransparencySpherePattern = r'右耳shellcanalsphere2'
            if re.match(shellTransparencySpherePattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        # 删除管道控制平面
        for obj in bpy.data.objects:
            shellArmatruePlanePattern = r'右耳shellCanalArmaturePlane'
            if re.match(shellArmatruePlanePattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        # 删除管道红球
        for key in object_dic:
            need_to_delete_model_name_list.append(key)
        delete_useless_object(need_to_delete_model_name_list)

    elif (name == "左耳"):
        # 更新记录红球信息
        if (not shellcanal_finishL):
            save_shellcanal_info()

        # 删除内外管道
        need_to_delete_model_name_list = [name + 'meshshelloutercanal', name + 'shelloutercanal', name + 'shellinnercanal',name + "shellCanalArmature"]
        # 删除透明红球
        for obj in bpy.data.objects:
            shellTransparencySpherePattern = r'左耳shellcanalsphere2'
            if re.match(shellTransparencySpherePattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        # 删除管道控制平面
        for obj in bpy.data.objects:
            shellArmatruePlanePattern = r'左耳shellCanalArmaturePlane'
            if re.match(shellArmatruePlanePattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        # 删除管道红球
        for key in object_dicL:
            need_to_delete_model_name_list.append(key)
        delete_useless_object(need_to_delete_model_name_list)




def reset_shellcanal():
    '''
    重置外壳管道
    '''
    # 删除多余的物体
    global object_dic
    global object_dicL
    global shellcanal_data
    global shellcanal_dataL
    global shellcanal_finish
    global shellcanal_finishL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        if not shellcanal_finish:
            #删除内外管道
            need_to_delete_model_name_list = [name + 'meshshelloutercanal', name + 'shelloutercanal', name + 'shellinnercanal', name + "shellCanalArmature"]
            # 删除透明红球
            for obj in bpy.data.objects:
                shellTransparencySpherePattern = r'右耳shellcanalsphere2'
                if re.match(shellTransparencySpherePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            # 删除管道控制平面
            for obj in bpy.data.objects:
                shellArmatruePlanePattern = r'右耳shellCanalArmaturePlane'
                if re.match(shellArmatruePlanePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            # 删除管道红球
            for key in object_dic:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            #将字典映射和红球位置信息清空
            object_dic.clear()
            shellcanal_data = []
            # 将控制点红球数量置为0
            global number
            number = 0
            bpy.context.scene.transparent3EnumR = 'OP1'
            # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')

    elif (name == "左耳"):
        if not shellcanal_finishL:
            # 删除内外管道
            need_to_delete_model_name_list = [name + 'meshshelloutercanal', name + 'shelloutercanal', name + 'shellinnercanal', name + "shellCanalArmature"]
            # 删除透明红球
            for obj in bpy.data.objects:
                shellTransparencySpherePattern = r'左耳shellcanalsphere2'
                if re.match(shellTransparencySpherePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            # 删除管道控制平面
            for obj in bpy.data.objects:
                shellArmatruePlanePattern = r'左耳shellCanalArmaturePlane'
                if re.match(shellArmatruePlanePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            # 删除管道红球
            for key in object_dicL:
                need_to_delete_model_name_list.append(key)
            delete_useless_object(need_to_delete_model_name_list)
            # 将字典映射和红球位置信息清空
            object_dicL.clear()
            shellcanal_dataL = []
            #将控制点红球数量置为0
            global numberL
            numberL = 0
            bpy.context.scene.transparent3EnumL = 'OP1'
            # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')



def adjustpoint():
    '''
    将外部管道向外伸一部分,提高布尔切割的成功率并保证切割处是一个整圆
    '''
    global number
    global numberL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        number_cur = number
    elif (name == "左耳"):
        number_cur = numberL
    first_armature_plane_name = name + "shellCanalArmaturePlane" + str(1)
    first_armature_plane_obj = bpy.data.objects.get(first_armature_plane_name)
    second_armature_name = name + "shellCanalArmaturePlane" + str(2)
    second_armature_obj = bpy.data.objects.get(second_armature_name)
    last_armature_plane_name = name + "shellCanalArmaturePlane" + str(number_cur)
    last_armature_plane_obj = bpy.data.objects.get(last_armature_plane_name)
    last_second_armature_name = name + "shellCanalArmaturePlane" + str(number_cur - 1)
    last_second_armature_obj = bpy.data.objects.get(last_second_armature_name)
    first_co = first_armature_plane_obj.location
    second_co = second_armature_obj.location
    last_co = last_armature_plane_obj.location
    last_second_co = last_second_armature_obj.location
    step = 1.5                                             #管道向外伸的长度
    normal = first_co - second_co
    first_armature_plane_obj.location = first_armature_plane_obj.location + normal.normalized() * step
    normal = last_co - last_second_co
    last_armature_plane_obj.location = last_armature_plane_obj.location + normal.normalized() * step


def submit_receiver():
    '''
    根据接受器对外壳模型进行提交
    '''
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    receiver_obj = bpy.data.objects.get(name + "receiver")
    receiver_plane_obj = bpy.data.objects.get(name + "ReceiverPlane")
    if(receiver_obj != None and cur_obj != None and receiver_plane_obj != None):
        # 将接收器与模型作布尔切割操作
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.hide_select = False
        cur_obj.select_set(True)
        receiver_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj
        bpy.ops.object.booltool_auto_difference()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # 删除接收器的父物体平面
        bpy.data.objects.remove(receiver_plane_obj, do_unlink=True)



def submit_shellcanal():
    '''
    将外壳管道提交并根据管道平滑参数对内外管道进行平滑操作
    '''

    global object_dic
    global object_dicL
    global shellcanal_finish
    global shellcanal_finishL
    name = bpy.context.scene.leftWindowObj
    shellcanal_finish_cur = None
    if (name == "右耳"):
        object_dic_cur = object_dic
        shellcanal_finish_cur = shellcanal_finish
        shellcanal_finish = True
    elif (name == "左耳"):
        object_dic_cur = object_dicL
        shellcanal_finish_cur = shellcanal_finishL
        shellcanal_finishL = True
    print("外壳管道提交")

    if len(object_dic_cur) > 0 and shellcanal_finish_cur == False:
        # 更新记录管道红球信息
        save_shellcanal_info()
        if len(object_dic_cur) >= 2:
            # 将内部曲线两端向外凸出一段距离
            adjustpoint()



            #将左右耳模型的内壁分离出来用于和外管道进行布尔操作
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj = bpy.data.objects.get(name)
            cur_obj.hide_select = False
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='Inner')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in bpy.data.objects:
                if obj.select_get() and obj != cur_obj:
                    inner_obj = obj
                    break
            inner_obj.name = name + "Inner"




            # 将吸附底部蓝线的平面复制一份用于切割外壳外部模型
            plane_obj = bpy.data.objects.get(name + "batteryPlaneSnapCurve")
            bpy.ops.object.select_all(action='DESELECT')
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            bpy.ops.constraint.apply(constraint="Child Of", owner='OBJECT')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)
            duplicate_plane_obj = plane_obj.copy()
            duplicate_plane_obj.data = plane_obj.data.copy()
            duplicate_plane_obj.animation_data_clear()
            duplicate_plane_obj.name = name + "PlaneCutForShellBottom"
            bpy.context.collection.objects.link(duplicate_plane_obj)
            duplicate_plane_obj.hide_set(False)
            duplicate_plane_obj.hide_select = False
            if (name == "右耳"):
                moveToRight(duplicate_plane_obj)
            elif (name == "左耳"):
                moveToLeft(duplicate_plane_obj)
            # 将复制出的平面模型平移至电池仓平面的上面
            ori_circle_me = plane_obj.data
            ori_circle_bm = bmesh.new()
            ori_circle_bm.from_mesh(ori_circle_me)
            ori_circle_bm.verts.ensure_lookup_table()
            plane_vert0 = ori_circle_bm.verts[0]
            plane_vert1 = ori_circle_bm.verts[1]
            plane_vert2 = ori_circle_bm.verts[2]
            point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
            point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
            point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
            vector1 = point2 - point1
            vector2 = point3 - point1
            normal = vector1.cross(vector2)
            if (normal.z < 0):
                normal = -normal
            duplicate_plane_obj.location = plane_obj.location + normal.normalized() * 1.2  # 1.2是电池仓的厚度
            ori_circle_bm.free()
            # 用复制出的平面切割外壳外部模型
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj.hide_select = False
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            # 将外壳模型外部桥接底面删除再为底部补一个整面
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.edge_face_add()
            #解决非流形问题和相交面,提高布尔切割成功率
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.print3d_clean_non_manifold()           # 修复模型的非流形问题,提高管道切割的成功率
            bpy.ops.mesh.print3d_clean_non_manifold()
            bpy.ops.mesh.print3d_clean_non_manifold()
            bpy.ops.mesh.select_all(action='SELECT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.mesh.print3d_check_intersect()             #检查模型的相交面并选中这些相交面,
            # bpy.ops.mesh.print3d_select_report(index=0)
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_interior_faces()
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            # 将复制出的平面与外壳外部模型作差集
            bpy.ops.object.select_all(action='DESELECT')
            duplicate_plane_obj.select_set(True)
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.booltool_auto_difference()
            # 记录切割的底面顶点,主要用于处理最终切割后的底面光影问题
            outer_shell_plane_bottom_vertex = cur_obj.vertex_groups.get("outerShellPlaneBottomVertex")
            if (outer_shell_plane_bottom_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group="outerShellPlaneBottomVertex")
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            outer_shell_plane_bottom_vertex = cur_obj.vertex_groups.new(name="outerShellPlaneBottomVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="outerShellPlaneBottomVertex")
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            # bool_modifier = cur_obj.modifiers.new(
            #     name="ShellOuterBottomPlaneBooleanModifier", type='BOOLEAN')
            # bool_modifier.operation = 'DIFFERENCE'
            # bool_modifier.solver = 'EXACT'
            # bool_modifier.object = duplicate_plane_obj
            # bpy.ops.object.modifier_apply(modifier="ShellOuterBottomPlaneBooleanModifier", single_user=True)




            # 将外管道与左右耳模型内部作布尔差集
            # 先将管道的骨骼修改器应用,去除外层管道的自交顶点并将外层管道上的顶点选中
            bpy.ops.object.select_all(action='DESELECT')
            shell_outer_canal_obj = bpy.data.objects.get(name + 'shelloutercanal')
            shell_outer_canal_obj.select_set(True)
            bpy.context.view_layer.objects.active = shell_outer_canal_obj
            bpy.ops.object.modifier_apply(modifier="Armature", single_user=True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_interior_faces()
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            # 将左右耳模型内壁设置为当前激活物体,将底面封闭以继续后续的布尔操作,并将顶点取消选中
            bpy.ops.object.select_all(action='DESELECT')
            inner_obj.select_set(True)
            bpy.context.view_layer.objects.active = inner_obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.edge_face_add()
            # 解决非流形问题和相交面,提高布尔切割成功率
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.print3d_clean_non_manifold()  # 修复模型的非流形问题,提高管道切割的成功率
            bpy.ops.mesh.print3d_clean_non_manifold()
            bpy.ops.mesh.print3d_clean_non_manifold()
            bpy.ops.mesh.select_all(action='SELECT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.mesh.print3d_check_intersect()             #检查模型的相交面并选中这些相交面,
            # bpy.ops.mesh.print3d_select_report(index=0)
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_interior_faces()
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            inner_obj.select_set(True)
            shell_outer_canal_obj.select_set(True)
            bpy.context.view_layer.objects.active = inner_obj
            bpy.ops.object.booltool_auto_difference()
            # 将分离出来的内壁与外部管道进行布尔操作
            # bool_modifier = inner_obj.modifiers.new(
            #     name="ShellOuterCanalBooleanModifier", type='BOOLEAN')
            # bool_modifier.operation = 'DIFFERENCE'
            # bool_modifier.solver = 'EXACT'
            # bool_modifier.object = shell_outer_canal_obj
            # bpy.ops.object.modifier_apply(modifier="ShellOuterCanalBooleanModifier", single_user=True)
            # 将布尔后的管道顶点保存下来用于指向外部管道的平滑
            outer_shell_smooth_eardrum_vertex = inner_obj.vertex_groups.get("outerShellSmoothVertex")
            if (outer_shell_smooth_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group="outerShellSmoothVertex")
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            outer_shell_smooth_eardrum_vertex = inner_obj.vertex_groups.new(name="outerShellSmoothVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="outerShellSmoothVertex")
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')





            #使用外壳模型内部物体切割外壳外部模型
            # bpy.ops.object.select_all(action='DESELECT')
            # cur_obj.select_set(True)
            # inner_obj.select_set(True)
            # bpy.context.view_layer.objects.active = cur_obj
            # bpy.ops.object.booltool_auto_difference()
            bpy.ops.object.select_all(action='DESELECT')
            inner_obj.select_set(True)
            bpy.context.view_layer.objects.active = inner_obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='outerShellSmoothVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj.select_set(True)
            inner_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.booltool_auto_difference()
            # bpy.ops.object.select_all(action='DESELECT')
            # cur_obj.select_set(True)
            # bpy.context.view_layer.objects.active = cur_obj
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.mode_set(mode='OBJECT')
            # bool_modifier = cur_obj.modifiers.new(
            #     name="ShellOuterBottomInnerBooleanModifier", type='BOOLEAN')
            # bool_modifier.operation = 'DIFFERENCE'
            # bool_modifier.solver = 'EXACT'
            # bool_modifier.object = inner_obj
            # bpy.ops.object.modifier_apply(modifier="ShellOuterBottomInnerBooleanModifier", single_user=True)
            # 外壁创建外管道平滑顶点组保存内部中的外管道平滑顶点
            outer_shell_smooth_eardrum_vertex = cur_obj.vertex_groups.get("outerShellSmoothVertex")
            if (outer_shell_smooth_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group="outerShellSmoothVertex")
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            outer_shell_smooth_eardrum_vertex = cur_obj.vertex_groups.new(name="outerShellSmoothVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="outerShellSmoothVertex")
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            # 删除外壳内部物体
            # bpy.data.objects.remove(inner_obj, do_unlink=True)





            # 将内管道与左右耳模型外部作布尔差集并保存内管道顶点组
            bpy.ops.object.select_all(action='DESELECT')
            shell_inner_canal_obj = bpy.data.objects.get(name + 'shellinnercanal')
            shell_inner_canal_obj.hide_select = False
            shell_inner_canal_obj.select_set(True)
            bpy.context.view_layer.objects.active = shell_inner_canal_obj
            # 解决内管道的自交问题,防止切割失败
            bpy.ops.object.modifier_apply(modifier="Armature", single_user=True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_interior_faces()
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            # 将左右耳模型设置为当前激活物体并将桥接底面删除再为底部补一个整面
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj.select_set(True)
            shell_inner_canal_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.booltool_auto_difference()
            # # 将模型与内部管道进行布尔操作
            # bool_modifier = cur_obj.modifiers.new(
            #     name="ShellInnerCanalBooleanModifier", type='BOOLEAN')
            # bool_modifier.operation = 'DIFFERENCE'
            # bool_modifier.solver = 'EXACT'
            # bool_modifier.object = shell_inner_canal_obj
            # bpy.ops.object.modifier_apply(modifier="ShellInnerCanalBooleanModifier", single_user=True)
            # 将布尔后的管道顶点保存下来用于指向内部管道的平滑
            inner_shell_smooth_eardrum_vertex = cur_obj.vertex_groups.get("innerShellSmoothVertex")
            if (inner_shell_smooth_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group="innerShellSmoothVertex")
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            inner_shell_smooth_eardrum_vertex = cur_obj.vertex_groups.new(name="innerShellSmoothVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="innerShellSmoothVertex")
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')






            # # 管道内边缘平滑
            # bpy.ops.object.select_all(action='DESELECT')
            # cur_obj.select_set(True)
            # bpy.context.view_layer.objects.active = cur_obj
            bpy.context.active_object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 0.81
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group="innerShellSmoothVertex")
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.mesh.region_to_loop()            # 选择内平滑顶点的边界
            # bpy.ops.object.mode_set(mode='OBJECT')
            # # 根据切割后的物体复制一份用于平滑失败的回退
            # shell_inner_canal_smooth_reset_obj = bpy.data.objects.get(name + "ShellInnerCanalSmoothReset")
            # if (shell_inner_canal_smooth_reset_obj != None):
            #     bpy.data.objects.remove(shell_inner_canal_smooth_reset_obj, do_unlink=True)
            # duplicate_obj = cur_obj.copy()
            # duplicate_obj.data = cur_obj.data.copy()
            # duplicate_obj.animation_data_clear()
            # duplicate_obj.name = name + "ShellInnerCanalSmoothReset"
            # bpy.context.collection.objects.link(duplicate_obj)
            # if name == '右耳':
            #     moveToRight(duplicate_obj)
            # elif name == '左耳':
            #     moveToLeft(duplicate_obj)
            # duplicate_obj.hide_set(True)
            # try:
            #     # 布尔后管道产生的新顶点被选中,根据选中的顶点找出其边界轮廓线,offset_cut后进行倒角
            #     offset_cut = bpy.context.scene.innerShellCanalOffsetR * 0.3  # 管道直径默认值为1,对应的offset_cut宽度为0.3
            #     bpy.ops.object.mode_set(mode='EDIT')
            #     bpy.ops.huier.offset_cut(width=offset_cut, shade_smooth=True, mark_sharp=False, all_cyclic=True)
            #     bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=80, segments=5, release_confirm=True)
            #     bpy.ops.mesh.select_all(action='DESELECT')
            #     bpy.ops.object.mode_set(mode='OBJECT')
            # except:
            #     bpy.ops.object.mode_set(mode='OBJECT')
            #     print("管道平滑失败回退")
            #     # 平滑失败则将当前左右耳物体删除并用平滑回退物体将其替换
            #     shell_inner_canal_smooth_reset_obj = bpy.data.objects.get(name + "ShellInnerCanalSmoothReset")
            #     if (shell_inner_canal_smooth_reset_obj != None):
            #         bpy.data.objects.remove(cur_obj, do_unlink=True)
            #         shell_inner_canal_smooth_reset_obj.name = name
            #         bpy.ops.object.select_all(action='DESELECT')
            #         shell_inner_canal_smooth_reset_obj.hide_set(False)
            #         shell_inner_canal_smooth_reset_obj.select_set(True)
            #         bpy.context.view_layer.objects.active = shell_inner_canal_smooth_reset_obj
            # # 若平滑成功未执行回退,则将平滑回退物体删除
            # shell_inner_canal_smooth_reset_obj = bpy.data.objects.get(name + "ShellInnerCanalSmoothReset")
            # if (shell_inner_canal_smooth_reset_obj != None):
            #     bpy.data.objects.remove(shell_inner_canal_smooth_reset_obj, do_unlink=True)



            # #解决切割平面底部平面的阴影问题           TODO   内管道与模型切割后会影响之前的顶点组信息,顶点组不准确
            # cur_obj = bpy.data.objects.get(name)
            # #根据当前物体复制出一份物体并将其自动光滑调整为30度,用于数据传递
            # target_obj = cur_obj.copy()
            # target_obj.data = cur_obj.data.copy()
            # target_obj.animation_data_clear()
            # target_obj.name = name + 'shellDataTransform'
            # bpy.context.scene.collection.objects.link(target_obj)
            # if name == '右耳':
            #     moveToRight(target_obj)
            # elif name == '左耳':
            #     moveToLeft(target_obj)
            # bpy.ops.object.select_all(action='DESELECT')
            # target_obj.select_set(True)
            # bpy.context.view_layer.objects.active = target_obj
            # bpy.ops.object.shade_smooth()
            # bpy.context.active_object.data.use_auto_smooth = True
            # bpy.context.object.data.auto_smooth_angle = 0.5236
            # #将复制物体底部的平滑数据根据顶点组传递给当前物体
            # bpy.ops.object.select_all(action='DESELECT')
            # cur_obj.select_set(True)
            # bpy.context.view_layer.objects.active = cur_obj
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')        #由于切割后的底部平面顶点组受影响,弃选以下顶点组
            # bpy.ops.object.vertex_group_set_active(group="outerShellPlaneBottomVertex")
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.object.vertex_group_set_active(group="outerShellSmoothVertex")
            # bpy.ops.object.vertex_group_deselect()
            # bpy.ops.object.vertex_group_set_active(group="innerShellSmoothVertex")
            # bpy.ops.object.vertex_group_deselect()
            # bpy.ops.object.vertex_group_set_active(group="Inner")
            # bpy.ops.object.vertex_group_deselect()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.mesh.select_more()
            # bpy.ops.object.vertex_group_set_active(group="outerShellPlaneBottomVertex")
            # bpy.ops.object.vertex_group_assign()
            # bpy.ops.object.mode_set(mode='OBJECT')
            # bpy.ops.object.shade_smooth()
            # bpy.context.active_object.data.use_auto_smooth = True
            # bpy.context.object.data.auto_smooth_angle = 3.14159
            # bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            # bpy.context.object.modifiers["DataTransfer"].object = target_obj
            # bpy.context.object.modifiers["DataTransfer"].vertex_group = "outerShellPlaneBottomVertex"
            # bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            # bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'CUSTOM_NORMAL'}
            # bpy.context.object.modifiers["DataTransfer"].loop_mapping = 'POLYINTERP_LNORPROJ'
            # bpy.ops.object.modifier_apply(modifier="DataTransfer", single_user=True)
            # bpy.data.objects.remove(target_obj, do_unlink=True)




        if(name == "右耳"):
            # 删除透明红球
            for obj in bpy.data.objects:
                shellTransparencySpherePattern = r'右耳shellcanalsphere2'
                if re.match(shellTransparencySpherePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            # 删除管道控制平面
            for obj in bpy.data.objects:
                shellArmatruePlanePattern = r'右耳shellCanalArmaturePlane'
                if re.match(shellArmatruePlanePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
        elif(name == "左耳"):
            # 删除透明红球
            for obj in bpy.data.objects:
                shellTransparencySpherePattern = r'左耳shellcanalsphere2'
                if re.match(shellTransparencySpherePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            # 删除管道控制平面
            for obj in bpy.data.objects:
                shellArmatruePlanePattern = r'左耳shellCanalArmaturePlane'
                if re.match(shellArmatruePlanePattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
        need_to_delete_model_name_list = [name + 'meshshelloutercanal', name + 'shelloutercanal', name + 'shellinnercanal', name + "shellCanalArmature"]
        #删除管道红球
        for key in object_dic_cur:
            need_to_delete_model_name_list.append(key)
        delete_useless_object(need_to_delete_model_name_list)


    bpy.ops.object.select_all(action='DESELECT')
    cur_obj = bpy.data.objects.get(name)
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if (name == "右耳"):
        bpy.context.scene.transparent3EnumR = 'OP1'
    elif(name == "左耳"):
        bpy.context.scene.transparent3EnumL = 'OP1'
    utils_re_color(name, (1, 0.319, 0.133))



class TEST_OT_addshellcanal(bpy.types.Operator):
    bl_idname = "object.addshellcanal"
    bl_label = "addshellcanal"
    bl_description = "双击添加外壳管道控制点"

    def addsphere(self, context, event):

        global number
        global numberL
        global add_or_delete
        global add_or_deleteL
        name = bpy.context.scene.leftWindowObj
        number_cur = None
        if (name == "右耳"):
            number_cur = number
            add_or_delete = True
        elif (name == "左耳"):
            number_cur = numberL
            add_or_deleteL = True
        if number_cur == 0:  # 如果number等于0，初始化
            co,normal = cal_co(name, context, event)
            if co != -1:
                generate_canal(co)
                # 设置旋转中心
                cur_obj = bpy.data.objects.get(name)
                bpy.ops.object.select_all(action='DESELECT')
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj

        elif number_cur == 1:  # 如果number等于1双击完成管道
            co,normal = cal_co(name, context, event)
            if co != -1:
                finish_canal(co)
                if name == '右耳':
                    bpy.context.scene.transparent3EnumR = 'OP3'
                elif name == '左耳':
                    bpy.context.scene.transparent3EnumL = 'OP3'
                bpy.ops.object.select_all(action='DESELECT')

        else:  # 如果number大于1，双击添加控制点
            shell_co,normal = cal_co(name, context, event)      #鼠标位于外层管道上时才能够添加控制点   TODO 绑定骨骼后若未应用修改器则管道网格数据并未形变
            if shell_co != -1:
                object_co, normal = cal_co(name, context, event)     #在模型上添加红球并根据管道offset参数在管道对应的位置上添加控制点
                if name == '右耳':
                    shellcanal_offset = bpy.context.scene.shellCanalOffsetR
                else:
                    shellcanal_offset = bpy.context.scene.shellCanalOffsetL
                point_co = object_co + normal.normalized() * shellcanal_offset
                insert_index = select_nearest_point(point_co)
                add_canal(object_co, insert_index)


        if name == '右耳':
            add_or_delete = False
        elif name == '左耳':
            add_or_deleteL = False

    def invoke(self, context, event):
        self.addsphere(context, event)
        return {'FINISHED'}


class TEST_OT_deleteshellcanal(bpy.types.Operator):
    bl_idname = "object.deleteshellcanal"
    bl_label = "deleteshellcanal"
    bl_description = "双击删除外壳管道控制点"

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
            if (name == "右耳"):
                if(sphere_number > 200):
                    sphere_name = name + 'shellcanalsphere' + str(sphere_number - 200)
                    transparency_sphere_name = name + 'shellcanalsphere' + str(sphere_number)
                    index = object_dic[sphere_name]
                else:
                    sphere_name = name + 'shellcanalsphere' + str(sphere_number)
                    transparency_sphere_name = name + 'shellcanalsphere' + str(200 + sphere_number)
                    index = object_dic[sphere_name]

                # 删除显示红球和透明红球
                bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
                bpy.data.objects.remove(bpy.data.objects[transparency_sphere_name], do_unlink=True)
                for key in object_dic:
                    if object_dic[key] > index:
                        object_dic[key] -= 1
                del object_dic[sphere_name]
                global number
                count = number - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        #更改显示红球的名称和字典中对应的索引
                        old_name = name + 'shellcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'shellcanalsphere' + str(sphere_number + i)
                        object_dic.update({replace_name: object_dic.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                        #更改透明控制红球的名称
                        transparency_old_name = name + 'shellcanalsphere' + str(200 + sphere_number + i + 1)
                        transparency_new_name = name + 'shellcanalsphere' + str(200 + sphere_number + i)
                        bpy.data.objects[transparency_old_name].name = transparency_new_name
                number -= 1
                createArmature()
                createShellCanal()
                updateArmaturePlaneLocationAndNormal()
                updateMeshOutShellCanal()
                save_shellcanal_info()
            elif (name == "左耳"):
                if (sphere_number > 200):
                    sphere_name = name + 'shellcanalsphere' + str(sphere_number - 200)
                    transparency_sphere_name = name + 'shellcanalsphere' + str(sphere_number)
                    index = object_dicL[sphere_name]
                else:
                    sphere_name = name + 'shellcanalsphere' + str(sphere_number)
                    transparency_sphere_name = name + 'shellcanalsphere' + str(200 + sphere_number)
                    index = object_dicL[sphere_name]

                # 删除显示红球和透明红球
                bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
                bpy.data.objects.remove(bpy.data.objects[transparency_sphere_name], do_unlink=True)
                for key in object_dicL:
                    if object_dicL[key] > index:
                        object_dicL[key] -= 1
                del object_dicL[sphere_name]
                global numberL
                count = numberL - sphere_number
                if count >= 1:
                    for i in range(0, count, 1):
                        # 更改显示红球的名称
                        old_name = name + 'shellcanalsphere' + str(sphere_number + i + 1)
                        replace_name = name + 'shellcanalsphere' + str(sphere_number + i)
                        object_dicL.update({replace_name: object_dicL.pop(old_name)})
                        bpy.data.objects[old_name].name = replace_name
                        # 更改透明控制红球的名称
                        transparency_old_name = name + 'shellcanalsphere' + str(200 + sphere_number + i + 1)
                        transparency_new_name = name + 'shellcanalsphere' + str(200 + sphere_number + i)
                        bpy.data.objects[transparency_old_name].name = transparency_new_name
                numberL -= 1
                createArmature()
                createShellCanal()
                updateArmaturePlaneLocationAndNormal()
                updateMeshOutShellCanal()
                save_shellcanal_info()


        if name == '右耳':
            add_or_delete = False
        elif name == '左耳':
            add_or_deleteL = False

    def invoke(self, context, event):
        self.deletesphere(context, event)
        return {'FINISHED'}


class TEST_OT_updateshellcanal(bpy.types.Operator):
    bl_idname = "object.updateshellcanal"
    bl_label = "更新管道的状态"
    bl_description = "显示或者隐藏管道"

    def invoke(self, context, event):
        print("updateshellcanal invoke")
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            useShellCanal = bpy.context.scene.useShellCanalR
            bpy.context.scene.useShellCanalR = not useShellCanal
        elif (name == "左耳"):
            useShellCanal = bpy.context.scene.useShellCanalL
            bpy.context.scene.useShellCanalL = not useShellCanal


def updateShellCanal(context,event,left_press):
    '''
    根据管道红球控制点跟新管道形状
    '''
    global object_dic
    global object_dicL
    global add_or_delete
    global add_or_deleteL
    global shellcanal_finish
    global shellcanal_finishL

    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        object_dic_cur = object_dic
        add_or_delete_cur = add_or_delete
        shellcanal_finish_cur = shellcanal_finish
        useShellCanal = bpy.context.scene.useShellCanalR

    elif (name == "左耳"):
        object_dic_cur = object_dicL
        add_or_delete_cur = add_or_deleteL
        shellcanal_finish_cur = shellcanal_finishL
        useShellCanal = bpy.context.scene.useShellCanalL


    if (not add_or_delete_cur and useShellCanal and not shellcanal_finish_cur):
        if len(object_dic_cur) < 2:
            #将旋转中心设置为左右耳模型
            co, normal = cal_co(name, context, event)
            if co == -1 and is_changed(context, event) == True:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                bpy.data.objects[name].select_set(True)

        elif len(object_dic_cur) >= 2:
            # 判断是否位于红球上,存在则返回其索引,不存在则返回0
            sphere_number = on_which_shpere(context, event)

            # 实时更新管道控制点的位置,随圆球位置更新而改变
            if sphere_number != 0:
                active_object = bpy.context.active_object
                # 当前激活物体为透明红球
                transparency_sphere_active = False
                if (active_object != None):
                    active_object_name = active_object.name
                    if (name == "右耳"):
                        pattern = r'右耳shellcanalsphere2'
                        if re.match(pattern, active_object_name):
                            transparency_sphere_active = True
                    elif (name == "左耳"):
                        pattern = r'左耳shellcanalsphere2'
                        if re.match(pattern, active_object_name):
                            transparency_sphere_active = True
                    if (transparency_sphere_active):
                        active_object_index = int(active_object_name.replace(name + 'shellcanalsphere', ''))
                        loc, normal = cal_co(name, context, event)
                        # 鼠标左键按下的时候,虽然不会发生鼠标行为的切换,但当我们操作管道末端透明控制红球的时候,若将鼠标同时移动到另外一端的透明控制红球的时候,
                        # 会将该透明圆球吸附到鼠标位置上,等于同时操控了两个圆球,为了避免这种现象,我们使用当前激活物体来限制确认操作的圆球物体,并非单纯根据鼠标在哪个物体上
                        sphere_number = active_object_index
                        sphere_number1 = active_object_index - 200
                        sphere_name = name + 'shellcanalsphere' + str(sphere_number)
                        obj = bpy.data.objects[sphere_name]
                        sphere_name1 = name + 'shellcanalsphere' + str(sphere_number1)
                        obj1 = bpy.data.objects[sphere_name1]
                        obj.location = obj1.location
                        if (loc != -1 and left_press):
                            obj1.location = loc
                            updateArmaturePlaneLocationAndNormal()
                            updateMeshOutShellCanal()










class public_add_shellcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.public_add_shellcanal"
    bl_label = "外壳管道添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作和公共鼠标行为"
    )
    bl_icon = "brush.sculpt.crease"
    bl_widget = None
    bl_keymap = (
        ("object.addshellcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class delete_drag_shellcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.delete_drag_shellcanal"
    bl_label = ""
    bl_description = (
        "对外壳圆球圆球移动和双击删除操作"
    )
    bl_icon = "brush.sculpt.displacement_eraser"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("object.deleteshellcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass



_classes = [
    TEST_OT_addshellcanal,
    TEST_OT_deleteshellcanal,
    TEST_OT_updateshellcanal
    # TEST_OT_shellcanalqiehuan
]


def register_shellcanal_tools():
    bpy.utils.register_tool(public_add_shellcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(delete_drag_shellcanal_MyTool, separator=True, group=False)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)



def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)

    bpy.utils.unregister_tool(public_add_shellcanal_MyTool)
    bpy.utils.unregister_tool(delete_drag_shellcanal_MyTool)