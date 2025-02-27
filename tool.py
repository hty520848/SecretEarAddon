import bpy
import blf
import math
import re
import sys
import os

import mathutils
import bpy_extras
from bpy_extras import view3d_utils
import bmesh
from mathutils import Vector
from collections import deque

prev_on_object = False

prev_on_object_stepcut = 5

# 控制台输出重定向
def output_redirect():
    # 获取 Blender 可执行文件的路径
    blender_exe_path = bpy.app.binary_path

    # 获取 Blender 可执行文件所在的目录
    blender_dir_path = os.path.dirname(blender_exe_path)
    # 重定向输出到文件
    log_file_path = os.path.join(blender_dir_path, "console_output.log")
    log_file = open(log_file_path, "w")  
    sys.stdout = log_file
    sys.stderr = log_file

    print("输出重定向已启动")


# 厚度显示
class MyHandleClass:
    _handler = None

    @classmethod
    def add_handler(cls, function, args=()):
        cls._handler = bpy.types.SpaceView3D.draw_handler_add(
            function, args, 'WINDOW', 'POST_PIXEL'
        )

    @classmethod
    def remove_handler(cls):
        if cls._handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(cls._handler, 'WINDOW')
            cls._handler = None


def draw_callback_px(self, thickness):
    """Draw on the viewports"""
    # BLF drawing routine
    font_id = font_info["font_id"]
    blf.position(font_id, 1300, 80, 0)
    blf.size(font_id, 50)
    rounded_number = round(thickness, 2)
    blf.draw(font_id, str(rounded_number) + "mm")


font_info = {
    "font_id": 0,
    "handler": None,
}


# 绘制右窗口标识R
def draw_right(self, text):
    """Draw on the viewports"""
    # BLF drawing routine
    override = getOverride()
    region = override['region']
    if bpy.context.window.workspace.name == '布局.001' and region.x == 0:
        font_id = font_info["font_id"]
        blf.color(0, 0.0, 0.0, 0.0, 1.0)
        blf.position(font_id, region.width - 100, region.height - 100, 0)
        blf.size(font_id, 50)
        blf.draw(font_id, text)


# 绘制左窗口标识L
def draw_left(self, text):
    """Draw on the viewports"""
    # BLF drawing routine
    override = getOverride2()
    region = override['region']
    if bpy.context.window.workspace.name == '布局.001' and region.x != 0:
        font_id = font_info["font_id"]
        blf.color(0, 0.0, 0.0, 0.0, 1.0)
        blf.position(font_id, region.width - 100, region.height - 100, 0)
        blf.size(font_id, 50)
        blf.draw(font_id, text)


# 根据集合名称获取layer_collection
def get_layer_collection(layer_collection, collection_name):
    if layer_collection.name == collection_name:
        return layer_collection
    for child in layer_collection.children:
        found = get_layer_collection(child, collection_name)
        if found:
            return found
    return None


# 将物体移动到Right集合
def moveToRight(obj):
    collection = bpy.data.collections['Right']
    collection2 = bpy.data.collections['Left']
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    if obj.name in collection2.objects:
        collection2.objects.unlink(obj)
    # 物体在根集合下
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)
        # print('start')
    # for obj in collection.objects:
    #             print('Right',obj.name)
    # print('end')


# 将物体移动到Left集合
def moveToLeft(obj):
    collection = bpy.data.collections['Left']
    collection2 = bpy.data.collections['Right']
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    if obj.name in collection2.objects:
        collection2.objects.unlink(obj)
    # 物体在根集合下
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)
        # print('start')
    # for obj in collection.objects:
    #             print('Left',obj.name)
    # print('end')


# 获取VIEW_3D区域的上下文
def getOverride():
    area_type = 'VIEW_3D'  # change this to use the correct Area Type context you want to process in
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
    #     raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")
        return

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override


# 第二个3d区域上下文
def getOverride2():
    area_type = 'VIEW_3D'  # change this to use the correct Area Type context you want to process in
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[1],
        'region': [region for region in areas[1].regions if region.type == 'WINDOW'][0],
    }

    return override


# 新建材质节点，模型颜色相关
def newMaterial(id):
    mat = bpy.data.materials.get(id)
    if mat is None:
        mat = bpy.data.materials.new(name=id)
    mat.use_nodes = True
    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()
    return mat


