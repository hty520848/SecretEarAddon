import bpy
import bmesh
import mathutils
from bpy_extras import view3d_utils
from math import sqrt, fabs
from mathutils import Vector
from .bottom_ring import boolean_apply, cut_bottom_part
from .dig_hole import boolean_dig, get_hole_border, get_order_border_vert
from .soft_eardrum.thickness_and_fill import set_finish, get_fill_plane, fill
from .soft_eardrum.soft_eardrum import soft_eardrum, get_cut_plane, plane_cut, delete_useless_part
from ..tool import recover_and_remind_border, moveToRight, utils_re_color, generate_cutplane, convert_to_mesh, \
    recover_to_dig
import re

prev_on_object = False
prev_mesh_name = ''


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


class MuJudict:  # Todo :切换时需要删除物体
    ruanermolist = ['BottomRingBorderR', 0.3]
    ruanermodict = {'meshBottomRingBorderR': ruanermolist}
    yingermodict = {}
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
        tempkuangjialist = [add_curve_name, 0.18, 2]
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

    # 细分曲线，添加控制点
    bpy.ops.curve.select_all(action='DESELECT')
    for i in range(index_initial, end_point, 1):  # 选中原本在第二条曲线上的点
        new_curve_data.splines[0].points[i].select = True
    bpy.ops.curve.subdivide(number_cuts=3)  # 细分次数
    bpy.ops.object.mode_set(mode='OBJECT')
    snaptoobject(curve_name)  # 将曲线吸附到物体上
    moveToRight(new_curve_obj)


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
        set_finish(True)
        bpy.ops.object.select_all(action='DESELECT')
        recover_and_remind_border()
        generate_cutplane()  # 生成曲线
        # soft_eardrum()
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

        get_fill_plane()
        fill()
        utils_re_color("右耳", (1, 0.319, 0.133))
        utils_re_color("右耳huanqiecompare", (1, 0.319, 0.133))

        convert_to_mesh(curve_name, mesh_name, depth)  # 重新生成网格
        set_finish(False)

    if (enum_name == '框架式耳膜'):
        if (re.match('HoleBorderCurve', curve_name) != None):  # 上部曲线改变
            recover_to_dig()
            number = 0
            for obj in bpy.data.objects:
                if re.match('HoleBorderCurve', obj.name) != None:
                    number += 1
            while (number > 0):
                local_curve_name = 'HoleBorderCurve' + str(number)
                dig_border = []
                for point in bpy.data.objects[local_curve_name].data.splines[0].points:
                    dig_border.append(point.co[0:3])
                template_highest_point = (-10.3681, 2.2440, 12.1771)
                get_hole_border(template_highest_point, dig_border)
                boolean_dig()
                bpy.data.objects.remove(bpy.data.objects['HoleBorderCurve'], do_unlink=True)
                bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
                number -= 1

            for obj in bpy.data.objects:
                if re.match('HoleBorderCurve', obj.name) != None:
                    local_mesh_name = 'mesh' + obj.name
                    convert_to_mesh(obj.name, local_mesh_name, depth)  # 重新生成网格

            utils_re_color("右耳", (1, 0.319, 0.133))

        else:  # 下部曲线改变
            recover_and_remind_border()
            generate_cutplane()
            soft_eardrum()

            number = 0
            for obj in bpy.data.objects:
                if re.match('HoleBorderCurve', obj.name) != None:
                    number += 1
            while (number > 0):
                local_curve_name = 'HoleBorderCurve' + str(number)
                dig_border = []
                for point in bpy.data.objects[local_curve_name].data.splines[0].points:
                    dig_border.append(point.co[0:3])
                template_highest_point = (-10.3681, 2.2440, 12.1771)
                get_hole_border(template_highest_point, dig_border)
                boolean_dig()
                bpy.data.objects.remove(bpy.data.objects['HoleBorderCurve'], do_unlink=True)
                bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
                number -= 1

            for obj in bpy.data.objects:
                if re.match('HoleBorderCurve', obj.name) != None:
                    local_mesh_name = 'mesh' + obj.name
                    convert_to_mesh(obj.name, local_mesh_name, depth)  # 重新生成网格

            utils_re_color("右耳", (1, 0.319, 0.133))


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
    for i in range(0, 3, 1):
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


