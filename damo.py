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
from .log_file import initial_log_file

# 控制台输出重定向
# output_redirect()
# initial_log_file()

prev_on_object = False  # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体上)

damo_mouse_listener = None  # 添加鼠标监听
left_mouse_press = False  # 鼠标左键是否按下
right_mouse_press = False  # 鼠标右键是否按下
middle_mouse_press = False  # 鼠标中键是否按下

smooth_modal_start = False  # 光滑模态是否开始，防止启动多个模态
thinning_modal_start = False  # 加薄模态是否开始，防止启动多个模态
thicking_modal_start = False  # 加厚模态是否开始，防止启动多个模态

# 用于保存未点击蜡厚度限制时超出限制的顶点下标
vertex_changesR = []
vertex_changesL = []

is_back = False
is_dialog = False


def get_is_back():
    global is_back
    return is_back


def get_is_dialog():
    global is_dialog
    return is_dialog


def remember_vertex_change():
    global vertex_changesR
    global vertex_changesL
    if bpy.context.scene.leftWindowObj == '右耳' and bpy.context.scene.localLaHouDuR:
        maxHoudu_cur = bpy.context.scene.maxLaHouDuR + bpy.context.scene.laHouDUR
        minLaHouDu_cur = bpy.context.scene.minLaHouDuR + bpy.context.scene.laHouDUR
        vertex_changesR = []
        vertex_changes = vertex_changesR
    elif bpy.context.scene.leftWindowObj == '左耳' and bpy.context.scene.localLaHouDuL:
        maxHoudu_cur = bpy.context.scene.maxLaHouDuL + bpy.context.scene.laHouDUL
        minLaHouDu_cur = bpy.context.scene.minLaHouDuL + bpy.context.scene.laHouDUL
        vertex_changesL = []
        vertex_changes = vertex_changesL
    # 获取活动对象
    obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    mesh = obj.data
    ori_obj = bpy.data.objects[bpy.context.scene.leftWindowObj + "DamoCompare"]
    ori_mesh = ori_obj.data

    # 遍历每个顶点
    for vert in mesh.vertices:
        dis_vec = vert.co - ori_mesh.vertices[vert.index].co
        distance = dis_vec.dot(dis_vec)
        thinkness = round(math.sqrt(distance), 2)
        ori_normal = ori_mesh.vertices[vert.index].normal
        flag = ori_normal.dot(dis_vec)
        if flag > 0:
            thinkness *= -1
        if (thinkness > maxHoudu_cur or thinkness < minLaHouDu_cur):
            vertex_changes.append(vert.index)


def set_modal_start_false():
    global thinning_modal_start
    thinning_modal_start = False
    global thicking_modal_start
    thicking_modal_start = False
    global smooth_modal_start
    smooth_modal_start = False


def get_modal_start():
    global thinning_modal_start
    global thicking_modal_start
    global smooth_modal_start
    return thinning_modal_start or thicking_modal_start or smooth_modal_start


