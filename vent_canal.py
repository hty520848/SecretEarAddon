import bpy
import bmesh
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
from math import sqrt
from .tool import newShader,moveToRight,utils_re_color,delete_useless_object,newColor
import re

prev_on_object = 0
prev_on_object_old = False
prev_on_object_now = False
number = 0  #记录管道控制点点的个数
object_dic = { }  #记录当前圆球以及对应控制点
ventcanal_data = [ ] #记录当前控制点的坐标

def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2

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
        object_index = int(key.replace('ventcanalsphere',''))

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
    curr_on_object_old = is_mouse_on_object('右耳',context, event)  # 当前鼠标在哪个物体上
    global prev_on_object_old  # 之前鼠标在那个物体上
    if (curr_on_object_old != prev_on_object_old):
        prev_on_object_old = curr_on_object_old
        return True
    else:
        return False
    
def is_changed_now(context, event):
    ''' 创建圆球后鼠标位置的判断 '''
    curr_on_object_now = is_mouse_on_object('meshventcanal',context, event)  # 当前鼠标在哪个物体上
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
                return co   # 如果发生交叉，返回坐标的值

    return -1

def select_nearest_point(co):
    '''
    选择曲线上离坐标位置最近的两个点
    :param co: 坐标的值
    :return: 最近两个点的坐标以及要插入的下标
    '''
    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects['ventcanal']
    # 获取曲线的数据
    curve_data = curve_obj.data
    # 遍历曲线的所有点
    min_distance = float('inf')
    second_min_distance = float('inf')
    nearest_index = -1
    second_nearest_index = -1

    for point_index, point in enumerate(curve_data.splines[0].points):
        # 计算点与给定点之间的距离
        distance = sqrt(sum((a - b) ** 2 for a, b in zip(point.co, co)))
        # 更新最小距离和对应的点索引
        if distance < min_distance:
            second_min_distance = min_distance
            min_distance = distance
            second_nearest_index = nearest_index
            nearest_index = point_index
        elif distance < second_min_distance:
            second_min_distance = distance
            second_nearest_index = point_index
    insert_index = max(nearest_index,second_nearest_index) 
    curve_object = bpy.data.objects['ventcanal']
    curve_data = curve_object.data
    min_co = Vector(curve_data.splines[0].points[nearest_index].co[0:3])
    secondmin_co = Vector(curve_data.splines[0].points[second_nearest_index].co[0:3])
    dis_vector1 = Vector(secondmin_co - co)
    dis_vector2 = Vector(min_co - co)
    if dis_vector1.dot(dis_vector2) < 0:
        return (min_co,secondmin_co,insert_index)
    else:
        if insert_index > nearest_index: 
            insert_index = nearest_index
            secondmin_co = Vector(curve_data.splines[0].points[second_nearest_index-2].co[0:3])
        else:
            secondmin_co = Vector(curve_data.splines[0].points[second_nearest_index+2].co[0:3])
        return (min_co,secondmin_co,insert_index)
        

def copy_curve():
    ''' 复制曲线数据 '''
    # 选择要复制数据的源曲线对象
    source_curve = bpy.data.objects['ventcanal']
    target_curve = new_curve('meshventcanal')
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

def convert_ventcanal():
    if(bpy.data.objects.get('meshventcanal')):
        bpy.data.objects.remove(bpy.data.objects['meshventcanal'], do_unlink=True)  # 删除原有网格
    copy_curve()
    duplicate_obj = bpy.data.objects['meshventcanal']
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    # while(bpy.context.active_object.modifiers):
    #     modifer_name = bpy.context.active_object.modifiers[0].name
    #     bpy.ops.object.modifier_apply(modifier = modifer_name)
    bpy.context.active_object.data.bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing / 2  # 设置曲线倒角深度
    bpy.context.active_object.data.bevel_resolution = 16
    bpy.context.active_object.data.use_fill_caps = True # 封盖
    bpy.ops.object.convert(target='MESH')  # 转化为网格
    duplicate_obj.hide_select = True
    duplicate_obj.data.materials.clear()
    duplicate_obj.data.materials.append(bpy.data.materials["grey"])

