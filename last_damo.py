import bpy
from bpy.types import WorkSpaceTool
from .tool import *
from math import *
import mathutils
import bmesh
import bpy_extras
from bpy_extras import view3d_utils
import math
from pynput import mouse


prev_on_object = False  # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体上)

damo_mouse_listener = None  # 添加鼠标监听
left_mouse_press = False  # 鼠标左键是否按下
right_mouse_press = False  # 鼠标右键是否按下
middle_mouse_press = False  # 鼠标中键是否按下

smooth_modal_start = False
thinning_modal_start = False
thicking_modal_start = False


def last_set_modal_start_false():
    global thinning_modal_start
    thinning_modal_start = False
    global thicking_modal_start
    thicking_modal_start = False
    global smooth_modal_start
    smooth_modal_start = False



def frontToLastDamo():
    #隐藏支撑和排气孔模块的对比物
    name = bpy.context.scene.leftWindowObj
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (sprue_compare_obj != None):
        sprue_compare_obj.hide_set(True)
    if (hard_support_compare_obj != None):
        hard_support_compare_obj.hide_set(True)
    if (soft_support_compare_obj != None):
        soft_support_compare_obj.hide_set(True)

    # 根据保存的DamoCopy,复制一份用来替换当前激活物体
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        name = bpy.context.scene.leftWindowObj
        if (selected_obj.name == name + "LastDamoReset" or selected_obj.name == name + "LastDamoForShow"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    #复制一份用于重置的物体
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LastDamoReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    duplicate_obj2 = obj.copy()
    duplicate_obj2.data = obj.data.copy()
    duplicate_obj2.animation_data_clear()
    duplicate_obj2.name = name + "LastDamoForShow"
    bpy.context.collection.objects.link(duplicate_obj2)
    if (name == "右耳"):
        moveToRight(duplicate_obj2)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj2)
    duplicate_obj2.hide_set(True)


    #将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

    last_set_modal_start_false()




    # 添加监听
    global damo_mouse_listener
    if (damo_mouse_listener == None):
        damo_mouse_listener = mouse.Listener(
            on_click=on_click
        )
        # 启动监听器
        damo_mouse_listener.start()


def frontFromLastDamo():
    # 将隐藏支撑和排气孔模块的对比物重新显示
    name = bpy.context.scene.leftWindowObj
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (sprue_compare_obj != None):
        sprue_compare_obj.hide_set(False)
    if (hard_support_compare_obj != None):
        hard_support_compare_obj.hide_set(False)
    if (soft_support_compare_obj != None):
        soft_support_compare_obj.hide_set(False)

    last_set_modal_start_false()
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    # 切换到物体模式
    bpy.ops.object.mode_set(mode='OBJECT')
    #将后期打磨操作后的物体删除
    resetname = name + "LastDamoReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if (name == "右耳"):
        moveToRight(duplicate_obj)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj)
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name + "LastDamoReset" or selected_obj.name == name + "LastDamoForShow"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



    # 将添加的鼠标监听删除
    global damo_mouse_listener
    if (damo_mouse_listener != None):
        damo_mouse_listener.stop()
        damo_mouse_listener = None

    if bpy.context.mode == 'SCULPT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(state=True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def on_click(x, y, button, pressed):
    global left_mouse_press
    global right_mouse_press
    global middle_mouse_press
    # 鼠标点击事件处理函数
    if button == mouse.Button.left and pressed:
        left_mouse_press = True
    elif button == mouse.Button.left and not pressed:
        left_mouse_press = False

    if button == mouse.Button.right and pressed:
        right_mouse_press = True
    elif button == mouse.Button.right and not pressed:
        right_mouse_press = False

    if button == mouse.Button.middle and pressed:
        middle_mouse_press = True
    elif button == mouse.Button.middle and not pressed:
        middle_mouse_press = False