# 新建与顶点颜色相同的材质
def newShader(id):
    mat = newMaterial(id)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    color = nodes.new(type="ShaderNodeVertexColor")
    shader.inputs[6].default_value = 0.46
    shader.inputs[7].default_value = 0
    shader.inputs[9].default_value = 0.472
    shader.inputs[14].default_value = 1
    shader.inputs[15].default_value = 0.105
    links.new(color.outputs[0], nodes["Principled BSDF"].inputs[0])
    links.new(shader.outputs[0], output.inputs[0])
    return mat


# 新建与RGB颜色相同的材质
def newColor(id, r, g, b, is_transparency, transparency_degree):
    mat = newMaterial(id)
    mat.use_backface_culling = True
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


# 为指定物体添加材质
def appendColor(object_name, material_name):
    obj = bpy.data.objects.get(object_name)
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials.get(material_name))


def initialTransparency():
    mat = newColor("Transparency", 1, 0.319, 0.133, 1, 0.2)  # 创建材质
    mat.use_backface_culling = False
    # mat = newShader("Transparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2





# 获取区域和空间，鼠标行为切换相关
def get_region_and_space(context, area_type, region_type, space_type):
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


# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    active_obj = bpy.data.objects.get(context.scene.leftWindowObj)
    is_on_object = False  # 初始化变量

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    if event.mouse_region_x > region1.width:
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y))
    else:
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    if event.mouse_region_x > region1.width:
        region = region2
        space = area.spaces.active
        
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


# 判断鼠标状态是否发生改变
def is_changed(context, event):
    active_obj = bpy.data.objects.get(context.scene.leftWindowObj)

    curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
    global prev_on_object  # 之前鼠标是否在物体上

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    # 鼠标位于右边窗口
    if event.mouse_region_x > region1.width:
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y))
    else:
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    # 鼠标位于右边窗口
    if event.mouse_region_x > region1.width:
        region = region2
        space = area.spaces.active

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
                curr_on_object = True  # 如果发生交叉，将变量设为True
    if (curr_on_object != prev_on_object):
        prev_on_object = curr_on_object
        return True
    else:
        return False


# 在侧切模块判断鼠标在哪个圆球上
def is_mouse_on_which_object(obj_name, context, event):
    sphere1 = bpy.data.objects[obj_name+"StepCutSphere1"]
    sphere2 = bpy.data.objects[obj_name+"StepCutSphere2"]
    sphere3 = bpy.data.objects[obj_name+"StepCutSphere3"]
    sphere4 = bpy.data.objects[obj_name+"StepCutSphere4"]

    is_on_object = 5  # 初始化变量

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    # 鼠标位于右边窗口
    if event.mouse_region_x > region1.width:
        area_prop = [area for area in bpy.context.screen.areas if area.type == 'PROPERTIES']
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y-area_prop[0].height))
    else:
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    # 鼠标位于右边窗口
    if event.mouse_region_x > region1.width:
        region = region2
        space = area.spaces.active

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
    mwi = sphere1.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if sphere1.type == 'MESH':
        if (sphere1.mode == 'OBJECT'):
            mesh = sphere1.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = 1
                return is_on_object

    mwi2 = sphere2.matrix_world.inverted()
    mwi_start2 = mwi2 @ start
    mwi_end2 = mwi2 @ end
    mwi_dir2 = mwi_end2 - mwi_start2

    if sphere2.type == 'MESH':
        if (sphere2.mode == 'OBJECT'):
            mesh = sphere2.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start2, mwi_dir2, 2000.0)

            if fidx is not None:
                is_on_object = 2
                return is_on_object

    mwi3 = sphere3.matrix_world.inverted()
    mwi_start3 = mwi3 @ start
    mwi_end3 = mwi3 @ end
    mwi_dir3 = mwi_end3 - mwi_start3

    if sphere3.type == 'MESH':
        if (sphere3.mode == 'OBJECT'):
            mesh = sphere3.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start3, mwi_dir3, 2000.0)

            if fidx is not None:
                is_on_object = 3
                return is_on_object

    mwi4 = sphere4.matrix_world.inverted()
    mwi_start4 = mwi4 @ start
    mwi_end4 = mwi4 @ end
    mwi_dir4 = mwi_end4 - mwi_start4

    if sphere4.type == 'MESH':
        if (sphere4.mode == 'OBJECT'):
            mesh = sphere4.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start4, mwi_dir4, 2000.0)

            if fidx is not None:
                is_on_object = 4
                return is_on_object

    return is_on_object