def backToDamo():
    # 若添加铸造法之后切换到支撑或者排气孔模块,再由支撑或排气孔模块跳过铸造法模块直接切换回前面的模块,则需要对物体进行特殊的处理
    name = bpy.context.scene.leftWindowObj
    casting_name = name + "CastingCompare"
    casting_compare_obj = bpy.data.objects.get(casting_name)
    if (casting_compare_obj != None):
        cur_obj = bpy.data.objects.get(name)
        casting_reset_obj = bpy.data.objects.get(name + "CastingReset")
        casting_last_obj = bpy.data.objects.get(name + "CastingLast")
        casting_compare_last_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if (cur_obj != None and casting_reset_obj != None and casting_last_obj != None and casting_compare_last_obj != None):
            bpy.data.objects.remove(cur_obj, do_unlink=True)
            casting_compare_obj.name = name
            bpy.data.objects.remove(casting_reset_obj, do_unlink=True)
            bpy.data.objects.remove(casting_last_obj, do_unlink=True)
            bpy.data.objects.remove(casting_compare_last_obj, do_unlink=True)
    # 后面模块切换到传声孔的时候,判断是否存在用于铸造法的 软耳膜附件Casting  和  用于字体附件的 LabelPlaneForCasting 若存在则将其删除
    handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (label_obj != None):
        bpy.data.objects.remove(label_obj, do_unlink=True)

    # 将后续模块中的reset和last都删除
    jiahou_copy = bpy.data.objects.get(name + "LocalThickCopy")
    jiahou_compare = bpy.data.objects.get(name + "LocalThickCompare")
    jiahou_last = bpy.data.objects.get(name + "LocalThickLast")
    qiege_copy = bpy.data.objects.get(name + "QieGeCopy")
    qiege_last = bpy.data.objects.get(name + "QieGeLast")
    mould_reset = bpy.data.objects.get(name + "MouldReset")
    mould_last = bpy.data.objects.get(name + "MouldLast")
    sound_reset = bpy.data.objects.get(name + "SoundCanalReset")
    sound_last = bpy.data.objects.get(name + "SoundCanalLast")
    vent_reset = bpy.data.objects.get(name + "VentCanalReset")
    vent_last = bpy.data.objects.get(name + "VentCanalLast")
    handle_reset = bpy.data.objects.get(name + "HandleReset")
    handle_last = bpy.data.objects.get(name + "HandleLast")
    label_reset = bpy.data.objects.get(name + "LabelReset")
    label_last = bpy.data.objects.get(name + "LabelLast")
    casting_reset = bpy.data.objects.get(name + "CastingReset")
    casting_last = bpy.data.objects.get(name + "CastingLast")
    support_reset = bpy.data.objects.get(name + "SupportReset")
    support_last = bpy.data.objects.get(name + "SupportLast")
    sprue_reset = bpy.data.objects.get(name + "SprueReset")
    sprue_last = bpy.data.objects.get(name + "SprueLast")
    if (jiahou_copy != None):
        bpy.data.objects.remove(jiahou_copy, do_unlink=True)
    if (jiahou_compare != None):
        bpy.data.objects.remove(jiahou_compare, do_unlink=True)
    if (jiahou_last != None):
        bpy.data.objects.remove(jiahou_last, do_unlink=True)
    if (qiege_copy != None):
        bpy.data.objects.remove(qiege_copy, do_unlink=True)
    if (qiege_last != None):
        bpy.data.objects.remove(qiege_last, do_unlink=True)
    if (mould_reset != None):
        bpy.data.objects.remove(mould_reset, do_unlink=True)
    if (mould_last != None):
        bpy.data.objects.remove(mould_last, do_unlink=True)
    if (sound_reset != None):
        bpy.data.objects.remove(sound_reset, do_unlink=True)
    if (sound_last != None):
        bpy.data.objects.remove(sound_last, do_unlink=True)
    if (vent_reset != None):
        bpy.data.objects.remove(vent_reset, do_unlink=True)
    if (vent_last != None):
        bpy.data.objects.remove(vent_last, do_unlink=True)
    if (handle_reset != None):
        bpy.data.objects.remove(handle_reset, do_unlink=True)
    if (handle_last != None):
        bpy.data.objects.remove(handle_last, do_unlink=True)
    if (label_reset != None):
        bpy.data.objects.remove(label_reset, do_unlink=True)
    if (label_last != None):
        bpy.data.objects.remove(label_last, do_unlink=True)
    if (casting_reset != None):
        bpy.data.objects.remove(casting_reset, do_unlink=True)
    if (casting_last != None):
        bpy.data.objects.remove(casting_last, do_unlink=True)
    if (support_reset != None):
        bpy.data.objects.remove(support_reset, do_unlink=True)
    if (support_last != None):
        bpy.data.objects.remove(support_last, do_unlink=True)
    if (sprue_reset != None):
        bpy.data.objects.remove(sprue_reset, do_unlink=True)
    if (sprue_last != None):
        bpy.data.objects.remove(sprue_last, do_unlink=True)
    support_casting_reset = bpy.data.objects.get(name + "CastingCompareSupportReset")
    support_casting_last = bpy.data.objects.get(name + "CastingCompareSupportLast")
    if (support_casting_reset != None):
        bpy.data.objects.remove(support_casting_reset, do_unlink=True)
    if (support_casting_last != None):
        bpy.data.objects.remove(support_casting_last, do_unlink=True)

    # 删除支撑和排气孔中可能存在的对比物体
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (soft_support_compare_obj != None):
        bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    if (hard_support_compare_obj != None):
        bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    # 根据保存的DamoCopy,复制一份用来替换当前激活物体
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects.get(name)
    collections = None
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

        bpy.context.scene.transparent2R = True
        bpy.context.scene.transparent3R = False
        collections = bpy.data.collections['Right']

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

        bpy.context.scene.transparent2L = True
        bpy.context.scene.transparent3L = False
        collections = bpy.data.collections['Left']

    set_modal_start_false()

    for obj in collections.objects:
        if obj.type == 'MESH':
            # 获取网格数据
            me = obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            if len(bm.verts.layers.float_color) > 0:
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 0
                    colvert.y = 0.25
                    colvert.z = 1

            bm.to_mesh(me)
            bm.free()

    # 添加监听
    global damo_mouse_listener
    if (damo_mouse_listener == None):
        damo_mouse_listener = mouse.Listener(
            on_click=on_click
        )
        # 启动监听器
        damo_mouse_listener.start()