# 打磨功能模块左侧按钮的加厚操作
class LastThickening(bpy.types.Operator):
    bl_idname = "object.last_thickening"
    bl_label = "加厚操作"
    bl_description = "点击鼠标左键加厚模型，右键改变区域选取圆环的大小"
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __initial_radius = None

    __flag = False
    __is_changed = False


    def invoke(self, context, event):
        global smooth_modal_start
        smooth_modal_start = False
        global thinning_modal_start
        thinning_modal_start = False

        op_cls = LastThickening
        bpy.context.scene.var = 111
        print("thicking_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "ADD"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = bpy.context.active_object.name
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
        bpy.data.brushes["SculptDraw"].strength = strength
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
        # bpy.context.scene.tool_settings.sculpt.show_brush = False
        # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")

        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None  # 锁定圆环和模型的比例
        op_cls.__flag = False
        op_cls.__is_changed = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        change_mat_mould(1)
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        global thicking_modal_start
        if not thicking_modal_start:
            print("后期打磨打厚modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式
            thicking_modal_start = True

        global damo_mouse_listener
        if (damo_mouse_listener == None):
            damo_mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            damo_mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = LastThickening
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 111):
            if is_mouse_on_object(context, event):
                if op_cls.__is_changed == True:
                    op_cls.__is_changed = False
                if is_changed(context, event) and not left_mouse_press:
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(
                        name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "ADD"
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                if event.type == 'TIMER' and left_mouse_press and bpy.context.mode == 'SCULPT':
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                elif bpy.context.mode == 'OBJECT' and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.ops.wm.tool_set_by_id(
                        name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "ADD"
                    bpy.context.scene.tool_settings.sculpt.show_brush = True

                    # 重新上色
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                    if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_radius = bpy.context.scene.tool_settings.unified_paint_settings.size
                        # print('初始大小',op_cls.__initial_radius)
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE' and not left_mouse_press:
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # if event.type == 'Q':
                    # 获取鼠标光标的区域坐标
                    mv = mathutils.Vector(
                        (event.mouse_region_x, event.mouse_region_y))

                    # 单击功能区上的“窗口”区域中的
                    # 获取信息和“三维视口”空间中的空间信息
                    region, space = get_region_and_space(
                        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
                    )
                    # 确定朝向鼠标光标位置发出的光线的方向
                    ray_dir = view3d_utils.region_2d_to_vector_3d(
                        region,
                        space.region_3d,
                        mv
                    )
                    # 确定朝向鼠标光标位置发出的光线源
                    ray_orig = view3d_utils.region_2d_to_origin_3d(
                        region,
                        space.region_3d,
                        mv
                    )
                    # 光线起点
                    start = ray_orig
                    # 光线终点
                    end = ray_orig + ray_dir

                    # 确定光线和对象的相交
                    # 交叉判定在对象的局部坐标下进行
                    # 将光线的起点和终点转换为局部坐标
                    mwi = active_obj.matrix_world.inverted()
                    # 光线起点
                    mwi_start = mwi @ start
                    # 光线终点
                    mwi_end = mwi @ end
                    # 光线方向
                    mwi_dir = mwi_end - mwi_start

                    # 取消选择对象的面
                    # bpy.ops.mesh.select_all(action='DESELECT')

                    # 获取活动对象
                    # active_obj = bpy.context.active_object
                    # name = bpy.context.object.name
                    # copyname = name + ".001"
                    # innermw = ori_obj.matrix_world
                    # innermw_inv = innermw.inverted()
                    # 确保活动对象的类型是网格
                    if active_obj.type == 'MESH':
                        # 确保活动对象可编辑
                        if active_obj.mode == 'SCULPT':
                            # bm.transform(active_obj.matrix_world)
                            # 构建BVH树
                            outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                            # innertree = mathutils.bvhtree.BVHTree.FromBMesh(oribm)
                            # 进行对象和光线交叉判定
                            co, _, fidx, dis = outertree.ray_cast(
                                mwi_start, mwi_dir)
                            # 网格和光线碰撞时
                            if fidx is not None:
                                min = 666
                                index = 0
                                bm.faces.ensure_lookup_table()
                                oribm.faces.ensure_lookup_table()
                                for v in bm.faces[fidx].verts:
                                    vec = v.co - co
                                    between = vec.dot(vec)
                                    if (between <= min):
                                        min = between
                                        index = v.index
                                bm.verts.ensure_lookup_table()
                                oribm.verts.ensure_lookup_table()
                                disvec = oribm.verts[index].co - \
                                         bm.verts[index].co
                                dis = disvec.dot(disvec)
                                final_dis = round(math.sqrt(dis), 2)
                                # 判断当前顶点与原顶点的位置关系
                                # origin = innermw_inv @ cl
                                # dest = innermw_inv @ co
                                # direc = dest - origin
                                # maxdis = math.sqrt(direc.dot(direc))
                                # _, _, fidx2, _ = innertree.ray_cast(
                                #     origin, direc, maxdis)
                                origin_vec = oribm.verts[index].normal
                                flag = origin_vec.dot(disvec)
                                if flag > 0:
                                    final_dis *= -1
                                MyHandleClass.remove_handler()
                                MyHandleClass.add_handler(
                                    draw_callback_px, (None, final_dis))
                                # print(final_dis)

                    if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y)))
                        # 上移扩大，下移缩小
                        op = 1
                        if (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            op = -1
                        # 设置圆环大小范围【50，200】
                        radius = max(op_cls.__initial_radius + dis * op, 50)
                        if radius > 200:
                            radius = 200
                        bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                        bpy.data.brushes["SculptDraw"].strength = 25 / radius
                        # 保存改变的圆环大小
                        name = bpy.context.scene.leftWindowObj
                        if name == '右耳':
                            context.scene.damo_circleRadius_R = radius
                            context.scene.damo_strength_R = 25 / radius
                        else:
                            context.scene.damo_circleRadius_L = radius
                            context.scene.damo_strength_L = 25 / radius

            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event):
                    if left_mouse_press:
                        op_cls.__flag = True

                    else:
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        name = bpy.context.scene.leftWindowObj
                        active_obj = bpy.data.objects.get(name)
                        # 获取网格数据
                        me = active_obj.data
                        # 创建bmesh对象
                        bm = bmesh.new()
                        # 将网格数据复制到bmesh对象
                        bm.from_mesh(me)
                        color_lay = bm.verts.layers.float_color["Color"]
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            colvert.x = 1
                            colvert.y = 0.319
                            colvert.z = 0.133

                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

                if not left_mouse_press and op_cls.__flag:
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
                    op_cls.__flag = False
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        colvert.x = 1
                        colvert.y = 0.319
                        colvert.z = 0.133

                    MyHandleClass.remove_handler()
                    context.area.tag_redraw()

                    bm.to_mesh(me)
                    bm.free()

                if (bpy.context.mode == 'SCULPT' and (left_mouse_press or right_mouse_press or middle_mouse_press)
                        and op_cls.__flag == False and event.mouse_x > 60):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式

                # 圆环移到物体外，不再改变大小
                if event.value == 'RELEASE' and op_cls.__right_mouse_down:
                    op_cls.__right_mouse_down = False

            return {'PASS_THROUGH'}

        elif bpy.context.scene.var != 111:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[context.scene.leftWindowObj].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}

        # 鼠标在区域外
        else:
            if not left_mouse_press and not op_cls.__is_changed:
                if MyHandleClass._handler:
                    MyHandleClass.remove_handler()
                active_obj = context.active_object
                # 获取网格数据
                me = active_obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 1
                    colvert.y = 0.319
                    colvert.z = 0.133
                bm.to_mesh(me)
                bm.free()
                op_cls.__is_changed = True
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


