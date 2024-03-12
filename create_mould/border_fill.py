import bpy
import bmesh
import math
from contextlib import redirect_stdout
import io
from ..utils.utils import utils_re_color
from .dig_hole import dig_hole
from ..tool import *


def get_different_vert(after_bm, before_bm):
    different_vert_co = []
    different_vert_index = []
    before_co = []
    for vert in before_bm.verts:
        before_co.append(vert.co)

    for vert in after_bm.verts:
        if vert.co not in before_co:
            different_vert_co.append(vert.co)
            different_vert_index.append(vert.index)

    return different_vert_index, different_vert_co


def get_up_center_point(selected_verts_co):
    size = len(selected_verts_co)
    center = [0, 0, 0]
    for vert in selected_verts_co:
        center[0] += vert[0]
        center[1] += vert[1]
        center[2] += vert[2]

    center[0] /= size
    center[1] /= size
    center[2] /= size

    return center


def extrude_border(border_co, bm):
    bpy.ops.mesh.select_all(action='DESELECT')

    outside_border_vert = []
    for v in bm.verts:
        if v.co in border_co:
            outside_border_vert.append(v)

    # 选中边界的边
    outside_edges = set()
    # 遍历选中的顶点
    for vert in outside_border_vert:
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in outside_border_vert and edge.verts[1] in outside_border_vert:
                outside_edges.add(edge)

    for v in outside_border_vert:
        v.select_set(True)

    for edge in outside_edges:
        edge.select_set(True)

    # 复制选中的顶点并沿着各自的法线方向移动
    bpy.ops.mesh.duplicate()

    # 获取所有选中的顶点
    inside_border_vert = [v for v in bm.verts if v.select]
    inside_border_vert_index = [v.index for v in inside_border_vert]
    inside_edges = [e for e in bm.edges if e.select]
    thickness = bpy.context.scene.zongHouDu
    for i, vert in enumerate(inside_border_vert):
        vert.co -= outside_border_vert[i].normal * thickness  # 沿法线方向移动

    # 重新选中外边界
    for v in outside_border_vert:
        v.select_set(True)

    for edge in outside_edges:
        edge.select_set(True)

    bpy.ops.mesh.bridge_edge_loops()

    return inside_border_vert_index, inside_border_vert, inside_edges


def remove_doubles(threshold, inside_border_vert, inside_edges, bm):
    # 为了防止问题，桥接完了再简化合并顶点
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in inside_border_vert:
        v.select_set(True)
    for e in inside_edges:
        e.select_set(True)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # any printing or operator output within this block
        # will go into 'stdout'
        bpy.ops.mesh.remove_doubles(threshold=threshold)
    del stdout

    inside_border_vert = [v for v in bm.verts if v.select]

    return inside_border_vert


def fill_inner_border(up_inner_border, bottom_inner_border, target_bm):
    bpy.ops.mesh.select_all(action='DESELECT')
    # 选中上内边界的边
    up_inner_edges = set()
    # 遍历选中的顶点
    for vert in up_inner_border:
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in up_inner_border and edge.verts[1] in up_inner_border:
                up_inner_edges.add(edge)

    # 选中上内边界
    for v in up_inner_border:
        v.select_set(True)

    for edge in up_inner_edges:
        edge.select_set(True)

    # 选中下内边界的边
    bottom_inner_edges = set()
    # 遍历选中的顶点
    for vert in bottom_inner_border:
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in bottom_inner_border and edge.verts[1] in bottom_inner_border:
                bottom_inner_edges.add(edge)

        # 选中上内边界
    for v in bottom_inner_border:
        v.select_set(True)

    for edge in bottom_inner_edges:
        edge.select_set(True)
    # 桥接上下内边界
    bpy.ops.mesh.bridge_edge_loops()


def recover_and_refill():
    '''
    为了调整厚度后重新桥接
    '''
    # 恢复到桥接前
    bpy.data.objects.remove(bpy.data.objects["右耳"], do_unlink=True)

    cur_obj = bpy.data.objects["右耳OriginForFill"]
    cur_obj.hide_set(False)
    cur_obj.name = "右耳"
    bpy.context.view_layer.objects.active = cur_obj

    # 重新挤出
    # get_up_inner_border_and_fill()
    # 重新挖洞
    # dig_hole()


    utils_re_color("右耳", (1, 0.319, 0.133))


