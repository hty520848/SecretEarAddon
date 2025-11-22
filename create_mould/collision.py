import bpy
import bmesh
import mathutils
import math
import os
from bpy_extras import view3d_utils
from math import sqrt
from ..tool import newShader, get_region_and_space, moveToRight, moveToLeft, utils_re_color, delete_useless_object, \
    newColor, getOverride, getOverride2, apply_material
from math import radians
from mathutils import Vector, Euler, Matrix
from ..global_manager import global_manager

is_modal_start = False
is_collision_modal_start = False

prev_on_object_stepcut = 0

prev_location1, prev_location2, prev_location3 = None, None, None
prev_rotation1, prev_rotation2, prev_rotation3 = None, None, None

# cube123是参与碰撞监测的组件，move_cube123是控制cube123跟随移动的组件
cube1, cube2, cube3 = None, None, None
move_cube1, move_cube2, move_cube3 = None, None, None

now_move_cube_name = ""  # 记录当前鼠标在哪个cube上，记录的格式是name+cube123
active_cube_name = ""  # 记录当前参与碰撞监测的主导cube，记录的格式是name+cube123
now_on_cube_name = ""  # 实时记录当前鼠标正在哪个cube上

mouse_pos_destination = None  # 在一次拖拽进行中时，更新当前的鼠标位置
mouse_pos_begin = None  # 第一次拖拽点击时，记录鼠标位置

# mouse_listener = None

ear_model = None
inner_ear_model = None

# 1-完全在内部，2-部分在内部，0:-完全不在内部
last_inclusion1, last_inclusion2, last_inclusion3 = 0, 0, 0

can_move1, can_move2, can_move3 = True, True, True

move_vector1 = None  # 记录本次移动组件是沿着哪个法向量移动
move_vector2 = None
move_vector3 = None

s1 = s2 = s3 = 0

is_pressing_L = None

# mat_silver = None
# mat_red = None

points1 = points2 = points3 = []

#记录碰撞检测中相关物体的位置信息,用于模块切换时恢复相关物体的位置
cube1_location = None
cube2_location = None
cube3_location = None
receiver_location = None
cube1_locationL  = None
cube2_locationL  = None
cube3_locationL  = None
receiver_locationL  = None
cube1_rotation  = None
cube2_rotation  = None
cube3_rotation  = None
receiver_rotation  = None
cube1_rotationL  = None
cube2_rotationL  = None
cube3_rotationL  = None
receiver_rotationL  = None

cube1_location_list = []
cube2_location_list = []
cube3_location_list = []
receiver_location_list = []
cube1_rotation_list = []
cube2_rotation_list = []
cube3_rotation_list = []
receiver_rotation_list = []

cube1_locationL_list = []
cube2_locationL_list = []
cube3_locationL_list = []
receiver_locationL_list = []
cube1_rotationL_list = []
cube2_rotationL_list = []
cube3_rotationL_list = []
receiver_rotationL_list = []


def register_collision_globals():
    global cube1_location_list, cube2_location_list, cube3_location_list, receiver_location_list
    global cube1_rotation_list, cube2_rotation_list, cube3_rotation_list, receiver_rotation_list
    global cube1_locationL_list, cube2_locationL_list, cube3_locationL_list, receiver_locationL_list
    global cube1_rotationL_list, cube2_rotationL_list, cube3_rotationL_list, receiver_rotationL_list
    global cube1_location, cube2_location, cube3_location, receiver_location
    global cube1_rotation, cube2_rotation, cube3_rotation, receiver_rotation
    global cube1_locationL, cube2_locationL, cube3_locationL, receiver_locationL
    global cube1_rotationL, cube2_rotationL, cube3_rotationL, receiver_rotationL
    global finish
    if cube1_location is not None:
        cube1_location_list = cube1_location[:]
        cube1_rotation_list = cube1_rotation[:]
    if cube2_location is not None:
        cube2_location_list = cube2_location[:]
        cube2_rotation_list = cube2_rotation[:]
    if cube3_location is not None:
        cube3_location_list = cube3_location[:]
        cube3_rotation_list = cube3_rotation[:]
    if receiver_location is not None:
        receiver_location_list = receiver_location[:]
        receiver_rotation_list = receiver_rotation[:]
    if cube1_locationL is not None:
        cube1_locationL_list = cube1_locationL[:]
        cube1_rotationL_list = cube1_rotationL[:]
    if cube2_locationL is not None:
        cube2_locationL_list = cube2_locationL[:]
        cube2_rotationL_list = cube2_rotationL[:]
    if cube3_locationL is not None:
        cube3_locationL_list = cube3_locationL[:]
        cube3_rotationL_list = cube3_rotationL[:]
    if receiver_locationL is not None:
        receiver_locationL_list = receiver_locationL[:]
        receiver_rotationL_list = receiver_rotationL[:]
    global_manager.register("cube1_location_list", cube1_location_list)
    global_manager.register("cube2_location_list", cube2_location_list)
    global_manager.register("cube3_location_list", cube3_location_list)
    global_manager.register("receiver_location_list", receiver_location_list)
    global_manager.register("cube1_rotation_list", cube1_rotation_list)
    global_manager.register("cube2_rotation_list", cube2_rotation_list)
    global_manager.register("cube3_rotation_list", cube3_rotation_list)
    global_manager.register("receiver_rotation_list", receiver_rotation_list)
    global_manager.register("cube1_locationL_list", cube1_locationL_list)
    global_manager.register("cube2_locationL_list", cube2_locationL_list)
    global_manager.register("cube3_locationL_list", cube3_locationL_list)
    global_manager.register("receiver_locationL_list", receiver_locationL_list)
    global_manager.register("cube1_rotationL_list", cube1_rotationL_list)
    global_manager.register("cube2_rotationL_list", cube2_rotationL_list)
    global_manager.register("cube3_rotationL_list", cube3_rotationL_list)
    global_manager.register("receiver_rotationL_list", receiver_rotationL_list)
    global_manager.register("finish", finish)


def load_collision_globals():
    global cube1_location_list, cube2_location_list, cube3_location_list, receiver_location_list
    global cube1_rotation_list, cube2_rotation_list, cube3_rotation_list, receiver_rotation_list
    global cube1_locationL_list, cube2_locationL_list, cube3_locationL_list, receiver_locationL_list
    global cube1_rotationL_list, cube2_rotationL_list, cube3_rotationL_list, receiver_rotationL_list
    global cube1_location, cube2_location, cube3_location, receiver_location
    global cube1_rotation, cube2_rotation, cube3_rotation, receiver_rotation
    global cube1_locationL, cube2_locationL, cube3_locationL, receiver_locationL
    global cube1_rotationL, cube2_rotationL, cube3_rotationL, receiver_rotationL

    if len(cube1_location_list) != 0:
        cube1_location = Vector(cube1_location_list)
        cube1_rotation = Euler(cube1_rotation_list, 'XYZ')
    if len(cube2_location_list) != 0:
        cube2_location = Vector(cube2_location_list)
        cube2_rotation = Euler(cube2_rotation_list, 'XYZ')
    if len(cube3_location_list) != 0:
        cube3_location = Vector(cube3_location_list)
        cube3_rotation = Euler(cube3_rotation_list, 'XYZ')
    if len(receiver_location_list) != 0:
        receiver_location = Vector(receiver_location_list)
        receiver_rotation = Euler(receiver_rotation_list, 'XYZ')
    if len(cube1_locationL_list) != 0:
        cube1_locationL = Vector(cube1_locationL_list)
        cube1_rotationL = Euler(cube1_rotationL_list, 'XYZ')
    if len(cube2_locationL_list) != 0:
        cube2_locationL = Vector(cube2_locationL_list)
        cube2_rotationL = Euler(cube2_rotationL_list, 'XYZ')
    if len(cube3_locationL_list) != 0:
        cube3_locationL = Vector(cube3_locationL_list)
        cube3_rotationL = Euler(cube3_rotationL_list, 'XYZ')
    if len(receiver_locationL_list) != 0:
        receiver_locationL = Vector(receiver_locationL_list)
        receiver_rotationL = Euler(receiver_rotationL_list, 'XYZ')


