import bpy
import bmesh
from bpy_extras import view3d_utils
from ..tool import moveToRight, moveToLeft, newMaterial, get_region_and_space, set_vert_group, delete_vert_group, \
                    utils_re_color, change_mat_mould, laplacian_smooth
from ..register_tool import unregister_tools
import mathutils
from mathutils import Vector
from math import sqrt
from ..global_manager import global_manager
from ..back_and_forward import record_state, backup_state, forward_state

color_mode = 0


def register_cut_mould_globals():
    global color_mode
    global_manager.register('color_mode', color_mode)


def cut_mould_backup():
    backup_state()


def cut_mould_forward():
    forward_state()


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

    if mode == 1:
        if name == '右耳':
            bpy.context.scene.transparent2EnumR = 'OP3'
            bpy.context.scene.transparent3EnumR = 'OP1'
        elif name == '左耳':
            bpy.context.scene.transparent2EnumL = 'OP3'
            bpy.context.scene.transparent3EnumL = 'OP1'
        change_mat_mould(1)
    else:
        if name == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP3'
        elif name == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP3'
    bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")


def frontFromCutMould(mode=0):
    global color_mode
    color_mode = mode
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

    if name == '右耳':
        collections = bpy.data.collections['Right']
        if color_mode == 0:
            bpy.context.scene.transparent2R = False
            bpy.context.scene.transparent3R = True
    elif name == '左耳':
        collections = bpy.data.collections['Left']
        if color_mode == 0:
            bpy.context.scene.transparent2L = False
            bpy.context.scene.transparent3L = True
    for obj in collections.objects:
        if obj.type == 'MESH':
            # 获取网格数据
            me = obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            if len(bm.verts.layers.float_color) > 0:
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 1
                    colvert.y = 0.319
                    colvert.z = 0.133

            bm.to_mesh(me)
            bm.free()

    submit_cut_mould(mode)

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


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


