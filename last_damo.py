import bpy
from bpy.types import WorkSpaceTool
from .tool import *
from math import *
import mathutils
import bmesh
import bpy_extras
import time
from bpy_extras import view3d_utils
import math
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running, \
    get_process_var_list

prev_on_object = False  # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体上)


thickening_modal_start = False
thinning_modal_start = False
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

    # 删除可能存在的LastDamoReset和LastDamoForShow
    lastdamo_reset_obj = bpy.data.objects.get(name + "LastDamoReset")
    lastdamo_show_obj = bpy.data.objects.get(name + "LastDamoForShow")
    if(lastdamo_reset_obj != None):
        bpy.data.objects.remove(lastdamo_reset_obj, do_unlink=True)
    if (lastdamo_show_obj != None):
        bpy.data.objects.remove(lastdamo_show_obj, do_unlink=True)
    #根据当前操作的左右耳模型复制两份物体作为重置和厚度显示的物体
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
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

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    bpy.ops.object.mode_set(mode='OBJECT')
    #使用LastDamoReset将操作物体还原
    resetname = name + "LastDamoReset"
    ori_obj = bpy.data.objects.get(resetname)
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

    # 删除可能存在的LastDamoReset和LastDamoForShow
    lastdamo_reset_obj = bpy.data.objects.get(name + "LastDamoReset")
    lastdamo_show_obj = bpy.data.objects.get(name + "LastDamoForShow")
    if (lastdamo_reset_obj != None):
        bpy.data.objects.remove(lastdamo_reset_obj, do_unlink=True)
    if (lastdamo_show_obj != None):
        bpy.data.objects.remove(lastdamo_show_obj, do_unlink=True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

    bpy.ops.object.mode_set(mode='OBJECT')

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(state=True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def color_vertex_by_thickness():
    active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    # 原始数据
    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
    ori_me = ori_obj.data
    ori_bm = bmesh.new()
    ori_bm.from_mesh(ori_me)
    # 遍历顶点，根据厚度设置颜色
    color_lay = bm.verts.layers.float_color["Color"]
    bm.verts.ensure_lookup_table()
    ori_bm.verts.ensure_lookup_table()
    for vert in bm.verts:
        colvert = vert[color_lay]
        index = vert.index
        distance_vector = ori_bm.verts[index].co - bm.verts[index].co
        thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
        origin_vertex_normal = ori_bm.verts[index].normal
        flag = origin_vertex_normal.dot(distance_vector)   # 判断当前顶点是否在原模型的内部
        if flag > 0:
            thickness *= -1

        color = round(thickness / 0.8, 2)
        if color >= 1:
            color = 1
        if color <= -1:
            color = -1
        if thickness >= 0:
            colvert.x = color
            colvert.y = 1 - color
            colvert.z = 0
        else:
            colvert.x = 0
            colvert.y = 1 + color
            colvert.z = color * (-1)

    bm.to_mesh(me)
    bm.free()


def cal_thickness(context, event):
    active_obj = bpy.data.objects[context.scene.leftWindowObj]
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    # 原始数据
    ori_obj = bpy.data.objects[active_obj.name + "LastDamoForShow"]
    ori_me = ori_obj.data
    ori_bm = bmesh.new()
    ori_bm.from_mesh(ori_me)
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

    # 确保活动对象的类型是网格
    if active_obj.type == 'MESH':
        # 确保活动对象可编辑
        if active_obj.mode == 'SCULPT':
            # 构建BVH树
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
            # 进行对象和光线交叉判定
            co, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir)
            # 网格和光线碰撞时
            if fidx is not None:
                min = float('inf')
                index = -1
                bm.faces.ensure_lookup_table()
                ori_bm.faces.ensure_lookup_table()
                for v in bm.faces[fidx].verts:
                    vec = v.co - co
                    between = vec.dot(vec)
                    if between <= min:
                        min = between
                        index = v.index
                bm.verts.ensure_lookup_table()
                ori_bm.verts.ensure_lookup_table()
                distance_vector = ori_bm.verts[index].co - bm.verts[index].co
                thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
                origin_vertex_normal = ori_bm.verts[index].normal
                flag = origin_vertex_normal.dot(distance_vector)  # 判断当前顶点是否在原模型的内部
                if flag > 0:
                    thickness *= -1
                MyHandleClass.remove_handler()
                MyHandleClass.add_handler(
                    draw_callback_px, (None, thickness))


def recolor_vertex():
    active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    color_lay = bm.verts.layers.float_color["Color"]
    for vert in bm.verts:
        colvert = vert[color_lay]
        colvert.x = 0
        colvert.y = 0.25
        colvert.z = 1

    bm.to_mesh(me)
    bm.free()


# 打磨功能模块左侧按钮的加厚操作
class LastThickening(bpy.types.Operator):
    bl_idname = "object.last_thickening"
    bl_label = "加厚操作"
    bl_description = "点击鼠标左键加厚模型，右键改变区域选取圆环的大小"

    __left_mouse_down = False
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __initial_radius = None

    __brush_mode = False
    __select_mode = True

    def invoke(self, context, event):
        op_cls = LastThickening
        # print("thicking_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "ADD"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = bpy.context.scene.leftWindowObj
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

        op_cls.__left_mouse_down = False  # 初始化鼠标左键行为操作
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None  # 锁定圆环和模型的比例
        op_cls.__flag = False
        op_cls.__is_changed = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        bpy.context.scene.var = 111
        global thickening_modal_start
        if not thickening_modal_start:
            thickening_modal_start = True
            print("后期打磨打厚modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = LastThickening
        global thickening_modal_start

        override1 = getOverride()
        area = override1['area']
        
        if context.area:
            context.area.tag_redraw()

        if bpy.context.screen.areas[0].spaces.active.context == 'TEXTURE':
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 111):
                if is_mouse_on_object(context, event):
                    if event.type == 'TIMER':
                        if op_cls.__left_mouse_down and bpy.context.mode == 'SCULPT':
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                            color_vertex_by_thickness()

                    elif event.type == 'LEFTMOUSE':  # 监听左键
                        if event.value == 'PRESS':  # 按下
                            op_cls.__left_mouse_down = True
                        return {'PASS_THROUGH'}

                    elif event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                        if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            op_cls.__right_mouse_down = True
                            op_cls.__initial_radius = bpy.context.scene.tool_settings.unified_paint_settings.size
                        elif event.value == 'RELEASE':
                            op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                        return {'RUNNING_MODAL'}

                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if op_cls.__select_mode:
                                op_cls.__brush_mode = True
                                op_cls.__select_mode = False
                                bpy.ops.object.mode_set(mode='SCULPT')
                                bpy.context.scene.tool_settings.sculpt.show_brush = True
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
                                bpy.data.brushes["SculptDraw"].direction = "ADD"
                                color_vertex_by_thickness()

                        else:
                            if op_cls.__select_mode:
                                op_cls.__brush_mode = True
                                op_cls.__select_mode = False
                                bpy.ops.object.mode_set(mode='SCULPT')
                                bpy.context.scene.tool_settings.sculpt.show_brush = True
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
                                bpy.data.brushes["SculptDraw"].direction = "ADD"
                                color_vertex_by_thickness()

                        if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                            op_cls.__now_mouse_y = event.mouse_region_y
                            op_cls.__now_mouse_x = event.mouse_region_x
                            dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                                op_cls.__now_mouse_y - op_cls.__initial_mouse_y)))
                            # 上移扩大，下移缩小
                            op = 1
                            if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                                op = -1
                            # 设置圆环大小范围【50，200】
                            radius = max(op_cls.__initial_radius + dis * op, 50)
                            if radius > 200:
                                radius = 200
                            bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                            if context.scene.leftWindowObj == '右耳':
                                bpy.data.brushes[
                                    "SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_R
                            else:
                                bpy.data.brushes[
                                    "SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_L
                            # 保存改变的圆环大小
                            name = bpy.context.scene.leftWindowObj
                            if name == '右耳':
                                context.scene.damo_circleRadius_R = radius
                                context.scene.damo_strength_R = 25 / radius
                            else:
                                context.scene.damo_circleRadius_L = radius
                                context.scene.damo_strength_L = 25 / radius

                        if not op_cls.__left_mouse_down and not op_cls.__right_mouse_down:
                            cal_thickness(context, event)

                    return {'PASS_THROUGH'}

                else:
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                op_cls.__left_mouse_down = True
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        elif event.value == 'RELEASE':  # 圆环移到物体外，不再改变大小
                            if op_cls.__right_mouse_down:
                                op_cls.__right_mouse_down = False
                        return {'PASS_THROUGH'}
                    elif event.type == 'MIDDLEMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False

                        if not op_cls.__select_mode:
                            op_cls.__select_mode = True
                            bpy.context.scene.tool_settings.sculpt.show_brush = False
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                            recolor_vertex()
                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 111 and bpy.context.scene.var in get_process_var_list("后期打磨"):
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                print("后期打磨打厚modal结束")
                thickening_modal_start = False
                return {'FINISHED'}

            # 鼠标在区域外
            else:
                if event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    if op_cls.__brush_mode:
                        op_cls.__brush_mode = False
                        op_cls.__select_mode = True
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        recolor_vertex()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                print("后期打磨打厚modal结束")
                set_switch_time(None)
                thickening_modal_start = False
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


# 打磨功能模块左侧按钮的减薄操作
class LastThinning(bpy.types.Operator):
    bl_idname = "object.last_thinning"
    bl_label = "减薄操作"
    bl_description = "点击鼠标左键减薄模型，右键改变区域选取圆环的大小"

    __left_mouse_down = False
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __initial_radius = None

    __brush_mode = False
    __select_mode = True

    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        op_cls = LastThinning
        # print("后期打磨打薄thinning_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = bpy.context.scene.leftWindowObj
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

        op_cls.__left_mouse_down = False  # 初始化鼠标左键行为操作
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None  # 锁定圆环和模型的比例
        op_cls.__flag = False
        op_cls.__is_changed = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        bpy.context.scene.var = 112
        global thinning_modal_start
        if not thinning_modal_start:
            thinning_modal_start = True
            print("后期打磨打薄modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = LastThinning
        global thinning_modal_start

        override1 = getOverride()
        area = override1['area']

        if context.area:
            context.area.tag_redraw()

        if bpy.context.screen.areas[0].spaces.active.context == 'TEXTURE':
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 112):
                if is_mouse_on_object(context, event):
                    if event.type == 'TIMER':
                        if op_cls.__left_mouse_down and bpy.context.mode == 'SCULPT':
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                            color_vertex_by_thickness()

                    elif event.type == 'LEFTMOUSE':  # 监听左键
                        if event.value == 'PRESS':  # 按下
                            op_cls.__left_mouse_down = True
                        return {'PASS_THROUGH'}

                    elif event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                        if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            op_cls.__right_mouse_down = True
                            op_cls.__initial_radius = bpy.context.scene.tool_settings.unified_paint_settings.size
                        elif event.value == 'RELEASE':
                            op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                        return {'RUNNING_MODAL'}

                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if op_cls.__select_mode:
                                op_cls.__brush_mode = True
                                op_cls.__select_mode = False
                                bpy.ops.object.mode_set(mode='SCULPT')
                                bpy.context.scene.tool_settings.sculpt.show_brush = True
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
                                bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
                                color_vertex_by_thickness()

                        else:
                            if op_cls.__select_mode:
                                op_cls.__brush_mode = True
                                op_cls.__select_mode = False
                                bpy.ops.object.mode_set(mode='SCULPT')
                                bpy.context.scene.tool_settings.sculpt.show_brush = True
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
                                bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
                                color_vertex_by_thickness()

                        if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                            op_cls.__now_mouse_y = event.mouse_region_y
                            op_cls.__now_mouse_x = event.mouse_region_x
                            dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                                op_cls.__now_mouse_y - op_cls.__initial_mouse_y)))
                            # 上移扩大，下移缩小
                            op = 1
                            if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                                op = -1
                            # 设置圆环大小范围【50，200】
                            radius = max(op_cls.__initial_radius + dis * op, 50)
                            if radius > 200:
                                radius = 200
                            bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                            if context.scene.leftWindowObj == '右耳':
                                bpy.data.brushes[
                                    "SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_R
                            else:
                                bpy.data.brushes[
                                    "SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_L
                            # 保存改变的圆环大小
                            name = bpy.context.scene.leftWindowObj
                            if name == '右耳':
                                context.scene.damo_circleRadius_R = radius
                                context.scene.damo_strength_R = 25 / radius
                            else:
                                context.scene.damo_circleRadius_L = radius
                                context.scene.damo_strength_L = 25 / radius

                        if not op_cls.__left_mouse_down and not op_cls.__right_mouse_down:
                            cal_thickness(context, event)

                        return {'PASS_THROUGH'}

                else:
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                op_cls.__left_mouse_down = True
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        elif event.value == 'RELEASE':  # 圆环移到物体外，不再改变大小
                            if op_cls.__right_mouse_down:
                                op_cls.__right_mouse_down = False
                        return {'PASS_THROUGH'}
                    elif event.type == 'MIDDLEMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False

                        if not op_cls.__select_mode:
                            op_cls.__select_mode = True
                            bpy.context.scene.tool_settings.sculpt.show_brush = False
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                            recolor_vertex()
                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 112 and bpy.context.scene.var in get_process_var_list("后期打磨"):
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                print("后期打磨打薄modal结束")
                thinning_modal_start = False
                return {'FINISHED'}

            # 鼠标在区域外
            else:
                if event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    if op_cls.__brush_mode:
                        op_cls.__brush_mode = False
                        op_cls.__select_mode = True
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        recolor_vertex()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                print("后期打磨打薄modal结束")
                thinning_modal_start = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


# 打磨功能模块左侧按钮的光滑操作
class LastSmooth(bpy.types.Operator):
    bl_idname = "object.last_smooth"
    bl_label = "光滑操作"
    bl_description = "点击鼠标左键光滑模型，右键改变区域选取圆环的大小"

    __left_mouse_down = False
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __initial_radius = None

    __brush_mode = False
    __select_mode = True

    # @classmethod
    # def poll(context):
    #     if(context.space_data.context == 'RENDER'):
    #         return True
    #     else:
    #         return False

    def invoke(self, context, event):
        op_cls = LastSmooth
        # print("后期打磨平滑smooth_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
        bpy.data.brushes["Smooth"].direction = 'SMOOTH'
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500

        # 设置圆环初始大小
        name = bpy.context.scene.leftWindowObj
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

        op_cls.__left_mouse_down = False  # 初始化鼠标左键行为操作
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None  # 锁定圆环和模型的比例
        op_cls.__flag = False
        op_cls.__is_changed = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        bpy.context.scene.var = 113
        global smooth_modal_start
        if not smooth_modal_start:
            smooth_modal_start = True
            print("后期打磨平滑modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = LastSmooth
        global smooth_modal_start

        override1 = getOverride()
        area = override1['area']

        if context.area:
            context.area.tag_redraw()

        if bpy.context.screen.areas[0].spaces.active.context == 'TEXTURE':
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 113):
                if is_mouse_on_object(context, event):
                    if event.type == 'TIMER':
                        if op_cls.__left_mouse_down and bpy.context.mode == 'SCULPT':
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                            color_vertex_by_thickness()

                    elif event.type == 'LEFTMOUSE':  # 监听左键
                        if event.value == 'PRESS':  # 按下
                            op_cls.__left_mouse_down = True
                        return {'PASS_THROUGH'}

                    elif event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                        if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                            op_cls.__initial_mouse_x = event.mouse_region_x
                            op_cls.__initial_mouse_y = event.mouse_region_y
                            op_cls.__right_mouse_down = True
                            op_cls.__initial_radius = bpy.context.scene.tool_settings.unified_paint_settings.size
                        elif event.value == 'RELEASE':
                            op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                        return {'RUNNING_MODAL'}

                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if op_cls.__select_mode:
                                op_cls.__brush_mode = True
                                op_cls.__select_mode = False
                                bpy.ops.object.mode_set(mode='SCULPT')
                                bpy.context.scene.tool_settings.sculpt.show_brush = True
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
                                bpy.data.brushes["Smooth"].direction = 'SMOOTH'
                                color_vertex_by_thickness()

                        else:
                            if op_cls.__select_mode:
                                op_cls.__brush_mode = True
                                op_cls.__select_mode = False
                                bpy.ops.object.mode_set(mode='SCULPT')
                                bpy.context.scene.tool_settings.sculpt.show_brush = True
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
                                bpy.data.brushes["Smooth"].direction = 'SMOOTH'
                                color_vertex_by_thickness()

                        if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                            op_cls.__now_mouse_y = event.mouse_region_y
                            op_cls.__now_mouse_x = event.mouse_region_x
                            dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                                op_cls.__now_mouse_y - op_cls.__initial_mouse_y)))
                            # 上移扩大，下移缩小
                            op = 1
                            if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                                op = -1
                            # 设置圆环大小范围【50，200】
                            radius = max(op_cls.__initial_radius + dis * op, 50)
                            if radius > 200:
                                radius = 200
                            bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                            if context.scene.leftWindowObj == '右耳':
                                bpy.data.brushes[
                                    "SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_R
                            else:
                                bpy.data.brushes[
                                    "SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_L
                            # 保存改变的圆环大小
                            name = bpy.context.scene.leftWindowObj
                            if name == '右耳':
                                context.scene.damo_circleRadius_R = radius
                                context.scene.damo_strength_R = 25 / radius
                            else:
                                context.scene.damo_circleRadius_L = radius
                                context.scene.damo_strength_L = 25 / radius

                        if not op_cls.__left_mouse_down and not op_cls.__right_mouse_down:
                            cal_thickness(context, event)

                        return {'PASS_THROUGH'}

                else:
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                op_cls.__left_mouse_down = True
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        elif event.value == 'RELEASE':  # 圆环移到物体外，不再改变大小
                            if op_cls.__right_mouse_down:
                                op_cls.__right_mouse_down = False
                        return {'PASS_THROUGH'}
                    elif event.type == 'MIDDLEMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__select_mode and op_cls.__brush_mode:
                                op_cls.__brush_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False

                        if not op_cls.__select_mode:
                            op_cls.__select_mode = True
                            bpy.context.scene.tool_settings.sculpt.show_brush = False
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                            recolor_vertex()
                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 113 and bpy.context.scene.var in get_process_var_list("后期打磨"):
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                print("后期打磨平滑modal结束")
                smooth_modal_start = False
                return {'FINISHED'}

            # 鼠标在区域外
            else:
                if event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    if op_cls.__brush_mode:
                        op_cls.__brush_mode = False
                        op_cls.__select_mode = True
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        recolor_vertex()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                if op_cls.__timer:
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                print("后期打磨平滑modal结束")
                smooth_modal_start = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class LastDamo_Reset(bpy.types.Operator):
    bl_idname = "object.last_damo_reset"
    bl_label = "重置操作"
    bl_description = "点击按钮恢复到原来的模型"

    def invoke(self, context, event):
        print("reset invoke")
        self.execute(context)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        bpy.context.scene.var = 114
        name = bpy.context.scene.leftWindowObj
        # 使用LastDamoReset将操作物体还原
        resetname = name + "LastDamoReset"
        cur_obj = bpy.data.objects.get(name)
        ori_obj = bpy.data.objects.get(resetname)
        if(ori_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
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
    bl_icon = "brush.paint_weight.blur"
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
    bl_icon = "brush.paint_weight.blur"
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


def register_lastdamo_tools():
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


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyToolLastDamo, separator=True, group=False)
    # bpy.utils.register_tool(MyToolLastDamo3, separator=True,
    #                         group=False, after={MyToolLastDamo.bl_idname})
    # bpy.utils.register_tool(MyToolLastDamo5, separator=True,
    #                         group=False, after={MyToolLastDamo3.bl_idname})
    # bpy.utils.register_tool(MyToolLastDamo7, separator=True,
    #                         group=False, after={MyToolLastDamo5.bl_idname})
    #
    # bpy.utils.register_tool(MyToolLastDamo2, separator=True, group=False)
    # bpy.utils.register_tool(MyToolLastDamo4, separator=True,
    #                         group=False, after={MyToolLastDamo2.bl_idname})
    # bpy.utils.register_tool(MyToolLastDamo6, separator=True,
    #                         group=False, after={MyToolLastDamo4.bl_idname})
    # bpy.utils.register_tool(MyToolLastDamo8, separator=True,
    #                         group=False, after={MyToolLastDamo6.bl_idname})


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
