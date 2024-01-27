import bpy
import bmesh
import mathutils
from bpy_extras import view3d_utils
from math import sqrt, fabs
from mathutils import Vector
from .bottom_ring import boolean_apply, cut_bottom_part

index_initial = -1  # 记录第一次点击蓝线时的下标索引
index_finish = -1  # 记录结束时点击蓝线的的下标索引
curve_name = ''  # 记录第一次点击蓝线时的曲线名字
mesh_name = ''  # 记录第一次点击蓝线时的物体名字
depth = 0  # 记录第一次点击蓝线时曲线的深度

index = -1  # 记录拖拽曲线时曲线中心点的下标
number = 10  # 记录拖拽曲线时上一次选中曲线控制点的数量

prev_on_object = False


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


def get_dic_name():
    ''' 获得当前磨具类型的曲线字典 '''

    ruanermolist = ['BottomRingBorderR', 0.3]
    ruanermodict = {'meshBottomRingBorderR': ruanermolist}
    yingermodict = {}
    yitidict = {}
    kuangjialist1 = ['BottomRingBorderR', 0.4]
    kuangjialist2 = ['HoleBorderCurveR', 0.18]
    kuangjiadict = {'meshBottomRingBorderR': kuangjialist1, 'meshHoleBorderCurveR': kuangjialist2}
    waikedict = {}
    mianbandict = {}

    mujudict = {'软耳模': ruanermodict,
                '硬耳膜': yingermodict,
                '一体外壳': yitidict,
                '框架式耳膜': kuangjiadict,
                '常规外壳': waikedict,
                '实心面板': mianbandict}

    enum = bpy.context.scene.muJuNameEnum
    return mujudict[enum]


