import bpy
import bmesh
import mathutils
import time
from bpy_extras import view3d_utils
from math import sqrt
from mathutils import Vector
from collections import OrderedDict

from .soft_eardrum.thickness_and_fill import set_finish, fill, draw_cut_plane, reset_to_after_cut, soft_eardrum

from .frame_style_eardrum.frame_fill_inner_face import fill_closest_point
from .frame_style_eardrum.frame_style_eardrum_dig_hole import dig_hole, re_dig_hole

from .hard_eardrum.hard_eardrum_cut import hard_recover_before_cut_and_remind_border
from .hard_eardrum.hard_eardrum_bottom_fill import hard_bottom_fill, recover_before_fill

from .shell_eardrum.shell_eardrum_bottom_fill import set_shell_modal_finish, copy_model_for_bottom_curve, \
    reset_after_bottom_curve_change, bridge_and_refill

from .parameters_for_create_mould import set_right_hard_eardrum_border_template, \
    set_left_hard_eardrum_border_template
from .parameters_for_create_mould import set_right_soft_eardrum_border_template, \
    set_left_soft_eardrum_border_template
from .parameters_for_create_mould import set_right_frame_style_eardrum_border_template, \
    set_left_frame_style_eardrum_border_template, set_right_frame_style_hole_border, \
    set_left_frame_style_hole_border
from .parameters_for_create_mould import set_right_shell_plane_border, set_left_shell_plane_border, \
    set_right_shell_border, set_left_shell_border

from ..tool import recover_and_remind_border, moveToRight, moveToLeft, utils_re_color, convert_to_mesh, \
    recover_to_dig, newColor, getOverride, extrude_border_by_vertex_groups
from ..utils.utils import get_cut_plane, plane_boolean_cut, delete_useless_part, resample_curve, judge_normals
from ..parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running, \
    get_shell_modal_start, get_soft_modal_start, get_point_qiehuan_modal_start, get_drag_curve_modal_start, \
    get_smooth_curve_modal_start, set_point_qiehuan_modal_start, set_drag_curve_modal_start, \
    set_smooth_curve_modal_start, get_process_var_list

import re

prev_on_object = False
prev_mesh_name = ''
is_cut_finish = True
is_fill_finish = True
last_co = None            # 点加蓝线时第一个点的坐标
idx_list = []               # 点加蓝线时新增曲线的点的下标
snap_object_name = None          # 点加蓝线时吸附物体的名字

# point_qiehuan_modal_start = False
# drag_curve_modal_start = False
# smooth_curve_modal_start = False


def get_region_and_space(context, area_type, region_type, space_type):
    ''' 获得当前区域的信息 '''
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


def is_changed(context, event):
    '''
    判断鼠标状态是否发生改变
    '''
    name = bpy.context.scene.leftWindowObj
    obj_list = [name + 'MouldReset', name + 'batteryPlaneSnapCurve']
    curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
    global prev_on_object  # 之前鼠标是否在物体上

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

    for obj_name in obj_list:
        active_obj = bpy.data.objects.get(obj_name)
        if active_obj is None:
            continue
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
                    curr_on_object = True  # 如果发生交叉，将变量设为True
    if curr_on_object != prev_on_object:
        prev_on_object = curr_on_object
        return True

    return False


class MuJudict:

    ruanermolistR = ['右耳BottomRingBorderR', 0.18]
    ruanermolistL = ['左耳BottomRingBorderR', 0.18]
    ruanermodictR = OrderedDict([('右耳meshBottomRingBorderR', ruanermolistR)])
    ruanermodictL = OrderedDict([('左耳meshBottomRingBorderR', ruanermolistL)])

    yingermolistR = ['右耳BottomRingBorderR', 0.18]
    yingermolistL = ['左耳BottomRingBorderR', 0.18]
    yingermodictR = OrderedDict([('右耳meshBottomRingBorderR', yingermolistR)])
    yingermodictL = OrderedDict([('左耳meshBottomRingBorderR', yingermolistL)])

    kuangjialist1R = ['右耳BottomRingBorderR', 0.18]
    kuangjialist1L = ['左耳BottomRingBorderR', 0.18]
    kuangjialist2R = ['右耳HoleBorderCurve1', 0.18]
    kuangjialist2L = ['左耳HoleBorderCurve1', 0.18]
    # 只存在底部蓝线
    # kuangjiadictR = {'右耳meshBottomRingBorderR': kuangjialist1R}
    # kuangjiadictL = {'左耳meshBottomRingBorderR': kuangjialist1L}
    kuangjiadictR = OrderedDict([('右耳meshHoleBorderCurve1', kuangjialist2R), ('右耳meshBottomRingBorderR', kuangjialist1R)])
    kuangjiadictL = OrderedDict([('左耳meshHoleBorderCurve1', kuangjialist2L), ('左耳meshBottomRingBorderR', kuangjialist1L)])

    waikelist1R = ['右耳BottomRingBorderR', 0.18]
    waikelist1L = ['左耳BottomRingBorderR', 0.18]
    waikelist12R = ['右耳PlaneBorderCurve', 0.18]
    waikelist12L = ['左耳PlaneBorderCurve', 0.18]
    waikedictR = OrderedDict([('右耳meshPlaneBorderCurve', waikelist12R), ('右耳meshBottomRingBorderR', waikelist1R)])
    waikedictL = OrderedDict([('左耳meshPlaneBorderCurve', waikelist12L), ('左耳meshBottomRingBorderR', waikelist1L)])

    yitidict = {}
    mianbandict = {}

    mujudictR = {'软耳模': ruanermodictR,
                '硬耳膜': yingermodictR,
                '常规外壳': waikedictR,
                '框架式耳膜': kuangjiadictR,
                '一体外壳': yitidict,
                '实心面板': mianbandict}

    mujudictL = {'软耳模': ruanermodictL,
                 '硬耳膜': yingermodictL,
                 '常规外壳': waikedictL,
                 '框架式耳膜': kuangjiadictL,
                 '一体外壳': yitidict,
                 '实心面板': mianbandict}

    def get_dic_name(self):
        ''' 获得当前磨具类型的曲线字典 '''
        enum = bpy.context.scene.muJuNameEnum
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            return self.mujudictR[enum]
        elif name == '左耳':
            return self.mujudictL[enum]


    def update_dic(self):
        number = 0
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            dic = self.kuangjiadictR
        elif name == '左耳':
            dic = self.kuangjiadictL
        for key in dic:
            if re.match(name + 'meshHoleBorderCurve', key) != None:
                number += 1
        add_mesh_name = name + 'meshHoleBorderCurve' + str(number + 1)
        # mesh = bpy.data.meshes.new(add_mesh_name)
        # obj = bpy.data.objects.new(add_mesh_name, mesh)
        # bpy.context.scene.collection.objects.link(obj)
        # if name == '右耳':
        #     moveToRight(obj)
        # elif name == '左耳':
        #     moveToLeft(obj)
        add_curve_name = name + 'HoleBorderCurve' + str(number + 1)
        tempkuangjialist = [add_curve_name, 0.18]
        if name == '右耳':
            dic[add_mesh_name] = tempkuangjialist
            dic.move_to_end(add_mesh_name, last=False)
        elif name == '左耳':
            dic[add_mesh_name] = tempkuangjialist
            dic.move_to_end(add_mesh_name, last=False)
        return add_curve_name


