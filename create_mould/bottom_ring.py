import bpy
import math
import bmesh
from ..tool import moveToRight, newColor
from contextlib import redirect_stdout
import io


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


def get_lowest_plane(high_percent):
    '''
    通过平面切片的方式，找到最小的环，即找最凹处
    :param high_percent:
    :return:
    '''
    # 获取套用模板后的初始高度
    template_height = get_plane_height(high_percent)
    min_distance = math.inf
    active_obj = bpy.context.active_object
    # 最凹切片边界点
    lowest_plane_border_point = list()
    # 最凹切片z坐标
    lowest_plane_height = math.inf
    h = template_height - 0.2
    while h < template_height + 0.2:
        distance = 0
        origin = (0, 0, h)
        for angle_degrees in range(0, 360, 1):
            direction = (
                math.cos(math.radians(angle_degrees)), math.sin(math.radians(angle_degrees)), 0)  # 举例：从起点向 x 轴正方向投射光线
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)

            if hit:
                # 相交后，继续向外走，找到最外侧的交点
                # 第一次交点
                count = 1
                while hit:
                    distance = distance + loc[0] ** 2 + loc[1] ** 2
                    # 去找下一个交点
                    # 注意 这里起始位置要往前走一点，否则一直会交在同一个点
                    hit, loc, normal, index = active_obj.ray_cast((loc[0] + math.cos(
                        math.radians(angle_degrees)) / 100, loc[1] + math.sin(
                        math.radians(angle_degrees)) / 100, loc[2]), direction)
                    # 相交次数+1
                    count = count + 1

        if distance < min_distance:
            min_distance = distance
            lowest_plane_height = h
        h = h + 0.1
    return lowest_plane_height


