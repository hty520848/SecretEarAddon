import bpy
import blf
import math
import re

import mathutils
import bpy_extras
from bpy_extras import view3d_utils
import bmesh
from mathutils import Vector

prev_on_object = False

prev_on_object_stepcut = 5


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
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

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
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2


# 根据传入的选中顶点组,将顶点组划分为边界点,内圈,外圈,并保存再对象中
class selectArea(object):
    def __init__(self, select_vert, color_lay, borderWidth):
        self.select_vert = select_vert
        self.borderWidth = borderWidth
        self.color_lay = color_lay
        self.border_out_vert = []  # 外边界顶点
        self.inner_vert = []
        self.out_vert = []  # 外圈顶点
        self.distance_dic = {}  # 每个顶点到边缘的距离
        self.order_border_co = []  # 顺序排列的边界坐标，用于绘制范围曲线

        # 分类顶点
        self.vertex_classification()
        self.get_order_border_co()
        self.draw_border_curve()

    # 顶点组划分
    def vertex_classification(self):
        # 对于被选择的点，判断边界
        for vert in self.select_vert:
            # 遍历这些顶点的相邻节点
            for edge in vert.link_edges:
                # 获取边的顶点
                v1 = edge.verts[0]
                v2 = edge.verts[1]
                # 确保获取的顶点不是当前顶点
                link_vert = v1 if v1 != vert else v2
                colvert = link_vert[self.color_lay]
                if round(colvert.x, 3) == 1.000 and round(colvert.y, 3) == 0.319 and round(colvert.z,
                                                                                           3) == 0.133:  # 相邻点有黑色（0，0，0），表示为边界
                    if link_vert not in self.border_out_vert:
                        self.border_out_vert.append(link_vert)  # !!!!!!特别注意这里，边界是获取到的相邻节点而不是被选择的节点本身

        # 计算内圈顶点
        for vert in self.select_vert:
            # 计算和外边界顶点的最小距离
            min_distance = math.inf
            for out_vert in self.border_out_vert:
                distance = math.sqrt((vert.co[0] - out_vert.co[0]) ** 2 + (vert.co[1] - out_vert.co[1]) ** 2 + (
                        vert.co[2] - out_vert.co[2]) ** 2)  # 计算欧几里得距离
                if distance < min_distance:
                    min_distance = distance

            # 判断是否正在内边界里
            if min_distance > self.borderWidth:
                self.inner_vert.append(vert)
            # 保存顶点到边界的距离以便后续使用
            self.distance_dic[vert.index] = min_distance

        self.out_vert = [x for x in self.select_vert if x not in self.inner_vert]

        # 这一段代码用于处理特别尖锐的边缘
        for vert in self.out_vert:
            count = 0
            # 遍历这些顶点的相邻节点
            for edge in vert.link_edges:
                # 获取边的顶点
                v1 = edge.verts[0]
                v2 = edge.verts[1]
                # 确保获取的顶点不是当前顶点
                link_vert = v1 if v1 != vert else v2
                if link_vert in self.inner_vert:
                    count = count + 1
            if count >= 3:  # 如果外围顶点相邻的至少三个顶点是内部顶点，那就把该外围顶点加入内部顶点
                self.inner_vert.append(vert)

        self.out_vert = [x for x in self.select_vert if x not in self.inner_vert]

    def get_order_border_co(self):
        # 尝试使用距离最近的点
        now_vert = self.border_out_vert[0]
        unprocessed_vertex = self.border_out_vert  # 未处理顶点
        while len(unprocessed_vertex) > 1:
            self.order_border_co.append(now_vert.co)
            unprocessed_vertex.remove(now_vert)

            min_distance = math.inf
            now_vert_co = now_vert.co
            # 每次都找离当前顶点最近的顶点
            for vert in unprocessed_vertex:
                distance = math.sqrt((vert.co[0] - now_vert_co[0]) ** 2 + (vert.co[1] - now_vert_co[1]) ** 2 + (
                        vert.co[2] - now_vert_co[2]) ** 2)  # 计算欧几里得距离
                if distance < min_distance:
                    min_distance = distance
                    now_vert = vert

    def draw_border_curve(self):
        active_obj = bpy.context.active_object

        # print('曲线',active_obj.name)

        new_node_list = list()
        for i in range(len(self.order_border_co)):
            if i % 2 == 0:
                new_node_list.append(self.order_border_co[i])
        # newnodelist = [node % 2 for node in range(len(order_border_co))]
        # 创建一个新的曲线对象
        curve_data = bpy.data.curves.new(name="BorderCurve", type='CURVE')
        curve_data.dimensions = '3D'

        obj = bpy.data.objects.new("BorderCurveObject", curve_data)
        bpy.context.collection.objects.link(obj)
        if active_obj.name == '左耳':
            moveToLeft(obj)
        elif active_obj.name == '右耳':
            moveToRight(obj)
        bpy.context.view_layer.objects.active = obj

        # 添加一个曲线样条
        spline = curve_data.splines.new('NURBS')
        spline.points.add(len(new_node_list) - 1)
        spline.use_cyclic_u = True

        # 设置每个点的坐标
        for i, point in enumerate(new_node_list):
            spline.points[i].co = (point.x, point.y, point.z, 1)

        # 更新场景
        # 这里可以自行调整数值
        # 解决上下文问题
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.context.active_object.data.bevel_depth = 0.18
            bpy.context.view_layer.update()
            bpy.context.view_layer.objects.active = active_obj


