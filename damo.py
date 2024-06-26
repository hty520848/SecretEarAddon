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


def copy_object():
    if not bpy.data.objects.get('右耳OriginForShow'):  # 未调整蜡厚度
        active_object = bpy.data.objects['右耳']
        duplicate_obj = active_object.copy()
        duplicate_obj.data = active_object.data.copy()
        duplicate_obj.name = '右耳OriginForShow'
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.hide_set(True)

    for active_obj in bpy.data.objects:  # 复制DamoReset
        if active_obj.name == '右耳':
            name = active_obj.name + "DamoReset"
            is_rightobj = bpy.data.objects.get(name)
            if not is_rightobj:
                duplicate_obj = active_obj.copy()
                duplicate_obj.data = active_obj.data.copy()
                duplicate_obj.name = name
                duplicate_obj.animation_data_clear()
                # 将复制的物体加入到场景集合中
                scene = bpy.context.scene
                scene.collection.objects.link(duplicate_obj)
                moveToRight(duplicate_obj)
                duplicate_obj.hide_set(True)

        if active_obj.name == '左耳':
            name = active_obj.name + "DamoReset"
            is_leftobj = bpy.data.objects.get(name)
            if not is_leftobj:
                duplicate_obj = active_obj.copy()
                duplicate_obj.data = active_obj.data.copy()
                duplicate_obj.name = name
                duplicate_obj.animation_data_clear()
                # 将复制的物体加入到场景集合中
                scene = bpy.context.scene
                scene.collection.objects.link(duplicate_obj)
                moveToLeft(duplicate_obj)
                duplicate_obj.hide_set(True)


def backToDamo():
    # 根据保存的DamoCopy,复制一份用来替换当前激活物体
    active_obj = bpy.context.active_object
    name = bpy.context.object.name
    if name == '右耳':
        copyname = name + "DamoCopy"
        waxname = name + "WaxForShow"
        if bpy.data.objects.get(copyname):
            ori_obj = bpy.data.objects[copyname]
            wax_obj = bpy.data.objects[waxname]
            bpy.data.objects.remove(active_obj, do_unlink=True)
            bpy.data.objects.remove(wax_obj, do_unlink=True)
            duplicate_obj = ori_obj.copy()
            duplicate_obj.data = ori_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = name
            bpy.context.scene.collection.objects.link(duplicate_obj)
            moveToRight(duplicate_obj)
            bpy.context.view_layer.objects.active = duplicate_obj
    elif name == '左耳':
        copyname = name + "DamoCopy"
        waxname = name + "WaxForShow"
        if bpy.data.objects.get(copyname):
            ori_obj = bpy.data.objects[copyname]
            wax_obj = bpy.data.objects[waxname]
            bpy.data.objects.remove(active_obj, do_unlink=True)
            bpy.data.objects.remove(wax_obj, do_unlink=True)
            duplicate_obj = ori_obj.copy()
            duplicate_obj.data = ori_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = name
            bpy.context.scene.collection.objects.link(duplicate_obj)
            moveToLeft(duplicate_obj)
            bpy.context.view_layer.objects.active = duplicate_obj

    # 添加监听
    global damo_mouse_listener
    if (damo_mouse_listener == None):
        damo_mouse_listener = mouse.Listener(
            on_click=on_click
        )
        # 启动监听器
        damo_mouse_listener.start()


