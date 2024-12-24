import bpy
import bmesh
import numpy as np
from ...utils.utils import utils_get_order_border_vert, utils_draw_curve, resample_curve
from ...tool import delete_vert_group, set_vert_group, subdivide, convert_to_mesh, moveToRight, moveToLeft, delete_useless_object, newColor
from ..parameters_for_create_mould import get_template_high, get_template_low, get_left_template_high, get_left_template_low
import math

min_z_before_cut = None
max_z_before_cut = None

def hard_recover_before_cut_and_remind_border():
    '''
    恢复到进入切割模式并且保留边界线，用于挖孔，切割报错时恢复
    '''
    recover_flag = False
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.context.view_layer.objects:
        if obj.name == name + "OriginForCreateMouldR":
            recover_flag = True
            break
    # 找到最初创建的  OriginForCreateMould 才能进行恢复
    if recover_flag:
        # 删除不需要的物体
        need_to_delete_model_name_list = [name, name + 'CutPlane']
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
        # if name == '右耳':
        #     moveToRight(duplicate_obj)
        # elif name == '左耳':
        #     moveToLeft(duplicate_obj)
        # duplicate_obj.hide_set(True)


def get_target_high_and_low():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name + "OriginForFitPlace"]

    # main_obj = bpy.data.objects[name]
    #
    # bpy.ops.object.select_all(action='DESELECT')
    # # 2024/05/29 这里要把obj显示出来才能设置为激活物体
    # obj.hide_set(False)
    # bpy.context.view_layer.objects.active = obj
    # obj.select_set(True)
    # bpy.ops.object.mode_set(mode='EDIT')
    # bm = bmesh.from_edit_mesh(obj.data)
    # result = []
    # for v in bm.verts:
    #     result.append(v)
    #
    # result.sort(key=lambda vert: vert.co[2], reverse=True)
    # high = result[0].co[0:3]
    # low = result[-1].co[0:3]
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.view_layer.objects.active = main_obj
    # main_obj.select_set(True)
    # obj.hide_set(True)

    result = []
    for v in obj.data.vertices:
        result.append(v)
    result.sort(key=lambda vert: vert.co[2], reverse=True)
    high = result[0].co[0:3]
    low = result[-1].co[0:3]
    return high, low


def get_actual_co(origin_co, target_high, target_low):
    template_high = get_template_high()
    template_low = get_template_low()

    templateL_high = get_left_template_high()
    templateL_low = get_left_template_low()

    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        high_percent = (origin_co[2] - template_low[2]) / (template_high[2] - template_low[2]) - 0.1
    elif name == '左耳':
        high_percent = (origin_co[2] - templateL_low[2]) / (templateL_high[2] - templateL_low[2]) - 0.1
    # high_percent = (origin_co[2] - template_low[2]) / (template_high[2] - template_low[2]) - 0.1


    xx_co = origin_co[0]
    yy_co = origin_co[1]

    zz_co = (target_high[2] - target_low[2]) * high_percent + target_low[2]
    actual_co = (xx_co, yy_co, zz_co)

    return actual_co


def translate_curve_to_mesh():
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects[name + "CutPlane"]
    main_obj = bpy.data.objects[name]

    bpy.context.view_layer.objects.active = curve_obj
    main_obj.select_set(False)
    curve_obj.select_set(True)

    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.looptools_flatten(influence=40, lock_x=False, lock_y=False, lock_z=False, plane='best_fit',
                                   restriction='none')
    bpy.ops.mesh.select_all(action='DESELECT')

    # 简化后可能会有几个点单独吊出来，需要删掉
    bm = bmesh.from_edit_mesh(curve_obj.data)
    for v in bm.verts:
        if len(v.link_edges) == 1:
            v.select_set(True)
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    curve_obj.select_set(False)


