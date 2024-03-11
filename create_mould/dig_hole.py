import bpy
import bmesh
import math

from ..tool import moveToRight, convert_to_mesh, subdivide, newColor


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
        moveToRight(bpy.context.active_object)

        # 为圆环上色
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


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


def darw_cylinder(outer_dig_border, inner_dig_border):
    order_outer_dig_border = get_order_border_vert(outer_dig_border)
    order_inner_dig_border = get_order_border_vert(inner_dig_border)
    order_outer_top = []
    order_outer_bottom = []
    order_inner_top = []
    order_inner_bottom = []

    for v in order_outer_dig_border:
        order_outer_top.append((v[0],v[1],10))
        order_outer_bottom.append((v[0],v[1],v[2]-0.2))
    for v in order_inner_dig_border:
        order_inner_bottom.append((v[0],v[1],-5))
        order_inner_top.append((v[0],v[1],v[2]+ 1))

    draw_border_curve(order_outer_dig_border, "HoleBorderCurve", 0.18)
    draw_border_curve(order_outer_dig_border, "CylinderOuter", 0)
    draw_border_curve(order_inner_dig_border, "CylinderInner", 0)

    draw_border_curve(order_outer_top, "CylinderOuterTop", 0)
    draw_border_curve(order_outer_bottom, "CylinderOuterBottom", 0)

    draw_border_curve(order_inner_top, "CylinderInnerTop", 0)
    draw_border_curve(order_inner_bottom, "CylinderInnerBottom", 0)
    for obj in bpy.data.objects:
        obj.select_set(False)
    # 转换为网格，用于后续桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterTop"]
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuterTop"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuter"]
    bpy.data.objects["CylinderOuter"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuter"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterBottom"]
    bpy.data.objects["CylinderOuterBottom"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuterBottom"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerTop"]
    bpy.data.objects["CylinderInnerTop"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInnerTop"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInner"]
    bpy.data.objects["CylinderInner"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInner"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerBottom"]
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInnerBottom"].select_set(False)

    # 分段桥接出一个圆柱
    # 边合并边设置顶点组用于后续方便选择
    # 上段圆柱合并与桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterTop"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_top_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuterTop", cylinder_top_index)

    # 合并1，2段
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.data.objects["CylinderOuter"].select_set(True)
    bpy.ops.object.join()
    # 获取第二段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_outer_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuter", cylinder_outer_index)

    # 合并2，3段
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.data.objects["CylinderOuterBottom"].select_set(True)
    bpy.ops.object.join()
    # 获取第三段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuterBottom", cylinder_inner_index)

    # 依次桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderOuterTop')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderOuterBottom')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')

    # 修改切割圆柱名称
    bpy.data.objects["CylinderOuterTop"].name = "CylinderForOuterDig"
    bpy.data.objects["CylinderForOuterDig"].select_set(False)

    # 下段圆柱合并于桥接

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerBottom"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_top_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInnerBottom", cylinder_top_index)

    # 合并1，2段
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.data.objects["CylinderInner"].select_set(True)
    bpy.ops.object.join()
    # 获取第二段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_outer_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInner", cylinder_outer_index)

    # 合并2，3段
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.data.objects["CylinderInnerTop"].select_set(True)
    bpy.ops.object.join()
    # 获取第三段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInnerTop", cylinder_inner_index)

    # 依次桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderInnerTop')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderInnerBottom')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')

    # 修改切割圆柱名称
    bpy.data.objects["CylinderInnerBottom"].name = "CylinderForInnerDig"
    bpy.data.objects["CylinderForInnerDig"].select_set(False)

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
    bpy.data.objects["右耳"].select_set(True)