def backFromDamo():
    # 根据当前激活物体,复制出来一份作为DamoCopy,用于后面模块返回到当前模块时恢复
    active_obj = bpy.context.active_object
    name = active_obj.name
    all_objs = bpy.data.objects
    if name == '右耳':
        # 删除已经存在的右耳DamoCopy
        for selected_obj in all_objs:
            if (selected_obj.name == "右耳DamoCopy"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "DamoCopy"
        bpy.context.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.hide_set(True)
        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue"))
        moveToRight(duplicate_obj2)
        duplicate_obj2.hide_set(True)
        active_obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = active_obj

    if name == '左耳':
        # 删除已经存在的左耳DamoCopy
        for selected_obj in all_objs:
            if (selected_obj.name == "左耳DamoCopy"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "DamoCopy"
        bpy.context.collection.objects.link(duplicate_obj)
        moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(True)
        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue"))
        moveToLeft(duplicate_obj2)
        duplicate_obj2.hide_set(True)
        active_obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = active_obj

    # 将添加的鼠标监听删除
    global damo_mouse_listener
    if (damo_mouse_listener != None):
        damo_mouse_listener.stop()
        damo_mouse_listener = None


def on_click(x, y, button, pressed):
    global left_mouse_press
    # 鼠标点击事件处理函数
    if button == mouse.Button.left and pressed:
        # print('press')
        left_mouse_press = True
    elif button == mouse.Button.left and not pressed:
        # print('release')
        left_mouse_press = False


# 打磨功能模块左侧按钮的加厚操作
class Thickening(bpy.types.Operator):
    bl_idname = "object.thickening"
    bl_label = "加厚操作"
    bl_description = "点击鼠标左键加厚模型，右键改变区域选取圆环的大小"
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None

    __flag = False

    # #打磨模块下左侧的三个按钮才起作用
    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        op_cls = Thickening
        bpy.context.scene.var = 1
        print("thicking_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "ADD"
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
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
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        copy_object()
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)  # 进入modal模式

        global damo_mouse_listener
        if (damo_mouse_listener == None):
            damo_mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            damo_mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Thickening
        global left_mouse_press

        # 重绘区域
        if context.area:
            context.area.tag_redraw()

        if (bpy.context.scene.var == 1):
            if (is_mouse_on_object(context, event)):
                if (is_changed(context, event)):
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    # bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(
                        name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "ADD"

                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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

                if event.type == 'TIMER' and left_mouse_press:
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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

                        # 厚度限制
                        if (context.scene.localLaHouDu):
                            # print('是否开启',context.scene.localLaHouDu)
                            maxHoudu = context.scene.maxLaHouDu
                            minHoudu = context.scene.minLaHouDu
                            # print("最大厚度：",maxHoudu)
                            # print("最小厚度：",minHoudu)
                            if (thinkness > maxHoudu or thinkness < minHoudu):
                                # print("原坐标：",oribm.verts[index_color].co)
                                # print("现坐标：",bm.verts[index_color].co)
                                # 理论厚度
                                if thinkness > maxHoudu:
                                    lenth = maxHoudu
                                elif thinkness < minHoudu:
                                    lenth = minHoudu
                                # print("实际厚度：",thinkness)
                                # print("理论厚度：",lenth)
                                # 根据理论厚度修改坐标
                                bm.verts[index_color].co = oribm.verts[index_color].co - \
                                                           disvec_color.normalized() * lenth
                                # print("原坐标：",oribm.verts[index_color].co)
                                # print("现坐标：",bm.verts[index_color].co)
                                disvec_color = oribm.verts[index_color].co - \
                                               bm.verts[index_color].co
                                dis_color = disvec_color.dot(
                                    disvec_color)
                                thinkness = round(
                                    math.sqrt(dis_color), 2)
                                origin_veccol = oribm.verts[index_color].normal
                                flag_color = origin_veccol.dot(
                                    disvec_color)
                                if flag_color > 0:
                                    thinkness *= -1
                                # print("修改后的厚度：",thinkness)

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
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis

            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event) and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                    # bpy.context.scene.tool_settings.sculpt.show_brush = False
                    # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")
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
                    MyHandleClass.remove_handler()
                    context.area.tag_redraw()

                    bm.to_mesh(me)
                    bm.free()

                elif not is_changed(context, event) and left_mouse_press:
                    op_cls.__flag = True

                elif op_cls.__flag == True and not left_mouse_press:
                    op_cls.__flag = False
                    if bpy.context.mode == 'SCULPT':
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        # bpy.context.scene.tool_settings.sculpt.show_brush = False
                        # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")

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
                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()
                    else:
                        pass

            return {'PASS_THROUGH'}
        else:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}


