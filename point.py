import bpy
import bmesh
import mathutils
from bpy_extras import view3d_utils
from math import sqrt
from mathutils import Vector
from .create_mould import bottom_ring

index_initial = -1  # 记录第一次点击蓝线时的下标索引
index_finish = -1  # 记录结束时点击蓝线的的下标索引

index = -1  # 记录拖拽曲线时曲线中心点的下标
number = 10 # 记录拖拽曲线时上一次选中曲线控制点的数量
prev_on_object = False 

def get_region_and_space(context, area_type, region_type, space_type):
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

# 返回鼠标点击位置的坐标，没有相交则返回-1
def co_on_object(name, context, event):
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

            co, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                return co  # 如果发生交叉，返回坐标的值
    return -1

#判断当前鼠标所在的物体是否发生改变
def is_changed(context, event):
    active_obj = bpy.data.objects['BottomRingBorderRForCutR']
    curr_on_object = False             # 当前鼠标是否在物体上,初始化为False
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
                curr_on_object = True                     # 如果发生交叉，将变量设为True
    if (curr_on_object != prev_on_object):
        prev_on_object = curr_on_object
        return True
    else:
        return False

# 选择曲线上离坐标位置最近的点
def select_nearest_point(co):

    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects['BottomRingBorderR']
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

# 复制曲线数据
def copy_curve(name):
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects[name]
    new_name = 'new' + name
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

# 将两条曲线合并
def join_curve():
    global index_initial
    global index_finish
    
    snaptoobject("point") # 将曲线吸附到物体上
    # 获取两条曲线对象
    curve_obj1 = bpy.data.objects['BottomRingBorderR']
    curve_obj2 = bpy.data.objects['point']
    
    # if index_initial > index_finish: #如果起始点的下标大于结束点，交换两个下标的值
    #     temp = index_initial
    #     index_initial = index_finish
    #     index_finish = temp

    if index_initial > index_finish: #如果起始点的下标大于结束点，反转曲线方向
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.switch_direction()
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 获取两条曲线的曲线数据
    curve_data1 = curve_obj1.data
    curve_data2 = curve_obj2.data

    # 创建一个新的曲线对象
    new_curve_data = bpy.data.curves.new(
        name="secondBottomRingBorderR", type='CURVE')
    new_curve_obj = bpy.data.objects.new(
        name="secondBottomRingBorderR", object_data=new_curve_data)

    # 将新的曲线对象添加到场景中
    bpy.context.collection.objects.link(new_curve_obj)

    # 获取新曲线对象的曲线数据
    new_curve_data = new_curve_obj.data

    # 合并两条曲线的点集
    new_curve_data.splines.clear()
    new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
    point_number = len(curve_data1.splines[0].points) + len(
        curve_data2.splines[0].points) - abs(index_finish-index_initial) - 1
    new_spline.points.add(point_number)

    # 将第一条曲线在初始起点前的点复制到新曲线
    for i, point in enumerate(curve_data1.splines[0].points):
        if i == index_initial:
            break
        new_spline.points[i].co = point.co

    # 将第二条曲线的点复制到新曲线
    for i, point in enumerate(curve_data2.splines[0].points):
        new_spline.points[i + index_initial].co = point.co
    length = len(curve_data2.splines[0].points) #length为第二条曲线的长度（控制点的个数）

    # 将第一条曲线在结束点之后的点复制到新曲线
    for i, point in enumerate(curve_data1.splines[0].points):
        if i >= index_finish:
            new_spline.points[i + length -
                              abs(index_finish-index_initial)].co = point.co

    bpy.data.objects.remove(
        bpy.data.objects['BottomRingBorderR'], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects['point'], do_unlink=True)
    new_curve_obj.name = 'BottomRingBorderR'

    bpy.context.view_layer.objects.active = bpy.data.objects['BottomRingBorderR']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['BottomRingBorderR'].select_set(state=True)
    bpy.context.object.data.dimensions = '3D'

    # 处理曲线结束时的瑕疵
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    end_point = index_initial + length
    bpy.data.objects['BottomRingBorderR'].data.splines[0].points[end_point].select = True
    bpy.ops.curve.delete(type='VERT')
    # bpy.ops.curve.select_all(action='DESELECT')
    # bpy.data.objects['BottomRingBorderR'].data.splines[0].points[end_point-1].select = True
    # bpy.data.objects['BottomRingBorderR'].data.splines[0].points[end_point].select = True
    # bpy.ops.curve.make_segment()

    # 细分曲线，添加控制点
    bpy.ops.curve.select_all(action='DESELECT')
    for i in range(index_initial, end_point, 1):  # 选中原本在第二条曲线上的点
        bpy.data.objects['BottomRingBorderR'].data.splines[0].points[i].select = True
    bpy.ops.curve.subdivide(number_cuts=3) #细分次数
    bpy.ops.object.mode_set(mode='OBJECT')