def saveCubeInfo():
    '''
    记录碰撞检测中相关物体和接收器的位置信息
    '''
    global cube1_location, cube2_location, cube3_location, receiver_location
    global cube1_rotation, cube2_rotation, cube3_rotation, receiver_rotation
    global cube1_locationL, cube2_locationL, cube3_locationL, receiver_locationL
    global cube1_rotationL, cube2_rotationL, cube3_rotationL, receiver_rotationL

    name = bpy.context.scene.leftWindowObj
    cube1_obj = bpy.data.objects.get(name + "cube1")
    cube2_obj = bpy.data.objects.get(name + "cube2")
    cube3_obj = bpy.data.objects.get(name + "cube3")
    receiver_plane_obj = bpy.data.objects.get(name + "ReceiverPlane")
    if (cube1_obj != None and cube2_obj != None and cube3_obj != None and receiver_plane_obj != None):
        if name == '右耳':
            cube1_location = [cube1_obj.location[0], cube1_obj.location[1], cube1_obj.location[2]]
            cube2_location = [cube2_obj.location[0], cube2_obj.location[1], cube2_obj.location[2]]
            cube3_location = [cube3_obj.location[0], cube3_obj.location[1], cube3_obj.location[2]]
            receiver_location = [receiver_plane_obj.location[0], receiver_plane_obj.location[1],
                                 receiver_plane_obj.location[2]]
            cube1_rotation = [cube1_obj.rotation_euler[0], cube1_obj.rotation_euler[1], cube1_obj.rotation_euler[2]]
            cube2_rotation = [cube2_obj.rotation_euler[0], cube2_obj.rotation_euler[1], cube2_obj.rotation_euler[2]]
            cube3_rotation = [cube3_obj.rotation_euler[0], cube3_obj.rotation_euler[1], cube3_obj.rotation_euler[2]]
            receiver_rotation = [receiver_plane_obj.rotation_euler[0], receiver_plane_obj.rotation_euler[1],
                                 receiver_plane_obj.rotation_euler[2]]
        elif name == '左耳':
            cube1_locationL = [cube1_obj.location[0], cube1_obj.location[1], cube1_obj.location[2]]
            cube2_locationL = [cube2_obj.location[0], cube2_obj.location[1], cube2_obj.location[2]]
            cube3_locationL = [cube3_obj.location[0], cube3_obj.location[1], cube3_obj.location[2]]
            receiver_locationL = [receiver_plane_obj.location[0], receiver_plane_obj.location[1],
                                 receiver_plane_obj.location[2]]
            cube1_rotationL = [cube1_obj.rotation_euler[0], cube1_obj.rotation_euler[1], cube1_obj.rotation_euler[2]]
            cube2_rotationL = [cube2_obj.rotation_euler[0], cube2_obj.rotation_euler[1], cube2_obj.rotation_euler[2]]
            cube3_rotationL = [cube3_obj.rotation_euler[0], cube3_obj.rotation_euler[1], cube3_obj.rotation_euler[2]]
            receiver_rotationL = [receiver_plane_obj.rotation_euler[0], receiver_plane_obj.rotation_euler[1],
                                 receiver_plane_obj.rotation_euler[2]]


def initialCubeLocation():
    '''
    根据记录的位置恢复碰撞检测中相关物体和接收器的位置
    '''
    global cube1_location, cube2_location, cube3_location, receiver_location
    global cube1_rotation, cube2_rotation, cube3_rotation, receiver_rotation
    global cube1_locationL, cube2_locationL, cube3_locationL, receiver_locationL
    global cube1_rotationL, cube2_rotationL, cube3_rotationL, receiver_rotationL

    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        cube1_location_cur = cube1_location
        cube2_location_cur = cube2_location
        cube3_location_cur = cube3_location
        receiver_location_cur = receiver_location
        cube1_rotation_cur = cube1_rotation
        cube2_rotation_cur = cube2_rotation
        cube3_rotation_cur = cube3_rotation
        receiver_rotation_cur = receiver_rotation
    elif name == '左耳':
        cube1_location_cur = cube1_locationL
        cube2_location_cur = cube2_locationL
        cube3_location_cur = cube3_locationL
        receiver_location_cur = receiver_locationL
        cube1_rotation_cur = cube1_rotationL
        cube2_rotation_cur = cube2_rotationL
        cube3_rotation_cur = cube3_rotationL
        receiver_rotation_cur = receiver_rotationL
    cube1_obj = bpy.data.objects.get(name + "cube1")
    cube2_obj = bpy.data.objects.get(name + "cube2")
    cube3_obj = bpy.data.objects.get(name + "cube3")
    receiver_plane_obj = bpy.data.objects.get(name + "ReceiverPlane")
    if(cube1_location_cur != None and cube2_location_cur != None and cube3_location_cur != None and receiver_location_cur != None and cube1_rotation_cur != None and cube2_rotation_cur != None and cube3_rotation_cur != None and receiver_rotation_cur != None):
        if (cube1_obj != None and cube2_obj != None and cube3_obj != None and receiver_plane_obj != None):
            cube1_obj.location[0:3] = cube1_location_cur
            cube2_obj.location[0:3] = cube2_location_cur
            cube3_obj.location[0:3] = cube3_location_cur
            receiver_plane_obj.location[0:3] = receiver_location_cur
            cube1_obj.rotation_euler[0:3] = cube1_rotation_cur
            cube2_obj.rotation_euler[0:3] = cube2_rotation_cur
            cube3_obj.rotation_euler[0:3] = cube3_rotation_cur
            receiver_plane_obj.rotation_euler[0:3] = receiver_rotation_cur