def getSmoothVertexGroup():
    # 将获取到的顶点加入到顶点组中
    name = "右耳"  # TODO    根据导入文件名称更改
    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForFill"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)

    # 最初始的，未挖孔与切割的为 XXXOriginForCreateMouldR
    origin_obj = bpy.data.objects["右耳OriginForCreateMouldR"]
    # 获取网格数据
    origin_mesh = origin_obj.data
    # 创建bmesh对象
    origin_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    origin_bm.from_mesh(origin_mesh)
    origin_bm.verts.ensure_lookup_table()

    # 挖孔后的物体为 XXXOriginForCutR
    dig_after_obj = bpy.data.objects["右耳OriginForCutR"]
    # 获取网格数据
    dig_after_mesh = dig_after_obj.data
    # 创建bmesh对象
    dig_after_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    dig_after_bm.from_mesh(dig_after_mesh)
    dig_after_bm.verts.ensure_lookup_table()

    # 挖孔,切割后的物体为 XXXOriginForFill
    fill_before_obj = bpy.data.objects["右耳OriginForFill"]
    # 获取网格数据
    fill_before_mesh = fill_before_obj.data
    # 创建bmesh对象
    fill_before_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    fill_before_bm.from_mesh(fill_before_mesh)
    fill_before_bm.verts.ensure_lookup_table()

    target_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    target_mesh = target_obj.data
    target_bm = bmesh.from_edit_mesh(target_mesh)

    # 获取上边界顶点
    _, up_border_co = get_different_vert(dig_after_bm, origin_bm)
    outer_border_index, _ = get_different_vert(fill_before_bm, origin_bm)
    bottom_outer_border_index, bottom_border_co = get_different_vert(fill_before_bm, dig_after_bm)
    up_outer_border_index = list(set(outer_border_index) - set(bottom_outer_border_index))

    up_inner_border_index, up_inner_border, up_inner_edge = extrude_border(up_border_co, target_bm)
    bottom_inner_border_index, bottom_inner_border, bottom_inner_edge = extrude_border(bottom_border_co, target_bm)

    bpy.ops.object.mode_set(mode='OBJECT')
    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    if (up_outer_border_vertex == None):
        up_outer_border_vertex = ori_obj.vertex_groups.new(name="UpOuterBorderVertex")
    for vert_index in up_outer_border_index:
        up_outer_border_vertex.add([vert_index], 1, 'ADD')

    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')

    up_inner_border_vertex = ori_obj.vertex_groups.get("UpInnerBorderVertex")
    if (up_inner_border_vertex == None):
        up_inner_border_vertex = ori_obj.vertex_groups.new(name="UpInnerBorderVertex")
    for vert_index in up_inner_border_index:
        up_inner_border_vertex.add([vert_index], 1, 'ADD')

    bottom_inner_border_vertex = ori_obj.vertex_groups.get("BottomInnerBorderVertex")
    if (bottom_inner_border_vertex == None):
        bottom_inner_border_vertex = ori_obj.vertex_groups.new(name="BottomInnerBorderVertex")
    for vert_index in bottom_inner_border_index:
        bottom_inner_border_vertex.add([vert_index], 1, 'ADD')