def is_changed_stepcut(obj_name, context, event):
    curr_on_object_stepcut = is_mouse_on_which_object(obj_name, context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_stepcut  # 之前鼠标在那个物体上

    if (curr_on_object_stepcut != prev_on_object_stepcut):
        prev_on_object_stepcut = curr_on_object_stepcut
        return True
    else:
        return False


def convert_to_mesh(curve_name, mesh_name, depth):
    name = bpy.context.scene.leftWindowObj
    last_active_obj = bpy.context.active_object
    active_obj = bpy.data.objects[curve_name]
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    for object in bpy.data.objects:
        if object.name == mesh_name:
            bpy.data.objects.remove(object, do_unlink=True)
    duplicate_obj.name = mesh_name
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = depth  # 设置曲线倒角深度
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    if last_active_obj:
        bpy.context.view_layer.objects.active = last_active_obj
        bpy.ops.object.select_all(action='DESELECT')
        last_active_obj.select_set(state=True)


def recover_and_remind_border():
    '''
    恢复到进入切割模式并且保留边界线，用于挖孔，切割报错时恢复
    '''
    name = bpy.context.scene.leftWindowObj
    recover_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == name + "OriginForCreateMouldR":
            recover_flag = True
            break
    # 找到最初创建的  OriginForCreateMould 才能进行恢复
    if recover_flag:
        enum = bpy.context.scene.muJuTypeEnum
        if enum == 'OP4':
            # need_to_delete_model_name_list = [name, name + "OriginForFill", name + "OriginForDigHole"]
            need_to_delete_model_name_list = [name, name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                              "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                              name + "OuterRetopo", name + "InnerRetopo", name + "huanqiecompare"]
            curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(curve_list)
            # delete_hole_border()  # 删除框架式耳模中的挖孔边界

        elif enum == 'OP2':
            need_to_delete_model_name_list = [name, name + "HardEarDrumForSmooth", name + 'ForBottomFillReset']
            curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(curve_list)

        elif enum == "OP1":
            need_to_delete_model_name_list = [name, name + "FillPlane", name + "ForGetFillPlane", name + "Inner",
                                              "RetopoPart", name + "OuterOrigin", name + "InnerOrigin",
                                              name + "OuterRetopo", name + "InnerRetopo", name + "huanqiecompare"]
            curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(curve_list)

        elif enum == "OP3":
            need_to_delete_model_name_list = [name]
            curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                          name + "point", name + 'create_mould_sphere']
            delete_useless_object(need_to_delete_model_name_list)
            delete_useless_object(curve_list)

        # 将最开始复制出来的OriginForCreateMould名称改为模型名称
        obj.hide_set(False)
        obj.name = name

        bpy.context.view_layer.objects.active = obj
        # 恢复完后重新复制一份
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)

        # duplicate_obj = cur_obj.copy()
        # duplicate_obj.data = cur_obj.data.copy()
        # duplicate_obj.animation_data_clear()
        # duplicate_obj.name = cur_obj.name + "OriginForCutR"
        # bpy.context.collection.objects.link(duplicate_obj)
        # duplicate_obj.hide_set(True)
        # if name == '右耳':
        #     moveToRight(duplicate_obj)
        # elif name == '左耳':
        #     moveToLeft(duplicate_obj)


def recover_to_dig():
    '''
    恢复到挖孔前的状态
    '''
    recover_flag = False
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.context.view_layer.objects:
        if obj.name == name + "OriginForDigHole":
            recover_flag = True
            break
    # 找到最初创建的  OriginForDigHole 才能进行恢复
    if recover_flag:
        # 删除不需要的物体
        need_to_delete_model_name_list = [name, name + "OriginForFill", name + "Inner"]
        curve_list = [name + "dragcurve", name + "selectcurve", name + "colorcurve", name + 'coloredcurve',
                      name + "point", name + 'create_mould_sphere']
        for selected_obj in bpy.data.objects:
            if (selected_obj.name in need_to_delete_model_name_list):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
            elif (selected_obj.name in curve_list):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=False)
        # 将最开始复制出来的OriginForDigHole名称改为模型名称
        obj.hide_set(False)
        obj.name = name

        bpy.context.view_layer.objects.active = obj
        # 恢复完后重新复制一份
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForDigHole"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)