# 打磨功能模块左侧按钮的减薄操作
class Thinning(bpy.types.Operator):
    bl_idname = "object.thinning"
    bl_label = "减薄操作"
    bl_description = "点击鼠标左键减薄模型，右键改变区域选取圆环的大小"
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None

    __flag = False

    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        op_cls = Thinning
        bpy.context.scene.var = 2
        print("thinning_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
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
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        copy_object()
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)  # 进入modal模式

        global damo_mouse_listener
        if (damo_mouse_listener == None):
            damo_mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            damo_mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Thinning
        global left_mouse_press

        active_obj = context.active_object

        # 重绘区域
        if context.area:
            context.area.tag_redraw()

        if (bpy.context.scene.var == 2):
            if (is_mouse_on_object(context, event)):
                if (is_changed(context, event)):
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    # bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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

                if event.type == 'TIMER' and left_mouse_press:
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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

                        # 厚度限制
                        if (context.scene.localLaHouDu):
                            # print('是否开启',context.scene.localLaHouDu)
                            maxHoudu = context.scene.maxLaHouDu
                            minHoudu = context.scene.minLaHouDu
                            # print("最大厚度：",maxHoudu)
                            # print("最小厚度：",minHoudu)
                            if (thinkness > maxHoudu or thinkness < minHoudu):
                                # print("原坐标：",oribm.verts[index_color].co)
                                # print("现坐标：",bm.verts[index_color].co)
                                # 理论厚度
                                if thinkness > maxHoudu:
                                    lenth = maxHoudu
                                elif thinkness < minHoudu:
                                    lenth = minHoudu
                                # print("实际厚度：",thinkness)
                                # print("理论厚度：",lenth)
                                # 根据理论厚度修改坐标
                                bm.verts[index_color].co = oribm.verts[index_color].co + \
                                                           disvec_color.normalized() * lenth
                                # print("原坐标：",oribm.verts[index_color].co)
                                # print("现坐标：",bm.verts[index_color].co)
                                disvec_color = oribm.verts[index_color].co - \
                                               bm.verts[index_color].co
                                dis_color = disvec_color.dot(
                                    disvec_color)
                                thinkness = round(
                                    math.sqrt(dis_color), 2)
                                origin_veccol = oribm.verts[index_color].normal
                                flag_color = origin_veccol.dot(
                                    disvec_color)
                                if flag_color > 0:
                                    thinkness *= -1
                                # print("修改后的厚度：",thinkness)

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
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis

            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event) and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                    # bpy.context.scene.tool_settings.sculpt.show_brush = False
                    # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")

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
                    MyHandleClass.remove_handler()
                    context.area.tag_redraw()

                    bm.to_mesh(me)
                    bm.free()

                elif not is_changed(context, event) and left_mouse_press:
                    op_cls.__flag = True

                elif op_cls.__flag == True and not left_mouse_press:
                    if bpy.context.mode == 'SCULPT':
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        # bpy.context.scene.tool_settings.sculpt.show_brush = False
                        # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")
                        op_cls.__flag = False

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
                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

            return {'PASS_THROUGH'}
        else:
            if not op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}


# 打磨功能模块左侧按钮的光滑操作
class Smooth(bpy.types.Operator):
    bl_idname = "object.smooth"
    bl_label = "光滑操作"
    bl_description = "点击鼠标左键光滑模型，右键改变区域选取圆环的大小"
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __timer = None
    __flag = False

    # @classmethod
    # def poll(context):
    #     if(context.space_data.context == 'RENDER'):
    #         return True
    #     else:
    #         return False

    def invoke(self, context, event):
        op_cls = Smooth
        bpy.context.scene.var = 3
        print("smooth_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
        bpy.data.brushes["SculptDraw"].direction = "ADD"
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
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
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        copy_object()
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)  # 进入modal模式

        global damo_mouse_listener
        if (damo_mouse_listener == None):
            damo_mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            damo_mouse_listener.start()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Smooth
        global left_mouse_press

        active_obj = context.active_object

        # 重绘区域
        if context.area:
            context.area.tag_redraw()

        if (bpy.context.scene.var == 3):
            if (is_mouse_on_object(context, event)):
                if (is_changed(context, event)):
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    # bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
                    bpy.data.brushes["SculptDraw"].direction = "ADD"

                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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

                if event.type == 'TIMER' and left_mouse_press:
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}

                elif event.type == 'MOUSEMOVE':
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "OriginForShow"]
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
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis

            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event) and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                    # bpy.context.scene.tool_settings.sculpt.show_brush = False
                    # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")
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
                    MyHandleClass.remove_handler()
                    context.area.tag_redraw()

                    bm.to_mesh(me)
                    bm.free()

                elif not is_changed(context, event) and left_mouse_press:
                    op_cls.__flag = True

                elif op_cls.__flag == True and not left_mouse_press:
                    if bpy.context.mode == 'SCULPT':
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        # bpy.context.scene.tool_settings.sculpt.show_brush = False
                        # bpy.ops.wm.tool_set_by_id(name="builtin.box_mask")
                        op_cls.__flag = False

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
                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

            return {'PASS_THROUGH'}
        else:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'FINISHED'}


