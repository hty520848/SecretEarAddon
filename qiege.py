import bpy
from bpy import context
from bpy_extras import view3d_utils
import mathutils
import bmesh
from mathutils import Vector
from bpy.types import WorkSpaceTool
from .damo import *

# 当前的context
gcontext = ''


flag = 0
old_radius = 8.0
scale_ratio = 1

a = 1
# 初始化


def initCircle():
    global old_radius
    # 新增圆环
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=old_radius, fill_type='NGON', calc_uvs=True, enter_editmode=False,
                                      align='WORLD', location=(8.0, -6.6, 11), rotation=(0.0, 0.0, 0.0), scale=(0.0, 0.0, 0.0))

    # 选择圆环
    circle = bpy.context.active_object
    # 设置圆环显示为线框
    circle.display_type = 'WIRE'

    # 进入编辑模式
    # bpy.context.view_layer.objects.active = circle
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # 翻转圆环法线
    bpy.ops.mesh.flip_normals(only_clnors=False)

    # 返回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    # 为模型添加布尔修改器
    obj_main = bpy.data.objects['右耳']
    bool_modifier = obj_main.modifiers.new(
        name="Boolean Modifier", type='BOOLEAN')
    # 设置布尔修饰符作用对象
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = circle

    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.ops.object.circlecut('INVOKE_DEFAULT')


def new_sphere(name, loc):
    # 创建一个新的网格
    mesh = bpy.data.meshes.new("MyMesh")
    obj = bpy.data.objects.new(name, mesh)

    # 在场景中添加新的对象
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    # 切换到编辑模式
    # bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    for i in bpy.context.visible_objects:
        if i.name == name:
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')

    # 获取编辑模式下的网格数据
    bm = bmesh.from_edit_mesh(obj.data)

    # 设置圆球的参数
    radius = 0.1  # 半径
    segments = 32  # 分段数

    # 在指定位置生成圆球
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments,
                              radius=radius * 2)

    # 更新网格数据
    bmesh.update_edit_mesh(obj.data)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    # 设置圆球的位置
    obj.location = loc  # 指定的位置坐标


def new_plane(name):
    mesh = bpy.data.meshes.new("MyMesh")
    obj = bpy.data.objects.new(name, mesh)

    # 在场景中添加新的对象
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')
    for i in bpy.context.visible_objects:
        if i.name == name:
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    # 创建四个顶点
    verts = [bm.verts.new((0, 0, 0)),
             bm.verts.new((1, 0, 0)),
             bm.verts.new((1, 1, 0)),
             bm.verts.new((0, 1, 0))]

    # 创建两个面
    bm.faces.new(verts[:3])
    bm.faces.new(verts[1:])

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=True)

    # 更新网格数据
    bmesh.update_edit_mesh(obj.data)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    object = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(object.data)
    bm.faces.ensure_lookup_table()
    bm.faces[1].normal_flip()
    object.hide_set(True)

    bool_modifier = object.modifiers.new(
        name="smooth", type='BEVEL')
    bool_modifier.segments = 32
    bool_modifier.width = 0.4
    bool_modifier.limit_method = 'NONE'


def update_plane():

    # 获取坐标
    loc = [bpy.data.objects['mysphere1'].location,
           bpy.data.objects['mysphere2'].location,
           bpy.data.objects['mysphere3'].location,
           bpy.data.objects['mysphere4'].location]

    # 更新位置
    obj = bpy.data.objects['myplane']
    bm = obj.data
    if bm.vertices:
        for i in range(0, 4):
            vertex = bm.vertices[i]
            vertex.co = loc[i]

    mesh = bmesh.new()
    mesh.from_mesh(bm)

    mesh.verts.ensure_lookup_table()
    dis = (mesh.verts[1].co - mesh.verts[2].co).normalized()
    mesh.verts[1].co += dis*20
    mesh.verts[2].co -= dis*20
    dis2 = (mesh.verts[0].co-(mesh.verts[1].co +
            mesh.verts[2].co)/2).normalized()
    mesh.verts[0].co += dis2*20
    dis3 = (mesh.verts[3].co-(mesh.verts[1].co +
            mesh.verts[2].co)/2).normalized()
    mesh.verts[3].co += dis3*20

    # 更新网格数据
    mesh.to_mesh(bm)
    mesh.free()