def add_sphere(co,index):
    ''' 
    在指定位置生成圆球用于控制管道曲线的移动 
    :param co:指定的坐标
    :param index:指定要钩挂的控制点的下标
    '''
    global number
    number += 1
    # 创建一个新的网格
    mesh = bpy.data.meshes.new("ventcanalsphere")
    name = 'ventcanalsphere' + str(number)
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
    hooktoobject(index) # 绑定到指定下标

class TEST_OT_addventcanal(bpy.types.Operator):

    bl_idname = "object.addventcanal"
    bl_label = "addventcanal"
    bl_description = "双击添加管道控制点"

    def excute(self, context, event):
        
        global number
        name = '右耳'
        mesh_name = 'meshventcanal'

        if number == 0 :  # 如果number等于0，初始化
            co = cal_co(name, context, event)
            generate_canal(co)

        elif number == 1 :   # 如果number等于1双击完成管道
            co = cal_co(name, context, event)
            finish_canal(co)
            bpy.data.objects['右耳'].data.materials.clear()  #清除材质
            bpy.data.objects['右耳'].data.materials.append(bpy.data.materials["Transparency"])
            bpy.ops.object.select_all(action='DESELECT')
            # bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')

        else: # 如果numberd大于1，双击添加控制点 
            co = cal_co(mesh_name, context, event)
            min_index,secondmin_index,insert_index = select_nearest_point(co)
            add_canal(min_index,secondmin_index,co,insert_index)

    def invoke(self, context, event):
        initialTransparency()
        newColor('red', 1, 0, 0, 0, 1)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)  #不透明材质
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.8) #透明材质
        self.excute(context, event)
        return {'FINISHED'}
    
class TEST_OT_ventcanalqiehuan(bpy.types.Operator):

    bl_idname = "object.ventcanalqiehuan"
    bl_label = "ventcanalqiehuan"
    bl_description = "鼠标行为切换"

    __timer = None
    
    def invoke(self, context, event): #初始化
        print('ventcanalqiehuan invoke')
        TEST_OT_ventcanalqiehuan.__timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        bpy.ops.wm.tool_set_by_id(name="builtin.select")
        bpy.context.scene.var = 23
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        global object_dic
        if bpy.context.scene.var != 23:
            context.window_manager.event_timer_remove(TEST_OT_ventcanalqiehuan.__timer)
            TEST_OT_ventcanalqiehuan.__timer = None
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            print('ventcanalqiehuan finish')
            return {'FINISHED'}

        if context.area:
            context.area.tag_redraw()

        if len(object_dic) > 2:
            
            sphere_number = on_which_shpere(context,event)
            if (event.type == 'TIMER'):
                if sphere_number == 0:
                    return {'PASS_THROUGH'}
                elif sphere_number == 1 or sphere_number == 2:
                    bpy.context.scene.tool_settings.use_snap = True
                else:
                    bpy.context.scene.tool_settings.use_snap = False
                bpy.context.view_layer.objects.active = bpy.data.objects['ventcanalsphere' + str(sphere_number)]
                obj = context.active_object
                if re.match('ventcanalsphere', obj.name)!= None:
                    flag = save_ventcanal_info(obj.location)
                    if flag:
                        sphere_name = 'ventcanalsphere' + str(sphere_number)
                        index = int(object_dic[sphere_name])
                        bpy.data.objects['ventcanal'].data.splines[0].points[index].co[0:3] = bpy.data.objects[sphere_name].location
                        bpy.data.objects['ventcanal'].data.splines[0].points[index].co[3] = 1
                        convert_ventcanal()
                return {'PASS_THROUGH'}

            if(cal_co('meshventcanal', context, event) == -1 and is_changed_now(context,event) == True):
                if sphere_number == 0:
                    bpy.data.objects['meshventcanal'].data.materials.clear()
                    bpy.data.objects['meshventcanal'].data.materials.append(bpy.data.materials["grey"])
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            elif cal_co('meshventcanal', context, event) != -1:
                if is_changed_now(context,event) == True:
                    bpy.data.objects['meshventcanal'].data.materials.clear()
                    bpy.data.objects['meshventcanal'].data.materials.append(bpy.data.materials["grey2"])
                
                if(sphere_number != 0 and is_changed(context,event) == True):
                    bpy.ops.wm.tool_set_by_id(name="builtin.select")

                elif(sphere_number == 0 and is_changed(context,event) == True):
                    bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")
            
        else:
            name = '右耳'
            if(cal_co(name, context, event) == -1 and is_changed_old(context,event) == True):
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            else:
                if is_changed_old(context,event) == True:
                    bpy.ops.wm.tool_set_by_id(name="my_tool.addventcanal2")

        return {'PASS_THROUGH'}