# 打磨功能模块左侧按钮的减薄操作
class LastThinning(bpy.types.Operator):
    bl_idname = "object.last_thinning"
    bl_label = "减薄操作"
    bl_description = "点击鼠标左键减薄模型，右键改变区域选取圆环的大小"
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __initial_radius = None

    __flag = False
    __is_changed = False

    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        global smooth_modal_start
        smooth_modal_start = False
        global thicking_modal_start
        thicking_modal_start = False

        op_cls = LastThinning
        bpy.context.scene.var = 112
        print("后期打磨打薄thinning_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = bpy.context.active_object.name
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
        bpy.data.brushes["SculptDraw"].strength = strength

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
        # bpy.context.scene.tool_settings.sculpt.show_brush = False
        # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None  # 锁定圆环和模型的比例
        op_cls.__flag = False
        op_cls.__is_changed = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        change_mat_mould(1)
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        global thinning_modal_start
        if not thinning_modal_start:
            print("打薄modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式
            thinning_modal_start = True

        global damo_mouse_listener
        if (damo_mouse_listener == None):
            damo_mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            damo_mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = LastThinning
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 112):
            if is_mouse_on_object(context, event):
                if op_cls.__is_changed == True:
                    op_cls.__is_changed = False
                if is_changed(context, event) and not left_mouse_press:
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1
                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                if event.type == 'TIMER' and left_mouse_press and bpy.context.mode == 'SCULPT':
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                elif bpy.context.mode == 'OBJECT' and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.ops.wm.tool_set_by_id(
                        name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
                    bpy.context.scene.tool_settings.sculpt.show_brush = True

                    # 重新上色
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                    if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_radius = bpy.context.scene.tool_settings.unified_paint_settings.size

                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE' and not left_mouse_press:
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # if event.type == 'Q':
                    # 获取鼠标光标的区域坐标
                    mv = mathutils.Vector(
                        (event.mouse_region_x, event.mouse_region_y))

                    # 单击功能区上的“窗口”区域中的
                    # 获取信息和“三维视口”空间中的空间信息
                    region, space = get_region_and_space(
                        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
                    )
                    # 确定朝向鼠标光标位置发出的光线的方向
                    ray_dir = view3d_utils.region_2d_to_vector_3d(
                        region,
                        space.region_3d,
                        mv
                    )
                    # 确定朝向鼠标光标位置发出的光线源
                    ray_orig = view3d_utils.region_2d_to_origin_3d(
                        region,
                        space.region_3d,
                        mv
                    )
                    # 光线起点
                    start = ray_orig
                    # 光线终点
                    end = ray_orig + ray_dir

                    # 确定光线和对象的相交
                    # 交叉判定在对象的局部坐标下进行
                    # 将光线的起点和终点转换为局部坐标
                    mwi = active_obj.matrix_world.inverted()
                    # 光线起点
                    mwi_start = mwi @ start
                    # 光线终点
                    mwi_end = mwi @ end
                    # 光线方向
                    mwi_dir = mwi_end - mwi_start

                    # 取消选择对象的面
                    # bpy.ops.mesh.select_all(action='DESELECT')

                    # 获取活动对象
                    # active_obj = bpy.context.active_object
                    # name = bpy.context.object.name
                    # copyname = name + ".001"
                    # innermw = ori_obj.matrix_world
                    # innermw_inv = innermw.inverted()
                    # 确保活动对象的类型是网格
                    if active_obj.type == 'MESH':
                        # 确保活动对象可编辑
                        if active_obj.mode == 'SCULPT':
                            # bm.transform(active_obj.matrix_world)
                            # 构建BVH树
                            outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                            # innertree = mathutils.bvhtree.BVHTree.FromBMesh(oribm)
                            # 进行对象和光线交叉判定
                            co, _, fidx, dis = outertree.ray_cast(
                                mwi_start, mwi_dir)
                            # 网格和光线碰撞时
                            if fidx is not None:
                                min = 666
                                index = 0
                                bm.faces.ensure_lookup_table()
                                oribm.faces.ensure_lookup_table()
                                for v in bm.faces[fidx].verts:
                                    vec = v.co - co
                                    between = vec.dot(vec)
                                    if (between <= min):
                                        min = between
                                        index = v.index
                                bm.verts.ensure_lookup_table()
                                oribm.verts.ensure_lookup_table()
                                disvec = oribm.verts[index].co - \
                                         bm.verts[index].co
                                dis = disvec.dot(disvec)
                                final_dis = round(math.sqrt(dis), 2)
                                # 判断当前顶点与原顶点的位置关系
                                # origin = innermw_inv @ cl
                                # dest = innermw_inv @ co
                                # direc = dest - origin
                                # maxdis = math.sqrt(direc.dot(direc))
                                # _, _, fidx2, _ = innertree.ray_cast(
                                #     origin, direc, maxdis)
                                origin_vec = oribm.verts[index].normal
                                flag = origin_vec.dot(disvec)
                                if flag > 0:
                                    final_dis *= -1
                                MyHandleClass.remove_handler()
                                MyHandleClass.add_handler(
                                    draw_callback_px, (None, final_dis))
                                # print(final_dis)

                    if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y)))
                        # 上移扩大，下移缩小
                        op = 1
                        if (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            op = -1
                        # 设置圆环大小范围【50，200】
                        radius = max(op_cls.__initial_radius + dis * op, 50)
                        if radius > 200:
                            radius = 200
                        bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                        bpy.data.brushes["SculptDraw"].strength = 25 / radius
                        # 保存改变的圆环大小
                        name = bpy.context.scene.leftWindowObj
                        if name == '右耳':
                            context.scene.damo_circleRadius_R = radius
                            context.scene.damo_strength_R = 25 / radius
                        else:
                            context.scene.damo_circleRadius_L = radius
                            context.scene.damo_strength_L = 25 / radius

            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event):
                    if left_mouse_press:
                        op_cls.__flag = True

                    else:
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        name = bpy.context.scene.leftWindowObj
                        active_obj = bpy.data.objects.get(name)
                        # 获取网格数据
                        me = active_obj.data
                        # 创建bmesh对象
                        bm = bmesh.new()
                        # 将网格数据复制到bmesh对象
                        bm.from_mesh(me)
                        color_lay = bm.verts.layers.float_color["Color"]
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            colvert.x = 1
                            colvert.y = 0.319
                            colvert.z = 0.133

                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

                if not left_mouse_press and op_cls.__flag:
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
                    op_cls.__flag = False
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        colvert.x = 1
                        colvert.y = 0.319
                        colvert.z = 0.133

                    MyHandleClass.remove_handler()
                    context.area.tag_redraw()

                    bm.to_mesh(me)
                    bm.free()

                if (bpy.context.mode == 'SCULPT' and (left_mouse_press or right_mouse_press or middle_mouse_press)
                        and op_cls.__flag == False and event.mouse_x > 60):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式

                # 圆环移到物体外，不再改变大小
                if event.value == 'RELEASE' and op_cls.__right_mouse_down:
                    op_cls.__right_mouse_down = False

            return {'PASS_THROUGH'}
        elif bpy.context.scene.var != 112:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[context.scene.leftWindowObj].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}

        # 鼠标在区域外
        else:
            if not left_mouse_press and not op_cls.__is_changed:
                if MyHandleClass._handler:
                    MyHandleClass.remove_handler()
                active_obj = context.active_object
                # 获取网格数据
                me = active_obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 1
                    colvert.y = 0.319
                    colvert.z = 0.133
                bm.to_mesh(me)
                bm.free()
                op_cls.__is_changed = True
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