def co_on_object(dic, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param dic: 要检测物体的字典
    :return: 相交的坐标、相交物体的名字和对应曲线的列表
    '''
    flag = False

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

    for key in dic:
        active_obj = bpy.data.objects.get(key)
        if active_obj is None:
            flag = True
            continue

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
                    return co, key, dic[key]  # 如果发生交叉，返回

    if flag:  # 如果没有物体
        return 0
    else:
        return -1


def cal_co(mesh_name, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param mesh_name: 要检测物体的名字
    :return: 相交的坐标
    '''

    active_obj = bpy.data.objects.get(mesh_name)
    if active_obj is None:
        return -1

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
                return co  # 如果发生交叉，返回坐标的值

    return -1


def select_nearest_point(curve_name, co):
    '''
    选择曲线上离坐标位置最近的点
    :param curve_name: 曲线的名字
    :param co: 坐标的值
    :return: 最近点在曲线上的下标
    '''
    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects[curve_name]
    # 获取曲线的数据
    curve_data = curve_obj.data
    # 遍历曲线的所有点
    min_dis = float('inf')
    min_dis_index = -1

    for spline in curve_data.splines:
        for point_index, point in enumerate(spline.points):
            # 计算点与给定点之间的距离
            distance_vector = Vector(point.co[0:3]) - co
            distance = distance_vector.dot(distance_vector)
            # 更新最小距离和对应的点索引
            if distance < min_dis:
                min_dis = distance
                min_dis_index = point_index

    return min_dis_index


def copy_curve(curve_name):
    ''' 复制曲线数据 '''
    name = bpy.context.scene.leftWindowObj
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = 'new' + curve_name
    # 创建一个新的曲线对象来存储复制的数据
    new_curve = bpy.data.curves.new(new_name, 'CURVE')
    new_curve.dimensions = '3D'
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)
    if name == '右耳':
        moveToRight(new_obj)
    elif name == '左耳':
        moveToLeft(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.points.add(len(spline.points) - 1)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def judge_curve(source_obj, curve_obj):
    center = mathutils.Vector((0, 0, 0))
    for point in curve_obj.data.splines[0].points:
        center += Vector(point.co[0:3])
    center /= len(curve_obj.data.splines[0].points)
    index_center = select_nearest_point(source_obj.name, center)
    return index_center


def calculate_direction(start, end, middle, n):
    # 计算顺时针距离
    clockwise_distance = (end - start) % n
    if clockwise_distance < 0:
        clockwise_distance += n

    # 计算从起始点到中间点的顺时针距离
    middle_clockwise_distance = (middle - start) % n
    if middle_clockwise_distance < 0:
        middle_clockwise_distance += n

    # 判断中间点在起始点到结束点的哪一侧
    if middle_clockwise_distance <= clockwise_distance:
        return "顺时针方向"
    else:
        return "逆时针方向"


def join_curve(curve_name, depth, index_initial, index_finish):
    '''
    合并曲线(添加蓝线point后)
    :param curve_name: 曲线名字
    :param depth: 曲线倒角深度
    :param index_initial: 曲线起始位置下标
    :param index_finish: 曲线结束位置下标
    '''
    # 经过起始点（下标为0）可能会切反
    name = bpy.context.scene.leftWindowObj
    # 获取两条曲线对象
    curve_obj1 = bpy.data.objects[curve_name]
    curve_obj2 = bpy.data.objects[name + 'point']
    len1 = len(curve_obj1.data.splines[0].points)

    # 判断曲线的方向
    index_center = judge_curve(curve_obj1, curve_obj2)

    direction = calculate_direction(index_initial, index_finish, index_center, len1)
    print(direction)

    # if index_initial > index_finish:  # 起始点的下标大于结束点
    if direction == "逆时针方向":
        # 获取两条曲线的曲线数据
        curve_data1 = curve_obj1.data
        curve_data2 = curve_obj2.data

        # 创建一个新的曲线对象
        new_curve_data = bpy.data.curves.new(
            name=name + "newcurve", type='CURVE')
        new_curve_obj = bpy.data.objects.new(
            name=name + "newcurve", object_data=new_curve_data)

        # 将新的曲线对象添加到场景中
        bpy.context.collection.objects.link(new_curve_obj)
        if name == '右耳':
            moveToRight(new_curve_obj)
        elif name == '左耳':
            moveToLeft(new_curve_obj)

        # 获取新曲线对象的曲线数据
        new_curve_data = new_curve_obj.data

        # 计算逆时针距离
        counterclockwise_distance = (index_initial - index_finish) % len1
        if counterclockwise_distance < 0:
            counterclockwise_distance += len1

        # 合并两条曲线的点集
        new_curve_data.splines.clear()
        new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
        point_number = len(curve_data1.splines[0].points) + len(
            curve_data2.splines[0].points) - counterclockwise_distance - 3
        new_spline.points.add(point_number)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True

        len2 = len(curve_data2.splines[0].points)  # length为第二条曲线的长度

        # 先复制第二条曲线
        for i, point in enumerate(curve_data2.splines[0].points):
            if i > point_number:
                break
            new_spline.points[i].co = point.co

        # 将第一条曲线的点复制到新曲线
        start_index = (index_finish - 1 + len1) % len1
        idx = 0
        while ((start_index - 1 + len1) % len1) != index_initial:
            if len2 + idx > point_number:
                break
            new_spline.points[len2 + idx].co = curve_data1.splines[0].points[start_index].co
            start_index = (start_index - 1 + len1) % len1
            idx += 1

        # 反转曲线方向
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.curve.select_all(action='SELECT')
        # bpy.ops.curve.switch_direction()
        # bpy.ops.object.mode_set(mode='OBJECT')

    else:
        # 获取两条曲线的曲线数据
        curve_data1 = curve_obj1.data
        curve_data2 = curve_obj2.data

        # 创建一个新的曲线对象
        new_curve_data = bpy.data.curves.new(
            name=name + "newcurve", type='CURVE')
        new_curve_obj = bpy.data.objects.new(
            name=name + "newcurve", object_data=new_curve_data)

        # 将新的曲线对象添加到场景中
        bpy.context.collection.objects.link(new_curve_obj)
        if name == '右耳':
            moveToRight(new_curve_obj)
        elif name == '左耳':
            moveToLeft(new_curve_obj)

        # 获取新曲线对象的曲线数据
        new_curve_data = new_curve_obj.data

        # 计算逆时针距离
        counterclockwise_distance = (index_finish - index_initial) % len1
        if counterclockwise_distance < 0:
            counterclockwise_distance += len1

        # 合并两条曲线的点集
        new_curve_data.splines.clear()
        new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
        point_number = len(curve_data1.splines[0].points) + len(
            curve_data2.splines[0].points) - counterclockwise_distance - 3
        new_spline.points.add(point_number)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True

        len2 = len(curve_data2.splines[0].points)  # length为第二条曲线的长度

        # 先复制第二条曲线
        for i, point in enumerate(curve_data2.splines[0].points):
            if i > point_number:
                break
            new_spline.points[i].co = point.co

        # 将第一条曲线的点复制到新曲线
        start_index = (index_finish + 1 + len1) % len1
        idx = 0
        while ((start_index + 1 + len1) % len1) != index_initial:
            if len2 + idx > point_number:
                break
            new_spline.points[len2 + idx].co = curve_data1.splines[0].points[start_index].co
            start_index = (start_index + 1 + len1) % len1
            idx += 1

    bpy.data.objects.remove(curve_obj1, do_unlink=True)
    bpy.data.objects.remove(curve_obj2, do_unlink=True)
    new_curve_obj.name = curve_name

    new_curve_obj.data.bevel_depth = depth
    new_curve_obj.data.dimensions = '3D'
    new_curve_obj.data.materials.append(bpy.data.materials['blue'])

    # 平滑
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.curve.select_all(action='DESELECT')
    # for i in range(0, len2, 1):  # 选中原本在第二条曲线上的点
    #     new_curve_data.splines[0].points[i].select = True
    # new_curve_data.splines[0].points[-1].select = True
    # new_curve_data.splines[0].points[len2].select = True
    # for _ in range(0, 3):
    #     bpy.ops.curve.smooth()
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # target_object = bpy.data.objects[name + "MouldReset"]
    # # 将曲线的每个顶点吸附到目标物体的表面
    # for i in range(0, len2, 1):  # 选中原本在第二条曲线上的点
    #     # 获取顶点原位置
    #     point = new_curve_data.splines[0].points[i]
    #
    #     # 计算顶点在目标物体面上的 closest point
    #     _, closest_co, _, _ = target_object.closest_point_on_mesh(
    #         Vector(point.co[0:3]))
    #
    #     # 将顶点位置设置为 closest point
    #     point.co[0:3] = closest_co
    #     point.co[3] = 1

    # 细分曲线，添加控制点
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.curve.select_all(action='DESELECT')
    # for i in range(index_initial, end_point, 1):  # 选中原本在第二条曲线上的点
    #     new_curve_data.splines[0].points[i].select = True
    # bpy.ops.curve.subdivide(number_cuts=3)  # 细分次数
    # bpy.ops.object.mode_set(mode='OBJECT')
    # snaptoobject(curve_name)  # 将曲线吸附到物体上
    # moveToRight(new_curve_obj)


def update_cut(curve_name, mesh_name, depth):
    '''
    更新切割状态，用于下一次切割
    :param curve_name:曲线名字
    :param mesh_name:曲线对应的网格名字
    :param depth:曲线倒角深度
    '''

    global is_fill_finish
    # 根据选择模板进入不同的切割方式
    enum_name = bpy.context.scene.muJuNameEnum
    name = bpy.context.scene.leftWindowObj
    if (enum_name == '软耳模'):
        set_finish(True)
        recover_and_remind_border()
        resample_curve(160, curve_name)
        convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
        recut_success = True
        try:
            soft_generate_cutplane(2, 2)  # 生成曲线
            get_cut_plane()
            # soft_generate_cutplane(2, 1)  # 生成曲线
            plane_boolean_cut()
            delete_useless_part()

            # 复制一份右耳
            cur_obj = bpy.data.objects[name]
            duplicate_obj = cur_obj.copy()
            duplicate_obj.data = cur_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = cur_obj.name + "huanqiecompare"
            bpy.context.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            elif name == '左耳':
                moveToLeft(duplicate_obj)
            duplicate_obj.hide_set(True)

            if name == "右耳":
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowR"])
            elif name == "左耳":
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowL"])

        except:
            print("切割出错")
            recut_success = False
            # 回退到初始
            hard_recover_before_cut_and_remind_border()

            if bpy.data.materials.get("error_yellow") == None:
                mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                mat.use_backface_culling = False
            bpy.data.objects[name].data.materials.clear()
            bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])

        if recut_success:
            bpy.ops.object.pointfill('INVOKE_DEFAULT')
            is_fill_finish = False

    elif (enum_name == '框架式耳膜'):
        set_finish(True)
        if (re.match(name + 'HoleBorderCurve', curve_name) != None):  # 上部曲线改变
            # recover_to_dig()
            reset_to_after_cut()
            convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
            number = 0
            for obj in bpy.data.objects:
                if re.match(name + 'HoleBorderCurve', obj.name) != None:
                    number += 1

            # 记录点的坐标
            frame_hole_border_list = list()
            for i in range(1, number + 1):
                local_curve_name = name + 'HoleBorderCurve' + str(i)
                curve_obj = bpy.data.objects[local_curve_name]
                dig_border = [point.co[0:3] for point in curve_obj.data.splines[0].points]
                frame_hole_border_list.append(dig_border)

            if name == '左耳':
                set_left_frame_style_hole_border(frame_hole_border_list)
            elif name == '右耳':
                set_right_frame_style_hole_border(frame_hole_border_list)

            bpy.ops.object.pointfill('INVOKE_DEFAULT')
            is_fill_finish = False

        else:  # 下部曲线改变
            recover_and_remind_border()
            resample_curve(160, curve_name)
            convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
            recut_success = True
            try:
                frame_generate_cutplane(2, 2)  # 生成曲线
                get_cut_plane()
                # frame_generate_cutplane(2, 1)  # 生成曲线
                plane_boolean_cut()
                delete_useless_part()
                # 复制一份右耳
                cur_obj = bpy.data.objects[name]
                duplicate_obj = cur_obj.copy()
                duplicate_obj.data = cur_obj.data.copy()
                duplicate_obj.animation_data_clear()
                duplicate_obj.name = cur_obj.name + "huanqiecompare"
                bpy.context.collection.objects.link(duplicate_obj)
                if name == '右耳':
                    moveToRight(duplicate_obj)
                elif name == '左耳':
                    moveToLeft(duplicate_obj)
                duplicate_obj.hide_set(True)

                # extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")
            except:
                print("切割出错")
                recut_success = False
                # 回退到初始
                hard_recover_before_cut_and_remind_border()

                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])

            if recut_success and bpy.data.objects.get(name + "HoleBorderCurve1") != None:
                bpy.ops.object.pointfill('INVOKE_DEFAULT')
                is_fill_finish = False

            # 删除原有的挖孔边界
            # for obj in bpy.data.objects:
            #     if re.match(name + 'HoleBorderCurve', obj.name) != None:
            #         bpy.data.objects.remove(obj, do_unlink=True)
            # 重新挖孔
            # dig_flag = re_dig_hole()
            # if dig_flag:
            #     fill_closest_point()

    elif (enum_name == '硬耳膜'):
        if bpy.context.scene.leftWindowObj == '右耳':
            bpy.context.scene.yingErMoSheRuPianYiR = 0
        else:
            bpy.context.scene.yingErMoSheRuPianYiL = 0
        recover_and_remind_border()
        resample_curve(160, curve_name)
        convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
        recut_success = True
        try:
            hard_generate_cutplane(2, 2)  # 生成曲线
            get_cut_plane()
            # hard_generate_cutplane(2, 1)  # 生成曲线
            plane_boolean_cut()
            delete_useless_part()

            if name == "右耳":
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowR"])
            elif name == "左耳":
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowL"])
        except:
            print("切割出错")
            recut_success = False
            # 回退到初始
            hard_recover_before_cut_and_remind_border()

            if bpy.data.materials.get("error_yellow") == None:
                mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                mat.use_backface_culling = False
            bpy.data.objects[name].data.materials.clear()
            bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])

        if recut_success:
            bpy.ops.object.pointfill('INVOKE_DEFAULT')
            is_fill_finish = False

    elif (enum_name == '常规外壳'):
        set_shell_modal_finish(True)
        if curve_name == name + "PlaneBorderCurve":  # 底部曲线改变
            reset_after_bottom_curve_change()
            convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格

            curve_obj = bpy.data.objects[curve_name]
            shell_border_list = [point.co[0:3] for point in curve_obj.data.splines[0].points]

            if name == '左耳':
                set_left_shell_plane_border(shell_border_list)
            elif name == '右耳':
                set_right_shell_plane_border(shell_border_list)

            bpy.ops.object.pointfill('INVOKE_DEFAULT')
            is_fill_finish = False

        else:  # 切割的蓝线改变
            recover_and_remind_border()
            resample_curve(160, curve_name)
            convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
            recut_success = True
            try:
                shell_generate_cutplane(2, 2)  # 生成曲线
                get_cut_plane()
                plane_boolean_cut()
                delete_useless_part()
                copy_model_for_bottom_curve()
            except:
                print("切割出错")
                recut_success = False
                # 回退到初始
                hard_recover_before_cut_and_remind_border()

                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])

            if recut_success:
                bpy.ops.object.pointfill('INVOKE_DEFAULT')
                is_fill_finish = False

        # 之前版本
        # bpy.ops.object.mode_set(mode='EDIT')  # 选中切割后的循环边
        # cur_obj = bpy.data.objects["右耳"]
        # bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
        # if (bottom_outer_border_vertex != None):
        #     bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.object.mode_set(mode='OBJECT')
        # bottom_fill()  # 底面切割后补面并且重拓扑
        # convert_to_mesh('BottomRingBorderR', 'meshBottomRingBorderR', 0.18)
        # bpy.ops.object.timer_add_modifier_after_qmesh()


# def soft_generate_cutplane(step_number_out, step_number_in):
#     name = bpy.context.scene.leftWindowObj
#     active_obj = bpy.data.objects[name + 'BottomRingBorderR']
#     duplicate_obj = active_obj.copy()
#     duplicate_obj.data = active_obj.data.copy()
#     duplicate_obj.name = name + "CutPlane"
#     duplicate_obj.animation_data_clear()
#     # 将复制的物体加入到场景集合中
#     bpy.context.collection.objects.link(duplicate_obj)
#     soft_border_template = [point.co[0:3] for point in duplicate_obj.data.splines[0].points]
#     if name == '右耳':
#         moveToRight(duplicate_obj)
#         set_right_soft_eardrum_border_template(soft_border_template)
#     elif name == '左耳':
#         moveToLeft(duplicate_obj)
#         set_left_soft_eardrum_border_template(soft_border_template)
#
#     duplicate_obj.data.bevel_depth = 0
#     bpy.ops.object.select_all(action='DESELECT')
#     bpy.context.view_layer.objects.active = duplicate_obj
#     duplicate_obj.select_set(state=True)
#     bpy.ops.object.convert(target='MESH')
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='SELECT')
#     duplicate_obj.vertex_groups.new(name='SoftEardrumBorderVertex')
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


def soft_generate_cutplane(step_number_out, step_number_in):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name + 'BottomRingBorderR']
    # active_obj.data.bevel_depth = 0
    # bpy.context.view_layer.objects.active = active_obj
    # bpy.ops.object.modifier_add(type='SHRINKWRAP')
    # active_obj.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
    # active_obj.modifiers["Shrinkwrap"].target = bpy.data.objects[name + 'MouldReset']
    # bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects[name + "MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects[name + 'Center']
    curve_object2 = bpy.data.objects[name + 'CutPlane']
    curve_object3 = bpy.data.objects[name + 'Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)

    soft_border_template = list()
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)

        soft_border_template.append((vertex_co[0:3], normal[0:3]))

        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)


    if name == '右耳':
        set_right_soft_eardrum_border_template(soft_border_template)
    elif name == '左耳':
        set_left_soft_eardrum_border_template(soft_border_template)

    # active_obj.data.bevel_depth = 0.18
    bpy.data.objects[name + 'Center'].data.bevel_depth = 0
    bpy.data.objects[name + 'CutPlane'].data.bevel_depth = 0
    bpy.data.objects[name + 'Inner'].data.bevel_depth = 0