def judge_normals():
    name = bpy.context.scene.leftWindowObj
    # selected_objs = bpy.data.objects
    # for selected_obj in selected_objs:
    #     print(selected_obj.name)
    cut_plane = bpy.data.objects[name + "CutPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)
    sum = 0
    for v in cut_plane_mesh.verts:
        sum += v.normal[2]
    return sum < 0


def get_bigger_cut_plane():
    circle_count = 0
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects[name + "CutPlane"]

    main_obj = bpy.data.objects[name]

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = curve_obj
    curve_obj.select_set(True)

    me = curve_obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    bpy.ops.mesh.select_all(action='SELECT')
    for _ in range(0, 12):
        curve_obj.vertex_groups.new(name="Circle" + str(circle_count))
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.duplicate()
        move_circle = [v for v in bm.verts if v.select]
        bpy.ops.object.vertex_group_remove_from()
        circle_count = circle_count + 1
        # 不用走的很精准，直接缩放
        bpy.ops.transform.resize(value=(1.2, 1.2, 1.1), orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                 mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                                 proportional_size=1, use_proportional_connected=False,
                                 use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'},
                                 use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True,
                                 use_snap_nonedit=True, use_snap_selectable=False)

    # 处理最后一次移出的顶点
    curve_obj.vertex_groups.new(name="Circle" + str(circle_count))
    bpy.ops.object.vertex_group_assign()
    bmesh.update_edit_mesh(me)
    bm.free()

    # 进行桥接
    for i in range(1, circle_count + 1):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group="Circle" + str(i - 1))
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group="Circle" + str(i))
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.bridge_edge_loops()
    # 内里填充
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group="Circle0")
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.select_all(action='SELECT')
    if judge_normals():
        bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)


def plane_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        name = bpy.context.scene.leftWindowObj
        if obj.name == name:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    # 获取活动对象
    obj = bpy.context.active_object

    # 存一下原先的顶点
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    ori_border_index = [v.index for v in bm.verts if v.select]
    all_index = [v for v in bm.verts]
    all_index.sort(key=lambda vert: vert.co[2])
    global min_z_before_cut, max_z_before_cut
    min_z_before_cut = all_index[0].co[2]
    max_z_before_cut = all_index[-1].co[2]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("all", ori_border_index)

    # 添加一个修饰器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[obj.name].select_set(True)
    name = bpy.context.scene.leftWindowObj
    cut_obj = bpy.data.objects[name + "CutPlane"]
    # 该布尔插件会直接删掉切割平面，最好是使用复制去切，以防后续会用到
    duplicate_obj = cut_obj.copy()
    duplicate_obj.data = cut_obj.data.copy()
    duplicate_obj.animation_data_clear()
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.select_set(True)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    # 使用布尔插件
    bpy.ops.object.booltool_auto_difference()

    # 获取下边界顶点用于挤出
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='all')
    # 有时候切成功了，会直接把切面的新点选上，但all会乱掉，所以把切完后自动选上的点从all里移出
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    # 创建bmesh对象
    name = bpy.context.scene.leftWindowObj
    bm = bmesh.from_edit_mesh(bpy.data.objects[name].data)
    bottom_outer_border_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.delete(type='FACE')

    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # 将下边界加入顶点组
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')
    delete_vert_group("all")


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