def utils_re_color(target_object_name, color):
    flag = False
    '''为模型重新上色'''
    # 遍历场景中的所有对象，并根据名称选择目标物体
    for obj in bpy.context.view_layer.objects:
        if obj.name == target_object_name:
            flag = True
            break
    if flag:
        me = obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            colvert.x = color[0]
            colvert.y = color[1]
            colvert.z = color[2]
        bm.to_mesh(me)
        bm.free()


def delete_useless_object(need_to_delete_model_name_list):
    for selected_obj in bpy.data.objects:
        if (selected_obj.name in need_to_delete_model_name_list):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=False)

def delete_hole_border():
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        for obj in bpy.data.objects:
            if re.match('右耳HoleBorderCurve', obj.name) is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
        for obj in bpy.data.objects:
            if re.match('右耳meshHoleBorderCurve', obj.name) is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
    elif name == '左耳':
        for obj in bpy.data.objects:
            if re.match('左耳HoleBorderCurve', obj.name) is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
        for obj in bpy.data.objects:
            if re.match('左耳meshHoleBorderCurve', obj.name) is not None:
                bpy.data.objects.remove(obj, do_unlink=True)

def subdivide(curve_name, subdivide_number):
    last_active_obj = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[curve_name]
    bpy.data.objects[curve_name].select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.subdivide(number_cuts=subdivide_number)  # 细分次数
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = last_active_obj
    bpy.ops.object.select_all(action='DESELECT')
    last_active_obj.select_set(state=True)


# 计算原点与给定坐标点之间的角度（弧度）
def calculate_angle(x, y):
    # 弧度
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees

# 获取模型最高点索引
def get_highest_vert(name):
    obj = bpy.data.objects[name]
    # 获取网格数据
    me = obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    return vert_order_by_z[0].index

# 获取投影参数
def get_change_parameters():
    tar_obj = bpy.context.scene.leftWindowObj
    ori_obj = bpy.context.scene.rightWindowObj
    
    obj_right = bpy.data.objects[ori_obj]
    obj_left = bpy.data.objects[tar_obj]

    # 获取模型最高点
    origin_highest_vert_index = get_highest_vert(ori_obj)
    target_highest_vert_index = get_highest_vert(tar_obj)

    origin_highest_vert = obj_right.data.vertices[origin_highest_vert_index].co @ obj_right.matrix_world
    target_highest_vert = obj_left.data.vertices[target_highest_vert_index].co @ obj_left.matrix_world
    print('origin_highest_vert',origin_highest_vert)
    print('target_highest_vert',target_highest_vert)
    # 计算旋转角度
    angle_origin = calculate_angle(origin_highest_vert[0], origin_highest_vert[1])
    angle_target = calculate_angle(target_highest_vert[0], target_highest_vert[1])
    rotate_angle = angle_target - angle_origin

    return rotate_angle, target_highest_vert[2] - origin_highest_vert[2]

def normal_ray_cast(index, rotate_angle, height_difference):

    closest_vert_index = None
    tar_obj = bpy.context.scene.leftWindowObj
    ori_obj = bpy.context.scene.rightWindowObj

    origin_obj = bpy.data.objects[ori_obj]
    me = origin_obj.data
    ori_bm = bmesh.new()
    ori_bm.from_mesh(me)