def curvature_calculation(a, b, c):
    '''
    输入a，b，c三点，计算点a的曲率
    :param a:
    :param b:
    :param c:
    :return:
    '''
    bc = ((c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2 + (c[2] - b[2]) ** 2) ** 0.5
    ab = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
    ac = ((c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2 + (c[2] - a[2]) ** 2) ** 0.5

    cos_bac = (ab ** 2 + ac ** 2 - bc ** 2) / (2 * ab * ac)
    sin_bac = (1 - cos_bac ** 2) ** 0.5
    # 曲率
    k = 2 * sin_bac / bc
    return k


def get_lowest_point(angle_degrees, z_co, count, origin_loc, origin_normal):
    '''
    算法大体思想是在当前平面内，找到距离z轴最近的点
    :param angle_degrees: 当前角度
    :param z_co: 模板的z坐标
    :param count: 第几个交点
    :param origin_loc: 模板套用后的初始点
    :return:
    '''
    # 获取活动对象
    active_obj = bpy.context.active_object

    min_distance = origin_loc[0] ** 2 + origin_loc[1] ** 2
    # 这个切片最大曲率
    max_curvature = 0

    lowest_point = origin_loc
    lowest_normal = origin_normal
    # 投射光线的方向
    direction = (math.cos(math.radians(angle_degrees)), math.sin(math.radians(angle_degrees)), 0)
    h = z_co
    while h < z_co + 1:
        up_origin = (0, 0, h + 0.2)
        down_origin = (0, 0, h - 0.2)
        origin = (0, 0, h)
        for times in range(0, count):  # 找到当前高度h的第n次交点（初始点是第几次交点就和第几次交点比）
            # todo 这里计算上面一个和下面一个顶点，然后计算高度为h的点的曲率，选择曲率最大的 并且这个点要比上下两点连线中点更靠z轴
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)
            # up_hit, up_loc, up_normal, up_index = active_obj.ray_cast(up_origin, direction)
            # down_hit, down_loc, down_normal, down_index = active_obj.ray_cast(down_origin, direction)

            if hit:  # 如果有交点，去找下一个交点
                origin = (loc[0] + math.cos(math.radians(angle_degrees)) / 100,
                          loc[1] + math.sin(math.radians(angle_degrees)) / 100, loc[2])
                # up_origin = (up_loc[0] + math.cos(math.radians(angle_degrees)) / 100,
                #           up_loc[1] + math.sin(math.radians(angle_degrees)) / 100, up_loc[2])
                # down_origin = (down_loc[0] + math.cos(math.radians(angle_degrees)) / 100,
                #           down_loc[1] + math.sin(math.radians(angle_degrees)) / 100, down_loc[2])
            else:
                break
        if hit:
            distance = loc[0] ** 2 + loc[1] ** 2
            # curvature = curvature_calculation(loc,up_loc,down_loc)
            # 切片距离法
            if distance < min_distance:
                min_distance = distance
                lowest_point = (loc[0], loc[1], loc[2])
                lowest_normal = normal
            # 切片曲率法
            # if curvature > max_curvature and (up_loc[0]/2+down_loc[0]/2)**2 +(up_loc[1]/2+down_loc[1]/2)**2 > distance:
            #     max_curvature = curvature
            #     lowest_point = (loc[0], loc[1], loc[2])
            #     lowest_normal = normal

        h = h + 0.2

    return lowest_point, lowest_normal


# 对顶点进行排序用于画圈
def get_order_border_vert(selected_verts):
    size = len(selected_verts)
    finish = False
    # 尝试使用距离最近的点
    order_border_vert = []
    now_vert = selected_verts[0]
    unprocessed_vertex = selected_verts  # 未处理顶点
    while len(unprocessed_vertex) > 1 and not finish:
        order_border_vert.append(now_vert)
        unprocessed_vertex.remove(now_vert)

        min_distance = math.inf
        now_vert_co = now_vert

        # 2024/1/2 z轴落差过大会导致问题，这里只考虑xy坐标
        for vert in unprocessed_vertex:
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert
        if min_distance > 3 and len(unprocessed_vertex) < 0.1 * size:
            finish = True
    return order_border_vert


# 绘制曲线
def draw_cut_border_curve(order_border_co, name, depth):
    active_obj = bpy.context.active_object
    new_node_list = list()
    for i in range(len(order_border_co)):
        if i % 2 == 1:  # 最后一个点连上去有点奇怪 所以换个方式
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

        # 为圆环上色
        # color_matercal = bpy.data.materials.new(name="BottomRingColor")
        # color_matercal.diffuse_color = (0.0, 0.0, 1.0, 1.0)
        # bpy.context.active_object.data.materials.append(color_matercal)
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


def translate_circle_to_object():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "BottomRingBorderR":
            bpy.context.view_layer.objects.active = obj

    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "ForCutR"
    bpy.context.collection.objects.link(duplicate_obj)
    # todo 先加到右耳集合，后续调整左右耳适配
    moveToRight(duplicate_obj)

    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "BottomRingBorderRForCutR":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')

    # # 合并简化网格
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        bpy.ops.mesh.remove_doubles(threshold=0.18)
    del stdout
    duplicate_obj.hide_set(True)


def boolean_apply():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    # 获取活动对象
    obj = bpy.context.active_object
    # 添加一个修饰器
    modifier = obj.modifiers.new(name="BottomCut", type='BOOLEAN')
    bpy.context.object.modifiers["BottomCut"].operation = 'DIFFERENCE'
    # todo 用交集可能会快点，但仍然有待测试
    # bpy.context.object.modifiers["BottomCut"].operation = 'UNION'
    bpy.context.object.modifiers["BottomCut"].object = bpy.data.objects["BottomRingBorderRForCutR"]
    # 2024/1/6 fast导致某些模型消失，暂时处理为改为exact，但是会很卡，后续找到问题所在再优化
    bpy.context.object.modifiers["BottomCut"].solver = 'EXACT'
    # 2024/1/17 发现洞大小会影响布尔的效果，不得已设置基于自身，导致非常的卡，需要未来优化
    bpy.context.object.modifiers["BottomCut"].use_self = True
    # 应用修改器
    bpy.ops.object.modifier_apply(modifier="BottomCut", single_user=True)

    # 重新生成网格物体
    bpy.data.objects.remove(bpy.data.objects['BottomRingBorderRForCutR'], do_unlink=True)
    bpy.context.view_layer.objects.active = bpy.data.objects['BottomRingBorderR']
    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "ForCutR"
    bpy.context.collection.objects.link(duplicate_obj)
    # todo 先加到右耳集合，后续调整左右耳适配
    moveToRight(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    bpy.ops.object.convert(target='MESH')


def cut_bottom_part():
    '''
    切割不需要的部分
    '''
    # 获取广搜的边界
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳OriginForCutR":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    active_obj = bpy.context.view_layer.objects.active

    before_me = active_obj.data
    # 创建bmesh对象
    before_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    before_bm.from_mesh(before_me)
    before_bm.verts.ensure_lookup_table()

    before_co = []
    for vert in before_bm.verts:
        before_co.append(vert.co)

    # 开始广搜
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    active_obj = bpy.context.active_object
    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    # 获取网格数据
    obj = bpy.context.active_object
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    # 获取最高点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    highest_vert = vert_order_by_z[0]

    # 从最高点开始 广搜
    # 切除下方，所以遍历到的顶点都是需要保存的
    save_part = []
    # 用于存放当前一轮还未处理的顶点
    wait_to_find_link_vert = []
    visited_vert = []  # 存放被访问过的节点防止重复访问
    un_reindex_vert = vert_order_by_z

    # 初始化处理第一个点
    wait_to_find_link_vert.append(highest_vert)
    visited_vert.append(highest_vert)
    un_reindex_vert.remove(highest_vert)

    while wait_to_find_link_vert:
        save_part.extend(wait_to_find_link_vert)
        temp_vert = []  # 存放下一层将要遍历的顶点，即与 wait_to_find_link_vert中顶点 相邻的点
        for vert in wait_to_find_link_vert:
            # 遍历顶点的连接边找寻顶点
            for edge in vert.link_edges:
                # 获取边的顶点
                v1 = edge.verts[0]
                v2 = edge.verts[1]
                # 确保获取的顶点不是当前顶点
                link_vert = v1 if v1 != vert else v2
                if link_vert not in visited_vert and link_vert.co in before_co:
                    temp_vert.append(link_vert)
                    visited_vert.append(link_vert)
                    un_reindex_vert.remove(link_vert)
        wait_to_find_link_vert = temp_vert
    # 反选，选出要删除的部分
    for i, v in enumerate(save_part):
        v.select_set(True)
    bpy.ops.mesh.select_all(action='INVERT')
    # 删除
    bpy.ops.mesh.delete(type='FACE')

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


def get_plane_height(high_percent):
    active_obj = bpy.context.active_object
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
    lowest_vert = vert_order_by_z[-1]

    return lowest_vert.co[2] + high_percent * (highest_vert.co[2] - lowest_vert.co[2])


def get_cut_border(high_percent):
    # 获取活动对象
    active_obj = bpy.context.active_object

    # 确保活动对象的类型是网格
    if active_obj.type == 'MESH':
        # origin z坐标后续根据比例来设置
        origin_z_co = get_plane_height(high_percent)
        # origin = (0, 0, get_lowest_plane(high_percent))
        origin = (0, 0, origin_z_co)
        # 存放最凹平面边界点
        lowest_plane_border = []
        order_border_co = []
        cut_plane = []
        angle_degrees = 0
        while angle_degrees < 360:
            direction = (
                math.cos(math.radians(angle_degrees)), math.sin(math.radians(angle_degrees)), 0)  # 举例：从起点向 x 轴正方向投射光线
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)

            if hit:
                # 相交后，继续向外走，找到最外侧的交点
                # 第一次交点
                count = 1
                while hit:
                    # todo 找到附近最凹处，并实现曲面切割
                    # todo 注意注意注意，如果之前加厚的时候设置了蜡厚度，那么模型就是一有内外壁的壳，必须判断交点是否在内外壁上
                    last_loc = loc
                    step = 0.5
                    lowest_point, lowest_normal = get_lowest_point(angle_degrees, origin_z_co, count,
                                                                   (loc[0], loc[1], loc[2]),
                                                                   (normal[0], normal[1], normal[2]))
                    border = (lowest_point[0] + lowest_normal[0] * step, lowest_point[1] + lowest_normal[1] * step,
                              lowest_point[2] + lowest_normal[2] * 0)

                    cut_plane.append(border)
                    order_border_co.append(lowest_point)
                    # 去找下一个交点
                    # 注意 这里起始位置要往前走一点，否则一直会交在同一个点
                    hit, loc, normal, index = active_obj.ray_cast((loc[0] + math.cos(
                        math.radians(angle_degrees)) / 100, loc[1] + math.sin(
                        math.radians(angle_degrees)) / 100, loc[2]), direction)
                    # 相交次数+1
                    count = count + 1
            angle_degrees = angle_degrees + 0.5
        # 2024/1/6 使用exact，曲线深度小于0.39也会有问题，这里设置为0.4
        draw_cut_border_curve(get_order_border_vert(order_border_co), "BottomRingBorderR", 0.18)
        draw_cut_border_curve(get_order_border_vert(cut_plane), "CutPlane", 0)
        # todo 先加到右耳集合，后续调整左右耳适配
        moveToRight(bpy.data.objects["BottomRingBorderR"])
        moveToRight(bpy.data.objects["CutPlane"])


def judge_normals():
    flag = True
    cut_plane = bpy.data.objects["CutPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)

    for v in cut_plane_mesh.verts:
        if v.normal[2] > 0:
            flag = False

    return flag


def get_cut_plane():
    bpy.data.objects["右耳"].select_set(False)
    cut_plane = bpy.data.objects["CutPlane"]
    bpy.context.view_layer.objects.active = cut_plane
    cut_plane.select_set(True)
    bpy.ops.object.convert(target='MESH')

    # 填充平面
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.fill()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.edge_face_add()

    if judge_normals():
        bpy.ops.mesh.flip_normals()

    bpy.data.objects["CutPlane"].select_set(False)
    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
    bpy.data.objects["右耳"].select_set(True)
    cut_plane.hide_set(True)
    bpy.ops.object.mode_set(mode='OBJECT')


def plane_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    # 获取活动对象
    obj = bpy.context.active_object
    # 添加一个修饰器
    modifier = obj.modifiers.new(name="BottomCut", type='BOOLEAN')
    bpy.context.object.modifiers["BottomCut"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["BottomCut"].object = bpy.data.objects["CutPlane"]

    bpy.context.object.modifiers["BottomCut"].solver = 'EXACT'
    # 应用修改器
    bpy.ops.object.modifier_apply(modifier="BottomCut", single_user=True)

    # 获取下边界顶点用于挤出
    bpy.ops.object.mode_set(mode='EDIT')
    # 创建bmesh对象
    bm = bmesh.from_edit_mesh(bpy.data.objects["右耳"].data)
    bottom_outer_border_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.delete(type='FACE')

    ori_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 将下边界加入顶点组
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')


def judge_if_need_invert():
    obj = bpy.data.objects["右耳"]
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    obj = bpy.data.objects["右耳"]
    bm = bmesh.from_edit_mesh(obj.data)
    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        # 判断最低点是否被选择
        invert_flag = judge_if_need_invert()

        if not invert_flag:
            # 不需要反转，直接删除面即可
            bpy.ops.mesh.delete(type='FACE')
        else:
            # 反转一下，删除顶点
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

    # 最后，删一下边界的直接的面
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = bpy.data.objects["右耳"].vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 最后删掉没用的CutPlane
    bpy.data.objects.remove(bpy.data.objects["CutPlane"], do_unlink=True)


def soft_eardrum_bottom_cut():
    # 复制一份模型
    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForCutR"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    # todo 先加到右耳集合，后续调整左右耳适配
    moveToRight(duplicate_obj)

    translate_circle_to_object()
    boolean_apply()
    cut_bottom_part()


def bottom_cut(high_percent):
    # 复制一份模型
    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForCutR"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    # todo 先加到右耳集合，后续调整左右耳适配
    moveToRight(duplicate_obj)

    get_cut_border(high_percent)
    get_cut_plane()
    plane_cut()
    delete_useless_part()

    # translate_circle_to_object()
    # boolean_apply()
    # cut_bottom_part()