def apply_cut_mould(mode):
    main_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    cut_obj = bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cut_obj
    cut_obj.select_set(True)
    bpy.ops.object.modifier_remove(modifier='Solidify', report=False)
    # 切割
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    cut_obj.select_set(True)
    # 使用布尔插件
    bpy.ops.object.booltool_auto_difference()
    bpy.ops.object.mode_set(mode='EDIT')
    main_obj.vertex_groups.new(name="CutVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bm = bmesh.from_edit_mesh(main_obj.data)
    selected_verts = [v for v in bm.verts if v.select]
    if len(selected_verts) == 0:
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        bpy.ops.mesh.fill()
        bpy.ops.object.mode_set(mode='OBJECT')
        apply_smooth(main_obj)
    delete_objects_and_recolor(mode)


def apply_smooth(main_obj):
    duplicate_obj = main_obj.copy()
    duplicate_obj.data = main_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = main_obj.name + "ForCut"
    bpy.context.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CutVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.region_to_loop()
    if bpy.context.scene.leftWindowObj == '右耳':
        pianyi = bpy.context.scene.cutmouldpianyiR
    else:
        pianyi = bpy.context.scene.cutmouldpianyiL
    if pianyi > 0:
        try:
            bm = bmesh.from_edit_mesh(duplicate_obj.data)
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)
            max_distance = float('-inf')
            # 遍历的每个顶点并计算距离
            for vertex in verts:
                distance = (vertex.co - center).length
                max_distance = max(max_distance, distance)
            bpy.ops.circle.smooth(width=pianyi, center_border_group_name='CutVertex',
                                  max_smooth_width=4, circle_radius=round(max_distance, 2) + 0.5, delete_vertex_group=False)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='CutVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            # bpy.ops.mesh.region_to_loop()
            # bpy.ops.mesh.remove_doubles(threshold=0.2)
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='CutVertex')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.mesh.select_more()
            bm = bmesh.from_edit_mesh(duplicate_obj.data)
            verts = [v for v in bm.verts if v.select]
            float_vector_layer_vertex_origin = bm.verts.layers.float_vector['OriginVertex']
            float_vector_layer_normal_origin = bm.verts.layers.float_vector['OriginNormal']
            for v in verts:
                v[float_vector_layer_vertex_origin] = v.co
                v[float_vector_layer_normal_origin] = v.normal
            bmesh.update_edit_mesh(duplicate_obj.data)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            delete_vert_group("CutVertex")
            bpy.data.objects.remove(main_obj, do_unlink=True)
            duplicate_obj.name = bpy.context.scene.leftWindowObj
        except:
            if duplicate_obj:
                bpy.data.objects.remove(duplicate_obj, do_unlink=True)
            if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'ForCutcopyBridgeBorder'):
                bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'ForCutcopyBridgeBorder'],
                                        do_unlink=True)
            bpy.context.view_layer.objects.active = main_obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            main_obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='CutVertex')
            bpy.ops.object.vertex_group_select()
            bm = bmesh.from_edit_mesh(main_obj.data)
            verts = [v for v in bm.verts if v.select]
            float_vector_layer_vertex_origin = bm.verts.layers.float_vector['OriginVertex']
            float_vector_layer_normal_origin = bm.verts.layers.float_vector['OriginNormal']
            for v in verts:
                v[float_vector_layer_vertex_origin] = v.co
                v[float_vector_layer_normal_origin] = v.normal
            bmesh.update_edit_mesh(main_obj.data)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            delete_vert_group("CutVertex")

    else:
        bm = bmesh.from_edit_mesh(main_obj.data)
        verts = [v for v in bm.verts if v.select]
        float_vector_layer_vertex_origin = bm.verts.layers.float_vector['OriginVertex']
        float_vector_layer_normal_origin = bm.verts.layers.float_vector['OriginNormal']
        for v in verts:
            v[float_vector_layer_vertex_origin] = v.co
            v[float_vector_layer_normal_origin] = v.normal
        bmesh.update_edit_mesh(main_obj.data)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        delete_vert_group("CutVertex")

    # bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
    # bpy.ops.mesh.separate(type='SELECTED')
    # for obj in bpy.data.objects:
    #     if obj.select_get() and obj != main_obj:
    #         inner_obj = obj
    #         break
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # inner_obj.select_set(True)
    # bpy.context.view_layer.objects.active = inner_obj
    # inner_obj.name = main_obj.name + "切割边界"
    # if main_obj.name == '右耳':
    #     moveToRight(inner_obj)
    # elif main_obj.name == '左耳':
    #     moveToLeft(inner_obj)
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.fill(use_beauty=False)
    # bm = bmesh.from_edit_mesh(inner_obj.data)
    # edges = [e for e in bm.edges if e.select]
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.mesh.select_mode(type='EDGE')
    # for e in edges:
    #     if not e.is_boundary:
    #         e.select_set(True)
    # bpy.ops.mesh.subdivide(number_cuts=10, ngon=False, quadcorner='INNERVERT')
    #
    # bpy.ops.mesh.select_mode(type='VERT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # verts = [v for v in bm.verts if v.select]
    # bpy.ops.mesh.select_all(action='DESELECT')
    # for v in verts:
    #     if not v.is_boundary:
    #         v.select_set(True)
    # bm = bmesh.from_edit_mesh(inner_obj.data)
    # verts_index = [v.index for v in bm.verts if v.select]
    # laplacian_smooth(verts_index, 0.5, 10)
    #
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.view_layer.objects.active = main_obj
    # main_obj.select_set(True)
    # inner_obj.select_set(True)
    # bpy.ops.object.join()
    #
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.remove_doubles()
    # bpy.ops.mesh.normals_make_consistent(inside=False)
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    # delete_vert_group("CutVertex")


def delete_objects_and_recolor(mode):
    # 删除用不到的物体
    del_objs = [bpy.context.scene.leftWindowObj + 'cutmouldpoint',
                bpy.context.scene.leftWindowObj + 'cutmouldpoint_extruded',
                bpy.context.scene.leftWindowObj + 'cutmouldpoint_extruded2',
                bpy.context.scene.leftWindowObj + 'cut_mould_sphere']
    for obj in del_objs:
        if (bpy.data.objects.get(obj)):
            bpy.data.objects.remove(bpy.data.objects.get(obj), do_unlink=True)
    if mode == 1:
        utils_re_color(bpy.context.scene.leftWindowObj, (0, 0.25, 1))
    else:
        utils_re_color(bpy.context.scene.leftWindowObj, (1, 0.319, 0.133))