#    ori_bm.transform(origin_obj.matrix_world)
    ori_bm.verts.ensure_lookup_table()
    
    # 根据index获取相应顶点
    vert = ori_bm.verts[index]
    # 获取顶点的法向
    origin_normal = vert.normal
    origin_co = vert.co

    # 计算得到实际的起点坐标
    xx_co = origin_co[0] * math.cos(math.radians(rotate_angle)) - origin_co[1] * math.sin(math.radians(rotate_angle))
    yy_co = origin_co[0] * math.sin(math.radians(rotate_angle)) + origin_co[1] * math.cos(math.radians(rotate_angle))
    zz_co = origin_co[2] + height_difference
    actual_co = (xx_co, yy_co, zz_co)
    actual_co = Vector(actual_co)
    
    xx_normal = origin_normal[0] * math.cos(math.radians(rotate_angle)) - origin_normal[1] * math.sin(
        math.radians(rotate_angle))
    yy_normal = origin_normal[0] * math.sin(math.radians(rotate_angle)) + origin_normal[1] * math.cos(
        math.radians(rotate_angle))
    actual_normal = (xx_normal, yy_normal, origin_normal[2])
    
    target_obj = bpy.data.objects[tar_obj]
    target_mesh = target_obj.data

    # 创建bmesh对象
    target_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    target_bm.from_mesh(target_mesh)
    target_bm.transform(target_obj.matrix_world)
    target_bm.verts.ensure_lookup_table()
    target_bm.faces.ensure_lookup_table()
    target_bm.to_mesh(target_obj.data)
    target_obj.data.update()

    # hit, loc, normal, index = target_obj.ray_cast(actual_co, actual_normal)
    # # 没有命中，那就反向向内尝试一下
    # if not hit:
    #     # print('反向投射')
    #     reverse_normal = (-xx_normal, -yy_normal, -origin_normal[2])
    #     hit, loc, normal, index = target_obj.ray_cast(actual_co, reverse_normal)

    # if hit:
    #     target_bm.transform(target_obj.matrix_world.inverted())
    #     target_bm.to_mesh(target_obj.data)
    #     target_obj.data.update()
    #     # 返回命中面索引
    #     return index
    
    hit = False
    out_hit, out_loc, out_normal, out_index = target_obj.ray_cast(actual_co, actual_normal)

    # 反向向内
    reverse_normal = (-xx_normal, -yy_normal, -origin_normal[2])
    in_hit, in_loc, in_normal, in_index = target_obj.ray_cast(actual_co, reverse_normal)

    if out_hit and not in_hit:  # 向外命中，向内没命中
        hit = out_hit
        loc = out_loc
        normal = out_normal
        index = out_index

    elif not out_hit and in_hit:  # 向内命中，向外没命中
        hit = in_hit
        loc = in_loc
        normal = in_normal
        index = in_index

    elif out_hit and in_hit:  # 内外都命中
        out_distance = ((origin_co[0] - out_loc[0]) ** 2 + (origin_co[1] - out_loc[1]) ** 2 + (
                    origin_co[2] - out_loc[2]) ** 2) ** 0.5
        in_distance = ((origin_co[0] - in_loc[0]) ** 2 + (origin_co[1] - in_loc[1]) ** 2 + (
                    origin_co[2] - in_loc[2]) ** 2) ** 0.5

        if out_distance < in_distance:
            hit = out_hit
            loc = out_loc
            normal = out_normal
            index = out_index
        else:
            hit = in_hit
            loc = in_loc
            normal = in_normal
            index = in_index

    if hit:
        target_bm.transform(target_obj.matrix_world.inverted())
        target_bm.to_mesh(target_obj.data)
        target_obj.data.update()
        # 返回命中面索引
        return index


# 获取投射后的顶点index (目标obj名字，来源顶点index)
def get_cast_index(tar_obj,ori_index):
    cast_vertex_index = []
    obj_left = bpy.data.objects[tar_obj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj_left
    obj_left.select_set(True)

    print('镜像前')
    rotate_angle, height_difference = get_change_parameters()
    print('rotate_angle',rotate_angle)
    print('height_difference',height_difference)
    # 关于y轴镜像
    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
    if obj_left.type == 'MESH':
        left_me = obj_left.data
        left_bm = bmesh.new()
        left_bm.from_mesh(left_me)   

    print('镜像后')                   
    rotate_angle, height_difference = get_change_parameters()
    print('rotate_angle',rotate_angle)
    print('height_difference',height_difference)

    print('bofore num',len(ori_index))
            
    # 计算投影点
    for i in ori_index:
        face_index = normal_ray_cast(i,rotate_angle, height_difference)
        if face_index is not None:
            left_bm.faces.ensure_lookup_table()
            min = float('inf')
            total = Vector()
            for v in left_bm.faces[face_index].verts:
                total += v.co
            center = total/len(left_bm.faces[face_index].verts)
            for v in left_bm.faces[face_index].verts:
                vec = v.co - center
                between = vec.dot(vec)
                if (between <= min):
                    min = between
                    index = v.index
            left_bm.verts.ensure_lookup_table()
            print(left_bm.verts[index].co)
            cast_vertex_index.append(index)
            
    print('after num',len(cast_vertex_index))
    print('ori_index',ori_index)
    print('cast index',cast_vertex_index)
    # 镜像还原
    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))

    return cast_vertex_index