def applySmooth():
    ori_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_all(action='DESELECT')

    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    if (up_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.remove_doubles(threshold=0.8)

    bpy.ops.mesh.select_all(action='DESELECT')
    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    if (up_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    up_inner_border_vertex = ori_obj.vertex_groups.get("UpInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    if (up_inner_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.subdivide()

    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bottom_inner_border_vertex = ori_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.subdivide()

    bpy.ops.mesh.select_all(action='SELECT')

    up_inner_border_vertex = ori_obj.vertex_groups.get("UpInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    if (up_inner_border_vertex != None):
        bpy.ops.object.vertex_group_deselect()
    bottom_inner_border_vertex = ori_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.object.vertex_group_deselect()
    bpy.ops.object.vertex_group_deselect()
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    if (up_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()

    outer_border_vertex = ori_obj.vertex_groups.get("OuterBorderVertex")
    if (outer_border_vertex == None):
        outer_border_vertex = ori_obj.vertex_groups.new(name="OuterBorderVertex")
    outer_border_vertex = ori_obj.vertex_groups.get("OuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='OuterBorderVertex')
    if (outer_border_vertex != None):
        bpy.ops.object.vertex_group_assign()

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.modifier_add(type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].vertex_group = "OuterBorderVertex"
    bpy.ops.object.modifier_add(type='SMOOTH')
    bpy.context.object.modifiers["Smooth.001"].vertex_group = "OuterBorderVertex"
    bpy.context.object.modifiers["Smooth.001"].invert_vertex_group = True


def border_fill():
    target_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    target_mesh = target_obj.data
    target_bm = bmesh.from_edit_mesh(target_mesh)

    # 根据顶点组获取上下内边缘点
    up_inner_border = []
    bottom_inner_border = []

    up_inner_border_vertex = target_obj.vertex_groups.get("UpInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    if (up_inner_border_vertex != None):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        up_inner_border = [v for v in target_bm.verts if v.select]
    bottom_inner_border_vertex = target_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bottom_inner_border = [v for v in target_bm.verts if v.select]

    # 简化合并顶点
    # up_inner_border = remove_doubles(0.8, up_inner_border, up_inner_edge, target_bm)
    # bottom_inner_border = remove_doubles(0.8, bottom_inner_border, bottom_inner_edge, target_bm)

    fill_inner_border(up_inner_border, bottom_inner_border, target_bm)

    # 2024/1/20 改为先桥接再合并
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # any printing or operator output within this block
        # will go into 'stdout'
        # 2024/1/29 补面的褶皱暂时处理
        bpy.ops.mesh.remove_doubles(threshold=2)
    del stdout

    bmesh.update_edit_mesh(target_mesh)

    bpy.ops.object.mode_set(mode='OBJECT')


def hard_eardrum_extrude_border():
    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForFill"
    bpy.context.collection.objects.link(duplicate_obj)

    duplicate_obj.hide_set(True)

    # 挖孔后的物体为 XXXOriginForCutR
    dig_after_obj = bpy.data.objects["右耳OriginForCutR"]
    # 获取网格数据
    dig_after_mesh = dig_after_obj.data
    # 创建bmesh对象
    dig_after_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    dig_after_bm.from_mesh(dig_after_mesh)
    dig_after_bm.verts.ensure_lookup_table()

    # 挖孔,切割后的物体为 XXXOriginForFill
    fill_before_obj = bpy.data.objects["右耳OriginForFill"]
    # 获取网格数据
    fill_before_mesh = fill_before_obj.data
    # 创建bmesh对象
    fill_before_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    fill_before_bm.from_mesh(fill_before_mesh)
    fill_before_bm.verts.ensure_lookup_table()

    target_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    target_mesh = target_obj.data
    target_bm = bmesh.from_edit_mesh(target_mesh)

    bottom_border_co = get_different_vert(fill_before_bm, dig_after_bm)

    bottom_inner_border, bottom_inner_edge = extrude_border(bottom_border_co, target_bm)

    bpy.ops.mesh.select_all(action='DESELECT')
    for v in bottom_inner_border:
        v.select_set(True)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # any printing or operator output within this block
        # will go into 'stdout'
        bpy.ops.mesh.remove_doubles(threshold=1)
    del stdout

    bmesh.update_edit_mesh(target_mesh)

    bpy.ops.object.mode_set(mode='OBJECT')
    

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


def calculate_angle(x, y):
    # 计算原点与给定坐标点之间的角度（弧度）
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees


# 对顶点进行排序用于画圈
def get_order_border_vert(selected_verts):
    # 尝试使用距离最近的点
    order_border_vert = []
    now_vert = selected_verts[0]
    unprocessed_vertex = selected_verts  # 未处理顶点
    while len(unprocessed_vertex) > 1:
        order_border_vert.append(now_vert)
        unprocessed_vertex.remove(now_vert)

        min_distance = math.inf
        now_vert_co = now_vert

        for vert in unprocessed_vertex:
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2 + (
                    vert[2] - now_vert_co[2]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert

    return order_border_vert


# 绘制曲线
def draw_border_curve(order_border_co, name, depth):
    active_obj = bpy.context.active_object
    new_node_list = list()
    for i in range(len(order_border_co)):
        if i % 2 == 0:
            new_node_list.append(order_border_co[i])
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # 添加一个曲线样条
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(new_node_list) - 1)
    spline.use_cyclic_u = True

    # 设置每个点的坐标
    for i, point in enumerate(new_node_list):
        spline.points[i].co = (point[0], point[1], point[2], 1)

    # 更新场景
    # 这里可以自行调整数值
    # 解决上下文问题
    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.context.active_object.data.bevel_depth = depth
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj





def get_up_inner_border_and_fill():
    name = "右耳"  # TODO    根据导入文件名称更改
    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForFill"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    moveToRight(duplicate_obj)

    # extrude_border_by_vertex_groups("BottomOuterBorderVertex")

    template_highest_point = (-10.3681, 2.2440, 12.1771)
    template_hole_border = [(3.6963632106781006, 1.4901610612869263, -3.0596837997436523),
                            (4.024533748626709, 1.8914767503738403, -3.1757700443267822),
                            (12.843214988708496, -0.8718163967132568, -1.313320279121399),
                            (2.6411678791046143, 0.5748220086097717, -2.386669874191284),
                            (2.965087652206421, 0.8165469765663147, -2.6314637660980225),
                            (2.3731651306152344, 0.39150846004486084, -2.145109176635742),
                            (12.957918167114258, 0.3651430904865265, -1.4536579847335815),
                            (12.93639087677002, -0.1488054245710373, -1.4047847986221313),
                            (3.3082826137542725, 1.1020065546035767, -2.855614423751831),
                            (1.2946960926055908, -11.398612022399902, 1.6817331314086914),
                            (0.9249364733695984, -11.130483627319336, 1.729994773864746),
                            (8.55871295928955, -9.40313720703125, 0.5494974851608276),
                            (8.253859519958496, -9.740730285644531, 0.6620934009552002),
                            (12.507063865661621, 3.5011401176452637, -1.4343156814575195),
                            (12.629599571228027, 3.0158896446228027, -1.4442719221115112),
                            (12.838188171386719, 2.016106605529785, -1.4517091512680054),
                            (12.920886039733887, 1.4565234184265137, -1.4722768068313599),
                            (12.964752197265625, 0.8709620237350464, -1.4785915613174438),
                            (12.894177436828613, -0.5520572662353516, -1.3555926084518433),
                            (12.792250633239746, -1.191575527191162, -1.2710481882095337),
                            (12.665345191955566, -1.7101281881332397, -1.202019453048706),
                            (12.548029899597168, -2.1346137523651123, -1.1526480913162231),
                            (12.329446792602539, -2.7304937839508057, -1.0837055444717407),
                            (12.135722160339355, -3.245666980743408, -1.022111177444458),
                            (11.993698120117188, -3.6173882484436035, -0.9790816307067871),
                            (11.820446968078613, -4.023478031158447, -0.9251344799995422),
                            (11.648019790649414, -4.4161057472229, -0.8655819296836853),
                            (11.399292945861816, -4.988503932952881, -0.7775691151618958),
                            (11.146452903747559, -5.531449317932129, -0.6900633573532104),
                            (10.932639122009277, -5.946956157684326, -0.6179193258285522),
                            (10.69723892211914, -6.402900695800781, -0.5425477623939514),
                            (10.414801597595215, -6.877074718475342, -0.44408175349235535),
                            (10.047009468078613, -7.438182353973389, -0.28980565071105957),
                            (10.230905532836914, -7.157628059387207, -0.36694368720054626),
                            (9.725630760192871, -7.912663459777832, -0.12675721943378448),
                            (9.448588371276855, -8.289192199707031, 0.03424111753702164),
                            (9.178918838500977, -8.651290893554688, 0.20285460352897644),
                            (8.807927131652832, -9.10722541809082, 0.42653241753578186),
                            (7.872547149658203, -10.117976188659668, 0.7865674495697021),
                            (7.516564846038818, -10.444554328918457, 0.8883602619171143),
                            (6.861769199371338, -10.914847373962402, 1.0598691701889038),
                            (7.189167022705078, -10.67970085144043, 0.9741148352622986),
                            (6.408305644989014, -11.182273864746094, 1.1770790815353394),
                            (5.931820869445801, -11.413411140441895, 1.2979679107666016),
                            (5.426996231079102, -11.603611946105957, 1.4154208898544312),
                            (4.9288201332092285, -11.754626274108887, 1.517586588859558),
                            (4.3456902503967285, -11.880534172058105, 1.6075023412704468),
                            (3.7905044555664062, -11.945758819580078, 1.6145703792572021),
                            (3.295797348022461, -11.95645809173584, 1.614926815032959),
                            (2.8174421787261963, -11.942265510559082, 1.6223126649856567),
                            (2.3959758281707764, -11.89465045928955, 1.628889560699463),
                            (1.8277599811553955, -11.697726249694824, 1.6549468040466309),
                            (0.6209799647331238, -10.828849792480469, 1.7945162057876587),
                            (0.25474610924720764, -10.368200302124023, 1.8780310153961182),
                            (0.04115241765975952, -10.001692771911621, 1.943669080734253),
                            (-0.15488965809345245, -9.519744873046875, 2.014132022857666),
                            (-0.2806141972541809, -9.038475036621094, 2.0703227519989014),
                            (-0.4320831298828125, -8.210223197937012, 2.1518802642822266),
                            (-0.3563486635684967, -8.624348640441895, 2.1111016273498535),
                            (-0.5111169219017029, -7.552506446838379, 2.218980073928833),
                            (-0.4716000258922577, -7.881364345550537, 2.1854300498962402),
                            (-0.5510504245758057, -7.072164058685303, 2.261087417602539),
                            (-0.5644205212593079, -6.41131591796875, 2.301321268081665),
                            (-0.5577354431152344, -6.741740703582764, 2.2812042236328125),
                            (-0.5188507437705994, -5.70134973526001, 2.3133866786956787),
                            (-0.5416356325149536, -6.056333065032959, 2.307353973388672),
                            (-0.44446927309036255, -5.299101829528809, 2.2926900386810303),
                            (-0.33486518263816833, -4.820234775543213, 2.2214596271514893),
                            (-0.18607106804847717, -4.31535005569458, 2.0996124744415283),
                            (-0.05270791053771973, -3.8721120357513428, 1.951110601425171),
                            (0.0926927924156189, -3.3574347496032715, 1.7276159524917603),
                            (0.24543948471546173, -2.766591787338257, 1.4007498025894165),
                            (0.1690661460161209, -3.0620131492614746, 1.5641828775405884),
                            (0.35218748450279236, -2.353675603866577, 1.1189075708389282),
                            (0.42767372727394104, -2.082745313644409, 0.9185145497322083),
                            (0.5506889224052429, -1.6927212476730347, 0.6130993962287903),
                            (0.6739373207092285, -1.3594837188720703, 0.3363266885280609),
                            (0.8197004199028015, -0.9980949759483337, 0.013687835074961185),
                            (0.9898991584777832, -0.7172536253929138, -0.2826230823993683),
                            (1.1958669424057007, -0.4482511579990387, -0.6342360973358154),
                            (1.5044136047363281, -0.15686918795108795, -1.0913158655166626),
                            (1.7636206150054932, 0.01574736088514328, -1.4392938613891602),
                            (2.0508487224578857, 0.1972091794013977, -1.804146647453308),
                            (4.282073497772217, 2.4328341484069824, -3.12270188331604),
                            (4.414315700531006, 2.861362934112549, -3.0006484985351562),
                            (4.4772772789001465, 3.2650697231292725, -2.82511830329895),
                            (4.510844707489014, 3.7770605087280273, -2.5967326164245605),
                            (4.467644691467285, 4.170411109924316, -2.311485528945923),
                            (4.378695964813232, 4.522683143615723, -2.0483224391937256),
                            (4.26571798324585, 4.796703338623047, -1.7735249996185303),
                            (4.131589412689209, 5.086734294891357, -1.464192509651184),
                            (3.7876899242401123, 5.6696343421936035, -0.7011098265647888),
                            (3.932565450668335, 5.41098165512085, -1.0380185842514038),
                            (3.6419053077697754, 6.0005621910095215, -0.3522648513317108),
                            (3.489401340484619, 6.398372173309326, 0.004454396199434996),
                            (3.347088575363159, 6.852729797363281, 0.3221167325973511),
                            (3.185861587524414, 7.368130683898926, 0.606022834777832),
                            (3.046299695968628, 7.814704895019531, 0.7769927382469177),
                            (2.928696393966675, 8.311086654663086, 0.9026482105255127),
                            (2.8672969341278076, 8.945741653442383, 0.9690952301025391),
                            (2.897996664047241, 8.628413200378418, 0.9358717203140259),
                            (2.891712188720703, 9.357293128967285, 0.9649021625518799),
                            (2.969801425933838, 9.796195030212402, 0.9363983273506165),
                            (3.097370147705078, 10.205504417419434, 0.8732314109802246),
                            (3.2856178283691406, 10.632874488830566, 0.7777088284492493),
                            (3.5745866298675537, 11.104231834411621, 0.5956199765205383),
                            (4.128652572631836, 11.561172485351562, 0.29141369462013245),
                            (3.8516197204589844, 11.332701683044434, 0.4435167908668518),
                            (4.762118816375732, 11.825363159179688, 0.04528630152344704),
                            (4.445385932922363, 11.693267822265625, 0.1683499813079834),
                            (5.436573505401611, 11.935258865356445, -0.11917311698198318),
                            (5.099346160888672, 11.880311012268066, -0.03694340959191322),
                            (6.213705539703369, 11.933711051940918, -0.27600592374801636),
                            (5.82513952255249, 11.93448543548584, -0.19758953154087067),
                            (6.88806676864624, 11.800002098083496, -0.39216119050979614),
                            (6.550886631011963, 11.866856575012207, -0.33408355712890625),
                            (7.556390285491943, 11.561113357543945, -0.48957374691963196),
                            (7.22222900390625, 11.680557250976562, -0.44086745381355286),
                            (8.049548149108887, 11.341865539550781, -0.5583334565162659),
                            (8.45046329498291, 11.13294506072998, -0.6198112964630127),
                            (8.814872741699219, 10.910809516906738, -0.6696509718894958),
                            (9.278361320495605, 10.617928504943848, -0.7709121108055115),
                            (9.886222839355469, 10.064255714416504, -0.8519656658172607),
                            (9.582292556762695, 10.341092109680176, -0.8114389181137085),
                            (10.256876945495605, 9.505382537841797, -0.8454475402832031),
                            (10.071550369262695, 9.784819602966309, -0.8487065434455872),
                            (10.476049423217773, 9.050673484802246, -0.8667536973953247),
                            (10.6874418258667, 8.51396656036377, -0.9210289716720581),
                            (10.889609336853027, 8.0023832321167, -0.9859399199485779),
                            (11.088006973266602, 7.5226945877075195, -1.0642449855804443),
                            (11.335945129394531, 6.902442455291748, -1.1789638996124268),
                            (11.211976051330566, 7.212568759918213, -1.1216044425964355),
                            (11.537689208984375, 6.35111665725708, -1.2761951684951782),
                            (11.753602027893066, 5.7709197998046875, -1.360693097114563),
                            (11.944221496582031, 5.24810791015625, -1.4160056114196777),
                            (12.122294425964355, 4.769081115722656, -1.4440431594848633),
                            (12.339226722717285, 4.112521171569824, -1.4512174129486084),
                            (12.23076057434082, 4.44080114364624, -1.4476302862167358),
                            (12.7205810546875, 2.586670398712158, -1.4396191835403442)]

    active_obj = bpy.data.objects["右耳"]
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    bm2 = bm.copy()
    bm.verts.ensure_lookup_table()

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    highest_vert = vert_order_by_z[0]

    # 用于计算模板旋转
    # 特别注意，因为导入时候，每个模型的角度不同，所以要将模型最高点（即耳道顶部）x，y轴坐标旋转到模板位置
    angle_template = calculate_angle(template_highest_point[0], template_highest_point[1])
    angle_now = calculate_angle(highest_vert.co[0], highest_vert.co[1])
    rotate_angle = angle_now - angle_template

    dig_border = []  # 被选择的挖孔顶点
    inner_border = []

    for template_hole_border_point in template_hole_border:  # 通过向z负方向投射找到边界
        # 根据模板旋转的角度，边界顶点也做相应的旋转
        xx = template_hole_border_point[0] * math.cos(math.radians(rotate_angle)) - template_hole_border_point[
            1] * math.sin(math.radians(rotate_angle))
        yy = template_hole_border_point[0] * math.sin(math.radians(rotate_angle)) + template_hole_border_point[
            1] * math.cos(math.radians(rotate_angle))
        origin = (xx, yy, 10)
        direction = (0, 0, -1)
        hit, loc, normal, index = active_obj.ray_cast(origin, direction)
        if hit:
            dig_border.append((loc[0], loc[1], loc[2]))
            step = 1.5
            inner_border.append((loc[0] - normal[0] * step, loc[1] - normal[1] * step, loc[2] - normal[2] * step))

    order_hole_border_vert = get_order_border_vert(dig_border)

    # draw_border_curve(order_hole_border_vert, "HoleBorderCurve", 0.18)
    draw_border_curve(get_order_border_vert(inner_border), "InnerBorder", 0)

    fill_up_and_bottom()

    bpy.ops.object.mode_set(mode='OBJECT')


def fill_up_and_bottom():
    main_obj = bpy.data.objects["右耳"]
    main_obj.select_set(False)
    # 转换为网格
    up_border_obj = bpy.data.objects["InnerBorder"]
    bpy.context.view_layer.objects.active = up_border_obj
    up_border_obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    # 将边界曲线合并到物体
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    bpy.ops.object.join()
    # 获取顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_linked(delimit=set())
    bpy.ops.mesh.select_all(action='INVERT')

    bm = bmesh.from_edit_mesh(main_obj.data)
    up_fill_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    up_fill_border_vertex = main_obj.vertex_groups.get("UpFillBorderVertex")
    if (up_fill_border_vertex == None):
        up_fill_border_vertex = main_obj.vertex_groups.new(name="UpFillBorderVertex")
    for vert_index in up_fill_border_index:
        up_fill_border_vertex.add([vert_index], 1, 'ADD')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.remove_doubles(threshold=1)

    # 桥接上下循环边
    bottom_inner_border_vertex = main_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.object.vertex_group_select()

    # 将内壁边界分离出来方便桥接后平滑
    fill_and_smooth_inner_face()

    # 桥接各边
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    # 保证内外底边顶点数相同，减少三角面
    times = 2
    for i in range(0, times + 1):
        bpy.ops.mesh.subdivide()

    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=3.14159)



# 更新顶点组
def update_vert_group():
    ori_obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ori_obj.data)

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])

    # 选中最低点，并选择相连区域
    vert_order_by_z[0].select_set(True)
    bpy.ops.mesh.select_linked(delimit=set())

    inside_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='INVERT')
    up_fill_border_index = [v.index for v in bm.verts if v.select]

    bpy.ops.object.mode_set(mode='OBJECT')
    # 将下边界加入顶点组
    set_vert_group("BottomInnerBorderVertex", inside_border_index)
    # 将上边界加入顶点组
    set_vert_group("UpFillBorderVertex", up_fill_border_index)

    return up_fill_border_index, inside_border_index


# 利用几何节点重采样上下边界使其顶点数量一致
def resample_curve():
    obj = bpy.context.active_object
    bpy.ops.object.convert(target='CURVE')
    main_obj = bpy.data.objects["右耳"]

    obj.select_set(False)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bm = bmesh.from_edit_mesh(main_obj.data)
    outer_border_index_list = [v.index for v in bm.verts if v.select]
    origin_size = len(outer_border_index_list)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(True)
    main_obj.select_set(False)
    bpy.context.view_layer.objects.active = obj

    # 添加几何节点修改器
    modifier = obj.modifiers.new(name="Resample", type='NODES')
    bpy.ops.node.new_geometry_node_group_assign()

    node_tree = bpy.data.node_groups[0]
    node_links = node_tree.links

    input_node = node_tree.nodes[0]
    output_node = node_tree.nodes[1]

    resample_node = node_tree.nodes.new("GeometryNodeResampleCurve")
    resample_node.inputs[2].default_value = origin_size * 2

    node_links.new(input_node.outputs[0], resample_node.inputs[0])
    node_links.new(resample_node.outputs[0], output_node.inputs[0])

    bpy.ops.object.convert(target='MESH')

def sub_surface(up_index, bottom_index):
    bpy.ops.object.mode_set(mode='OBJECT')
    obj = bpy.context.active_object
    # 添加表面细分一个修饰器
    modifier = obj.modifiers.new(name="Smooth", type='SUBSURF')
    bpy.context.object.modifiers["Smooth"].subdivision_type = 'CATMULL_CLARK'
    bpy.context.object.modifiers["Smooth"].levels = 1
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    # 更新下底
    for i in bottom_index:
        bm.verts[i].select_set(True)
    # 遍历所有点，如果一个点有两个邻接点被选中，说明是边界细分出的点
    for v in bm.verts:
        count = 0
        for edge in v.link_edges:
            # 获取边的顶点
            v1 = edge.verts[0]
            v2 = edge.verts[1]
            # 确保获取的顶点不是当前顶点
            link_vert = v1 if v1 != v else v2
            if link_vert.select:
                count = count + 1
        if count == 2:
            bottom_index.append(v.index)

    bpy.ops.mesh.select_all(action='DESELECT')
    # 更新上底
    for i in up_index:
        bm.verts[i].select_set(True)
    # 遍历所有点，如果一个点有两个邻接点被选中，说明是边界细分出的点
    for v in bm.verts:
        count = 0
        for edge in v.link_edges:
            # 获取边的顶点
            v1 = edge.verts[0]
            v2 = edge.verts[1]
            # 确保获取的顶点不是当前顶点
            link_vert = v1 if v1 != v else v2
            if link_vert.select:
                count = count + 1
        if count == 2:
            up_index.append(v.index)

    bpy.ops.object.mode_set(mode='OBJECT')

    delete_vert_group("UpFillBorderVertex")
    delete_vert_group("BottomInnerBorderVertex")
    set_vert_group("UpFillBorderVertex", up_index)
    set_vert_group("BottomInnerBorderVertex", bottom_index)

    return up_index, bottom_index


def fill_and_smooth_inner_face():
    bpy.ops.mesh.separate(type='SELECTED')

    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != "右耳":
                inner_obj = obj
                bpy.context.view_layer.objects.active = inner_obj
            else:
                obj.select_set(False)

    resample_curve()
    up_index,bottom_index = update_vert_group()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='UpFillBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.fill_grid(span=0, offset=6)

    times = 2
    # 使用表面细分修改器
    for i in range(0,times):
        up_index,bottom_index = sub_surface(up_index,bottom_index)



    bpy.ops.object.mode_set(mode='OBJECT')
    # 合并内外壁
    main_obj = bpy.data.objects["右耳"]
    combine_obj = bpy.context.active_object

    main_obj.select_set(True)
    combine_obj.select_set(True)

    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()


def fill_frame_style_inner_face():
    name = "右耳"  # TODO    根据导入文件名称更改
    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForFill"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    moveToRight(duplicate_obj)

    extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")



    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.fill()
    bpy.ops.mesh.subdivide(number_cuts=4)

    bm = bmesh.from_edit_mesh(obj.data)
    inner_face_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("InnerFaceVertex",inner_face_index)

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="Smooth", type='LAPLACIANSMOOTH')
    bpy.context.object.modifiers["Smooth"].vertex_group = "InnerFaceVertex"
    bpy.context.object.modifiers["Smooth"].iterations = 20
    bpy.context.object.modifiers["Smooth"].lambda_factor = 20
    bpy.ops.object.modifier_apply(modifier="Smooth", single_user=True)