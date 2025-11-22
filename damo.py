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
from .log_file import initial_log_file
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running,\
    get_process_var_list, get_mirror_context, set_mirror_context
from .tool import track_time,reset_time_tracker
from .global_manager import global_manager
from .back_and_forward import record_state, backup_state, forward_state

# 控制台输出重定向
# output_redirect()
initial_log_file()

prev_on_object = False  # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体上)

thickening_modal_start = False  # 加厚模态是否开始，防止启动多个模态
thinning_modal_start = False  # 加薄模态是否开始，防止启动多个模态
smooth_modal_start = False  # 光滑模态是否开始，防止启动多个模态

# 用于保存顶点坐标更改的字典
vertex_changesR = {}
vertex_changesL = {}

# 存储先前的厚度值
previous_thicknessR = 0.0
previous_thicknessL = 0.0
# 用于防止更改厚度值时触发回调函数
is_dialog = False


def set_previous_thicknessR(value):
    global previous_thicknessR
    previous_thicknessR = value

def set_previous_thicknessL(value):
    global previous_thicknessL
    previous_thicknessL = value

def get_is_dialog():
    global is_dialog
    return is_dialog

def register_damo_globals():
    global previous_thicknessR, previous_thicknessL
    global_manager.register("previous_thicknessR", previous_thicknessR)
    global_manager.register("previous_thicknessL", previous_thicknessL)

    
def damo_backup():
    backup_state()


def damo_forward():
    forward_state()


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
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

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


