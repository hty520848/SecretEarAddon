import bpy
from bpy import context
from bpy_extras import view3d_utils
import mathutils
import bmesh
from mathutils import Vector
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


def initPlane():
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
    global a
    a = 2
    # 新增立方体
    bpy.ops.mesh.primitive_cube_add(enter_editmode=True,
                                    align='WORLD',
                                    location=(11.8, -9, 14.2),
                                    rotation=(0.0, 0.0, -2.26),
                                    scale=(6.05, 6.05, 6.05))
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    # 选择平面
    bpy.ops.object.mode_set(mode='OBJECT')
    plane = bpy.context.active_object

    # 删除多余的平面
    # bpy.context.view_layer.objects.active = circle
    bm = bmesh.new()
    bm.from_mesh(plane.data)
    bm.faces.ensure_lookup_table()
    bm.faces[0].select = True
    bm.faces[1].select = True
    bm.faces[2].select = True
    bm.faces[3].select = False
    bm.faces[4].select = False
    bm.faces[5].select = True
    bm.to_mesh(plane.data)
    bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    # #分离平面
    # bm2 = bmesh.new()
    # bm2.from_mesh(plane.data)
    # bm2.faces.ensure_lookup_table()
    # bm2.faces[0].select = True
    # bm2.faces[1].select = False
    # bm2.to_mesh(plane.data)
    # bm2.free()
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.separate(type='SELECTED')
    # bpy.ops.object.mode_set(mode='OBJECT')

    # 应用变换
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 为模型添加布尔修改器
    obj_main = bpy.data.objects['右耳']
    bool_modifier = obj_main.modifiers.new(
        name="step cut", type='BOOLEAN')
    # 设置布尔修饰符作用对象
    # bool_modifier.operand_type = 'COLLECTION'
    bool_modifier.operation = 'DIFFERENCE'
    bool_modifier.object = plane
    # bool_modifier.collection = bpy.data.collections['MyCollection']

    # TODO: 添加圆柱体在平面上
    bm1 = bmesh.new()
    bm1.from_mesh(plane.data)
    bm1.faces.ensure_lookup_table()
    x = 0
    y = 0
    z = 0
    for vert in bm1.faces[0].verts:
        x += vert.co.x
        y += vert.co.y
        z += vert.co.z
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD',
                                        location=(x/4, y/4, z/4-3),
                                        scale=(0.5, 0.5, 1),
                                        rotation=(1.57, 0.0, -2.26))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bm2 = bmesh.new()
    bm2.from_mesh(plane.data)
    bm2.faces.ensure_lookup_table()
    x = 0
    y = 0
    z = 0
    for vert in bm2.faces[1].verts:
        x += vert.co.x
        y += vert.co.y
        z += vert.co.z
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD',
                                        location=(x/4-3, y/4+3, z/4),
                                        scale=(0.5, 0.5, 1))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
        if i.name == "Cube":
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)
            i.hide_set(True)

    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.ops.object.stepcut('INVOKE_DEFAULT')

# z轴自适应缩放


def scaleCircle():
    global old_radius
    global scale_ratio
    # 获取圆环的z坐标
    obj_circle = bpy.data.objects['Circle']
    z_circle = obj_circle.location[2]
    print('圆环的z坐标', z_circle)

    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects['右耳']
    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)

    # 选取Z坐标相等的顶点
    selected_verts = [v for v in bm.verts if round(v.co.z, 2) < round(
        z_circle, 2) + 0.1 and round(v.co.z, 2) > round(z_circle, 2) - 0.1]

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
    obj_circle.scale[0] = scale_ratio+0.2
    obj_circle.scale[1] = scale_ratio+0.2
    obj_circle.scale[2] = scale_ratio+0.2

    # 移动圆环到几何中心
    obj_circle.location[0] = round(center.x, 2)
    obj_circle.location[1] = round(center.y, 2)

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
        obj_circle = bpy.data.objects['Circle']
        bpy.data.objects.remove(obj_circle, do_unlink=True)