def generate_cubes():  # 生成立方体，改材质，获取六个角点，开启modal
    # global mat_silver, mat_red
    global points1, points2, points3
    """
    生成三个立方体组件
    """
    mat_silver = newColor("Silver", 0.588, 0.588, 0.588, 0, 0.01)
    mat_red = newColor("Red", 1, 0.3, 0.35, 0, 0.01)

    def create_single_cube(cube_name, location, rotation, scale):  # 生成指定大小的立方体，并且细分
        name = bpy.context.scene.leftWindowObj
        bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation,scale=scale)
        cube = bpy.context.active_object
        cube.name = cube_name
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=10)
        bpy.ops.object.mode_set(mode='OBJECT')
        if (name == "右耳"):
            moveToRight(cube)
        elif (name == "左耳"):
            moveToLeft(cube)
        return cube

    def create_single_cube1(cube_name, location, rotation, scale):  # 生成指定大小的立方体，不进行细分，进行倒角
        name = bpy.context.scene.leftWindowObj
        bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation,scale=scale)
        cube = bpy.context.active_object
        cube.name = cube_name
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edges_select_sharp()
        bpy.ops.mesh.bevel(offset=0.1, offset_pct=0, affect='EDGES')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if(name == "右耳"):
            moveToRight(cube)
        elif(name == "左耳"):
            moveToLeft(cube)
        return cube

    name = bpy.context.scene.leftWindowObj

    mat = newColor("HandleTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质

    # 创建立方体
    loc1 = (10, 0, 10)
    rot1 = (0, 0, 0)
    sca1 = (2, 3, 1)


    loc1_=(10,2.8,10)
    c1 = create_single_cube1(name + "cube1", loc1, rot1, sca1)  # 跟随者
    mc1 = create_single_cube(name + "move_cube1", loc1, rot1, sca1)
    c1.data.materials.clear()
    c1.data.materials.append(mat_silver)
    mc1.data.materials.clear()
    mc1.data.materials.append(mat)

    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', radius=0.5, location=loc1_,
                                        rotation=(1.5708, 0, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = name + "littleShellCylinder1"
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = bpy.data.objects[name+"cube1"]




    loc2 = (15, 5, 10)
    rot2 = (0, 0, 0)
    sca2 = (1.5, 3, 1.5)
    c2 = create_single_cube1(name + "cube2", loc2, rot2, sca2)  # 跟随者
    mc2 = create_single_cube(name + "move_cube2", loc2, rot2, sca2)
    c2.data.materials.clear()
    c2.data.materials.append(mat_silver)
    mc2.data.materials.clear()
    mc2.data.materials.append(mat)
    loc2_=(15,7.8,10)
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', radius=0.5, location=loc2_,
                                        rotation=(1.5708, 0, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = name + "littleShellCylinder2"
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = bpy.data.objects[name + "cube2"]





    loc3 = (10, 5, 10)
    rot3 = (0, 0, 0)
    sca3 = (2, 3, 1)
    c3 = create_single_cube1(name + "cube3", loc3, rot3, sca3)  # 跟随者
    mc3 = create_single_cube(name + "move_cube3", loc3, rot3, sca3)
    c3.data.materials.clear()
    c3.data.materials.append(mat_silver)
    mc3.data.materials.clear()
    mc3.data.materials.append(mat)

    # loc3_1=(1.3,-1,0.8)
    # loc3_2=(0.4,-1,0.8)
    # loc3_3=(0.8,0.5,0.8)
    # loc3_4=(-0.5,1.7,0.8)
    # loc3_5=(4.2,-7.3,1.3)
    loc3_1 = (11.3, 4, 10.8)
    loc3_2 = (10.4, 4, 10.8)
    loc3_3 = (10.8, 5.5, 10.8)
    loc3_4 = (9.5, 6.7, 10.8)
    sca3_1=(0.3,0.64,0.5)
    sca3_2=(0.3,0.64,0.5)
    sca3_3=(0.7,0.4,0.5)
    sca3_4=(0.3,0.5,0.5)
    bpy.ops.mesh.primitive_cube_add(location=loc3_1, rotation=rot3, scale=sca3_1)
    bpy.context.active_object.name = name + "littleShellCube1"
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = bpy.data.objects[name + "cube3"]
    bpy.ops.mesh.primitive_cube_add(location=loc3_2, rotation=rot3, scale=sca3_2)
    bpy.context.active_object.name = name + "littleShellCube2"
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = bpy.data.objects[name + "cube3"]
    bpy.ops.mesh.primitive_cube_add(location=loc3_3, rotation=rot3, scale=sca3_3)
    bpy.context.active_object.name = name + "littleShellCube3"
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = bpy.data.objects[name + "cube3"]
    bpy.ops.mesh.primitive_cube_add(location=loc3_4, rotation=rot3, scale=sca3_4)
    bpy.context.active_object.name = name + "littleShellCube4"
    bpy.ops.object.constraint_add(type='CHILD_OF')
    bpy.context.object.constraints["Child Of"].target = bpy.data.objects[name + "cube3"]
    littleShellCubeObj1 = bpy.data.objects.get(name + "littleShellCube1")
    littleShellCubeObj2 = bpy.data.objects.get(name + "littleShellCube2")
    littleShellCubeObj3 = bpy.data.objects.get(name + "littleShellCube3")
    littleShellCubeObj4 = bpy.data.objects.get(name + "littleShellCube4")
    if(littleShellCubeObj1 != None):
        if (name == "右耳"):
            moveToRight(littleShellCubeObj1)
        elif (name == "左耳"):
            moveToLeft(littleShellCubeObj1)
    if (littleShellCubeObj2 != None):
        if (name == "右耳"):
            moveToRight(littleShellCubeObj2)
        elif (name == "左耳"):
            moveToLeft(littleShellCubeObj2)
    if (littleShellCubeObj3 != None):
        if (name == "右耳"):
            moveToRight(littleShellCubeObj3)
        elif (name == "左耳"):
            moveToLeft(littleShellCubeObj3)
    if (littleShellCubeObj4 != None):
        if (name == "右耳"):
            moveToRight(littleShellCubeObj4)
        elif (name == "左耳"):
            moveToLeft(littleShellCubeObj4)






    # 生成接收器组件，用于测试
    # bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(10, 10, 10), scale=(1, 1, 1))
    # ball = bpy.context.active_object
    # ball.name = name + "receiver"
    bpy.ops.object.select_all(action='DESELECT')
    script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    relative_path = os.path.join(script_dir, "stl\\receiver.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    receiver_name = "receiver"
    receiver_obj = bpy.data.objects.get(receiver_name)
    receiver_obj.name = name + "receiver"
    newColor("receiverRed", 1, 0, 0, 0, 1)
    receiver_obj.data.materials.clear()
    receiver_obj.data.materials.append(bpy.data.materials["receiverRed"])
    if (name == "右耳"):
        moveToRight(receiver_obj)
    elif (name == "左耳"):
        moveToLeft(receiver_obj)
    #创建平面作为接收器的父物体,优化吸附效果, 设置初始位置
    plane_obj = bpy.data.objects.get(name + "ReceiverPlane")
    if(plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    bpy.ops.mesh.primitive_plane_add(size=1.5, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_obj.name = name + "ReceiverPlane"
    newColor('shellReceiverPlaneTransparency', 0.8, 0.8, 0.8, 1, 0.03)
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials["shellReceiverPlaneTransparency"])
    if (name == "右耳"):
        moveToRight(plane_obj)
    elif (name == "左耳"):
        moveToLeft(plane_obj)
    bpy.ops.object.select_all(action='DESELECT')
    receiver_obj.select_set(True)
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    plane_obj.location[0] = 10
    plane_obj.location[1] = 10
    plane_obj.location[2] = 10

    #根据记录的位置信息恢复接收器相关物体的位置
    initialCubeLocation()

    #初始化立方体全局变量
    initCube()


    # 开启移动立方体modal
    # bpy.ops.object.movecube('INVOKE_DEFAULT')


# 材质相关------
def newMaterial(id):
    mat = bpy.data.materials.get(id)
    if mat is None:
        mat = bpy.data.materials.new(name=id)
    mat.use_nodes = True
    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()
    return mat


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
    shader.inputs[15].default_value = 1
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


def initialCompleteTransparency():
    newColor("CompleteTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质


def initialRed():
    newColor("Red", 0.839, 0.301, 0.357, 0, 0.01)  # 创建材质


def initialSilver():
    newColor("Sliver", 0.804, 0.804, 0.804, 0, 0.01)  # 创建材质


def on_which_move_cube(context, event):
    '''
    依次检测名称为name+move_cube123的物体，返回1/2/3，未检测到则返回0
    '''
    name = bpy.context.scene.leftWindowObj
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

    cube_name1 = name + 'move_cube1'
    cube_obj1 = bpy.data.objects.get(cube_name1)
    if (cube_obj1 != None):
        mwi = cube_obj1.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if cube_obj1.type == 'MESH':
            if (cube_obj1.mode == 'OBJECT'):
                mesh = cube_obj1.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 1
    cube_name2 = name + 'move_cube2'
    cube_obj2 = bpy.data.objects.get(cube_name2)
    if (cube_obj2 != None):
        mwi = cube_obj2.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if cube_obj2.type == 'MESH':
            if (cube_obj2.mode == 'OBJECT'):
                mesh = cube_obj2.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 2
    cube_name3 = name + 'move_cube3'
    cube_obj3 = bpy.data.objects.get(cube_name3)
    if (cube_obj3 != None):
        mwi = cube_obj3.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if cube_obj3.type == 'MESH':
            if (cube_obj3.mode == 'OBJECT'):
                mesh = cube_obj3.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 3
    cube_name4 = name + "receiver"
    cube_obj4 = bpy.data.objects.get(cube_name4)
    if (cube_obj4 != None):
        mwi = cube_obj4.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start
        if cube_obj4.type == 'MESH':
            if (cube_obj4.mode == 'OBJECT'):
                mesh = cube_obj4.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx is not None:
                    return 4
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


def is_changed_stepcut(context, event):
    curr_on_object_stepcut = on_which_move_cube(context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_stepcut  # 之前鼠标在那个物体上

    if (curr_on_object_stepcut != prev_on_object_stepcut):
        prev_on_object_stepcut = curr_on_object_stepcut
        return True
    else:
        return False


is_pressing_R = False

# def on_click(x, y, button, pressed):
#     global active_cube_name, now_move_cube_name
#     global mouse_pos_begin, mouse_pos_destination
#     global cube1, cube2, cube3
#     global is_pressing_L, is_pressing_R
#     global rotation_stage
#
#     if button == mouse.Button.left and pressed:
#         print("左键按下")
#         if now_move_cube_name != "":
#             if now_move_cube_name == name + "cube1":
#                 active_cube_name = now_move_cube_name
#                 mouse_pos_begin = (x, y)
#             elif now_move_cube_name == name + "cube2":
#                 active_cube_name = now_move_cube_name
#                 mouse_pos_begin = (x, y)
#             elif now_move_cube_name == name + "cube3":
#                 active_cube_name = now_move_cube_name
#                 mouse_pos_begin = (x, y)
#         is_pressing_L = True
#         rotation_stage = True
#     if button == mouse.Button.left and not pressed:
#         print("左键松开")
#         # if active_cube_name != "":
#         if active_cube_name == name + "cube1":
#             equal_loc_and_rot(cube1, move_cube1)
#         elif active_cube_name == name + "cube2":
#             equal_loc_and_rot(cube2, move_cube2)
#         elif active_cube_name == name + "cube3":
#             equal_loc_and_rot(cube3, move_cube3)
#         # active_cube_name = ""
#         now_move_cube_name = ""
#         is_pressing_L = False
#         mouse_pos_begin = None
#
#     if button == mouse.Button.right and pressed:
#         if now_move_cube_name != "":
#             if now_move_cube_name == name + "cube1":
#                 active_cube_name = now_move_cube_name
#                 mouse_pos_begin = (x, y)
#             elif now_move_cube_name == name + "cube2":
#                 active_cube_name = now_move_cube_name
#                 mouse_pos_begin = (x, y)
#             elif now_move_cube_name == name + "cube3":
#                 active_cube_name = now_move_cube_name
#                 mouse_pos_begin = (x, y)
#         print("右键按下")
#         is_pressing_R = True
#     if button == mouse.Button.right and not pressed:
#         print("右键松开")
#         is_pressing_R = False


def on_move(x, y):
    global mouse_pos_destination
    global is_pressing_L
    if is_pressing_L:
        mouse_pos_destination = (x, y)
    else:
        mouse_pos_destination = None


receiver = None
receiver_prev_location = None

def update_cube1_by_receiver():  # 如果receiver位置改变了，就更新cube1与receiver的位置对齐
    global receiver, cube1
    global receiver_prev_location

    name = bpy.context.scene.leftWindowObj
    plane_obj = bpy.data.objects.get(name + "ReceiverPlane")
    if plane_obj and cube1:
        if plane_obj.location != receiver_prev_location:
            # 计算方向向量
            direction = plane_obj.location - cube1.location
            direction.normalize()

            # 计算欧拉角
            rot_y = direction.to_track_quat('Y', 'Z').to_euler()

            # 设置旋转
            cube1.rotation_euler = rot_y
            receiver_prev_location = plane_obj.location.copy()



# 以下modal已经集成
class MoveCube(bpy.types.Operator):
    bl_idname = "object.movecube"
    bl_label = "移动立方体行为"

    __timer = None

    def invoke(self, context, event):
        global is_modal_start
        global cube1, cube2, cube3
        global move_cube1, move_cube2, move_cube3
        # global mouse_listener
        global ear_model
        global receiver,receiver_prev_location

        op_cls = MoveCube

        name = bpy.context.scene.leftWindowObj

        move_cube1 = bpy.data.objects.get(name + "move_cube1")
        move_cube2 = bpy.data.objects.get(name + "move_cube2")
        move_cube3 = bpy.data.objects.get(name + "move_cube3")
        cube1 = bpy.data.objects.get(name + "cube1")
        cube2 = bpy.data.objects.get(name + "cube2")
        cube3 = bpy.data.objects.get(name + "cube3")
        ear_model = bpy.data.objects.get(name)
        receiver = bpy.data.objects.get(name + "receiver")
        receiver.location = receiver.location.copy()

        bpy.context.scene.var = 120

        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.03, window=context.window)

        if not is_modal_start:
            is_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("movecube_modal_invoke")

        # if mouse_listener is None:
        #     mouse_listener = mouse.Listener(
        #         on_click=on_click,
        #         on_move=on_move
        #     )
        #     # 启动监听器
        #     mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_modal_start
        # global mouse_listener
        global prev_location1, prev_location2, prev_location3
        global prev_rotation1, prev_rotation2, prev_rotation3
        global last_inclusion1, last_inclusion2, last_inclusion3
        global cube1, cube2, cube3
        global move_cube1, move_cube2, move_cube3
        global now_move_cube_name, active_cube_name
        global can_move1, can_move2, can_move3
        global is_pressing_L
        global total_rot_x, total_rot_y, total_rot_z
        global receiver

        op_cls = MoveCube

        if (bpy.context.scene.var != 120):
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            # if mouse_listener:
            #     # 关闭监听器
            #     mouse_listener.stop()
            #     mouse_listener = None
            is_modal_start = False
            print("movecube_modal_finish")
            return {'FINISHED'}

        # print(f"当前鼠标状态：{on_which_move_cube(context, event)}")

        if cube1 and cube2 and cube3 and move_cube1 and move_cube2 and move_cube3 and ear_model:
            name = bpy.context.scene.leftWindowObj
            update_cube1_by_receiver()

            # 对于正在移动的组件，cube跟随move_cube移动，其他组件则将cube的位置直接复制到move_cube
            if active_cube_name == name + 'cube1':
                if can_move1:
                    lerp_move_far(cube1, move_cube1,0.3,0)
                if is_pressing_R:
                    equal_loc_and_rot(move_cube1, cube1)
            elif active_cube_name == name + 'cube2':
                if can_move2:
                    lerp_move_far(cube2, move_cube2,0.3,0)
                if is_pressing_R:
                    equal_loc_and_rot(move_cube2, cube2)
            elif active_cube_name == name + 'cube3':
                if can_move3:
                    lerp_move_far(cube3, move_cube3,0.3,0)
                if is_pressing_R:
                    equal_loc_and_rot(move_cube3, cube3)

            # 检测到在立方体上，切换到拖拽立方体工具
            if (on_which_move_cube(context, event) != 0):
                if on_which_move_cube(context, event) == 1 and is_changed_stepcut(context, event):
                    bpy.ops.object.select_all(action='DESELECT')
                    move_cube1.select_set(True)
                    bpy.context.view_layer.objects.active = move_cube1
                    # print("on cube1")
                    now_move_cube_name = name + "cube1"
                    total_rot_x = total_rot_y = total_rot_z = 0
                    bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
                elif on_which_move_cube(context, event) == 2 and is_changed_stepcut(context, event):
                    bpy.ops.object.select_all(action='DESELECT')
                    move_cube2.select_set(True)
                    bpy.context.view_layer.objects.active = move_cube2
                    now_move_cube_name = name + "cube2"
                    total_rot_x = total_rot_y = total_rot_z = 0
                    bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
                elif on_which_move_cube(context, event) == 3 and is_changed_stepcut(context, event):
                    bpy.ops.object.select_all(action='DESELECT')
                    move_cube3.select_set(True)
                    bpy.context.view_layer.objects.active = move_cube3
                    now_move_cube_name = name + "cube3"
                    total_rot_x = total_rot_y = total_rot_z = 0
                    bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
                elif on_which_move_cube(context, event) == 4 and is_changed_stepcut(context, event):
                    bpy.ops.object.select_all(action='DESELECT')
                    receiver.select_set(True)
                    bpy.context.view_layer.objects.active = receiver
                    now_move_cube_name = name + "receiver"
                    total_rot_x = total_rot_y = total_rot_z = 0
                    bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")

            # 正常情况下，切换到公共鼠标工具
            elif on_which_move_cube(context, event) == 0 and is_changed_stepcut(context, event):
                cur_obj = bpy.data.objects.get(name)

                bpy.ops.object.select_all(action='DESELECT')
                cur_obj.select_set(True)
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                bpy.context.view_layer.objects.active = cur_obj

            return {'PASS_THROUGH'}
        else:
            return {'PASS_THROUGH'}


def setActiveAndMoveCubeName(index):
    global active_cube_name
    global now_move_cube_name
    global total_rot_x
    global total_rot_y
    global total_rot_z

    active_cube_name = None
    now_move_cube_name = None

    name = bpy.context.scene.leftWindowObj
    total_rot_x = total_rot_y = total_rot_z = 0
    if(index == 4):
        now_move_cube_name = name + "receiver"
    else:
        now_move_cube_name = name + "cube" + str(index)



def initCube():
    '''
    全局变量初始化赋值
    '''
    global cube1, cube2, cube3
    global move_cube1, move_cube2, move_cube3
    # global mouse_listener
    global ear_model
    global receiver, receiver_prev_location


    name = bpy.context.scene.leftWindowObj

    move_cube1 = bpy.data.objects.get(name + "move_cube1")
    move_cube2 = bpy.data.objects.get(name + "move_cube2")
    move_cube3 = bpy.data.objects.get(name + "move_cube3")
    cube1 = bpy.data.objects.get(name + "cube1")
    cube2 = bpy.data.objects.get(name + "cube2")
    cube3 = bpy.data.objects.get(name + "cube3")
    ear_model = bpy.data.objects.get(name)
    receiver = bpy.data.objects.get(name + "receiver")
    receiver.location = receiver.location.copy()


def resetCubeLocationAndRotation():
    '''
    将用于拖动的透明立方体的位置和旋转角度重置为 显示的立方体的位置
    '''
    name = bpy.context.scene.leftWindowObj
    move_cube1 = bpy.data.objects.get(name + "move_cube1")
    move_cube2 = bpy.data.objects.get(name + "move_cube2")
    move_cube3 = bpy.data.objects.get(name + "move_cube3")
    cube1 = bpy.data.objects.get(name + "cube1")
    cube2 = bpy.data.objects.get(name + "cube2")
    cube3 = bpy.data.objects.get(name + "cube3")
    if(move_cube1 != None and cube1 != None):
        if(move_cube1.location != cube1.location):
            move_cube1.location = cube1.location
        if (move_cube1.rotation_euler != cube1.rotation_euler):
            move_cube1.rotation_euler = cube1.rotation_euler
    if (move_cube2 != None and cube2 != None):
        if (move_cube2.location != cube2.location):
            move_cube2.location = cube2.location
        if (move_cube2.rotation_euler != cube2.rotation_euler):
            move_cube2.rotation_euler = cube2.rotation_euler
    if (move_cube3 != None and cube3 != None):
        if (move_cube3.location != cube3.location):
            move_cube3.location = cube3.location
        if (move_cube3.rotation_euler != cube3.rotation_euler):
            move_cube3.rotation_euler = cube3.rotation_euler




def update_cube_location_rotate(is_pressing_R):
    '''
    立方体移动的缓动效果
    '''
    global prev_location1, prev_location2, prev_location3
    global prev_rotation1, prev_rotation2, prev_rotation3
    global last_inclusion1, last_inclusion2, last_inclusion3
    global cube1, cube2, cube3
    global move_cube1, move_cube2, move_cube3
    # global now_move_cube_name, active_cube_name
    global can_move1, can_move2, can_move3
    global s1, s2, s3
    global is_pressing_L
    global total_rot_x, total_rot_y, total_rot_z
    global receiver


    if cube1 and cube2 and cube3 and move_cube1 and move_cube2 and move_cube3 and ear_model:

        update_cube1_by_receiver()

        name = bpy.context.scene.leftWindowObj
        active_obj = bpy.context.active_object
        if(active_obj != None):
            active_cube_name = active_obj.name
            # 对于正在移动的组件，cube跟随move_cube移动，其他组件则将cube的位置直接复制到move_cube
            if active_cube_name == name + 'move_cube1':
                cube1 = bpy.data.objects.get(name + 'cube1')
                if can_move1:
                    lerp_move_far(cube1, active_obj, 0.3, 0)
                if is_pressing_R:
                    equal_loc_and_rot(active_obj, cube1)
            elif active_cube_name == name + 'move_cube2':
                cube2 = bpy.data.objects.get(name + 'cube2')
                if can_move2:
                    lerp_move_far(cube2, active_obj, 0.3, 0)
                if is_pressing_R:
                    equal_loc_and_rot(active_obj, cube2)
            elif active_cube_name == name + 'move_cube3':
                cube3 = bpy.data.objects.get(name + 'cube3')
                if can_move3:
                    lerp_move_far(cube3, active_obj, 0.3, 0)
                if is_pressing_R:
                    equal_loc_and_rot(active_obj, cube3)


is_first_in1, is_first_in2, is_first_in3 = True, True, True
is_first_complete_in1, is_first_complete_in2, is_first_complete_in3 = True, True, True

mine_timer = 0
finish = True

def get_is_collision_finish():
    global finish
    return finish


def set_is_collision_finish(value):
    global finish
    finish = value


class MoveCube_collision(bpy.types.Operator):
    bl_idname = "object.movecube_collision"
    bl_label = "移动立方体行为"

    # __timer = None

    def invoke(self, context, event):
        global is_collision_modal_start
        global cube1, cube2, cube3
        global move_cube1, move_cube2, move_cube3
        global ear_model, inner_ear_model
        global last_inclusion1, last_inclusion2, last_inclusion3
        global prev_location1, prev_location2, prev_location3
        global prev_rotation1, prev_rotation2, prev_rotation3
        # global mat_silver, mat_red
        global is_first_in1, is_first_complete_in1, is_first_in2, is_first_complete_in2, is_first_in3, is_first_complete_in3
        global mine_timer

        op_cls = MoveCube_collision

        name = bpy.context.scene.leftWindowObj

        move_cube1 = bpy.data.objects.get(name + "move_cube1")
        move_cube2 = bpy.data.objects.get(name + "move_cube2")
        move_cube3 = bpy.data.objects.get(name + "move_cube3")
        cube1 = bpy.data.objects.get(name + "cube1")
        cube2 = bpy.data.objects.get(name + "cube2")
        cube3 = bpy.data.objects.get(name + "cube3")

        ear_model = bpy.data.objects.get(name)
        inner_ear_model = bpy.data.objects.get(name + 'shellInnerObj')

        if cube1 and cube2 and cube3 and inner_ear_model:
            last_inclusion1 = check_cube_inclusion(cube1, inner_ear_model)
            last_inclusion2 = check_cube_inclusion(cube2, inner_ear_model)
            last_inclusion3 = check_cube_inclusion(cube3, inner_ear_model)

            prev_location1 = cube1.location.copy()
            prev_location2 = cube2.location.copy()
            prev_location3 = cube3.location.copy()
            prev_rotation1 = cube1.rotation_euler.copy()
            prev_rotation2 = cube2.rotation_euler.copy()
            prev_rotation3 = cube3.rotation_euler.copy()

        # if not op_cls.__timer:
        #     op_cls.__timer = context.window_manager.event_timer_add(0.03, window=context.window)

        if not is_collision_modal_start:
            is_collision_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("movecube_collision_modal_invoke")

        bpy.ops.wm.tool_set_by_id(name="my_tool.addshellcanal2")

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_collision_modal_start
        global prev_location1, prev_location2, prev_location3
        global prev_rotation1, prev_rotation2, prev_rotation3
        global last_inclusion1, last_inclusion2, last_inclusion3
        global cube1, cube2, cube3
        global move_cube1, move_cube2, move_cube3
        global now_move_cube_name, active_cube_name, now_on_cube_name
        global can_move1, can_move2, can_move3
        global s1, s2, s3
        global mouse_pos_destination, mouse_pos_begin
        global is_pressing_L
        # global mat_red, mat_silver
        global is_first_in1, is_first_in2, is_first_in3, is_first_complete_in1, is_first_complete_in2, is_first_complete_in3
        global receiver, receiver_prev_location
        global mine_timer
        global finish

        op_cls = MoveCube_collision

        if (bpy.context.scene.muJuTypeEnum != "OP3"):
            # if op_cls.__timer:
            #     context.window_manager.event_timer_remove(op_cls.__timer)
            #     op_cls.__timer = None
            is_collision_modal_start = False
            print("movecube_collision_modal_finish")
            return {'FINISHED'}

        if finish:
            # if op_cls.__timer:
            #     context.window_manager.event_timer_remove(op_cls.__timer)
            #     op_cls.__timer = None
            is_collision_modal_start = False
            print("movecube_collision_modal_finish")
            return {'FINISHED'}

        print(f"mouse_pos_destination:{mouse_pos_destination}，mouse_pos_begin:{mouse_pos_begin}")

        print(f"当前鼠标状态：{on_which_move_cube(context, event)}")

        name = bpy.context.scene.leftWindowObj
        inner_ear_model = bpy.data.objects.get(name + 'shellInnerObj')
        if cube1 and cube2 and cube3 and move_cube1 and move_cube2 and move_cube3 and ear_model and inner_ear_model != None:
            update_cube1_by_receiver()

            s1 = check_cube_inclusion(cube1, inner_ear_model)
            s2 = check_cube_inclusion(cube2, inner_ear_model)
            s3 = check_cube_inclusion(cube3, inner_ear_model)

            if last_inclusion1 == 1 and s1 == 2:
                can_move1 = False
                print(f"now loc:{cube1.location},need:{prev_location1}")
                cube1.location = prev_location1.copy()
                cube1.rotation_euler = prev_rotation1.copy()

                #change_material_out(cube1, "to red")

                print("回退1")
            elif s1 == 1:
                prev_location1 = cube1.location.copy()
                prev_rotation1 = cube1.rotation_euler.copy()
                print("cube1完全在内部")
                print(f"当前cube1坐标{cube1.location}，之前保存的坐标{prev_location1}")
                can_move1 = True
                change_material_out(cube1, "to silver")
                if not is_pressing_L and active_cube_name == name + 'cube1':
                    active_cube_name = ""


            elif s1 == 0:
                prev_location1 = cube1.location.copy()
                prev_rotation1 = cube1.rotation_euler.copy()
                can_move1 = True

            if last_inclusion2 == 1 and s2 == 2:
                can_move2 = False
                print(f"now loc:{cube2.location},need:{prev_location2}")
                cube2.location = prev_location2.copy()
                cube2.rotation_euler = prev_rotation2.copy()
                #change_material_out(cube2, "to red")

                print("回退2")
            elif s2 == 1:
                prev_location2 = cube2.location.copy()
                prev_rotation2 = cube2.rotation_euler.copy()
                print("cube2完全在内部")
                print(f"当前cube2坐标{cube2.location}，之前保存的坐标{prev_location2}")
                can_move2 = True
                change_material_out(cube2, "to silver")
                if not is_pressing_L and active_cube_name == name + 'cube2':
                    active_cube_name = ""

            elif s2 == 0:
                prev_location2 = cube2.location.copy()
                prev_rotation2 = cube2.rotation_euler.copy()
                can_move2 = True

            if last_inclusion3 == 1 and s3 == 2:
                can_move3 = False
                cube3.location = prev_location3.copy()
                cube3.rotation_euler = prev_rotation3.copy()
                #change_material_out(cube3, "to red")

                print("回退2")
            elif s3 == 1:
                prev_location3 = cube3.location.copy()
                prev_rotation3 = cube3.rotation_euler.copy()
                print("cube2完全在内部")
                can_move3 = True
                change_material_out(cube3, "to silver")
                if not is_pressing_L and active_cube_name == name + 'cube3':
                    active_cube_name = ""

            elif s3 == 0:
                prev_location3 = cube3.location.copy()
                prev_rotation3 = cube3.rotation_euler.copy()
                can_move3 = True

            if s1 == 2:
                move_cube_along_normal(move_cube1, cube1, inner_ear_model)
                can_move1 = False
                change_material_out(cube1, "to red")

            if s2 == 2:
                move_cube_along_normal(move_cube2, cube2, inner_ear_model)
                can_move2 = False
                change_material_out(cube2, "to red")

            if s3 == 2:
                move_cube_along_normal(move_cube3, cube3, inner_ear_model)
                can_move3 = False
                change_material_out(cube3, "to red")

            last_inclusion1 = s1
            last_inclusion2 = s2
            last_inclusion3 = s3

            print(f"s1: {s1}, s2: {s2}, s3: {s3}")

            # # 对于正在移动的组件，cube跟随move_cube移动，其他组件则将cube的位置直接复制到move_cube
            # if active_cube_name == name + 'cube1':
            #     if can_move1:
            #         lerp_follow(cube1, move_cube1)
            #     equal_loc_and_rot(cube2, move_cube2)
            #     equal_loc_and_rot(cube3, move_cube3)
            #     if is_pressing_R:
            #         equal_loc_and_rot(move_cube1, cube1)
            # elif active_cube_name == name + 'cube2':
            #     if can_move2:
            #         lerp_follow(cube2, move_cube2)
            #     equal_loc_and_rot(cube1, move_cube1)
            #     equal_loc_and_rot(cube3, move_cube3)
            #     if is_pressing_R:
            #         equal_loc_and_rot(move_cube2, cube2)
            # elif active_cube_name == name + 'cube3':
            #     if can_move3:
            #         lerp_follow(cube3, move_cube3)
            #     equal_loc_and_rot(cube1, move_cube1)
            #     equal_loc_and_rot(cube2, move_cube2)
            #     if is_pressing_R:
            #         equal_loc_and_rot(move_cube3, cube3)
            #
            # # 检测到在立方体上，切换到拖拽立方体工具
            # if (on_which_move_cube(context, event) != 0):
            #     if on_which_move_cube(context, event) == 1 and is_changed_stepcut(context, event):
            #         bpy.ops.object.select_all(action='DESELECT')
            #         move_cube1.select_set(True)
            #         bpy.context.view_layer.objects.active = move_cube1
            #         print("on cube1")
            #         now_move_cube_name = name + "cube1"
            #         bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
            #     elif on_which_move_cube(context, event) == 2 and is_changed_stepcut(context, event):
            #         bpy.ops.object.select_all(action='DESELECT')
            #         move_cube2.select_set(True)
            #         bpy.context.view_layer.objects.active = move_cube2
            #         now_move_cube_name = name + "cube2"
            #         bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
            #     elif on_which_move_cube(context, event) == 3 and is_changed_stepcut(context, event):
            #         bpy.ops.object.select_all(action='DESELECT')
            #         move_cube3.select_set(True)
            #         bpy.context.view_layer.objects.active = move_cube3
            #         now_move_cube_name = name + "cube3"
            #         bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
            #     elif on_which_move_cube(context, event) == 4 and is_changed_stepcut(context, event):
            #         bpy.ops.object.select_all(action='DESELECT')
            #         receiver.select_set(True)
            #         bpy.context.view_layer.objects.active = receiver
            #         now_move_cube_name = name + "receiver"
            #         bpy.ops.wm.tool_set_by_id(name="my_tool.drag_cube")
            #
            # # 正常情况下，切换到公共鼠标工具
            # elif on_which_move_cube(context, event) == 0 and is_changed_stepcut(context, event):
            #     cur_obj = bpy.data.objects.get(name)
            #
            #     bpy.ops.object.select_all(action='DESELECT')
            #     cur_obj.select_set(True)
            #     bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            #     bpy.context.view_layer.objects.active = cur_obj

            # if 位置改变：

            collision_detection(active_cube_name)

            return {'PASS_THROUGH'}
        else:
            return {'PASS_THROUGH'}


def change_material(obj, mat):
    if obj.data.materials[0] != mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)

def change_material_out(obj, statement):
    global mine_timer
    # global mat_red, mat_silver

    if statement == 'to red' and obj.data.materials[0].name != "Red":
        obj.data.materials.clear()
        if bpy.data.materials.get("Red") is None:
            mat_red = newColor("Red", 1, 0.3, 0.35, 0, 0.01)
        obj.data.materials.append(bpy.data.materials.get("Red"))
    elif statement == 'to silver' and obj.data.materials[0].name != "Silver":
        mine_timer += 1
        if mine_timer >= 30:
            mine_timer = 0
            obj.data.materials.clear()
            if bpy.data.materials.get("Silver") is None:
                mat_silver = newColor("Silver", 0.588, 0.588, 0.588, 0, 0.01)
            obj.data.materials.append(bpy.data.materials.get("Silver"))

# === 跟随移动相关
rotation_stage = True
total_rot_x, total_rot_y, total_rot_z = 0, 0, 0

def get_view_matrix():
    """将坐标系改成“视图”并获得视图坐标系，用于后续在视图坐标系下旋转"""
    bpy.context.scene.transform_orientation_slots[0].type = 'VIEW'
    # 获取当前区域的 3D 视图
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    region_3d = space.region_3d
                    view_matrix = region_3d.view_matrix
                    view_matrix_inverted = view_matrix.inverted()

                    # 提取并转置视图矩阵，保留六位小数
                    matrix_transposed = tuple(
                        tuple(round(view_matrix_inverted[j][i], 6) for j in range(3))
                        for i in range(3)
                    )
    return matrix_transposed



def lerp_follow(cube, target, rotate_factor=0.03, speed1=0.07, rotate_factor1=0.01, speed2=0.2, rotate_factor2=0.0001, threshold=200, only_rot_threshold = 100):
    global rotation_stage

    print(f"lerp: {mouse_pos_begin}, {mouse_pos_destination}")
    if mouse_pos_begin and mouse_pos_destination:

        distance = math.sqrt((mouse_pos_destination[0] - mouse_pos_begin[0]) ** 2 +
                             (mouse_pos_destination[1] - mouse_pos_begin[1]) ** 2)
        if distance > threshold:
            rotation_stage = False
        if distance <only_rot_threshold:
            lerp_only_rot(cube, target, rotate_factor)
        elif rotation_stage:
            lerp_move_near(cube, target, speed1, rotate_factor1)
        else:
            lerp_move_near(cube, target, speed2, rotate_factor2)

def lerp_only_rot(cube, target, rotate_lerp_factor):
    global total_rot_x, total_rot_y, total_rot_z

    """
    插值跟随和旋转函数
    cube: 跟随的cube
    target: 目标cube
    speed: 固定移动速度
    rotate_lerp_factor: 旋转插值系数
    """
    # 计算位移向量
    direction = target.location - cube.location
    distance = direction.length

    relative_position = target.location - cube.location

    # 根据相对位置计算旋转角度
    angle_x = -relative_position.x * rotate_lerp_factor
    angle_y = relative_position.y * rotate_lerp_factor
    angle_z = -relative_position.z * rotate_lerp_factor

    total_rot_x += angle_x
    total_rot_y += angle_y
    total_rot_z += angle_z

    if total_rot_x >= 90 or total_rot_y >= 90 or total_rot_z >= 90:
        return

    # 当前旋转
    current_rotation = cube.rotation_euler

    # 插值旋转
    new_rotation = Euler((
        current_rotation.x + angle_x,
        current_rotation.y + angle_y,
        current_rotation.z + angle_z
    ), 'XYZ')

    cube.rotation_euler = new_rotation


def lerp_move_near(cube, target, speed=0.5, rotate_lerp_factor=0):
    global total_rot_x, total_rot_y, total_rot_z

    """
    插值跟随和旋转函数
    cube: 跟随的cube
    target: 目标cube
    speed: 固定移动速度
    rotate_lerp_factor: 旋转插值系数
    """
    # 计算位移向量
    direction = target.location - cube.location
    distance = direction.length

    # 如果距离大于速度，则移动，否则直接到达目标位置
    if distance > speed:
        direction.normalize()
        displacement = direction * speed
    else:
        displacement = direction

    # 更新位置
    cube.location += displacement

    # 计算相对位置
    relative_position = target.location - cube.location

    # 根据相对位置计算旋转角度
    angle_x = -relative_position.y * rotate_lerp_factor
    angle_y = relative_position.x * rotate_lerp_factor
    angle_z = -relative_position.x * rotate_lerp_factor

    total_rot_x += angle_x
    total_rot_y += angle_y
    total_rot_z += angle_z

    if total_rot_x >= 90 or total_rot_y >= 90 or total_rot_z >= 90:
        return

    # 当前旋转
    current_rotation = cube.rotation_euler

    # 插值旋转
    new_rotation = Euler((
        current_rotation.x + angle_x,
        current_rotation.y + angle_y,
        current_rotation.z + angle_z
    ), 'XYZ')

    cube.rotation_euler = new_rotation


def lerp_move_far(cube, target, speed=0.5, rotate_lerp_factor=0.01):
    """
    插值跟随和旋转函数
    cube: 跟随的cube
    target: 目标cube
    speed: 固定移动速度
    rotate_lerp_factor: 旋转插值系数
    """
    # 计算位移向量
    direction = target.location - cube.location
    distance = direction.length

    # 如果距离大于速度，则移动，否则直接到达目标位置
    if distance > speed:
        direction.normalize()
        displacement = direction * speed
    else:
        displacement = direction

    # 更新位置
    cube.location += displacement

    # 计算相对位置
    relative_position = target.location - cube.location

    # # 根据相对位置计算旋转角度
    # angle_x = -relative_position.y * rotate_lerp_factor
    # angle_y = relative_position.x * rotate_lerp_factor
    # angle_z = -relative_position.x * rotate_lerp_factor
    #
    # # 当前旋转
    # current_rotation = cube.rotation_euler
    #
    # # 插值旋转
    # new_rotation = Euler((
    #     current_rotation.x + angle_x,
    #     current_rotation.y + angle_y,
    #     current_rotation.z + angle_z
    # ), 'XYZ')
    #
    # cube.rotation_euler = new_rotation


def receiver_fit_rotate(normal,location):
    '''
    将支撑移动到位置location并将连界面与向量normal对齐垂直
    '''
    #获取支撑平面(支撑的父物体)
    name = bpy.context.scene.leftWindowObj
    planename = name + "ReceiverPlane"
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
    # 将支撑摆正对齐
    if(plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z


def cal_co(name, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :return: 相交的坐标
    '''

    active_obj = bpy.data.objects.get(name)

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


class HideReceiverDoubleClick(bpy.types.Operator):
    bl_idname = "hide.receiverdoubleclick"
    bl_label = "双击隐藏接收器位置"

    def invoke(self, context, event):
        # 将Plane隐藏
        name = bpy.context.scene.leftWindowObj
        if name == "右耳":
            useShellCanal = bpy.context.scene.useShellCanalR
        elif name == "左耳":
            useShellCanal = bpy.context.scene.useShellCanalL
        receiver_name = name + "receiver"
        receiver_obj = bpy.data.objects.get(receiver_name)
        co, normal = cal_co(receiver_name, context, event)
        if co != -1 and not receiver_obj.hide_get() and (bpy.data.objects.get(name + 'meshshelloutercanal') is not None
            or (bpy.data.objects.get(name + 'meshshelloutercanal') is None and not useShellCanal)):
            receiver_obj.hide_set(True)
        # self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}


class AdjustReceiverDoubleClick(bpy.types.Operator):
    bl_idname = "adjust.receiverdoubleclick"
    bl_label = "双击改变接收器位置"

    def invoke(self, context, event):
        # 将Plane激活并选中,位置设置为双击的位置
        name = bpy.context.scene.leftWindowObj
        receiver_name = name + "receiver"
        receiver_obj = bpy.data.objects.get(receiver_name)
        co, normal = cal_co(name, context, event)
        if co != -1 and receiver_obj.hide_get():
            receiver_fit_rotate(normal,co)
            update_cube1_by_receiver()
            receiver_obj.hide_set(False)
        # self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}


# =============
def equal_loc_and_rot(ori, tar):
    """
    将tar对象的location和rotation置为ori的
    """
    if ori and tar:
        tar.location = ori.location
        tar.rotation_euler = ori.rotation_euler


# 碰撞监测相关工具
def get_axes_from_object(obj):
    return [obj.matrix_world.to_3x3() @ axis for axis in [mathutils.Vector((1, 0, 0)),
                                                          mathutils.Vector((0, 1, 0)),
                                                          mathutils.Vector((0, 0, 1))]]


def get_object_vertices(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def find_mtv(axes, vertices1, vertices2):
    min_overlap = float('inf')
    mtv_axis = None

    for axis in axes:
        axis = axis.normalized()
        proj1 = [v.dot(axis) for v in vertices1]
        proj2 = [v.dot(axis) for v in vertices2]
        min1, max1 = min(proj1), max(proj1)
        min2, max2 = min(proj2), max(proj2)
        overlap = min(max1, max2) - max(min1, min2)
        if overlap < 0:
            return None, 0
        if overlap < min_overlap:
            min_overlap = overlap
            mtv_axis = axis

    return mtv_axis, min_overlap


def calculate_rotation_axis_and_angle(collision_point, centroid, threshold=0.1):
    rotation_axis = (collision_point - centroid).normalized()
    rotation_angle = -0.05

    if abs(rotation_axis.x) < threshold:
        rotation_axis.x = 0
    if abs(rotation_axis.y) < threshold:
        rotation_axis.y = 0
    if abs(rotation_axis.z) < threshold:
        rotation_axis.z = 0

    return rotation_axis, rotation_angle


def apply_transformations(obj, move_vector, rotation_axis, rotation_angle):
    obj.location += move_vector

    if rotation_axis.length_squared != 0:
        rotation_quaternion = mathutils.Quaternion(rotation_axis, rotation_angle)
        current_rotation = obj.rotation_euler.to_quaternion()
        new_rotation = (rotation_quaternion @ current_rotation).to_euler()
        obj.rotation_euler = new_rotation


def find_collision_point(obj1, obj2, mtv_axis, vertices1, vertices2):
    point1 = min(vertices1, key=lambda v: (v - obj1.matrix_world.translation).dot(mtv_axis))
    point2 = min(vertices2, key=lambda v: (v - obj2.matrix_world.translation).dot(-mtv_axis))
    collision_point = (point1 + point2) / 2
    return collision_point


def check_and_resolve_collision(obj1_name, obj2_name):
    global s1, s2, s3
    global prev_rotation1, prev_rotation2, prev_rotation3
    global prev_location1, prev_location2, prev_location3
    global cube1, cube2, cube3

    obj1 = bpy.data.objects[obj1_name]
    obj2 = bpy.data.objects[obj2_name]

    axes1 = get_axes_from_object(obj1)
    axes2 = get_axes_from_object(obj2)

    vertices1 = get_object_vertices(obj1)
    vertices2 = get_object_vertices(obj2)

    mtv_axis, min_overlap = find_mtv(axes1 + axes2, vertices1, vertices2)

    if mtv_axis is None:
        # print("没有碰撞")
        return False

    collision_point = find_collision_point(obj1, obj2, mtv_axis, vertices1, vertices2)
    print(f"碰撞点: {collision_point}")

    center1 = obj1.matrix_world.translation
    center2 = obj2.matrix_world.translation

    direction = center2 - center1
    if direction.dot(mtv_axis) < 0:
        mtv_axis = -mtv_axis

    move_vector = mtv_axis * min_overlap
    rotation_axis, rotation_angle = calculate_rotation_axis_and_angle(collision_point, center2)

    apply_transformations(obj2, move_vector, rotation_axis, rotation_angle)

    name = bpy.context.scene.leftWindowObj
    if obj2_name == name + 'cube1':
        if s1 == 2:
            cube1.location = prev_location1
            cube1.rotation_euler = prev_rotation1
    elif obj2_name == name + 'cube2':
        if s2 == 2:
            cube2.location = prev_location2
            cube2.rotation_euler = prev_rotation2
    elif obj2_name == name + 'cube3':
        if s3 == 2:
            cube3.location = prev_location3
            cube3.rotation_euler = prev_rotation3

    return True


def collision_detection(active_cube_name):
    """
    碰撞监测函数，一个主导对象、两个被动对象，主导对象会推动被动对象移动，被动对象之间其中一个作为主导
    active_cube: 本次碰撞检测作为主导的cube
    """
    name = bpy.context.scene.leftWindowObj
    obj1_name = name + "cube1"
    obj2_name = name + "cube2"
    obj3_name = name + "cube3"
    if active_cube_name == obj1_name:
        check_and_resolve_collision(obj1_name, obj2_name)
        check_and_resolve_collision(obj1_name, obj3_name)
        check_and_resolve_collision(obj2_name, obj3_name)
        check_and_resolve_collision(obj3_name, obj2_name)
    elif active_cube_name == obj2_name:
        check_and_resolve_collision(obj2_name, obj1_name)
        check_and_resolve_collision(obj2_name, obj3_name)
        check_and_resolve_collision(obj1_name, obj3_name)
        check_and_resolve_collision(obj3_name, obj1_name)
    elif active_cube_name == obj3_name:
        check_and_resolve_collision(obj3_name, obj1_name)
        check_and_resolve_collision(obj3_name, obj2_name)
        check_and_resolve_collision(obj1_name, obj2_name)
        check_and_resolve_collision(obj2_name, obj1_name)
    elif active_cube_name == "":
        check_and_resolve_collision(obj1_name, obj2_name)
        check_and_resolve_collision(obj1_name, obj3_name)
        check_and_resolve_collision(obj2_name, obj1_name)
        check_and_resolve_collision(obj2_name, obj3_name)
        check_and_resolve_collision(obj3_name, obj1_name)
        check_and_resolve_collision(obj3_name, obj2_name)
        equal_loc_and_rot(cube1, move_cube1)
        equal_loc_and_rot(cube2, move_cube2)
        equal_loc_and_rot(cube3, move_cube3)


# ===========
# 检测cube是否完全在模型内部/部分在模型内部/不在模型内部

def is_point_inside(obj, point):
    # 射线方向
    direction = Vector((1, 0, 0))
    count = 0

    # 投射射线，统计交点数量
    result, location, normal, index = obj.ray_cast(point, direction)
    while result:
        count += 1
        point = location + direction * 0.0001  # 移动到交点略微偏移的位置
        result, location, normal, index = obj.ray_cast(point, direction)

    # 奇偶规则判断
    return count % 2 == 1


def check_cube_inclusion(cube, complex_model):
    if cube.type != 'MESH' or complex_model.type != 'MESH':
        raise TypeError("Both objects must be of type 'MESH'")

    cube_vertices = [cube.matrix_world @ v.co for v in cube.data.vertices]
    inside_count = 0

    for vertex in cube_vertices:
        if is_point_inside(complex_model, vertex):
            inside_count += 1

    if inside_count == len(cube_vertices):
        return 1  # 完全在内部
    elif inside_count > 0:
        return 2  # 部分在内部
    else:
        return 0  # 完全不在内部


# ===== 自动摆放相关
def find_closest_vertex_index(cube, complex_cube):
    if cube.type != 'MESH' or complex_cube.type != 'MESH':
        return

    cube_world_matrix = cube.matrix_world
    complex_cube_world_matrix = complex_cube.matrix_world
    cube_location_world = cube_world_matrix.translation
    complex_cube_mesh = complex_cube.data

    bm = bmesh.new()
    bm.from_mesh(complex_cube_mesh)

    min_distance = float('inf')
    closest_vertex_index = -1

    for vert in bm.verts:
        vert_world_location = complex_cube_world_matrix @ vert.co
        distance = (vert_world_location - cube_location_world).length
        if distance < min_distance:
            min_distance = distance
            closest_vertex_index = vert.index

    bm.free()
    return closest_vertex_index


def move_cube_along_normal(move_cube, cube, complex_cube):
    closest_vertex_index = find_closest_vertex_index(cube, complex_cube)
    complex_cube_mesh = complex_cube.data

    bm = bmesh.new()
    bm.from_mesh(complex_cube_mesh)

    bm.verts.ensure_lookup_table()

    closest_vertex_normal = -bm.verts[closest_vertex_index].normal

    distance_factor = 0.1
    move_vector = closest_vertex_normal * distance_factor
    cube.location += move_vector

    move_cube.location = cube.location
    move_cube.rotation_euler = cube.rotation_euler

    bm.free()


class MoveCube_update(bpy.types.Operator):
    bl_idname = "object.updatecollision"
    bl_label = "更新碰撞检测的状态"
    bl_description = "激活或者暂停碰撞检测"

    def invoke(self, context, event):
        print("updatecollision invoke")
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        global finish
        if not finish:
            finish = True
        else:
            finish = False
            bpy.ops.object.movecube_collision('INVOKE_DEFAULT')

# ===
# def
# if (on_which_move_cube(context, event) != 0):
#     if on_which_move_cube(context, event) == 1:
#         now_on_cube_name = name + "cube1"
#     elif on_which_move_cube(context, event) == 2:
#         now_on_cube_name = name + "cube2"
#     elif on_which_move_cube(context, event) == 3:
#         now_on_cube_name = name + "cube3"
#     else:
#         now_on_cube_name = ""


# ===

def register():
    bpy.utils.register_class(MoveCube)
    bpy.utils.register_class(MoveCube_collision)
    bpy.utils.register_class(MoveCube_update)
    bpy.utils.register_class(HideReceiverDoubleClick)
    bpy.utils.register_class(AdjustReceiverDoubleClick)


def unregister():
    bpy.utils.unregister_class(MoveCube)
    bpy.utils.unregister_class(MoveCube_collision)
    bpy.utils.unregister_class(MoveCube_update)