# 打磨功能模块左侧按钮的光滑操作
class LastSmooth(bpy.types.Operator):
    bl_idname = "object.last_smooth"
    bl_label = "光滑操作"
    bl_description = "点击鼠标左键光滑模型，右键改变区域选取圆环的大小"
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __initial_radius = None

    __flag = False
    __is_changed = False

    # @classmethod
    # def poll(context):
    #     if(context.space_data.context == 'RENDER'):
    #         return True
    #     else:
    #         return False

    def invoke(self, context, event):
        global thinning_modal_start
        thinning_modal_start = False
        global thicking_modal_start
        thicking_modal_start = False

        op_cls = LastSmooth
        bpy.context.scene.var = 113
        print("后期打磨平滑smooth_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
        bpy.data.brushes["Smooth"].direction = 'SMOOTH'
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500

        # 设置圆环初始大小
        name = bpy.context.active_object.name
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
        bpy.data.brushes["Smooth"].strength = strength

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
        # bpy.context.scene.tool_settings.sculpt.show_brush = False
        # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None  # 锁定圆环和模型的比例
        op_cls.__flag = False
        op_cls.__is_changed = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        change_mat_mould(1)
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)
        global smooth_modal_start
        if not smooth_modal_start:
            print("平滑modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式
            smooth_modal_start = True

        global damo_mouse_listener
        if (damo_mouse_listener == None):
            damo_mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            damo_mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = LastSmooth
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 113):
            if is_mouse_on_object(context, event):
                if op_cls.__is_changed == True:
                    op_cls.__is_changed = False
                if is_changed(context, event) and not left_mouse_press:
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
                    bpy.data.brushes["Smooth"].direction = 'SMOOTH'

                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)
                    bm.to_mesh(me)
                    bm.free()

                if event.type == 'TIMER' and left_mouse_press and bpy.context.mode == 'SCULPT':
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1
                        name = bpy.context.scene.leftWindowObj

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                elif bpy.context.mode == 'OBJECT' and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
                    bpy.data.brushes["Smooth"].direction = 'SMOOTH'
                    bpy.context.scene.tool_settings.sculpt.show_brush = True

                    # 重新上色
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # 遍历顶点，根据厚度设置颜色
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        index_color = vert.index
                        disvec_color = oribm.verts[index_color].co - bm.verts[index_color].co
                        dis_color = disvec_color.dot(disvec_color)
                        thinkness = round(math.sqrt(dis_color), 2)
                        origin_veccol = oribm.verts[index_color].normal
                        flag_color = origin_veccol.dot(disvec_color)
                        if flag_color > 0:
                            thinkness *= -1

                        color = round(thinkness / 0.8, 2)
                        if color >= 1:
                            color = 1
                        if color <= -1:
                            color = -1
                        if thinkness >= 0:
                            colvert.x = color
                            colvert.y = 1 - color
                            colvert.z = 0
                        else:
                            colvert.x = 0
                            colvert.y = 1 + color
                            colvert.z = color * (-1)

                    bm.to_mesh(me)
                    bm.free()

                if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                    if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_radius = bpy.context.scene.tool_settings.unified_paint_settings.size
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE' and not left_mouse_press:
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
                    orime = ori_obj.data
                    oribm = bmesh.new()
                    oribm.from_mesh(orime)
                    # if event.type == 'Q':
                    # 获取鼠标光标的区域坐标
                    mv = mathutils.Vector(
                        (event.mouse_region_x, event.mouse_region_y))

                    # 单击功能区上的“窗口”区域中的
                    # 获取信息和“三维视口”空间中的空间信息
                    region, space = get_region_and_space(
                        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
                    )
                    # 确定朝向鼠标光标位置发出的光线的方向
                    ray_dir = view3d_utils.region_2d_to_vector_3d(
                        region,
                        space.region_3d,
                        mv
                    )
                    # 确定朝向鼠标光标位置发出的光线源
                    ray_orig = view3d_utils.region_2d_to_origin_3d(
                        region,
                        space.region_3d,
                        mv
                    )
                    # 光线起点
                    start = ray_orig
                    # 光线终点
                    end = ray_orig + ray_dir

                    # 确定光线和对象的相交
                    # 交叉判定在对象的局部坐标下进行
                    # 将光线的起点和终点转换为局部坐标
                    mwi = active_obj.matrix_world.inverted()
                    # 光线起点
                    mwi_start = mwi @ start
                    # 光线终点
                    mwi_end = mwi @ end
                    # 光线方向
                    mwi_dir = mwi_end - mwi_start

                    # 取消选择对象的面
                    # bpy.ops.mesh.select_all(action='DESELECT')

                    # 获取活动对象
                    # active_obj = bpy.context.active_object
                    # name = bpy.context.object.name
                    # copyname = name + ".001"
                    # innermw = ori_obj.matrix_world
                    # innermw_inv = innermw.inverted()
                    # 确保活动对象的类型是网格
                    if active_obj.type == 'MESH':
                        # 确保活动对象可编辑
                        if active_obj.mode == 'SCULPT':
                            # bm.transform(active_obj.matrix_world)
                            # 构建BVH树
                            outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                            # innertree = mathutils.bvhtree.BVHTree.FromBMesh(oribm)
                            # 进行对象和光线交叉判定
                            co, _, fidx, dis = outertree.ray_cast(
                                mwi_start, mwi_dir)
                            # 网格和光线碰撞时
                            if fidx is not None:
                                min = 666
                                index = 0
                                bm.faces.ensure_lookup_table()
                                oribm.faces.ensure_lookup_table()
                                for v in bm.faces[fidx].verts:
                                    vec = v.co - co
                                    between = vec.dot(vec)
                                    if (between <= min):
                                        min = between
                                        index = v.index
                                bm.verts.ensure_lookup_table()
                                oribm.verts.ensure_lookup_table()
                                disvec = oribm.verts[index].co - \
                                         bm.verts[index].co
                                dis = disvec.dot(disvec)
                                final_dis = round(math.sqrt(dis), 2)
                                # 判断当前顶点与原顶点的位置关系
                                # origin = innermw_inv @ cl
                                # dest = innermw_inv @ co
                                # direc = dest - origin
                                # maxdis = math.sqrt(direc.dot(direc))
                                # _, _, fidx2, _ = innertree.ray_cast(
                                #     origin, direc, maxdis)
                                origin_vec = oribm.verts[index].normal
                                flag = origin_vec.dot(disvec)
                                if flag > 0:
                                    final_dis *= -1
                                MyHandleClass.remove_handler()
                                MyHandleClass.add_handler(
                                    draw_callback_px, (None, final_dis))
                                # print(final_dis)

                    if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y)))
                        # 上移扩大，下移缩小
                        op = 1
                        if (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            op = -1
                        # 设置圆环大小范围【50，200】
                        radius = max(op_cls.__initial_radius + dis * op, 50)
                        if radius > 200:
                            radius = 200
                        bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                        bpy.data.brushes["Smooth"].strength = 25 / radius * 1.5
                        # 保存改变的圆环大小
                        name = bpy.context.scene.leftWindowObj
                        if name == '右耳':
                            context.scene.damo_circleRadius_R = radius
                            context.scene.damo_strength_R = 25 / radius
                        else:
                            context.scene.damo_circleRadius_L = radius
                            context.scene.damo_strength_L = 25 / radius

            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event):
                    if left_mouse_press:
                        op_cls.__flag = True

                    else:
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        name = bpy.context.scene.leftWindowObj
                        active_obj = bpy.data.objects.get(name)
                        # 获取网格数据
                        me = active_obj.data
                        # 创建bmesh对象
                        bm = bmesh.new()
                        # 将网格数据复制到bmesh对象
                        bm.from_mesh(me)
                        color_lay = bm.verts.layers.float_color["Color"]
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            colvert.x = 1
                            colvert.y = 0.319
                            colvert.z = 0.133

                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

                if not left_mouse_press and op_cls.__flag:
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
                    op_cls.__flag = False
                    name = bpy.context.scene.leftWindowObj
                    active_obj = bpy.data.objects.get(name)
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    color_lay = bm.verts.layers.float_color["Color"]
                    for vert in bm.verts:
                        colvert = vert[color_lay]
                        colvert.x = 1
                        colvert.y = 0.319
                        colvert.z = 0.133

                    MyHandleClass.remove_handler()
                    context.area.tag_redraw()

                    bm.to_mesh(me)
                    bm.free()

                if (bpy.context.mode == 'SCULPT' and (left_mouse_press or right_mouse_press or middle_mouse_press)
                        and op_cls.__flag == False and event.mouse_x > 60):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式

                # 圆环移到物体外，不再改变大小
                if event.value == 'RELEASE' and op_cls.__right_mouse_down:
                    op_cls.__right_mouse_down = False

            return {'PASS_THROUGH'}
        elif bpy.context.scene.var != 113:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[context.scene.leftWindowObj].select_set(True)
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}

        # 鼠标在区域外
        else:
            if not left_mouse_press and not op_cls.__is_changed:
                if MyHandleClass._handler:
                    MyHandleClass.remove_handler()
                active_obj = context.active_object
                # 获取网格数据
                me = active_obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 1
                    colvert.y = 0.319
                    colvert.z = 0.133
                bm.to_mesh(me)
                bm.free()
                op_cls.__is_changed = True
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