def submit_cut_mould(mode):
    cut_obj = bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj')
    if cut_obj:     # 如果没有应用切割将其提交
        apply_cut_mould(mode)

    else:
        point_obj = bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'cutmouldpoint')
        if point_obj:
            bpy.data.objects.remove(point_obj, do_unlink=True)
        sphere_obj = bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'cut_mould_sphere')
        if sphere_obj:
            bpy.data.objects.remove(sphere_obj, do_unlink=True)

    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


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
    area = next(a for a in bpy.context.window.screen.areas if a.type == 'VIEW_3D')
    r3d = area.spaces[0].region_3d
    cam_loc = r3d.view_matrix.inverted().translation

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
    # view_direction = get_view_direction()
    # if view_direction is None:
    #     print("无法获取视图方向")
    #     return

    # 挤出曲线
    # distance = view_direction * distance
    for point1, point2 in zip(new_curve_data.splines[0].points, new_curve_data2.splines[0].points):
        vertex_co = Vector(point1.co[0:3])
        move_co1 = vertex_co + (vertex_co - cam_loc).normalized() * distance
        move_co2 = vertex_co + (cam_loc - vertex_co).normalized() * distance
        point1.co = [move_co1[0], move_co1[1], move_co1[2], 1]
        point2.co = [move_co2[0], move_co2[1], move_co2[2], 1]

    # 创建新的网格对象
    mesh_data = bpy.data.meshes.new(curve_obj.name + "_mesh")
    mesh_obj = bpy.data.objects.new(curve_obj.name + "_mesh_obj", mesh_data)
    bpy.context.collection.objects.link(mesh_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(mesh_obj)
    else:
        moveToLeft(mesh_obj)

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

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 隐藏物体
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness = -0.5
    # curve_obj.hide_set(True)
    # new_curve_obj.hide_set(True)
    # new_curve_obj2.hide_set(True)
    bpy.data.objects.remove(curve_obj, do_unlink=True)
    bpy.data.objects.remove(new_curve_obj, do_unlink=True)
    bpy.data.objects.remove(new_curve_obj2, do_unlink=True)


def start_curve():
    """ 在点加蓝线初始只有一个点时在点击的位置生成圆球 """
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects.get(name + 'cutmouldpoint')
    # 先在点加位置添加一个新点
    first_co = curve_obj.data.splines[0].points[0].co[0:3]

    name = bpy.context.scene.leftWindowObj
    mesh = bpy.data.meshes.new(name + "cut_mould_sphere")
    obj = bpy.data.objects.new(name + "cut_mould_sphere", mesh)
    bpy.context.collection.objects.link(obj)
    if name == '右耳':
        moveToRight(obj)
    elif name == '左耳':
        moveToLeft(obj)
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # 设置圆球的参数
    radius = 0.3  # 半径
    segments = 16  # 分段数
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius*2)
    bm.to_mesh(me)
    bm.free()
    obj.location = first_co
    newColor('red', 1, 0, 0, 1, 1)
    obj.data.materials.append(bpy.data.materials['red'])