class TEST_OT_finishventcanal(bpy.types.Operator):
    bl_idname = "object.finishventcanal"
    bl_label = "完成操作"
    bl_description = "点击按钮完成管道制作"

    def invoke(self, context, event):
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        bpy.context.scene.var = 24
        return {'FINISHED'}

    def excute(self, context, event):
        submit_ventcanal()
        

class TEST_OT_resetventcanal(bpy.types.Operator):
    bl_idname = "object.resetventcanal"
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
        need_to_delete_model_name_list = ['meshventcanal','ventcanal']
        for key in object_dic:
            bpy.data.objects.remove(bpy.data.objects[key], do_unlink=True)
        delete_useless_object(need_to_delete_model_name_list)
        object_dic.clear()
        # 将VentCanalReset复制并替代当前操作模型
        oriname = "右耳"  # TODO    右耳最终需要替换为导入时的文件名
        ori_obj = bpy.data.objects.get(oriname)
        copyname = "右耳VentCanalReset"
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
    obj.data.bevel_depth = bpy.context.scene.tongQiGuanDaoZhiJing / 2   #管道孔径
    obj.data.bevel_resolution = 16
    obj.data.use_fill_caps = True # 封盖
    return obj

def generate_canal(co):
    ''' 初始化管道 '''
    global number
    obj = new_curve('ventcanal')
    obj.data.materials.append(bpy.data.materials["grey"])
    # 添加一个曲线样条
    spline = obj.data.splines.new(type = 'NURBS')
    spline.order_u = 2
    spline.use_smooth = True
    spline.points[number].co[0:3] = co
    spline.points[number].co[3] = 1
    #spline.use_cyclic_u = True
    #spline.use_endpoint_u = True

    #开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    add_sphere(co,0)

def project_point_on_line(point, line_point1, line_point2):
    line_vec = line_point2 - line_point1
    line_vec.normalize()
    point_vec = point - line_point1
    projection = line_vec.dot(point_vec) * line_vec
    projected_point = line_point1 + projection
    return projected_point
   
def add_canal(min_co,secondmin_co,co,insert_index):
    ''' 在管道上增加控制点 '''
    
    projected_point = project_point_on_line(co, min_co, secondmin_co)  # 计算目标点在向量上的投影点
    add_point(insert_index,projected_point)
    add_sphere(projected_point,insert_index)

def add_point(index,co):
    global number
    global object_dic
    curve_object = bpy.data.objects['ventcanal']
    curve_data = curve_object.data
    new_curve_data = new_curve('newcurve').data
    # 在曲线上插入新的控制点
    new_curve_data.splines.clear()
    spline = new_curve_data.splines.new(type = 'NURBS')
    spline.order_u = 2
    spline.use_smooth = True
    new_curve_data.splines[0].points.add(count = number)

    # 设置新控制点的坐标
    for i, point in enumerate(curve_data.splines[0].points):
        if i < index:
            spline.points[i].co = point.co
    
    spline.points[index].co[0:3] = co
    spline.points[index].co[3] = 1

    for i, point in enumerate(curve_data.splines[0].points):
        if i >= index:
            spline.points[i+1].co = point.co
    
    bpy.data.objects.remove(curve_object, do_unlink=True)
    bpy.data.objects['newcurve'].name = 'ventcanal'
    bpy.data.objects['ventcanal'].hide_set(True)

    for key in object_dic:
        if object_dic[key] >= index:
            object_dic[key] += 1


def finish_canal(co):
    ''' 完成管道的初始化 '''
    global number
    curve_object = bpy.data.objects['ventcanal']
    curve_data = curve_object.data
    curve_data.splines[0].points.add(count = 1)
    curve_data.splines[0].points[number].co[0:3] = co
    curve_data.splines[0].points[number].co[3] = 1
    bpy.context.view_layer.objects.active = curve_object
    bpy.ops.object.select_all(action='DESELECT')
    curve_object.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT') #进入编辑模式
    bpy.ops.curve.select_all(action='DESELECT')
    curve_data.splines[0].points[0].select = True
    curve_data.splines[0].points[1].select = True
    bpy.ops.curve.subdivide(number_cuts = 1) #细分次数
    bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式
    curve_object.hide_set(True)
    bpy.data.objects['右耳'].hide_select = True
    add_sphere(co,2) 
    temp_co = curve_data.splines[0].points[1].co[0:3]
    add_sphere(temp_co,1)
    convert_ventcanal()
    save_ventcanal_info(temp_co)

