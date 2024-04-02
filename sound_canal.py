import bpy
import bmesh
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
from math import sqrt
from .tool import newShader, moveToRight, utils_re_color, delete_useless_object, newColor
import re

prev_on_object = 0
prev_on_object_old = False
prev_on_object_now = False
number = 0  # 记录管道控制点点的个数
object_dic = {}  # 记录当前圆球以及对应控制点
soundcanal_data = []  # 记录当前控制点的坐标
soundcanal_finish = False


def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.use_backface_culling = True
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.4


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


def on_which_shpere(context, event):
    '''
    判断鼠标在哪个圆球上
    '''
    global object_dic

    for key in object_dic:
        active_obj = bpy.data.objects[key]
        object_index = int(key.replace('soundcanalsphere', ''))

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
            if (active_obj.mode == 'OBJECT'):
                mesh = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    return object_index

    return 0


def is_mouse_on_object(name, context, event):
    active_obj = bpy.data.objects[name]

    is_on_object = False  # 初始化变量

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
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


def is_changed_old(context, event):
    ''' 创建圆球前鼠标位置的判断 '''
    curr_on_object_old = is_mouse_on_object('右耳', context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_old  # 之前鼠标在那个物体上
    if (curr_on_object_old != prev_on_object_old):
        prev_on_object_old = curr_on_object_old
        return True
    else:
        return False


def is_changed_now(context, event):
    ''' 创建圆球后鼠标位置的判断 '''
    curr_on_object_now = is_mouse_on_object('meshsoundcanal', context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_now  # 之前鼠标在那个物体上
    if (curr_on_object_now != prev_on_object_now):
        prev_on_object_now = curr_on_object_now
        return True
    else:
        return False


def is_changed(context, event):
    curr_on_object = on_which_shpere(context, event)  # 当前鼠标在哪个物体上
    global prev_on_object  # 之前鼠标在那个物体上

    if (curr_on_object != prev_on_object):
        prev_on_object = curr_on_object
        return True
    else:
        return False


def cal_co(name, context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :param name: 要检测物体的名字
    :return: 相交的坐标
    '''

    active_obj = bpy.data.objects[name]
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

            co, _, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None:
                return co  # 如果发生交叉，返回坐标的值

    return -1


def select_nearest_point(co):
    '''
    选择曲线上离坐标位置最近的两个点
    :param co: 坐标的值
    :return: 最近两个点的坐标以及要插入的下标
    '''
    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects['soundcanal']
    # 获取曲线的数据
    curve_data = curve_obj.data
    # 遍历曲线的所有点
    min_dis = float('inf')
    min_dis_index = -1

    length = len(curve_data.splines[0].points) 
        
    for spline in curve_data.splines:
        for point_index, point in enumerate(spline.points):
            # 计算点与给定点之间的距离
            distance_vector = Vector(point.co[0:3]) - co
            distance = distance_vector.dot(distance_vector)
            # 更新最小距离和对应的点索引
            if distance < min_dis:
                min_dis = distance
                min_dis_index = point_index

    if min_dis_index == 0:
        return (Vector(curve_data.splines[0].points[0].co[0:3]), 
                Vector(curve_data.splines[0].points[1].co[0:3]), 1)
    
    elif min_dis_index == length - 1:
        return (Vector(curve_data.splines[0].points[length -2].co[0:3]), 
                Vector(curve_data.splines[0].points[length -1].co[0:3]), length -1)

    min_co = Vector(curve_data.splines[0].points[min_dis_index].co[0:3])
    secondmin_co = Vector(curve_data.splines[0].points[min_dis_index - 1].co[0:3])
    dis_vector1 = Vector(secondmin_co - co)
    dis_vector2 = Vector(min_co - co)
    if dis_vector1.dot(dis_vector2) < 0:
        insert_index = min_dis_index
    else:
        secondmin_co = Vector(curve_data.splines[0].points[min_dis_index + 1].co[0:3])
        insert_index = min_dis_index + 1
    return (min_co, secondmin_co, insert_index)


def copy_curve():
    ''' 复制曲线数据 '''
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects['soundcanal']
    target_curve = new_curve('meshsoundcanal')
    # 复制源曲线的数据到新曲线
    target_curve.data.splines.clear()
    for spline in source_curve.data.splines:
        new_spline = target_curve.data.splines.new(spline.type)
        new_spline.points.add(len(spline.points) - 1)
        new_spline.order_u = 2
        new_spline.use_smooth = True
        # new_spline.use_endpoint_u = True
        # new_spline.use_cyclic_u = True
        for i, point in enumerate(spline.points):
            new_spline.points[i].co = point.co


def convert_soundcanal():
    if (bpy.data.objects.get('meshsoundcanal')):
        bpy.data.objects.remove(bpy.data.objects['meshsoundcanal'], do_unlink=True)  # 删除原有网格
    copy_curve()
    duplicate_obj = bpy.data.objects['meshsoundcanal']
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    # while(bpy.context.active_object.modifiers):
    #     modifer_name = bpy.context.active_object.modifiers[0].name
    #     bpy.ops.object.modifier_apply(modifier = modifer_name)
    bpy.context.active_object.data.bevel_depth = bpy.context.scene.chuanShenGuanDaoZhiJing / 2  # 设置曲线倒角深度
    bpy.context.active_object.data.bevel_resolution = 16
    bpy.context.active_object.data.use_fill_caps = True  # 封盖
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    duplicate_obj.hide_select = True
    duplicate_obj.data.materials.clear()
    duplicate_obj.data.materials.append(bpy.data.materials["grey"])


def add_sphere(co, index):
    '''
    在指定位置生成圆球用于控制管道曲线的移动
    :param co:指定的坐标
    :param index:指定要钩挂的控制点的下标
    '''
    global number
    number += 1
    # 创建一个新的网格
    mesh = bpy.data.meshes.new("soundcanalsphere")
    name = 'soundcanalsphere' + str(number)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    moveToRight(obj)
    # 切换到编辑模式
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')

    # 获取编辑模式下的网格数据
    bm = bmesh.from_edit_mesh(obj.data)

    # 设置圆球的参数
    radius = 0.4  # 半径
    segments = 32  # 分段数

    # 在指定位置生成圆球
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                              radius=radius * 2)

    # 更新网格数据
    bmesh.update_edit_mesh(obj.data)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.materials.append(bpy.data.materials['red'])

    # 设置圆球的位置
    obj.location = co  # 指定的位置坐标
    hooktoobject(index)  # 绑定到指定下标


class TEST_OT_addsoundcanal(bpy.types.Operator):
    bl_idname = "object.addsoundcanal"
    bl_label = "addsoundcanal"
    bl_description = "双击添加管道控制点"

    def excute(self, context, event):

        global number
        name = '右耳'
        mesh_name = 'meshsoundcanal'

        if number == 0:  # 如果number等于0，初始化
            co = cal_co(name, context, event)
            if co != -1:
                generate_canal(co)

        elif number == 1:  # 如果number等于1双击完成管道
            co = cal_co(name, context, event)
            if co != -1:
                finish_canal(co)
                bpy.data.objects['右耳'].data.materials.clear()  # 清除材质
                bpy.data.objects['右耳'].data.materials.append(bpy.data.materials["Transparency"])
                bpy.ops.object.select_all(action='DESELECT')
                # bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')

        else:  # 如果number大于1，双击添加控制点
            co = cal_co(mesh_name, context, event)
            if co != -1:
                min_index, secondmin_index, insert_index = select_nearest_point(co)
                add_canal(min_index, secondmin_index, co, insert_index)

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_deletesoundcanal(bpy.types.Operator):
    bl_idname = "object.deletesoundcanal"
    bl_label = "deletesoundcanal"
    bl_description = "双击删除管道控制点"

    def excute(self, context, event):

        global object_dic
        sphere_number = on_which_shpere(context, event)

        if sphere_number == 0:
            pass

        elif sphere_number == 1 or sphere_number == 2:
            pass

        else:  # 如果number大于1，双击添加控制点
            sphere_name = 'soundcanalsphere' + str(sphere_number)
            index = object_dic[sphere_name]
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['soundcanal'].hide_set(False)
            bpy.context.view_layer.objects.active = bpy.data.objects['soundcanal']
            bpy.data.objects['soundcanal'].select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式删除点
            bpy.ops.curve.select_all(action='DESELECT')
            bpy.data.objects['soundcanal'].data.splines[0].points[index].select = True
            bpy.ops.curve.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.data.objects['soundcanal'].select_set(False)
            bpy.data.objects['soundcanal'].hide_set(True)

            # 更新
            bpy.data.objects.remove(bpy.data.objects[sphere_name], do_unlink=True)
            for key in object_dic:
                if object_dic[key] > index:
                    object_dic[key] -= 1
            del object_dic[sphere_name]
            global number
            number -= 1
            convert_soundcanal()
            save_soundcanal_info([0, 0, 0])

    def invoke(self, context, event):
        self.excute(context, event)
        return {'FINISHED'}


class TEST_OT_soundcanalqiehuan(bpy.types.Operator):
    bl_idname = "object.soundcanalqiehuan"
    bl_label = "soundcanalqiehuan"
    bl_description = "鼠标行为切换"

    __timer = None
    __flag = False

    def invoke(self, context, event):  # 初始化
        print('soundcanalqiehuan invoke')
        initialTransparency()
        newColor('red', 1, 0, 0, 0, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)  # 不透明材质
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)  # 透明材质
        TEST_OT_soundcanalqiehuan.__timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)
        bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")
        bpy.context.scene.var = 23
        op_cls = TEST_OT_soundcanalqiehuan
        op_cls.__flag = False
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global object_dic
        op_cls = TEST_OT_soundcanalqiehuan
        if bpy.context.scene.var != 23:
            context.window_manager.event_timer_remove(TEST_OT_soundcanalqiehuan.__timer)
            TEST_OT_soundcanalqiehuan.__timer = None
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            print('soundcanalqiehuan finish')
            return {'FINISHED'}

        if context.area:
            context.area.tag_redraw()

        if len(object_dic) >= 2:

            sphere_number = on_which_shpere(context, event)
            if (event.type == 'TIMER'):
                if sphere_number == 0:
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
                    bpy.data.objects['右耳'].select_set(True)
                    return {'PASS_THROUGH'}
                elif sphere_number == 1 or sphere_number == 2:
                    bpy.context.scene.tool_settings.use_snap = True
                else:
                    bpy.context.scene.tool_settings.use_snap = False
                bpy.context.view_layer.objects.active = bpy.data.objects['soundcanalsphere' + str(sphere_number)]
                obj = context.active_object
                if re.match('soundcanalsphere', obj.name) != None:
                    sphere_name = 'soundcanalsphere' + str(sphere_number)
                    index = int(object_dic[sphere_name])
                    bpy.data.objects['soundcanal'].data.splines[0].points[index].co[0:3] = bpy.data.objects[
                        sphere_name].location
                    bpy.data.objects['soundcanal'].data.splines[0].points[index].co[3] = 1
                    flag = save_soundcanal_info(obj.location)
                    if flag:
                        convert_soundcanal()
                return {'PASS_THROUGH'}

            if (sphere_number != 0 and is_changed(context, event) == True):
                # bpy.ops.wm.tool_set_by_id(name="builtin.select")
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal3")

            elif (sphere_number == 0 and is_changed(context, event) == True):
                bpy.ops.wm.tool_set_by_id(name="my_tool.addsoundcanal2")

            if cal_co('meshsoundcanal', context, event) == -1:
                if sphere_number == 1 or sphere_number == 2 and (not op_cls.__flag):
                    op_cls.__flag == True
                    bpy.data.objects['meshsoundcanal'].data.materials.clear()
                    bpy.data.objects['meshsoundcanal'].data.materials.append(bpy.data.materials["grey2"])
                elif is_changed_now(context, event) == True:
                    bpy.data.objects['meshsoundcanal'].data.materials.clear()
                    bpy.data.objects['meshsoundcanal'].data.materials.append(bpy.data.materials["grey"])

            elif cal_co('meshsoundcanal', context, event) != -1:
                if sphere_number == 1 or sphere_number == 2 and (op_cls.__flag):
                    op_cls.__flag == False
                    bpy.data.objects['meshsoundcanal'].data.materials.clear()
                    bpy.data.objects['meshsoundcanal'].data.materials.append(bpy.data.materials["grey"])
                elif is_changed_now(context, event) == True:
                    bpy.data.objects['meshsoundcanal'].data.materials.clear()
                    bpy.data.objects['meshsoundcanal'].data.materials.append(bpy.data.materials["grey2"])

        return {'PASS_THROUGH'}


class TEST_OT_finishsoundcanal(bpy.types.Operator):
    bl_idname = "object.finishsoundcanal"
    bl_label = "完成操作"
    bl_description = "点击按钮完成管道制作"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 24
        return {'FINISHED'}

    def excute(self, context, event):
        submit_soundcanal()
        global soundcanal_finish
        soundcanal_finish = True


class TEST_OT_resetsoundcanal(bpy.types.Operator):
    bl_idname = "object.resetsoundcanal"
    bl_label = "重置操作"
    bl_description = "点击按钮重置管道制作"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 25
        return {'FINISHED'}

    def excute(self, context, event):
        # 删除多余的物体
        global object_dic
        need_to_delete_model_name_list = ['meshsoundcanal', 'soundcanal']
        for key in object_dic:
            bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
        delete_useless_object(need_to_delete_model_name_list)
        # 将SoundCanalReset复制并替代当前操作模型
        oriname = "右耳"  # TODO    右耳最终需要替换为导入时的文件名
        ori_obj = bpy.data.objects.get(oriname)
        copyname = "右耳SoundCanalReset"
        copy_obj = bpy.data.objects.get(copyname)
        if (ori_obj != None and copy_obj != None):
            bpy.data.objects.remove(ori_obj, do_unlink=True)
            duplicate_obj = copy_obj.copy()
            duplicate_obj.data = copy_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = oriname
            bpy.context.collection.objects.link(duplicate_obj)
            moveToRight(duplicate_obj)
        # bpy.data.objects['右耳'].data.materials.clear()
        # bpy.data.objects['右耳'].data.materials.append(bpy.data.materials['Yellow'])
        # utils_re_color("右耳", (1, 0.319, 0.133))
        global number
        number = 0


def new_curve(curve_name):
    ''' 创建并返回一个新的曲线对象 '''
    curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
    curve_data.dimensions = '3D'
    obj = bpy.data.objects.new(curve_name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    moveToRight(obj)
    obj.data.bevel_depth = bpy.context.scene.chuanShenGuanDaoZhiJing / 2  # 管道孔径
    obj.data.bevel_resolution = 16
    obj.data.use_fill_caps = True  # 封盖
    return obj


def generate_canal(co):
    ''' 初始化管道 '''
    global number
    obj = new_curve('soundcanal')
    obj.data.materials.append(bpy.data.materials["grey"])
    # 添加一个曲线样条
    spline = obj.data.splines.new(type='NURBS')
    spline.order_u = 2
    spline.use_smooth = True
    spline.points[number].co[0:3] = co
    spline.points[number].co[3] = 1
    # spline.use_cyclic_u = True
    # spline.use_endpoint_u = True

    # 开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    add_sphere(co, 0)
    save_soundcanal_info(co)


def project_point_on_line(point, line_point1, line_point2):
    line_vec = line_point2 - line_point1
    line_vec.normalize()
    point_vec = point - line_point1
    projection = line_vec.dot(point_vec) * line_vec
    projected_point = line_point1 + projection
    return projected_point


def add_canal(min_co, secondmin_co, co, insert_index):
    ''' 在管道上增加控制点 '''

    projected_point = project_point_on_line(co, min_co, secondmin_co)  # 计算目标点在向量上的投影点
    add_point(insert_index, projected_point)
    add_sphere(projected_point, insert_index)


def add_point(index, co):
    global number
    global object_dic
    curve_object = bpy.data.objects['soundcanal']
    curve_data = curve_object.data
    new_curve_data = new_curve('newcurve').data
    # 在曲线上插入新的控制点
    new_curve_data.splines.clear()
    spline = new_curve_data.splines.new(type='NURBS')
    spline.order_u = 2
    spline.use_smooth = True
    new_curve_data.splines[0].points.add(count=number)

    # 设置新控制点的坐标
    for i, point in enumerate(curve_data.splines[0].points):
        if i < index:
            spline.points[i].co = point.co

    spline.points[index].co[0:3] = co
    spline.points[index].co[3] = 1

    for i, point in enumerate(curve_data.splines[0].points):
        if i >= index:
            spline.points[i + 1].co = point.co

    bpy.data.objects.remove(curve_object, do_unlink=True)
    bpy.data.objects['newcurve'].name = 'soundcanal'
    bpy.data.objects['soundcanal'].hide_set(True)

    for key in object_dic:
        if object_dic[key] >= index:
            object_dic[key] += 1


def finish_canal(co):
    ''' 完成管道的初始化 '''
    curve_object = bpy.data.objects['soundcanal']
    curve_data = curve_object.data
    obj = bpy.data.objects['右耳']
    first_co = Vector(curve_data.splines[0].points[0].co[0:3])
    _, _, normal, _ = obj.closest_point_on_mesh(first_co)
    reverse_normal = (-normal[0], -normal[1], -normal[2])
    reverse_normal = Vector(reverse_normal)
    reverse_normal.normalize()
    point_vec = co - first_co
    projection = reverse_normal.dot(point_vec) * reverse_normal
    projected_point = first_co + projection
    curve_data.splines[0].points.add(count=2)
    curve_data.splines[0].points[1].co[0:3] = projected_point
    curve_data.splines[0].points[1].co[3] = 1
    curve_data.splines[0].points[2].co[0:3] = co
    curve_data.splines[0].points[2].co[3] = 1
    add_sphere(co, 2)
    add_sphere(projected_point, 1)
    convert_soundcanal()
    save_soundcanal_info(co)
    curve_object.hide_set(True)
    bpy.data.objects['右耳'].hide_select = True
    # bpy.context.view_layer.objects.active = curve_object
    # bpy.ops.object.select_all(action='DESELECT')
    # curve_object.select_set(state=True)
    # bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式
    # bpy.ops.curve.select_all(action='DESELECT')
    # curve_data.splines[0].points[0].select = True
    # curve_data.splines[0].points[1].select = True
    # bpy.ops.curve.subdivide(number_cuts=1)  # 细分次数
    # bpy.ops.object.mode_set(mode='OBJECT')  # 返回对象模式
    # add_sphere(co, 2)
    # temp_co = curve_data.splines[0].points[1].co[0:3]
    # add_sphere(temp_co, 1)
    # convert_soundcanal()
    # save_soundcanal_info(temp_co)


def hooktoobject(index):
    ''' 建立指定下标的控制点到圆球的字典 '''
    global number
    global object_dic
    sphere_name = 'soundcanalsphere' + str(number)
    object_dic.update({sphere_name: index})


def save_soundcanal_info(co):
    global soundcanal_data
    cox = round(co[0], 3)
    coy = round(co[1], 3)
    coz = round(co[2], 3)
    if (cox not in soundcanal_data) or (coy not in soundcanal_data) or (coz not in soundcanal_data):
        for object in bpy.data.objects:
            if object.name == 'soundcanal':
                soundcanal_data = []
                curve_data = object.data
                for point in curve_data.splines[0].points:
                    soundcanal_data.append(round(point.co[0], 3))
                    soundcanal_data.append(round(point.co[1], 3))
                    soundcanal_data.append(round(point.co[2], 3))
        return True
    return False


def initial_soundcanal():
    # 初始化
    global object_dic
    global soundcanal_data
    global soundcanal_finish
    soundcanal_finish = False
    if len(object_dic) >= 2:  # 存在已保存的圆球位置,复原原有的管道
        initialTransparency()
        newColor('red', 1, 0, 0, 1, 0.8)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.4)
        obj = new_curve('soundcanal')
        obj.data.materials.append(bpy.data.materials["grey"])

        # 添加一个曲线样条
        spline = obj.data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points.add(count=len(object_dic) - 1)
        for i, point in enumerate(spline.points):
            point.co = (soundcanal_data[3 * i], soundcanal_data[3 * i + 1], soundcanal_data[3 * i + 2], 1)

        # 生成圆球
        for key in object_dic:
            mesh = bpy.data.meshes.new("soundcanalsphere")
            obj = bpy.data.objects.new(key, mesh)
            bpy.context.collection.objects.link(obj)
            moveToRight(obj)

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(obj.data)

            # 设置圆球的参数
            radius = 0.4  # 半径
            segments = 32  # 分段数

            # 在指定位置生成圆球
            bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                                      radius=radius * 2)
            bmesh.update_edit_mesh(obj.data)  # 更新网格数据

            bpy.ops.object.mode_set(mode='OBJECT')
            obj.data.materials.append(bpy.data.materials['red'])
            obj.location = bpy.data.objects['soundcanal'].data.splines[0].points[object_dic[key]].co[0:3]  # 指定的位置坐标

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        bpy.data.objects['右耳'].data.materials.clear()
        bpy.data.objects['右耳'].data.materials.append(bpy.data.materials["Transparency"])
        bpy.data.objects['右耳'].hide_select = True
        convert_soundcanal()
        bpy.data.objects['soundcanal'].hide_set(True)
        save_soundcanal_info([0, 0, 0])
        bpy.data.objects['soundcanal'].hide_set(True)

    elif len(object_dic) == 1:  # 只点击了一次
        newColor('red', 1, 0, 0, 1, 0.8)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        obj = new_curve('soundcanal')
        obj.data.materials.append(bpy.data.materials["grey"])
        # 添加一个曲线样条
        spline = obj.data.splines.new(type='NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points[0].co[0:3] = soundcanal_data[0:3]
        spline.points[0].co[3] = 1
        # spline.use_cyclic_u = True
        # spline.use_endpoint_u = True

        # 开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        mesh = bpy.data.meshes.new("soundcanalsphere")
        obj = bpy.data.objects.new("soundcanalsphere1", mesh)
        bpy.context.collection.objects.link(obj)
        moveToRight(obj)

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(state=True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        # 设置圆球的参数
        radius = 0.4  # 半径
        segments = 32  # 分段数

        # 在指定位置生成圆球
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                                  radius=radius * 2)
        bmesh.update_edit_mesh(obj.data)  # 更新网格数据

        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.materials.append(bpy.data.materials['red'])
        obj.location = soundcanal_data[0:3]  # 指定的位置坐标

    else:  # 不存在已保存的圆球位置
        pass

    bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')


def submit_soundcanal():
    # 应用修改器，删除多余的物体
    global object_dic
    global soundcanal_finish
    if len(object_dic) > 0 and soundcanal_finish == False:
        adjustpoint()
        bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
        bool_modifier = bpy.context.active_object.modifiers.new(
            name="Soundcanal Boolean Modifier", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = bpy.data.objects['meshsoundcanal']
        bpy.ops.object.modifier_apply(modifier="Soundcanal Boolean Modifier", single_user=True)
        need_to_delete_model_name_list = ['meshsoundcanal', 'soundcanal']
        for key in object_dic:
            need_to_delete_model_name_list.append(key)
        delete_useless_object(need_to_delete_model_name_list)
        bpy.context.active_object.data.materials.clear()
        bpy.context.active_object.data.materials.append(bpy.data.materials['Yellow'])
        utils_re_color("右耳", (1, 0.319, 0.133))
        bpy.context.active_object.data.use_auto_smooth = True
        bpy.data.objects['右耳'].hide_select = False


def adjustpoint():
    curve_object = bpy.data.objects['soundcanal']
    curve_data = curve_object.data
    last_index = len(curve_data.splines[0].points) - 1
    first_point = curve_data.splines[0].points[0]
    last_point = curve_data.splines[0].points[last_index]
    step = 0.3
    normal = Vector(first_point.co[0:3]) - Vector(curve_data.splines[0].points[1].co[0:3])
    first_point.co = (first_point.co[0] + normal[0] * step, first_point.co[1] + normal[1] * step,
                      first_point.co[2] + normal[2] * step, 1)
    normal = Vector(last_point.co[0:3]) - Vector(curve_data.splines[0].points[last_index - 1].co[0:3])
    last_point.co = (last_point.co[0] + normal[0] * step, last_point.co[1] + normal[1] * step,
                     last_point.co[2] + normal[2] * step, 1)
    convert_soundcanal()


def checkposition():
    object = bpy.data.objects['meshsoundcanal']
    target_object = bpy.data.objects['右耳']
    bm = bmesh.new()
    bm.from_mesh(object.data)  # 获取网格数据
    bm.verts.ensure_lookup_table()
    color_lay = bm.verts.layers.float_color["Color"]
    for vert in bm.verts:
        _, co, normal, _ = target_object.closest_point_on_mesh(vert.co)
        flag = (vert.co - co).dot(normal)
        colorvert = vert[color_lay]
        if (flag > 0):
            colorvert.x = 0.8
            colorvert.y = 0.8
            colorvert.z = 0.8
        else:
            colorvert.x = 1
            colorvert.y = 0
            colorvert.z = 0
    bm.to_mesh(object.data)
    bm.free()


def frontToSoundCanal():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SoundCanalReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SoundCanalReset"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)

    initial_soundcanal()


def frontFromSoundCanal():
    save_soundcanal_info([0, 0, 0])
    need_to_delete_model_name_list = ['meshsoundcanal', 'soundcanal']
    for key in object_dic:
        need_to_delete_model_name_list.append(key)
    delete_useless_object(need_to_delete_model_name_list)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    resetname = name + "SoundCanalReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SoundCanalReset" or selected_obj.name == "右耳SoundCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToSoundCanal():
    exist_SoundCanalReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SoundCanalReset"):
            exist_SoundCanalReset = True
    if (exist_SoundCanalReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "SoundCanalReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        initial_soundcanal()
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳SoundCanalLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SoundCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        initial_soundcanal()


def backFromSoundCanal():
    save_soundcanal_info([0, 0, 0])
    submit_soundcanal()
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SoundCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "SoundCanalLast"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)


class addsoundcanal_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addsoundcanal2"
    bl_label = "传声孔添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作"
    )
    bl_icon = "ops.curves.sculpt_smooth"
    bl_widget = None
    bl_keymap = (
        ("object.addsoundcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class addsoundcanal_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addsoundcanal3"
    bl_label = "传声孔对圆球操作"
    bl_description = (
        "传声孔对圆球移动、双击操作"
    )
    bl_icon = "ops.curves.sculpt_pinch"
    bl_widget = None
    bl_keymap = (
        ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, None),
        ("object.deletesoundcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class finishsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishsoundcanal"
    bl_label = "传声孔完成"
    bl_description = (
        "完成管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_puff"
    bl_widget = None
    bl_keymap = (
        ("object.finishsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetsoundcanal"
    bl_label = "传声孔重置"
    bl_description = (
        "重置管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_slide"
    bl_widget = None
    bl_keymap = (
        ("object.resetsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrorsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrorsoundcanal"
    bl_label = "传声孔镜像"
    bl_description = (
        "点击镜像传声孔"
    )
    bl_icon = "ops.curve.pen"
    bl_widget = None
    bl_keymap = (
        ("object.mirrorsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


_classes = [
    TEST_OT_addsoundcanal,
    TEST_OT_deletesoundcanal,
    TEST_OT_soundcanalqiehuan,
    TEST_OT_finishsoundcanal,
    TEST_OT_resetsoundcanal,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_tool(resetsoundcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishsoundcanal_MyTool, separator=True, group=False,
                            after={resetsoundcanal_MyTool.bl_idname})
    bpy.utils.register_tool(mirrorsoundcanal_MyTool, separator=True, group=False,
                            after={finishsoundcanal_MyTool.bl_idname})

    bpy.utils.register_tool(addsoundcanal_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(addsoundcanal_MyTool3, separator=True, group=False)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)

    bpy.utils.unregister_tool(resetsoundcanal_MyTool)
    bpy.utils.unregister_tool(finishsoundcanal_MyTool)
    bpy.utils.unregister_tool(mirrorsoundcanal_MyTool)

    bpy.utils.unregister_tool(addsoundcanal_MyTool2)
    bpy.utils.unregister_tool(addsoundcanal_MyTool3)