class Damo_Reset(bpy.types.Operator):
    bl_idname = "object.damo_reset"
    bl_label = "重置操作"
    bl_description = "点击按钮恢复到原来的模型"

    def invoke(self, context, event):
        print("reset invoke")
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context, event):
        bpy.context.scene.var = 4
        active_obj = bpy.context.active_object
        name = bpy.context.object.name
        # copyname = name + ".001"
        reset_name = name + "DamoReset"
        if bpy.data.objects.get(reset_name):
            ori_obj = bpy.data.objects[reset_name]
            bpy.data.objects.remove(active_obj, do_unlink=True)
            ori_obj.name = name
            ori_obj.hide_set(False)

        bpy.ops.object.select_all(action='DESELECT')
        for i in bpy.context.visible_objects:  # 迭代所有可见物体,激活当前物体
            if i.name == name:
                bpy.context.view_layer.objects.active = i
                i.select_set(state=True)

        # bpy.ops.geometry.color_attribute_add()
        # active_obj = bpy.context.active_object
        # me = active_obj.data
        # bm = bmesh.new()
        # bm.from_mesh(me)
        # color_lay = bm.verts.layers.float_color["Color"]
        # for vert in bm.verts:
        #     colvert = vert[color_lay]
        #     colvert.x = 0
        #     colvert.y = 0.25
        #     colvert.z = 1
        # bm.to_mesh(me)
        # bm.free()

        return {'FINISHED'}


class MyTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thickening"
    bl_label = "加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        ("object.thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thickening2"
    bl_label = "加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        ("object.thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thinning"
    bl_label = "磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.mesh.spin"
    bl_widget = None
    bl_keymap = (
        ("object.thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool4(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thinning2"
    bl_label = "磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.mesh.spin"
    bl_widget = None
    bl_keymap = (
        ("object.thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool5(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smooth"
    bl_label = "圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "ops.mesh.extrude_region_move"
    bl_widget = None
    bl_keymap = (
        ("object.smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool6(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smooth2"
    bl_label = "圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "ops.mesh.extrude_region_move"
    bl_widget = None
    bl_keymap = (
        ("object.smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool7(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.damo_reset"
    bl_label = "重置"
    bl_description = (
        "点击进行重置操作"
    )
    bl_icon = "ops.mesh.inset"
    bl_widget = None
    bl_keymap = (
        ("object.damo_reset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool8(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.damo_reset2"
    bl_label = "重置"
    bl_description = (
        "点击进行重置操作"
    )
    bl_icon = "ops.mesh.inset"
    bl_widget = None
    bl_keymap = (
        ("object.damo_reset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [

    Thickening,
    Thinning,
    Smooth,
    Damo_Reset
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool, separator=True, group=False)
    bpy.utils.register_tool(MyTool3, separator=True,
                            group=False, after={MyTool.bl_idname})
    bpy.utils.register_tool(MyTool5, separator=True,
                            group=False, after={MyTool3.bl_idname})
    bpy.utils.register_tool(MyTool7, separator=True,
                            group=False, after={MyTool5.bl_idname})

    bpy.utils.register_tool(MyTool2, separator=True, group=False)
    bpy.utils.register_tool(MyTool4, separator=True,
                            group=False, after={MyTool2.bl_idname})
    bpy.utils.register_tool(MyTool6, separator=True,
                            group=False, after={MyTool4.bl_idname})
    bpy.utils.register_tool(MyTool8, separator=True,
                            group=False, after={MyTool6.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool)
    bpy.utils.unregister_tool(MyTool3)
    bpy.utils.unregister_tool(MyTool5)
    bpy.utils.unregister_tool(MyTool7)

    bpy.utils.unregister_tool(MyTool2)
    bpy.utils.unregister_tool(MyTool4)
    bpy.utils.unregister_tool(MyTool6)
    bpy.utils.unregister_tool(MyTool8)