class LastDamo_Reset(bpy.types.Operator):
    bl_idname = "object.last_damo_reset"
    bl_label = "重置操作"
    bl_description = "点击按钮恢复到原来的模型"

    def invoke(self, context, event):
        print("reset invoke")
        last_set_modal_start_false()
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context, event):
        bpy.context.scene.var = 4
        active_obj = bpy.context.active_object
        name = bpy.context.object.name
        reset_name = name + "LastDamoReset"
        if bpy.data.objects.get(reset_name):
            ori_obj = bpy.data.objects[reset_name]
            bpy.data.objects.remove(active_obj, do_unlink=True)
            ori_obj.name = name
            ori_obj.hide_set(False)
        bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
            if i.name == name:
                bpy.context.view_layer.objects.active = i
                i.select_set(state=True)


class MyToolLastDamo(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thickening"
    bl_label = "后期加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.armature.extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("object.last_thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thickening2"
    bl_label = "后期加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.armature.extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("object.last_thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thinning"
    bl_label = "后期磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.sequencer.blade"
    bl_widget = None
    bl_keymap = (
        ("object.last_thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo4(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thinning2"
    bl_label = "后期磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.sequencer.blade"
    bl_widget = None
    bl_keymap = (
        ("object.last_thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo5(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_smooth"
    bl_label = "后期圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "ops.sequencer.retime"
    bl_widget = None
    bl_keymap = (
        ("object.last_smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo6(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_smooth2"
    bl_label = "后期圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "ops.sequencer.retime"
    bl_widget = None
    bl_keymap = (
        ("object.last_smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo7(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_damo_reset"
    bl_label = "后期重置"
    bl_description = (
        "点击进行重置操作"
    )
    bl_icon = "brush.particle.puff"
    bl_widget = None
    bl_keymap = (
        ("object.last_damo_reset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo8(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_damo_reset2"
    bl_label = "后期重置"
    bl_description = (
        "点击进行重置操作"
    )
    bl_icon = "brush.particle.puff"
    bl_widget = None
    bl_keymap = (
        ("object.last_damo_reset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    LastThickening,
    LastThinning,
    LastSmooth,
    LastDamo_Reset
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyToolLastDamo, separator=True, group=False)
    bpy.utils.register_tool(MyToolLastDamo3, separator=True,
                            group=False, after={MyToolLastDamo.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo5, separator=True,
                            group=False, after={MyToolLastDamo3.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo7, separator=True,
                            group=False, after={MyToolLastDamo5.bl_idname})

    bpy.utils.register_tool(MyToolLastDamo2, separator=True, group=False)
    bpy.utils.register_tool(MyToolLastDamo4, separator=True,
                            group=False, after={MyToolLastDamo2.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo6, separator=True,
                            group=False, after={MyToolLastDamo4.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo8, separator=True,
                            group=False, after={MyToolLastDamo6.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyToolLastDamo)
    bpy.utils.unregister_tool(MyToolLastDamo3)
    bpy.utils.unregister_tool(MyToolLastDamo5)
    bpy.utils.unregister_tool(MyToolLastDamo7)

    bpy.utils.unregister_tool(MyToolLastDamo2)
    bpy.utils.unregister_tool(MyToolLastDamo4)
    bpy.utils.unregister_tool(MyToolLastDamo6)
    bpy.utils.unregister_tool(MyToolLastDamo8)
