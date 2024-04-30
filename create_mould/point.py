import bpy
import bmesh
import mathutils
from bpy_extras import view3d_utils
from math import sqrt, fabs
from mathutils import Vector
from .dig_hole import boolean_cut, get_hole_border, translate_circle_to_cylinder, frame_clear_border_list, \
    frame_set_border_list, frame_get_border_list, frame_set_highest_vert_for_dig, darw_cylinder_bottom
from .border_fill import fill_frame_style_inner_face
from .soft_eardrum.thickness_and_fill import set_finish, get_fill_plane, fill, draw_cut_plane
from .soft_eardrum.soft_eardrum import soft_eardrum, get_cut_plane, plane_cut, delete_useless_part, \
    soft_set_co_and_normal, soft_clear_co_and_normal, soft_eardrum_smooth_initial, soft_set_highest_vert
from .frame_style_eardrum.frame_style_eardrum import frame_clear_co_and_normal, frame_set_co_and_normal, \
    extrude_border_by_vertex_groups, update_vert_group, fill_closest_point, frame_set_highest_vert
from .hard_eardrum.hard_eardrum import bottom_fill, hard_clear_co_and_normal, hard_set_co_and_normal, \
    hard_set_highest_vert, hard_cut, hard_fill
from ..tool import recover_and_remind_border, moveToRight, utils_re_color, convert_to_mesh, \
    recover_to_dig, newColor, subdivide, getOverride
from .create_mould import complete, delete_useless_object, delete_hole_border
from ..utils.utils import utils_plane_cut
import re


prev_on_object = False
prev_mesh_name = ''
is_cut_finish = True
is_fill_finish = True


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

    active_obj = bpy.data.objects["右耳MouldReset"]
    curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
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
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "EDIT_CURVE"):
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