def initialBlueColor():
    ''' 生成蓝色材质 '''
    material = bpy.data.materials.new(name="blue")
    material.use_nodes = True
    bpy.data.materials["blue"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        0, 0, 1, 1.0)
    material.blend_method = "BLEND"
    material.use_backface_culling = True


def checkinitialBlueColor():
    ''' 确认是否生成蓝色材质 '''
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'blue':
            return True
    return False


def initialGreenColor():
    ''' 生成绿色材质 '''
    material = bpy.data.materials.new(name="green")
    material.use_nodes = True
    bpy.data.materials["green"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        0, 1, 0, 1.0)
    material.blend_method = "BLEND"
    material.use_backface_culling = True


def checkinitialGreenColor():
    ''' 确认是否生成绿色材质 '''
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'green':
            return True
    return False


def checkcopycurve(curve_name):
    ''' 确认是否有复制曲线 '''
    objects = bpy.data.objects
    copy_name = 'select' + curve_name
    for object in objects:
        if object.name == copy_name:
            return True
    return False


def checkdragcurve():
    ''' 确认是否有拖拽曲线 '''
    objects = bpy.data.objects
    drag_name = 'dragcurve'
    for object in objects:
        if object.name == drag_name:
            return True
    return False


def checkaddcurve():
    ''' 确认是否有新增曲线 '''
    objects = bpy.data.objects
    for object in objects:
        if object.name == 'point':
            return True
    return False


def copy_select_curve(curve_name):
    ''' 复制曲线数据 '''
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[curve_name]
    new_name = 'select' + curve_name
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
    select_name = 'select' + curve_name
    if checkcopycurve(curve_name) == True:
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
    if checkinitialGreenColor() == False:
        initialGreenColor()
    bpy.data.objects['dragcurve'].data.materials.append(bpy.data.materials['green'])
    moveToRight(bpy.data.objects['dragcurve'])
    bpy.context.view_layer.objects.active = bpy.data.objects['dragcurve']
    bpy.context.object.data.bevel_depth = depth
    bpy.ops.object.select_all(action='DESELECT')


def selectcurve(context, event, curve_name, mesh_name, depth, number):
    ''' 选择拖拽曲线对象 '''

    select_name = 'select' + curve_name
    if checkcopycurve(curve_name) == True:
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
    if checkinitialGreenColor() == False:
        initialGreenColor()
    bpy.data.objects['dragcurve'].data.materials.append(bpy.data.materials['green'])
    moveToRight(bpy.data.objects['dragcurve'])
    bpy.context.view_layer.objects.active = bpy.data.objects['dragcurve']
    bpy.context.object.data.bevel_depth = depth
    bpy.ops.object.select_all(action='DESELECT')
    return index