def initialModelColor():
    yellow_material = bpy.data.materials.new(name="yellow")
    yellow_material.use_nodes = True
    bpy.data.materials["yellow"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1.0, 0.319, 0.133, 1.0)
    bpy.data.objects['右耳'].data.materials.append(yellow_material)


def initialTransparency():
    yellow_material = bpy.data.materials.new(name="yellow2")
    yellow_material.use_nodes = True
    bpy.data.materials["yellow2"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
        1.0, 0.319, 0.133, 1.0)
    yellow_material.blend_method = "BLEND"
    # 3.6
    yellow_material.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.5
    # 4.0
    yellow_material.node_tree.nodes["Principled BSDF"].inputs[4].default_value = 0.5
    # bpy.data.objects['右耳.001'].data.materials.append(yellow_material)


def initPlane():

    global a
    a = 2

    # 新建圆球
    new_sphere('mysphere1', (10.290, -8.958, 6.600))
    new_sphere('mysphere2', (5.266, -9.473, 6.613))
    new_sphere('mysphere3', (11.282, -2.077, 6.607))
    new_sphere('mysphere4', (8.107, -6.029, 13.345))
    new_plane('myplane')

    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    bpy.data.objects['mysphere1'].data.materials.append(red_material)
    bpy.data.objects['mysphere2'].data.materials.append(red_material)
    bpy.data.objects['mysphere3'].data.materials.append(red_material)
    bpy.data.objects['mysphere4'].data.materials.append(red_material)

    # 开启吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'CENTER'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True
    bpy.context.scene.tool_settings.use_snap_backface_culling = True

    for i in bpy.context.visible_objects:
        if i.name == "右耳":
            bpy.context.view_layer.objects.active = i
            obj = bpy.context.active_object
            obj_copy = obj.copy()
            obj_copy.data = obj.data.copy()
            obj_copy.animation_data_clear()
            scene = bpy.context.scene
            scene.collection.objects.link(obj_copy)
            obj.hide_select = True
            obj_copy.hide_select = True

    initialModelColor()
    initialTransparency()
    bpy.ops.object.select_all(action='DESELECT')

    plane = bpy.data.objects['myplane']
    # plane.data.materials.append(mat2)
    obj_main = bpy.data.objects['右耳']
    bool_modifier = obj_main.modifiers.new(
        name="step cut", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = plane
    # bool_modifier2 = obj_main.modifiers.new(
    #     name="Remesh", type='REMESH')
    # bool_modifier2.mode = 'VOXEL'

    # 调用调整按钮
    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.ops.wm.tool_set_by_id(name="builtin.select")
        bpy.ops.object.stepcut('INVOKE_DEFAULT')


# z轴自适应缩放

def scaleCircle():
    global old_radius
    global scale_ratio
    # 获取圆环的z坐标
    obj = bpy.data.objects['Circle']
    jobj = obj.location[2]
    print('圆环的z坐标', jobj)

    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects['右耳']
    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)

    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        jobj, 2) + 0.1 and round(v.co.z, 2) > round(jobj, 2) - 0.1]

    if selected_verts:
        # 计算平面的几何中心
        center = sum((v.co for v in selected_verts),
                     Vector()) / len(selected_verts)
        # 输出几何中心坐标
        print("Geometry Center:", center)

    # 初始化最大距离为负无穷大
    max_distance = float('-inf')

    # 遍历的每个顶点并计算距离
    for vertex in selected_verts:
        distance = (vertex.co - center).length
        max_distance = max(max_distance, distance)

    # 输出最大距离
    # print("最大距离:", max_distance)

    # 缩放比例
    scale_ratio *= round(max_distance/old_radius, 5)
    old_radius = max_distance
    print('半径', old_radius)
    print("缩放比例:", scale_ratio)

    # 缩放圆环大小
    obj.scale[0] = scale_ratio+0.2
    obj.scale[1] = scale_ratio+0.2
    obj.scale[2] = scale_ratio+0.2

    # 移动圆环到几何中心
    obj.location[0] = round(center.x, 2)
    obj.location[1] = round(center.y, 2)

    bm.free()

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