def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    bm = bmesh.from_edit_mesh(obj.data)

    # 先删一下多余的面
    bpy.ops.mesh.delete(type='FACE')
    # 可能会切出不连续的小碎片，删除
    temp = list()
    for v in bm.verts:
        temp.append(v)
    temp.sort(key=lambda vert: vert.co[2], reverse=True)
    if len(temp) > 0:
        temp[0].select_set(True)
        bpy.ops.mesh.select_linked(delimit=set())
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='VERT')

    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()

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
    bottom_outer_border_vertex = bpy.data.objects[name].vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 判断切割是否把整个切掉了
    target_me = obj.data
    # 创建bmesh对象
    target_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    target_bm.from_mesh(target_me)
    global min_z_before_cut
    all_verts = [v for v in target_bm.verts]
    all_verts.sort(key=lambda vert: vert.co[2])
    if len(target_bm.verts) < 100:
        print("切割出错，完全切掉了")
        raise ValueError("切割出错，完全切掉了")
    elif min_z_before_cut == all_verts[0].co[2]:
        print("切割出错，没有切掉下半部分")
        if all_verts[-1].co[2] != max_z_before_cut:
            print("切反了")
            # recover_and_remind_border()
            # # 翻转平面法线
            # bpy.ops.object.select_all(action='DESELECT')
            # bpy.context.view_layer.objects.active = bpy.data.objects[name + "CutPlane"]
            # bpy.data.objects[name + "CutPlane"].select_set(True)
            # bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='SELECT')
            # bpy.ops.mesh.flip_normals()
            # bpy.ops.object.mode_set(mode='OBJECT')
            # plane_boolean_cut()
            # delete_useless_part()
        else:
            raise ValueError("切割出错，没有切掉下半部分")

    # 最后删掉没用的CutPlane
    # bpy.data.objects.remove(bpy.data.objects["CutPlane"], do_unlink=True)


def draw_cut_border_point():
    name = bpy.context.scene.leftWindowObj
    main_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    iterations = 0
    for i in range(0, iterations):
        bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
    # bpy.ops.mesh.select_nth(skip=5, nth=1)

    bm = bmesh.from_edit_mesh(main_obj.data)
    border_co = [v.co[0:3] for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    utils_draw_curve(utils_get_order_border_vert(border_co), name + "BottomRingBorderR", 0.18)
    blue_mat = bpy.data.materials.get('blue')
    newColor('blue', 0, 0, 1, 1, 1)
    bpy.data.objects[name + "BottomRingBorderR"].data.materials.append(bpy.data.materials['blue'])
    if name == '右耳':
        moveToRight(bpy.data.objects[name + "BottomRingBorderR"])
    elif name == '左耳':
        moveToLeft(bpy.data.objects[name + "BottomRingBorderR"])

    # 细分一次，避免来回切换时丢失顶点
    # subdivide("BottomRingBorderR", 1)
    # 生成用于判断鼠标位置的网格
    convert_to_mesh(name+"BottomRingBorderR", name + "meshBottomRingBorderR", 0.18)

    cur_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='EDIT')  # 选中切割后的循环边
    bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.object.mode_set(mode='OBJECT')


def init_hard_cut(hard_eardrum_border):
    name = bpy.context.scene.leftWindowObj
    # 存储模板耳道口边界的坐标与法向以及最高点坐标
    target_high, target_low = get_target_high_and_low()
    # 为了解决节点dead的问题，把bmesh信息获取拿出来，作为传参进去
    target_obj = bpy.data.objects[name]
    # 获取网格数据
    target_me = target_obj.data

    # 创建bmesh对象
    target_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    target_bm.from_mesh(target_me)
    target_bm.verts.ensure_lookup_table()

    border_vert_co = list()

    for vert in hard_eardrum_border:
        # cast_vert,cast_normal = normal_ray_cast(vert, rotate_angle, height_difference, target_bm)
        actual_co = get_actual_co(vert, target_high, target_low)
        border_vert_co.append(actual_co)

    # points = np.array(border_vert_co)
    # plane_border_index = find_convex_hull(points)
    # plane_border_co = points[plane_border_index].tolist()
    plane_border_co = convex_hull(border_vert_co)

    order_border_vert = utils_get_order_border_vert(plane_border_co)
    utils_draw_curve(order_border_vert, name + "CutPlane", 0)

    translate_curve_to_mesh()
    get_bigger_cut_plane()
    plane_cut()

    # 下面这个函数有改动，先删一下切出来的面
    delete_useless_part()
    draw_cut_border_point()
    resample_curve(160, name + "BottomRingBorderR")
    # bpy.data.objects["CutPlane"].hide_set(True)
    bpy.data.objects.remove(bpy.data.objects[name + "CutPlane"], do_unlink=True)
    # bpy.ops.object.shade_smooth(use_auto_smooth=True)