# 将选中的顶点组根据连通性划分,每个区域再划分为内外顶点组并保存再对象中
def get_continuous_area(select_vert, color_lay, borderWidth):
    for obj in bpy.data.objects:
        pattern = r'BorderCurveObject'
        if re.match(pattern, obj.name):
            # 删除以BorderCurveObject开头的物体
            bpy.data.objects.remove(obj, do_unlink=True)
    continuous_area = []  # 用于存放连续区域的class
    unprocessed_vertex = select_vert  # 用于存放未处理的节点
    visited_vert = []  # 存放被访问过的节点防止重复访问

    # 处理所有选中顶点,一次循环生成一个连通区域
    while unprocessed_vertex:
        area_vert = []  # 用于存放当前区域的顶点,即一个连通区域,初始化为空
        wait_to_find_link_vert = [unprocessed_vertex[0]]  # 初始化,加入第一个顶点
        visited_vert.append(unprocessed_vertex[0])
        unprocessed_vertex.remove(unprocessed_vertex[0])

        # 一次循环生成一个连通区域
        while wait_to_find_link_vert:
            # 将这wait_to_find_link_vert的顶点全部加入区域顶点area_vert
            area_vert.extend(wait_to_find_link_vert)
            temp_vert = []  # 存放下一层将要遍历的顶点，即与 wait_to_find_link_vert中顶点 相邻的点
            for vert in wait_to_find_link_vert:
                for edge in vert.link_edges:
                    # 获取边的顶点
                    v1 = edge.verts[0]
                    v2 = edge.verts[1]
                    # 确保获取的顶点不是当前顶点
                    link_vert = v1 if v1 != vert else v2
                    # 若当前顶点被选中，且未被处理
                    if link_vert in unprocessed_vertex and link_vert not in visited_vert:
                        temp_vert.append(link_vert)
                        visited_vert.append(link_vert)
                        unprocessed_vertex.remove(link_vert)

            wait_to_find_link_vert = temp_vert

        # 一片连通区域,所有顶点存放再area_vert,通过selectArea方法将其顶点分类到各个数组中并生成一个对象保存
        area = selectArea(area_vert, color_lay, borderWidth)

        continuous_area.append(area)

    return continuous_area


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
    active_obj = context.active_object
    is_on_object = False  # 初始化变量

    if context.area:
        context.area.tag_redraw()

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
    active_obj = context.active_object

    curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
    global prev_on_object  # 之前鼠标是否在物体上

    if context.area:
        context.area.tag_redraw()

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


# 判断鼠标在哪个物体上


def is_mouse_on_which_object(obj_name,context, event):
    sphere1 = bpy.data.objects[obj_name+"StepCutSphere1"]
    sphere2 = bpy.data.objects[obj_name+"StepCutSphere2"]
    sphere3 = bpy.data.objects[obj_name+"StepCutSphere3"]
    sphere4 = bpy.data.objects[obj_name+"StepCutSphere4"]

    is_on_object = 5  # 初始化变量

    if context.area:
        context.area.tag_redraw()

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