# 获取VIEW_3D区域的上下文


def getOverride():
    # change this to use the correct Area Type context you want to process in
    area_type = 'VIEW_3D'
    areas = [
        area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(
            f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override


# 退出操作
def quitCut():
    for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
        if i.name == "右耳":
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)
    bpy.ops.object.modifier_remove(modifier='Boolean Modifier', report=False)
    global a
    a = 2
    if (bpy.data.objects['Circle']):
        obj = bpy.data.objects['Circle']
        bpy.data.objects.remove(obj, do_unlink=True)


def quitStepCut():
    for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
        if i.name == "右耳":
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)
    bpy.ops.object.modifier_remove(modifier='step cut', report=False)
    global a
    a = 1
    if (bpy.data.objects['mysphere1']):
        obj = bpy.data.objects['mysphere1']
        bpy.data.objects.remove(obj, do_unlink=True)
    if (bpy.data.objects['mysphere2']):
        obj = bpy.data.objects['mysphere2']
        bpy.data.objects.remove(obj, do_unlink=True)
    if (bpy.data.objects['mysphere3']):
        obj = bpy.data.objects['mysphere3']
        bpy.data.objects.remove(obj, do_unlink=True)
    if (bpy.data.objects['mysphere4']):
        obj = bpy.data.objects['mysphere4']
        bpy.data.objects.remove(obj, do_unlink=True)
    if (bpy.data.objects['myplane']):
        obj = bpy.data.objects['myplane']
        bpy.data.objects.remove(obj, do_unlink=True)
    if (bpy.data.objects['右耳.001']):
        obj = bpy.data.objects['右耳.001']
        bpy.data.objects.remove(obj, do_unlink=True)


class Circle_Cut(bpy.types.Operator):
    bl_idname = "object.circlecut"
    bl_label = "圆环切割"

    __initial_rotation_x = None  # 初始x轴旋转角度
    __left_mouse_down = False  # 按下右键未松开时，旋转圆环角度
    __right_mouse_down = False  # 按下右键未松开时，圆环上下移动
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    def invoke(self, context, event):
        op_cls = Circle_Cut
        print('invoke')
        op_cls.__initial_rotation_x = None
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None

        global a
        a = 1

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Circle_Cut

        if context.area:
            context.area.tag_redraw()

        global gcontext
        global a
        if gcontext == 'VIEW_LAYER':
            # 鼠标是否在圆环上
            if (a == 1 and is_mouse_on_object(context, event)):
                active_obj = bpy.data.objects['Circle']
                # print('在圆环上')
                if event.type == 'LEFTMOUSE':
                    if event.value == 'PRESS':
                        op_cls.__left_mouse_down = True
                        op_cls.__initial_rotation_x = active_obj.rotation_euler[0]
                        op_cls.__initial_mouse_x = event.mouse_region_x
                    # 取消
                    elif event.value == 'RELEASE':
                        op_cls.__left_mouse_down = False
                        op_cls.__initial_rotation_x = None
                        op_cls.__initial_mouse_x = None
                    return {'RUNNING_MODAL'}

                elif event.type == 'RIGHTMOUSE':
                    if event.value == 'PRESS':
                        print('右键press')
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                    elif event.value == 'RELEASE':
                        print('右键release')
                        op_cls.__right_mouse_down = False
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    # 左键按住旋转
                    if op_cls.__left_mouse_down:
                        # x轴旋转角度
                        rotate_angle_x = (
                            event.mouse_region_x - op_cls.__initial_mouse_x) * 0.01
                        active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                            rotate_angle_x
                        return {'RUNNING_MODAL'}
                    elif op_cls.__right_mouse_down:
                        obj = bpy.data.objects['Circle']
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        print(event.mouse_prev_x)
                        print(event.mouse_x)
                        # dis = int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)+fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                        dis = (op_cls.__now_mouse_y -
                               op_cls.__initial_mouse_y)*0.01
                        # dis = 0.1
                        print('移动的距离', dis)
                        # 法线方向
                        # print(active_obj.name)
                        # print(active_obj.location[2])
                        normal = obj.data.polygons[0].normal
                        obj.location += normal*dis
                        # if(op_cls.__now_mouse_y > op_cls.__initial_mouse_y) or (op_cls.__now_mouse_x > op_cls.__initial_mouse_x):
                        #     obj.location += normal*dis
                        # else:
                        #     obj.location -= normal*dis

                        scaleCircle()
            else:
                # print('不在圆环上')
                pass
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}

    def cast_ray(self, context, event):

        # cast ray from mouse location, return data from ray
        scene = context.scene
        region = context.region
        rv3d = context.region_data
        print('rv3d', rv3d)
        print('area', region.type)
        coord = event.mouse_region_x, event.mouse_region_y
        viewlayer = context.view_layer.depsgraph
        # get the ray from the viewport and mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        hit, location, normal, index, object, matrix = scene.ray_cast(
            viewlayer, ray_origin, view_vector)
        return hit, location, normal, index, object, matrix