def get_cut_plane_for_re_cut():
    name = bpy.context.scene.leftWindowObj
    # 外边界顶点组
    bpy.data.objects[name].select_set(False)
    cut_plane_outer = bpy.data.objects[name + "CutPlane"]
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_outer.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Outer", vert_index)

    # 中间边界顶点组
    bpy.data.objects[name + "CutPlane"].select_set(False)
    cut_plane_center = bpy.data.objects[name + "Center"]
    bpy.context.view_layer.objects.active = cut_plane_center
    cut_plane_center.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_center.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Center", vert_index)

    # 内边界顶点组
    bpy.data.objects[name + "Center"].select_set(False)
    cut_plane_inner = bpy.data.objects[name + "Inner"]
    bpy.context.view_layer.objects.active = cut_plane_inner
    cut_plane_inner.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_inner.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Inner", vert_index)

    # 合并
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    cut_plane_center.select_set(True)
    cut_plane_inner.select_set(True)
    bpy.ops.object.join()

    # 拼接成面
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)

    # # 最内补面
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='Inner')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.edge_face_add()

    # 桥接内中边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='Center')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    # 桥接中外边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Outer')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='Center')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='SELECT')
    if judge_normals():
        bpy.ops.mesh.flip_normals()

    # bpy.ops.mesh.remove_doubles(threshold=0.25)

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects[name + "CutPlane"].select_set(False)
    main_obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)


# def re_hard_cut(hard_eardrum_border, step_number_out, step_number_in):
#     name = bpy.context.scene.leftWindowObj
#     utils_draw_curve(hard_eardrum_border, name + "BottomRingBorderR", 0.18)
#     # 给蓝线上色
#     newColor('blue', 0, 0, 1, 1, 1)
#     bpy.data.objects[name + "BottomRingBorderR"].data.materials.append(bpy.data.materials['blue'])
#     resample_curve(160,name + "BottomRingBorderR")
#     convert_to_mesh(name + 'BottomRingBorderR', name + 'meshBottomRingBorderR', 0.18)
#
#     # 重新切割
#     active_obj = bpy.data.objects[name + 'BottomRingBorderR']
#     duplicate_obj = active_obj.copy()
#     duplicate_obj.data = active_obj.data.copy()
#     duplicate_obj.name = name + "CutPlane"
#     duplicate_obj.animation_data_clear()
#     # 将复制的物体加入到场景集合中
#     bpy.context.collection.objects.link(duplicate_obj)
#     if name == '右耳':
#         moveToRight(duplicate_obj)
#     elif name == '左耳':
#         moveToLeft(duplicate_obj)
#
#     duplicate_obj.data.bevel_depth = 0
#     bpy.ops.object.select_all(action='DESELECT')
#     bpy.context.view_layer.objects.active = duplicate_obj
#     duplicate_obj.select_set(state=True)
#     bpy.ops.object.convert(target='MESH')
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='SELECT')
#     duplicate_obj.vertex_groups.new(name='HardEardrumBorderVertex')
#     bpy.ops.object.vertex_group_assign()
#     bpy.ops.mesh.offset_edges(geometry_mode='extrude', width=step_number_out, caches_valid=False)
#     bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
#     bpy.ops.object.vertex_group_remove_from()
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.vertex_group_select()
#     bpy.ops.mesh.offset_edges(geometry_mode='extrude', width=-step_number_in, caches_valid=False)
#     bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
#     bpy.ops.mesh.select_all(action='SELECT')
#     bpy.ops.mesh.normals_make_consistent(inside=False)
#     if judge_normals():
#         bpy.ops.mesh.flip_normals()
#     bpy.ops.object.mode_set(mode='OBJECT')
#     plane_cut()
#     # 下面这个函数有改动，先删一下切出来的面
#     delete_useless_part()
#     bpy.data.objects.remove(bpy.data.objects[name + "CutPlane"], do_unlink=True)