class MuJudict:
    ruanermolist = ['BottomRingBorderR', 0.18]
    ruanermodict = {'meshBottomRingBorderR': ruanermolist}
    yingermolist = ['BottomRingBorderR', 0.18]
    yingermodict = {'meshBottomRingBorderR': yingermolist}
    yitidict = {}
    kuangjialist1 = ['BottomRingBorderR', 0.18]
    kuangjialist2 = ['HoleBorderCurve1', 0.18]
    kuangjialist3 = ['HoleBorderCurve2', 0.18]
    kuangjiadict = {'meshBottomRingBorderR': kuangjialist1, 'meshHoleBorderCurve1': kuangjialist2,
                    'meshHoleBorderCurve2': kuangjialist3}
    waikedict = {}
    mianbandict = {}

    mujudict = {'软耳模': ruanermodict,
                '硬耳膜': yingermodict,
                '一体外壳': yitidict,
                '框架式耳膜': kuangjiadict,
                '常规外壳': waikedict,
                '实心面板': mianbandict}

    def get_dic_name(self):
        ''' 获得当前磨具类型的曲线字典 '''
        enum = bpy.context.scene.muJuNameEnum
        return self.mujudict[enum]

    def update_dic(self):
        number = 0
        for key in self.kuangjiadict:
            if re.match('meshHoleBorderCurve', key) != None:
                number += 1
        add_mesh_name = 'meshHoleBorderCurve' + str(number + 1)
        mesh = bpy.data.meshes.new(add_mesh_name)
        obj = bpy.data.objects.new(add_mesh_name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        moveToRight(obj)
        add_curve_name = 'HoleBorderCurve' + str(number + 1)
        tempkuangjialist = [add_curve_name, 0.18]
        self.kuangjiadict.update({add_mesh_name: tempkuangjialist})
        return add_curve_name


def co_on_object(dic, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param dic: 要检测物体的字典
    :return: 相交的坐标、相交物体的名字和对应曲线的列表
    '''
    dic = MuJudict().get_dic_name()
    dismin = float('inf')
    mesh_name = ''
    flag = 0
    finalco = []
    for key in dic:
        active_obj = bpy.data.objects[key]

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

                co, _, _, dis = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if co is not None:
                    flag = 1
                    if (dis < dismin):
                        dismin = dis
                        mesh_name = key
                        finalco = co
    if (flag == 1):
        return (finalco, mesh_name, dic[mesh_name])  # 如果发生交叉，返回
    else:
        return -1


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
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = 'new' + curve_name
    # 创建一个新的曲线对象来存储复制的数据
    new_curve = bpy.data.curves.new(new_name, 'CURVE')
    new_curve.dimensions = '3D'
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)
    moveToRight(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.points.add(len(spline.points) - 1)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def join_curve(curve_name, depth, index_initial, index_finish):
    '''
    合并曲线(添加蓝线point后)
    :param curve_name: 曲线名字
    :param depth: 曲线倒角深度
    :param index_initial: 曲线起始位置下标
    :param index_finish: 曲线结束位置下标
    '''

    # 获取两条曲线对象
    curve_obj1 = bpy.data.objects[curve_name]
    curve_obj2 = bpy.data.objects['point']

    if index_initial > index_finish:  # 起始点的下标大于结束点

        # 获取两条曲线的曲线数据
        curve_data1 = curve_obj1.data
        curve_data2 = curve_obj2.data

        # 创建一个新的曲线对象
        new_curve_data = bpy.data.curves.new(
            name="newcurve", type='CURVE')
        new_curve_obj = bpy.data.objects.new(
            name="newcurve", object_data=new_curve_data)

        # 将新的曲线对象添加到场景中
        bpy.context.collection.objects.link(new_curve_obj)
        moveToRight(new_curve_obj)

        # 获取新曲线对象的曲线数据
        new_curve_data = new_curve_obj.data

        # 合并两条曲线的点集
        new_curve_data.splines.clear()
        new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
        point_number = len(curve_data1.splines[0].points) + len(
            curve_data2.splines[0].points) - abs(index_finish - index_initial) - 1
        new_spline.points.add(point_number)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True

        length = len(curve_data1.splines[0].points)  # length为第一条曲线的长度
        end_point = point_number - index_initial

        # 将第一条曲线在起始点后的点复制到新曲线
        for i, point in enumerate(curve_data1.splines[0].points):
            if i >= index_initial:
                new_spline.points[length - 1 - i].co = point.co

        # 将第二条曲线的点复制到新曲线
        for i, point in enumerate(curve_data2.splines[0].points):
            new_spline.points[i + length - index_initial].co = point.co

        # 将第一条曲线在结束点之后的点复制到新曲线
        for i, point in enumerate(curve_data1.splines[0].points):
            if i < index_finish:
                new_spline.points[point_number - i].co = point.co

        # 反转曲线方向
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.switch_direction()
        bpy.ops.object.mode_set(mode='OBJECT')

    else:
        # 获取两条曲线的曲线数据
        curve_data1 = curve_obj1.data
        curve_data2 = curve_obj2.data

        # 创建一个新的曲线对象
        new_curve_data = bpy.data.curves.new(
            name="newcurve", type='CURVE')
        new_curve_obj = bpy.data.objects.new(
            name="newcurve", object_data=new_curve_data)

        # 将新的曲线对象添加到场景中
        bpy.context.collection.objects.link(new_curve_obj)
        moveToRight(new_curve_obj)

        # 获取新曲线对象的曲线数据
        new_curve_data = new_curve_obj.data

        # 合并两条曲线的点集
        new_curve_data.splines.clear()
        new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
        point_number = len(curve_data1.splines[0].points) + len(
            curve_data2.splines[0].points) - abs(index_finish - index_initial) - 1
        new_spline.points.add(point_number)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True

        length = len(curve_data2.splines[0].points)  # length为第二条曲线的长度
        end_point = index_initial + length

        # 将第一条曲线在初始起点前的点复制到新曲线
        for i, point in enumerate(curve_data1.splines[0].points):
            if i == index_initial:
                break
            new_spline.points[i].co = point.co

        # 将第二条曲线的点复制到新曲线
        for i, point in enumerate(curve_data2.splines[0].points):
            new_spline.points[i + index_initial].co = point.co

        # 将第一条曲线在结束点之后的点复制到新曲线
        for i, point in enumerate(curve_data1.splines[0].points):
            if i >= index_finish:
                new_spline.points[index_initial + length + i - index_finish].co = point.co

    bpy.data.objects.remove(curve_obj1, do_unlink=True)
    bpy.data.objects.remove(curve_obj2, do_unlink=True)
    new_curve_obj.name = curve_name

    bpy.context.view_layer.objects.active = new_curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    new_curve_obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = depth
    bpy.context.object.data.dimensions = '3D'
    bpy.context.object.data.materials.append(bpy.data.materials['blue'])

    # 处理曲线结束时的瑕疵
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    new_curve_data.splines[0].points[end_point].select = True
    bpy.ops.curve.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

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

    # 根据选择模板进入不同的切割方式
    enum_name = bpy.context.scene.muJuNameEnum

    if (enum_name == '软耳模'):
        is_success = True
        set_finish(True)
        bpy.ops.object.select_all(action='DESELECT')
        recover_and_remind_border()
        soft_generate_cutplane(0.6, 0.2)  # 生成曲线
        # soft_eardrum()
        try:
            bpy.data.objects.remove(bpy.data.objects["RetopoPlane"], do_unlink=True)
            get_cut_plane()
            plane_cut()
            delete_useless_part()
            # 复制一份右耳
            cur_obj = bpy.data.objects["右耳"]
            duplicate_obj = cur_obj.copy()
            duplicate_obj.data = cur_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = cur_obj.name + "huanqiecompare"
            bpy.context.collection.objects.link(duplicate_obj)
            moveToRight(duplicate_obj)
            duplicate_obj.hide_set(True)

            if not bpy.data.objects.get('右耳Circle'):
                draw_cut_plane("右耳")
                bpy.ops.object.softeardrumcirclecut('INVOKE_DEFAULT')

            get_fill_plane()
            fill()
            utils_re_color("右耳", (1, 0.319, 0.133))
            utils_re_color("右耳huanqiecompare", (1, 0.319, 0.133))

            soft_eardrum_smooth_initial()
            convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
            set_finish(False)
        except:
            is_success = False

        if not is_success:
            recover_and_remind_border()
            if bpy.data.objects.get("Center") != None:
                bpy.data.objects.remove("Center", do_unlink=True)
            if bpy.data.objects.get("CutPlane") != None:
                bpy.data.objects.remove("CutPlane", do_unlink=True)
            if bpy.data.objects.get("Inner") != None:
                bpy.data.objects.remove("Inner", do_unlink=True)
            convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
            utils_re_color("右耳", (1, 1, 0))
            utils_re_color("右耳huanqiecompare", (1, 1, 0))

    if (enum_name == '框架式耳膜'):
        if (re.match('HoleBorderCurve', curve_name) != None):  # 上部曲线改变
            recover_to_dig()
            number = 0
            for obj in bpy.data.objects:
                if re.match('HoleBorderCurve', obj.name) != None:
                    number += 1

            # 记录点的坐标，删除原有的曲线
            frame_clear_border_list()
            for i in range(1, number + 1):
                local_curve_name = 'HoleBorderCurve' + str(i)
                dig_border = []
                for point in bpy.data.objects[local_curve_name].data.splines[0].points:
                    dig_border.append(point.co[0:3])
                frame_set_border_list(dig_border)
                bpy.data.objects.remove(bpy.data.objects[local_curve_name], do_unlink=True)

            # 根据点的坐标重新画线，画一个挖一个
            border_list = frame_get_border_list()
            template_highest_point = frame_set_highest_vert_for_dig()
            for i in range(1, number + 1):
                local_curve_name = 'HoleBorderCurve' + str(i)
                local_mesh_name = 'mesh' + local_curve_name
                # 重新生成曲线
                # get_hole_border(template_highest_point, border_list[i - 1], i)
                draw_curve(border_list[i - 1], local_curve_name, 0.18)
                darw_cylinder_bottom(border_list[i - 1])
                translate_circle_to_cylinder()
                boolean_cut()
                convert_to_mesh(local_curve_name, local_mesh_name, depth)  # 重新生成网格
                # bpy.context.view_layer.objects.active = bpy.data.objects['右耳']

            # fill_frame_style_inner_face()
            update_vert_group()
            fill_closest_point()
            bpy.ops.object.timer_framestyleeardrum_add_modifier_after_qmesh()
            utils_re_color("右耳", (1, 0.319, 0.133))

        else:  # 下部曲线改变
            recover_and_remind_border()
            frame_generate_cutplane(0.6, 0.2)
            soft_eardrum()
            extrude_border_by_vertex_groups("BottomOuterBorderVertex", "BottomInnerBorderVertex")
            convert_to_mesh(curve_name, mesh_name, depth)

            number = 0
            for obj in bpy.data.objects:
                if re.match('HoleBorderCurve', obj.name) != None:
                    number += 1

            # 上部曲线不动，所以仅需删除原有的曲线
            # frame_clear_border_list()
            for i in range(1, number + 1):
                local_curve_name = 'HoleBorderCurve' + str(i)
                # dig_border = []
                # for point in bpy.data.objects[local_curve_name].data.splines[0].points:
                #     dig_border.append(point.co[0:3])
                # frame_set_border_list(dig_border)
                bpy.data.objects.remove(bpy.data.objects[local_curve_name], do_unlink=True)

            # 根据点的坐标重新画线，画一个挖一个
            border_list = frame_get_border_list()
            template_highest_point = frame_set_highest_vert_for_dig()
            for i in range(1, number + 1):
                local_curve_name = 'HoleBorderCurve' + str(i)
                local_mesh_name = 'mesh' + local_curve_name
                # 重新生成曲线
                # get_hole_border(template_highest_point, border_list[i - 1], i)
                draw_curve(border_list[i - 1], local_curve_name, 0.18)
                darw_cylinder_bottom(border_list[i - 1])
                translate_circle_to_cylinder()
                boolean_cut()
                convert_to_mesh(local_curve_name, local_mesh_name, depth)  # 重新生成网格
                # bpy.context.view_layer.objects.active = bpy.data.objects['右耳']

            # fill_frame_style_inner_face()
            update_vert_group()
            fill_closest_point()
            bpy.ops.object.timer_framestyleeardrum_add_modifier_after_qmesh()
            utils_re_color("右耳", (1, 0.319, 0.133))

    if (enum_name == '硬耳膜'):
        recover_and_remind_border()
        convert_to_mesh('BottomRingBorderR', 'meshBottomRingBorderR', 0.18)
        hard_generate_cutplane(1, 0.2)  # 生成曲线
        utils_plane_cut()
        bpy.ops.object.mode_set(mode='EDIT')  # 选中切割后的循环边
        cur_obj = bpy.data.objects["右耳"]
        bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
        if (bottom_outer_border_vertex != None):
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.pointfill('INVOKE_DEFAULT')
        global is_fill_finish
        is_fill_finish = False
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


def soft_generate_cutplane(step_number_out, step_number_in):
    active_obj = bpy.data.objects['BottomRingBorderR']
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects['Center']
    curve_object2 = bpy.data.objects['CutPlane']
    curve_object3 = bpy.data.objects['Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    soft_clear_co_and_normal()
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)
        soft_set_co_and_normal(vertex_co[0:3], normal[0:3])
        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)

    soft_set_highest_vert()
    bpy.data.objects['Center'].data.bevel_depth = 0
    bpy.data.objects['CutPlane'].data.bevel_depth = 0
    bpy.data.objects['Inner'].data.bevel_depth = 0


def frame_generate_cutplane(step_number_out, step_number_in):
    active_obj = bpy.data.objects['BottomRingBorderR']
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects['Center']
    curve_object2 = bpy.data.objects['CutPlane']
    curve_object3 = bpy.data.objects['Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    frame_clear_co_and_normal()
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)
        frame_set_co_and_normal(vertex_co[0:3], normal[0:3])
        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)

    frame_set_highest_vert()
    bpy.data.objects['Center'].data.bevel_depth = 0
    bpy.data.objects['CutPlane'].data.bevel_depth = 0
    bpy.data.objects['Inner'].data.bevel_depth = 0


def hard_generate_cutplane(step_number_out, step_number_in):
    active_obj = bpy.data.objects['BottomRingBorderR']
    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "Center"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "CutPlane"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    duplicate_obj = active_obj.copy()
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "Inner"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)

    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
    # 获取曲线对象
    curve_object = bpy.data.objects['Center']
    curve_object2 = bpy.data.objects['CutPlane']
    curve_object3 = bpy.data.objects['Inner']

    # 获取数据
    curve_data = curve_object.data
    curve_data2 = curve_object2.data
    curve_data3 = curve_object3.data
    # subdivide('CutPlane', 3)
    hard_clear_co_and_normal()
    # 将曲线的每个顶点沿法向移动
    length = len(curve_data.splines[0].points)
    for i in range(0, length):
        # 获取顶点原位置
        vertex_co = curve_object.matrix_world @ mathutils.Vector(curve_data.splines[0].points[i].co[0:3])
        _, _, normal, _ = target_object.closest_point_on_mesh(vertex_co)
        hard_set_co_and_normal(vertex_co[0:3], normal[0:3])
        out_point = curve_data2.splines[0].points[i]
        inner_point = curve_data3.splines[0].points[i]
        step_out = step_number_out
        out_point.co = (out_point.co[0] + normal[0] * step_out, out_point.co[1] + normal[1] * step_out,
                        out_point.co[2] + normal[2] * step_out, 1)
        step_in = step_number_in
        inner_point.co = (inner_point.co[0] - normal[0] * step_in, inner_point.co[1] - normal[1] * step_in,
                          inner_point.co[2] - normal[2] * step_in, 1)

    hard_set_highest_vert()
    bpy.data.objects['Center'].data.bevel_depth = 0
    bpy.data.objects['CutPlane'].data.bevel_depth = 0
    bpy.data.objects['Inner'].data.bevel_depth = 0


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
    for i in range(0, point_number, 1):
        bpy.ops.curve.smooth()  # 平滑曲线
    bpy.ops.object.mode_set(mode='OBJECT')


def snaptoobject(curve_name):
    ''' 将指定的曲线对象吸附到最近的顶点上 '''
    # 获取曲线对象
    curve_object = bpy.data.objects[curve_name]
    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
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


def snapselect(curve_name, index, number):
    ''' 将选中的曲线部分吸附到最近的顶点上 '''
    # 获取曲线对象
    curve_object = bpy.data.objects[curve_name]
    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
    # 获取数据
    curve_data = curve_object.data

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
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = 'selectcurve'
    # 创建一个新的曲线对象来存储复制的数据
    # if bpy.data.objects.get(new_name) != None:
    #     return False
    new_curve = bpy.data.curves.new(new_name, 'CURVE')
    new_curve.dimensions = '3D'
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)
    moveToRight(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True
        new_spline.points.add(len(spline.points) - 1)
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co
    # return True


def copy_color_curve(curve_name):
    ''' 复制曲线数据 '''
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = 'colorcurve'
    # 创建一个新的曲线对象来存储复制的数据
    new_curve = bpy.data.curves.new(new_name, 'CURVE')
    new_curve.dimensions = '3D'
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)
    moveToRight(new_obj)

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
    select_name = 'selectcurve'
    if bpy.data.objects.get(select_name) != None:
        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
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
            object.name = 'dragcurve'
            break

    bpy.data.objects['dragcurve'].data.materials.clear()  # 清除材质
    newColor('green', 0, 1, 0, 1, 1)
    bpy.data.objects['dragcurve'].data.materials.append(bpy.data.materials['green'])
    moveToRight(bpy.data.objects['dragcurve'])
    bpy.context.view_layer.objects.active = bpy.data.objects['dragcurve']
    bpy.context.object.data.bevel_depth = depth
    bpy.ops.object.select_all(action='DESELECT')


def selectcurve(context, event, curve_name, mesh_name, depth, number):
    ''' 选择拖拽曲线对象 '''

    select_name = 'selectcurve'
    if bpy.data.objects.get(select_name) != None:
        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    copy_select_curve(curve_name)  # 复制一份数据用于分离
    if cal_co(mesh_name, context, event) != -1:
        co = cal_co(mesh_name, context, event)
        index = select_nearest_point(curve_name, co)
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
            object.name = 'dragcurve'
            break

    bpy.data.objects['dragcurve'].data.materials.clear()  # 清除材质
    newColor('green', 0, 1, 0, 1, 1)
    bpy.data.objects['dragcurve'].data.materials.append(bpy.data.materials['green'])
    moveToRight(bpy.data.objects['dragcurve'])
    bpy.context.view_layer.objects.active = bpy.data.objects['dragcurve']
    bpy.context.object.data.bevel_depth = depth
    bpy.ops.object.select_all(action='DESELECT')
    return index


def colorcurve(curve_name, index, number):
    ''' 移动时将移动的部分标绿 '''

    if bpy.data.objects.get('colorcurve') != None:
        bpy.data.objects.remove(bpy.data.objects['colorcurve'], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects['coloredcurve'], do_unlink=True)
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    copy_color_curve(curve_name)  # 复制一份数据用于分离
    curve_obj = bpy.data.objects['colorcurve']
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
    bpy.data.objects['colorcurve'].hide_set(True)
    copy_name = 'colorcurve' + '.001'
    for object in bpy.data.objects:  # 改名
        if object.name == copy_name:
            object.name = 'coloredcurve'
            break

    bpy.data.objects['coloredcurve'].data.materials.clear()  # 清除材质
    newColor('green', 0, 1, 0, 1, 1)
    bpy.data.objects['coloredcurve'].data.materials.append(bpy.data.materials['green'])
    moveToRight(bpy.data.objects['coloredcurve'])
    bpy.context.view_layer.objects.active = bpy.data.objects['coloredcurve']
    bpy.context.object.data.bevel_depth = 0.18
    bpy.ops.object.select_all(action='DESELECT')


def movecurve(co, initial_co, curve_name, index, number):
    curve_obj = bpy.data.objects[curve_name]
    bpy.context.view_layer.objects.active = curve_obj
    curve_data = curve_obj.data
    dis = (co - initial_co).normalized()  # 距离向量
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    # start_index = (index - number + point_number) % point_number
    # finish_index = (index + number + point_number) % point_number
    for i in range(index - number, index + number):
        insert_index = (i + point_number) % point_number
        point = curve_data.splines[0].points[insert_index]
        vector_co = Vector(point.co[0:3]) + dis * disfunc(abs(i - index), number)
        point.co[0:3] = vector_co[0:3]
        point.co[3] = 1


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

    # 获取两条曲线对象
    curve_obj1 = bpy.data.objects[curve_name]
    curve_obj2 = bpy.data.objects['dragcurve']

    # 获取两条曲线的曲线数据
    curve_data1 = curve_obj1.data
    curve_data2 = curve_obj2.data

    # 创建一个新的曲线对象
    new_curve_data = bpy.data.curves.new(
        name="newdragcurve", type='CURVE')
    new_curve_obj = bpy.data.objects.new(
        name="newdragcurve", object_data=new_curve_data)

    # 将新的曲线对象添加到场景中
    bpy.context.collection.objects.link(new_curve_obj)
    moveToRight(new_curve_obj)

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
    bpy.data.objects.remove(bpy.data.objects['selectcurve'], do_unlink=True)
    new_curve_obj.name = curve_name

    bpy.context.view_layer.objects.active = new_curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    new_curve_obj.select_set(state=True)
    new_curve_obj.data.materials.clear()
    new_curve_obj.data.materials.append(bpy.data.materials['blue'])
    bpy.context.object.data.bevel_depth = depth
    bpy.context.object.data.dimensions = '3D'


def draw_curve(order_border_co, name, depth):
    active_obj = bpy.context.active_object
    new_node_list = list()
    for i in range(len(order_border_co)):
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
                    pass
                    # print("软耳模切割")
                    # soft_cut()
                    # bpy.context.scene.neiBianJiXian = False
                elif mould_type == "OP2":
                    # print("硬耳膜切割")
                    pass
            except:
                print("切割出错")
                cut_success = False
                # todo 回退到初始
            if cut_success:
                global is_fill_finish
                is_fill_finish = False
                # todo 回退到初始
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
        if not is_fill_finish:
            is_fill_finish = True
            try:
                mould_type = bpy.context.scene.muJuTypeEnum
                if mould_type == "OP1":
                    pass
                    # print("软耳模填充")
                    # soft_fill()
                elif mould_type == "OP2":
                    print("硬耳模填充")
                    hard_fill()
            except:
                print("填充失败")
                fill_success = False
                # todo 回退到切割后
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

    def excute(self, context, event):
        mujudict = MuJudict().get_dic_name()
        op_cls = TEST_OT_addcurve

        if co_on_object(mujudict, context, event) == -1:  # 双击位置不在曲线上
            if bpy.context.scene.neiBianJiXian and bpy.context.scene.muJuTypeEnum == 'OP4':
                if cal_co('右耳', context, event) != -1:  # 双击位置在耳模上
                    co = cal_co('右耳', context, event)
                    if bpy.context.mode == 'OBJECT':
                        # 创建一个新的曲线对象
                        new_curve_name = MuJudict().update_dic()
                        new_curve_data = bpy.data.curves.new(
                            name=new_curve_name, type='CURVE')
                        new_curve_obj = bpy.data.objects.new(
                            name=new_curve_name, object_data=new_curve_data)
                        new_curve_data.bevel_depth = 0.18  # 管道孔径
                        new_curve_data.dimensions = '3D'
                        bpy.context.collection.objects.link(new_curve_obj)
                        moveToRight(new_curve_obj)
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
                        # new_curve_data.splines[0].points.add(count = 1)
                        # new_curve_data.splines[0].points[1].co[0:3] = co
                        # new_curve_data.splines[0].points[1].co[3] = 1

                        # 开启吸附
                        bpy.context.scene.tool_settings.use_snap = True
                        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
                        bpy.context.scene.tool_settings.snap_target = 'CLOSEST'
                        bpy.context.scene.tool_settings.use_snap_align_rotation = True
                        bpy.context.scene.tool_settings.use_snap_backface_culling = True
                        bpy.context.view_layer.objects.active = new_curve_obj
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.curve.select_all(action='DESELECT')
                        new_curve_data.splines[0].points[0].select = True
                        bpy.ops.wm.tool_set_by_id(name="builtin.extrude_cursor")

                    elif bpy.context.mode == 'EDIT_CURVE':
                        curve_obj = bpy.context.active_object
                        curve_obj.data.splines[0].use_cyclic_u = True
                        idx = len(curve_obj.data.splines[0].points) - 1
                        bpy.ops.curve.select_all(action='DESELECT')
                        curve_obj.data.splines[0].points[idx].select = True
                        bpy.ops.curve.delete(type='VERT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # 将曲线转换成网格，切割
                        local_curve_name = curve_obj.name
                        local_mesh_name = 'mesh' + curve_obj.name
                        update_cut(local_curve_name, local_mesh_name, 0.18)
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        else:
            if bpy.context.mode == 'OBJECT':  # 如果处于物体模式下，蓝线双击开始绘制
                if bpy.context.scene.muJuTypeEnum == 'OP1':
                    set_finish(True)
                co, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
                op_cls.__curve_name = curve_list[0]
                op_cls.__depth = curve_list[1]
                op_cls.__index_initial = select_nearest_point(op_cls.__curve_name, co)
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
                    name='point', type='CURVE')
                new_curve_obj = bpy.data.objects.new(
                    name='point', object_data=new_curve_data)
                new_curve_data.bevel_depth = op_cls.__depth  # 管道孔径
                new_curve_data.dimensions = '3D'
                bpy.context.collection.objects.link(new_curve_obj)
                moveToRight(new_curve_obj)
                new_curve_data.materials.append(bpy.data.materials['blue'])
                new_curve_data.splines.clear()
                new_spline = new_curve_data.splines.new(type='NURBS')
                new_spline.use_smooth = True
                new_spline.order_u = 2
                new_curve_data.splines[0].points[0].co[0:3] = co
                new_curve_data.splines[0].points[0].co[3] = 1

                bpy.context.view_layer.objects.active = new_curve_obj
                bpy.ops.object.select_all(action='DESELECT')
                new_curve_obj.select_set(state=True)
                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式进行操作
                bpy.ops.curve.select_all(action='DESELECT')
                new_curve_data.splines[0].points[0].select = True
                # 开启吸附
                bpy.context.scene.tool_settings.use_snap = True
                bpy.context.scene.tool_settings.snap_elements = {'FACE'}
                bpy.context.scene.tool_settings.snap_target = 'CLOSEST'
                bpy.context.scene.tool_settings.use_snap_align_rotation = True
                bpy.context.scene.tool_settings.use_snap_backface_culling = True
                bpy.ops.wm.tool_set_by_id(name="builtin.extrude_cursor")

            elif bpy.context.mode == 'EDIT_CURVE':  # 如果处于编辑模式下，蓝线双击确认完成
                # print("起始位置的下标是", op_cls.__index_initial)
                co = cal_co(op_cls.__mesh_name, context, event)
                op_cls.__index_finish = select_nearest_point(op_cls.__curve_name, co)
                # print("结束的下标是", op_cls.__index_finish)
                bpy.ops.object.mode_set(mode='OBJECT')  # 返回对象模式
                bpy.context.scene.tool_settings.use_snap = False  # 取消吸附
                join_object(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth, op_cls.__index_initial,
                            op_cls.__index_finish)  # 合并曲线
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                if bpy.context.scene.muJuTypeEnum == 'OP1':
                    set_finish(False)
            else:
                pass

    def invoke(self, context, event):
        op_cls = TEST_OT_addcurve
        newColor('blue', 0, 0, 1, 1, 1)
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_qiehuan(bpy.types.Operator):
    bl_idname = "object.pointqiehuan"
    bl_label = "pointqiehuan"
    bl_description = "鼠标行为切换"

    def invoke(self, context, event):  # 初始化
        print('pointqiehuan invoke')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 19
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if bpy.context.scene.var != 19:
            print('pointqiehuan finish')
            return {'FINISHED'}
        elif cal_co('右耳MouldReset', context, event) != -1 and is_changed(context, event) == True:
            if bpy.context.mode == 'OBJECT':
                bpy.ops.wm.tool_set_by_id(name="my_tool.addcurve3")
            elif bpy.context.mode == 'EDIT_CURVE':
                bpy.ops.wm.tool_set_by_id(name="builtin.extrude_cursor")
        elif cal_co('右耳MouldReset', context, event) == -1 and is_changed(context, event) == True:
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        return {'PASS_THROUGH'}


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

    def invoke(self, context, event):  # 初始化
        bpy.context.scene.var = 20
        print('dragcurve invoke')
        newColor('green', 0, 1, 0, 1, 1)
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到公共鼠标行为
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

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TEST_OT_dragcurve
        mujudict = MuJudict().get_dic_name()
        if bpy.context.scene.var != 20:
            print('drag finish')
            return {'FINISHED'}
        if co_on_object(mujudict, context, event) == -1:  # 鼠标不在曲线上时
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
                    if bpy.data.objects.get('colorcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['colorcurve'], do_unlink=True)  # 删除原有曲线
                    if bpy.data.objects.get('coloredcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['coloredcurve'], do_unlink=True)
            if op_cls.__right_mouse_down == False:
                if op_cls.__left_mouse_down == False and op_cls.__is_modifier == False:
                    if bpy.data.objects.get('selectcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['selectcurve'], do_unlink=True)  # 删除原有曲线
                    if bpy.data.objects.get('dragcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
            if op_cls.__right_mouse_down == True:  # 鼠标右键按下
                min_number = max(int(op_cls.__curve_length * 0.01), 2)
                max_number = int(op_cls.__curve_length * 0.4)
                # op_cls.__is_modifier_right = True
                # 记录下第一次点击鼠标的位置
                op_cls.__now_mouse_x_right = event.mouse_region_x
                op_cls.__now_mouse_y_right = event.mouse_region_y
                dis = int(sqrt(fabs(op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) * fabs(
                    op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) + fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right) * fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right)) / 10)  # 鼠标移动的距离
                if (dis >= 1):
                    if (op_cls.__now_mouse_x_right < op_cls.__initial_mouse_x_right or \
                            op_cls.__now_mouse_y_right < op_cls.__initial_mouse_y_right):
                        dis *= -1  # 根据鼠标移动的方向确定是增大还是减小区域
                    op_cls.__number += dis  # 根据鼠标移动的距离扩大或缩小选区
                    if (op_cls.__number < min_number):  # 防止选不到点弹出报错信息
                        op_cls.__number = min_number
                    if (op_cls.__number > max_number):
                        op_cls.__number = max_number
                    changearea(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__depth)
                    op_cls.__initial_mouse_x_right = op_cls.__now_mouse_x_right  # 重新开始检测
                    op_cls.__initial_mouse_y_right = op_cls.__now_mouse_y_right
            if op_cls.__left_mouse_down == True:  # 鼠标左键按下
                co = cal_co('右耳MouldReset', context, event)
                op_cls.__is_modifier = True
                if co != -1:
                    if (co - op_cls.__initial_co).dot(co - op_cls.__initial_co) >= 0.05:
                        movecurve(co, op_cls.__initial_co, op_cls.__curve_name, op_cls.__index, op_cls.__number)
                        snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number)  # 将曲线吸附到物体上
                        op_cls.__initial_co = co
            if op_cls.__left_mouse_down == False:
                # 重新切割
                if bpy.data.objects.get('selectcurve') == None and op_cls.__is_modifier == True:
                    # join_dragcurve(op_cls.__curve_name,op_cls.__depth)
                    update_cut(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                    op_cls.__is_modifier = False
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            return {'PASS_THROUGH'}

        else:
            global prev_mesh_name
            _, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
            if (prev_mesh_name != op_cls.__mesh_name and op_cls.__is_modifier == False) or op_cls.__curve_name == '':
                if not bpy.data.objects.get('selectcurve'):
                    prev_mesh_name = op_cls.__mesh_name
                    op_cls.__curve_name = curve_list[0]
                    op_cls.__depth = curve_list[1]
                    op_cls.__curve_length = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                    op_cls.__number = int(op_cls.__curve_length * 0.05)
            if event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    op_cls.__is_moving = True
                    op_cls.__left_mouse_down = True
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                    if bpy.data.objects.get('selectcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['selectcurve'], do_unlink=True)  # 删除原有曲线
                        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                elif event.value == 'RELEASE':
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
                    if bpy.data.objects.get('colorcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['colorcurve'], do_unlink=True)  # 删除原有曲线
                    if bpy.data.objects.get('coloredcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['coloredcurve'], do_unlink=True)
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
                if op_cls.__is_modifier == False:
                    op_cls.__index = selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name,
                                                 op_cls.__depth, op_cls.__number)
                    op_cls.__initial_co = get_co(op_cls.__curve_name, op_cls.__index)

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

    def invoke(self, context, event):  # 初始化
        bpy.context.scene.var = 21
        print('smoothcurve invoke')
        newColor('green', 0, 1, 0, 1, 1)
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到公共鼠标行为
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

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # 右键选区，左键平滑
        op_cls = TEST_OT_smoothcurve
        mujudict = MuJudict().get_dic_name()
        if bpy.context.scene.var != 21:
            print('smooth finish')
            return {'FINISHED'}
        if co_on_object(mujudict, context, event) == -1:  # 鼠标不在曲线上时
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
                    if bpy.data.objects.get('selectcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['selectcurve'], do_unlink=True)  # 删除原有曲线
                    if bpy.data.objects.get('dragcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                    if bpy.data.objects.get('colorcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['colorcurve'], do_unlink=True)  # 删除原有曲线
                    if bpy.data.objects.get('coloredcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['coloredcurve'], do_unlink=True)
            if op_cls.__right_mouse_down == True:  # 鼠标右键按下
                min_number = max(int(op_cls.__curve_length * 0.01), 2)
                max_number = int(op_cls.__curve_length * 0.4)
                # op_cls.__is_modifier_right = True
                op_cls.__now_mouse_x_right = event.mouse_region_x
                op_cls.__now_mouse_y_right = event.mouse_region_y
                dis = int(sqrt(fabs(op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) * fabs(
                    op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) + fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right) * fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right)) / 10)  # 鼠标移动的距离
                if (dis >= 1):
                    if (op_cls.__now_mouse_x_right < op_cls.__initial_mouse_x_right or \
                            op_cls.__now_mouse_y_right < op_cls.__initial_mouse_y_right):
                        dis *= -1  # 根据鼠标移动的方向确定是增大还是减小区域
                    op_cls.__number += dis  # 根据鼠标移动的距离扩大或缩小选区
                    if (op_cls.__number < min_number):  # 防止选不到点弹出报错信息
                        op_cls.__number = min_number
                    if (op_cls.__number > max_number):
                        op_cls.__number = max_number
                    changearea(op_cls.__curve_name, op_cls.__index, op_cls.__number, op_cls.__depth)
                    op_cls.__initial_mouse_x_right = op_cls.__now_mouse_x_right  # 重新开始检测
                    op_cls.__initial_mouse_y_right = op_cls.__now_mouse_y_right
            if op_cls.__left_mouse_down == True:  # 鼠标左键按下
                op_cls.__is_modifier = True
                op_cls.__now_mouse_x = event.mouse_region_x
                op_cls.__now_mouse_y = event.mouse_region_y
                dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                    op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                    op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                    op_cls.__now_mouse_x - op_cls.__initial_mouse_x)) / 10)  # 鼠标移动的距离
                if (dis >= 1):
                    smoothcurve(op_cls.__curve_name, op_cls.__index, op_cls.__number)
                    snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number)  # 将曲线吸附到物体上
                    op_cls.__initial_mouse_x = op_cls.__now_mouse_x  # 重新开始检测
                    op_cls.__initial_mouse_y = op_cls.__now_mouse_y
            if op_cls.__left_mouse_down == False:
                # 吸附，重新切割
                if bpy.data.objects.get('selectcurve') == None and op_cls.__is_modifier == True:
                    # join_dragcurve(op_cls.__curve_name, op_cls.__depth)
                    update_cut(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                    op_cls.__is_modifier = False
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            return {'PASS_THROUGH'}

        else:
            global prev_mesh_name
            _, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
            if (prev_mesh_name != op_cls.__mesh_name and op_cls.__is_modifier == False) or op_cls.__curve_name == '':
                if not bpy.data.objects.get('selectcurve'):
                    prev_mesh_name = op_cls.__mesh_name
                    op_cls.__curve_name = curve_list[0]
                    op_cls.__depth = curve_list[1]
                    op_cls.__curve_length = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                    op_cls.__number = int(op_cls.__curve_length * 0.05)
            if event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    op_cls.__is_moving = True
                    op_cls.__left_mouse_down = True
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                    if bpy.data.objects.get('selectcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['selectcurve'], do_unlink=True)  # 删除原有曲线
                        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                elif event.value == 'RELEASE':
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
                    op_cls.__now_mouse_x = None
                    op_cls.__now_mouse_y = None
                    if bpy.data.objects.get('colorcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['colorcurve'], do_unlink=True)  # 删除原有曲线
                    if bpy.data.objects.get('coloredcurve') != None:
                        bpy.data.objects.remove(bpy.data.objects['coloredcurve'], do_unlink=True)
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
                if op_cls.__is_modifier == False:
                    op_cls.__index = selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name,
                                                 op_cls.__depth, op_cls.__number)

        return {'PASS_THROUGH'}


class TEST_OT_resethmould(bpy.types.Operator):
    bl_idname = "object.resetmould"
    bl_label = "重置操作"
    bl_description = "点击按钮重置创建磨具"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 32
        return {'FINISHED'}

    def excute(self, context, event):
        recover_flag = False
        for obj in bpy.context.view_layer.objects:
            if obj.name == "右耳OriginForCreateMouldR":
                recover_flag = True
                break
        # 找到最初创建的  OriginForCreateMould 才能进行恢复
        if recover_flag:
            # 删除不需要的物体
            need_to_delete_model_name_list = ["右耳", "HoleCutCylinderBottomR",
                                              "HoleBorderCurveR", "BottomRingBorderR", "cutPlane",
                                              "BottomRingBorderRForCutR",
                                              "右耳OriginForCutR", "右耳Circle", "右耳Torus", "左耳Circle", "左耳Torus",
                                              "右耳huanqiecompare", "FillPlane",
                                              "右耳ForGetFillPlane", "meshBottomRingBorderR", "dragcurve",
                                              "selectcurve"]
            delete_useless_object(need_to_delete_model_name_list)
            delete_hole_border()
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

            enum = bpy.context.scene.muJuTypeEnum
            if enum == "OP1":
                set_finish(True)


class TEST_OT_finishmould(bpy.types.Operator):
    bl_idname = "object.finishmould"
    bl_label = "完成操作"
    bl_description = "点击按钮完成创建磨具"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 31
        return {'FINISHED'}

    def excute(self, context, event):
        complete()


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


class addcurve_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVE'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addcurve2"
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
        ("object.addcurve", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'},
         {}),
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


class dragcurve_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVE'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.dragcurve2"
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


class smoothcurve_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVE'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smoothcurve2"
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


class resetmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetmould"
    bl_label = "重置创建磨具"
    bl_description = (
        "点击重置创建磨具"
    )
    bl_icon = "ops.curves.sculpt_comb"
    bl_widget = None
    bl_keymap = (
        ("object.resetmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetmould_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVE'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetmould2"
    bl_label = "重置创建磨具"
    bl_description = (
        "点击重置创建磨具"
    )
    bl_icon = "ops.curves.sculpt_comb"
    bl_widget = None
    bl_keymap = (
        ("object.resetmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class finishmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishmould"
    bl_label = "完成创建磨具"
    bl_description = (
        "点击完成创建磨具"
    )
    bl_icon = "ops.curves.sculpt_delete"
    bl_widget = None
    bl_keymap = (
        ("object.finishmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class finishmould_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVE'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishmould2"
    bl_label = "完成创建磨具"
    bl_description = (
        "点击完成创建磨具"
    )
    bl_icon = "ops.curves.sculpt_delete"
    bl_widget = None
    bl_keymap = (
        ("object.finishmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class PrintMoban(bpy.types.Operator):  # 打印模板数据
    bl_idname = "object.printmoban"
    bl_label = "3D Model"

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        curve_object = bpy.data.objects['BottomRingBorderR']
        target_object = bpy.data.objects["右耳MouldReset"]
        curve_data = curve_object.data
        temp = []
        for spline in curve_data.splines:
            for point in spline.points:
                # 获取顶点原位置
                vertex_co = curve_object.matrix_world @ mathutils.Vector(point.co[0:3])
                _, co, normal, _ = target_object.closest_point_on_mesh(vertex_co)
                temp.append((co[0:3], normal[0:3]))
        print(temp)


# 按钮
class Point_Button(bpy.types.Panel):
    bl_label = "按钮测试"
    bl_idname = "POINT_PT_Button"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TestButton"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("object.printmoban", text="打印模板")


_classes = [

    TEST_OT_addcurve,
    TEST_OT_dragcurve,
    TEST_OT_smoothcurve,
    TEST_OT_qiehuan,
    TEST_OT_resethmould,
    TEST_OT_finishmould,
    PointCut,
    PointFill,
    PrintMoban,
    Point_Button
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(addcurve_MyTool, separator=True, group=False)
    bpy.utils.register_tool(dragcurve_MyTool, separator=True,
                            group=False, after={addcurve_MyTool.bl_idname})
    bpy.utils.register_tool(smoothcurve_MyTool, separator=True,
                            group=False, after={dragcurve_MyTool.bl_idname})
    bpy.utils.register_tool(resetmould_MyTool, separator=True,
                            group=False, after={smoothcurve_MyTool.bl_idname})
    bpy.utils.register_tool(finishmould_MyTool, separator=True,
                            group=False, after={resetmould_MyTool.bl_idname})
    bpy.utils.register_tool(addcurve_MyTool3)

    bpy.utils.register_tool(addcurve_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(dragcurve_MyTool2, separator=True,
                            group=False, after={addcurve_MyTool2.bl_idname})
    bpy.utils.register_tool(smoothcurve_MyTool2, separator=True,
                            group=False, after={dragcurve_MyTool2.bl_idname})
    bpy.utils.register_tool(resetmould_MyTool2, separator=True,
                            group=False, after={smoothcurve_MyTool2.bl_idname})
    bpy.utils.register_tool(finishmould_MyTool2, separator=True,
                            group=False, after={resetmould_MyTool2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(addcurve_MyTool)
    bpy.utils.unregister_tool(dragcurve_MyTool)
    bpy.utils.unregister_tool(smoothcurve_MyTool)
    bpy.utils.unregister_tool(resetmould_MyTool)
    bpy.utils.unregister_tool(finishmould_MyTool)
    bpy.utils.unregister_tool(addcurve_MyTool3)

    bpy.utils.unregister_tool(addcurve_MyTool2)
    bpy.utils.unregister_tool(dragcurve_MyTool2)
    bpy.utils.unregister_tool(smoothcurve_MyTool2)
    bpy.utils.unregister_tool(resetmould_MyTool2)
    bpy.utils.unregister_tool(finishmould_MyTool2)