def join_object():
    join_curve()  # 合并曲线对象
    
    copy_curve('BottomRingBorderR')  # 复制一份曲线数据
    bpy.data.objects.remove(
        bpy.data.objects['BottomRingBorderRForCutR'], do_unlink=True)  # 删除原有蓝线
    obj = bpy.data.objects['newBottomRingBorderR']
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = 0.4  # 设置曲线倒角深度为0.4
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    bpy.data.objects['newBottomRingBorderR'].data.materials.append(
        bpy.data.materials['blue'])
    bpy.data.objects['newBottomRingBorderR'].name = 'BottomRingBorderRForCutR'

# 将指定的曲线对象吸附到最近的顶点上
def snaptoobject(name):
    # 获取曲线对象
    curve_object = bpy.data.objects[name]
    # 获取目标物体
    # target_object = bpy.data.objects["右耳OriginForCutR"]
    target_object = bpy.data.objects["右耳"]
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

def initialBlueColor():
    yellow_material = bpy.data.materials.new(name="blue")
    yellow_material.use_nodes = True
    bpy.data.materials["blue"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        0, 0, 1, 1.0)


def checkinitialBlueColor():
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'blue':
            return True
    return False

def initialGreenColor():
    yellow_material = bpy.data.materials.new(name="green")
    yellow_material.use_nodes = True
    bpy.data.materials["green"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        0, 1, 0, 1.0)


def checkinitialGreenColor():
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'green':
            return True
    return False

def checkcopycurve():
    objects = bpy.data.objects
    for object in objects:
        if object.name == 'newBottomRingBorderR':
            return True
    return False

def selectcurve(context,event):
    global number
    global index
    if checkcopycurve() == True:
        bpy.data.objects.remove(bpy.data.objects['newBottomRingBorderR'], do_unlink=True)  # 删除原有曲线
        bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
    point_number = len(bpy.data.objects['BottomRingBorderR'].data.splines[0].points)-1
    copy_curve('BottomRingBorderR')  #复制一份数据用于分离
    bpy.data.objects['BottomRingBorderR'].hide_set(True)
    bpy.data.objects['BottomRingBorderRForCutR'].hide_set(True)
    if co_on_object('BottomRingBorderRForCutR', context, event) != -1:
        co = co_on_object('BottomRingBorderRForCutR', context, event)
        index = select_nearest_point(co)
    curve_obj = bpy.data.objects['newBottomRingBorderR']
    bpy.context.view_layer.objects.active = curve_obj
    bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
    bpy.context.object.data.bevel_depth = 0.4
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    if (index - number) <= 0: #防止下标越界
        number = index
    if (index + number) >= point_number:
        number = point_number - index
    for i in range(index-number,index+number,1):
        curve_obj.data.splines[0].points[i].select = True
    bpy.ops.curve.separate()  # 分离要进行拖拽的点
    bpy.ops.object.mode_set(mode='OBJECT')
    for object in bpy.data.objects:  # 改名
        if object.name == 'newBottomRingBorderR.001':
            # print('select copy object')
            object.name = 'dragcurve'
            break
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects['dragcurve'].data.materials.clear()  #清除材质
    bpy.data.objects['dragcurve'].data.materials.append(bpy.data.materials['green'])
    bpy.context.object.data.bevel_depth = 0.4
    bpy.context.view_layer.objects.active = bpy.data.objects['dragcurve']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['dragcurve'].select_set(state=True)

# def movecurve(co):
#     curve_obj = bpy.data.objects['dragcurve']
#     curve_data = curve_obj.data
#     point_number = int(len(curve_data.splines[0].points)/2)
#     for spline in curve_data.splines:
#         for point_index, point in enumerate(spline.points):
#             vertex_co = curve_obj.matrix_world @ Vector(point.co[0:3])
#             dis = (co - vertex_co) * disfunc(point_index-point_number) #距离向量
#             point.co[0:3] = co
#             point.co[3] = 1