def is_changed_stepcut(obj_name,context, event):
    curr_on_object_stepcut = is_mouse_on_which_object(obj_name,context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_stepcut  # 之前鼠标在那个物体上

    if (curr_on_object_stepcut != prev_on_object_stepcut):
        prev_on_object_stepcut = curr_on_object_stepcut
        return True
    else:
        return False


def convert_to_mesh(curve_name, mesh_name, depth):
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
    moveToRight(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = depth  # 设置曲线倒角深度
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    duplicate_obj.select_set(state=False)

def generate_cutplane():
    active_obj = bpy.data.objects['BottomRingBorderR']
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    # 获取曲线对象
    curve_object = bpy.data.objects['CutPlane']
    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
    # 获取数据
    curve_data = curve_object.data

    # 将曲线的每个顶点沿法向移动
    for spline in curve_data.splines:
        for point in spline.points:
            # 获取顶点原位置
            vertex_co = curve_object.matrix_world @ mathutils.Vector(point.co[0:3])
            _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)
            step = 0.2
            point.co = (point.co[0] - normal[0] * step, point.co[1] - normal[1] * step,
                        point.co[2] - normal[2] * step, 1)

    bpy.context.view_layer.objects.active = bpy.data.objects['CutPlane']
    bpy.context.object.data.bevel_depth = 0


def recover_and_remind_border():
    '''
    恢复到进入切割模式并且保留边界线，用于挖孔，切割报错时恢复
    '''
    recover_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == "右耳OriginForCreateMouldR":
            recover_flag = True
            break
    # 找到最初创建的  OriginForCreateMould 才能进行恢复
    if recover_flag:
        # 删除不需要的物体
        need_to_delete_model_name_list = ["右耳", "cutPlane", "右耳OriginForCutR",
                                          "右耳OriginForFill", "FillPlane", "右耳ForGetFillPlane", "右耳huanqiecompare",
                                          "dragcurve"]
        for selected_obj in bpy.data.objects:
            if (selected_obj.name in need_to_delete_model_name_list):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
        # 将最开始复制出来的OriginForCreateMould名称改为模型名称
        obj.hide_set(False)
        obj.name = "右耳"

        bpy.context.view_layer.objects.active = obj
        # 恢复完后重新复制一份
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        # todo 先加到右耳集合，后续调整左右耳适配
        moveToRight(duplicate_obj)

        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForCutR"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        moveToRight(duplicate_obj)


def recover_to_dig():
    '''
    恢复到挖孔前的状态
    '''
    recover_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == "右耳OriginForDigHole":
            recover_flag = True
            break
    # 找到最初创建的  OriginForDigHole 才能进行恢复
    if recover_flag:
        # 删除不需要的物体
        need_to_delete_model_name_list = ["右耳", "cutPlane",
                                          "右耳OriginForFill", "FillPlane", "右耳ForGetFillPlane", "右耳huanqiecompare",
                                          "dragcurve"]
        for selected_obj in bpy.data.objects:
            if (selected_obj.name in need_to_delete_model_name_list):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=False)
        # 将最开始复制出来的OriginForDigHole名称改为模型名称
        obj.hide_set(False)
        obj.name = "右耳"

        bpy.context.view_layer.objects.active = obj
        # 恢复完后重新复制一份
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForDigHole"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        # todo 先加到右耳集合，后续调整左右耳适配
        moveToRight(duplicate_obj)

        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForFill"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        moveToRight(duplicate_obj)


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


def subdivide(curve_name, subdivide_number):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[curve_name]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.subdivide(number_cuts=subdivide_number)  # 细分次数
    bpy.ops.object.mode_set(mode='OBJECT')

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

    hit, loc, normal, index = target_obj.ray_cast(actual_co, actual_normal)
    # 没有命中，那就反向向内尝试一下
    if not hit:
        print('反向投射')
        reverse_normal = (-xx_normal, -yy_normal, -origin_normal[2])
        hit, loc, normal, index = target_obj.ray_cast(actual_co, reverse_normal)

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