def quitStepCut():
    for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
        if i.name == "右耳":
            bpy.context.view_layer.objects.active = i
            i.select_set(state=True)
    bpy.ops.object.modifier_remove(modifier='step cut', report=False)
    global a
    a = 1
    if (bpy.data.objects['Cube']):
        obj_circle = bpy.data.objects['Cube']
        bpy.data.objects.remove(obj_circle, do_unlink=True)
    # if (bpy.data.objects['Cube.001']):
    #     obj_circle = bpy.data.objects['Cube']
    #     bpy.data.objects.remove(obj_circle, do_unlink=True)

    # # 获取要删除的集合
    # collection = bpy.data.collections.get("MyCollection")

    # # 如果集合存在，则删除它
    # if collection:
    #     bpy.data.collections.remove(collection)


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
                        obj_circle = bpy.data.objects['Circle']
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
                        normal = obj_circle.data.polygons[0].normal
                        obj_circle.location += normal*dis
                        # if(op_cls.__now_mouse_y > op_cls.__initial_mouse_y) or (op_cls.__now_mouse_x > op_cls.__initial_mouse_x):
                        #     obj_circle.location += normal*dis
                        # else:
                        #     obj_circle.location -= normal*dis

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

    __initial_rotation_x = None  # 初始x轴旋转角度
    __left_mouse_down = False  # 按下右键未松开时，旋转圆环角度
    __right_mouse_down = False  # 按下右键未松开时，圆环上下移动
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    def invoke(self, context, event):
        op_cls = Step_Cut
        print('invoke')
        op_cls.__initial_rotation_x = None
        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None

        global a
        a = 2

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Step_Cut

        if context.area:
            context.area.tag_redraw()

        global gcontext
        global a
        if gcontext == 'VIEW_LAYER':
            # 鼠标是否在圆环上
            if (a == 2 and (is_mouse_on_which_object(context, event) != -1)):
                index = is_mouse_on_which_object(context, event)
                if (index == 0):
                    # TODO:激活物体
                    bpy.ops.object.select_all(action='DESELECT')
                    for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
                        if i.name == "Cylinder":
                            bpy.context.view_layer.objects.active = i
                            i.select_set(state=True)
                    active_obj = bpy.data.objects['Cylinder']
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
                    elif event.type == 'MOUSEMOVE':
                        # 左键按住旋转
                        if op_cls.__left_mouse_down:
                            # x轴旋转角度
                            rotate_angle_x = (
                                event.mouse_region_x - op_cls.__initial_mouse_x) * 0.01
                            active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                                rotate_angle_x
                            return {'RUNNING_MODAL'}
                if (index == 1):
                    bpy.ops.object.select_all(action='DESELECT')
                    for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
                        if i.name == "Cylinder.001":
                            bpy.context.view_layer.objects.active = i
                            i.select_set(state=True)
                    active_obj = bpy.data.objects['Cylinder.001']
                    return {'RUNNING_MODAL'}
                    # if event.type == 'LEFTMOUSE':
                    #     if event.value == 'PRESS':
                    #         op_cls.__left_mouse_down = True
                    #         op_cls.__initial_rotation_x = active_obj.rotation_euler[0]
                    #         op_cls.__initial_mouse_x = event.mouse_region_x
                    #     # 取消
                    #     elif event.value == 'RELEASE':
                    #         op_cls.__left_mouse_down = False
                    #         op_cls.__initial_rotation_x = None
                    #         op_cls.__initial_mouse_x = None
                    #     return {'RUNNING_MODAL'}

                    # elif event.type == 'RIGHTMOUSE':
                    #     if event.value == 'PRESS':
                    #         print('右键press')
                    #         op_cls.__right_mouse_down = True
                    #         op_cls.__initial_mouse_x = event.mouse_region_x
                    #         op_cls.__initial_mouse_y = event.mouse_region_y
                    #     elif event.value == 'RELEASE':
                    #         print('右键release')
                    #         op_cls.__right_mouse_down = False
                    #     return {'RUNNING_MODAL'}

                    # elif event.type == 'MOUSEMOVE':
                    #     # 左键按住旋转
                    #     if op_cls.__left_mouse_down:
                    #         # x轴旋转角度
                    #         rotate_angle_x = (
                    #             event.mouse_region_x - op_cls.__initial_mouse_x) * 0.01
                    #         active_obj.rotation_euler[0] = op_cls.__initial_rotation_x + \
                    #             rotate_angle_x
                    #         return {'RUNNING_MODAL'}
                    #     elif op_cls.__right_mouse_down:
                    #         obj_circle = bpy.data.objects['Circle']
                    #         op_cls.__now_mouse_y = event.mouse_region_y
                    #         op_cls.__now_mouse_x = event.mouse_region_x
                    #         print(event.mouse_prev_x)
                    #         print(event.mouse_x)
                    #         # dis = int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)+fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                    #         dis = (op_cls.__now_mouse_y -
                    #             op_cls.__initial_mouse_y)*0.01
                    #         # dis = 0.1
                    #         print('移动的距离', dis)
                    #         # 法线方向
                    #         # print(active_obj.name)
                    #         # print(active_obj.location[2])
                    #         normal = obj_circle.data.polygons[0].normal
                    #         obj_circle.location += normal*dis
                    #         # if(op_cls.__now_mouse_y > op_cls.__initial_mouse_y) or (op_cls.__now_mouse_x > op_cls.__initial_mouse_x):
                    #         #     obj_circle.location += normal*dis
                    #         # else:
                    #         #     obj_circle.location -= normal*dis

            else:
                # print('不在圆环上')
                pass
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}
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
            if (a == 1):
                quitCut()
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


def unregister():
    bpy.utils.unregister_class(Circle_Cut)
    bpy.utils.unregister_class(Step_Cut)