def hooktoobject(index):
    ''' 建立指定下标的控制点到圆球的字典 '''
    global number
    global object_dic
    sphere_name = 'ventcanalsphere' + str(number)
    object_dic.update({sphere_name :index})

def save_ventcanal_info(co):
    global ventcanal_data
    cox = round(co[0], 3)
    coy = round(co[1], 3)
    coz = round(co[2], 3)
    if (cox not in ventcanal_data) or (coy not in ventcanal_data) or (coz not in ventcanal_data):
        for object in bpy.data.objects:
            if object.name == 'ventcanal':
                ventcanal_data = []
                curve_data = object.data
                for point in curve_data.splines[0].points:
                    ventcanal_data.append(round(point.co[0], 3))
                    ventcanal_data.append(round(point.co[1], 3))
                    ventcanal_data.append(round(point.co[2], 3))
        return True
    return False

def initial_ventcanal():
    #初始化
    global object_dic
    global ventcanal_data
    if len(object_dic) > 2:    #存在已保存的圆球位置,复原原有的管道
        initialTransparency()
        newColor('red', 1, 0, 0, 1, 0.8)
        newColor('grey', 0.8, 0.8, 0.8, 0, 1)
        newColor('grey2', 0.8, 0.8, 0.8, 1, 0.8)
        obj = new_curve('ventcanal')
        obj.data.materials.append(bpy.data.materials["grey"])

        # 添加一个曲线样条
        spline = obj.data.splines.new(type = 'NURBS')
        spline.order_u = 2
        spline.use_smooth = True
        spline.points.add(count = len(object_dic) - 1)
        for i, point in enumerate(spline.points):
            point.co = (ventcanal_data[3*i],ventcanal_data[3*i+1],ventcanal_data[3*i+2],1)
        
        # 生成圆球
        for key in object_dic:
            mesh = bpy.data.meshes.new("ventcanalsphere")
            obj = bpy.data.objects.new(key, mesh)
            bpy.context.collection.objects.link(obj)
            moveToRight(obj)

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(obj.data)

            # 设置圆球的参数
            radius = 0.3  # 半径
            segments = 32  # 分段数

            # 在指定位置生成圆球
            bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                                    radius=radius * 2)
            bmesh.update_edit_mesh(obj.data) # 更新网格数据

            bpy.ops.object.mode_set(mode='OBJECT')
            obj.data.materials.append(bpy.data.materials['red'])
            obj.location = obj.data.splines[0].points[object_dic[key]].co[0:3] # 指定的位置坐标
        
        #开启吸附
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.snap_target = 'CENTER'
        bpy.context.scene.tool_settings.use_snap_align_rotation = True
        bpy.context.scene.tool_settings.use_snap_backface_culling = True

        bpy.data.objects['右耳'].data.materials.append(bpy.data.materials["Transparency"])
        bpy.data.objects['右耳'].hide_select = True
        bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
        
    else: #不存在已保存的圆球位置
        pass

def submit_ventcanal():
    # 应用修改器，删除多余的物体
    global object_dic
    if len(object_dic) >0 :
        adjustpoint()
        bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
        bool_modifier = bpy.context.active_object.modifiers.new(
        name="Ventcanal Boolean Modifier", type='BOOLEAN')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = bpy.data.objects['meshventcanal']
        bpy.ops.object.modifier_apply(modifier="Ventcanal Boolean Modifier", single_user=True)
        need_to_delete_model_name_list = ['meshventcanal','ventcanal']
        for key in object_dic:
            need_to_delete_model_name_list.append(key)
        delete_useless_object(need_to_delete_model_name_list)
        bpy.context.active_object.data.materials.clear()
        bpy.context.active_object.data.materials.append(bpy.data.materials['Yellow'])
        utils_re_color("右耳", (1, 0.319, 0.133))
        bpy.context.active_object.data.use_auto_smooth = True