# def frame_generate_cutplane(step_number_out, step_number_in):
#     name = bpy.context.scene.leftWindowObj
#     active_obj = bpy.data.objects[name + 'BottomRingBorderR']
#     duplicate_obj = active_obj.copy()
#     duplicate_obj.data = active_obj.data.copy()
#     duplicate_obj.name = name + "CutPlane"
#     duplicate_obj.animation_data_clear()
#     # 将复制的物体加入到场景集合中
#     bpy.context.collection.objects.link(duplicate_obj)
#     frame_border_template = [point.co[0:3] for point in duplicate_obj.data.splines[0].points]
#     if name == '右耳':
#         moveToRight(duplicate_obj)
#         set_right_frame_style_eardrum_border_template(frame_border_template)
#     elif name == '左耳':
#         moveToLeft(duplicate_obj)
#         set_left_frame_style_eardrum_border_template(frame_border_template)
#
#     duplicate_obj.data.bevel_depth = 0
#     bpy.ops.object.select_all(action='DESELECT')
#     bpy.context.view_layer.objects.active = duplicate_obj
#     duplicate_obj.select_set(state=True)
#     bpy.ops.object.convert(target='MESH')
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='SELECT')
#     duplicate_obj.vertex_groups.new(name='FrameEardrumBorderVertex')
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


def frame_generate_cutplane(step_number_out, step_number_in):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name + 'BottomRingBorderR']
    # active_obj.data.bevel_depth = 0
    # bpy.context.view_layer.objects.active = active_obj
    # bpy.ops.object.modifier_add(type='SHRINKWRAP')
    # active_obj.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
    # active_obj.modifiers["Shrinkwrap"].target = bpy.data.objects[name + 'MouldReset']
    # bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects[name + "MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects[name + 'Center']
    curve_object2 = bpy.data.objects[name + 'CutPlane']
    curve_object3 = bpy.data.objects[name + 'Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)
    frame_border_template = list()
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)

        frame_border_template.append((vertex_co[0:3], normal[0:3]))

        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)

    if name == '右耳':
        set_right_frame_style_eardrum_border_template(frame_border_template)
    elif name == '左耳':
        set_left_frame_style_eardrum_border_template(frame_border_template)

    # active_obj.data.bevel_depth = 0.18
    bpy.data.objects[name + 'Center'].data.bevel_depth = 0
    bpy.data.objects[name + 'CutPlane'].data.bevel_depth = 0
    bpy.data.objects[name + 'Inner'].data.bevel_depth = 0


# def hard_generate_cutplane(step_number_out, step_number_in):
#     name = bpy.context.scene.leftWindowObj
#     active_obj = bpy.data.objects[name + 'BottomRingBorderR']
#     duplicate_obj = active_obj.copy()
#     duplicate_obj.data = active_obj.data.copy()
#     duplicate_obj.name = name + "CutPlane"
#     duplicate_obj.animation_data_clear()
#     # 将复制的物体加入到场景集合中
#     bpy.context.collection.objects.link(duplicate_obj)
#     hard_border_template = [point.co[0:3] for point in duplicate_obj.data.splines[0].points]
#     if name == '右耳':
#         moveToRight(duplicate_obj)
#         set_right_hard_eardrum_border_template(hard_border_template)
#     elif name == '左耳':
#         moveToLeft(duplicate_obj)
#         set_left_hard_eardrum_border_template(hard_border_template)
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


def hard_generate_cutplane(step_number_out, step_number_in):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name + 'BottomRingBorderR']
    # active_obj.data.bevel_depth = 0
    # bpy.context.view_layer.objects.active = active_obj
    # bpy.ops.object.modifier_add(type='SHRINKWRAP')
    # active_obj.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
    # active_obj.modifiers["Shrinkwrap"].target = bpy.data.objects[name + 'MouldReset']
    # bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects[name + "MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects[name + 'Center']
    curve_object2 = bpy.data.objects[name + 'CutPlane']
    curve_object3 = bpy.data.objects[name + 'Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)

    hard_border_template = list()
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)

        hard_border_template.append((vertex_co[0:3], normal[0:3]))

        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)


    if name == '右耳':
        set_right_hard_eardrum_border_template(hard_border_template)
    elif name == '左耳':
        set_left_hard_eardrum_border_template(hard_border_template)

    # active_obj.data.bevel_depth = 0.18
    bpy.data.objects[name + 'Center'].data.bevel_depth = 0
    bpy.data.objects[name + 'CutPlane'].data.bevel_depth = 0
    bpy.data.objects[name + 'Inner'].data.bevel_depth = 0


def shell_generate_cutplane(step_number_out, step_number_in):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name + 'BottomRingBorderR']
    # active_obj.data.bevel_depth = 0
    # bpy.context.view_layer.objects.active = active_obj
    # bpy.ops.object.modifier_add(type='SHRINKWRAP')
    # active_obj.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
    # active_obj.modifiers["Shrinkwrap"].target = bpy.data.objects[name + 'MouldReset']
    # bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = name + "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects[name + "MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects[name + 'Center']
    curve_object2 = bpy.data.objects[name + 'CutPlane']
    curve_object3 = bpy.data.objects[name + 'Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)

    shell_border_template = list()
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)

        shell_border_template.append((vertex_co[0:3], normal[0:3]))

        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)


    if name == '右耳':
        set_right_shell_border(shell_border_template)
    elif name == '左耳':
        set_left_shell_border(shell_border_template)

    # active_obj.data.bevel_depth = 0.18
    bpy.data.objects[name + 'Center'].data.bevel_depth = 0
    bpy.data.objects[name + 'CutPlane'].data.bevel_depth = 0
    bpy.data.objects[name + 'Inner'].data.bevel_depth = 0


def join_object(curve_name, mesh_name, depth, index_start, index_finish):
    ''' 合并曲线并转化成网格用于下一次操作 '''

    join_curve(curve_name, depth, index_start, index_finish)  # 合并曲线
    update_cut(curve_name, mesh_name, depth)  # 更新切割状态


def smoothcurve(curve_name, index, number):
    curve_obj = bpy.data.objects[curve_name]
    bpy.context.view_layer.objects.active = curve_obj
    curve_data = curve_obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    start_index = (index - number + point_number) % point_number
    finish_index = (index + number + point_number) % point_number
    if (start_index < finish_index):
        for i in range(start_index, finish_index, 1):
            curve_data.splines[0].points[i].select = True
    else:
        for i in range(start_index, point_number, 1):
            curve_data.splines[0].points[i].select = True
        for i in range(0, finish_index, 1):
            curve_data.splines[0].points[i].select = True
    # 平滑次数待优化
    for i in range(0, 3, 1):
        bpy.ops.curve.smooth()  # 平滑曲线
    bpy.ops.object.mode_set(mode='OBJECT')


def snaptoobject(curve_name):
    ''' 将指定的曲线对象吸附到最近的顶点上 '''
    name = bpy.context.scene.leftWindowObj
    # 获取曲线对象
    curve_object = bpy.data.objects[curve_name]
    # 获取目标物体
    target_object = bpy.data.objects[name + "MouldReset"]
    # 获取数据
    curve_data = curve_object.data

    # 将曲线的每个顶点吸附到目标物体的表面
    for spline in curve_data.splines:
        for point in spline.points:
            # 获取顶点原位置
            vertex_co = curve_object.matrix_world @ Vector(point.co[0:3])

            # 计算顶点在目标物体面上的 closest point
            _, closest_co, _, _ = target_object.closest_point_on_mesh(
                vertex_co)

            # 将顶点位置设置为 closest point
            point.co[0:3] = closest_co
            point.co[3] = 1


def snapselect(curve_name, index, number, target_object_name):
    ''' 将选中的曲线部分吸附到最近的顶点上 '''
    # 获取曲线对象
    curve_object = bpy.data.objects[curve_name]
    # 获取数据
    curve_data = curve_object.data
    target_object = bpy.data.objects[target_object_name]

    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    start_index = (index - number + point_number) % point_number
    finish_index = (index + number + point_number) % point_number
    if (start_index < finish_index):
        for i in range(start_index, finish_index, 1):
            point = curve_data.splines[0].points[i]
            vertex_co = curve_object.matrix_world @ Vector(point.co[0:3])
            # 计算顶点在目标物体面上的 closest point
            _, closest_co, _, _ = target_object.closest_point_on_mesh(
                vertex_co)

            # 将顶点位置设置为 closest point
            point.co[0:3] = closest_co
            point.co[3] = 1
    else:
        for i in range(start_index, point_number, 1):
            point = curve_data.splines[0].points[i]
            vertex_co = curve_object.matrix_world @ Vector(point.co[0:3])
            # 计算顶点在目标物体面上的 closest point
            _, closest_co, _, _ = target_object.closest_point_on_mesh(
                vertex_co)

            # 将顶点位置设置为 closest point
            point.co[0:3] = closest_co
            point.co[3] = 1
        for i in range(0, finish_index, 1):
            point = curve_data.splines[0].points[i]
            vertex_co = curve_object.matrix_world @ Vector(point.co[0:3])
            # 计算顶点在目标物体面上的 closest point
            _, closest_co, _, _ = target_object.closest_point_on_mesh(
                vertex_co)

            # 将顶点位置设置为 closest point
            point.co[0:3] = closest_co
            point.co[3] = 1

    colorcurve(curve_name, index, number)


def copy_select_curve(curve_name):
    ''' 复制曲线数据 '''
    name = bpy.context.scene.leftWindowObj
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = name + 'selectcurve'
    # 创建一个新的曲线对象来存储复制的数据
    # if bpy.data.objects.get(new_name) != None:
    #     return False
    new_curve = bpy.data.curves.new(new_name, 'CURVE')
    new_curve.dimensions = '3D'
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)
    if name == '右耳':
        moveToRight(new_obj)
    elif name == '左耳':
        moveToLeft(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True
        new_spline.points.add(len(spline.points) - 1)
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def copy_color_curve(curve_name):
    ''' 复制曲线数据 '''
    name = bpy.context.scene.leftWindowObj
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = name + 'colorcurve'
    # 创建一个新的曲线对象来存储复制的数据
    new_curve = bpy.data.curves.new(new_name, 'CURVE')
    new_curve.dimensions = '3D'
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)
    if name == '右耳':
        moveToRight(new_obj)
    elif name == '左耳':
        moveToLeft(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True
        new_spline.points.add(len(spline.points) - 1)
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def changearea(curve_name, index, number, depth):
    name = bpy.context.scene.leftWindowObj
    select_name = name + 'selectcurve'
    if bpy.data.objects.get(select_name) != None:
        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects[name + 'dragcurve'], do_unlink=True)
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    copy_select_curve(curve_name)  # 复制一份数据用于分离
    curve_obj = bpy.data.objects[select_name]
    bpy.context.view_layer.objects.active = curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')

    start_index = (index - number + point_number) % point_number
    finish_index = (index + number + point_number) % point_number
    if (start_index < finish_index):
        for i in range(start_index, finish_index, 1):
            curve_obj.data.splines[0].points[i].select = True
    else:
        for i in range(start_index, point_number, 1):
            curve_obj.data.splines[0].points[i].select = True
        for i in range(0, finish_index, 1):
            curve_obj.data.splines[0].points[i].select = True

    bpy.ops.curve.separate()  # 分离要进行拖拽的点
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects[select_name].hide_set(True)
    copy_name = select_name + '.001'
    for object in bpy.data.objects:  # 改名
        if object.name == copy_name:
            object.name = name + 'dragcurve'
            break

    bpy.data.objects[name + 'dragcurve'].data.materials.clear()  # 清除材质
    newColor('green', 0, 1, 0, 1, 1)
    bpy.data.objects[name + 'dragcurve'].data.materials.append(bpy.data.materials['green'])
    if name == '右耳':
        moveToRight(bpy.data.objects[name + 'dragcurve'])
    elif name == '左耳':
        moveToLeft(bpy.data.objects[name + 'dragcurve'])
    bpy.data.objects[name + 'dragcurve'].data.bevel_depth = depth


def selectcurve(curve_name, depth, index, number):
    ''' 选择拖拽曲线对象 '''
    name = bpy.context.scene.leftWindowObj
    select_name = name + 'selectcurve'
    if bpy.data.objects.get(select_name) != None:
        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects[name + 'dragcurve'], do_unlink=True)
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    copy_select_curve(curve_name)  # 复制一份数据用于分离
    curve_obj = bpy.data.objects[select_name]
    bpy.context.view_layer.objects.active = curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')

    start_index = (index - number + point_number) % point_number
    finish_index = (index + number + point_number) % point_number
    if (start_index < finish_index):
        for i in range(start_index, finish_index, 1):
            curve_obj.data.splines[0].points[i].select = True
    else:
        for i in range(start_index, point_number, 1):
            curve_obj.data.splines[0].points[i].select = True
        for i in range(0, finish_index, 1):
            curve_obj.data.splines[0].points[i].select = True

    bpy.ops.curve.separate()  # 分离要进行拖拽的点
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects[select_name].hide_set(True)
    copy_name = select_name + '.001'
    for object in bpy.data.objects:  # 改名
        if object.name == copy_name:
            object.name = name + 'dragcurve'
            break

    bpy.data.objects[name + 'dragcurve'].data.materials.clear()  # 清除材质
    newColor('green', 0, 1, 0, 1, 1)
    bpy.data.objects[name + 'dragcurve'].data.materials.append(bpy.data.materials['green'])
    if name == '右耳':
        moveToRight(bpy.data.objects[name + 'dragcurve'])
    elif name == '左耳':
        moveToLeft(bpy.data.objects[name + 'dragcurve'])
    bpy.data.objects[name + 'dragcurve'].data.bevel_depth = depth