def re_hard_cut(hard_eardrum_border_and_normal, step_out, step_in):
    name = bpy.context.scene.leftWindowObj
    # 进入这里说明移动过蓝线了，进行二次切割，传入的参数已经是排序好的圆环数据，不需要重新排序
    center_border = list()
    inner_border = list()
    cut_plane_border = list()
    for item in hard_eardrum_border_and_normal:
        border_co = item[0]
        normal = item[1]
        center_border.append(border_co)
        cut_plane_border.append((border_co[0] + normal[0] * step_out, border_co[1] + normal[1] * step_out, border_co[2] + normal[2] * step_out))
        inner_border.append((border_co[0] - normal[0] * step_in, border_co[1] - normal[1] * step_in, border_co[2] - normal[2] * step_in))
    utils_draw_curve(center_border, name + "BottomRingBorderR", 0.18)
    # 给蓝线上色
    newColor('blue', 0, 0, 1, 1, 1)
    bpy.data.objects[name + "BottomRingBorderR"].data.materials.append(bpy.data.materials['blue'])
    resample_curve(160,name + "BottomRingBorderR")
    convert_to_mesh(name + 'BottomRingBorderR', name + 'meshBottomRingBorderR', 0.18)

    utils_draw_curve(center_border, name + "Center", 0)
    utils_draw_curve(cut_plane_border, name + "CutPlane", 0)
    utils_draw_curve(inner_border, name + "Inner", 0)

    # 根据中内外三圈绘制切割平面
    get_cut_plane_for_re_cut()
    # 套用切割
    plane_cut()
    # 下面这个函数有改动，先删一下切出来的面
    delete_useless_part()
    bpy.data.objects.remove(bpy.data.objects[name + "CutPlane"], do_unlink=True)
    # bpy.ops.object.shade_smooth(use_auto_smooth=True)


# ----------------凸包算法，用于把模板调整为凸多边形，防止扩大时重叠----------------
def normalize(v):
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm


def vector_angle(u, v):
    """Returns the angle between two vectors."""
    return np.arccos(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1.0, 1.0))


def find_convex_hull(points):
    n_points = points.shape[0]
    hull = []
    used_set = set()

    # Step 1: Find an initial point (e.g., the point with the lowest x-coordinate)
    initial_point = np.argmin(points[:, 0])
    hull.append(initial_point)

    # Step 2: Find a point that forms the smallest angle with the x-axis
    reference_direction = np.array([1, 0, 0])
    current_point = initial_point

    while True:
        next_point = None
        min_angle = 2 * np.pi

        for i in range(n_points):
            if i == current_point:
                continue

            candidate_direction = points[i] - points[current_point]
            angle = vector_angle(reference_direction, candidate_direction)

            if angle < min_angle:
                min_angle = angle
                next_point = i

        if next_point == initial_point or next_point in used_set:
            break  # Completed the hull
        hull.append(next_point)
        used_set.add(next_point)
        current_point = next_point
        reference_direction = points[next_point] - points[hull[-2]]

    return np.array(hull)


def orientation(p, q, r):
    """ 计算三点的方向 """
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0:
        return 0  # 共线
    return 1 if val > 0 else 2  # 顺时针或逆时针


def convex_hull(points):
    """ 使用 Graham 扫描算法计算凸包 """
    n = len(points)
    if n < 3:
        return points  # 不能形成凸包

    # 找到最低的点
    lowest = min(points, key=lambda p: (p[1], p[0]))
    points.remove(lowest)

    # 按极角排序
    points.sort(key=lambda p: math.atan2(p[1] - lowest[1], p[0] - lowest[0]))

    # 添加最低点
    hull = [lowest]

    for point in points:
        while len(hull) > 1 and orientation(hull[-2], hull[-1], point) != 2:
            hull.pop()
        hull.append(point)

    return hull
