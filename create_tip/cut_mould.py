import bpy
import bmesh
from bpy_extras import view3d_utils
from ..tool import moveToRight, moveToLeft, newMaterial, get_region_and_space, set_vert_group, delete_vert_group, \
                    utils_re_color, change_mat_mould
import mathutils
from mathutils import Vector
from math import sqrt

mouse_loc = None
old_radius = 7
on_obj = True
color_mode = 0


def get_color_mode():
    global color_mode
    return color_mode


def frontToCutMould(mode=0):
    global color_mode
    color_mode = mode
    name = bpy.context.scene.leftWindowObj
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (sprue_compare_obj != None):
        sprue_compare_obj.hide_set(True)
    if (hard_support_compare_obj != None):
        hard_support_compare_obj.hide_set(True)
    if (soft_support_compare_obj != None):
        soft_support_compare_obj.hide_set(True)

    # initial_cut_mould()
    if mode == 1:
        if name == '右耳':
            bpy.context.scene.transparent2EnumR = 'OP3'
            bpy.context.scene.transparent3EnumR = 'OP1'
        elif name == '左耳':
            bpy.context.scene.transparent2EnumL = 'OP3'
            bpy.context.scene.transparent3EnumL = 'OP1'
        change_mat_mould(1)
    bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")


def frontFromCutMould():
    name = bpy.context.scene.leftWindowObj
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (sprue_compare_obj != None):
        sprue_compare_obj.hide_set(False)
    if (hard_support_compare_obj != None):
        hard_support_compare_obj.hide_set(False)
    if (soft_support_compare_obj != None):
        soft_support_compare_obj.hide_set(False)

    submit_cut_mould()


def get_co():
    bpy.ops.view3d.cursor3d('INVOKE_DEFAULT', use_depth=False, orientation='VIEW')
    location = bpy.context.scene.cursor.location
    return location