def movecurve(co, initial_co, curve_name, index, number):
    curve_obj = bpy.data.objects[curve_name]
    bpy.context.view_layer.objects.active = curve_obj
    curve_data = curve_obj.data
    dis = (co - initial_co).normalized()  # 距离向量
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points)
    start_index = (index - number + point_number) % point_number
    finish_index = (index + number + point_number) % point_number
    if (start_index < finish_index):
        curve_number, mid_index = get_len(start_index, finish_index, point_number)
        for i in range(start_index, finish_index, 1):
            point = curve_data.splines[0].points[i]
            point.co[0:3] = Vector(point.co[0:3]) + dis * disfunc(abs(i - mid_index), curve_number)
            point.co[3] = 1
    else:
        curve_number, mid_index = get_len(start_index, finish_index, point_number)
        for i in range(start_index, point_number, 1):
            if (curve_number == 0):
                break
            if (i - mid_index >= curve_number):
                insert_index = point_number - i + mid_index
            else:
                insert_index = i - mid_index
            point = curve_data.splines[0].points[i]
            point.co[0:3] = Vector(point.co[0:3]) + dis * disfunc(insert_index, curve_number)
            point.co[3] = 1
        for i in range(0, finish_index, 1):
            if (curve_number == 0):
                break
            point = curve_data.splines[0].points[i]
            point.co[0:3] = Vector(point.co[0:3]) + dis * disfunc(insert_index, curve_number)
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
    select_name = 'select' + curve_name
    bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)
    new_curve_obj.name = curve_name

    bpy.context.view_layer.objects.active = new_curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    new_curve_obj.select_set(state=True)
    new_curve_obj.data.materials.clear()
    new_curve_obj.data.materials.append(bpy.data.materials['blue'])
    bpy.context.object.data.bevel_depth = depth
    bpy.context.object.data.dimensions = '3D'


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
                        idx = len(curve_obj.data.splines[0].points) - 1
                        bpy.ops.curve.select_all(action='DESELECT')
                        curve_obj.data.splines[0].points[idx].select = True
                        bpy.ops.curve.delete(type='VERT')
                        curve_obj.data.splines[0].use_cyclic_u = True
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # 将曲线转换成网格，切割
                        local_curve_name = curve_obj.name
                        local_mesh_name = 'mesh' + curve_obj.name
                        update_cut(local_curve_name, local_mesh_name, 0.18)

        else:
            if bpy.context.mode == 'OBJECT':  # 如果处于物体模式下，蓝线双击开始绘制
                co, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
                op_cls.__curve_name = curve_list[0]
                op_cls.__depth = curve_list[1]
                curve_obj = bpy.data.objects[op_cls.__curve_name]
                bpy.context.view_layer.objects.active = curve_obj
                bpy.ops.object.select_all(action='DESELECT')
                curve_obj.select_set(state=True)
                op_cls.__index_initial = select_nearest_point(op_cls.__curve_name, co)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                curve_obj.data.splines[0].points[op_cls.__index_initial].select = True
                bpy.ops.curve.separate()  # 分离将要进行操作的点
                bpy.ops.object.mode_set(mode='OBJECT')
                for object in bpy.data.objects:  # 改名
                    copy_name = op_cls.__curve_name + '.001'
                    if object.name == copy_name:
                        object.name = 'point'
                        break
                bpy.context.view_layer.objects.active = bpy.data.objects['point']
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects['point'].select_set(state=True)

                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式进行操作
                bpy.ops.curve.select_all(action='SELECT')
                bpy.context.object.data.bevel_depth = op_cls.__depth  # 设置倒角深度
                bpy.data.objects['point'].data.materials.append(
                    bpy.data.materials['blue'])
                # 开启吸附
                bpy.context.scene.tool_settings.use_snap = True
                bpy.context.scene.tool_settings.snap_elements = {'FACE'}
                bpy.context.scene.tool_settings.snap_target = 'CLOSEST'
                bpy.context.scene.tool_settings.use_snap_align_rotation = True
                bpy.context.scene.tool_settings.use_snap_backface_culling = True
                bpy.ops.wm.tool_set_by_id(name="builtin.extrude_cursor")

            elif bpy.context.mode == 'EDIT_CURVE':  # 如果处于编辑模式下，蓝线双击确认完成
                print("起始位置的下标是", op_cls.__index_initial)
                co = cal_co(op_cls.__mesh_name, context, event)
                op_cls.__index_finish = select_nearest_point(op_cls.__curve_name, co)
                print("结束的下标是", op_cls.__index_initial)
                bpy.ops.object.mode_set(mode='OBJECT')  # 返回对象模式
                bpy.context.scene.tool_settings.use_snap = False  # 取消吸附
                join_object(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth, op_cls.__index_initial,
                            op_cls.__index_finish)  # 合并曲线
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                set_finish(False)
            else:
                pass

    def invoke(self, context, event):
        op_cls = TEST_OT_addcurve
        if checkinitialBlueColor() == False:
            initialBlueColor()
        self.excute(context, event)
        set_finish(True)

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
        if checkinitialGreenColor() == False:
            initialGreenColor()
        if checkinitialBlueColor() == False:
            initialBlueColor()
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
        op_cls.__is_modifier_right = False

        op_cls.__prev_mouse_location_x = -1
        op_cls.__prev_mouse_location_y = -1

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
                if op_cls.__is_moving == True:  # 鼠标左键松开
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
            if op_cls.__right_mouse_down == False:
                if checkcopycurve(op_cls.__curve_name) == True and op_cls.__left_mouse_down == False \
                        and op_cls.__is_modifier_right == False and op_cls.__is_modifier == False:
                    select_name = 'select' + op_cls.__curve_name
                    bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
                    bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            if op_cls.__right_mouse_down == True:  # 鼠标右键按下
                min_number = int(op_cls.__curve_length * 0.1)
                max_number = int(op_cls.__curve_length * 0.8)
                op_cls.__is_modifier_right = True
                op_cls.__now_mouse_x_right = event.mouse_region_x
                op_cls.__now_mouse_y_right = event.mouse_region_y
                dis = int(sqrt(fabs(op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) * fabs(
                    op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) + fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right) * fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right)) / 10)  # 鼠标移动的距离
                if (dis > 2):
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
                if co != -1 and (op_cls.__prev_mouse_location_x != event.mouse_region_x or \
                                 op_cls.__prev_mouse_location_y != event.mouse_region_y):
                    op_cls.__prev_mouse_location_x = event.mouse_region_x
                    op_cls.__prev_mouse_location_y = event.mouse_region_y
                    if (co - op_cls.__initial_co).dot(co - op_cls.__initial_co) >= 0.2:
                        movecurve(co, op_cls.__initial_co, op_cls.__curve_name, op_cls.__index, op_cls.__number)
                        snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number)  # 将曲线吸附到物体上
                        op_cls.__initial_co = co
            if op_cls.__left_mouse_down == False:
                # 重新切割
                if checkcopycurve(op_cls.__curve_name) == False and op_cls.__is_modifier == True:
                    # join_dragcurve(op_cls.__curve_name,op_cls.__depth)
                    update_cut(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                    op_cls.__is_modifier = False
                    op_cls.__is_modifier_right = False
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            return {'PASS_THROUGH'}

        else:
            global prev_mesh_name
            _, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
            if (
                    prev_mesh_name != op_cls.__mesh_name and op_cls.__is_modifier == False and op_cls.__is_modifier_right == False) or op_cls.__curve_name == '':
                prev_mesh_name = op_cls.__mesh_name
                op_cls.__curve_name = curve_list[0]
                op_cls.__depth = curve_list[1]
                op_cls.__curve_length = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                op_cls.__number = int(op_cls.__curve_length * 0.2)
            if event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    op_cls.__is_moving = True
                    op_cls.__left_mouse_down = True
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                    if (checkcopycurve(op_cls.__curve_name) == True):
                        select_name = 'select' + op_cls.__curve_name
                        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
                        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                elif event.value == 'RELEASE':
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
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
            elif event.type == 'MOUSEMOVE' and op_cls.__left_mouse_down == False and op_cls.__right_mouse_down == False:  # 鼠标移动时选择不同的曲线区域
                if (
                        op_cls.__prev_mouse_location_x != event.mouse_region_x or op_cls.__prev_mouse_location_y != event.mouse_region_y):
                    op_cls.__prev_mouse_location_x = event.mouse_region_x
                    op_cls.__prev_mouse_location_y = event.mouse_region_y
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
        print('smoothcurve invoke')
        bpy.context.scene.var = 21
        if checkinitialGreenColor() == False:
            initialGreenColor()
        if checkinitialBlueColor() == False:
            initialBlueColor()
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
        op_cls.__is_modifier_right = False

        op_cls.__prev_mouse_location_x = -1
        op_cls.__prev_mouse_location_y = -1

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
                if op_cls.__is_moving == True:  # 鼠标左键松开
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
                    op_cls.__now_mouse_x = None
                    op_cls.__now_mouse_y = None
            if op_cls.__right_mouse_down == False:
                if checkcopycurve(op_cls.__curve_name) == True and op_cls.__left_mouse_down == False \
                        and op_cls.__is_modifier == False and op_cls.__is_modifier_right == False:
                    select_name = 'select' + op_cls.__curve_name
                    bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
                    bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            if op_cls.__right_mouse_down == True:  # 鼠标右键按下
                min_number = int(op_cls.__curve_length * 0.1)
                max_number = int(op_cls.__curve_length * 0.8)
                op_cls.__is_modifier_right = True
                op_cls.__now_mouse_x_right = event.mouse_region_x
                op_cls.__now_mouse_y_right = event.mouse_region_y
                dis = int(sqrt(fabs(op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) * fabs(
                    op_cls.__now_mouse_y_right - op_cls.__initial_mouse_y_right) + fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right) * fabs(
                    op_cls.__now_mouse_x_right - op_cls.__initial_mouse_x_right)) / 10)  # 鼠标移动的距离
                if (dis > 2):
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
                if (dis > 2):
                    smoothcurve(op_cls.__curve_name, op_cls.__index, op_cls.__number)
                    snapselect(op_cls.__curve_name, op_cls.__index, op_cls.__number)  # 将曲线吸附到物体上
                    op_cls.__initial_mouse_x = op_cls.__now_mouse_x  # 重新开始检测
                    op_cls.__initial_mouse_y = op_cls.__now_mouse_y
            if op_cls.__left_mouse_down == False:
                # 吸附，重新切割
                if checkcopycurve(op_cls.__curve_name) == False and op_cls.__is_modifier == True:
                    # join_dragcurve(op_cls.__curve_name, op_cls.__depth)
                    update_cut(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                    op_cls.__is_modifier = False
                    op_cls.__is_modifier_right = False
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            return {'PASS_THROUGH'}

        else:
            global prev_mesh_name
            _, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
            if (
                    prev_mesh_name != op_cls.__mesh_name and op_cls.__is_modifier == False and op_cls.__is_modifier_right == False) or op_cls.__curve_name == '':
                prev_mesh_name = op_cls.__mesh_name
                op_cls.__curve_name = curve_list[0]
                op_cls.__depth = curve_list[1]
                op_cls.__curve_length = len(bpy.data.objects[op_cls.__curve_name].data.splines[0].points)
                op_cls.__number = int(op_cls.__curve_length * 0.2)
            if event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    op_cls.__is_moving = True
                    op_cls.__left_mouse_down = True
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                    if (checkcopycurve(op_cls.__curve_name) == True):
                        select_name = 'select' + op_cls.__curve_name
                        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
                        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                elif event.value == 'RELEASE':
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
                    op_cls.__now_mouse_x = None
                    op_cls.__now_mouse_y = None
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
            elif event.type == 'MOUSEMOVE' and op_cls.__left_mouse_down == False and op_cls.__right_mouse_down == False:  # 鼠标移动时选择不同的曲线区域
                if (
                        op_cls.__prev_mouse_location_x != event.mouse_region_x or op_cls.__prev_mouse_location_y != event.mouse_region_y):
                    op_cls.__prev_mouse_location_x = event.mouse_region_x
                    op_cls.__prev_mouse_location_y = event.mouse_region_y
                    op_cls.__index = selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name,
                                                 op_cls.__depth, op_cls.__number)

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


_classes = [

    TEST_OT_addcurve,
    TEST_OT_dragcurve,
    TEST_OT_smoothcurve,
    TEST_OT_qiehuan
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