def colorcurve(curve_name, index, number):
    ''' 移动时将移动的部分标绿 '''
    name = bpy.context.scene.leftWindowObj
    if bpy.data.objects.get(name + 'colorcurve') != None:
        bpy.data.objects.remove(bpy.data.objects[name + 'colorcurve'], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects[name + 'coloredcurve'], do_unlink=True)
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    copy_color_curve(curve_name)  # 复制一份数据用于分离
    curve_obj = bpy.data.objects[name + 'colorcurve']
    bpy.context.view_layer.objects.active = curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')

    start_index = (index - number + point_number) % point_number
    finish_index = (index + number + point_number) % point_number
    if (start_index < finish_index):
        for i in range(start_index, finish_index, 1):
            curve_obj.data.splines[0].points[i].select = True
    else:
        for i in range(start_index, point_number, 1):
            curve_obj.data.splines[0].points[i].select = True
        for i in range(0, finish_index, 1):
            curve_obj.data.splines[0].points[i].select = True

    bpy.ops.curve.separate()  # 分离要进行拖拽的点
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects[name + 'colorcurve'].hide_set(True)
    copy_name = name + 'colorcurve' + '.001'
    for object in bpy.data.objects:  # 改名
        if object.name == copy_name:
            object.name = name + 'coloredcurve'
            break

    bpy.data.objects[name + 'coloredcurve'].data.materials.clear()  # 清除材质
    newColor('green', 0, 1, 0, 1, 1)
    bpy.data.objects[name + 'coloredcurve'].data.materials.append(bpy.data.materials['green'])
    if name == '右耳':
        moveToRight(bpy.data.objects[name + 'coloredcurve'])
    elif name == '左耳':
        moveToLeft(bpy.data.objects[name + 'coloredcurve'])
    bpy.data.objects[name + 'coloredcurve'].data.bevel_depth = 0.18


def movecurve(co, initial_co, curve_name, index, number):
    curve_obj = bpy.data.objects[curve_name]
    bpy.context.view_layer.objects.active = curve_obj
    curve_data = curve_obj.data
    dis = co - initial_co  # 距离向量
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    # start_index = (index - number + point_number) % point_number
    # finish_index = (index + number + point_number) % point_number
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    for i in range(index - number + 1, index + number - 1):
        insert_index = (i + point_number) % point_number
        point = curve_data.splines[0].points[insert_index]
        vector_co = Vector(point.co[0:3]) + dis * disfunc(abs(i - index), number)
        point.co[0:3] = vector_co[0:3]
        point.co[3] = 1
        if i != index or i != index + 1 or i != index - 1:
            curve_data.splines[0].points[insert_index].select = True

    bpy.ops.curve.smooth()
    bpy.ops.object.mode_set(mode='OBJECT')


def get_co(curve_name, index):
    curve_obj = bpy.data.objects[curve_name]
    curve_data = curve_obj.data
    return Vector(curve_data.splines[0].points[index].co[0:3])


def get_len(start_index, finish_index, point_number):
    if (start_index < finish_index):
        return (int((finish_index - start_index + 1) / 2), int((start_index + finish_index) / 2))
    else:
        curve_number = int(point_number - start_index + finish_index + 1) / 2
        mid_index = (start_index + curve_number) % point_number
        return (curve_number, mid_index)


def disfunc(x, y):
    out = round(x / y, 2)
    return round(sqrt(1 - out), 2)


def join_dragcurve(curve_name, depth, index, number):
    ''' 合并拖拽或平滑后的曲线 '''
    name = bpy.context.scene.leftWindowObj
    # 获取两条曲线对象
    curve_obj1 = bpy.data.objects[curve_name]
    curve_obj2 = bpy.data.objects[name + 'dragcurve']

    # 获取两条曲线的曲线数据
    curve_data1 = curve_obj1.data
    curve_data2 = curve_obj2.data

    # 创建一个新的曲线对象
    new_curve_data = bpy.data.curves.new(
        name=name + "newdragcurve", type='CURVE')
    new_curve_obj = bpy.data.objects.new(
        name=name + "newdragcurve", object_data=new_curve_data)

    # 将新的曲线对象添加到场景中
    bpy.context.collection.objects.link(new_curve_obj)
    if name == '右耳':
        moveToRight(new_curve_obj)
    elif name == '左耳':
        moveToLeft(new_curve_obj)

    # 获取新曲线对象的曲线数据
    new_curve_data = new_curve_obj.data

    # 合并两条曲线的点集
    new_curve_data.splines.clear()
    new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
    point_number = len(curve_data1.splines[0].points) + len(
        curve_data2.splines[0].points) - number * 2 - 1
    length = len(curve_data2.splines[0].points)  # length为第二条曲线的长度
    new_spline.points.add(point_number)
    new_spline.use_cyclic_u = True
    new_spline.use_smooth = True

    # 将第一条曲线在初始起点前的点复制到新曲线
    for i, point in enumerate(curve_data1.splines[0].points):
        if i == index - number:
            break
        new_spline.points[i].co = point.co

    # 将第二条曲线的点复制到新曲线
    for i, point in enumerate(curve_data2.splines[0].points):
        new_spline.points[i + index - number].co = point.co

    # 将第一条曲线在结束点之后的点复制到新曲线
    for i, point in enumerate(curve_data1.splines[0].points):
        if i >= index + number:
            new_spline.points[i + length - 2 * number].co = point.co

    bpy.data.objects.remove(curve_obj1, do_unlink=True)
    bpy.data.objects.remove(curve_obj2, do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects[name + 'selectcurve'], do_unlink=True)
    new_curve_obj.name = curve_name

    bpy.context.view_layer.objects.active = new_curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    new_curve_obj.select_set(state=True)
    new_curve_obj.data.materials.clear()
    new_curve_obj.data.materials.append(bpy.data.materials['blue'])
    new_curve_obj.data.bevel_depth = depth
    new_curve_obj.data.dimensions = '3D'


def start_curve(color_mode=0):
    """ 在点加蓝线初始只有一个点时在点击的位置生成圆球 """
    name = bpy.context.scene.leftWindowObj
    curve_obj = bpy.data.objects.get(name + "point")
    # 先在点加位置添加一个新点
    first_co = curve_obj.data.splines[0].points[0].co[0:3]

    mesh = bpy.data.meshes.new(name + "create_mould_sphere")
    obj = bpy.data.objects.new(name + "create_mould_sphere", mesh)
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
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, radius=radius)
    bm.to_mesh(me)
    bm.free()
    obj.location = first_co
    if color_mode == 0:
        newColor('red', 1, 0, 0, 1, 1)
        obj.data.materials.append(bpy.data.materials['red'])
    else:
        newColor('yellow', 1, 1, 0, 1, 1)
        obj.data.materials.append(bpy.data.materials['yellow'])


