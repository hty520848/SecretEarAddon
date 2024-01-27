import bpy
import blf
import math
import re

import mathutils
import bpy_extras
from bpy_extras import view3d_utils
import bmesh

prev_on_object = False

prev_on_object_stepcut = 5

#厚度显示
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
    blf.draw(font_id, str(rounded_number)+"mm")

font_info = {
    "font_id": 0,
    "handler": None,
}


# 将物体移动到Right集合
def moveToRight(obj):
    collection = bpy.data.collections['Right']
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    # 物体在根集合下
    if obj.name in bpy.context.scene.collection.objects: 
        bpy.context.scene.collection.objects.unlink(obj) 
    print('start')
    for obj in collection.objects:
                print('Right',obj.name)
    print('end')

# 将物体移动到Left集合
def moveToLeft(obj):
    collection = bpy.data.collections['Left']
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    # 物体在根集合下
    if obj.name in bpy.context.scene.collection.objects: 
        bpy.context.scene.collection.objects.unlink(obj) 


# 获取VIEW_3D区域的上下文
def getOverride():
    area_type = 'VIEW_3D' # change this to use the correct Area Type context you want to process in
    areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
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



#根据传入的选中顶点组,将顶点组划分为边界点,内圈,外圈,并保存再对象中
class selectArea(object):
    def __init__(self, select_vert, color_lay,borderWidth):
        self.select_vert = select_vert
        self.borderWidth = borderWidth
        self.color_lay = color_lay
        self.border_out_vert = []  # 外边界顶点
        self.inner_vert = []
        self.out_vert = []  # 外圈顶点
        self.distance_dic = {}  # 每个顶点到边缘的距离
        self.order_border_co = [] # 顺序排列的边界坐标，用于绘制范围曲线

        # 分类顶点
        self.vertex_classification()
        self.get_order_border_co()
        self.draw_border_curve()

    #顶点组划分
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
                if round(colvert.x,3) == 1.000 and round(colvert.y,3) == 0.319 and round(colvert.z,3) == 0.133:  # 相邻点有黑色（0，0，0），表示为边界
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




#将选中的顶点组根据连通性划分,每个区域再划分为内外顶点组并保存再对象中
def get_continuous_area(select_vert, color_lay, borderWidth):
    for obj in bpy.data.objects:
        pattern = r'BorderCurveObject'
        if re.match(pattern, obj.name):
            # 删除以BorderCurveObject开头的物体
            bpy.data.objects.remove(obj, do_unlink=True)
    continuous_area = []  # 用于存放连续区域的class
    unprocessed_vertex = select_vert  # 用于存放未处理的节点
    visited_vert = []  # 存放被访问过的节点防止重复访问

    #处理所有选中顶点,一次循环生成一个连通区域
    while unprocessed_vertex: 
        area_vert = []  # 用于存放当前区域的顶点,即一个连通区域,初始化为空
        wait_to_find_link_vert = [unprocessed_vertex[0]]  # 初始化,加入第一个顶点
        visited_vert.append(unprocessed_vertex[0])
        unprocessed_vertex.remove(unprocessed_vertex[0])

         #一次循环生成一个连通区域
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


        #一片连通区域,所有顶点存放再area_vert,通过selectArea方法将其顶点分类到各个数组中并生成一个对象保存
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


# 判断鼠标状态是否发生改变
def is_changed(context, event):
    active_obj = context.active_object

    curr_on_object = False             # 当前鼠标是否在物体上,初始化为False
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
                curr_on_object = True                     # 如果发生交叉，将变量设为True
    if (curr_on_object != prev_on_object):
        prev_on_object = curr_on_object
        return True
    else:
        return False

# 判断鼠标在哪个物体上


def is_mouse_on_which_object(context, event):
    sphere1 = bpy.data.objects["StepCutSphere1"]
    sphere2 = bpy.data.objects["StepCutSphere2"]
    sphere3 = bpy.data.objects["StepCutSphere3"]
    sphere4 = bpy.data.objects["StepCutSphere4"]

    is_on_object = 5  # 初始化变量

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


def is_changed_stepcut(context, event):
    curr_on_object_stepcut = is_mouse_on_which_object(context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_stepcut  # 之前鼠标在那个物体上

    if (curr_on_object_stepcut != prev_on_object_stepcut):
        prev_on_object_stepcut = curr_on_object_stepcut
        return True
    else:
        return False
    
def convert_to_mesh(curve_name,depth):
    active_obj = bpy.data.objects[curve_name]
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "mesh" + active_obj.name 
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = depth # 设置曲线倒角深度
    bpy.ops.object.convert(target='MESH')  # 转化为网格