def cal_co(mesh_name, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param mesh_name: 要检测物体的名字
    :return: 相交的坐标
    '''

    active_obj = bpy.data.objects[mesh_name]

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
                return 1   # 如果发生交叉，返回1

    return -1   # 如果未发生交叉，返回-1


def newColor(id, r, g, b, is_transparency, transparency_degree, is_use_backface_culling=True):
    mat = newMaterial(id)
    mat.use_backface_culling = is_use_backface_culling
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


def copyModel(obj_name):
    # 获取当前选中的物体
    obj_ori = bpy.data.objects[obj_name]
    # 复制物体用于对比突出加厚的预览效果
    obj_all = bpy.data.objects
    copy_compare = True  # 判断是否复制当前物体作为透明的参照,不存在参照物体时默认会复制一份新的参照物体
    for selected_obj in obj_all:
        if (selected_obj.name == obj_name + "huanqiecompare"):
            copy_compare = False  # 当存在参照物体时便不再复制新的物体
            # break
    if (copy_compare):  # 复制一份物体作为透明的参照
        active_obj = obj_ori
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.name = active_obj.name + "huanqiecompare"
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)

        if obj_name == '右耳':
            moveToRight(duplicate_obj)
        elif obj_name == '左耳':
            moveToLeft(duplicate_obj)


def getModelZ(obj_name):
    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects[obj_name]
    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)

    # 初始化最大距离为负无穷大
    z_max = float('-inf')
    z_min = float('inf')

    # 遍历的每个顶点并计算距离
    for vertex in bm.verts:
        z_max = max(z_max, vertex.co.z)
        z_min = min(z_min, vertex.co.z)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    return z_max, z_min


def initial_cut_mould():
    global old_radius
    global color_mode
    obj_name = bpy.context.scene.leftWindowObj
    obj_main = bpy.data.objects[obj_name]

    # 复制一份物体用于对比
    copyModel(obj_name)

    # 获取模型的高度
    zmax, zmin = getModelZ(obj_name)

    # 根据高度初始化圆环的位置
    initZ = round(zmax * 0.95, 2)

    if color_mode == 0:
        newColor('yellow2', 1.0, 0.319, 0.133, 1, 0.5)
        obj_compare = bpy.data.objects[obj_name + 'huanqiecompare']
        obj_compare.data.materials.clear()
        obj_compare.data.materials.append(bpy.data.materials['yellow2'])
    else:
        change_mat_mould(1)
        utils_re_color(obj_name, (0, 0.25, 1))
        newColor('yellow2', 0, 0.25, 1, 1, 0.5)
        obj_compare = bpy.data.objects[obj_name + 'huanqiecompare']
        obj_compare.data.materials.clear()
        obj_compare.data.materials.append(bpy.data.materials['yellow2'])

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj_main
    obj_main.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)
    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
    if selected_verts:
        # 计算平面的几何中心
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
    else:  # 初始高度没有顶点
        initZ = (zmax + zmin) / 2  # 改变初始高度
        selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
            initZ, 2) + 0.1 and round(v.co.z, 2) > round(initZ, 2) - 0.1]
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    initX = center.x
    initY = center.y

    # 若存在原始物体，先删除
    torus = bpy.data.objects.get(obj_name + 'Torus')
    circle = bpy.data.objects.get(obj_name + 'Circle')
    if (torus):
        bpy.data.objects.remove(torus, do_unlink=True)
    if (circle):
        bpy.data.objects.remove(circle, do_unlink=True)

    # 正常初始化
    # 大圆环
    bpy.ops.mesh.primitive_circle_add(
        vertices=32, radius=25, fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD', location=(
            initX, initY, initZ), rotation=(
            0.0, 0.0, 0.0), scale=(
            1.0, 1.0, 1.0))

    # 初始化环体
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(
        initX, initY, initZ), rotation=(0.0, 0, 0), major_segments=80, minor_segments=80, major_radius=old_radius,
                                     minor_radius=0.4)

    obj = bpy.context.active_object
    obj.name = obj_name + 'Torus'
    if obj_name == '右耳':
        moveToRight(obj)
    elif obj_name == '左耳':
        moveToLeft(obj)
    # 环体颜色
    newColor('red', 1, 0, 0, 0, 1)
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials['red'])
    # 选择圆环
    obj_circle = bpy.data.objects['Circle']
    obj_circle.name = obj_name + 'Circle'
    if obj_name == '右耳':
        moveToRight(obj_circle)
    elif obj_name == '左耳':
        moveToLeft(obj_circle)

    # 进入编辑模式
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj_circle
    obj_circle.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # 翻转圆环法线
    bpy.ops.mesh.flip_normals(only_clnors=False)
    # 隐藏圆环
    obj_circle.hide_set(True)
    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    apply_circle_cut(obj_name)

    bpy.ops.object.cutmould('INVOKE_DEFAULT')


def submit_cut_mould():
    del_objs = [bpy.context.scene.leftWindowObj + 'Circle', bpy.context.scene.leftWindowObj + 'Torus',
                bpy.context.scene.leftWindowObj + 'huanqiecompare', bpy.context.scene.leftWindowObj + 'cutmouldforshow']

    for obj in del_objs:
        if (bpy.data.objects[obj]):
            obj1 = bpy.data.objects[obj]
            bpy.data.objects.remove(obj1, do_unlink=True)
    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=False)
    delete_vert_group("CircleCutBorderVertex")
    utils_re_color("右耳", (1, 0.319, 0.133))


def is_mouse_on_object(context, event):
    global mouse_loc

    active_obj = bpy.data.objects[context.scene.leftWindowObj + 'Torus']
    is_on_object = False  # 初始化变量

    if context.area:
        context.area.tag_redraw()

    # 获取鼠标光标的区域坐标
    mv = Vector((event.mouse_region_x, event.mouse_region_y))

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

            loc, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                co = loc
                mouse_loc = loc
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


def getRadius(op):
    global on_obj
    # 翻转圆环法线
    obj_torus = bpy.data.objects[bpy.context.scene.leftWindowObj + 'Torus']
    obj_circle = bpy.data.objects[bpy.context.scene.leftWindowObj + 'Circle']
    active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj + 'huanqiecompare']
    for selected_obj in bpy.data.objects:
        if (selected_obj.name == bpy.context.scene.leftWindowObj + "huanqiecompareintersect"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = active_obj.name + "intersect"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj

    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate_obj.modifiers.new(name="Boolean Intersect", type='BOOLEAN')
    duplicate_obj.modifiers[0].operation = 'INTERSECT'
    duplicate_obj.modifiers[0].object = obj_circle
    duplicate_obj.modifiers[0].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier='Boolean Intersect', single_user=True)

    rbm = bmesh.new()
    rbm.from_mesh(duplicate_obj.data)
    # 获取截面上的点
    plane_normal = obj_circle.matrix_world.to_3x3(
    ) @ obj_circle.data.polygons[0].normal
    plane_point = obj_circle.location.copy()
    plane_verts = [v for v in rbm.verts if distance_to_plane(plane_normal, plane_point, v.co) == 0]

    # 圆环不在物体上
    if (len(plane_verts) == 0):
        on_obj = False
    else:
        on_obj = True

    if on_obj:
        center = sum((v.co for v in plane_verts), Vector()) / len(plane_verts)

        # 初始化最大距离为负无穷大
        max_distance = float('-inf')
        min_distance = float('inf')

        # 遍历的每个顶点并计算距离
        for vertex in plane_verts:
            distance = (vertex.co - obj_torus.location).length
            max_distance = max(max_distance, distance)
            min_distance = min(min_distance, distance)

        radius = round(max_distance, 2)
        radius = radius + 0.5

        # 删除复制的物体
        bpy.data.objects.remove(duplicate_obj, do_unlink=True)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_torus
        obj_torus.select_set(True)
        # 缩放圆环及调整位置
        if op == 'move':
            obj_torus.location = center
            obj_circle.location = center
        scale_ratio = round(radius / old_radius, 3)
        # print('缩放比例', scale_ratio)
        obj_torus.scale = (scale_ratio, scale_ratio, 1)


def distance_to_plane(plane_normal, plane_point, point):
    return round(abs(plane_normal.dot(point - plane_point)), 4)


def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
    bpy.ops.object.vertex_group_select()

    # 补面
    bpy.ops.mesh.fill()

    # 选择循环点
    bpy.ops.mesh.loop_to_region(select_bigger=True)

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
    name = bpy.context.scene.leftWindowObj
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = bpy.data.objects[name].vertex_groups.get("CircleCutBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')


def judge_if_need_invert():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def apply_circle_cut(obj_name):
    global on_obj
    global color_mode

    obj_ori = bpy.data.objects[obj_name + 'huanqiecompare']
    obj_main = bpy.data.objects[obj_name]
    obj_circle = bpy.data.objects[obj_name + 'Circle']
    obj_torus = bpy.data.objects[obj_name + 'Torus']
    if obj_name == '右耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiR
    elif obj_name == '左耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiL
    # 从透明对比物体 获取原始网格数据
    orime = obj_ori.data
    oribm = bmesh.new()
    oribm.from_mesh(orime)
    # 应用原始网格数据
    oribm.to_mesh(obj_main.data)
    oribm.free()

    # 圆环在物体上，则进行平滑
    if on_obj:
        # 存一下原先的顶点
        obj_main.select_set(True)
        bpy.context.view_layer.objects.active = obj_main
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bm = bmesh.from_edit_mesh(obj_main.data)
        ori_border_index = [v.index for v in bm.verts if v.select]
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        set_vert_group("all", ori_border_index)
        cut_success = True

        # 首先用圆环进行切割
        try:
            # print('开始切割',datetime.datetime.now())
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_main
            obj_main.select_set(True)
            cut_obj = obj_circle
            # 该布尔插件会直接删掉切割平面，最好是使用复制去切，以防后续会用到
            duplicate_obj = cut_obj.copy()
            duplicate_obj.data = cut_obj.data.copy()
            duplicate_obj.animation_data_clear()
            bpy.context.collection.objects.link(duplicate_obj)
            duplicate_obj.select_set(True)
            if bpy.context.scene.leftWindowObj == '右耳':
                moveToRight(duplicate_obj)
            else:
                moveToLeft(duplicate_obj)
            # 使用布尔插件
            bpy.ops.object.booltool_auto_difference()

            # 获取下边界顶点
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='all')
            # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')

            bm = bmesh.from_edit_mesh(obj_main.data)
            outer_border_index = [v.index for v in bm.verts if v.select]

            bpy.ops.object.mode_set(mode='OBJECT')

            # 将下边界加入顶点组
            bottom_outer_border_vertex = obj_main.vertex_groups.get("CircleCutBorderVertex")
            if (bottom_outer_border_vertex == None):
                bottom_outer_border_vertex = obj_main.vertex_groups.new(name="CircleCutBorderVertex")
            for vert_index in outer_border_index:
                bottom_outer_border_vertex.add([vert_index], 1, 'ADD')
            delete_vert_group("all")

            delete_useless_part()

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
            bpy.ops.object.vertex_group_select()
            # 将周围的面变成三角面
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='CircleCutBorderVertex')
            bpy.ops.object.vertex_group_select()

            # 补面
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            bpy.ops.mesh.fill()
            bpy.ops.mesh.select_all(action='DESELECT')
            # 栅格填充方式
            # bpy.ops.mesh.subdivide(number_cuts=1)
            # bpy.ops.mesh.fill_grid(span=10)
            # bpy.ops.object.vertex_group_remove_from()
            # bpy.ops.mesh.select_mode(type='EDGE')
            # bpy.ops.mesh.region_to_loop()
            # bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
            if color_mode == 1:
                utils_re_color(obj_name, (0, 0.25, 1))
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj_circle
            obj_circle.select_set(True)
        except:
            cut_success = False
            print('切割失败')
            bpy.ops.object.mode_set(mode='OBJECT')


# 获取当前3D视图的方向
def get_view_direction():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region_3d = area.spaces.active.region_3d
            view_matrix = region_3d.view_matrix
            view_direction = view_matrix.to_3x3().inverted() @ mathutils.Vector((0.0, 0.0, -1.0))
            return view_direction
    return None


# 挤出曲线并生成面
def extrude_curve_and_generate_faces(curve_obj, distance):
    # 获取曲线数据
    curve_data = curve_obj.data

    # 创建新的挤出曲线
    new_curve_data = curve_data.copy()
    new_curve_data2 = curve_data.copy()
    new_curve_obj = bpy.data.objects.new(curve_obj.name + "_extruded", new_curve_data)
    new_curve_obj2 = bpy.data.objects.new(curve_obj.name + "_extruded2", new_curve_data2)
    bpy.context.collection.objects.link(new_curve_obj)
    bpy.context.collection.objects.link(new_curve_obj2)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(new_curve_obj)
        moveToRight(new_curve_obj2)
    else:
        moveToLeft(new_curve_obj)
        moveToLeft(new_curve_obj2)

    # 设置挤出方向
    view_direction = get_view_direction()
    if view_direction is None:
        print("无法获取视图方向")
        return

    # 挤出曲线
    distance = view_direction * distance
    for point1, point2 in zip(new_curve_data.splines[0].points, new_curve_data2.splines[0].points):
        point1.co = [point1.co[0] + distance[0], point1.co[1] + distance[1], point1.co[2] + distance[2], point1.co[3]]
        point2.co = [point2.co[0] - distance[0], point2.co[1] - distance[1], point2.co[2] - distance[2], point2.co[3]]

    # 创建新的网格对象
    mesh_data = bpy.data.meshes.new(curve_obj.name + "_mesh")
    mesh_obj = bpy.data.objects.new(curve_obj.name + "_mesh_obj", mesh_data)
    bpy.context.collection.objects.link(mesh_obj)

    # 使用 BMesh 生成面
    bm = bmesh.new()

    # 获取挤出曲线的顶点
    extruded_splines1 = new_curve_data.splines
    extruded_splines2 = new_curve_data2.splines

    for extruded_spline1, extruded_spline2 in zip(extruded_splines1, extruded_splines2):
        extruded_points1 = extruded_spline1.points
        extruded_points2 = extruded_spline2.points

        # 创建顶点
        extruded_verts1 = [bm.verts.new(point.co[0:3]) for point in extruded_points1]
        extruded_verts2 = [bm.verts.new(point.co[0:3]) for point in extruded_points2]

        # 创建边
        for v1, v2 in zip(extruded_verts1, extruded_verts2):
            bm.edges.new([v1, v2])

        bm.verts.ensure_lookup_table()
        # 创建面
        num_points = len(extruded_points1)
        for i in range(num_points):
            v1 = extruded_verts1[i]
            v2 = extruded_verts2[i]
            v3 = extruded_verts2[(i + 1) % num_points]
            v4 = extruded_verts1[(i + 1) % num_points]
            bm.faces.new([v1, v2, v3, v4])

    # 更新网格对象
    bm.to_mesh(mesh_data)
    bm.free()

    # 设置网格对象的位置与原曲线相同
    mesh_obj.location = curve_obj.location
    mesh_obj.data.materials.clear()
    newColor('blue2', 0, 0, 1, 0, 1, False)
    mesh_obj.data.materials.append(bpy.data.materials['blue2'])

    # 隐藏物体
    curve_obj.hide_set(True)
    new_curve_obj.hide_set(True)
    new_curve_obj2.hide_set(True)


def start_curve(mode):
    """ 在点加蓝线只剩一个点时将曲线延长方便查看 """
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects.get(name + 'cutmouldpoint')
    # 先在点加位置添加一个新点
    spline = curve_obj.data.splines[0]
    spline.points.add(1)
    first_co = spline.points[0].co
    direction = get_view_direction()
    spline.points[-1].co = (first_co[0] - direction[0] * 3, first_co[1] - direction[1] * 3, first_co[2] - direction[2] * 3, 1)
    if mode == 0:
        newColor('green', 0, 1, 0, 0, 1)
        curve_obj.data.materials.clear()
        curve_obj.data.materials.append(bpy.data.materials['green'])
    if mode == 1:
        newColor('red', 1, 0, 0, 0, 1)
        curve_obj.data.materials.clear()
        curve_obj.data.materials.append(bpy.data.materials['red'])


class Cut_Mould(bpy.types.Operator):
    bl_idname = "object.cutmould"
    bl_label = "模具切割"

    __initial_rotation_x = None  # 初始x轴旋转角度
    __initial_rotation_y = None
    __initial_rotation_z = None
    __left_mouse_down = False  # 按下右键未松开时，旋转圆环角度
    __right_mouse_down = False  # 按下右键未松开时，圆环上下移动
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __is_moving = False
    __dx = 0
    __dy = 0

    def invoke(self, context, event):

        op_cls = Cut_Mould
        bpy.context.scene.var = 120

        print('invokeCutMould')

        op_cls.__initial_rotation_x = None
        op_cls.__initial_rotation_y = None
        op_cls.__initial_rotation_z = None
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None

        context.window_manager.modal_handler_add(self)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        op_cls = Cut_Mould

        if context.area:
            context.area.tag_redraw()
        # 未切割时起效
        if (bpy.context.scene.var == 120):

            obj_torus = bpy.data.objects[context.scene.leftWindowObj + 'Torus']
            active_obj = bpy.data.objects[context.scene.leftWindowObj + 'Circle']

            # 鼠标是否在圆环上
            if is_mouse_on_object(context, event):
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj_torus
                obj_torus.select_set(True)
                if event.type == 'LEFTMOUSE':
                    if event.value == 'PRESS':
                        op_cls.__is_moving = True
                        op_cls.__left_mouse_down = True
                        op_cls.__initial_rotation_x = obj_torus.rotation_euler[0]
                        op_cls.__initial_rotation_y = obj_torus.rotation_euler[1]
                        op_cls.__initial_rotation_z = obj_torus.rotation_euler[2]
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y

                        # print('鼠标坐标',mouse_loc)
                        op_cls.__dx = round(mouse_loc.x, 2)
                        op_cls.__dy = round(mouse_loc.y, 2)
                        # print('dx',op_cls.__dx)
                        # print('dy',op_cls.__dy)

                    # 取消
                    elif event.value == 'RELEASE':
                        normal = active_obj.matrix_world.to_3x3(
                        ) @ active_obj.data.polygons[0].normal
                        if normal.z > 0:
                            active_obj.hide_set(False)
                            bpy.context.view_layer.objects.active = active_obj
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='SELECT')
                            # 翻转圆环法线
                            bpy.ops.mesh.flip_normals()
                            # 隐藏圆环
                            active_obj.hide_set(True)
                            # 返回对象模式
                            bpy.ops.object.mode_set(mode='OBJECT')
                            print('反转后法线', active_obj.matrix_world.to_3x3(
                            ) @ active_obj.data.polygons[0].normal)

                        apply_circle_cut(context.scene.leftWindowObj)
                        op_cls.__is_moving = False
                        op_cls.__left_mouse_down = False
                        op_cls.__initial_rotation_x = None
                        op_cls.__initial_rotation_y = None
                        op_cls.__initial_rotation_z = None
                        op_cls.__initial_mouse_x = None
                        op_cls.__initial_mouse_y = None

                    return {'RUNNING_MODAL'}

                elif event.type == 'RIGHTMOUSE':
                    if event.value == 'PRESS':
                        op_cls.__is_moving = True
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                    elif event.value == 'RELEASE':
                        apply_circle_cut(context.scene.leftWindowObj)
                        op_cls.__is_moving = False
                        op_cls.__right_mouse_down = False
                        op_cls.__initial_mouse_x = None
                        op_cls.__initial_mouse_y = None

                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # 旋转角度正负号
                        if (op_cls.__dy < 0):
                            symx = -1
                        else:
                            symx = 1

                        if (op_cls.__dx > 0):
                            symy = -1
                        else:
                            symy = 1

                        # print('symx',symx)
                        # print('symy',symy)

                        # x,y轴旋转比例
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                   4)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                   4)
                        # print('px',px)
                        # print('py',py)

                        # 旋转角度
                        rotate_angle_x = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                        rotate_angle_y = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                        rotate_angle_z = round((event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)
                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                       rotate_angle_x * symx
                        active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                       rotate_angle_y * symy
                        active_obj.rotation_euler[2] = op_cls.__initial_rotation_z + \
                                                       rotate_angle_z

                        obj_torus.rotation_euler[0] = active_obj.rotation_euler[0]
                        obj_torus.rotation_euler[1] = active_obj.rotation_euler[1]
                        obj_torus.rotation_euler[2] = active_obj.rotation_euler[2]

                        getRadius('rotate')
                        return {'RUNNING_MODAL'}
                    elif op_cls.__right_mouse_down:
                        obj_circle = bpy.data.objects[context.scene.leftWindowObj + 'Circle']
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal

                        dis = event.mouse_region_y - op_cls.__initial_mouse_y
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        # print('距离',dis)
                        obj_circle.location -= normal * dis * 0.05
                        obj_torus.location -= normal * dis * 0.05
                        getRadius('move')
                        return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}
                # return {'RUNNING_MODAL'}

            else:
                tar_obj = bpy.data.objects[context.scene.leftWindowObj]
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = tar_obj
                tar_obj.select_set(True)
                obj_torus = bpy.data.objects[context.scene.leftWindowObj + 'Torus']
                active_obj = bpy.data.objects[context.scene.leftWindowObj + 'Circle']
                if event.value == 'RELEASE' and op_cls.__is_moving:
                    normal = active_obj.matrix_world.to_3x3(
                    ) @ active_obj.data.polygons[0].normal
                    if normal.z > 0:
                        active_obj.hide_set(False)
                        bpy.context.view_layer.objects.active = active_obj
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        # 翻转圆环法线
                        bpy.ops.mesh.flip_normals()
                        # 隐藏圆环
                        active_obj.hide_set(True)
                        # 返回对象模式
                        bpy.ops.object.mode_set(mode='OBJECT')
                        print('反转后法线', active_obj.matrix_world.to_3x3(
                        ) @ active_obj.data.polygons[0].normal)

                    apply_circle_cut(context.scene.leftWindowObj)
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__right_mouse_down = False
                    op_cls.__initial_rotation_x = None
                    op_cls.__initial_rotation_y = None
                    op_cls.__initial_rotation_z = None
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None

                if event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # 旋转正负号
                        if (op_cls.__dy < 0):
                            symx = -1
                        else:
                            symx = 1

                        if (op_cls.__dx > 0):
                            symy = -1
                        else:
                            symy = 1

                        # print('symx',symx)
                        # print('symy',symy)

                        #  x,y轴旋转比例
                        px = round(abs(op_cls.__dy) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                   4)
                        py = round(abs(op_cls.__dx) / sqrt(op_cls.__dx * op_cls.__dx + op_cls.__dy * op_cls.__dy),
                                   4)
                        # print('px',px)
                        # print('py',py)

                        # 旋转角度
                        rotate_angle_x = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * px, 4)
                        rotate_angle_y = round((event.mouse_region_y - op_cls.__initial_mouse_y) * 0.01 * py, 4)
                        rotate_angle_z = round((event.mouse_region_x - op_cls.__initial_mouse_x) * 0.005, 4)
                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                                       rotate_angle_x * symx
                        active_obj.rotation_euler[1] = op_cls.__initial_rotation_y + \
                                                       rotate_angle_y * symy
                        active_obj.rotation_euler[2] = op_cls.__initial_rotation_z + \
                                                       rotate_angle_z
                        obj_torus.rotation_euler[0] = active_obj.rotation_euler[0]
                        obj_torus.rotation_euler[1] = active_obj.rotation_euler[1]
                        obj_torus.rotation_euler[2] = active_obj.rotation_euler[2]

                        getRadius('rotate')
                        return {'RUNNING_MODAL'}

                    elif op_cls.__right_mouse_down:
                        obj_circle = bpy.data.objects[context.scene.leftWindowObj + 'Circle']
                        # 平面法线方向
                        normal = obj_circle.matrix_world.to_3x3(
                        ) @ obj_circle.data.polygons[0].normal
                        dis = event.mouse_region_y - op_cls.__initial_mouse_y
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        # print('距离',dis)
                        obj_circle.location -= normal * dis * 0.05
                        obj_torus.location -= normal * dis * 0.05
                        getRadius('move')
                        return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}


        else:
            print("退出模具切割")
            return {'FINISHED'}


class Reset_CutMould(bpy.types.Operator):
    bl_idname = "cutmould.resetcut"
    bl_label = "重置切割"

    def invoke(self, context, event):
        self.excute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context):
        del_objs = [context.scene.leftWindowObj + 'cutmouldpoint',
                    context.scene.leftWindowObj + 'cutmouldpoint_extruded',
                    context.scene.leftWindowObj + 'cutmouldpoint_extruded2',
                    context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj']
        for obj in del_objs:
            if (bpy.data.objects.get(obj)):
                bpy.data.objects.remove(bpy.data.objects.get(obj), do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects[context.scene.leftWindowObj]
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # 重新初始化
        # initial_cut_mould()
        bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")


class Finish_CutMould(bpy.types.Operator):
    bl_idname = "cutmould.finishcut"
    bl_label = "完成切割"

    def invoke(self, context, event):
        self.excute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context):
        # 应用切割
        obj = bpy.data.objects[context.scene.leftWindowObj]
        cut_obj = bpy.data.objects[context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj']

        # 重新计算圆环法线用于切割
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cut_obj
        cut_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')

        # 切割
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        cut_obj.select_set(True)
        # 使用布尔插件
        bpy.ops.object.booltool_auto_difference()
        # 删除用不到的物体
        del_objs = [context.scene.leftWindowObj + 'cutmouldpoint',
                    context.scene.leftWindowObj + 'cutmouldpoint_extruded',
                    context.scene.leftWindowObj + 'cutmouldpoint_extruded2']
        for obj in del_objs:
            if (bpy.data.objects.get(obj)):
                bpy.data.objects.remove(bpy.data.objects.get(obj), do_unlink=True)
        if color_mode == 1:
            utils_re_color(context.scene.leftWindowObj, (0, 0.25, 1))
        else:
            utils_re_color(context.scene.leftWindowObj, (1, 0.319, 133))
        bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")


class TEST_OT_cutmouldstart(bpy.types.Operator):
    bl_idname = "cutmould.start"
    bl_label = "cutmouldstart"
    bl_description = "开始切割模具"

    def invoke(self, context, event):  # 初始化
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        name = bpy.context.scene.leftWindowObj
        co = get_co()
        new_curve_data = bpy.data.curves.new(
            name=name + 'cutmouldpoint', type='CURVE')
        new_curve_obj = bpy.data.objects.new(
            name=name + 'cutmouldpoint', object_data=new_curve_data)
        new_curve_data.bevel_depth = 0.18
        new_curve_data.dimensions = '3D'
        bpy.context.collection.objects.link(new_curve_obj)
        if name == '右耳':
            moveToRight(new_curve_obj)
        elif name == '左耳':
            moveToLeft(new_curve_obj)
        newColor('blue', 0, 0, 1, 1, 1)
        new_curve_data.materials.append(bpy.data.materials['blue'])
        new_curve_data.splines.clear()
        new_spline = new_curve_data.splines.new(type='NURBS')
        new_spline.use_smooth = True
        new_spline.order_u = 2
        new_curve_data.splines[0].points[0].co[0:3] = co
        new_curve_data.splines[0].points[0].co[3] = 1
        start_curve(0)
        bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch2")


class TEST_OT_cutmouldfinish(bpy.types.Operator):
    bl_idname = "cutmould.finish"
    bl_label = "cutmouldfinish"
    bl_description = "结束切割模具"

    def invoke(self, context, event):  # 初始化
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        add_curve_name = context.scene.leftWindowObj + 'cutmouldpoint'
        curve_obj = bpy.data.objects[add_curve_name]
        curve_obj.data.splines[0].use_cyclic_u = True
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT')
        curve_obj.data.splines[0].points[-1].select = True
        bpy.ops.curve.delete(type='VERT')
        bpy.ops.curve.select_all(action='SELECT')
        # 细分
        bpy.ops.curve.subdivide(number_cuts=10)
        # 平滑
        for _ in range(10):
            bpy.ops.curve.smooth()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 生成切割用的物体
        extrude_curve_and_generate_faces(curve_obj, 20)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
        bpy.data.objects[context.scene.leftWindowObj].select_set(True)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


class TEST_OT_cutmouldaddpoint(bpy.types.Operator):
    bl_idname = "cutmould.addpoint"
    bl_label = "cutmouldaddpoint"
    bl_description = "单击左键添加控制点"

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        name = context.scene.leftWindowObj
        add_curve_name = name + 'cutmouldpoint'
        co = get_co()
        if bpy.data.objects.get(add_curve_name) != None and cal_co(add_curve_name, context, event) == -1:
            curve_obj = bpy.data.objects.get(add_curve_name)
            if curve_obj.data.materials[0].name == 'green' or curve_obj.data.materials[0].name == 'red':
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = curve_obj
                curve_obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                curve_obj.data.splines[0].points[-1].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                curve_obj.data.materials.clear()
                curve_obj.data.materials.append(bpy.data.materials['blue'])

            spline = curve_obj.data.splines[0]
            spline.points.add(1)
            spline.points[-1].co = (co[0], co[1], co[2], 1)


class TEST_OT_cutmoulddeletepoint(bpy.types.Operator):
    bl_idname = "cutmould.deletepoint"
    bl_label = "deletepoint"
    bl_description = "单击右键删除控制点"

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        name = context.scene.leftWindowObj
        add_curve_name = name + 'cutmouldpoint'
        if bpy.data.objects.get(add_curve_name) != None:
            # 删除最后一个控制点
            curve_len = len(bpy.data.objects[add_curve_name].data.splines[0].points)
            if curve_len > 1:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[add_curve_name]
                bpy.data.objects[add_curve_name].select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                bpy.data.objects[add_curve_name].data.splines[0].points[-1].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                if len(bpy.data.objects[add_curve_name].data.splines[0].points) == 1:
                    start_curve(1)

            elif curve_len == 1:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[add_curve_name]
                bpy.data.objects[add_curve_name].select_set(True)
                bpy.data.objects.remove(bpy.data.objects[add_curve_name], do_unlink=True)
                bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")


class Tool_ResetCutMould(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldreset"
    bl_label = "重置模具切割"
    bl_description = (
        "点击重置模具切割"
    )
    bl_icon = "brush.paint_texture.multiply"
    bl_widget = None
    bl_keymap = (
        ("cutmould.reset", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class Tool_FinishCutMould(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldfinish"
    bl_label = "完成模具切割"
    bl_description = (
        "点击完成模具切割"
    )
    bl_icon = "brush.paint_texture.smear"
    bl_widget = None
    bl_keymap = (
        ("cutmould.finishcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class Switch_CutMould1(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldswitch1"
    bl_label = "开始切割模具"
    bl_description = (
        "点击开始切割模具"
    )
    bl_icon = "brush.paint_texture.soften"
    bl_widget = None
    bl_keymap = (
        ("cutmould.start", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class Switch_CutMould2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldswitch2"
    bl_label = "切割模具"
    bl_description = (
        "进行切割模具"
    )
    bl_icon = "brush.paint_vertex.alpha"
    bl_widget = None
    bl_keymap = (
        ("cutmould.finish", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("cutmould.addpoint", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("cutmould.deletepoint", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None)
    )

    def draw_settings(context, layout, tool):
        pass


def register():
    bpy.utils.register_class(Cut_Mould)
    bpy.utils.register_class(Reset_CutMould)
    bpy.utils.register_class(Finish_CutMould)
    bpy.utils.register_class(TEST_OT_cutmouldstart)
    bpy.utils.register_class(TEST_OT_cutmouldaddpoint)
    bpy.utils.register_class(TEST_OT_cutmoulddeletepoint)
    bpy.utils.register_class(TEST_OT_cutmouldfinish)

    bpy.utils.register_tool(Tool_ResetCutMould)
    bpy.utils.register_tool(Tool_FinishCutMould, separator=True, group=False, after={Tool_ResetCutMould.bl_idname})

    bpy.utils.register_tool(Switch_CutMould1)
    bpy.utils.register_tool(Switch_CutMould2)


def unregister():
    bpy.utils.unregister_class(Cut_Mould)
    bpy.utils.unregister_class(Reset_CutMould)
    bpy.utils.unregister_class(Finish_CutMould)
    bpy.utils.unregister_class(TEST_OT_cutmouldstart)
    bpy.utils.unregister_class(TEST_OT_cutmouldaddpoint)
    bpy.utils.unregister_class(TEST_OT_cutmoulddeletepoint)
    bpy.utils.unregister_class(TEST_OT_cutmouldfinish)

    bpy.utils.unregister_tool(Tool_ResetCutMould)
    bpy.utils.unregister_tool(Tool_FinishCutMould)
    bpy.utils.unregister_tool(Switch_CutMould1)
    bpy.utils.unregister_tool(Switch_CutMould2)