class Step_Cut(bpy.types.Operator):
    bl_idname = "object.stepcut"
    bl_label = "阶梯切割"

    __timer = None

    def invoke(self, context, event):
        op_cls = Step_Cut
        print('invoke')
        global a
        a = 2
        op_cls.__timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        update_plane()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Step_Cut

        if context.area:
            context.area.tag_redraw()

        global gcontext
        global a
        if gcontext == 'VIEW_LAYER':
            # 鼠标是否在圆环上
            if (a == 2 and is_mouse_on_which_object(context, event) != 5):

                if event.type == 'TIMER':
                    update_plane()

                return {'PASS_THROUGH'}

            elif (a == 1):
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
                return {'FINISHED'}
            else:
                return {'PASS_THROUGH'}

        else:
            return {'PASS_THROUGH'}


class Finish_Cut(bpy.types.Operator):
    bl_idname = "object.finishcut"
    bl_label = "完成切割"

    def invoke(self, context, event):
        self.excute(context)
        return {'FINISHED'}

    def excute(self, context):
        global a
        if (a == 1):
            for i in bpy.context.visible_objects:
                if i.name == "右耳":
                    bpy.context.view_layer.objects.active = i
                    bpy.ops.object.modifier_apply(modifier="Boolean Modifier")
            bpy.data.objects.remove(bpy.data.objects['Circle'], do_unlink=True)
            a = 3

        if (a == 2):
            for i in bpy.context.visible_objects:
                if i.name == "右耳":
                    bpy.context.view_layer.objects.active = i
                    bpy.ops.object.modifier_apply(modifier="step cut")
            for i in bpy.context.visible_objects:
                if i.name == "myplane":
                    i.hide_set(False)
                    bpy.context.view_layer.objects.active = i
                    bpy.ops.object.modifier_apply(modifier="smooth")
            bpy.data.objects.remove(
                bpy.data.objects['mysphere1'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['mysphere2'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['mysphere3'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['mysphere4'], do_unlink=True)
            bpy.data.objects.remove(
                bpy.data.objects['myplane'], do_unlink=True)
            bpy.data.objects.remove(bpy.data.objects['右耳.001'], do_unlink=True)
            # bpy.ops.object.modifier_apply(modifier="Remesh")
            a = 3

        return {'FINISHED'}
    
class Reset_Cut(bpy.types.Operator):
    bl_idname = "object.resetcut"
    bl_label = "完成重置"

    def invoke(self, context, event):
        print('invoke')
        self.excute(context)
        return {'FINISHED'}

    def excute(self, context):
        global a
        if (a == 1):
            for i in bpy.context.visible_objects:
                if i.name == "右耳":
                    bpy.context.view_layer.objects.active = i
                    bpy.ops.object.modifier_remove(modifier="Boolean Modifier")
            bpy.data.objects.remove(bpy.data.objects['Circle'], do_unlink=True)
            initCircle()
            a = 4

        if (a == 2):
            # 回到原来的位置
            bpy.data.objects['mysphere1'].location = (10.290, -8.958, 6.600) 
            bpy.data.objects['mysphere2'].location = (5.266, -9.473, 6.613)
            bpy.data.objects['mysphere3'].location = (11.282, -2.077, 6.607)
            bpy.data.objects['mysphere4'].location = (8.107, -6.029, 13.345)
            update_plane()
            bpy.ops.mesh.select_all(action='DESELECT')
            a = 4

        return {'FINISHED'}


class qiegeTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishcut"
    bl_label = "完成"
    bl_description = (
        "点击完成切割操作"
    )
    bl_icon = "ops.mesh.inset"
    bl_widget = None
    bl_keymap = (
        ("object.finishcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass

class qiegeTool2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetcut"
    bl_label = "重置切割"
    bl_description = (
        "点击完成重置操作"
    )
    bl_icon = "ops.mesh.inset"
    bl_widget = None
    bl_keymap = (
        ("object.resetcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass

# 监听回调函数
def msgbus_callback(*args):
    global gcontext
    global flag
    global a
    current_tab = bpy.context.screen.areas[0].spaces.active.context
    gcontext = current_tab
    if (current_tab == 'VIEW_LAYER'):
        flag = True
        if flag:
            initCircle()
        # override = getOverride()
        # with bpy.context.temp_override(**override):
        #     bpy.ops.object.circlecut('INVOKE_DEFAULT')
    else:
        if (flag):
            flag == False
            # TODO:测试用
            # if (a == 1):
            #     quitCut()
            # if (a == 2):
            #     quitStepCut()
    print(f'Current Tab: {current_tab}')


# 监听属性
subscribe_to = bpy.types.SpaceProperties, 'context'

# 发布订阅，监听context变化
bpy.msgbus.subscribe_rna(
    key=subscribe_to,
    owner=object(),
    args=(1, 2, 3),
    notify=msgbus_callback,
)

# bpy.utils.register_class(Circle_Cut)


def register():
    bpy.utils.register_class(Circle_Cut)
    bpy.utils.register_class(Step_Cut)
    bpy.utils.register_class(Finish_Cut)
    bpy.utils.register_class(Reset_Cut)

    bpy.utils.register_tool(qiegeTool, separator=True, group=False)
    bpy.utils.register_tool(qiegeTool2, separator=True, group=False, after={qiegeTool.bl_idname})

def unregister():
    bpy.utils.unregister_class(Circle_Cut)
    bpy.utils.unregister_class(Step_Cut)
    bpy.utils.unregister_class(Finish_Cut)
    bpy.utils.unregister_class(Reset_Cut)

    bpy.utils.unregister_tool(qiegeTool)
    bpy.utils.unregister_tool(qiegeTool2)






    # # 创建一个新的集合
    # collection = bpy.data.collections.new("MyCollection")

    # # 将新的集合添加到场景中
    # bpy.context.scene.collection.children.link(collection)

    # # 获取当前场景
    # scene = bpy.context.scene

    # # 遍历场景中的所有集合
    # for collection in scene.collection.children:
    #     if collection.name == "MyCollection":
    #         bpy.context.view_layer.active_layer_collection =  bpy.context.view_layer.layer_collection.children[collection.name]

    # # 获取要删除的集合
    # collection = bpy.data.collections.get("MyCollection")

    # # 如果集合存在，则删除它
    # if collection:
    #     bpy.data.collections.remove(collection)