class PointCut(bpy.types.Operator):  # 这里切割外型
    bl_idname = "object.pointcut"
    bl_label = "3D Model"

    def modal(self, context, event):
        global is_cut_finish
        cut_success = True
        if not is_cut_finish:
            is_cut_finish = True
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    # print("软耳模切割")
                    pass
                elif mould_type == "OP2":
                    # print("硬耳膜切割")
                    pass
            except:
                print("切割出错")
                cut_success = False
            if cut_success:
                global is_fill_finish
                is_fill_finish = False
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class PointFill(bpy.types.Operator):  # 这里填充
    bl_idname = "object.pointfill"
    bl_label = "3D Model"

    def modal(self, context, event):
        global is_fill_finish
        fill_success = True
        name = bpy.context.scene.leftWindowObj
        if not is_fill_finish:
            is_fill_finish = True
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    print("软耳模填充")
                    soft_eardrum()
                    set_finish(False)
                elif mould_type == "OP2":
                    print("硬耳模填充")
                    hard_bottom_fill()
                elif mould_type == "OP3":
                    print("常规外壳底部桥接")
                    bridge_and_refill()
                    set_shell_modal_finish(False)
                elif mould_type == "OP4":
                    print("框架式耳膜挖洞与填充")
                    re_dig_hole()
                    # 之前版本：挖洞后上下边界桥接补面
                    # fill_closest_point()
                    soft_eardrum()
                    set_finish(False)

                if name == "右耳":
                    bpy.data.objects[name].data.materials.clear()
                    bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowR"])
                elif name == "左耳":
                    bpy.data.objects[name].data.materials.clear()
                    bpy.data.objects[name].data.materials.append(bpy.data.materials["YellowL"])
            except:
                print("填充失败")
                fill_success = False
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    reset_to_after_cut()
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                elif mould_type == "OP2":
                    # 回退到补面前的状态
                    recover_before_fill()
                    # 将选择模式改回点选择
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                elif mould_type == "OP3":
                    reset_after_bottom_curve_change()
                    # 将选择模式改回点选择
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                elif mould_type == "OP4":
                    # recover_to_dig()
                    reset_to_after_cut()
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')

                if bpy.data.materials.get("error_yellow") == None:
                    mat = newColor("error_yellow", 1, 1, 0, 0, 1)
                    mat.use_backface_culling = False
                bpy.data.objects[name].data.materials.clear()
                bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class TEST_OT_addcurve(bpy.types.Operator):
    bl_idname = "object.addcurve"
    bl_label = "addcurve"
    bl_description = "双击蓝线改变蓝线形态"

    __index_initial = None
    __index_finish = None
    __curve_name = ''
    __mesh_name = ''
    __depth = None
    __mode = 0

    def addcurve(self, context, event):
        global last_co
        global idx_list
        global snap_object_name

        mujudict = MuJudict().get_dic_name()
        op_cls = TEST_OT_addcurve
        name = bpy.context.scene.leftWindowObj
        neiBianJiXianCur = None
        if name == '右耳':
            neiBianJiXianCur = bpy.context.scene.neiBianJiXianR
        elif name == '左耳':
            neiBianJiXianCur = bpy.context.scene.neiBianJiXianL
        if co_on_object(mujudict, context, event) == -1:  # 双击位置不在曲线上
            # 框架式耳膜挖洞
            if neiBianJiXianCur and bpy.context.scene.muJuTypeEnum == 'OP4':
                if cal_co(name, context, event) != -1:  # 双击位置在耳模上
                    co = cal_co(name, context, event)
                    if bpy.data.objects.get(name + 'point') == None:
                        op_cls.__mode = 1
                        last_co = co
                        idx_list = [0]
                        snap_object_name = name + "MouldReset"
                        # 创建一个新的曲线对象
                        new_curve_name = name + 'point'
                        op_cls.__curve_name = new_curve_name
                        new_curve_data = bpy.data.curves.new(
                            name=new_curve_name, type='CURVE')
                        new_curve_obj = bpy.data.objects.new(
                            name=new_curve_name, object_data=new_curve_data)
                        new_curve_data.bevel_depth = 0.18  # 管道孔径
                        new_curve_data.dimensions = '3D'
                        bpy.context.collection.objects.link(new_curve_obj)
                        if name == '右耳':
                            moveToRight(new_curve_obj)
                        elif name == '左耳':
                            moveToLeft(new_curve_obj)
                        new_curve_data.materials.append(bpy.data.materials['blue'])
                        bpy.ops.object.select_all(action='DESELECT')
                        new_curve_obj.select_set(state=True)

                        new_curve_data = new_curve_obj.data
                        new_curve_data.splines.clear()
                        new_spline = new_curve_data.splines.new(type='NURBS')
                        new_spline.use_smooth = True
                        new_spline.order_u = 2

                        new_curve_data.splines[0].points[0].co[0:3] = co
                        new_curve_data.splines[0].points[0].co[3] = 1

                        start_curve(color_mode=1)

                        if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                            if bpy.data.objects.get(name + "Torus") is not None:
                                bpy.data.objects[name + "Torus"].hide_set(True)
                            if bpy.data.objects.get(name + "UpperTorus") is not None:
                                bpy.data.objects[name + "UpperTorus"].hide_set(True)

                        elif bpy.context.scene.muJuTypeEnum == 'OP3':
                            if bpy.data.objects.get(name + "BottomTorus") is not None:
                                bpy.data.objects[name + "BottomTorus"].hide_set(True)
                            if bpy.data.objects.get(name + "MiddleTorus") is not None:
                                if name == "右耳":
                                    kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                                elif name == "左耳":
                                    kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                                if kongQiangMianBanType == 'OP1':
                                    bpy.data.objects[name + "MiddleTorus"].hide_set(True)
                            if bpy.data.objects.get(name + "TopTorus") is not None:
                                bpy.data.objects[name + "TopTorus"].hide_set(True)

                    # 双击位置距离新增的曲线起始点小于1,闭合曲线
                    elif (co - Vector(bpy.data.objects[op_cls.__curve_name].data.splines[0].points[0].co[0:3])).length < 1 \
                            and len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points) > 2 and op_cls.__mode == 1:
                        curve_obj = bpy.data.objects[op_cls.__curve_name]
                        curve_obj.data.splines[0].use_cyclic_u = True
                        # idx = len(curve_obj.data.splines[0].points) - 1
                        # bpy.ops.object.select_all(action='DESELECT')
                        # bpy.context.view_layer.objects.active = curve_obj
                        # curve_obj.select_set(True)
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.curve.select_all(action='DESELECT')
                        # curve_obj.data.splines[0].points[idx].select = True
                        # bpy.ops.curve.delete(type='VERT')
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        spline = curve_obj.data.splines[0]
                        if len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points) < 4:
                            spline.order_u = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                        else:
                            spline.order_u = 4
                        # 重新切割
                        local_curve_name = MuJudict().update_dic()
                        curve_obj.name = local_curve_name
                        if re.match(r'右耳', local_curve_name):
                            local_mesh_name = name + 'mesh' + local_curve_name.replace('右耳', '')
                        elif re.match(r'左耳', local_curve_name):
                            local_mesh_name = name + 'mesh' + local_curve_name.replace('左耳', '')
                        resample_number = len(bpy.data.objects[local_curve_name].data.splines[0].points)
                        resample_curve(resample_number, local_curve_name)
                        if bpy.data.objects.get(name + 'create_mould_sphere') != None:
                            bpy.data.objects.remove(bpy.data.objects[name + 'create_mould_sphere'], do_unlink=True)
                        # convert_to_mesh(local_curve_name, local_mesh_name, 0.18)
                        update_cut(local_curve_name, local_mesh_name, 0.18)
                        bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")

                        if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                            if bpy.data.objects.get(name + "Torus") is not None:
                                bpy.data.objects[name + "Torus"].hide_set(False)
                            if bpy.data.objects.get(name + "UpperTorus") is not None:
                                bpy.data.objects[name + "UpperTorus"].hide_set(False)

                        elif bpy.context.scene.muJuTypeEnum == 'OP3':
                            if bpy.data.objects.get(name + "BottomTorus") is not None:
                                bpy.data.objects[name + "BottomTorus"].hide_set(False)
                            if bpy.data.objects.get(name + "MiddleTorus") is not None:
                                if name == "右耳":
                                    kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                                elif name == "左耳":
                                    kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                                if kongQiangMianBanType == 'OP1':
                                    bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                            if bpy.data.objects.get(name + "TopTorus") is not None:
                                bpy.data.objects[name + "TopTorus"].hide_set(False)

                    else:
                        pass

        elif co_on_object(mujudict, context, event) == 0:  # 重置后没有曲线
            if cal_co(name + "batteryPlaneSnapCurve", context, event) != -1:  # 双击位置在电池仓的吸附平面上
                co = cal_co(name + "batteryPlaneSnapCurve", context, event)
                if bpy.data.objects.get(name + 'point') == None:
                    op_cls.__mode = 2
                    last_co = co
                    idx_list = [0]
                    snap_object_name = name + "batteryPlaneSnapCurve"
                    # 创建一个新的曲线对象
                    new_curve_name = name + 'point'
                    op_cls.__curve_name = new_curve_name
                    new_curve_data = bpy.data.curves.new(
                        name=new_curve_name, type='CURVE')
                    new_curve_obj = bpy.data.objects.new(
                        name=new_curve_name, object_data=new_curve_data)
                    new_curve_data.bevel_depth = 0.18  # 管道孔径
                    new_curve_data.dimensions = '3D'
                    bpy.context.collection.objects.link(new_curve_obj)
                    if name == '右耳':
                        moveToRight(new_curve_obj)
                    elif name == '左耳':
                        moveToLeft(new_curve_obj)
                    new_curve_data.materials.append(bpy.data.materials['blue'])
                    bpy.ops.object.select_all(action='DESELECT')
                    new_curve_obj.select_set(state=True)

                    new_curve_data = new_curve_obj.data
                    new_curve_data.splines.clear()
                    new_spline = new_curve_data.splines.new(type='NURBS')
                    new_spline.use_smooth = True
                    new_spline.order_u = 2

                    new_curve_data.splines[0].points[0].co[0:3] = co
                    new_curve_data.splines[0].points[0].co[3] = 1

                    start_curve()

                    if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                        if bpy.data.objects.get(name + "Torus") is not None:
                            bpy.data.objects[name + "Torus"].hide_set(True)
                        if bpy.data.objects.get(name + "UpperTorus") is not None:
                            bpy.data.objects[name + "UpperTorus"].hide_set(True)

                    elif bpy.context.scene.muJuTypeEnum == 'OP3':
                        if bpy.data.objects.get(name + "BottomTorus") is not None:
                            bpy.data.objects[name + "BottomTorus"].hide_set(True)
                        if bpy.data.objects.get(name + "MiddleTorus") is not None:
                            if name == "右耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                            elif name == "左耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                            if kongQiangMianBanType == 'OP1':
                                bpy.data.objects[name + "MiddleTorus"].hide_set(True)
                        if bpy.data.objects.get(name + "TopTorus") is not None:
                            bpy.data.objects[name + "TopTorus"].hide_set(True)

                elif (co - Vector(bpy.data.objects[op_cls.__curve_name].data.splines[0].points[0].co[0:3])).length < 1 \
                        and len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points) > 2 and op_cls.__mode == 2:
                    curve_obj = bpy.data.objects[op_cls.__curve_name]
                    curve_obj.data.splines[0].use_cyclic_u = True
                    # idx = len(curve_obj.data.splines[0].points) - 1
                    # bpy.ops.object.select_all(action='DESELECT')
                    # bpy.context.view_layer.objects.active = curve_obj
                    # curve_obj.select_set(True)
                    # bpy.ops.object.mode_set(mode='EDIT')
                    # bpy.ops.curve.select_all(action='DESELECT')
                    # curve_obj.data.splines[0].points[idx].select = True
                    # bpy.ops.curve.delete(type='VERT')
                    # bpy.ops.object.mode_set(mode='OBJECT')
                    if bpy.data.objects.get(name + 'create_mould_sphere') != None:
                        bpy.data.objects.remove(bpy.data.objects[name + 'create_mould_sphere'], do_unlink=True)
                    # 重新切割，根据不同的模块更改不同的名字
                    if bpy.context.scene.muJuTypeEnum == 'OP3':
                        curve_obj.name = name + 'PlaneBorderCurve'
                        battery_obj = bpy.data.objects.get(name + "shellBattery")
                        child_of_constraint = curve_obj.constraints.new(type='CHILD_OF')  # 设置为为电池的子物体
                        child_of_constraint.target = battery_obj
                        mesh_name = name + 'meshPlaneBorderCurve'
                        update_cut(curve_obj.name, mesh_name, 0.18)

                    bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")

                    if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                        if bpy.data.objects.get(name + "Torus") is not None:
                            bpy.data.objects[name + "Torus"].hide_set(False)
                        if bpy.data.objects.get(name + "UpperTorus") is not None:
                            bpy.data.objects[name + "UpperTorus"].hide_set(False)

                    elif bpy.context.scene.muJuTypeEnum == 'OP3':
                        if bpy.data.objects.get(name + "BottomTorus") is not None:
                            bpy.data.objects[name + "BottomTorus"].hide_set(False)
                        if bpy.data.objects.get(name + "MiddleTorus") is not None:
                            if name == "右耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                            elif name == "左耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                            if kongQiangMianBanType == 'OP1':
                                bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                        if bpy.data.objects.get(name + "TopTorus") is not None:
                            bpy.data.objects[name + "TopTorus"].hide_set(False)

                else:
                    pass

            elif cal_co(name, context, event) != -1 and bpy.context.scene.muJuTypeEnum != 'OP3':  # 双击位置在耳模上
                co = cal_co(name, context, event)
                if bpy.data.objects.get(name + 'point') == None:
                    op_cls.__mode = 2
                    last_co = co
                    idx_list = [0]
                    snap_object_name = name + "MouldReset"
                    # 创建一个新的曲线对象
                    new_curve_name = name + 'point'
                    op_cls.__curve_name = new_curve_name
                    new_curve_data = bpy.data.curves.new(
                        name=new_curve_name, type='CURVE')
                    new_curve_obj = bpy.data.objects.new(
                        name=new_curve_name, object_data=new_curve_data)
                    new_curve_data.bevel_depth = 0.18  # 管道孔径
                    new_curve_data.dimensions = '3D'
                    bpy.context.collection.objects.link(new_curve_obj)
                    if name == '右耳':
                        moveToRight(new_curve_obj)
                    elif name == '左耳':
                        moveToLeft(new_curve_obj)
                    new_curve_data.materials.append(bpy.data.materials['blue'])
                    bpy.ops.object.select_all(action='DESELECT')
                    new_curve_obj.select_set(state=True)

                    new_curve_data = new_curve_obj.data
                    new_curve_data.splines.clear()
                    new_spline = new_curve_data.splines.new(type='NURBS')
                    new_spline.use_smooth = True
                    new_spline.order_u = 2

                    new_curve_data.splines[0].points[0].co[0:3] = co
                    new_curve_data.splines[0].points[0].co[3] = 1

                    start_curve()

                    if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                        if bpy.data.objects.get(name + "Torus") is not None:
                            bpy.data.objects[name + "Torus"].hide_set(True)
                        if bpy.data.objects.get(name + "UpperTorus") is not None:
                            bpy.data.objects[name + "UpperTorus"].hide_set(True)

                    elif bpy.context.scene.muJuTypeEnum == 'OP3':
                        if bpy.data.objects.get(name + "BottomTorus") is not None:
                            bpy.data.objects[name + "BottomTorus"].hide_set(True)
                        if bpy.data.objects.get(name + "MiddleTorus") is not None:
                            if name == "右耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                            elif name == "左耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                            if kongQiangMianBanType == 'OP1':
                                bpy.data.objects[name + "MiddleTorus"].hide_set(True)
                        if bpy.data.objects.get(name + "TopTorus") is not None:
                            bpy.data.objects[name + "TopTorus"].hide_set(True)

                # 双击位置距离新增的曲线起始点小于1,闭合曲线
                elif (co - Vector(bpy.data.objects[op_cls.__curve_name].data.splines[0].points[0].co[0:3])).length < 1 \
                        and len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points) > 2 and op_cls.__mode == 2:
                    curve_obj = bpy.data.objects[op_cls.__curve_name]
                    curve_obj.data.splines[0].use_cyclic_u = True
                    # idx = len(curve_obj.data.splines[0].points) - 1
                    # bpy.ops.object.select_all(action='DESELECT')
                    # bpy.context.view_layer.objects.active = curve_obj
                    # curve_obj.select_set(True)
                    # bpy.ops.object.mode_set(mode='EDIT')
                    # bpy.ops.curve.select_all(action='DESELECT')
                    # curve_obj.data.splines[0].points[idx].select = True
                    # bpy.ops.curve.delete(type='VERT')
                    # bpy.ops.object.mode_set(mode='OBJECT')
                    if bpy.data.objects.get(name + 'create_mould_sphere') != None:
                        bpy.data.objects.remove(bpy.data.objects[name + 'create_mould_sphere'], do_unlink=True)
                    # 重新切割，根据不同的模块更改不同的名字
                    if bpy.context.scene.muJuTypeEnum == 'OP2':
                        curve_obj.name = name + 'BottomRingBorderR'
                        mesh_name = name + 'meshBottomRingBorderR'
                        update_cut(curve_obj.name, mesh_name, 0.18)
                    elif bpy.context.scene.muJuTypeEnum == 'OP1':
                        curve_obj.name = name + 'BottomRingBorderR'
                        mesh_name = name + 'meshBottomRingBorderR'
                        update_cut(curve_obj.name, mesh_name, 0.18)
                    elif bpy.context.scene.muJuTypeEnum == 'OP4':
                        if bpy.data.objects.get(name + 'BottomRingBorderR') == None:
                            curve_obj.name = name + 'BottomRingBorderR'
                            mesh_name = name + 'meshBottomRingBorderR'
                            update_cut(curve_obj.name, mesh_name, 0.18)
                        else:
                            curve_obj.name = name + 'HoleBorderCurve1'
                            mesh_name = name + 'meshHoleBorderCurve1'
                            update_cut(curve_obj.name, mesh_name, 0.18)

                    bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")

                    if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                        if bpy.data.objects.get(name + "Torus") is not None:
                            bpy.data.objects[name + "Torus"].hide_set(False)
                        if bpy.data.objects.get(name + "UpperTorus") is not None:
                            bpy.data.objects[name + "UpperTorus"].hide_set(False)

                    elif bpy.context.scene.muJuTypeEnum == 'OP3':
                        if bpy.data.objects.get(name + "BottomTorus") is not None:
                            bpy.data.objects[name + "BottomTorus"].hide_set(False)
                        if bpy.data.objects.get(name + "MiddleTorus") is not None:
                            if name == "右耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                            elif name == "左耳":
                                kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                            if kongQiangMianBanType == 'OP1':
                                bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                        if bpy.data.objects.get(name + "TopTorus") is not None:
                            bpy.data.objects[name + "TopTorus"].hide_set(False)

                else:
                    pass

        else:
            if bpy.data.objects.get(name + 'point') == None:  # 双击在原有曲线上
                # if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                #     set_finish(True)
                op_cls.__mode = 3
                co, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
                last_co = co
                idx_list = [0]
                op_cls.__curve_name = curve_list[0]
                op_cls.__depth = curve_list[1]
                op_cls.__index_initial = select_nearest_point(op_cls.__curve_name, co)
                if op_cls.__curve_name == name + "PlaneBorderCurve":
                    snap_object_name = name + "batteryPlaneSnapCurve"
                else:
                    snap_object_name = name + "MouldReset"
                # curve_obj = bpy.data.objects[op_cls.__curve_name]
                # bpy.context.view_layer.objects.active = curve_obj
                # bpy.ops.object.select_all(action='DESELECT')
                # curve_obj.select_set(state=True)
                # bpy.ops.object.mode_set(mode='EDIT')
                # bpy.ops.curve.select_all(action='DESELECT')
                # curve_obj.data.splines[0].points[op_cls.__index_initial].select = True
                # bpy.ops.curve.separate()  # 分离将要进行操作的点
                # bpy.ops.object.mode_set(mode='OBJECT')
                # for object in bpy.data.objects:  # 改名
                #     copy_name = op_cls.__curve_name + '.001'
                #     if object.name == copy_name:
                #         object.name = 'point'
                #         break
                # bpy.context.view_layer.objects.active = bpy.data.objects['point']
                # bpy.ops.object.select_all(action='DESELECT')
                # bpy.data.objects['point'].select_set(state=True)

                # bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式进行操作
                # bpy.ops.curve.select_all(action='SELECT')
                # bpy.context.object.data.bevel_depth = op_cls.__depth  # 设置倒角深度
                # bpy.data.objects['point'].data.materials.append(
                #     bpy.data.materials['blue'])

                # 创建一个新的曲线对象
                new_curve_data = bpy.data.curves.new(
                    name=name + 'point', type='CURVE')
                new_curve_obj = bpy.data.objects.new(
                    name=name + 'point', object_data=new_curve_data)
                new_curve_data.bevel_depth = op_cls.__depth  # 管道孔径
                new_curve_data.dimensions = '3D'
                bpy.context.collection.objects.link(new_curve_obj)
                if name == '右耳':
                    moveToRight(new_curve_obj)
                elif name == '左耳':
                    moveToLeft(new_curve_obj)
                new_curve_data.materials.append(bpy.data.materials['blue'])
                new_curve_data.splines.clear()
                new_spline = new_curve_data.splines.new(type='NURBS')
                new_spline.use_smooth = True
                new_spline.order_u = 2
                new_curve_data.splines[0].points[0].co[0:3] = co
                new_curve_data.splines[0].points[0].co[3] = 1

                start_curve()

                if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                    if bpy.data.objects.get(name + "Torus") is not None:
                        bpy.data.objects[name + "Torus"].hide_set(True)
                    if bpy.data.objects.get(name + "UpperTorus") is not None:
                        bpy.data.objects[name + "UpperTorus"].hide_set(True)

                elif bpy.context.scene.muJuTypeEnum == 'OP3':
                    if bpy.data.objects.get(name + "BottomTorus") is not None:
                        bpy.data.objects[name + "BottomTorus"].hide_set(True)
                    if bpy.data.objects.get(name + "MiddleTorus") is not None:
                        if name == "右耳":
                            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                        elif name == "左耳":
                            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                        if kongQiangMianBanType == 'OP1':
                            bpy.data.objects[name + "MiddleTorus"].hide_set(True)
                    if bpy.data.objects.get(name + "TopTorus") is not None:
                        bpy.data.objects[name + "TopTorus"].hide_set(True)

            else:    # 存在曲线，双击确认完成
                # print("起始位置的下标是", op_cls.__index_initial)
                if op_cls.__mesh_name == '' or op_cls.__mode != 3:
                    return
                if bpy.data.objects.get(name + 'create_mould_sphere') != None:
                    bpy.data.objects.remove(bpy.data.objects[name + 'create_mould_sphere'], do_unlink=True)
                co, _, _ = co_on_object(mujudict, context, event)
                op_cls.__index_finish = select_nearest_point(op_cls.__curve_name, co)
                # print("结束的下标是", op_cls.__index_finish)
                join_object(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth, op_cls.__index_initial,
                            op_cls.__index_finish)  # 合并曲线
                bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")
                # if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                #     set_finish(False)

                if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                    if bpy.data.objects.get(name + "Torus") is not None:
                        bpy.data.objects[name + "Torus"].hide_set(False)
                    if bpy.data.objects.get(name + "UpperTorus") is not None:
                        bpy.data.objects[name + "UpperTorus"].hide_set(False)

                elif bpy.context.scene.muJuTypeEnum == 'OP3':
                    if bpy.data.objects.get(name + "BottomTorus") is not None:
                        bpy.data.objects[name + "BottomTorus"].hide_set(False)
                    if bpy.data.objects.get(name + "MiddleTorus") is not None:
                        if name == "右耳":
                            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                        elif name == "左耳":
                            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                        if kongQiangMianBanType == 'OP1':
                            bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                    if bpy.data.objects.get(name + "TopTorus") is not None:
                        bpy.data.objects[name + "TopTorus"].hide_set(False)


    def invoke(self, context, event):
        newColor('blue', 0, 0, 1, 1, 1)
        self.addcurve(context, event)
        return {'FINISHED'}