def backFromDamo():
    # 根据当前激活物体,复制出来一份作为DamoCopy,用于后面模块返回到当前模块时恢复
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects.get(name)
    all_objs = bpy.data.objects
    collections = None
    if name == '右耳':
        # 删除已经存在的右耳DamoCopy, 右耳WaxForShow
        for selected_obj in all_objs:
            if (selected_obj.name == "右耳DamoCopy"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
            elif (selected_obj.name == "右耳WaxForShow"):
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
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_r"))
        moveToRight(duplicate_obj2)
        duplicate_obj2.hide_set(True)

        bpy.context.scene.transparent2R = False
        bpy.context.scene.transparent3R = True
        collections = bpy.data.collections['Right']

    elif name == '左耳':
        # 删除已经存在的左耳DamoCopy, 左耳WaxForShow
        for selected_obj in all_objs:
            if (selected_obj.name == "左耳DamoCopy"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
            elif (selected_obj.name == "左耳WaxForShow"):
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
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_l"))
        moveToLeft(duplicate_obj2)
        duplicate_obj2.hide_set(True)

        bpy.context.scene.transparent2L = False
        bpy.context.scene.transparent3L = True
        collections = bpy.data.collections['Left']

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
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects.get(name)
    all_objs = bpy.data.objects
    collections = None
    if name == '右耳':
        # 删除已经存在的右耳DamoCopy, 右耳WaxForShow
        for selected_obj in all_objs:
            if (selected_obj.name == "右耳DamoCopy"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
            elif (selected_obj.name == "右耳WaxForShow"):
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
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_r"))
        moveToRight(duplicate_obj2)
        duplicate_obj2.hide_set(True)

        # bpy.context.scene.transparent2R = False
        # bpy.context.scene.transparent3R = True
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
        duplicate_obj.hide_set(True)

        duplicate_obj2 = active_obj.copy()
        duplicate_obj2.data = active_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        duplicate_obj2.name = name + "WaxForShow"
        bpy.context.collection.objects.link(duplicate_obj2)
        duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_blue_l"))
        moveToLeft(duplicate_obj2)
        duplicate_obj2.hide_set(True)

        # bpy.context.scene.transparent2L = False
        # bpy.context.scene.transparent3L = True
        collections = bpy.data.collections['Left']

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
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LabelPlaneForCasting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳软耳膜附件Casting'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

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

    # 从切割模具模块回来，根据切割后的结果重新复制出一份用于对比的物体
    # compare_name = name + 'DamoCompare'
    # if name == "右耳":
    #     thickness = bpy.context.scene.laHouDUR
    # elif name == "左耳":
    #     thickness = bpy.context.scene.laHouDUL
    # active_obj = bpy.data.objects.get(name)
    # is_compare_obj = bpy.data.objects.get(compare_name)
    # if is_compare_obj != None:
    #     bpy.data.objects.remove(bpy.data.objects.get(compare_name), do_unlink=True)
    #     duplicate_obj = active_obj.copy()
    #     duplicate_obj.data = active_obj.data.copy()
    #     duplicate_obj.name = compare_name
    #     duplicate_obj.animation_data_clear()
    #     # 将复制的物体加入到场景集合中
    #     scene = bpy.context.scene
    #     scene.collection.objects.link(duplicate_obj)
    #     moveToRight(duplicate_obj)
    #     duplicate_obj.hide_set(True)
    #
    #     if thickness != 0:
    #         mesh = duplicate_obj.data
    #         for idx, vert in enumerate(mesh.vertices):
    #             vert.co = vert.co - mesh.vertices[idx].normal.normalized() * thickness

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


def color_vertex_by_thickness():
    active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)

    float_vector_layer_vertex_origin = bm.verts.layers.float_vector['OriginVertex']
    float_vector_layer_normal_origin = bm.verts.layers.float_vector['OriginNormal']
    color_lay = bm.verts.layers.float_color["Color"]
    for v in bm.verts:
        colvert = v[color_lay]
        distance_vector = v[float_vector_layer_vertex_origin] - v.co
        thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
        origin_vertex_normal = v[float_vector_layer_normal_origin]
        flag = origin_vertex_normal.dot(distance_vector)  # 判断当前顶点是否在原模型的内部
        if flag > 0:
            thickness *= -1

    # 原始数据
    # ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
    # ori_me = ori_obj.data
    # ori_bm = bmesh.new()
    # ori_bm.from_mesh(ori_me)
    # # 遍历顶点，根据厚度设置颜色
    # color_lay = bm.verts.layers.float_color["Color"]
    # bm.verts.ensure_lookup_table()
    # ori_bm.verts.ensure_lookup_table()
    # for vert in bm.verts:
    #     colvert = vert[color_lay]
    #     index = vert.index
    #     distance_vector = ori_bm.verts[index].co - bm.verts[index].co
    #     thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
    #     origin_vertex_normal = ori_bm.verts[index].normal
    #     flag = origin_vertex_normal.dot(distance_vector)   # 判断当前顶点是否在原模型的内部
    #     if flag > 0:
    #         thickness *= -1

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


def color_vertex_and_record_thickness(vertex_set):
    global vertex_changesR, vertex_changesL

    track_time("顶点上色")

    active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
    if bpy.context.scene.leftWindowObj == '右耳':
        localLaHouDu_cur = bpy.context.scene.localLaHouDuR
        maxHoudu_cur = bpy.context.scene.maxLaHouDuR + bpy.context.scene.laHouDUR
        minLaHouDu_cur = bpy.context.scene.minLaHouDuR + bpy.context.scene.laHouDUR
    elif bpy.context.scene.leftWindowObj == '左耳':
        localLaHouDu_cur = bpy.context.scene.localLaHouDuL
        maxHoudu_cur = bpy.context.scene.maxLaHouDuL + bpy.context.scene.laHouDUL
        minLaHouDu_cur = bpy.context.scene.minLaHouDuL + bpy.context.scene.laHouDUL
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    # 原始数据
    # ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
    # ori_me = ori_obj.data
    # ori_bm = bmesh.new()
    # ori_bm.from_mesh(ori_me)
    # 遍历顶点，根据厚度设置颜色
    color_lay = bm.verts.layers.float_color["Color"]
    float_vector_layer_vertex_origin = bm.verts.layers.float_vector['OriginVertex']
    float_vector_layer_normal_origin = bm.verts.layers.float_vector['OriginNormal']
    bm.verts.ensure_lookup_table()
    # ori_bm.verts.ensure_lookup_table()
    vertex_set.clear()
    for vert in bm.verts:
        colvert = vert[color_lay]
        index = vert.index
        if bpy.context.scene.leftWindowObj == '右耳':
            # 如果在字典中，则检查坐标是否发生更改
            if vert.co != vertex_changesR[index]:
                # 如果坐标更改了，则将顶点索引存储到列表中
                vertex_set.add(index)
                # 更新更改字典中的坐标
                vertex_changesR[index] = vert.co.copy()
        elif bpy.context.scene.leftWindowObj == '左耳':
            # 如果在字典中，则检查坐标是否发生更改
            if vert.co != vertex_changesL[index]:
                # 如果坐标更改了，则将顶点索引存储到列表中
                vertex_set.add(index)
                # 更新更改字典中的坐标
                vertex_changesL[index] = vert.co.copy()
        distance_vector = vert[float_vector_layer_vertex_origin] - bm.verts[index].co
        thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
        origin_vertex_normal = vert[float_vector_layer_normal_origin]
        flag = origin_vertex_normal.dot(distance_vector)  # 判断当前顶点是否在原模型的内部
        if flag > 0:
            thickness *= -1

        # 厚度限制
        if localLaHouDu_cur:
            maxHoudu = maxHoudu_cur
            minHoudu = minLaHouDu_cur
            if (thickness > maxHoudu or thickness < minHoudu) and (index in vertex_set):
                # 理论厚度
                if thickness > maxHoudu:
                    length = maxHoudu
                elif thickness < minHoudu:
                    length = minHoudu
                # 根据理论厚度修改坐标
                if length > 0:
                    bm.verts[index].co = vert[float_vector_layer_vertex_origin] - \
                                               distance_vector.normalized() * length
                else:
                    bm.verts[index].co = vert[float_vector_layer_vertex_origin] + \
                                               distance_vector.normalized() * length
                distance_vector = vert[float_vector_layer_vertex_origin] - bm.verts[index].co
                thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
                origin_vertex_normal = vert[float_vector_layer_normal_origin]
                flag = origin_vertex_normal.dot(distance_vector)  # 判断当前顶点是否在原模型的内部
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

    track_time("顶点上色结束")
    reset_time_tracker()


def cal_thickness(context, event):
    active_obj = bpy.data.objects[context.scene.leftWindowObj]
    # 获取网格数据
    me = active_obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    # 原始数据
    # ori_obj = bpy.data.objects[active_obj.name + "DamoCompare"]
    # ori_me = ori_obj.data
    # ori_bm = bmesh.new()
    # ori_bm.from_mesh(ori_me)
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
                # ori_bm.faces.ensure_lookup_table()
                for v in bm.faces[fidx].verts:
                    vec = v.co - co
                    between = vec.dot(vec)
                    if between <= min:
                        min = between
                        index = v.index
                bm.verts.ensure_lookup_table()
                float_vector_layer_vertex_origin = bm.verts.layers.float_vector['OriginVertex']
                float_vector_layer_normal_origin = bm.verts.layers.float_vector['OriginNormal']
                # ori_bm.verts.ensure_lookup_table()
                min_distance_vert = bm.verts[index]
                distance_vector = min_distance_vert[float_vector_layer_vertex_origin] - min_distance_vert.co
                thickness = round(math.sqrt(distance_vector.dot(distance_vector)), 2)
                origin_vertex_normal = min_distance_vert[float_vector_layer_normal_origin]
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
class Thickening(bpy.types.Operator):
    bl_idname = "object.thickening"
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
    __over_thickness_vertex = set()
    __check_flag = False

    # #打磨模块下左侧的三个按钮才起作用
    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        op_cls = Thickening
        # print("thicking_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "ADD"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = context.scene.leftWindowObj
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_R
            # 将其添加到字典中，并记录初始坐标
            global vertex_changesR
            vertex_changesR.clear()
            for vert in bpy.data.objects[context.scene.leftWindowObj].data.vertices:
                vertex_changesR[vert.index] = vert.co.copy()
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_L
            global vertex_changesL
            vertex_changesL.clear()
            for vert in bpy.data.objects[context.scene.leftWindowObj].data.vertices:
                vertex_changesL[vert.index] = vert.co.copy()

        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
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
        op_cls.__initial_radius = None
        op_cls.__select_mode = True
        op_cls.__brush_mode = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.2, window=context.window)

        bpy.context.scene.var = 1
        global thickening_modal_start
        if not thickening_modal_start:
            thickening_modal_start = True
            print("打厚modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Thickening
        global vertex_changesR
        global vertex_changesL
        global thickening_modal_start

        if context.area:
            context.area.tag_redraw()

        if get_mirror_context():
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print("打厚modal结束")
            thickening_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        if bpy.context.scene.var == 1:
            if event.type == 'FOUR':
                if event.value == 'RELEASE':
                    bpy.ops.object.thinning('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            if event.type == 'FIVE':
                if event.value == 'RELEASE':
                    bpy.ops.object.smooth('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}

            if is_mouse_on_object(context, event):
                if event.type == 'TIMER':
                    if op_cls.__left_mouse_down and bpy.context.mode == 'SCULPT':
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        if not op_cls.__check_flag:
                            op_cls.__check_flag = True
                        color_vertex_and_record_thickness(op_cls.__over_thickness_vertex)

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
                        record_state()
                        if op_cls.__brush_mode:
                            if op_cls.__check_flag:
                                op_cls.__check_flag = False
                                color_vertex_and_record_thickness(op_cls.__over_thickness_vertex)
                                op_cls.__over_thickness_vertex.clear()
                        elif op_cls.__select_mode:
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
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        # 上移扩大，下移缩小
                        op = 1
                        if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                            op = -1
                        # 设置圆环大小范围【25，200】
                        radius = max(op_cls.__initial_radius + dis * op, 25)
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
                        record_state()
                        if op_cls.__brush_mode:
                            if op_cls.__check_flag:
                                op_cls.__check_flag = False
                                color_vertex_and_record_thickness(op_cls.__over_thickness_vertex)
                                op_cls.__over_thickness_vertex.clear()

                    if not op_cls.__select_mode:
                        op_cls.__select_mode = True
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        recolor_vertex()
            return {'PASS_THROUGH'}

        else:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print("打厚modal结束")
            thickening_modal_start = False
            return {'FINISHED'}


# 打磨功能模块左侧按钮的减薄操作
class Thinning(bpy.types.Operator):
    bl_idname = "object.thinning"
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
    __over_thickness_vertex = set()
    __check_flag = False

    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

    def invoke(self, context, event):
        op_cls = Thinning
        # print("thinning_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction = "SUBTRACT"
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500
        # 设置圆环初始大小
        name = context.scene.leftWindowObj
        if name == '右耳':
            radius = context.scene.damo_circleRadius_R
            strength = context.scene.damo_strength_R
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_R
            # 将其添加到字典中，并记录初始坐标
            global vertex_changesR
            vertex_changesR.clear()
            for vert in bpy.data.objects[context.scene.leftWindowObj].data.vertices:
                vertex_changesR[vert.index] = vert.co.copy()
        else:
            radius = context.scene.damo_circleRadius_L
            strength = context.scene.damo_strength_L
            bpy.data.brushes["SculptDraw"].strength = strength * context.scene.damo_scale_strength_L
            global vertex_changesL
            vertex_changesL.clear()
            for vert in bpy.data.objects[context.scene.leftWindowObj].data.vertices:
                vertex_changesL[vert.index] = vert.co.copy()

        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
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
        op_cls.__select_mode =  True
        op_cls.__brush_mode = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.1, window=context.window)

        bpy.context.scene.var = 2
        global thinning_modal_start
        if not thinning_modal_start:
            thinning_modal_start = True
            print("打薄modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Thinning
        global vertex_changesR
        global vertex_changesL
        global thinning_modal_start

        if context.area:
            context.area.tag_redraw()

        if get_mirror_context():
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print("打薄modal结束")
            thinning_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        if bpy.context.scene.var == 2:
            if event.type == 'THREE':
                if event.value == 'RELEASE':
                    bpy.ops.object.thickening('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            if event.type == 'FIVE':
                if event.value == 'RELEASE':
                    bpy.ops.object.smooth('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}

            if is_mouse_on_object(context, event):
                if event.type == 'TIMER':
                    if op_cls.__left_mouse_down and bpy.context.mode == 'SCULPT':
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        if not op_cls.__check_flag:
                            op_cls.__check_flag = True
                        color_vertex_and_record_thickness(op_cls.__over_thickness_vertex)

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
                        record_state()
                        if op_cls.__brush_mode:
                            if op_cls.__check_flag:
                                op_cls.__check_flag = False
                                color_vertex_and_record_thickness(op_cls.__over_thickness_vertex)
                                op_cls.__over_thickness_vertex.clear()
                        elif op_cls.__select_mode:
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
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        # 上移扩大，下移缩小
                        op = 1
                        if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                            op = -1
                        # 设置圆环大小范围【25，200】
                        radius = max(op_cls.__initial_radius + dis * op, 25)
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
                        record_state()
                        if op_cls.__brush_mode:
                            if op_cls.__check_flag:
                                op_cls.__check_flag = False
                                color_vertex_and_record_thickness(op_cls.__over_thickness_vertex)
                                op_cls.__over_thickness_vertex.clear()

                    if not op_cls.__select_mode:
                        op_cls.__select_mode = True
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        recolor_vertex()
            return {'PASS_THROUGH'}

        else:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print("打薄modal结束")
            thinning_modal_start = False
            return {'FINISHED'}


# 打磨功能模块左侧按钮的光滑操作
class Smooth(bpy.types.Operator):
    bl_idname = "object.smooth"
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
        op_cls = Smooth
        # print("smooth_invoke")
        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
        bpy.data.brushes["Smooth"].direction = 'SMOOTH'
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为500

        # 设置圆环初始大小
        name = context.scene.leftWindowObj
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
        op_cls.__select_mode = True
        op_cls.__brush_mode = False
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        if not op_cls.__timer:
            op_cls.__timer = context.window_manager.event_timer_add(0.1, window=context.window)

        bpy.context.scene.var = 3
        global smooth_modal_start
        if not smooth_modal_start:
            smooth_modal_start = True
            print("平滑modal")
            context.window_manager.modal_handler_add(self)  # 进入modal模式

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Smooth
        global smooth_modal_start

        if context.area:
            context.area.tag_redraw()

        if get_mirror_context():
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print("平滑modal结束")
            smooth_modal_start = False
            set_mirror_context(False)
            return {'FINISHED'}

        if bpy.context.scene.var == 3:
            if event.type == 'THREE':
                if event.value == 'RELEASE':
                    bpy.ops.object.thickening('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            if event.type == 'FOUR':
                if event.value == 'RELEASE':
                    bpy.ops.object.thinning('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
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
                        record_state()
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
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        # 上移扩大，下移缩小
                        op = 1
                        if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                            op = -1
                        # 设置圆环大小范围【25，200】
                        radius = max(op_cls.__initial_radius + dis * op, 25)
                        if radius > 200:
                            radius = 200
                        bpy.context.scene.tool_settings.unified_paint_settings.size = radius
                        if context.scene.leftWindowObj == '右耳':
                            bpy.data.brushes[
                                "Smooth"].strength = 25 / radius * context.scene.damo_scale_strength_R
                        else:
                            bpy.data.brushes[
                                "Smooth"].strength = 25 / radius * context.scene.damo_scale_strength_L
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
                        record_state()
                    if not op_cls.__select_mode:
                        op_cls.__select_mode = True
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        if MyHandleClass._handler:
                            MyHandleClass.remove_handler()
                        recolor_vertex()
            return {'PASS_THROUGH'}

        else:
            if op_cls.__timer:
                context.window_manager.event_timer_remove(op_cls.__timer)
                op_cls.__timer = None
            print("平滑modal结束")
            smooth_modal_start = False
            return {'FINISHED'}


class Damo_Reset(bpy.types.Operator):
    bl_idname = "object.damo_reset"
    bl_label = "重置操作"
    bl_description = "点击按钮恢复到原来的模型"

    def invoke(self, context, event):
        print("reset invoke")
        self.execute(context)
        record_state()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        bpy.context.scene.var = 4
        name = context.scene.leftWindowObj
        active_obj = bpy.data.objects[context.scene.leftWindowObj]
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

        # compare_name = name + "DamoCompare"
        # ori_name = name + "OriginForShow"
        # if bpy.data.objects.get(ori_name):
        #     ori_obj = bpy.data.objects[ori_name]
        #     # 先根据重置的物体复制出一份新的物体
        #     duplicate_obj = ori_obj.copy()
        #     duplicate_obj.data = ori_obj.data.copy()
        #     duplicate_obj.name = ori_name + "copy"
        #     duplicate_obj.animation_data_clear()
        #     # 将复制的物体加入到场景集合中
        #     scene = bpy.context.scene
        #     scene.collection.objects.link(duplicate_obj)
        #     if name == '右耳':
        #         moveToRight(duplicate_obj)
        #     elif name == '左耳':
        #         moveToLeft(duplicate_obj)
        #     duplicate_obj.hide_set(True)
        #
        #     # 替换原有的物体
        #     bpy.data.objects.remove(bpy.data.objects[compare_name], do_unlink=True)
        #     duplicate_obj.name = compare_name

        bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.leftWindowObj]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[context.scene.leftWindowObj].select_set(True)


class DamoOperator(bpy.types.Operator):
    bl_idname = "object.damo_operator"
    bl_label = "3D Model"

    my_string: bpy.props.StringProperty(name="", default="可能会丢失数据")
    my_bool: bpy.props.BoolProperty(name="确认")

    def execute(self, context):
        global is_dialog
        global previous_thicknessR
        global previous_thicknessL
        active_object = bpy.data.objects[context.scene.leftWindowObj]
        if context.scene.leftWindowObj == '右耳':
            thickness = context.scene.laHouDUR
        elif context.scene.leftWindowObj == '左耳':
            thickness = context.scene.laHouDUL
        # 确认
        if self.my_bool:
            # 根据最原始的物体加蜡
            ori_obj = bpy.data.objects[context.scene.leftWindowObj + 'OriginForShow']
            reset_obj = bpy.data.objects[context.scene.leftWindowObj + 'DamoReset']
            me = active_object.data
            reset_me = reset_obj.data

            ori_me = ori_obj.data
            ori_bm = bmesh.new()
            ori_bm.from_mesh(ori_me)
            ori_bm.verts.ensure_lookup_table()

            for vert in ori_bm.verts:
                vert.co = ori_bm.verts[vert.index].co + ori_bm.verts[vert.index].normal.normalized() * thickness

            ori_bm.to_mesh(me)
            ori_bm.to_mesh(reset_me)
            ori_bm.free()
            record_state()

        else:
            if context.scene.leftWindowObj == '右耳':
                is_dialog = True
                context.scene.laHouDUR = previous_thicknessR
                is_dialog = False
            elif context.scene.leftWindowObj == '左耳':
                is_dialog = True
                context.scene.laHouDUL = previous_thicknessL
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


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
