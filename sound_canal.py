import bpy
import bmesh
import mathutils
from bpy_extras import view3d_utils
from math import sqrt
from .tool import newShader

prev_on_object = 0
number = 0  #记录管道控制点点的个数
object_list = [ ] #记录当前圆球的物体列表

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

def is_changed(context, event):
    '''
    判断鼠标状态是否发生改变
    '''
    global object_list
    global prev_on_object  # 之前鼠标在哪个物体上

    for name in object_list:
        active_obj = bpy.data.objects[name]
        curr_on_object = 0            # 当前鼠标在那个物体上,初始化为0
        object_index = int(name.replace('cannelsphere',''))

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
                    curr_on_object = object_index
                    print(object_index)                     # 如果发生交叉，将变量设为True
                    break

    if (prev_on_object != curr_on_object):
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

            co, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                return co   # 如果发生交叉，返回坐标的值

    return -1

def select_nearest_point(co):
    '''
    选择曲线上离坐标位置最近的两个点
    :param co: 坐标的值
    :return: 最近两个点的下标
    '''
    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects['canal']
    # 获取曲线的数据
    curve_data = curve_obj.data
    # 遍历曲线的所有点
    min_dis = float('inf')
    secondmin_dis = float('inf')
    min_dis_index = -1
    secondmin_dis_index = -1

    for spline in curve_data.splines:
        for point_index, point in enumerate(spline.points):
            # 计算点与给定点之间的距离
            distance = sqrt(sum((a - b) ** 2 for a, b in zip(point.co, co)))
            # 更新最小距离和对应的点索引
            if distance < secondmin_dis:
                secondmin_dis = distance
                secondmin_dis_index = point_index
                if distance < min_dis:
                    min_dis = distance
                    min_dis_index = point_index

    return (min_dis_index,secondmin_dis_index)

def initialRedColor():
    ''' 生成红色材质 '''
    material = bpy.data.materials.new(name="red")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1, 0, 0, 1.0)
    
def checkinitialRedColor():
    ''' 确认是否生成红色材质 '''
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'red':
            return True
    return False

def initialGreyColor():
    ''' 生成灰色材质 '''
    material = bpy.data.materials.new(name="grey")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1, 1, 1, 0.8)
    material.blend_method = "BLEND"
    material.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2

def checkinitialGreyColor():
    ''' 确认是否生成灰色材质 '''
    materials = bpy.data.materials
    for material in materials:
        if material.name == 'grey':
            return True
    return False

def checkmesh():
    objects = bpy.data.objects
    mesh_name = 'meshcannal'
    for object in objects:
        if object.name == mesh_name:
            return True
    return False

def convert_to_mesh():
    active_obj = bpy.data.objects['canal']
    duplicate_obj = active_obj.copy()
    if(checkmesh() == True):
        bpy.data.objects.remove(bpy.data.objects['meshcanal'], do_unlink=True)  # 删除原有网格
    duplicate_obj.data = active_obj.data.copy()
    duplicate_obj.name = "mesh" + active_obj.name 
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(state=True)
    while(bpy.context.active_object.modifiers):
        modifer_name = bpy.context.active_object.modifiers[0].name
        bpy.ops.object.modifier_apply(modifier = modifer_name)
    bpy.context.object.data.bevel_depth = 1 # 设置曲线倒角深度
    bpy.ops.object.convert(target='MESH')  # 转化为网格


def add_sphere(co,index):
    ''' 
    在指定位置生成圆球用于控制管道曲线的移动 
    :param co:指定的坐标
    :param index:指定要钩挂的控制点的下标
    '''
    global number
    global object_list
    number += 1
    # 创建一个新的网格
    mesh = bpy.data.meshes.new("MyMesh")
    name = 'cannelsphere' + str(number)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    object_list.append(name)
    # 切换到编辑模式
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT')

    # 获取编辑模式下的网格数据
    bm = bmesh.from_edit_mesh(obj.data)

    # 设置圆球的参数
    radius = 0.3  # 半径
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
    hooktoobject(index)