class TEST_OT_qiehuan(bpy.types.Operator):
    bl_idname = "object.pointqiehuan"
    bl_label = "pointqiehuan"
    bl_description = "鼠标行为切换"

    __left_mouse_down = False
    __middle_mouse_down = False
    __right_mouse_down = False
    __add_point_mode = False
    __select_mode = True

    def invoke(self, context, event):  # 初始化
        global snap_object_name
        name = bpy.context.scene.leftWindowObj
        if bpy.context.scene.muJuTypeEnum != "OP3":
            snap_object_name = name + "MouldReset"
        op_cls = TEST_OT_qiehuan
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 19
        if not get_point_qiehuan_modal_start():
            set_point_qiehuan_modal_start(True)
            print('pointqiehuan invoke')
            context.window_manager.modal_handler_add(self)

        op_cls.__flag = False

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global snap_object_name
        op_cls = TEST_OT_qiehuan
        name = bpy.context.scene.leftWindowObj

        override1 = getOverride()
        area = override1['area']
        if bpy.context.screen.areas[0].spaces.active.context == 'SCENE':
            if bpy.context.scene.muJuTypeEnum == "OP3" and bpy.data.objects.get(name + "point") is None:
                return {'PASS_THROUGH'}

            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 19):

                if event.type == 'LEFTMOUSE':  # 监听左键
                    if event.value == 'PRESS':  # 按下
                        op_cls.__left_mouse_down = True
                    return {'PASS_THROUGH'}

                elif event.type == 'MIDDLEMOUSE':  # 监听左键
                    if event.value == 'PRESS':  # 按下
                        op_cls.__middle_mouse_down = False
                    return {'PASS_THROUGH'}

                elif event.type == 'RIGHTMOUSE':  # 监听左键
                    if event.value == 'PRESS':  # 按下
                        op_cls.__right_mouse_down = False
                    return {'PASS_THROUGH'}

                elif event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    elif op_cls.__middle_mouse_down:
                        op_cls.__middle_mouse_down = False
                    elif op_cls.__right_mouse_down:
                        op_cls.__right_mouse_down = False

                    if snap_object_name is not None and cal_co(snap_object_name, context, event) != -1:
                        if not (op_cls.__left_mouse_down or op_cls.__middle_mouse_down or op_cls.__right_mouse_down):
                            if not op_cls.__add_point_mode:
                                bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")
                                op_cls.__add_point_mode = True
                                op_cls.__select_mode = False

                    else:
                        if not (op_cls.__left_mouse_down or op_cls.__middle_mouse_down or op_cls.__right_mouse_down):
                            if not op_cls.__select_mode:
                                bpy.ops.object.select_all(action='DESELECT')
                                bpy.context.view_layer.objects.active = bpy.data.objects[name]
                                bpy.data.objects[name].select_set(True)
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                                op_cls.__add_point_mode = False
                                op_cls.__select_mode = True

                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 19 and bpy.context.scene.var in get_process_var_list("创建模具"):
                print('pointqiehuan finish')
                set_point_qiehuan_modal_start(False)
                return {'FINISHED'}

            else:
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                print('pointqiehuan finish')
                set_point_qiehuan_modal_start(False)
                if not get_shell_modal_start() and not get_soft_modal_start():
                    set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class TEST_OT_addpoint(bpy.types.Operator):
    bl_idname = "object.addpoint"
    bl_label = "addpoint"
    bl_description = "单击左键添加控制点"

    def invoke(self, context, event):
        self.addpoint(context, event)
        return {'FINISHED'}

    def addpoint(self, context, event):
        global last_co
        global idx_list
        global snap_object_name
        add_curve_name = context.scene.leftWindowObj + 'point'
        if add_curve_name == None or bpy.data.objects.get(add_curve_name) == None or bpy.data.objects.get(snap_object_name) == None:
            return
        co = cal_co(snap_object_name, context, event)
        if co != -1 and bpy.data.objects.get(add_curve_name) != None:
            # if (co - Vector(bpy.data.objects[add_curve_name].data.splines[0].points[0].co[0:3])).length < 1:
            #     return
            curve_obj = bpy.data.objects.get(add_curve_name)
            # 先在点加位置添加一个新点
            spline = curve_obj.data.splines[0]
            spline.points.add(1)
            spline.points[-1].co = (co[0], co[1], co[2], 1)

            distance = (co - last_co).length
            if distance > 1:   # 点击之间的距离大于1就细分
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = curve_obj
                curve_obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                curve_obj.data.splines[0].points[-1].select = True
                curve_obj.data.splines[0].points[-2].select = True
                number = int(distance)   # 细分次数
                bpy.ops.curve.subdivide(number_cuts=number)

                # 将新细分出的点吸附到物体表面上
                new_length = len(curve_obj.data.splines[0].points)
                snap_object = bpy.data.objects[snap_object_name]
                for i in range(new_length - number - 1, new_length - 1):
                    point = curve_obj.data.splines[0].points[i]
                    # 计算顶点在目标物体面上的 closest point
                    _, closest_co, _, _ = snap_object.closest_point_on_mesh(
                        Vector(point.co[0:3]))
                    point.co[0:3] = closest_co
                idx_list.append(new_length - 1)
                last_co = co
                bpy.ops.object.mode_set(mode='OBJECT')

            else:
                idx_list.append(len(curve_obj.data.splines[0].points) - 1)
                last_co = co


class TEST_OT_deletepoint(bpy.types.Operator):
    bl_idname = "object.deletepoint"
    bl_label = "deletepoint"
    bl_description = "单击右键删除控制点"

    def invoke(self, context, event):
        self.deletepoint(context, event)
        return {'FINISHED'}

    def deletepoint(self, context, event):
        global last_co
        global idx_list
        global snap_object_name
        add_curve_name = context.scene.leftWindowObj + 'point'
        if add_curve_name == None or bpy.data.objects.get(add_curve_name) == None or bpy.data.objects.get(snap_object_name) == None:
            return
        co = cal_co(snap_object_name, context, event)
        if co != -1 and bpy.data.objects.get(add_curve_name) != None:
            list_len = len(idx_list)
            curve_obj = bpy.data.objects.get(add_curve_name)
            if list_len > 1:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = curve_obj
                curve_obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                last_point_idx = idx_list[-1]
                second_last_point_idx = idx_list[-2]
                for i in range(second_last_point_idx + 1, last_point_idx + 1, 1):
                    curve_obj.data.splines[0].points[i].select = True
                bpy.ops.curve.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                last_co = get_co(add_curve_name, idx_list[-2])
                idx_list = idx_list[:-1]

            # 删除最后一个控制点
            elif list_len == 1:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[add_curve_name]
                bpy.data.objects[add_curve_name].select_set(True)
                bpy.data.objects.remove(bpy.data.objects[add_curve_name], do_unlink=True)
                model_name = context.scene.leftWindowObj
                if bpy.data.objects.get(model_name + 'create_mould_sphere') != None:
                    bpy.data.objects.remove(bpy.data.objects[model_name + 'create_mould_sphere'], do_unlink=True)
                bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")

                name = bpy.context.scene.leftWindowObj
                if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                    if bpy.data.objects.get(name + "Torus") is not None:
                        bpy.data.objects[name + "Torus"].hide_set(False)
                    if bpy.data.objects.get(name + "UpperTorus") is not None:
                        bpy.data.objects[name + "UpperTorus"].hide_set(False)

                elif bpy.context.scene.muJuTypeEnum == 'OP3':
                    if bpy.data.objects.get(name + "BottomTorus") is not None:
                        bpy.data.objects[name + "BottomTorus"].hide_set(False)
                    if bpy.data.objects.get(name + "MiddleTorus") is not None:
                        if name == "右耳":
                            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                        elif name == "左耳":
                            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                        if kongQiangMianBanType == 'OP1':
                            bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                    if bpy.data.objects.get(name + "TopTorus") is not None:
                        bpy.data.objects[name + "TopTorus"].hide_set(False)

            else:
                pass