def adjustpoint():
    curve_object = bpy.data.objects['ventcanal']
    curve_data = curve_object.data
    last_index = len(curve_data.splines[0].points) - 1
    first_point = curve_data.splines[0].points[0]
    last_point = curve_data.splines[0].points[last_index]
    step = 0.5
    normal = Vector(first_point.co[0:3]) - Vector(curve_data.splines[0].points[1].co[0:3])  
    first_point.co = (first_point.co[0] + normal[0] * step, first_point.co[1] + normal[1] * step,
                       first_point.co[2] + normal[2] * step, 1)
    normal = Vector(last_point.co[0:3]) - Vector(curve_data.splines[0].points[last_index - 1].co[0:3])  
    last_point.co = (last_point.co[0] + normal[0] * step, last_point.co[1] + normal[1] * step,
                      last_point.co[2] + normal[2] * step, 1)
    convert_ventcanal()


def checkposition():
    object = bpy.data.objects['meshventcanal']
    target_object = bpy.data.objects['右耳']
    bm = bmesh.new()
    bm.from_mesh(object.data) #获取网格数据
    bm.verts.ensure_lookup_table()
    color_lay = bm.verts.layers.float_color["Color"]
    for vert in bm.verts:
        _, co, normal, _= target_object.closest_point_on_mesh(vert.co)
        flag = (vert.co - co).dot(normal)
        colorvert = vert[color_lay]
        if(flag > 0):
            colorvert.x = 0.8 
            colorvert.y = 0.8
            colorvert.z = 0.8
        else:
            colorvert.x = 1 
            colorvert.y = 0
            colorvert.z = 0
    bm.to_mesh(object.data)
    bm.free()
           
def frontToVentCanal():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳VentCanalReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "VentCanalReset"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)

    initial_ventcanal()

def frontFromVentCanal():
    save_ventcanal_info()
    need_to_delete_model_name_list = ['meshventcanal','ventcanal']
    for key in object_dic:
        need_to_delete_model_name_list.append(key)
    delete_useless_object(need_to_delete_model_name_list)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    resetname = name + "VentCanalReset"
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
        if (selected_obj.name == "右耳VentCanalReset" or selected_obj.name == "右耳VentCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

def backToVentCanal():
    exist_VentCanalReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳VentCanalReset"):
            exist_VentCanalReset = True
    if (exist_VentCanalReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "VentCanalReset"
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

        initial_ventcanal()
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳VentCanalLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳SoundCanalLast") != None):
            lastname = "右耳SoundCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
            bpy.context.collection.objects.link(ori_obj)
            moveToRight(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "VentCanalReset"
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

        initial_ventcanal()

def backFromVentCanal():
    save_ventcanal_info()
    submit_ventcanal()
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳VentCanalLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "VentCanalLast"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)

class addventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addventcanal"
    bl_label = "通气孔双击添加控制点"
    bl_description = (
        "使用鼠标双击添加控制点"
    )
    bl_icon = "ops.curves.sculpt_pinch"
    bl_widget = None
    bl_keymap = (
        ("object.ventcanalqiehuan", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class addventcanal_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addventcanal2"
    bl_label = "通气孔添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作"
    )
    bl_icon = "ops.curves.sculpt_pinch"
    bl_widget = None
    bl_keymap = (
        ("object.addventcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class finishventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishventcanal"
    bl_label = "通气孔完成"
    bl_description = (
        "完成管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_puff" 
    bl_widget = None
    bl_keymap = (
        ("object.finishventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class resetventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetventcanal"
    bl_label = "通气孔重置"
    bl_description = (
        "重置管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_slide"
    bl_widget = None
    bl_keymap = (
        ("object.resetventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

_classes = [
    TEST_OT_addventcanal,
    TEST_OT_ventcanalqiehuan,
    TEST_OT_finishventcanal,
    TEST_OT_resetventcanal
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(addventcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(resetventcanal_MyTool, separator=True, group=False,
                            after={addventcanal_MyTool.bl_idname})
    bpy.utils.register_tool(finishventcanal_MyTool, separator=True, group=False,
                            after={resetventcanal_MyTool.bl_idname})
    
    bpy.utils.register_tool(addventcanal_MyTool2, separator=True, group=False)
    
def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(addventcanal_MyTool)
    bpy.utils.unregister_tool(resetventcanal_MyTool)
    bpy.utils.unregister_tool(finishventcanal_MyTool)

    bpy.utils.unregister_tool(addventcanal_MyTool2)