class TEST_OT_addcanal(bpy.types.Operator):

    bl_idname = "object.addcanal"
    bl_label = "addcannal"
    bl_description = "双击添加管道控制点"

    def excute(self, context, event):
        
        global number
        name = '右耳'
        mesh_name = 'meshcanal'
        if cal_co(name, context, event) == -1:
            print("不在物体上")
            if(number > 2 and cal_co(mesh_name,context,event) == -1):  # 双击位置不在曲线上不做任何事
                print("不在曲线上")
            elif(number > 2 and cal_co(mesh_name,context,event) != -1):
                print('在曲线上')
    
        else:
            if  number == 0 :  # 如果number等于0，初始化
                co = cal_co(name, context, event)
                generate_canal(co)

            elif number == 1 :   # 如果number等于1双击完成管道
                co = cal_co(name, context, event)
                finish_canal(co)
                bpy.data.objects['右耳'].data.materials.clear()  #清除材质
                bpy.data.objects['右耳'].data.materials.append(bpy.data.materials["Transparency"])
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')

            else:    # 如果numberd大于1，双击添加控制点
                co = cal_co(name, context, event)
                min_index, secondmin_index = select_nearest_point(co)
                add_canal(min_index, secondmin_index)
                
    def invoke(self, context, event):
        if checkinitialRedColor() == False:
            initialRedColor()
        if checkinitialGreyColor() == False:
            initialGreyColor()
        initialTransparency()
        self.excute(context, event)
        return {'FINISHED'}
    
class TEST_OT_qiehuan(bpy.types.Operator):

    bl_idname = "object.soundcanalqiehuan"
    bl_label = "soundcanalqiehuan"
    bl_description = "鼠标行为切换"


    def invoke(self, context, event): #初始化
        print('soundcanalqiehuan invoke')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        global prev_on_object
        if(is_changed(context,event) == True and prev_on_object == 0):
            bpy.ops.wm.tool_set_by_id(name="builtin.select")
        elif(is_changed(context,event) == True and prev_on_object != 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.addcanal")

        return {'PASS_THROUGH'}
    
def generate_canal(co):
    ''' 初始化管道 '''
    global number
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name='newcurve', type='CURVE')
    curve_data.dimensions = '3D'

    obj = bpy.data.objects.new('canal', curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.data.bevel_depth = 1 #管道孔径
    obj.hide_select = True
    obj.data.materials.append(bpy.data.materials["grey"])

    # 添加一个曲线样条
    spline = curve_data.splines.new('NURBS')
    spline.order_u = 3
    spline.points[number].co[0:3] = co
    spline.points[number].co[3] = 1
    #spline.use_cyclic_u = True

    add_sphere(co,0)
    
def add_canal(min_index, secondmin_index):
    ''' 在管道上增加控制点 '''
    global number
    curve_object = bpy.data.objects['canal']
    curve_data = curve_object.data
    bpy.context.view_layer.objects.active = curve_object
    bpy.ops.object.select_all(action='DESELECT')
    curve_object.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT') #进入编辑模式
    bpy.ops.curve.select_all(action='DESELECT')
    curve_data.splines[0].points[min_index].select = True
    curve_data.splines[0].points[secondmin_index].select = True
    bpy.ops.curve.subdivide(number_cuts=1) #细分次数
    bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式
    add_index = max(min_index,secondmin_index)
    temp_co = curve_data.splines[0].points[add_index]
    add_sphere(temp_co,add_index)

def finish_canal(co):
    ''' 完成管道的初始化 '''
    global number
    curve_object = bpy.data.objects['canal']
    curve_data = curve_object.data
    curve_data.splines[0].points.add(count = 1)
    curve_data.splines[0].points[number].co[0:3] = co
    curve_data.splines[0].points[number].co[3] = 1
    add_sphere(co,1)
    bpy.context.view_layer.objects.active = curve_object
    bpy.ops.object.select_all(action='DESELECT')
    curve_object.select_set(state=True)
    bpy.ops.object.mode_set(mode='EDIT') #进入编辑模式
    bpy.ops.curve.select_all(action='DESELECT')
    curve_data.splines[0].points[0].select = True
    curve_data.splines[0].points[1].select = True
    bpy.ops.curve.subdivide(number_cuts=1) #细分次数
    bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式
    bpy.data.objects['右耳'].hide_select = True
    temp_co = curve_data.splines[0].points[1].co[0:3]
    add_sphere(temp_co,1)
    convert_to_mesh()

def hooktoobject(index):
    ''' 将指定下标的控制点钩挂到圆球 '''
    global number
    sphere_name = 'cannelsphere' + str(number)
    sphere_object = bpy.data.objects[sphere_name]
    curve_object = bpy.data.objects['canal']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = curve_object
    curve_object.select_set(True)
    sphere_object.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT') #进入编辑模式
    bpy.ops.curve.select_all(action='DESELECT')
    curve_object.data.splines[0].points[index].select = True
    bpy.ops.object.hook_add_selob(use_bone=False)
    bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式

class addcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addcanal"
    bl_label = "双击添加控制点"
    bl_description = (
        "使用鼠标双击添加控制点"
    )
    bl_icon = "ops.mesh.knife_tool"  # TODO:修改图标
    bl_widget = None
    bl_keymap = (
        ("object.addcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

_classes = [
    TEST_OT_addcanal,
    TEST_OT_qiehuan
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(addcanal_MyTool, separator=True, group=False)

def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(addcanal_MyTool)