def co_on_object(dic, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param dic: 要检测物体的字典
    :return: 相交的坐标、相交物体和对应曲线的名字
    '''
    dic = get_dic_name()
    dismin = float('inf')
    mesh_name = None
    flag = 0
    for key in dic:
        active_obj = bpy.data.objects[key]
        co = []

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

                co, _, fidx, dis = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    flag = 1
                    if (dis < dismin):
                        dismin = dis
                        mesh_name = key
    if (flag == 1):
        return (co, mesh_name, dic[mesh_name])  # 如果发生交叉，返回坐标的值和物体的名字
    else:
        return -1


def co_on_object(dic, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param dic: 要检测物体的字典
    :return: 相交的坐标、相交物体的名字和对应曲线的列表
    '''
    dic = get_dic_name()
    dismin = float('inf')
    mesh_name = None
    flag = 0
    for key in dic:
        active_obj = bpy.data.objects[key]
        co = []

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

                co, _, fidx, dis = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    flag = 1
                    if (dis < dismin):
                        dismin = dis
                        mesh_name = key
    if (flag == 1):
        return (co, mesh_name, dic[mesh_name])  # 如果发生交叉，返回
    else:
        return -1


def cal_co(mesh_name, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param mesh_name: 要检测物体的名字
    :return: 相交的坐标
    '''

    active_obj = bpy.data.objects[mesh_name]
    co = []

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

            co, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
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
            distance = sqrt(sum((a - b) ** 2 for a, b in zip(point.co, co)))
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
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.points.add(len(spline.points) - 1)
        new_spline.use_cyclic_u = True
        new_spline.use_smooth = True
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def join_curve(curve_name, depth):
    '''
    合并曲线(添加蓝线point后)
    :param curve_name: 曲线名字
    :param depth: 曲线倒角深度
    '''
    global index_initial
    global index_finish

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


def convert_tomesh(curve_name, mesh_name, depth):
    '''
    将曲线转化成网格
    :param curve_name:曲线名字
    :param mesh_name:曲线对应的网格名字
    :param depth:曲线倒角深度
    '''
    copy_curve(curve_name)  # 复制一份曲线数据
    bpy.data.objects.remove(bpy.data.objects[mesh_name], do_unlink=True)  # 删除原有蓝线网格
    new_name = "new" + curve_name
    obj = bpy.data.objects[new_name]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = depth  # 设置曲线倒角深度
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    obj.data.materials.append(bpy.data.materials['blue'])
    obj.name = mesh_name


def join_object(curve_name, mesh_name, depth):
    ''' 合并曲线并转化成网格用于下一次操作 '''

    join_curve(curve_name, depth)  # 合并曲线
    convert_tomesh(curve_name, mesh_name, depth)  # 将曲线转化成网格


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


def snapselect(curve_name):
    ''' 将选中的曲线部分吸附到最近的顶点上 '''
    # 获取曲线对象
    curve_object = bpy.data.objects[curve_name]
    # 获取目标物体
    target_object = bpy.data.objects["右耳MouldReset"]
    # 获取数据
    curve_data = curve_object.data

    # 将曲线的每个顶点吸附到目标物体的表面
    for i in range(index - number, index + number, 1):
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
    ''' 确认是否有拖拽曲线 '''
    objects = bpy.data.objects
    drag_name = 'select' + curve_name
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
    new_obj = bpy.data.objects.new(new_name, new_curve)
    bpy.context.collection.objects.link(new_obj)

    # 复制源曲线的数据到新曲线
    new_curve.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = new_curve.splines.new(spline.type)
        new_spline.points.add(len(spline.points) - 1)
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def selectcurve(context, event, curve_name, mesh_name, depth):
    ''' 选择拖拽曲线对象 '''
    global number
    global index

    select_name = 'select' + curve_name
    if checkcopycurve(curve_name) == True:
        bpy.data.objects.remove(bpy.data.objects[select_name], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
    point_number = len(bpy.data.objects[curve_name].data.splines[0].points) - 1
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

    if (index - number) <= 0:  # 防止越界
        index = number
    if (index + number) >= point_number:
        index = point_number - number
    for i in range(index - number, index + number, 1):
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
    bpy.data.objects['dragcurve'].data.materials.append(bpy.data.materials['green'])
    bpy.context.view_layer.objects.active = bpy.data.objects['dragcurve']
    bpy.context.object.data.bevel_depth = depth
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['dragcurve'].select_set(state=True)


def movecurve(co, initial_co, curve_name):
    global index
    global number
    curve_obj = bpy.data.objects[curve_name]
    curve_data = curve_obj.data
    dis = (co - initial_co).normalized()  # 距离向量
    for i in range(index - number, index + number, 1):
        point = curve_data.splines[0].points[i]
        point.co[0:3] = Vector(point.co[0:3]) + dis * disfunc(abs(int(i - index)), number)
        point.co[3] = 1


def get_co(curve_name):
    global index
    curve_obj = bpy.data.objects[curve_name]
    curve_data = curve_obj.data
    return Vector(curve_data.splines[0].points[index].co[0:3])


def disfunc(x, y):
    out = round(x / y, 2)
    return round(sqrt(1 - out), 2)


def join_dragcurve(curve_name, depth):
    ''' 合并拖拽或平滑后的曲线 '''
    global index
    global number

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


def smoothcurve():
    curve_obj = bpy.data.objects['dragcurve']
    bpy.context.view_layer.objects.active = curve_obj
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.smooth()  # 平滑曲线
    bpy.ops.object.mode_set(mode='OBJECT')


class TEST_OT_addcurve(bpy.types.Operator):
    bl_idname = "object.addcurve"
    bl_label = "addcurve"
    bl_description = "双击蓝线改变蓝线形态"

    def excute(self, context, event):
        global index_initial
        global index_finish
        global curve_name
        global mesh_name
        global depth
        mujudict = get_dic_name()

        if co_on_object(mujudict, context, event) == -1:  # 双击位置不在曲线上不做任何事
            print("不在曲线上")

        else:
            if bpy.context.mode == 'OBJECT':  # 如果处于物体模式下，蓝线双击开始绘制
                co, mesh_name, curve_list = co_on_object(mujudict, context, event)
                curve_name = curve_list[0]
                depth = curve_list[1]
                index = select_nearest_point(curve_name, co)
                print("在曲线上最近点的下标是", index)
                index_initial = index
                curve_obj = bpy.data.objects[curve_name]
                bpy.context.view_layer.objects.active = curve_obj
                bpy.ops.object.select_all(action='DESELECT')
                curve_obj.select_set(state=True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                curve_obj.data.splines[0].points[index].select = True
                bpy.ops.curve.separate()  # 分离将要进行操作的点
                bpy.ops.object.mode_set(mode='OBJECT')
                for object in bpy.data.objects:  # 改名
                    copy_name = curve_name + '.001'
                    if object.name == copy_name:
                        object.name = 'point'
                        break
                bpy.context.view_layer.objects.active = bpy.data.objects['point']
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects['point'].select_set(state=True)

                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式进行操作
                bpy.ops.curve.select_all(action='SELECT')
                bpy.context.object.data.bevel_depth = depth  # 设置倒角深度
                bpy.data.objects['point'].data.materials.append(
                    bpy.data.materials['blue'])
                # 开启吸附
                bpy.context.scene.tool_settings.use_snap = True
                bpy.context.scene.tool_settings.snap_elements = {'FACE'}
                bpy.context.scene.tool_settings.snap_target = 'CLOSEST'
                bpy.context.scene.tool_settings.use_snap_align_rotation = True
                bpy.context.scene.tool_settings.use_snap_backface_culling = True
                bpy.ops.object.pointqiehuan('INVOKE_DEFAULT')

            elif bpy.context.mode == 'EDIT_CURVE':  # 如果处于编辑模式下，蓝线双击确认完成
                print("起始位置的下标是", index_initial)
                co = cal_co(mesh_name, context, event)
                index_finish = select_nearest_point(curve_name, co)
                print("在曲线上最近点的下标是", index_finish)
                bpy.ops.object.mode_set(mode='OBJECT')  # 返回对象模式
                bpy.context.scene.tool_settings.use_snap = False  # 取消吸附
                join_object(curve_name, mesh_name, depth)  # 合并曲线
                # boolean_apply()
                # cut_bottom_part()
            else:
                pass

    def invoke(self, context, event):
        if checkinitialBlueColor() == False:
            initialBlueColor()
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_qiehuan(bpy.types.Operator):
    bl_idname = "object.pointqiehuan"
    bl_label = "pointqiehuan"
    bl_description = "鼠标行为切换"

    def invoke(self, context, event):  # 初始化
        print('pointqiehuan invoke')
        bpy.ops.wm.tool_set_by_id(name="builtin.extrude_cursor")  # 调用挤出至光标工具
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if checkaddcurve() == False:
            print('pointqiehuan finish')
            return {'FINISHED'}
        elif cal_co('右耳MouldReset', context, event) != -1 and is_changed(context, event) == True:
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
    __depth = 0
    __initial_co = None

    def invoke(self, context, event):  # 初始化
        bpy.context.scene.var = 19
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
        op_cls.__depth = 0
        op_cls.__initial_co = None

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TEST_OT_dragcurve
        mujudict = get_dic_name()
        if bpy.context.scene.var != 19:
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
                global number
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
                    number += dis  # 根据鼠标移动的距离扩大或缩小选区
                    if (number < 10):  # 防止选不到点弹出报错信息
                        number = 10
                    if (number > 200):  # 设置最大值
                        number = 200
                    selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
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
                        movecurve(co, op_cls.__initial_co, op_cls.__curve_name)
                        snapselect(op_cls.__curve_name)  # 将曲线吸附到物体上
                        op_cls.__initial_co = co
            if op_cls.__left_mouse_down == False:
                # 重新切割
                if checkcopycurve(op_cls.__curve_name) == True and op_cls.__is_modifier == True:
                    # join_dragcurve(op_cls.__curve_name,op_cls.__depth)
                    convert_tomesh(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    bpy.data.objects[op_cls.__mesh_name].hide_set(False)
                    op_cls.__is_modifier = False
                    op_cls.__is_modifier_right = False
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            return {'PASS_THROUGH'}

        else:
            _, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
            op_cls.__curve_name = curve_list[0]
            op_cls.__depth = curve_list[1]
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
                    selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    op_cls.__initial_co = get_co(op_cls.__curve_name)

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

    def invoke(self, context, event):  # 初始化
        print('smoothcurve invoke')
        bpy.context.scene.var = 20
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
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # 右键选区，左键平滑
        op_cls = TEST_OT_smoothcurve
        mujudict = get_dic_name()
        if bpy.context.scene.var != 20:
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
                global number
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
                    number += dis  # 根据鼠标移动的距离扩大或缩小选区
                    if (number < 10):  # 防止选不到点弹出报错信息
                        number = 10
                    if (number > 200):  # 设置最大值
                        number = 200
                    selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    op_cls.__initial_mouse_x_right = op_cls.__now_mouse_x_right  # 重新开始检测
                    op_cls.__initial_mouse_y_right = op_cls.__now_mouse_y_right
            if op_cls.__left_mouse_down == True:  # 鼠标左键按下
                bpy.data.objects[op_cls.__mesh_name].hide_set(True)
                op_cls.__is_modifier = True
                op_cls.__now_mouse_x = event.mouse_region_x
                op_cls.__now_mouse_y = event.mouse_region_y
                dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                    op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                    op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                    op_cls.__now_mouse_x - op_cls.__initial_mouse_x)) / 10)  # 鼠标移动的距离
                if (dis > 2):
                    smoothcurve()
                    op_cls.__initial_mouse_x = op_cls.__now_mouse_x  # 重新开始检测
                    op_cls.__initial_mouse_y = op_cls.__now_mouse_y
            if op_cls.__left_mouse_down == False:
                # 吸附，重新切割
                if checkcopycurve(op_cls.__curve_name) == True and op_cls.__is_modifier == True:
                    snaptoobject('dragcurve')
                    join_dragcurve(op_cls.__curve_name, op_cls.__depth)
                    convert_tomesh(op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)
                    op_cls.__is_modifier = False
                    op_cls.__is_modifier_right = False

            return {'PASS_THROUGH'}

        else:
            _, op_cls.__mesh_name, curve_list = co_on_object(mujudict, context, event)
            op_cls.__curve_name = curve_list[0]
            op_cls.__depth = curve_list[1]
            if event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    op_cls.__is_moving = True
                    op_cls.__left_mouse_down = True
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
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
                    if op_cls.__is_modifier == False:
                        selectcurve(context, event, op_cls.__curve_name, op_cls.__mesh_name, op_cls.__depth)

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
    bl_icon = "ops.curve.pen"
    bl_widget = None
    bl_keymap = (
        ("object.addcurve", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'},
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
    bl_icon = "ops.curve.radius"
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
    bl_icon = "ops.curve.vertex_random"
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
    bpy.utils.register_tool(addcurve_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(dragcurve_MyTool, separator=True,
                            group=False, after={addcurve_MyTool.bl_idname})
    bpy.utils.register_tool(smoothcurve_MyTool, separator=True,
                            group=False, after={dragcurve_MyTool.bl_idname})
    bpy.utils.register_tool(resetmould_MyTool, separator=True,
                            group=False, after={smoothcurve_MyTool.bl_idname})
    bpy.utils.register_tool(finishmould_MyTool, separator=True,
                            group=False, after={resetmould_MyTool.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(addcurve_MyTool)
    bpy.utils.unregister_tool(addcurve_MyTool2)
    bpy.utils.unregister_tool(dragcurve_MyTool)
    bpy.utils.unregister_tool(smoothcurve_MyTool)
    bpy.utils.unregister_tool(resetmould_MyTool)
    bpy.utils.unregister_tool(finishmould_MyTool)