# def extrude_border_by_vertex_groups(ori_group_name, target_group_name):
#     name = bpy.context.scene.leftWindowObj
#     ori_obj = bpy.data.objects[name]
#     bpy.ops.object.mode_set(mode='EDIT')
#     bm = bmesh.from_edit_mesh(ori_obj.data)
#     bpy.ops.mesh.select_all(action='DESELECT')
#
#     outer_border_vertex = ori_obj.vertex_groups.get(ori_group_name)
#     bpy.ops.object.vertex_group_set_active(group=ori_group_name)
#     if (outer_border_vertex != None):
#         bpy.ops.object.vertex_group_select()
#         bpy.ops.mesh.remove_doubles(threshold=0.8)
#         outer_border = [v for v in bm.verts if v.select]
#         outer_edges = set()
#         extrude_direction = {}
#         # 遍历选中的顶点
#         for vert in outer_border:
#             key = (vert.co[0], vert.co[1], vert.co[2])
#             extrude_direction[key] = vert.normal
#             for edge in vert.link_edges:
#                 # 检查边的两个顶点是否都在选中的顶点中
#                 if edge.verts[0] in outer_border and edge.verts[1] in outer_border:
#                     outer_edges.add(edge)
#                     edge.select_set(True)
#
#         # 复制选中的顶点并沿着各自的法线方向移动
#         bpy.ops.mesh.duplicate()
#
#         # 获取所有选中的顶点
#         inside_border_vert = [v for v in bm.verts if v.select]
#         inside_border_index = [v.index for v in bm.verts if v.select]
#
#         inside_edges = [e for e in bm.edges if e.select]
#
#         thickness = bpy.context.scene.zongHouDu
#         for i, vert in enumerate(inside_border_vert):
#             key = (vert.co[0], vert.co[1], vert.co[2])
#             dir = extrude_direction[key]
#             vert.co -= dir * thickness  # 沿法线方向移动
#
#         # 重新选中外边界
#         for v in outer_border:
#             v.select_set(True)
#
#         for edge in outer_edges:
#             edge.select_set(True)
#
#         bpy.ops.mesh.bridge_edge_loops()
#
#         bpy.ops.object.mode_set(mode='OBJECT')
#         set_vert_group(target_group_name, inside_border_index)
#     return inside_border_index


def extrude_border_by_vertex_groups(ori_group_name, target_group_name):
    name = bpy.context.scene.leftWindowObj
    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ori_obj.data)
    bpy.ops.mesh.select_all(action='DESELECT')

    outer_border_vertex = ori_obj.vertex_groups.get(ori_group_name)
    bpy.ops.object.vertex_group_set_active(group=ori_group_name)
    if (outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.remove_doubles(threshold=0.7)
        outer_border = [v for v in bm.verts if v.select]
        outer_edges = set()
        extrude_direction = {}
        # 遍历选中的顶点
        for vert in outer_border:
            key = (vert.co[0], vert.co[1], vert.co[2])
            extrude_direction[key] = vert.normal
            for edge in vert.link_edges:
                # 检查边的两个顶点是否都在选中的顶点中
                if edge.verts[0] in outer_border and edge.verts[1] in outer_border:
                    outer_edges.add(edge)
                    edge.select_set(True)

        # 复制选中的顶点并沿着各自的法线方向移动
        bpy.ops.mesh.duplicate()

        # 获取所有选中的顶点
        inside_border_vert = [v for v in bm.verts if v.select]
        inside_border_index = [v.index for v in bm.verts if v.select]

        if name == '右耳':
            thickness = bpy.context.scene.zongHouDuR
        elif name == '左耳':
            thickness = bpy.context.scene.zongHouDuL
        for i, vert in enumerate(inside_border_vert):
            key = (vert.co[0], vert.co[1], vert.co[2])
            dir = extrude_direction[key]
            vert.co -= dir * thickness  # 沿法线方向移动
        bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
        bpy.ops.mesh.looptools_flatten(influence=100, lock_x=False, lock_y=False, lock_z=False, plane='best_fit',
                                       restriction='none')
        # bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)

        # 重新选中外边界
        for v in outer_border:
            v.select_set(True)

        for edge in outer_edges:
            edge.select_set(True)

        bpy.ops.mesh.bridge_edge_loops()

        bpy.ops.object.mode_set(mode='OBJECT')
        set_vert_group(target_group_name, inside_border_index)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group=target_group_name)
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group=ori_group_name)
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.object.mode_set(mode='OBJECT')

    return inside_border_index


def set_vert_group(group_name, vert_index_list):
    ori_obj = bpy.context.active_object

    vert_group = ori_obj.vertex_groups.get(group_name)
    if (vert_group == None):
        vert_group = ori_obj.vertex_groups.new(name=group_name)
    for vert_index in vert_index_list:
        vert_group.add([vert_index], 1, 'ADD')