def boolean_dig():
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigOuterHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigOuterHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigOuterHole"].object = bpy.data.objects["CylinderForOuterDig"]
    bpy.context.object.modifiers["DigOuterHole"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="DigOuterHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_outer_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpOuterBorderVertex", up_outer_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("OuterHoleBorderVertex", up_outer_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigInnerHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigInnerHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigInnerHole"].object = bpy.data.objects["CylinderForInnerDig"]
    bpy.context.object.modifiers["DigInnerHole"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="DigInnerHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_inner_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpInnerBorderVertex", up_inner_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("InnerHoleBorderVertex", up_inner_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # 桥接上下边界
    bpy.ops.object.vertex_group_set_active(group='InnerHoleBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.object.vertex_group_set_active(group='OuterHoleBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.bridge_edge_loops()

    # 删除辅助用的物体
    bpy.data.objects.remove(bpy.data.objects["CylinderForInnerDig"], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["CylinderForOuterDig"], do_unlink=True)

    delete_vert_group("InnerHoleBorderVertex")
    delete_vert_group("OuterHoleBorderVertex")

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


# 获取洞边界顶点
def get_hole_border(template_highest_point, template_hole_border):
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
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

        outer_dig_border = []  # 外壁挖孔边界
        inner_dig_border = []  # 内壁挖孔边界

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
                outer_dig_border.append((loc[0], loc[1], loc[2]))

                # 击中后，去找内壁边界
                origin = (loc[0] - normal[0] * 0.1, loc[1] - normal[1] * 0.1, loc[2] - normal[2] * 0.1)
                direction = (-normal[0], -normal[1], -normal[2])
                hit, loc, normal, index = active_obj.ray_cast(origin, direction)
                if hit:
                    inner_dig_border.append((loc[0], loc[1], loc[2]))

        darw_cylinder(outer_dig_border, inner_dig_border)

        bpy.ops.object.mode_set(mode='OBJECT')


def dig_hole():
    # 复制切割补面完成后的物体
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForDigHole"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    moveToRight(duplicate_obj)

    # todo 将来调整模板圆环位置后，要记录调整后的以下两个参数，若有记录，读取记录， 没有则读取套用的模板本身的参数
    template_highest_point = (-10.3681, 2.2440, 12.1771)
    template_hole_border_list = [
        [(5.96461296081543, -2.744267225265503, -0.07517538219690323),
         (6.695276260375977, -3.3451476097106934, 0.06827423721551895),
         (5.193972587585449, -2.281285285949707, -0.175833061337471),
         (4.375587463378906, -1.9626996517181396, -0.2210894227027893),
         (3.5247483253479004, -1.7453439235687256, -0.25106701254844666),
         (2.6553757190704346, -1.5920460224151611, -0.23524697124958038),
         (1.7374874353408813, -1.4963675737380981, -0.1559559553861618),
         (0.7106194496154785, -1.3782386779785156, 0.017644573003053665),
         (-0.3205421566963196, -1.2317662239074707, 0.24440406262874603),
         (-1.3119431734085083, -1.0292805433273315, 0.5063814520835876),
         (-1.4190728664398193, -1.8889247179031372, 1.035017967224121),
         (-1.5773382186889648, -2.8111331462860107, 1.4743074178695679),
         (-1.7737654447555542, -3.798762559890747, 1.768851637840271),
         (-1.9728513956069946, -4.828219890594482, 1.8874255418777466),
         (7.3692545890808105, -4.0578532218933105, 0.16739416122436523),
         (7.9814348220825195, -4.847168445587158, 0.1591436266899109),
         (8.5460844039917, -5.676958084106445, 0.03819790482521057),
         (9.08694839477539, -6.510298252105713, -0.1554052084684372),
         (8.382986068725586, -7.033217906951904, 0.2704339623451233),
         (7.62994909286499, -7.474363327026367, 0.7390419244766235),
         (6.797980308532715, -7.839724540710449, 1.240189790725708),
         (5.861752033233643, -8.161980628967285, 1.7305153608322144),
         (4.813824653625488, -8.449161529541016, 2.100529432296753),
         (3.6875340938568115, -8.694571495056152, 2.3481063842773438),
         (-2.234387159347534, -6.85148811340332, 1.818561315536499),
         (-2.2709853649139404, -7.836289882659912, 1.6764923334121704),
         (-2.1328012943267822, -5.854104518890381, 1.8926604986190796),
         (-2.2396419048309326, -8.84366226196289, 1.4936046600341797),
         (-1.0980910062789917, -8.924724578857422, 1.66081964969635),
         (0.048644013702869415, -8.97464656829834, 1.9054828882217407),
         (1.2453348636627197, -8.979107856750488, 2.2301149368286133),
         (2.480426788330078, -8.889814376831055, 2.4283695220947266)],

        [(10.240168571472168, 2.986708402633667, -1.8354297876358032),
         (9.910574913024902, 2.39359188079834, -1.9890505075454712),
         (11.038174629211426, 3.5313632488250732, -1.6788139343261719),
         (7.1755499839782715, 3.345161199569702, -2.2481749057769775),
         (6.464272499084473, 3.736074447631836, -2.230243444442749),
         (6.946434020996094, 4.612470626831055, -1.7905505895614624),
         (7.574184417724609, 5.537206172943115, -1.3134567737579346),
         (8.268343925476074, 6.4678263664245605, -0.926133930683136),
         (9.56075668334961, 8.401710510253906, -0.7333204746246338),
         (8.968050003051758, 7.425933837890625, -0.7171981334686279),
         (10.40972900390625, 7.674126625061035, -1.086659550666809),
         (7.8538689613342285, 2.9238970279693604, -2.2778031826019287),
         (8.513564109802246, 2.4804251194000244, -2.255873441696167),
         (9.189750671386719, 2.0603692531585693, -2.1888108253479004),
         (9.91439437866211, 1.7067705392837524, -2.0465681552886963),
         (12.740507125854492, 4.244335174560547, -1.7829004526138306),
         (11.889632225036621, 3.8975226879119873, -1.6395297050476074),
         (12.257303237915039, 5.078887462615967, -1.7274757623672485),
         (11.710976600646973, 5.9391279220581055, -1.60963773727417),
         (11.116840362548828, 6.828858375549316, -1.3770354986190796)]

    ]

    for template_hole_border in template_hole_border_list:
        get_hole_border(template_highest_point, template_hole_border)
        boolean_dig()

    for obj in bpy.data.objects:
        if obj.name == 'HoleBorderCurve':
            obj.name = 'HoleBorderCurve1'
            subdivide('HoleBorderCurve1', 3)
            convert_to_mesh('HoleBorderCurve1', 'meshHoleBorderCurve1', 0.18)

        if obj.name == 'HoleBorderCurve.001':
            obj.name = 'HoleBorderCurve2'
            subdivide('HoleBorderCurve2', 3)
            convert_to_mesh('HoleBorderCurve2', 'meshHoleBorderCurve2', 0.18)


'''
    以下函数已弃用
'''


def darw_cylinder_bottom(order_hole_border_vert):
    pass


def draw_hole_border_curve(order_border_co, name, depth):
    pass


def translate_circle_to_cylinder():
    pass


#
#
# # 使用布尔修改器
def boolean_cut():
    pass


#
#
# # 删除布尔后多余的部分
def delete_useless_part(cut_cylinder_buttom_co):
    pass