class Reset_CutMould(bpy.types.Operator):
    bl_idname = "cutmould.resetcut"
    bl_label = "重置切割"

    def invoke(self, context, event):
        bpy.context.scene.var = 90
        self.execute(context)
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        del_objs = [context.scene.leftWindowObj + 'cutmouldpoint',
                    context.scene.leftWindowObj + 'cutmouldpoint_extruded',
                    context.scene.leftWindowObj + 'cutmouldpoint_extruded2',
                    context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj',
                    context.scene.leftWindowObj + 'cut_mould_sphere']
        for obj in del_objs:
            if (bpy.data.objects.get(obj)):
                bpy.data.objects.remove(bpy.data.objects.get(obj), do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects[context.scene.leftWindowObj]
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # 重新初始化
        bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")


class Finish_CutMould(bpy.types.Operator):
    bl_idname = "cutmould.finishcut"
    bl_label = "完成切割"

    def invoke(self, context, event):
        bpy.context.scene.var = 91
        self.execute(context)
        record_state()
        return {'FINISHED'}

    def execute(self, context):
        global color_mode
        # 应用切割
        cut_obj = bpy.data.objects.get(context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj')
        if cut_obj:
            apply_cut_mould(color_mode)
            # bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        else:
            bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch2")

        if not bpy.context.scene.pressfinish:
            unregister_tools()
            bpy.context.scene.pressfinish = True


class TEST_OT_cutmouldstart(bpy.types.Operator):
    bl_idname = "cutmould.start"
    bl_label = "cutmouldstart"
    bl_description = "开始切割模具"

    def invoke(self, context, event):  # 初始化
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
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
        newColor('blue', 0, 0, 1, 0, 1)
        new_curve_data.materials.append(bpy.data.materials['blue'])
        new_curve_data.splines.clear()
        new_spline = new_curve_data.splines.new(type='NURBS')
        new_spline.use_smooth = True
        new_spline.order_u = 2
        new_curve_data.splines[0].points[0].co[0:3] = co
        new_curve_data.splines[0].points[0].co[3] = 1
        start_curve()
        bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch2")


class TEST_OT_cutmouldfinish(bpy.types.Operator):
    bl_idname = "cutmould.finish"
    bl_label = "cutmouldfinish"
    bl_description = "结束切割模具"

    def invoke(self, context, event):  # 初始化
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global color_mode
        co = get_co()
        add_curve_name = context.scene.leftWindowObj + 'cutmouldpoint'
        curve_obj = bpy.data.objects[add_curve_name]
        if ((co - Vector(curve_obj.data.splines[0].points[0].co[0:3])).length < 1 and
                len(curve_obj.data.splines[0].points) > 2):
            sphere_obj = bpy.data.objects.get(context.scene.leftWindowObj + 'cut_mould_sphere')
            if sphere_obj:
                bpy.data.objects.remove(sphere_obj, do_unlink=True)
            curve_obj.data.splines[0].use_cyclic_u = True
            # bpy.ops.object.select_all(action='DESELECT')
            # bpy.context.view_layer.objects.active = curve_obj
            # curve_obj.select_set(True)
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.curve.select_all(action='SELECT')
            # # 细分
            # bpy.ops.curve.subdivide(number_cuts=10)
            # # 平滑
            # for _ in range(10):
            #     bpy.ops.curve.smooth()
            # bpy.ops.object.mode_set(mode='OBJECT')
            cut_obj = bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'cutmouldpoint_mesh_obj')
            if cut_obj:  # 如果没有应用切割将其提交
                apply_cut_mould(color_mode)

            # 生成切割用的物体
            extrude_curve_and_generate_faces(curve_obj, 20)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
            bpy.data.objects[context.scene.leftWindowObj].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")
            record_state()
            # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        else:
            pass


class TEST_OT_cutmouldaddpoint(bpy.types.Operator):
    bl_idname = "cutmould.addpoint"
    bl_label = "cutmouldaddpoint"
    bl_description = "单击左键添加控制点"

    def invoke(self, context, event):
        self.addpoint(context, event)
        return {'FINISHED'}

    def addpoint(self, context, event):
        name = context.scene.leftWindowObj
        add_curve_name = name + 'cutmouldpoint'
        curve_obj = bpy.data.objects.get(add_curve_name)
        co = get_co()
        if curve_obj != None:
            spline = curve_obj.data.splines[0]
            spline.points.add(1)
            spline.points[-1].co = (co[0], co[1], co[2], 1)


class TEST_OT_cutmoulddeletepoint(bpy.types.Operator):
    bl_idname = "cutmould.deletepoint"
    bl_label = "deletepoint"
    bl_description = "单击右键删除控制点"

    def invoke(self, context, event):
        self.deletepoint(context, event)
        return {'FINISHED'}

    def deletepoint(self, context, event):
        name = context.scene.leftWindowObj
        add_curve_name = name + 'cutmouldpoint'
        if bpy.data.objects.get(add_curve_name) != None:
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

            # 删除最后一个控制点
            elif curve_len == 1:
                sphere_obj = bpy.data.objects.get(context.scene.leftWindowObj + 'cut_mould_sphere')
                if sphere_obj:
                    bpy.data.objects.remove(sphere_obj, do_unlink=True)
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[add_curve_name]
                bpy.data.objects[add_curve_name].select_set(True)
                bpy.data.objects.remove(bpy.data.objects[add_curve_name], do_unlink=True)
                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                bpy.data.objects[name].select_set(True)
                bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")

            else:
                pass


def register():
    bpy.utils.register_class(Reset_CutMould)
    bpy.utils.register_class(Finish_CutMould)
    bpy.utils.register_class(TEST_OT_cutmouldstart)
    bpy.utils.register_class(TEST_OT_cutmouldaddpoint)
    bpy.utils.register_class(TEST_OT_cutmoulddeletepoint)
    bpy.utils.register_class(TEST_OT_cutmouldfinish)


def unregister():
    bpy.utils.unregister_class(Reset_CutMould)
    bpy.utils.unregister_class(Finish_CutMould)
    bpy.utils.unregister_class(TEST_OT_cutmouldstart)
    bpy.utils.unregister_class(TEST_OT_cutmouldaddpoint)
    bpy.utils.unregister_class(TEST_OT_cutmoulddeletepoint)
    bpy.utils.unregister_class(TEST_OT_cutmouldfinish)