def delete_vert_group(group_name):
    ori_obj = bpy.context.active_object

    vert_group = ori_obj.vertex_groups.get(group_name)
    if (vert_group != None):
        bpy.ops.object.vertex_group_set_active(group=group_name)
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)


def is_on_object(name, context, event):
    """ 当前鼠标位置是否在指定的物体上 """
    active_obj = bpy.data.objects[name]
    is_on_object = False  # 初始化变量

    # 获取鼠标光标的区域坐标
    override1 = getOverride()
    override2 = getOverride2()
    region1 = override1['region']
    region2 = override2['region']
    area = override2['area']
    if event.mouse_region_x > region1.width:
        new_x = event.mouse_region_x - region1.width
        mv = mathutils.Vector((new_x, event.mouse_region_y))
    else:
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    if event.mouse_region_x > region1.width:
        region = region2
        space = area.spaces.active

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

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


# 在不同模式间切换时选择不同的材质
def change_mat_mould(type):
    #  type=0 RGB模式， type=1 顶点颜色模式
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        mat = bpy.data.materials.get("YellowR")
    elif name == '左耳':
        mat = bpy.data.materials.get("YellowL")
    if mat:
        if type == 0:
            is_initial = False
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for node in nodes:
                if node.name == 'RGB':
                    is_initial = True
            if not is_initial:
                new_node = nodes.new(type="ShaderNodeRGB")
                new_node.outputs[0].default_value = (1.0, 0.319, 0.133, 1)
            for link in links:
                links.remove(link)
            links.new(nodes["RGB"].outputs[0], nodes["Principled BSDF"].inputs[0])
            links.new(nodes["Principled BSDF"].outputs[0], nodes["Material Output"].inputs[0])

        elif type == 1:
            is_initial = False
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for node in nodes:
                if node.name == 'Color Attribute':
                    is_initial = True
            if not is_initial:
                nodes.new(type="ShaderNodeVertexColor")
            for link in links:
                links.remove(link)
            links.new(nodes["Color Attribute"].outputs[0], nodes["Principled BSDF"].inputs[0])
            links.new(nodes["Principled BSDF"].outputs[0], nodes["Material Output"].inputs[0])


def laplacian_smooth(smooth_index, factor, iteration):
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    me = obj.data
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    select_vert = list()
    for index in smooth_index:
        select_vert.append(bm.verts[index])
    for i in range(iteration):
        final_co_dict = dict()
        for v in select_vert:
            final_co = v.co * 0
            for edge in v.link_edges:
                # 确保获取的顶点不是当前顶点
                link_vert = edge.other_vert(v)
                final_co += link_vert.co
            final_co /= len(v.link_edges)
            final_co_dict[v.index] = v.co + factor * (final_co - v.co)
        for v in select_vert:
            v.co = final_co_dict[v.index]

    bm.to_mesh(obj.data)
    bm.free()


def apply_material():
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        mat = bpy.data.materials.get("YellowR")
    elif name == '左耳':
        mat = bpy.data.materials.get("YellowL")
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def transform_normal(target_obj_name, vert_index_list):
    """
    将目标物体的法线信息传递给当前物体
    :param target_obj_name: 目标物体名称
    :param vert_index_list: 顶点索引列表
    """
    target_obj = bpy.data.objects[target_obj_name]

    main_obj = bpy.context.active_object
    vert_group = main_obj.vertex_groups.get("TransformBorder")
    if (vert_group == None):
        vert_group = main_obj.vertex_groups.new(name="TransformBorder")
    if len(vert_index_list) > 0:
        for vert_index in vert_index_list:
            vert_group.add([vert_index], 1, 'ADD')

    bpy.ops.object.shade_smooth()
    bpy.context.active_object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = 3.14159
    bpy.ops.object.modifier_add(type='DATA_TRANSFER')
    bpy.context.object.modifiers["DataTransfer"].object = target_obj
    bpy.context.object.modifiers["DataTransfer"].vertex_group = "TransformBorder"
    bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
    bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'CUSTOM_NORMAL'}
    bpy.context.object.modifiers["DataTransfer"].loop_mapping = 'POLYINTERP_LNORPROJ'
    bpy.ops.object.modifier_apply(modifier="DataTransfer", single_user=True)