def disfunc(x):
    return float(1 / (1 + pow(x,2)))

def movecurve(co):
    curve_obj = bpy.data.objects['dragcurve']
    curve_obj.location = co

class TEST_OT_doubleclick(bpy.types.Operator):

    bl_idname = "object.doubleclick"
    bl_label = "doubleclick"
    bl_description = "双击蓝线改变蓝线形态"

    def excute(self, context, event):
        global index_initial
        global index_finish
        if co_on_object('BottomRingBorderRForCutR',context, event) == -1:  # 双击位置不在曲线上不做任何事
            print("不在曲线上")

        else:
            if bpy.context.mode == 'OBJECT':  # 如果处于物体模式下，蓝线双击开始绘制
                co = co_on_object('BottomRingBorderRForCutR',context, event)
                index = select_nearest_point(co)
                print("在曲线上最近点的下标是", index)
                index_initial = index
                curve_obj = bpy.data.objects['BottomRingBorderR']
                bpy.context.view_layer.objects.active = curve_obj
                bpy.ops.object.select_all(action='DESELECT')
                curve_obj.select_set(state=True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                curve_obj.data.splines[0].points[index].select = True
                bpy.ops.curve.separate()  # 分离将要进行操作的点
                bpy.ops.object.mode_set(mode='OBJECT')
                for object in bpy.data.objects:  # 改名
                    if object.name == 'BottomRingBorderR.001':
                        # print('select copy object')
                        object.name = 'point'
                        break
                bpy.context.view_layer.objects.active = bpy.data.objects['point']
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects['point'].select_set(state=True)

                bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式进行操作
                bpy.ops.curve.select_all(action='SELECT')
                bpy.ops.wm.tool_set_by_id(
                    name="builtin.extrude_cursor")  # 调用挤出至光标工具
                bpy.context.object.data.bevel_depth = 0.4  # 设置倒角深度
                bpy.data.objects['point'].data.materials.append(
                    bpy.data.materials['blue'])
                # 开启吸附
                bpy.context.scene.tool_settings.use_snap = True
                bpy.context.scene.tool_settings.snap_elements = {'FACE'}
                bpy.context.scene.tool_settings.snap_target = 'CENTER'
                bpy.context.scene.tool_settings.use_snap_align_rotation = True
                bpy.context.scene.tool_settings.use_snap_backface_culling = True

            elif bpy.context.mode == 'EDIT_CURVE':  # 如果处于编辑模式下，蓝线双击确认完成
                print("起始位置的下标是", index_initial)
                co = co_on_object('BottomRingBorderRForCutR',context, event)
                index_finish = select_nearest_point(co)
                print("在曲线上最近点的下标是", index_finish)
                bpy.ops.object.mode_set(mode='OBJECT')  # 返回对象模式
                bpy.context.scene.tool_settings.use_snap = False  # 取消吸附

                # #删除两个索引间的顶点
                # curve_obj = bpy.data.objects['BottomRingBorderR']
                # bpy.context.view_layer.objects.active = curve_obj
                # bpy.ops.object.select_all(action='DESELECT')
                # curve_obj.select_set(state=True)
                # bpy.ops.object.mode_set(mode='EDIT')
                # bpy.ops.curve.select_all(action='DESELECT')
                # for i in range(index_initial,index_finish,1):  #选中两个索引中的点
                #     curve_obj.data.splines[0].points[i].select = True
                # bpy.ops.curve.delete(type='SEGMENT')
                # bpy.ops.curve.delete(type='SEGMENT')
                # # bpy.ops.curve.delete(type='VERT')
                # bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式

                join_object()  # 合并曲线
                # bottom_ring.boolean_apply()
                # bottom_ring.cut_bottom_part()

            else:
                pass

    def invoke(self, context, event):
        if checkinitialBlueColor() == False:
            initialBlueColor()
        self.excute(context, event)
        return {'FINISHED'}

class TEST_OT_dragcurve(bpy.types.Operator):

    bl_idname = "object.selectregion"
    bl_label = "selectregion"
    bl_description = "移动鼠标选取区域"

    __left_mouse_down = False
    __right_mouse_down = False
    __initial_mouse_x = None  #点击鼠标左键的初始位置
    __initial_mouse_y = None
    __initial_mouse_x_right = None  #点击鼠标右键的初始位置
    __is_moving = False
    __is_moving_right = False
    __is_modifier = False

    def invoke(self, context, event): #初始化
        print('dragcurve invoke')
        if checkinitialGreenColor() == False:
            initialGreenColor()
        if checkinitialBlueColor() == False:
            initialBlueColor()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box") #切换到公共鼠标行为
        op_cls = TEST_OT_dragcurve
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_mouse_x_right = None
        op_cls.__is_moving = False
        op_cls. __is_moving_right = False
        op_cls.__is_modifier = False
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        op_cls = TEST_OT_dragcurve
        if co_on_object('BottomRingBorderRForCutR', context, event) == -1:  #鼠标不在曲线上时
            if event.value == 'RELEASE':
                print("release")
                if op_cls.__is_moving_right == True: #鼠标右键松开
                    op_cls.__right_mouse_down = False
                    op_cls.__initial_mouse_x_right = None
                    op_cls.__is_moving_right = False
                if op_cls.__is_moving == True: #鼠标左键松开
                    op_cls.__is_moving = False
                    op_cls.__left_mouse_down = False
                    op_cls.__initial_mouse_x = None
                    op_cls.__initial_mouse_y = None
            if op_cls.__right_mouse_down == False:
                if checkcopycurve() == True and op_cls.__left_mouse_down == False and op_cls.__is_modifier == False:
                    bpy.data.objects.remove(bpy.data.objects['newBottomRingBorderR'], do_unlink=True)  # 删除原有曲线
                    bpy.data.objects.remove(bpy.data.objects['dragcurve'], do_unlink=True)
                    bpy.data.objects['BottomRingBorderR'].hide_set(False)        #显示隐藏的物体
                    bpy.data.objects['BottomRingBorderRForCutR'].hide_set(False)
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            if op_cls.__right_mouse_down == True:  #鼠标右键按下
                global number
                number += int((event.mouse_region_x - op_cls.__initial_mouse_x_right) / 5) #扩大或缩小选区
                if(number < 10): #防止选不到点弹出报错信息
                    number = 10
                selectcurve(context,event)
            if op_cls.__left_mouse_down == True:  #鼠标左键按下
                # co = co_on_object('右耳OriginForCutR',context,event)
                op_cls.__is_modifier = True
                co = co_on_object('右耳',context,event)
                if co != -1:
                    movecurve(co)
            if op_cls.__left_mouse_down == False:
                # 吸附，重新切割
                pass  

            return {'PASS_THROUGH'}
        
        else:
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
                return {'RUNNING_MODAL'}
            elif event.type == 'RIGHTMOUSE':
                if event.value == 'PRESS':
                    op_cls.__right_mouse_down = True
                    op_cls.__initial_mouse_x_right = event.mouse_region_x
                    op_cls.__is_moving_right = True
                elif event.value == 'RELEASE':
                    op_cls.__right_mouse_down = False
                    op_cls.__initial_mouse_x_right = None
                    op_cls.__is_moving_right = False
                return {'RUNNING_MODAL'}
            elif event.type == 'MOUSEMOVE' and op_cls.__left_mouse_down == False and op_cls.__right_mouse_down == False:  #鼠标移动时选择不同的曲线区域
                selectcurve(context,event)

        return {'PASS_THROUGH'}

class doubleclick_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.doubleclick"
    bl_label = "双击添加点"
    bl_description = (
        "使用鼠标双击添加点"
    )
    bl_icon = "ops.mesh.knife_tool"  # TODO:修改图标
    bl_widget = None
    bl_keymap = (
        ("object.doubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'},
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
    bl_icon = "ops.mesh.knife_tool"  # TODO:修改图标
    bl_widget = None
    bl_keymap = (
        ("object.selectregion",{"type": 'MOUSEMOVE', "value": 'ANY'}, 
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

_classes = [

    TEST_OT_doubleclick,
    TEST_OT_dragcurve
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(doubleclick_MyTool, separator=True, group=False)
    bpy.utils.register_tool(dragcurve_MyTool, separator=True,
                            group=False, after={doubleclick_MyTool.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(doubleclick_MyTool)
    bpy.utils.unregister_tool(dragcurve_MyTool)