def backFromDamo():
    set_modal_start_false()
    # 根据当前激活物体,复制出来一份作为DamoCopy,用于后面模块返回到当前模块时恢复
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects.get(name)
    all_objs = bpy.data.objects
    collections = None
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

        bpy.context.scene.transparent2R = False
        bpy.context.scene.transparent3R = True
        duplicate_obj.hide_set(True)
        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_r"))
        moveToRight(duplicate_obj2)
        duplicate_obj2.hide_set(True)
        active_obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = active_obj
        collections = bpy.data.collections['Right']

    elif name == '左耳':
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

        bpy.context.scene.transparent2L = False
        bpy.context.scene.transparent3L = True
        duplicate_obj.hide_set(True)
        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_l"))
        moveToLeft(duplicate_obj2)
        duplicate_obj2.hide_set(True)
        active_obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = active_obj
        collections = bpy.data.collections['Left']

    # 将添加的鼠标监听删除
    global damo_mouse_listener
    if (damo_mouse_listener != None):
        damo_mouse_listener.stop()
        damo_mouse_listener = None

    if bpy.context.mode == 'SCULPT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 获取网格数据
    for obj in collections.objects:
        if obj.type == 'MESH':
            me = obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            if len(bm.verts.layers.float_color) > 0:
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 1
                    colvert.y = 0.319
                    colvert.z = 0.133

            bm.to_mesh(me)
            bm.free()

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def frontFromDamo():
    set_modal_start_false()
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects.get(name)
    all_objs = bpy.data.objects
    collections = None
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

        # bpy.context.scene.transparent2R = False
        # bpy.context.scene.transparent3R = True
        duplicate_obj.hide_set(True)
        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_r"))
        moveToRight(duplicate_obj2)
        duplicate_obj2.hide_set(True)
        active_obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = active_obj
        collections = bpy.data.collections['Right']

    elif name == '左耳':
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

        # bpy.context.scene.transparent2L = False
        # bpy.context.scene.transparent3L = True
        duplicate_obj.hide_set(True)
        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_l"))
        moveToLeft(duplicate_obj2)
        duplicate_obj2.hide_set(True)
        active_obj = bpy.data.objects[name]
        bpy.context.view_layer.objects.active = active_obj
        collections = bpy.data.collections['Left']

    # 将添加的鼠标监听删除
    global damo_mouse_listener
    if (damo_mouse_listener != None):
        damo_mouse_listener.stop()
        damo_mouse_listener = None

    if bpy.context.mode == 'SCULPT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 获取网格数据
    # for obj in collections.objects:
    #     if obj.type == 'MESH':
    #         me = obj.data
    #         # 创建bmesh对象
    #         bm = bmesh.new()
    #         # 将网格数据复制到bmesh对象
    #         bm.from_mesh(me)
    #         if len(bm.verts.layers.float_color) > 0:
    #             color_lay = bm.verts.layers.float_color["Color"]
    #             for vert in bm.verts:
    #                 colvert = vert[color_lay]
    #                 colvert.x = 1
    #                 colvert.y = 0.319
    #                 colvert.z = 0.133
    #
    #         bm.to_mesh(me)
    #         bm.free()

    # 激活右耳或左耳为当前活动物体
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(True)
    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def frontToDamo():
    set_modal_start_false()
    # 从切割模具模块回来，根据切割后的结果重新复制出一份用于对比的物体
    name = bpy.context.scene.leftWindowObj
    compare_name = name + 'DamoCompare'
    if name == "右耳":
        thickness = bpy.context.scene.laHouDUR
    elif name == "左耳":
        thickness = bpy.context.scene.laHouDUL
    active_obj = bpy.data.objects.get(name)
    is_compare_obj = bpy.data.objects.get(compare_name)
    if is_compare_obj != None:
        bpy.data.objects.remove(bpy.data.objects.get(compare_name), do_unlink=True)
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.name = compare_name
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.hide_set(True)

        if thickness != 0:
            mesh = duplicate_obj.data
            for idx, vert in enumerate(mesh.vertices):
                vert.co = vert.co - mesh.vertices[idx].normal.normalized() * thickness

    collections = None
    if name == '右耳':
        collections = bpy.data.collections['Right']
        bpy.context.scene.transparent2R = True
        bpy.context.scene.transparent3R = False
    elif name == '左耳':
        collections = bpy.data.collections['Left']
        bpy.context.scene.transparent2R = True
        bpy.context.scene.transparent3R = False
    for obj in collections.objects:
        if obj.type == 'MESH':
            # 获取网格数据
            me = obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            if len(bm.verts.layers.float_color) > 0:
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    colvert.x = 0
                    colvert.y = 0.25
                    colvert.z = 1

            bm.to_mesh(me)
            bm.free()


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
    __initial_radius = None

    __flag = False
    __is_changed = False

    # #打磨模块下左侧的三个按钮才起作用
    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        global smooth_modal_start
        smooth_modal_start = False
        global thinning_modal_start
        thinning_modal_start = False
        op_cls = Thickening
        bpy.context.scene.var = 1
        # print("thicking_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "ADD"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = bpy.context.active_object.name
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_R
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_L

        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
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
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        global thicking_modal_start
        if not thicking_modal_start:
            print("打厚modal")
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
        op_cls = Thickening
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press
        global vertex_changesR
        global vertex_changesL

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 1):
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

                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                        localLaHouDu_cur = None
                        maxHoudu_cur = None
                        minLaHouDu_cur = None
                        if name == '右耳':
                            localLaHouDu_cur = context.scene.localLaHouDuR
                            maxHoudu_cur = context.scene.maxLaHouDuR + context.scene.laHouDUR
                            minLaHouDu_cur = context.scene.minLaHouDuR + context.scene.laHouDUR
                            vertex_changes = vertex_changesR
                        elif name == '左耳':
                            localLaHouDu_cur = context.scene.localLaHouDuL
                            maxHoudu_cur = context.scene.maxLaHouDuL + context.scene.laHouDUL
                            minLaHouDu_cur = context.scene.minLaHouDuL + context.scene.laHouDUL
                            vertex_changes = vertex_changesL
                        # 厚度限制
                        if (localLaHouDu_cur):
                            maxHoudu = maxHoudu_cur
                            minHoudu = minLaHouDu_cur
                            # print("最大厚度：",maxHoudu)
                            # print("最小厚度：",minHoudu)
                            if (thinkness > maxHoudu or thinkness < minHoudu) and (index_color not in vertex_changes):
                                # print("原坐标：",oribm.verts[index_color].co)
                                # print("现坐标：",bm.verts[index_color].co)
                                # 理论厚度
                                if thinkness > maxHoudu:
                                    length = maxHoudu
                                elif thinkness < minHoudu:
                                    length = minHoudu
                                # print("实际厚度：",thinkness)
                                # print("理论厚度：",length)
                                # 根据理论厚度修改坐标
                                if length > 0:
                                    bm.verts[index_color].co = oribm.verts[index_color].co - \
                                                               disvec_color.normalized() * length
                                else:
                                    bm.verts[index_color].co = oribm.verts[index_color].co + \
                                                               disvec_color.normalized() * length
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

                elif bpy.context.mode == 'OBJECT' and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.ops.wm.tool_set_by_id(
                        name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "ADD"
                    bpy.context.scene.tool_settings.sculpt.show_brush = True

                    # 重新上色
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                        if context.scene.leftWindowObj == '右耳':
                            bpy.data.brushes["SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_R
                        else:
                            bpy.data.brushes["SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_L
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
                            colvert.x = 0
                            colvert.y = 0.25
                            colvert.z = 1

                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

                if not left_mouse_press and op_cls.__flag:
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
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
                        colvert.x = 0
                        colvert.y = 0.25
                        colvert.z = 1

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

        elif bpy.context.scene.var != 1:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
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
                    colvert.x = 0
                    colvert.y = 0.25
                    colvert.z = 1
                bm.to_mesh(me)
                bm.free()
                op_cls.__is_changed = True
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


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

        op_cls = Thinning
        bpy.context.scene.var = 2
        # print("thinning_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = bpy.context.active_object.name
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_R
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_L

        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
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
        op_cls = Thinning
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press
        global vertex_changesR
        global vertex_changesL

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 2):
            if is_mouse_on_object(context, event):
                if op_cls.__is_changed == True:
                    op_cls.__is_changed = False
                if is_changed(context, event) and not left_mouse_press:
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.context.scene.tool_settings.sculpt.show_brush = True
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
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                        localLaHouDu_cur = None
                        maxHoudu_cur = None
                        minHouDu_cur = None
                        if name == '右耳':
                            localLaHouDu_cur = context.scene.localLaHouDuR
                            maxHoudu_cur = context.scene.maxLaHouDuR + context.scene.laHouDUR
                            minHouDu_cur = context.scene.minLaHouDuR + context.scene.laHouDUR
                            vertex_changes = vertex_changesR
                        elif name == '左耳':
                            localLaHouDu_cur = context.scene.localLaHouDuL
                            maxHoudu_cur = context.scene.maxLaHouDuL + context.scene.laHouDUR
                            minHouDu_cur = context.scene.minLaHouDuL + context.scene.laHouDUR
                            vertex_changes = vertex_changesL
                        # 厚度限制
                        if (localLaHouDu_cur):
                            maxHoudu = maxHoudu_cur
                            minHoudu = minHouDu_cur
                            # print("最大厚度：",maxHoudu)
                            # print("最小厚度：",minHoudu)
                            if (thinkness > maxHoudu or thinkness < minHoudu) and (index_color not in vertex_changes):
                                # print("原坐标：",oribm.verts[index_color].co)
                                # print("现坐标：",bm.verts[index_color].co)
                                # 理论厚度
                                if thinkness > maxHoudu:
                                    length = maxHoudu
                                elif thinkness < minHoudu:
                                    length = minHoudu
                                # print("实际厚度：",thinkness)
                                # print("理论厚度：",length)
                                # 根据理论厚度修改坐标
                                if length > 0:
                                    bm.verts[index_color].co = oribm.verts[index_color].co - \
                                                               disvec_color.normalized() * length
                                else:
                                    bm.verts[index_color].co = oribm.verts[index_color].co + \
                                                               disvec_color.normalized() * length
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

                elif bpy.context.mode == 'OBJECT' and not left_mouse_press:
                    bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.ops.wm.tool_set_by_id(
                        name="builtin_brush.Draw")  # 调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
                    bpy.context.scene.tool_settings.sculpt.show_brush = True

                    # 重新上色
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                        if context.scene.leftWindowObj == '右耳':
                            bpy.data.brushes["SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_R
                        else:
                            bpy.data.brushes["SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_L
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
                            colvert.x = 0
                            colvert.y = 0.25
                            colvert.z = 1

                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

                if not left_mouse_press and op_cls.__flag:
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
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
                        colvert.x = 0
                        colvert.y = 0.25
                        colvert.z = 1

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

        elif (bpy.context.scene.var != 2):
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
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
                    colvert.x = 0
                    colvert.y = 0.25
                    colvert.z = 1
                bm.to_mesh(me)
                bm.free()
                op_cls.__is_changed = True
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


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

        op_cls = Smooth
        bpy.context.scene.var = 3
        # print("smooth_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
        bpy.data.brushes["Smooth"].direction = 'SMOOTH'
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500

        # 设置圆环初始大小
        name = bpy.context.active_object.name
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
            bpy.data.brushes["Smooth"].strength = strength * context.scene.damo_scale_strength_R
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
            bpy.data.brushes["Smooth"].strength = strength * context.scene.damo_scale_strength_L

        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
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
        op_cls = Smooth
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press
        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y+area.height and bpy.context.scene.var == 3):
            if is_mouse_on_object(context, event):
                if op_cls.__is_changed == True:
                    op_cls.__is_changed = False
                if is_changed(context, event) and not left_mouse_press:
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                        bpy.ops.object.mode_set(mode='SCULPT')
                    bpy.context.scene.tool_settings.sculpt.show_brush = True
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
                    bpy.data.brushes["Smooth"].direction = 'SMOOTH'

                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                    active_obj = context.active_object
                    # 获取网格数据
                    me = active_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    # 原始数据
                    ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
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
                        if context.scene.leftWindowObj == '右耳':
                            bpy.data.brushes["Smooth"].strength = 25 / radius * context.scene.damo_scale_strength_R
                        else:
                            bpy.data.brushes["Smooth"].strength = 25 / radius * context.scene.damo_scale_strength_L
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
                            colvert.x = 0
                            colvert.y = 0.25
                            colvert.z = 1

                        MyHandleClass.remove_handler()
                        context.area.tag_redraw()

                        bm.to_mesh(me)
                        bm.free()

                if not left_mouse_press and op_cls.__flag:
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
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
                        colvert.x = 0
                        colvert.y = 0.25
                        colvert.z = 1

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

        elif (bpy.context.scene.var != 3):
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
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
                    colvert.x = 0
                    colvert.y = 0.25
                    colvert.z = 1
                bm.to_mesh(me)
                bm.free()
                op_cls.__is_changed = True
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}


class Damo_Reset(bpy.types.Operator):
    bl_idname = "object.damo_reset"
    bl_label = "重置操作"
    bl_description = "点击按钮恢复到原来的模型"

    def invoke(self, context, event):
        set_modal_start_false()
        print("reset invoke")
        self.excute(context, event)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def excute(self, context, event):
        bpy.context.scene.var = 4
        active_obj = bpy.context.active_object
        name = bpy.context.object.name
        reset_name = name + "DamoReset"
        if bpy.data.objects.get(reset_name):
            ori_obj = bpy.data.objects[reset_name]
            # 先根据重置的物体复制出一份新的物体
            duplicate_obj = ori_obj.copy()
            duplicate_obj.data = ori_obj.data.copy()
            duplicate_obj.name = reset_name + "copy"
            duplicate_obj.animation_data_clear()
            # 将复制的物体加入到场景集合中
            scene = bpy.context.scene
            scene.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            elif name == '左耳':
                moveToLeft(duplicate_obj)
            duplicate_obj.hide_set(True)

            # 替换原有的物体
            bpy.data.objects.remove(active_obj, do_unlink=True)
            ori_obj.name = name
            ori_obj.hide_set(False)

            duplicate_obj.name = reset_name

        bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[context.scene.leftWindowObj].select_set(True)


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


class DamoOperator(bpy.types.Operator):
    bl_idname = "object.damo_operator"
    bl_label = "3D Model"

    my_string: bpy.props.StringProperty(name="", default="可能会丢失数据")
    my_bool: bpy.props.BoolProperty(name="确认")

    def execute(self, context):
        global is_back
        global is_dialog
        active_object = bpy.data.objects[context.scene.leftWindowObj]
        if context.scene.leftWindowObj == '右耳':
            thickness = context.scene.laHouDUR
        elif context.scene.leftWindowObj == '左耳':
            thickness = context.scene.laHouDUL
        # 确认
        if self.my_bool:
            is_back = True
            # 根据最原始的物体加蜡
            ori_obj = bpy.data.objects[context.scene.leftWindowObj + 'OriginForShow']
            me = active_object.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            ori_me = ori_obj.data
            ori_bm = bmesh.new()
            ori_bm.from_mesh(ori_me)
            ori_bm.verts.ensure_lookup_table()

            for vert in bm.verts:
                vert.co = ori_bm.verts[vert.index].co + ori_bm.verts[vert.index].normal.normalized() * thickness
            bm.to_mesh(me)
            bm.free()
            ori_bm.free()

        else:
            is_dialog = True
            if context.scene.leftWindowObj == '右耳':
                context.scene.laHouDUR -= 0.05
            elif context.scene.leftWindowObj == '左耳':
                context.scene.laHouDUR -= 0.05
            is_dialog = False

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        context.window.cursor_warp(context.window.width // 2, context.window.height // 2)
        return wm.invoke_props_dialog(self)


# 注册类
_classes = [

    Thickening,
    Thinning,
    Smooth,
    Damo_Reset,
    DamoOperator
]


def register_damo_tools():
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


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool, separator=True, group=False)
    # bpy.utils.register_tool(MyTool3, separator=True,
    #                         group=False, after={MyTool.bl_idname})
    # bpy.utils.register_tool(MyTool5, separator=True,
    #                         group=False, after={MyTool3.bl_idname})
    # bpy.utils.register_tool(MyTool7, separator=True,
    #                         group=False, after={MyTool5.bl_idname})
    #
    # bpy.utils.register_tool(MyTool2, separator=True, group=False)
    # bpy.utils.register_tool(MyTool4, separator=True,
    #                         group=False, after={MyTool2.bl_idname})
    # bpy.utils.register_tool(MyTool6, separator=True,
    #                         group=False, after={MyTool4.bl_idname})
    # bpy.utils.register_tool(MyTool8, separator=True,
    #                         group=False, after={MyTool6.bl_idname})


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
