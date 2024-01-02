import bpy
import bmesh
import mathutils
from bpy_extras import view3d_utils
from math import sqrt

index_initial = -1 #记录第一次点击蓝线时的下标索引
index_finish = -1  #记录结束时点击蓝线的的下标索引

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

def co_on_object(context, event):
    active_obj = bpy.data.objects['curve']

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
                return co # 如果发生交叉，返回坐标的值
    return -1

def select_nearest_point(co):

    # 获取当前选择的曲线对象
    curve_obj = bpy.data.objects['operatecurve']
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

def join_curve():
    # 获取两条曲线对象
    curve_obj1 = bpy.data.objects['operatecurve']
    curve_obj2 = bpy.data.objects['point']

    bpy.context.view_layer.objects.active = curve_obj2
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj2.select_set(state=True)
    bpy.context.object.data.bevel_depth = 0

    # 获取两条曲线的曲线数据
    curve_data1 = curve_obj1.data
    curve_data2 = curve_obj2.data

    # 创建一个新的曲线对象
    new_curve_data = bpy.data.curves.new(name="secondoperatecurve", type='CURVE')
    new_curve_obj = bpy.data.objects.new(name="secondoperatecurve", object_data=new_curve_data)

    # 将新的曲线对象添加到场景中
    bpy.context.collection.objects.link(new_curve_obj)

    # 获取新曲线对象的曲线数据
    new_curve_data = new_curve_obj.data

    # 合并两条曲线的点集
    new_curve_data.splines.clear()
    new_spline = new_curve_data.splines.new(type=curve_data1.splines[0].type)
    new_spline.points.add(len(curve_data1.splines[0].points) + len(curve_data2.splines[0].points) - 1)

    # 将第一条曲线的点复制到新曲线
    for i, point in enumerate(curve_data1.splines[0].points):
        new_spline.points[i].co = point.co

    # 将第二条曲线的点复制到新曲线
    for i, point in enumerate(curve_data2.splines[0].points):
        new_spline.points[i + len(curve_data1.splines[0].points) - 1].co = point.co

    bpy.data.objects.remove(bpy.data.objects['operatecurve'],do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects['point'],do_unlink=True)
    new_curve_obj.name = 'operatecurve'


def join_object():

    join_curve() #合并曲线对象
 
    copy_curve('operatecurve')  #复制一份曲线数据
    bpy.data.objects.remove(bpy.data.objects['curve'],do_unlink=True) #删除原有蓝线
    obj = bpy.data.objects['newoperatecurve'] 
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.context.object.data.bevel_depth = 0.1 #设置曲线倒角深度为0.1
    bpy.ops.object.convert(target='MESH') #转化为网格
    bpy.data.objects['newoperatecurve'].data.materials.append(bpy.data.materials['blue'])
    bpy.data.objects['newoperatecurve'].name = 'curve'

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

class TEST_OT_doubleclick(bpy.types.Operator):

    bl_idname = "object.doubleclick"
    bl_label = "doubleclick"
    bl_description = "双击蓝线改变蓝线形态"

    def excute(self, context, event):
        global index_initial
        global index_finish
        if co_on_object(context, event) == -1:  #双击位置不在曲线上不做任何事
            print("不在曲线上")

        else:
            if bpy.context.mode == 'OBJECT':   #如果处于物体模式下，蓝线双击开始绘制
                co = co_on_object(context, event)
                index = select_nearest_point(co)
                print("在曲线上最近点的下标是",index)
                index_initial = index
                curve_obj = bpy.data.objects['operatecurve']
                bpy.context.view_layer.objects.active = curve_obj
                bpy.ops.object.select_all(action='DESELECT')
                curve_obj.select_set(state=True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                curve_obj.data.splines[0].points[index].select = True
                bpy.ops.curve.separate() #分离将要进行操作的点
                bpy.ops.object.mode_set(mode='OBJECT')
                for object in bpy.data.objects:  #改名
                    if object.name == 'operatecurve.001':
                        print('select copy object')
                        object.name = 'point'
                        break
                bpy.context.view_layer.objects.active = bpy.data.objects['point']
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects['point'].select_set(state=True)

                bpy.ops.object.mode_set(mode='EDIT')   #进入编辑模式进行操作
                bpy.ops.curve.select_all(action='SELECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.extrude_cursor")  #调用挤出至光标工具
                bpy.context.object.data.bevel_depth = 0.1                 #设置倒角深度
                bpy.data.objects['point'].data.materials.append(bpy.data.materials['blue'])
                # 开启吸附
                bpy.context.scene.tool_settings.use_snap = True
                bpy.context.scene.tool_settings.snap_elements = {'FACE'}
                bpy.context.scene.tool_settings.snap_target = 'CENTER'
                bpy.context.scene.tool_settings.use_snap_align_rotation = True
                bpy.context.scene.tool_settings.use_snap_backface_culling = True
                
            elif bpy.context.mode == 'EDIT_CURVE': #如果处于编辑模式下，蓝线双击确认完成
                print("起始位置的下标是",index_initial)
                co = co_on_object(context, event)
                index_finish = select_nearest_point(co)
                print("在曲线上最近点的下标是",index_finish)
                bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式
                curve_obj = bpy.data.objects['operatecurve']
                bpy.context.view_layer.objects.active = curve_obj
                bpy.ops.object.select_all(action='DESELECT')
                curve_obj.select_set(state=True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.select_all(action='DESELECT')
                for i in range(index_initial,index_finish,1):  #选中两个索引中的点
                    curve_obj.data.splines[0].points[i].select = True
                bpy.ops.curve.delete(type='SEGMENT')      #删除选中的顶点
                # bpy.ops.curve.delete(type='VERT')  
                bpy.ops.object.mode_set(mode='OBJECT') #返回对象模式
                bpy.context.scene.tool_settings.use_snap = False #取消吸附
                join_object() #合并物体

            else:
                pass

    def invoke(self, context, event):
        if checkinitialBlueColor() == False:
            initialBlueColor() 
        self.excute(context,event)
        return {'FINISHED'}



class MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.doubleclick"
    bl_label = "双击"
    bl_description = (
        "使用鼠标双击添加点"
    )
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        ("object.doubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass
            
bpy.utils.register_class(TEST_OT_doubleclick)

bpy.utils.register_tool(MyTool, separator=True, group=False)