class TEST_OT_dragcurve(bpy.types.Operator):
    bl_idname = "object.dragcurve"
    bl_label = "dragcurve"
    bl_description = "移动鼠标拖拽曲线"

    __left_mouse_down = False
    __right_mouse_down = False
    __initial_mouse_x = None  # 点击鼠标左键的初始位置
    __initial_mouse_y = None
    __initial_mouse_x_right = None  # 点击鼠标右键的初始位置
    __initial_mouse_y_right = None
    __now_mouse_x_right = None  # 鼠标右键的现位置
    __now_mouse_y_right = None
    __is_moving = False
    __is_moving_right = False
    __is_modifier = False
    __is_modifier_right = False

    __prev_mouse_location_x = None
    __prev_mouse_location_y = None

    __curve_name = None
    __mesh_name = None
    __depth = None
    __initial_co = None
    __number = None
    __curve_length = None
    __index = None
    __snap_object_name = None

    def invoke(self, context, event):  # 初始化
        newColor('green', 0, 1, 0, 1, 1)
        newColor('blue', 0, 0, 1, 1, 1)
        op_cls = TEST_OT_dragcurve
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_mouse_x_right = None
        op_cls.__initial_mouse_y_right = None
        op_cls.__now_mouse_x_right = None
        op_cls.__now_mouse_y_right = None
        op_cls.__is_moving = False
        op_cls.__is_moving_right = False
        op_cls.__is_modifier = False
        # op_cls.__is_modifier_right = False

        # op_cls.__prev_mouse_location_x = None
        # op_cls.__prev_mouse_location_y = None

        op_cls.__curve_name = ''
        op_cls.__mesh_name = ''
        op_cls.__depth = None
        op_cls.__initial_co = None
        op_cls.__number = None
        op_cls.__curve_length = None
        op_cls.__index = None
        op_cls.__snap_object_name = None

        bpy.context.scene.var = 20
        if not get_drag_curve_modal_start():
            set_drag_curve_modal_start(True)
            context.window_manager.modal_handler_add(self)
            print('dragcurve invoke')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到公共鼠标行为

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TEST_OT_dragcurve
        mujudict = MuJudict().get_dic_name()
        name = bpy.context.scene.leftWindowObj
        override1 = getOverride()
        area = override1['area']
        if bpy.context.screen.areas[0].spaces.active.context == 'SCENE':
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 20):
                if co_on_object(mujudict, context, event) == -1 or co_on_object(mujudict, context, event) == 0:  # 鼠标不在曲线上时
                    if event.value == 'RELEASE':
                        if op_cls.__is_moving_right == True:  # 鼠标右键松开
                            op_cls.__right_mouse_down = False
                            op_cls.__initial_mouse_x_right = None
                            op_cls.__initial_mouse_y_right = None
                            op_cls.__now_mouse_x_right = None
                            op_cls.__now_mouse_y_right = None
                            op_cls.__is_moving_right = False
                            context.window.cursor_warp(event.mouse_prev_press_x, event.mouse_prev_press_y)
                        if op_cls.__is_moving == True:  # 鼠标左键松开
                            op_cls.__is_moving = False
                            op_cls.__left_mouse_down = False
                            op_cls.__initial_mouse_x = None
                            op_cls.__initial_mouse_y = None
                            if bpy.data.objects.get(name + 'colorcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'colorcurve'], do_unlink=True)  # 删除原有曲线
                            if bpy.data.objects.get(name + 'coloredcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'coloredcurve'], do_unlink=True)
                    if op_cls.__right_mouse_down == False:
                        if op_cls.__left_mouse_down == False and op_cls.__is_modifier == False:
                            if bpy.data.objects.get(name + 'selectcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'selectcurve'], do_unlink=True)  # 删除原有曲线
                            if bpy.data.objects.get(name + 'dragcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'dragcurve'], do_unlink=True)
                    if op_cls.__right_mouse_down == True:  # 鼠标右键按下
                        min_number = max(int(op_cls.__curve_length * 0.01), 3)
                        max_number = int(op_cls.__curve_length * 0.4)
                        # op_cls.__is_modifier_right = True
                        # 记录下第一次点击鼠标的位置
                        op_cls.__now_mouse_x_right = event.mouse_region_x
                        op_cls.__now_mouse_y_right = event.mouse_region_y
                        dis = int(((op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) ** 2 +
                                   (op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right) ** 2 ) ** 0.5 / 10)  # 鼠标移动的距离
                        if dis >= 1:
                            if op_cls.__now_mouse_y_right < op_cls.__initial_mouse_y_right:
                                dis *= -1  # 根据鼠标移动的方向确定是增大还是减小区域
                            op_cls.__number += dis  # 根据鼠标移动的距离扩大或缩小选区
                            if op_cls.__number < min_number:  # 防止选不到点弹出报错信息
                                op_cls.__number = min_number
                            if op_cls.__number > max_number:
                                op_cls.__number = max_number
                            changearea(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__depth)
                            op_cls.__initial_mouse_x_right = op_cls.__now_mouse_x_right  # 重新开始检测
                            op_cls.__initial_mouse_y_right = op_cls.__now_mouse_y_right
                    if op_cls.__left_mouse_down == True:  # 鼠标左键按下
                        co = cal_co(op_cls.__snap_object_name, context, event)
                        op_cls.__is_modifier = True
                        if co != -1:
                            if (co - op_cls.__initial_co).length > 0.1:
                                movecurve(co, op_cls.__initial_co, op_cls.__curve_name, op_cls.__index, op_cls.__number)
                                snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__snap_object_name)  # 将曲线吸附到物体上
                                op_cls.__initial_co = co
                    if op_cls.__left_mouse_down == False:
                        # 重新切割
                        if bpy.data.objects.get(name + 'selectcurve') == None and op_cls.__is_modifier == True:
                            # join_dragcurve(op_cls.__curve_name,op_cls.__depth)
                            update_cut(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                            bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                            if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                                if bpy.data.objects.get(name + "Torus") is not None:
                                    bpy.data.objects[name + "Torus"].hide_set(False)
                                if bpy.data.objects.get(name + "UpperTorus") is not None:
                                    bpy.data.objects[name + "UpperTorus"].hide_set(False)
                            elif bpy.context.scene.muJuTypeEnum == 'OP3':
                                if bpy.data.objects.get(name + "BottomTorus") is not None:
                                    bpy.data.objects[name + "BottomTorus"].hide_set(False)
                                if bpy.data.objects.get(name + "MiddleTorus") is not None:
                                    if name == "右耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                                    elif name == "左耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                                    if kongQiangMianBanType == 'OP1':
                                        bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                                if bpy.data.objects.get(name + "TopTorus") is not None:
                                    bpy.data.objects[name + "TopTorus"].hide_set(False)
                            op_cls.__is_modifier = False
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

                    return {'PASS_THROUGH'}

                else:  # 鼠标在曲线上时
                    global prev_mesh_name
                    co, mesh_name, curve_list = co_on_object(mujudict, context, event)
                    if (prev_mesh_name != mesh_name and op_cls.__left_mouse_down == False
                        and op_cls.__right_mouse_down == False) or op_cls.__curve_name == '':
                        if not bpy.data.objects.get(name + 'selectcurve') and op_cls.__is_modifier == False:
                            op_cls.__mesh_name = mesh_name
                            prev_mesh_name = op_cls.__mesh_name
                            op_cls.__curve_name = curve_list[0]
                            op_cls.__depth = curve_list[1]
                            op_cls.__curve_length = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                            op_cls.__number = int(op_cls.__curve_length * 0.1)
                            if op_cls.__curve_name == name + "PlaneBorderCurve":
                                op_cls.__snap_object_name = name + "batteryPlaneSnapCurve"
                            else:
                                op_cls.__snap_object_name = name + "MouldReset"
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            op_cls.__is_moving = True
                            op_cls.__left_mouse_down = True
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                            op_cls.__initial_co = co
                            if bpy.data.objects.get(name + 'selectcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'selectcurve'], do_unlink=True)  # 删除原有曲线
                                bpy.data.objects.remove(bpy.data.objects[name + 'dragcurve'], do_unlink=True)
                            if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                                if bpy.data.objects.get(name + "Torus") is not None:
                                    bpy.data.objects[name + "Torus"].hide_set(True)
                                if bpy.data.objects.get(name + "UpperTorus") is not None:
                                    bpy.data.objects[name + "UpperTorus"].hide_set(True)
                            elif bpy.context.scene.muJuTypeEnum == 'OP3':
                                if bpy.data.objects.get(name + "BottomTorus") is not None:
                                    bpy.data.objects[name + "BottomTorus"].hide_set(True)
                                if bpy.data.objects.get(name + "MiddleTorus") is not None:
                                    if name == "右耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                                    elif name == "左耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                                    if kongQiangMianBanType == 'OP1':
                                        bpy.data.objects[name + "MiddleTorus"].hide_set(True)
                                if bpy.data.objects.get(name + "TopTorus") is not None:
                                    bpy.data.objects[name + "TopTorus"].hide_set(True)
                        elif event.value == 'RELEASE':
                            op_cls.__is_moving = False
                            op_cls.__left_mouse_down = False
                            op_cls.__initial_mouse_x = None
                            op_cls.__initial_mouse_y = None
                            if bpy.data.objects.get(name + 'colorcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'colorcurve'], do_unlink=True)  # 删除原有曲线
                            if bpy.data.objects.get(name + 'coloredcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'coloredcurve'], do_unlink=True)
                        return {'RUNNING_MODAL'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            op_cls.__right_mouse_down = True
                            op_cls.__initial_mouse_x_right = event.mouse_region_x
                            op_cls.__initial_mouse_y_right = event.mouse_region_y
                            op_cls.__is_moving_right = True
                        elif event.value == 'RELEASE':
                            op_cls.__right_mouse_down = False
                            op_cls.__initial_mouse_x_right = None
                            op_cls.__initial_mouse_y_right = None
                            op_cls.__now_mouse_y_right = None
                            op_cls.__now_mouse_y_right = None
                            op_cls.__is_moving_right = False
                        return {'RUNNING_MODAL'}
                    elif event.type == 'MOUSEMOVE' and op_cls.__left_mouse_down == False and op_cls.__right_mouse_down == False:
                        # 鼠标移动时选择不同的曲线区域
                        if op_cls.__is_modifier == False and op_cls.__curve_name != '':
                            op_cls.__index = select_nearest_point(op_cls.__curve_name, co)
                            selectcurve(op_cls.__curve_name, op_cls.__depth, op_cls.__index, op_cls.__number)
                            # op_cls.__initial_co = get_co(op_cls.__curve_name, op_cls.__index)

                    return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 20 and bpy.context.scene.var in get_process_var_list("创建模具"):
                print('drag finish')
                set_drag_curve_modal_start(False)
                return {'FINISHED'}

            else:
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                print('drag finish')
                set_drag_curve_modal_start(False)
                if not get_shell_modal_start() and not get_soft_modal_start():
                    set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class TEST_OT_smoothcurve(bpy.types.Operator):
    bl_idname = "object.smoothcurve"
    bl_label = "smoothcurve"
    bl_description = "移动鼠标平滑曲线"

    __left_mouse_down = False
    __right_mouse_down = False
    __initial_mouse_x = None  # 点击鼠标左键的初始位置
    __initial_mouse_y = None
    __now_mouse_x = None  # 鼠标左键的现位置
    __now_mouse_y = None
    __initial_mouse_x_right = None  # 点击鼠标右键的初始位置
    __initial_mouse_y_right = None
    __now_mouse_x_right = None  # 鼠标右键的现位置
    __now_mouse_y_right = None
    __is_moving = False
    __is_moving_right = False
    __is_modifier = False
    __is_modifier_right = False

    __prev_mouse_location_x = None
    __prev_mouse_location_y = None

    __curve_name = ''
    __mesh_name = ''
    __depth = 0
    __number = None
    __curve_length = None
    __index = None
    __is_changed = None
    __snap_object_name = None

    def invoke(self, context, event):  # 初始化
        newColor('green', 0, 1, 0, 1, 1)
        newColor('blue', 0, 0, 1, 1, 1)
        op_cls = TEST_OT_smoothcurve
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_mouse_x_right = None
        op_cls.__initial_mouse_y_right = None
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__now_mouse_x_right = None
        op_cls.__now_mouse_y_right = None
        op_cls.__is_moving = False
        op_cls.__is_moving_right = False
        op_cls.__is_modifier = False
        # op_cls.__is_modifier_right = False

        # op_cls.__prev_mouse_location_x = None
        # op_cls.__prev_mouse_location_y = None

        op_cls.__curve_name = ''
        op_cls.__mesh_name = ''
        op_cls.__depth = 0
        op_cls.__number = None
        op_cls.__curve_length = None
        op_cls.__index = None
        op_cls.__is_changed = False
        op_cls.__snap_object_name = None

        bpy.context.scene.var = 21
        if not get_smooth_curve_modal_start():
            set_smooth_curve_modal_start(True)
            context.window_manager.modal_handler_add(self)
            print('smoothcurve invoke')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到公共鼠标行为

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # 右键选区，左键平滑
        op_cls = TEST_OT_smoothcurve
        mujudict = MuJudict().get_dic_name()
        name = bpy.context.scene.leftWindowObj
        override1 = getOverride()
        area = override1['area']
        if bpy.context.screen.areas[0].spaces.active.context == 'SCENE':
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 21):
                if co_on_object(mujudict, context, event) == -1 or co_on_object(mujudict, context, event) == 0:  # 鼠标不在曲线上时
                    if event.value == 'RELEASE':
                        if op_cls.__is_moving_right == True:  # 鼠标右键松开
                            op_cls.__right_mouse_down = False
                            op_cls.__initial_mouse_x_right = None
                            op_cls.__initial_mouse_y_right = None
                            op_cls.__now_mouse_x_right = None
                            op_cls.__now_mouse_y_right = None
                            op_cls.__is_moving_right = False
                            context.window.cursor_warp(event.mouse_prev_press_x, event.mouse_prev_press_y)
                        if op_cls.__is_moving == True:  # 鼠标左键松开
                            op_cls.__is_moving = False
                            op_cls.__left_mouse_down = False
                            op_cls.__initial_mouse_x = None
                            op_cls.__initial_mouse_y = None
                            op_cls.__now_mouse_x = None
                            op_cls.__now_mouse_y = None
                    if op_cls.__right_mouse_down == False:
                        if op_cls.__left_mouse_down == False and op_cls.__is_modifier == False:
                            if bpy.data.objects.get(name + 'selectcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'selectcurve'], do_unlink=True)  # 删除原有曲线
                            if bpy.data.objects.get(name + 'dragcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'dragcurve'], do_unlink=True)
                            if bpy.data.objects.get(name + 'colorcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'colorcurve'], do_unlink=True)  # 删除原有曲线
                            if bpy.data.objects.get(name + 'coloredcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'coloredcurve'], do_unlink=True)
                    if op_cls.__right_mouse_down == True:  # 鼠标右键按下
                        min_number = max(int(op_cls.__curve_length * 0.01), 3)
                        max_number = int(op_cls.__curve_length * 0.4)
                        # op_cls.__is_modifier_right = True
                        op_cls.__now_mouse_x_right = event.mouse_region_x
                        op_cls.__now_mouse_y_right = event.mouse_region_y
                        dis = int(((op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) ** 2 +
                                   (op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right) ** 2 ) ** 0.5 / 10)  # 鼠标移动的距离
                        if dis >= 1:
                            if op_cls.__now_mouse_y_right < op_cls.__initial_mouse_y_right:
                                dis *= -1  # 根据鼠标移动的方向确定是增大还是减小区域
                            op_cls.__number += dis  # 根据鼠标移动的距离扩大或缩小选区
                            if op_cls.__number < min_number:  # 防止选不到点弹出报错信息
                                op_cls.__number = min_number
                            if op_cls.__number > max_number:
                                op_cls.__number = max_number
                            changearea(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__depth)
                            op_cls.__initial_mouse_x_right = op_cls.__now_mouse_x_right  # 重新开始检测
                            op_cls.__initial_mouse_y_right = op_cls.__now_mouse_y_right
                    if op_cls.__left_mouse_down == True:  # 鼠标左键按下
                        op_cls.__is_modifier = True
                        op_cls.__now_mouse_x = event.mouse_region_x
                        op_cls.__now_mouse_y = event.mouse_region_y
                        dis = int(((op_cls.__now_mouse_y - op_cls.__initial_mouse_y) ** 2 +
                                   (op_cls.__now_mouse_x - op_cls.__initial_mouse_x) ** 2 ) ** 0.5 / 10)  # 鼠标移动的距离
                        if dis >= 1 and op_cls.__is_changed == False:
                            smoothcurve(op_cls.__curve_name, op_cls.__index, op_cls.__number)
                            snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__snap_object_name)  # 将曲线吸附到物体上
                            op_cls.__initial_mouse_x = op_cls.__now_mouse_x  # 重新开始检测
                            op_cls.__initial_mouse_y = op_cls.__now_mouse_y
                    if op_cls.__left_mouse_down == False:
                        # 吸附，重新切割
                        if bpy.data.objects.get(name + 'selectcurve') == None and op_cls.__is_modifier == True:
                            # join_dragcurve(op_cls.__curve_name, op_cls.__depth)
                            update_cut(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                            bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                            if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                                if bpy.data.objects.get(name + "Torus") is not None:
                                    bpy.data.objects[name + "Torus"].hide_set(False)
                                if bpy.data.objects.get(name + "UpperTorus") is not None:
                                    bpy.data.objects[name + "UpperTorus"].hide_set(False)
                            elif bpy.context.scene.muJuTypeEnum == 'OP3':
                                if bpy.data.objects.get(name + "BottomTorus") is not None:
                                    bpy.data.objects[name + "BottomTorus"].hide_set(False)
                                if bpy.data.objects.get(name + "MiddleTorus") is not None:
                                    if name == "右耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                                    elif name == "左耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                                    if kongQiangMianBanType == 'OP1':
                                        bpy.data.objects[name + "MiddleTorus"].hide_set(False)
                                if bpy.data.objects.get(name + "TopTorus") is not None:
                                    bpy.data.objects[name + "TopTorus"].hide_set(False)
                            op_cls.__is_modifier = False
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

                    return {'PASS_THROUGH'}

                else:  # 鼠标在曲线上时
                    global prev_mesh_name
                    co, mesh_name, curve_list = co_on_object(mujudict, context, event)
                    if (prev_mesh_name != mesh_name and op_cls.__left_mouse_down == False
                        and op_cls.__right_mouse_down == False) or op_cls.__curve_name == '':
                        if not bpy.data.objects.get(name + 'selectcurve') and op_cls.__is_modifier == False:
                            op_cls.__mesh_name = mesh_name
                            prev_mesh_name = op_cls.__mesh_name
                            op_cls.__curve_name = curve_list[0]
                            op_cls.__depth = curve_list[1]
                            op_cls.__curve_length = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                            op_cls.__number = int(op_cls.__curve_length * 0.1)
                            if op_cls.__curve_name == name + "PlaneBorderCurve":
                                op_cls.__snap_object_name = name + "batteryPlaneSnapCurve"
                            else:
                                op_cls.__snap_object_name = name + "MouldReset"
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            op_cls.__is_moving = True
                            op_cls.__left_mouse_down = True
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                            if bpy.data.objects.get(name + 'selectcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'selectcurve'], do_unlink=True)  # 删除原有曲线
                                bpy.data.objects.remove(bpy.data.objects[name + 'dragcurve'], do_unlink=True)
                            if bpy.context.scene.muJuTypeEnum == 'OP1' or bpy.context.scene.muJuTypeEnum == 'OP4':
                                if bpy.data.objects.get(name + "Torus") is not None:
                                    bpy.data.objects[name + "Torus"].hide_set(True)
                                if bpy.data.objects.get(name + "UpperTorus") is not None:
                                    bpy.data.objects[name + "UpperTorus"].hide_set(True)
                            elif bpy.context.scene.muJuTypeEnum == 'OP3':
                                if bpy.data.objects.get(name + "BottomTorus") is not None:
                                    bpy.data.objects[name + "BottomTorus"].hide_set(True)
                                if bpy.data.objects.get(name + "MiddleTorus") is not None:
                                    if name == "右耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
                                    elif name == "左耳":
                                        kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
                                    if kongQiangMianBanType == 'OP1':
                                        bpy.data.objects[name + "MiddleTorus"].hide_set(True)
                                if bpy.data.objects.get(name + "TopTorus") is not None:
                                    bpy.data.objects[name + "TopTorus"].hide_set(True)
                        elif event.value == 'RELEASE':
                            op_cls.__is_moving = False
                            op_cls.__left_mouse_down = False
                            op_cls.__initial_mouse_x = None
                            op_cls.__initial_mouse_y = None
                            op_cls.__now_mouse_x = None
                            op_cls.__now_mouse_y = None
                            if bpy.data.objects.get(name + 'colorcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'colorcurve'], do_unlink=True)  # 删除原有曲线
                            if bpy.data.objects.get(name + 'coloredcurve') != None:
                                bpy.data.objects.remove(bpy.data.objects[name + 'coloredcurve'], do_unlink=True)
                        return {'RUNNING_MODAL'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            op_cls.__right_mouse_down = True
                            op_cls.__initial_mouse_x_right = event.mouse_region_x
                            op_cls.__initial_mouse_y_right = event.mouse_region_y
                            op_cls.__is_moving_right = True
                        elif event.value == 'RELEASE':
                            op_cls.__right_mouse_down = False
                            op_cls.__initial_mouse_x_right = None
                            op_cls.__initial_mouse_y_right = None
                            op_cls.__now_mouse_y_right = None
                            op_cls.__now_mouse_y_right = None
                            op_cls.__is_moving_right = False
                        return {'RUNNING_MODAL'}
                    elif event.type == 'MOUSEMOVE':
                        # 鼠标移动时选择不同的曲线区域
                        if (op_cls.__left_mouse_down == False and op_cls.__right_mouse_down == False and
                                op_cls.__is_modifier == False and op_cls.__curve_name != ''):
                            op_cls.__index = select_nearest_point(op_cls.__curve_name, co)
                            selectcurve(op_cls.__curve_name, op_cls.__depth, op_cls.__index, op_cls.__number)
                        elif op_cls.__left_mouse_down == True and op_cls.__is_modifier == True:
                            index = select_nearest_point(op_cls.__curve_name, co)
                            if abs(index - op_cls.__index) > max(int(op_cls.__number * 0.3), 2):
                                op_cls.__is_changed = True
                                op_cls.__index = index
                                for _ in range(0, 3):
                                    smoothcurve(op_cls.__curve_name, op_cls.__index, op_cls.__number)
                                snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__snap_object_name)
                                op_cls.__is_changed = False
                            elif abs(index - op_cls.__index) > max(int(op_cls.__number * 0.1), 2):
                                op_cls.__is_changed = True
                                for _ in range(0, 3):
                                    smoothcurve(op_cls.__curve_name, op_cls.__index, op_cls.__number)
                                snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__snap_object_name)
                                op_cls.__is_changed = False

                    return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 21 and bpy.context.scene.var in get_process_var_list("创建模具"):
                print('smooth finish')
                set_smooth_curve_modal_start(False)
                return {'FINISHED'}

            else:
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                print('smooth finish')
                set_smooth_curve_modal_start(False)
                if not get_shell_modal_start() and not get_soft_modal_start():
                    set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class addcurve_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addcurve"
    bl_label = "双击添加点"
    bl_description = (
        "使用鼠标双击添加点"
    )
    bl_icon = "ops.curves.sculpt_cut"
    bl_widget = None
    bl_keymap = (
        ("object.pointqiehuan", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class addcurve_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addcurve3"
    bl_label = "添加点操作"
    bl_description = (
        "实现鼠标双击添加点操作"
    )
    bl_icon = "ops.curves.sculpt_grow_shrink"
    bl_widget = None
    bl_keymap = (
        ("object.addcurve", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("object.addpoint", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("object.deletepoint", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class dragcurve_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.dragcurve"
    bl_label = "拖拽曲线"
    bl_description = (
        "使用鼠标拖拽曲线"
    )
    bl_icon = "ops.curves.sculpt_density"
    bl_widget = None
    bl_keymap = (
        ("object.dragcurve", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class smoothcurve_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smoothcurve"
    bl_label = "平滑曲线"
    bl_description = (
        "使用鼠标平滑曲线"
    )
    bl_icon = "ops.curves.sculpt_add"
    bl_widget = None
    bl_keymap = (
        ("object.smoothcurve", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


_classes = [

    TEST_OT_addcurve,
    TEST_OT_dragcurve,
    TEST_OT_smoothcurve,
    TEST_OT_qiehuan,
    PointCut,
    PointFill,
    TEST_OT_addpoint,
    TEST_OT_deletepoint
]


def register_point_tools():
    bpy.utils.register_tool(addcurve_MyTool, separator=True, group=False)
    bpy.utils.register_tool(dragcurve_MyTool, separator=True,
                            group=False, after={addcurve_MyTool.bl_idname})
    bpy.utils.register_tool(smoothcurve_MyTool, separator=True,
                            group=False, after={dragcurve_MyTool.bl_idname})
    bpy.utils.register_tool(addcurve_MyTool3)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(addcurve_MyTool, separator=True, group=False)
    # bpy.utils.register_tool(dragcurve_MyTool, separator=True,
    #                         group=False, after={addcurve_MyTool.bl_idname})
    # bpy.utils.register_tool(smoothcurve_MyTool, separator=True,
    #                         group=False, after={dragcurve_MyTool.bl_idname})
    # bpy.utils.register_tool(addcurve_MyTool3)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(addcurve_MyTool)
    bpy.utils.unregister_tool(dragcurve_MyTool)
    bpy.utils.unregister_tool(smoothcurve_MyTool)
    bpy.utils.unregister_tool(addcurve_MyTool3)
