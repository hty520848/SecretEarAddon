import bpy
import bmesh
import re
import sys
import mathutils
from time import time as now
from .tool import *
from math import *
from datetime import *
from mathutils import Vector, kdtree
from bpy_extras import view3d_utils
from bpy.types import WorkSpaceTool
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running, \
    get_mirror_context, set_mirror_context, get_process_var_list
from .log_file import write_info

prev_on_object = False            # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体

# 主要用于加厚按钮中，第一次加厚初始化状态数组。局部加厚模块切换时的状态判断
is_copy_local_thickening = False  # 判断加厚状态，值为True时为未提交，值为False为提交后或重置后(未处于加厚预览状态)
is_copy_local_thickeningL = False

local_thickening_objects_array = []          # 保存局部加厚功能中每一步加厚时物体的状态的物体名称，用于单步撤回
local_thickening_objects_arrayL = []
objects_array_index = -1                     # 数组指针，指向数组中当前需要访问状态的元素，用于单步撤回操作,指向数组中与当前激活物体相同的对象
objects_array_indexL = -1

prev_localthick_area_index = []              # 保存上次局部加厚的顶点,主要用于判断选中的局部加厚区域是否改变,在增大或缩小区域后执行自动加厚
prev_localthick_area_indexL = []

switch_selected_vertex_index = []            # 用于保存当前模型的局部加厚区域,从其他模式切换到局部加厚模式时根据该区域初始化模型
switch_selected_vertex_indexL = []

operator_obj = ''                   # 当前操作的物体是左耳还是右耳

left_is_submit = False              # 保存左耳的submit状态，用于限制提交修改后的操作
right_is_submit = False             # 保存右耳的submit状态

continuous_area = None             #记录根据选中顶点进行区域划分后的内外边界信息,避免更新参数面板的时候重复获取造成卡顿
continuous_areaL = None

add_area_modal_start = False
reduce_area_modal_start = False
thicken_modal_start = False

# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]

    is_on_object = False  # 初始化变量

    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
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
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT" or active_obj.mode == "VERTEX_PAINT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


# 判断鼠标状态是否发生改变
def is_changed(context, event):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]

    curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
    global prev_on_object  # 之前鼠标是否在物体上

    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
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
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start
    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT" or active_obj.mode == "VERTEX_PAINT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
            if fidx is not None:
                curr_on_object = True  # 如果发生交叉，将变量设为True
    if (curr_on_object != prev_on_object):
        prev_on_object = curr_on_object
        return True
    else:
        return False


def initialModelColor():
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        # mat = newShader("YellowR")
        mat = bpy.data.materials.get("YellowR")
    elif name == '左耳':
        # mat = newShader("YellowL")
        mat = bpy.data.materials.get("YellowL")
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def initialTransparency():
    mat = newShader("Transparency")
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.data.materials['Transparency'].blend_method = "BLEND"
    bpy.data.materials["Transparency"].node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2


# 前面的打磨功能切换到 局部加厚模式时
def frontToLocalThickening():
    global switch_selected_vertex_index
    global switch_selected_vertex_indexL
    global objects_array_index
    global objects_array_indexL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global is_copy_local_thickening
    global is_copy_local_thickeningL
    global left_is_submit,right_is_submit
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickening == True):
            size = len(local_thickening_objects_array)
            objects_array_index = size - 1
        else:
            objects_array_index = -1
    elif (name == "左耳"):
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickeningL == True):
            size = len(local_thickening_objects_arrayL)
            objects_array_indexL = size - 1
        else:
            objects_array_indexL = -1

    #进入该模块的时候,将左/右耳设置为当前激活物体
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


    # 若存在LocalThickCopy和LocalThickCompare,则将其删除并重新生成
    all_objs = bpy.data.objects
    active_obj = bpy.data.objects[name]
    for selected_obj in all_objs:
        if (selected_obj.name == name+"LocalThickCopy" or selected_obj.name == name+"LocalThickCompare"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    # 获取新的LocalThickCompare物体
    size_cur = None
    local_thickening_objects_array_cur = None
    if (name == "右耳"):
        size_cur = len(local_thickening_objects_array)
        local_thickening_objects_array_cur = local_thickening_objects_array
    elif (name == "左耳"):
        size_cur = len(local_thickening_objects_arrayL)
        local_thickening_objects_array_cur = local_thickening_objects_arrayL
    if(size_cur > 0):
        # 根据数组中报错的状态数组名称复制得到用于重置的LocalThickCompare
        local_thickening_object = bpy.data.objects.get(local_thickening_objects_array_cur[size_cur - 1])
        if(local_thickening_object != None):
            duplicate_obj1 = local_thickening_object.copy()
            duplicate_obj1.data = local_thickening_object.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj1)
            if name=='右耳':
                moveToRight(duplicate_obj1)
            elif name=='左耳':
                moveToLeft(duplicate_obj1)
            duplicate_obj1.hide_set(True)
            duplicate_obj1.hide_set(False)
    else:
        # 根据当前激活物体复制得到用于重置的LocalThickCompare
        duplicate_obj1 = active_obj.copy()
        duplicate_obj1.data = active_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = name + "LocalThickCompare"
        bpy.context.collection.objects.link(duplicate_obj1)
        if name=='右耳':
            moveToRight(duplicate_obj1)
        elif name=='左耳':
            moveToLeft(duplicate_obj1)
        duplicate_obj1.hide_set(True)
        duplicate_obj1.hide_set(False)
    # 根据当前激活物体复制得到用于重置的LocalThickCopy
    duplicate_obj2 = active_obj.copy()
    duplicate_obj2.data = active_obj.data.copy()
    duplicate_obj2.animation_data_clear()
    duplicate_obj2.name = name + "LocalThickCopy"
    bpy.context.collection.objects.link(duplicate_obj2)
    if name=='右耳':
        moveToRight(duplicate_obj2)
    elif name=='左耳':
        moveToLeft(duplicate_obj2)
    duplicate_obj2.hide_set(True)  # 将LocalThickCopy隐藏
    active_obj = bpy.data.objects[name]  # 将右耳设置为当前激活物体
    bpy.context.view_layer.objects.active = active_obj

    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        # 根据switch_selected_vertex中保存的模型上的已选中顶点,将其置为局部加厚中已选中顶点并根据offset和borderWidth进行加厚,进行初始化处理
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert_index in switch_selected_vertex_index:
                colvert = bm.verts[vert_index][color_lay]
                colvert.x = 0.133
                colvert.y = 1.000
                colvert.z = 1.000
            bm.to_mesh(me)
            bm.free()

        if (len(switch_selected_vertex_index) != 0):
            # 对选中区域自动进行加厚处理,会根据LocalThickCopy先重置打回,再根据offset和borderWidth进行加厚
            auto_thickening()
    elif (name == "左耳"):
        # 根据switch_selected_vertex中保存的模型上的已选中顶点,将其置为局部加厚中已选中顶点并根据offset和borderWidth进行加厚,进行初始化处理
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert_index in switch_selected_vertex_indexL:
                colvert = bm.verts[vert_index][color_lay]
                colvert.x = 0.133
                colvert.y = 1.000
                colvert.z = 1.000
            bm.to_mesh(me)
            bm.free()

        if (len(switch_selected_vertex_indexL) != 0):
            # 对选中区域自动进行加厚处理,会根据LocalThickCopy先重置打回,再根据offset和borderWidth进行加厚
            auto_thickening()

    
    # 重置提交状态
    if name == '左耳':
        left_is_submit = False
    else:
        right_is_submit = False

    # 将当前模块操作的激活物体变透明
    initialTransparency()


def frontFromLocalThickening():
    # 保存模型上选中的局部加厚区域中的顶点索引,同样保存模型上已选中点放在submit功能模块中
    global left_is_submit
    global right_is_submit
    global switch_selected_vertex_index
    global switch_selected_vertex_indexL
    global is_copy_local_thickening
    global is_copy_local_thickeningL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global objects_array_index
    global objects_array_indexL
    #将模型上的顶点取消选中
    # 将选中顶点取消选中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 未提交时,保存局部加厚区域中顶点索引。若已提交,则submit按钮中已经保存该顶点索引,无序置空在重新确定顶点索引
    name = bpy.context.scene.leftWindowObj
    submit = None
    if name == '左耳':
        #重置状态数组指针
        size = len(local_thickening_objects_arrayL)
        objects_array_indexL = size - 1
        submit = left_is_submit
        if (submit == False):
            switch_selected_vertex_indexL = []
            active_obj = bpy.data.objects[name]
            if active_obj.type == 'MESH':
                me = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                        switch_selected_vertex_indexL.append(vert.index)
                bm.to_mesh(me)
                bm.free()
    else:
        # 重置状态数组指针
        size = len(local_thickening_objects_array)
        objects_array_index = size - 1
        submit = right_is_submit
        if (submit == False):
            switch_selected_vertex_index = []
            active_obj = bpy.data.objects[name]
            if active_obj.type == 'MESH':
                me = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                        switch_selected_vertex_index.append(vert.index)
                bm.to_mesh(me)
                bm.free()

    # 根据LocalThickCopy复制出一份物体并替换为当前激活物体
    active_obj = bpy.data.objects[name]  # 将当前激活的模型替换为执行加厚操作之前的模型
    copyname = name + "LocalThickCopy"
    ori_obj = bpy.data.objects[copyname]
    bpy.data.objects.remove(active_obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name=='右耳':
        moveToRight(duplicate_obj)
    elif name=='左耳':
        moveToLeft(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj

    # 删除场景中局部加厚相关的用于重置的LocalThickCopy和初始时的参照物LocalThickCompare
    selected_objs = bpy.data.objects
    active_object = bpy.data.objects[name]
    name = active_object.name
    for selected_obj in selected_objs:
        if (selected_obj.name == name + "LocalThickCompare" or selected_obj.name == name + "LocalThickCopy"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 删除局部加厚中的圆环
    border_obj = bpy.data.objects.get(name + "LocalThickAreaClassificationBorder")
    if (border_obj != None):
        bpy.data.objects.remove(border_obj, do_unlink=True)

    #若未做任何操作,将初始化变为透明的物体变为不透明的实体
    initialModelColor()

    if bpy.context.mode == 'PAINT_VERTEX':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

# 后面的其他功能切换到局部加厚模式时
def backToLocalThickening():
    global switch_selected_vertex_index
    global switch_selected_vertex_indexL
    global objects_array_index
    global objects_array_indexL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global is_copy_local_thickening
    global is_copy_local_thickeningL

    # 进入该模块的时候,将左/右耳设置为当前激活物体
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

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

    name = bpy.context.scene.leftWindowObj
    switch_selected_vertex_index_cur = None
    if (name == "右耳"):
        switch_selected_vertex_index_cur = switch_selected_vertex_index
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickening == True):
            size = len(local_thickening_objects_array)
            objects_array_index = size - 1
        else:
            objects_array_index = -1
    elif (name == "左耳"):
        switch_selected_vertex_index_cur = switch_selected_vertex_indexL
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickeningL == True):
            size = len(local_thickening_objects_arrayL)
            objects_array_indexL = size - 1
        else:
            objects_array_indexL = -1


    exist_LocalThickCopy = False

    # 判断场景中是否存在LocalThickCopy,若存在则利用该模型生成LocalThickCompare并根据LocalThickCopy进行加厚
    # 若场景中不存在LocalThickCopy,则说明未经过局部加厚操作,获取打磨模块中的DamoCopy并生成LocalThickCopy,Compare和激活物体
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name+"LocalThickCopy"):
            exist_LocalThickCopy = True
    if (exist_LocalThickCopy):
        # 根据LocalThickCopy复制出来一份物体用来替换当前激活物体
        active_obj = bpy.data.objects[name]
        copyname = name + "LocalThickCopy"
        ori_obj = bpy.data.objects[copyname]
        bpy.data.objects.remove(active_obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if name=='右耳':
            moveToRight(duplicate_obj)
        elif name=='左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        # 获取新的LocalThickCompare物体
        size_cur = None
        local_thickening_objects_array_cur = None
        if (name == "右耳"):
            size_cur = len(local_thickening_objects_array)
            local_thickening_objects_array_cur = local_thickening_objects_array
        elif (name == "左耳"):
            size_cur = len(local_thickening_objects_arrayL)
            local_thickening_objects_array_cur = local_thickening_objects_arrayL
        if (size_cur > 0):
            # 根据数组中报错的状态数组名称复制得到用于重置的LocalThickCompare
            local_thickening_object = bpy.data.objects.get(local_thickening_objects_array_cur[size_cur - 1])
            if (local_thickening_object != None):
                duplicate_obj1 = local_thickening_object.copy()
                duplicate_obj1.data = local_thickening_object.data.copy()
                duplicate_obj1.animation_data_clear()
                duplicate_obj1.name = name + "LocalThickCompare"
                bpy.context.collection.objects.link(duplicate_obj1)
                if name == '右耳':
                    moveToRight(duplicate_obj1)
                elif name == '左耳':
                    moveToLeft(duplicate_obj1)
                duplicate_obj1.hide_set(True)
                duplicate_obj1.hide_set(False)
        else:
            # 根据当前激活物体复制得到用于重置的LocalThickCompare
            duplicate_obj1 = ori_obj.copy()
            duplicate_obj1.data = ori_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj1)
            if name == '右耳':
                moveToRight(duplicate_obj1)
            elif name == '左耳':
                moveToLeft(duplicate_obj1)
            duplicate_obj1.hide_set(True)
            duplicate_obj1.hide_set(False)

        # 根据switch_selected_vertex中保存的模型上的已选中顶点,将其置为局部加厚中已选中顶点并根据offset和borderWidth进行加厚,进行初始化处理
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert_index in switch_selected_vertex_index_cur:
                colvert = bm.verts[vert_index][color_lay]
                colvert.x = 0.133
                colvert.y = 1.000
                colvert.z = 1.000
            bm.to_mesh(me)
            bm.free()
        if (len(switch_selected_vertex_index_cur) != 0):
            # 对选中区域自动进行加厚处理,会根据LocalThickCopy先重置打回,再根据offset和borderWidth进行加厚
            auto_thickening()
    else:
        active_obj = bpy.data.objects[name]
        copyname = name + "DamoCopy"
        ori_obj = bpy.data.objects[copyname]
        # 根据DamoCopy生成LocalThickCopy
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "LocalThickCopy"
        bpy.context.scene.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)  # 将LocalThickCopy隐藏
        # 根据DamoCopy生成LocalThickCompare
        duplicate_obj1 = ori_obj.copy()
        duplicate_obj1.data = ori_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = name + "LocalThickCompare"
        bpy.context.scene.collection.objects.link(duplicate_obj1)
        if name=='右耳':
            moveToRight(duplicate_obj1)
        elif name=='左耳':
            moveToLeft(duplicate_obj1)
        # 删除当前激活物体并根据DamoCopy重新生成当前激活物体
        bpy.data.objects.remove(active_obj, do_unlink=True)
        duplicate_obj2 = ori_obj.copy()
        duplicate_obj2.data = ori_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate_obj2)
        if name=='右耳':
            moveToRight(duplicate_obj2)
        elif name=='左耳':
            moveToLeft(duplicate_obj2)
        duplicate_obj2.name = name
        bpy.context.view_layer.objects.active = duplicate_obj2

    #将当前模块操作的激活物体变透明
    initialTransparency()


# 从当前的局部加厚切换到后面的其他功能时
def backFromLocalThickening():
    # 保存模型上选中的局部加厚区域中的顶点索引,同样保存模型上已选中点放在submit功能模块中
    global left_is_submit
    global right_is_submit
    global switch_selected_vertex_index
    global switch_selected_vertex_indexL
    global is_copy_local_thickening
    global is_copy_local_thickeningL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global objects_array_index
    global objects_array_indexL
    # 将选中顶点取消选中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 未提交时,保存局部加厚区域中顶点索引。若已提交,则submit按钮中已经保存该顶点索引,无序置空在重新确定顶点索引
    name = bpy.context.scene.leftWindowObj
    if name == '左耳':
        submit = left_is_submit
        # 重置状态数组指针
        size = len(local_thickening_objects_arrayL)
        objects_array_indexL = size - 1
    else:
        submit = right_is_submit
        # 重置状态数组指针
        size = len(local_thickening_objects_array)
        objects_array_index = size - 1
    if (submit == False):
        if (name == "右耳"):
            switch_selected_vertex_index = []
            active_obj = bpy.data.objects[name]
            if active_obj.type == 'MESH':
                me = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                        switch_selected_vertex_index.append(vert.index)
                bm.to_mesh(me)
                bm.free()
        elif (name == "左耳"):
            switch_selected_vertex_indexL = []
            active_obj = bpy.data.objects[name]
            if active_obj.type == 'MESH':
                me = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                        switch_selected_vertex_indexL.append(vert.index)
                bm.to_mesh(me)
                bm.free()


    # 将当前模型的预览提交
    utils_re_color(name, (1, 0.319, 0.133))
    # bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    # bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    # bpy.ops.paint.vertex_color_set()
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #删除局部加厚中的圆环
    border_obj = bpy.data.objects.get(name + "LocalThickAreaClassificationBorder")
    if (border_obj != None):
        bpy.data.objects.remove(border_obj, do_unlink=True)


    # 删除场景中局部加厚相关的初始时的参照物LocalThickCompare
    selected_objs = bpy.data.objects
    active_object = bpy.data.objects[name]
    name = active_object.name
    for selected_obj in selected_objs:
        if (selected_obj.name == name + "LocalThickCompare"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)



    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == name+"LocalThickLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LocalThickLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    if name=='右耳':
        moveToRight(duplicate_obj1)
    elif name=='左耳':
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)


    # 若未做任何操作,将初始化变为透明的物体变为不透明的实体
    initialModelColor()
    #切换到后续模块的时候,颜色显示改为RGB
    # change_mat_mould(0)

    if bpy.context.mode == 'PAINT_VERTEX':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



def backup(context):
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global objects_array_index
    global objects_array_indexL
    name = bpy.context.scene.leftWindowObj
    objects_array_index_cur = None
    if (name == "右耳"):
        objects_array_index_cur = objects_array_index
    elif (name == "左耳"):
        objects_array_index_cur = objects_array_indexL
    if (objects_array_index_cur > 0):
        name = bpy.context.scene.leftWindowObj
        cur_obj = None
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            objects_array_index = objects_array_index - 1
            # 从状态数组中获取替换物体,再将作为对比的物体删除
            cur_obj = bpy.data.objects.get(local_thickening_objects_array[objects_array_index])
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            objects_array_indexL = objects_array_indexL - 1
            # 从状态数组中获取替换物体,再将作为对比的物体删除
            cur_obj = bpy.data.objects.get(local_thickening_objects_arrayL[objects_array_indexL])
        comparename = name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        bpy.data.objects.remove(compare_obj, do_unlink=True)
        # 将替换物体作为对比物体
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = comparename
        bpy.context.collection.objects.link(duplicate_obj)
        # 解决模型重叠问题
        comparename = name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        compare_obj.hide_set(True)
        compare_obj.hide_set(False)

        if name == '右耳':
            offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
            borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
        else:
            offset = bpy.context.scene.localThicking_offset_L  # 获取局部加厚面板中的偏移量参数
            borderWidth = bpy.context.scene.localThicking_borderWidth_L  # 获取局部加厚面板中的边界宽度参数
        # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
        auto_thickening()
        # thickening_reset()
        # thickening_offset_borderwidth(offset, borderWidth)
        # applySmooth()


def forward(context):
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global objects_array_index
    global objects_array_indexL
    name = bpy.context.scene.leftWindowObj
    objects_array_index_cur = None
    size = None
    if (name == "右耳"):
        objects_array_index_cur = objects_array_index
        size = len(local_thickening_objects_array)
    elif (name == "左耳"):
        objects_array_index_cur = objects_array_indexL
        size = len(local_thickening_objects_arrayL)
    if (objects_array_index_cur + 1 < size):
        name = bpy.context.scene.leftWindowObj
        cur_obj = None
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            objects_array_index = objects_array_index + 1
            # 从状态数组中获取替换物体,再将作为对比的物体删除
            cur_obj = bpy.data.objects.get(local_thickening_objects_array[objects_array_index])
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            objects_array_indexL = objects_array_indexL + 1
            # 从状态数组中获取替换物体,再将作为对比的物体删除
            cur_obj = bpy.data.objects.get(local_thickening_objects_arrayL[objects_array_indexL])
        comparename = name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        bpy.data.objects.remove(compare_obj, do_unlink=True)
        # 将替换物体作为对比物体
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = comparename
        bpy.context.collection.objects.link(duplicate_obj)
        # 解决模型重叠问题
        comparename = name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        compare_obj.hide_set(True)
        compare_obj.hide_set(False)

        if name == '右耳':
            offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
            borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
        else:
            offset = bpy.context.scene.localThicking_offset_L  # 获取局部加厚面板中的偏移量参数
            borderWidth = bpy.context.scene.localThicking_borderWidth_L  # 获取局部加厚面板中的边界宽度参数
        # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
        auto_thickening()
        # thickening_reset()
        # thickening_offset_borderwidth(offset, borderWidth)
        # applySmooth()



# 保存加厚顶点
def saveSelected():
    global switch_selected_vertex_index,switch_selected_vertex_indexL
    selected_vertex_index = []
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]
    if active_obj.type == 'MESH':
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                selected_vertex_index.append(vert.index)
        bm.to_mesh(me)
        bm.free()
    if name == '右耳':
        switch_selected_vertex_index = selected_vertex_index
    elif name == '左耳':
        switch_selected_vertex_indexL = selected_vertex_index



# 获取当前激活物体上局部加厚区域是否改变
def isSelectedAreaChanged():
    global prev_localthick_area_index
    global prev_localthick_area_indexL
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        flag = False
        selected_area_vertex_index = []
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            select_vert = []  # 被选择的顶点
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                    selected_area_vertex_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()
        if (len(selected_area_vertex_index) != len(prev_localthick_area_index)):
            flag = True
        prev_localthick_area_index.clear()
        prev_localthick_area_index = selected_area_vertex_index.copy()
        return flag
    elif name == '左耳':
        flag = False
        selected_area_vertex_index = []
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            select_vert = []  # 被选择的顶点
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                    selected_area_vertex_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()
        if (len(selected_area_vertex_index) != len(prev_localthick_area_indexL)):
            flag = True
        prev_localthick_area_indexL.clear()
        prev_localthick_area_indexL = selected_area_vertex_index.copy()
        return flag



def showThickness(context, event):
    # 鼠标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
    region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
    ray_dir = view3d_utils.region_2d_to_vector_3d(region, space.region_3d, mv)
    ray_orig = view3d_utils.region_2d_to_origin_3d(region, space.region_3d, mv)
    start = ray_orig
    end = ray_orig + ray_dir

    #  物体
    active_obj = context.active_object
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]  # 操作物体
    copyname = name + "LocalThickCopy"
    ori_obj = bpy.data.objects[copyname]  # 作为厚度对比的源物体
    orime = ori_obj.data
    oribm = bmesh.new()
    oribm.from_mesh(orime)
    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT" or active_obj.mode == "VERTEX_PAINT"):
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            # bm.transform(active_obj.matrix_world)
            # 构建BVH树
            outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
            # 进行对象和光线交叉判定
            co, _, fidx, dis = outertree.ray_cast(mwi_start, mwi_dir)
            # 网格和光线碰撞时   fidx代表鼠标射线与相交面的索引
            if fidx is not None:
                min = 666
                index = 0
                bm.faces.ensure_lookup_table()
                oribm.faces.ensure_lookup_table()
                bm.faces[fidx].material_index = 1
                for v in bm.faces[fidx].verts:
                    vec = v.co - co
                    between = vec.dot(vec)
                    if (between <= min):
                        min = between
                        index = v.index  # 通过fidx获取相交面,通过距离计算得出相交面中距离相交点位置co最近的点，获取该点索引index
                        bm.verts.ensure_lookup_table()
                        oribm.verts.ensure_lookup_table()
                        disvec = oribm.verts[index].co - \
                                 bm.verts[index].co
                        dis = disvec.dot(disvec)
                        final_dis = round(sqrt(dis), 2)
                        origin_vec = oribm.verts[index].normal
                        flag = origin_vec.dot(disvec)
                        if flag > 0:
                            final_dis *= -1
                        MyHandleClass.remove_handler()
                        MyHandleClass.add_handler(draw_callback_px, (None, final_dis))



def auto_thickening():
    '''
        调用增大或缩小区域按钮重新选择顶点后,根据面板参数调用该函数自动对选中区域进行加厚
    '''
    global right_is_submit,left_is_submit
    global continuous_area,continuous_areaL
    name = bpy.context.scene.leftWindowObj
    if name == '左耳':
        left_is_submit = False
    else:
        right_is_submit = False

    if name == '右耳':
        offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
        borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
    else:
        offset = bpy.context.scene.localThicking_offset_L  # 获取局部加厚面板中的偏移量参数
        borderWidth = bpy.context.scene.localThicking_borderWidth_L  # 获取局部加厚面板中的边界宽度参数

    #更新区域划分的全局变量
    if (borderWidth == 0):
        borderWidth = 0.01
    select_vert_index = []  # 被选择的顶点
    active_obj = bpy.data.objects[name]
    if active_obj.type == 'MESH':
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                select_vert_index.append(vert.index)
        bm.to_mesh(me)
        bm.free()
    continuousArea = get_continuous_area(select_vert_index, borderWidth)
    if name == '右耳':
        continuous_area = continuousArea
    elif name == '左耳':
        continuous_areaL = continuousArea

    # 重新根据offset和borderwidth对模型进行加厚
    thickening_reset()
    initialTransparency()
    thickening_offset_borderwidth(offset, borderWidth)
    applySmooth()
    draw_border_curve(select_vert_index)


def thickening_reset():
    '''
    在不改变选中的局部加厚顶点颜色的情况下,将之前加厚的区域重置为未加厚的高度
    '''
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]
    if active_obj.type == 'MESH':
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        # 获取厚度对比物体的网格激活物体
        copyname = name + "LocalThickCompare"
        ori_obj = bpy.data.objects[copyname]
        ori_me = ori_obj.data
        ori_bm = bmesh.new()
        ori_bm.from_mesh(ori_me)
        ori_bm.verts.ensure_lookup_table()

        for vert in bm.verts:
            vert.co = ori_bm.verts[vert.index].co

        bm.to_mesh(me)
        bm.free()
        ori_bm.free()


#将选中的局部加厚区域应用拉普拉斯平滑函数,优化加厚效果
def applySmooth():
    global continuous_area
    global continuous_areaL
    name = bpy.context.scene.leftWindowObj
    continuous_area_cur = None
    borderWidth = None
    if name == '右耳':
        continuous_area_cur = continuous_area
        borderWidth = bpy.context.scene.localThicking_borderWidth
    elif name == '左耳':
        continuous_area_cur = continuous_areaL
        borderWidth = bpy.context.scene.localThicking_borderWidth_L
    # 获取需要进行操作的选中区域的顶点划分列表
    if (continuous_area_cur != None):
        # 执行加厚操作
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            # 依次处理每个连续区域,根据原区域的最高点与offset参数和borderWidth参数进行加厚
            area_index = 0
            while (area_index < len(continuous_area_cur)):
                select_area = continuous_area_cur[area_index]

                smooth_inner_vert = []          #该连通区域的内部平滑顶点
                smooth_outer_vert = []          #该连通区域的外部平滑顶点

                #划分该连通区域的内外边界顶点
                for vert_index in select_area.vert_index:
                    vert = bm.verts[vert_index]
                    dis = select_area.distance_dic[vert.index]
                    if (dis < borderWidth):
                        smooth_outer_vert.append(vert)
                    else:
                        smooth_inner_vert.append(vert)

                #扩大外圈区域的平滑范围
                add_smooth_outer_vert = []
                for i in range(1):                             # 将选中区域扩大一圈
                    for vert in smooth_outer_vert:
                        for edge in vert.link_edges:
                            v1 = edge.verts[0]
                            v2 = edge.verts[1]
                            link_vert = v1 if v1 != vert else v2
                            if not (link_vert in smooth_outer_vert):
                                add_smooth_outer_vert.append(link_vert)
                    for vert in add_smooth_outer_vert:         # 根据扩大区域重置选择区域
                        if not (vert in smooth_outer_vert):
                            smooth_outer_vert.append(vert)
                #去除扩大外圈范围过程中选中的内圈顶点
                # smooth_outer_vert = [vert for vert in smooth_outer_vert if vert not in smooth_inner_vert]


                #该连通区域的外圈顶点平滑
                for _ in range(5):
                    # Create a list to store new vertex positions
                    new_positions = [None] * len(bm.verts)

                    # Compute new vertex positions based on the Laplacian operator
                    for v in smooth_outer_vert:
                        if not v.is_boundary:
                            avg_neighbor_pos = sum((e.other_vert(v).co for e in v.link_edges), v.co * 0) / len(v.link_edges)
                            new_positions[v.index] = v.co + 0.15 * (avg_neighbor_pos - v.co)
                        else:
                            new_positions[v.index] = v.co
                    # Update vertex positions
                    for v in smooth_outer_vert:
                        v.co = new_positions[v.index]

                #该连通区域的内圈顶点平滑
                for _ in range(3):
                    # Create a list to store new vertex positions
                    new_positions = [None] * len(bm.verts)
                    # Compute new vertex positions based on the Laplacian operator
                    for v in smooth_inner_vert:
                        if not v.is_boundary:
                            avg_neighbor_pos = sum((e.other_vert(v).co for e in v.link_edges), v.co * 0) / len(v.link_edges)
                            new_positions[v.index] = v.co + 0.05 * (avg_neighbor_pos - v.co)
                        else:
                            new_positions[v.index] = v.co
                    # Update vertex positions
                    for v in smooth_inner_vert:
                        v.co = new_positions[v.index]

                area_index += 1

            bm.to_mesh(me)
            bm.free()




#保存局部加厚中的选中的顶点信息并重置全局变量
def localThickSaveInfo():
    global is_copy_local_thickening
    global is_copy_local_thickeningL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL
    global objects_array_index
    global objects_array_indexL
    global switch_selected_vertex_index
    global switch_selected_vertex_indexL
    global right_is_submit,left_is_submit

    name = bpy.context.scene.leftWindowObj
    if name == '左耳':
        left_is_submit = True

        # 提交前将模型中局部加厚的点索引给保存下来
        switch_selected_vertex_indexL = []
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                    switch_selected_vertex_indexL.append(vert.index)
            bm.to_mesh(me)
            bm.free()

    else:
        right_is_submit = True

        # 提交前将模型中局部加厚的点索引给保存下来
        switch_selected_vertex_index = []
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                    switch_selected_vertex_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()






# offset和borderWidth为面板参数,reset为将该局部加厚区域顶点重置会原模型高度
def thickening_offset_borderwidth(offset, borderWidth):
    global objects_array_index
    global objects_array_indexL
    global continuous_area
    global continuous_areaL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL

    continuous_area_cur = None
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        continuous_area_cur = continuous_area
    elif name == '左耳':
        continuous_area_cur = continuous_areaL
    if (borderWidth == 0):
        borderWidth = 0.01

    #获取需要进行操作的选中区域的顶点划分列表
    if(continuous_area_cur != None):
        continuousArea = continuous_area_cur
    else:
        select_vert_index = []  # 被选择的顶点
        active_obj = bpy.data.objects[name]
        if active_obj.type == 'MESH':
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                    select_vert_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()
        continuousArea = get_continuous_area(select_vert_index, borderWidth)
        if name == '右耳':
            continuous_area = continuousArea
        elif name == '左耳':
            continuous_areaL = continuousArea

    # 执行加厚操作
    active_obj = bpy.data.objects[name]
    if active_obj.type == 'MESH':
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        # 依次处理每个连续区域,根据原区域的最高点与offset参数和borderWidth参数进行加厚
        area_index = 0
        while (area_index < len(continuousArea)):
            select_area = continuousArea[area_index]

            # 先将选中顶点位置重置为原始位置再根据offset与max_offset重新加厚
            for vert_index in select_area.vert_index:
                vert = bm.verts[vert_index]
                dis = select_area.distance_dic[vert.index]
                if(dis < borderWidth):
                    thickness = offset * (dis / borderWidth)
                    if(thickness < 0.03):
                        thickness = 0.1
                    vert.co += vert.normal.normalized() * thickness
                else:
                    vert.co += vert.normal.normalized() * (offset)


            area_index += 1

        bm.to_mesh(me)
        bm.free()



'''
    以下部分的函数主要用于区域划分
'''
def get_selected_area_border(select_vert_index):
    '''
    根据模型上选中的顶点,获取其对应的边界顶点索引集合,并根据选中顶点生成边界圆环曲线
    '''
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)

    me = cur_obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    for vert in bm.verts:
        vert.select_set(False)
        if(vert.index in select_vert_index):
            vert.select_set(True)
    bm.to_mesh(me)
    bm.free()

    #根据得到的离散区域块复制得到离散区域的边界线
    localthick_areaclassification_border_obj = cur_obj.copy()
    localthick_areaclassification_border_obj.data = cur_obj.data.copy()
    localthick_areaclassification_border_obj.animation_data_clear()
    localthick_areaclassification_border_obj.name = name + 'LocalThickAreaClassification'
    bpy.context.collection.objects.link(localthick_areaclassification_border_obj)

    border_me = localthick_areaclassification_border_obj.data
    border_bm = bmesh.new()
    border_bm.from_mesh(border_me)
    border_bm.verts.ensure_lookup_table()
    for vert in border_bm.verts:
        if not vert.select:
            border_bm.verts.remove(vert)
    border_bm.to_mesh(border_me)

    # 选择不为边界的边
    for edge in border_bm.edges:
        edge.select_set(False)
        if not edge.is_boundary:
            edge.select_set(True)
    border_bm.to_mesh(border_me)
    # 注意，这里必须选完一次性删除，直接判断不为边界删除的话，删除某个点之后，有些本来不为边界的点就变成边界了，会出现问题
    for edge in border_bm.edges:
        if edge.select:
            border_bm.edges.remove(edge)

    # 删除所有离散点
    for vert in border_bm.verts:
        if len(vert.link_edges) == 0:
            border_bm.verts.remove(vert)
    border_bm.to_mesh(border_me)

    if name == '右耳':
        moveToRight(localthick_areaclassification_border_obj)
    elif name == '左耳':
        moveToLeft(localthick_areaclassification_border_obj)

    border_index_set = set()
    # localthick_index_layer = border_bm.verts.layers.int.get('LocalThickObjectIndex')
    for vert in border_bm.verts:
        # border_index_set.add(vert[localthick_index_layer])
        border_index_set.add(vert.index)

    return border_index_set, localthick_areaclassification_border_obj


def get_connected_vertices_breadth(bm, start_vertex_index, visited, vertex_indices):
    '''
    通过广度优先遍历,根据bm,处理vertex_indices未被visited的顶点,得到与start_vertex_index相连的区域顶点
    '''
    queue = deque([start_vertex_index])
    connected_vertices = []

    while queue:
        current_index = queue.popleft()
        if current_index in visited or current_index not in vertex_indices:
            continue
        visited.add(current_index)
        connected_vertices.append(current_index)

        # 将相邻顶点加入队列
        bm.verts.ensure_lookup_table()
        for edge in bm.verts[current_index].link_edges:
            for vert in edge.verts:
                if vert.index not in visited and vert.index in vertex_indices:
                    queue.append(vert.index)

    return connected_vertices


def get_connected_vertices_depth(bm, start_vertex_index, visited, vertex_indices):
    '''
    通过深度优先遍历,根据bm,处理vertex_indices未被visited的顶点,得到与start_vertex_index相连的区域顶点
    '''
    stack = [start_vertex_index]
    connected_vertices = []

    while stack:
        current_index = stack.pop()
        if current_index in visited or current_index not in vertex_indices:
            continue
        visited.add(current_index)
        connected_vertices.append(current_index)

        # 将相邻顶点加入栈
        bm.verts.ensure_lookup_table()
        for edge in bm.verts[current_index].link_edges:
            for vert in edge.verts:
                if vert.index not in visited and vert.index in vertex_indices:
                    stack.append(vert.index)

    return connected_vertices


def find_connected_regions_in_list_depth(vertex_indices, obj):
    '''
        对选中的顶点进行区域划分
    '''
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    visited = set()
    regions = []

    # 遍历给定的顶点索引列表
    for index in vertex_indices:
        if index not in visited:
            connected_vertices = get_connected_vertices_depth(bm, index, visited, vertex_indices)
            regions.append(connected_vertices)

    return regions


def find_connected_regions_in_list_breadth(vertex_indices, obj):
    '''
    对选中的顶点进行区域划分
    '''
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    visited = set()
    regions = []

    # 遍历给定的顶点索引列表
    for index in vertex_indices:
        if index not in visited:
            connected_vertices = get_connected_vertices_breadth(bm, index, visited, vertex_indices)
            regions.append(connected_vertices)

    return regions

def average_locations(locationslist):
    avg = Vector()

    for n in locationslist:
        avg += n

    return avg / len(locationslist)

def smooth_coords(coords, iterations):
    '''
    给定一组闭合曲线的位置,根据迭代次数iterations进行迭代处理,使其位置分布更加圆润
    '''
    while iterations:
        iterations -= 1

        smoothed = []

        for idx, co in enumerate(coords):
            if idx in [0, len(coords) - 1]:
                if idx == 0:
                    smoothed.append(average_locations([coords[-1], coords[1]]))
                elif idx == len(coords) - 1:
                    smoothed.append(average_locations([coords[-2], coords[0]]))
            else:
                co_prev = coords[idx - 1]
                co_next = coords[idx + 1]
                smoothed.append(average_locations([co_prev, co_next]))

        coords = smoothed

    return coords

def draw_border_curve(select_vert_index):
    '''
    根据选中顶点边界绘制出边界红环
    '''
    name = bpy.context.scene.leftWindowObj
    # 删除原先存在的边界红环
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LocalThickAreaClassificationBorder'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LocalThickAreaClassificationBorder'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    if (len(select_vert_index) > 1):

        # 扩大选中区域范围,进而使边界更大一些
        cur_obj = bpy.data.objects[name]
        if cur_obj.type == 'MESH':
            me = cur_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            add_select_vert = []
            for i in range(1):  # 将选中区域扩大一圈
                for vert_index in select_vert_index:
                    vert = bm.verts[vert_index]
                    for edge in vert.link_edges:
                        v1 = edge.verts[0]
                        v2 = edge.verts[1]
                        link_vert = v1 if v1 != vert else v2
                        if not (link_vert.index in add_select_vert):
                            add_select_vert.append(link_vert.index)
                for vert_index in add_select_vert:  # 根据扩大区域重置选择区域
                    if not (vert_index in select_vert_index):
                        select_vert_index.append(vert_index)
            bm.to_mesh(me)
            bm.free()
        # 将左右耳模型复制一份,根据其中其中的选中顶点,得到边界顶点集合以及删除顶点后得到的边界物体
        border_index_set, localthick_areaclassification_obj = get_selected_area_border(select_vert_index)  # 得到边界点的索引
        # 根据边界物体,对其进行区域划分
        border_regions = find_connected_regions_in_list_depth(border_index_set, localthick_areaclassification_obj)
        # 得到边界物体区域划分中的顶点对应的位置,用于生成圆环曲线
        coords = []
        for border_region in border_regions:
            coord = []
            for index in border_region:
                coord.append(localthick_areaclassification_obj.data.vertices[index].co)
            coords.append(coord)

        # 删除离散区域块物体
        bpy.data.objects.remove(localthick_areaclassification_obj, do_unlink=True)

        # 对边界物体区域划分后得到的位置进行原话处理,使得边界圆环更加圆润                                  #TODO   优化圆环边界的圆滑方法
        coords_smooth = []
        for coord in coords:
            coord_smooth = smooth_coords(coord, 1)
            coords_smooth.append(coord_smooth)

        # 创建新的曲线对象,通过边界圆环区域的位置信息,控制曲线的形状
        curve_name = name + 'LocalThickAreaClassificationBorder'
        curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
        curve_data.dimensions = '3D'
        # curve_data.offset = -0.5                   #设置偏移距离,用于补偿平滑顶点位置数组导致的凹陷  #TODO   优化圆环边界的圆滑方法
        for loop_coords in coords_smooth:
            spline = curve_data.splines.new('NURBS')
            spline.points.add(len(loop_coords) - 1)
            for i, co in enumerate(loop_coords):
                spline.points[i].co = (co.x, co.y, co.z, 1)
            spline.use_cyclic_u = True  # 开启循环
            spline.use_smooth = True  # 开启平滑,将阶数设置为6,分辨率设置为36,使其更加圆滑
            spline.order_u = 6
            spline.resolution_u = 36

        # 根据边界曲线得到边界红环物体
        localthick_areaclassification_border_obj = bpy.data.objects.new(curve_name, curve_data)
        bpy.context.collection.objects.link(localthick_areaclassification_border_obj)
        if name == '右耳':
            moveToRight(localthick_areaclassification_border_obj)
        elif name == '左耳':
            moveToLeft(localthick_areaclassification_border_obj)
        localthick_areaclassification_border_obj.data.bevel_depth = 0.1
        localthick_areaclassification_border_obj.data.bevel_resolution = 10
        newColor('localthick_border_red', 1, 0, 0, 0, 1)
        localthick_areaclassification_border_obj.data.materials.append(bpy.data.materials["localthick_border_red"])

def get_continuous_area(select_vert_index, borderWidth):
    '''
    根据左右耳模型中的选中顶点,进行区域划分得到区域顶点集合  regions

    根据左右耳模型复制一份根据其中的选中顶点,删除顶点后得到区域边界线,进行区域划分后得到区域边界集合  border_regions  coords

    根据区域划分后的边界区域顶点位置的集合coords,将其作为曲线控制点生成曲线并得到边界红环

    针对每个连通区域单独处理:
        根据borderwidth划分该区域的内外边界顶点: 遍历区域中的顶点,获取每个顶点距离 离散的区域边界中的最近顶点 的距离,以此划分内外边界
        保存记录其在原始左右耳模型上的顶点索引
    '''
    global continuous_area
    global continuous_areaL
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    continuous_area_prev = None
    if (name == "右耳"):
        continuous_area_prev = continuous_area
    elif (name == "左耳"):
        continuous_area_prev = continuous_areaL

    #删除原先存在的边界红环
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳LocalThickAreaClassificationBorder'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳LocalThickAreaClassificationBorder'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)

    print("区域划分开始:", datetime.now())
    #存在加厚区域的时候
    if(len(select_vert_index) > 1):

        #将左右耳模型复制一份,根据其中其中的选中顶点,得到边界顶点集合以及删除顶点后得到的边界物体
        border_index_set, localthick_areaclassification_obj = get_selected_area_border(select_vert_index)  # 得到边界点的索引
        print("获取区域边界:", datetime.now())
        #根据左右耳模型上选中的顶点索引,对其进行区域划分
        regions = find_connected_regions_in_list_breadth(select_vert_index, cur_obj)
        print("连通区域划分完成:", datetime.now())
        # 根据边界物体,对其进行区域划分
        border_regions = find_connected_regions_in_list_depth(border_index_set, localthick_areaclassification_obj)
        print("边界连通区域划分完成:", datetime.now())
        #得到边界物体区域划分中的顶点对应的位置,用于生成圆环曲线
        coords = []
        for border_region in border_regions:
            coord = []
            for index in border_region:
                coord.append(localthick_areaclassification_obj.data.vertices[index].co)
            coords.append(coord)

        # 删除离散区域块物体
        bpy.data.objects.remove(localthick_areaclassification_obj, do_unlink=True)


        coord_co = []         #存放边界顶点的位置,用于计算borderwidth
        for coord in coords:
            coord_co.extend(coord)


        # #对边界物体区域划分后得到的位置进行原话处理,使得边界圆环更加圆润                                  #TODO   优化圆环边界的圆滑方法
        # coords_smooth = []
        # for coord in coords:
        #     coord_smooth = smooth_coords(coord,1)
        #     coords_smooth.append(coord_smooth)
        #
        #
        # # 创建新的曲线对象,通过边界圆环区域的位置信息,控制曲线的形状
        # curve_name = name + 'LocalThickAreaClassificationBorder'
        # curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
        # curve_data.dimensions = '3D'
        # # curve_data.offset = -0.5                   #设置偏移距离,用于补偿平滑顶点位置数组导致的凹陷  #TODO   优化圆环边界的圆滑方法
        # for loop_coords in coords_smooth:
        #     spline = curve_data.splines.new('NURBS')
        #     spline.points.add(len(loop_coords) - 1)
        #     for i, co in enumerate(loop_coords):
        #         spline.points[i].co = (co.x, co.y, co.z, 1)
        #     spline.use_cyclic_u = True             #开启循环
        #     spline.use_smooth = True               #开启平滑,将阶数设置为6,分辨率设置为36,使其更加圆滑
        #     spline.order_u = 6
        #     spline.resolution_u = 36
        #
        #
        # # 根据边界曲线得到边界红环物体
        # localthick_areaclassification_border_obj = bpy.data.objects.new(curve_name, curve_data)
        # bpy.context.collection.objects.link(localthick_areaclassification_border_obj)
        # if name == '右耳':
        #     moveToRight(localthick_areaclassification_border_obj)
        # elif name == '左耳':
        #     moveToLeft(localthick_areaclassification_border_obj)
        # localthick_areaclassification_border_obj.data.bevel_depth = 0.1
        # localthick_areaclassification_border_obj.data.bevel_resolution = 10
        # newColor('localthick_border_red', 1, 0, 0, 0, 1)
        # localthick_areaclassification_border_obj.data.materials.append(bpy.data.materials["localthick_border_red"])
        #
        # print("平滑边界并生成红环:", datetime.now())

        # # 获取上一次区域划分中 选中的顶点索引 顶点对应的距离字典
        # select_vert_index_prev = []          #上一次区域划分中的顶点索引
        # distance_dic_prev = {}               #上一次区域划分中的顶点索引到区域边界距离字典
        # difference_list = []                 #上次的区域划分与本次区域划分的顶点差集
        # area_index = 0
        # if(continuous_area_prev != None):
        #     while (area_index < len(continuous_area_prev)):
        #         select_area = continuous_area_prev[area_index]
        #         select_vert_index_prev.extend(select_area.vert_index)
        #         distance_dic_prev.update(select_area.distance_dic)
        #         area_index += 1
        #     set_select_vert_index_prev = set(select_vert_index_prev)
        #     set_select_vert_index = set(select_vert_index)
        #     if(len(set_select_vert_index_prev) > len(set_select_vert_index)):
        #         difference = set_select_vert_index_prev.difference(set_select_vert_index)
        #     else:
        #         difference = set_select_vert_index.difference(set_select_vert_index_prev)
        #     difference_list = list(difference)



        # # 对当前选中区域进行区域划分,计算选中顶点到边界的距离
        continuous_area = []      # 存放连续区域对象信息(左右耳模型的顶点索引)

        me = cur_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        # # 更新上一次区域划分中的部分顶点距离,对于两次区域划分的的新顶点,更新其附近的顶点到区域边界的距离,直至距离不再改变为止
        # update_flag = True                             # 记录附近顶点中是否存在边界距离更新
        # if(len(select_vert_index_prev) > 0):
        #     update_flag = True
        # else:
        #     update_flag = False
        # base_verts_index = difference_list             # 以该顶点索引集合为基础进行边界扩散得到附件的可能需要更新边界距离的顶点
        # # print(base_verts_index)
        # while(update_flag):
        #     update_flag = False                        # 是否有顶点距离更新
        #     update_verts_index = []                    #可能需要更新边界距离的顶点
        #     for i in range(2):                         #以base_verts_index为基础边界扩散两圈获取边界距离更新顶点索引集
        #         for vert_index in base_verts_index:
        #             # print(vert_index)
        #             vert = bm.verts[vert_index]
        #             for edge in vert.link_edges:
        #                 v1 = edge.verts[0]
        #                 v2 = edge.verts[1]
        #                 link_vert_index = v1.index if v1 != vert else v2.index
        #                 # print("添加的顶点索引",link_vert_index)
        #                 if not (link_vert_index in update_verts_index):
        #                     update_verts_index.append(link_vert_index)
        #         for vert_index in update_verts_index:         # 根据扩大区域重置基础扩散区域
        #             if not (vert_index in base_verts_index):
        #                 base_verts_index.append(vert_index)
        #         # print("一次循环选取结束")
        #         # print(base_verts_index)
        #     print("开始计算距离")
        #
        #                                                #对于得到的边界距离更新顶点索引集,只处理位于上一次边界划分中的顶点
        #     update_verts_index = list(set(update_verts_index) & set(select_vert_index_prev))
        #
        #     for update_vert_index in update_verts_index:
        #         vert = bm.verts[update_vert_index]
        #         vert_co = vert.co
        #         min_distance = math.inf
        #         for border_co in coord_co:
        #             distance = math.sqrt(
        #                 (vert_co[0] - border_co[0]) ** 2 + (vert_co[1] - border_co[1]) ** 2 + (
        #                         vert_co[2] - border_co[2]) ** 2)
        #             if (min_distance > distance):
        #                 min_distance = distance
        #         old_distance = distance_dic_prev[update_vert_index]
        #         if(old_distance != min_distance):
        #             update_flag = True
        #             distance_dic_prev[update_vert_index] = min_distance
        #     print("距离更新结束")
        #保存每个连通区域的顶点索引及其到边界的距离(当该顶点存在于上一次顶点划分区域中时,边界距离直接获取上一次区域划分中记录的边界距离,优化性能)
        for region in regions:
            vert_index = []        # 存放该连通区域的顶点(左右耳模型的顶点索引)
            distance_dic = {}      # 存放该区域顶点到边界的最近距离(左右耳模型的顶点距离)
            for region_index in region:
                min_distance = math.inf
                # if(region_index in select_vert_index_prev):                 #上一次区域划分中存在该顶点,则直接读取边界距离
                #     min_distance = distance_dic_prev[region_index]
                if(False):
                    pass
                else:                                                       #对于新增顶点,计算边界距离
                    vert = bm.verts[region_index]
                    vert_co = vert.co
                    for border_co in coord_co:
                        distance = math.sqrt(
                            (vert_co[0] - border_co[0]) ** 2 + (vert_co[1] - border_co[1]) ** 2 + (
                                    vert_co[2] - border_co[2]) ** 2)
                        if (min_distance > distance):
                            min_distance = distance
                vert_index.append(region_index)
                distance_dic[region_index] = min_distance

            # 将划分的顶点信息保存
            area = selectArea(vert_index, distance_dic)
            continuous_area.append(area)
        print("边界距离计算:", datetime.now())

        bm.to_mesh(me)
        bm.free()
        return continuous_area
    return []



# 根据传入的选中顶点组,将顶点组划分为边界点,内圈,外圈,并保存再对象中
class selectArea(object):
    def __init__(self, vert_index, distance_dic):
        self.vert_index = vert_index
        self.distance_dic = distance_dic

'''
    以上部分的函数主要用于区域划分
'''







# 局部加厚镜像
class Local_Thickening_Mirror(bpy.types.Operator):
    bl_idname = "obj.localthickeningjingxiang"
    bl_label = "将右耳加厚区域镜像到左耳"

    def invoke(self, context, event):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        self.execute(context)
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):
        global switch_selected_vertex_index, switch_selected_vertex_indexL, operator_obj
        global left_is_submit, right_is_submit

        name = bpy.context.scene.leftWindowObj
        workspace = context.window.workspace.name

        left_obj = bpy.data.objects.get(context.scene.leftWindowObj)
        right_obj = bpy.data.objects.get(context.scene.rightWindowObj)

        # 只操作一个耳朵时，不执行镜像
        if left_obj == None or right_obj == None:
            return {'FINISHED'}

        # 判断参数是否为空，即左/右耳是否已经操作过
        if name == '左耳':
            # 对应的右耳是否有加厚区域
            switch_selected_vertex_index_cur = switch_selected_vertex_index
            is_submit = left_is_submit
        else:
            switch_selected_vertex_index_cur = switch_selected_vertex_indexL
            is_submit = right_is_submit

        # 只有在双窗口下执行镜像
        # 2024/10/24 单窗口的时候也可以镜像, 通过是否有加厚区域来判断
        # 判断是否提交修改,未提交时才可镜像
        # if workspace == '布局.001':
        if switch_selected_vertex_index_cur and not is_submit:
            # print('开始镜像')
            # 目标物体
            tar_obj = context.scene.leftWindowObj
            ori_obj = context.scene.rightWindowObj
            print('镜像目标', tar_obj)
            print('镜像来源', ori_obj)

            operator_obj = tar_obj

            cast_vertex_index = []
            # 右窗口物体
            obj_right = bpy.data.objects[ori_obj]
            # 左窗口物体
            obj_left = bpy.data.objects[tar_obj]



            # 若存在LocalThickCopy,则将其删除并重新生成
            all_objs = bpy.data.objects
            for selected_obj in all_objs:
                if (selected_obj.name == tar_obj + "LocalThickCopy" or selected_obj.name == tar_obj + "LocalThickCompare"):
                    bpy.data.objects.remove(selected_obj, do_unlink=True)

            if obj_left.type == 'MESH':
                left_me = obj_left.data
                left_bm = bmesh.new()
                left_bm.from_mesh(left_me)

            # 重置为初始颜色
            left_bm.verts.ensure_lookup_table()
            color_lay = left_bm.verts.layers.float_color["Color"]
            for vert in left_bm.verts:
                colvert = vert[color_lay]
                colvert.x = 1.000
                colvert.y = 0.319
                colvert.z = 0.133
            left_bm.to_mesh(left_me)
            left_bm.free()

            # duplicate_obj1.hide_set(True)

            initialModelColor()

            # 根据当前激活物体复制得到用于重置的LocalThickCopy和初始时的参照物LocalThickCompare
            active_obj = bpy.data.objects[name]
            name = active_obj.name
            duplicate_obj1 = active_obj.copy()
            duplicate_obj1.data = active_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj1)
            if tar_obj == '右耳':
                moveToRight(duplicate_obj1)
                selected_vertex_index = switch_selected_vertex_indexL
            elif tar_obj == '左耳':
                moveToLeft(duplicate_obj1)
                selected_vertex_index = switch_selected_vertex_index
            print('原有点', len(selected_vertex_index))

            initialModelColor()

            duplicate_obj2 = active_obj.copy()
            duplicate_obj2.data = active_obj.data.copy()
            duplicate_obj2.animation_data_clear()
            duplicate_obj2.name = name + "LocalThickCopy"
            bpy.context.collection.objects.link(duplicate_obj2)
            if tar_obj == '右耳':
                moveToRight(duplicate_obj2)
            elif tar_obj == '左耳':
                moveToLeft(duplicate_obj2)
            duplicate_obj2.hide_set(True)  # 将LocalThickCopy隐藏

            cast_vertex_index = point_mirror_mine(obj_left)
            print('投射点', len(cast_vertex_index))
            # 存储投射后的得到点
            if tar_obj == '右耳':
                switch_selected_vertex_index = cast_vertex_index
            elif tar_obj == '左耳':
                switch_selected_vertex_indexL = cast_vertex_index

            if obj_left.type == 'MESH':
                left_me = obj_left.data
                left_bm = bmesh.new()
                left_bm.from_mesh(left_me)

            # 给投影点上色
            left_bm.verts.ensure_lookup_table()
            color_lay = left_bm.verts.layers.float_color["Color"]
            for vert_index in cast_vertex_index:
                colvert = left_bm.verts[vert_index][color_lay]
                colvert.x = 0.133
                colvert.y = 1.000
                colvert.z = 1.000
            left_bm.to_mesh(left_me)
            left_bm.free()

            initialTransparency()

            # if name == '右耳':
            #     offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
            #     borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
            # else:
            #     offset = bpy.context.scene.localThicking_offset_L  # 获取局部加厚面板中的偏移量参数
            #     borderWidth = bpy.context.scene.localThicking_borderWidth_L  # 获取局部加厚面板中的边界宽度参数

            # 参数应该与另一只耳朵对应
            context.scene.is_thickening_completed = True    # 防止重复调用回调函数
            if name == '右耳':
                bpy.context.scene.localThicking_offset = bpy.context.scene.localThicking_offset_L
                context.scene.is_thickening_completed = False  # 利用回调函数对选中的区域进行加厚
                bpy.context.scene.localThicking_borderWidth = bpy.context.scene.localThicking_borderWidth_L
            else:
                bpy.context.scene.localThicking_offset_L = bpy.context.scene.localThicking_offset
                context.scene.is_thickening_completed = False  # 利用回调函数对选中的区域进行加厚
                bpy.context.scene.localThicking_borderWidth_L = bpy.context.scene.localThicking_borderWidth

            # thickening_reset()
            # thickening_offset_borderwidth(offset, borderWidth)
            # applySmooth()

            for o in bpy.data.objects:
                print(f"物体：{o.name}，是否显示：{o.visible_get()}")

            # 绘制选中区域边界
            select_vert_index = []
            cur_obj = bpy.data.objects[name]
            if cur_obj.type == 'MESH':
                me = cur_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.verts:
                    colvert = vert[color_lay]
                    if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z,
                                                                                               3) != 0.133:
                        select_vert_index.append(vert.index)
                bm.to_mesh(me)
                bm.free()
            draw_border_curve(select_vert_index)
        else:
            print('镜像出错')



def point_mirror_mine(tar_obj):
    """
    镜像映射点，返回目标模型上应当投射点的索引
    Args:
        tar_obj: 目标对象
    """

    def mirror_curve():
        target_object_name = ""
        target_collection_name = ""

        if tar_obj.name == '左耳':
            target_object_name = "右耳LocalThickAreaClassificationBorder"
            target_collection_name = "Left"
        else:
            target_object_name = "左耳LocalThickAreaClassificationBorder"
            target_collection_name = "Right"

        # 查找目标对象
        target_object = bpy.data.objects.get(target_object_name)

        if target_object:
            # 复制目标对象
            new_object = target_object.copy()
            new_object.data = target_object.data.copy()
            new_object.name = "curve"
            bpy.context.collection.objects.link(new_object)

            # 创建镜像变换
            new_object.scale.y = -1

            # 查找或创建目标集合
            target_collection = bpy.data.collections.get(target_collection_name)
            if not target_collection:
                target_collection = bpy.data.collections.new(target_collection_name)
                bpy.context.scene.collection.children.link(target_collection)

            # 将新对象移动到目标集合
            for collection in new_object.users_collection:
                collection.objects.unlink(new_object)
            target_collection.objects.link(new_object)

            print(f"对象'{target_object_name}'已复制并镜像放入集合'{target_collection_name}'中。")
        else:
            print(f"未找到名为'{target_object_name}'的对象。")

    mirror_curve()

    print('--------------------------------')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 获取模型和路径对象

    model = tar_obj
    path = bpy.data.objects["curve"]

    bpy.context.view_layer.objects.active = path
    bpy.context.object.data.bevel_depth = 0
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].target = model
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

    bpy.context.view_layer.objects.active = model

    #######################################################

    # 准备一个列表来存储所有路径上的点
    path_points = []

    # 遍历路径对象的所有点
    for spline in path.data.splines:
        tmp_points = []
        for point in spline.points:
            co = path.matrix_world @ Vector((point.co.x, point.co.y, point.co.z))
            local_path_point = model.matrix_world.inverted() @ co
            tmp_points.append(local_path_point)
        path_points.append(tmp_points)

    group = model.vertex_groups.new(name="all")
    bpy.ops.object.vertex_group_set_active(group='all')

    bpy.ops.object.mode_set(mode='EDIT')

    all_points = []
    # 获取模型的网格数据
    bm = bmesh.from_edit_mesh(model.data)
    bm.verts.ensure_lookup_table()

    # 查找模型上最接近路径点的顶点并选中
    for tmp in path_points:
        n_points = []
        for path_point in tmp:
            local_path_point = model.matrix_world.inverted() @ path_point

            closest_vert = None
            min_dist = float('inf')

            for vert in bm.verts:
                dist = (vert.co - local_path_point).length
                if dist < min_dist:
                    min_dist = dist
                    closest_vert = vert
            n_points.append(closest_vert)
        all_points.append(n_points)

    # 存储所有的外围顶点的索引
    all_points_idx = []

    for n_points in all_points:
        for i in range(len(n_points) - 1):
            p1 = n_points[i]
            p2 = n_points[i + 1]

            if p1.index == p2.index:
                continue

            p1.select_set(True)
            all_points_idx.append(p1.index)

            for v in bm.verts:
                v.select_set(False)

            if any(p2 in edge.verts for edge in bm.edges if p1 in edge.verts):
                continue
            else:
                p1.select_set(True)
                p2.select_set(True)

                bpy.ops.mesh.shortest_path_select()
                p1.select_set(False)
                p2.select_set(False)

                for v in bm.verts:
                    if v.select:
                        all_points_idx.append(v.index)

                for v in bm.verts:
                    v.select_set(False)

        p1 = n_points[-1]
        p2 = n_points[0]
        p1.select_set(True)

        all_points_idx.append(p1.index)

        for v in bm.verts:
            v.select_set(False)

        if any(p2 in edge.verts for edge in bm.edges if p1 in edge.verts):
            continue
        else:
            p1.select_set(True)
            p2.select_set(True)

            bpy.ops.mesh.shortest_path_select()
            p1.select_set(False)
            p2.select_set(False)

            for v in bm.verts:
                if v.select:
                    all_points_idx.append(v.index)

            for v in bm.verts:
                v.select_set(False)

    for index in all_points_idx:
        bm.verts[index].select = True

    bpy.ops.object.vertex_group_assign()

    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.loop_to_region()

    target_vert_indices = [v.index for v in bm.verts if v.select]

    bpy.data.objects.remove(path, do_unlink=True)
    bm.free()

    bpy.ops.object.mode_set(mode='OBJECT')

    return target_vert_indices


class Local_Thickening_Reset(bpy.types.Operator):
    bl_idname = "obj.localthickeningreset"
    bl_label = "重置模型"

    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):

        global is_copy_local_thickening
        global is_copy_local_thickeningL

        global local_thickening_objects_array
        global local_thickening_objects_arrayL
        global objects_array_index
        global objects_array_indexL
        bpy.context.scene.var = 9

        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            #删除保存的LocalThickCompare状态物体
            for local_thickening_objects_name in local_thickening_objects_array:
                local_thickening_object = bpy.data.objects.get(local_thickening_objects_name)
                if(local_thickening_object != None):
                    bpy.data.objects.remove(local_thickening_object, do_unlink=True)
            # 重置状态数组
            local_thickening_objects_array = []  # 重置局部加厚中保存模型各个状态的数组
            objects_array_index = -1
            is_copy_local_thickening = False
        elif name == '左耳':
            # 删除保存的LocalThickCompare状态物体
            for local_thickening_objects_name in local_thickening_objects_arrayL:
                local_thickening_object = bpy.data.objects.get(local_thickening_objects_name)
                if (local_thickening_object != None):
                    bpy.data.objects.remove(local_thickening_object, do_unlink=True)
            # 重置状态数组
            local_thickening_objects_arrayL = []  # 重置局部加厚中保存模型各个状态的数组
            objects_array_indexL = -1
            is_copy_local_thickeningL = False


        # 根据LocalThickCopy复制出一份物体用来将参照物LocalThickCompare为最初的模型
        for selected_obj in bpy.data.objects:
            if (selected_obj.name == name + "LocalThickCompare"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        copyname = name + "LocalThickCopy"
        ori_obj = bpy.data.objects[copyname]
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "LocalThickCompare"
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)

        # 根据LocalThickCopy复制出一份物体并替换为当前激活物体
        active_obj = bpy.data.objects[name]
        copyname = name + "LocalThickCopy"
        ori_obj = bpy.data.objects[copyname]
        bpy.data.objects.remove(active_obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)


        # 删除局部加厚中的圆环
        border_obj = bpy.data.objects.get(name + "LocalThickAreaClassificationBorder")
        if(border_obj != None):
            bpy.data.objects.remove(border_obj, do_unlink=True)

        return {'FINISHED'}


class Local_Thickening_AddArea(bpy.types.Operator):
    bl_idname = "obj.localthickeningaddarea"
    bl_label = "增大局部加厚区域"

    __left_mouse_down = False
    __right_mouse_down = False        # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None              # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None          # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __initial_radius = None           # 圆环初始大小

    __object_mode = None             # 当前应该处于物体模式,该标志为True,需要切换为物体模式调用公共鼠标行为
    __vertex_paint_mode = None       # 当前应该处于顶点绘制模式,该标志为True,切换到顶点绘制模式调用颜色笔刷


    def invoke(self, context, event):
        op_cls = Local_Thickening_AddArea

        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False                       # 初始化鼠标右键行为操作，通过鼠标右键控制圆环大小
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_radius = None

        op_cls.__object_mode = True
        op_cls.__vertex_paint_mode = False

        bpy.ops.object.mode_set(mode='VERTEX_PAINT')            # 将默认的物体模式切换到顶点绘制模式
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")    # 调用自由线笔刷
        bpy.data.brushes["Draw"].color = (0.4, 1, 1)            # 设置笔刷颜色,该颜色用于扩大局部加厚区域
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'      # 衰减设置为常量
        bpy.ops.object.mode_set(mode='OBJECT')                  # 将默认的顶点绘制模式切换到物体模式
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")    # 切换到选择模式，执行公共鼠标行为

        bpy.context.scene.var = 5
        global add_area_modal_start
        if not add_area_modal_start:
            add_area_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("Local_Thickening_AddArea_invoke")

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_AddArea
        name = bpy.context.scene.leftWindowObj

        global add_area_modal_start

        override1 = getOverride()
        area = override1['area']

        if context.area:
            context.area.tag_redraw()

        if bpy.context.screen.areas[0].spaces.active.context == 'OUTPUT':
            if get_mirror_context():
                print('Local_Thickening_AddArea_finish')
                add_area_modal_start = False
                set_mirror_context(False)
                return {'FINISHED'}

            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 5):
                if is_mouse_on_object(context, event):
                    if event.type == 'LEFTMOUSE':  # 监听左键
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

                    elif event.type == 'WHEELUPMOUSE':
                        if name == '右耳':
                            bpy.context.scene.localThicking_offset += 0.05
                        else:
                            bpy.context.scene.localThicking_offset_L += 0.05
                        return {'RUNNING_MODAL'}
                    elif event.type == 'WHEELDOWNMOUSE':
                        if name == '右耳':
                            bpy.context.scene.localThicking_offset -= 0.05
                        else:
                            bpy.context.scene.localThicking_offset_L -= 0.05
                        return {'RUNNING_MODAL'}

                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if isSelectedAreaChanged():
                                auto_thickening()
                                saveSelected()

                            if op_cls.__object_mode:
                                op_cls.__vertex_paint_mode = True
                                op_cls.__object_mode = False
                                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                                if name == '右耳':  # 设置圆环大小
                                    radius = context.scene.localThicking_circleRedius
                                else:
                                    radius = context.scene.localThicking_circleRedius_L
                                bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                                bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例

                        else:
                            if op_cls.__object_mode:
                                op_cls.__vertex_paint_mode = True
                                op_cls.__object_mode = False
                                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                                if name == '右耳':  # 设置圆环大小
                                    radius = context.scene.localThicking_circleRedius
                                else:
                                    radius = context.scene.localThicking_circleRedius_L
                                bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                                bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例

                        if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                            op_cls.__now_mouse_y = event.mouse_region_y
                            op_cls.__now_mouse_x = event.mouse_region_x
                            dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                                op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                            # 上移扩大，下移缩小
                            op = 1
                            if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                                op = -1
                            radius = min(max(op_cls.__initial_radius + dis * op, 50), 200)  # 圆环大小  [50,200]
                            bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = radius
                            if name == '右耳':
                                context.scene.localThicking_circleRedius = radius  # 保存改变的圆环大小
                            else:
                                context.scene.localThicking_circleRedius_L = radius

                        if not op_cls.__left_mouse_down and not op_cls.__right_mouse_down:
                            showThickness(context, event)  # 添加厚度显示,鼠标位于模型上时，显示模型上鼠标指针处的厚度

                        return {'PASS_THROUGH'}

                # 鼠标不在模型上的时候,从模型上切换到空白区域的时候,切换到顶点绘制模式调用颜色笔刷,移除厚度显示
                else:
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__object_mode and op_cls.__vertex_paint_mode:
                                op_cls.__vertex_paint_mode = False
                                op_cls.__left_mouse_down = True
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__object_mode and op_cls.__vertex_paint_mode:
                                op_cls.__vertex_paint_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        elif event.value == 'RELEASE':  # 圆环移到物体外，不再改变大小
                            if op_cls.__right_mouse_down:
                                op_cls.__right_mouse_down = False
                        return {'PASS_THROUGH'}
                    elif event.type == 'MIDDLEMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__object_mode and op_cls.__vertex_paint_mode:
                                op_cls.__vertex_paint_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if isSelectedAreaChanged():
                                auto_thickening()
                                saveSelected()

                        if not op_cls.__object_mode:
                            op_cls.__object_mode = True
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                                bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = 1

                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 5 and bpy.context.scene.var in get_process_var_list("局部加厚"):
                print("Local_Thickening_AddArea_finish")
                add_area_modal_start = False
                return {'FINISHED'}

            else:
                if event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and now() - get_switch_time() > 0.3 and get_switch_flag():
                print("Local_Thickening_AddArea_finish")
                add_area_modal_start = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class Local_Thickening_ReduceArea(bpy.types.Operator):
    bl_idname = "obj.localthickeningreducearea"
    bl_label = "减小局部加厚区域"

    __left_mouse_down = False
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __initial_radius = None  # 圆环初始大小

    __object_mode = None  # 当前应该处于物体模式,该标志为True,需要切换为物体模式调用公共鼠标行为
    __vertex_paint_mode = None  # 当前应该处于顶点绘制模式,该标志为True,切换到顶点绘制模式调用颜色笔刷

    def invoke(self, context, event):
        op_cls = Local_Thickening_ReduceArea

        op_cls.__left_mouse_down = False
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作，通过鼠标右键控制圆环大小
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_radius = None

        op_cls.__object_mode = True
        op_cls.__vertex_paint_mode = False

        bpy.ops.object.mode_set(mode='VERTEX_PAINT')         # 将默认的物体模式切换到顶点绘制模式
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw") # 设置笔刷颜色,该颜色用于缩小局部加厚区域
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)       # 调用自由线笔刷
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'   # 衰减设置为常量
        bpy.ops.object.mode_set(mode='OBJECT')               # 将默认的顶点绘制模式切换到物体模式
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box") # 切换到选择模式，执行公共鼠标行为

        bpy.context.scene.var = 6
        global reduce_area_modal_start
        if not reduce_area_modal_start:
            reduce_area_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("Local_Thickening_ReduceArea_invoke")

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_ReduceArea
        name = bpy.context.scene.leftWindowObj

        global reduce_area_modal_start

        override1 = getOverride()
        area = override1['area']

        if context.area:
            context.area.tag_redraw()

        if bpy.context.screen.areas[0].spaces.active.context == 'OUTPUT':
            if get_mirror_context():
                print('Local_Thickening_ReduceArea_finish')
                reduce_area_modal_start = False
                set_mirror_context(False)
                return {'FINISHED'}

            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 6):
                if is_mouse_on_object(context, event):
                    if event.type == 'LEFTMOUSE':  # 监听左键
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

                    elif event.type == 'WHEELUPMOUSE':
                        if name == '右耳':
                            bpy.context.scene.localThicking_offset += 0.05
                        else:
                            bpy.context.scene.localThicking_offset_L += 0.05
                        return {'RUNNING_MODAL'}
                    elif event.type == 'WHEELDOWNMOUSE':
                        if name == '右耳':
                            bpy.context.scene.localThicking_offset -= 0.05
                        else:
                            bpy.context.scene.localThicking_offset_L -= 0.05
                        return {'RUNNING_MODAL'}

                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if isSelectedAreaChanged():
                                auto_thickening()
                                saveSelected()

                            if op_cls.__object_mode:
                                op_cls.__vertex_paint_mode = True
                                op_cls.__object_mode = False
                                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                                if name == '右耳':  # 设置圆环大小
                                    radius = context.scene.localThicking_circleRedius
                                else:
                                    radius = context.scene.localThicking_circleRedius_L
                                bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                                bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例

                        else:
                            if op_cls.__object_mode:
                                op_cls.__vertex_paint_mode = True
                                op_cls.__object_mode = False
                                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                                if name == '右耳':  # 设置圆环大小
                                    radius = context.scene.localThicking_circleRedius
                                else:
                                    radius = context.scene.localThicking_circleRedius_L
                                bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                                bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例

                        if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                            op_cls.__now_mouse_y = event.mouse_region_y
                            op_cls.__now_mouse_x = event.mouse_region_x
                            dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                                op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                            # 上移扩大，下移缩小
                            op = 1
                            if op_cls.__now_mouse_y < op_cls.__initial_mouse_y:
                                op = -1
                            radius = min(max(op_cls.__initial_radius + dis * op, 50), 200)  # 圆环大小  [50,200]
                            bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = radius
                            if name == '右耳':
                                context.scene.localThicking_circleRedius = radius  # 保存改变的圆环大小
                            else:
                                context.scene.localThicking_circleRedius_L = radius

                        if not op_cls.__left_mouse_down and not op_cls.__right_mouse_down:
                            showThickness(context, event)  # 添加厚度显示,鼠标位于模型上时，显示模型上鼠标指针处的厚度

                        return {'PASS_THROUGH'}

                # 鼠标不在模型上的时候,从模型上切换到空白区域的时候,切换到顶点绘制模式调用颜色笔刷,移除厚度显示
                else:
                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__object_mode and op_cls.__vertex_paint_mode:
                                op_cls.__vertex_paint_mode = False
                                op_cls.__left_mouse_down = True
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'RIGHTMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__object_mode and op_cls.__vertex_paint_mode:
                                op_cls.__vertex_paint_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        elif event.value == 'RELEASE':  # 圆环移到物体外，不再改变大小
                            if op_cls.__right_mouse_down:
                                op_cls.__right_mouse_down = False
                        return {'PASS_THROUGH'}
                    elif event.type == 'MIDDLEMOUSE':
                        if event.value == 'PRESS':
                            if event.mouse_x > 60 and op_cls.__object_mode and op_cls.__vertex_paint_mode:
                                op_cls.__vertex_paint_mode = False
                                bpy.ops.object.mode_set(mode='OBJECT')
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式
                        return {'PASS_THROUGH'}
                    elif event.type == 'MOUSEMOVE':
                        if op_cls.__left_mouse_down:
                            op_cls.__left_mouse_down = False
                            if isSelectedAreaChanged():
                                auto_thickening()
                                saveSelected()

                        if not op_cls.__object_mode:
                            op_cls.__object_mode = True
                            if MyHandleClass._handler:
                                MyHandleClass.remove_handler()
                                bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = 1

                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 6 and bpy.context.scene.var in get_process_var_list("局部加厚"):
                print("Local_Thickening_ReduceArea_finish")
                reduce_area_modal_start = False
                return {'FINISHED'}

            else:
                if event.type == 'MOUSEMOVE':
                    if op_cls.__left_mouse_down:
                        op_cls.__left_mouse_down = False
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and now() - get_switch_time() > 0.3 and get_switch_flag():
                print("Local_Thickening_ReduceArea_finish")
                reduce_area_modal_start = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class Local_Thickening_Thicken(bpy.types.Operator):
    bl_idname = "obj.localthickeningthick"
    bl_label = "对选中的加厚区域进行加厚,透明预览"

    def invoke(self, context, event):

        global is_copy_local_thickening                          # 用于在第一次加厚时,将LocalThickCopy复制下来并保存以初始化状态数组
        global is_copy_local_thickeningL
        global local_thickening_objects_array                    # 将模型加厚的各个状态保存到状态数组中
        global local_thickening_objects_arrayL
        global objects_array_index
        global objects_array_indexL
        global right_is_submit,left_is_submit


        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            if not is_copy_local_thickening:
                # 保存模型最初的状态，用于重置,并将LocalThickCopy保存到状态数组的初始化状态
                is_copy_local_thickening = True
                # 将当前模型状态保存进状态数组
                comparename = name + "LocalThickCopy"
                compare_obj = bpy.data.objects[comparename]
                duplicate_obj = compare_obj.copy()
                duplicate_obj.data = compare_obj.data.copy()
                duplicate_obj.animation_data_clear()
                objects_array_index = objects_array_index + 1
                duplicate_obj.name = "右耳localThick_array_objects" + str(objects_array_index)
                bpy.context.collection.objects.link(duplicate_obj)
                duplicate_obj.hide_set(True)
                moveToRight(duplicate_obj)
                local_thickening_objects_array.append(duplicate_obj.name)
                right_is_submit = False

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            initialTransparency()

            name = bpy.context.scene.leftWindowObj
            if name == '右耳':
                offset = bpy.context.scene.localThicking_offset
                borderWidth = bpy.context.scene.localThicking_borderWidth
            else:
                offset = bpy.context.scene.localThicking_offset_L
                borderWidth = bpy.context.scene.localThicking_borderWidth_L

            # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth)
            applySmooth()

            # 将加厚之后的模型保存到状态数组中
            initialModelColor()
            active_obj = bpy.data.objects[name]
            duplicate_obj = active_obj.copy()
            duplicate_obj.data = active_obj.data.copy()
            duplicate_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(duplicate_obj)
            bpy.context.view_layer.objects.active = duplicate_obj
            # 将其颜色全部覆盖重置再保存到数组中
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
            bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
            bpy.ops.paint.vertex_color_set()
            bpy.ops.object.mode_set(mode='OBJECT')
            duplicate_obj1 = duplicate_obj.copy()
            duplicate_obj1.data = duplicate_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            objects_array_index = objects_array_index + 1
            duplicate_obj1.name = "右耳localThick_array_objects" + str(objects_array_index)
            bpy.context.collection.objects.link(duplicate_obj1)
            duplicate_obj1.hide_set(True)
            moveToRight(duplicate_obj1)
            local_thickening_objects_array.append(duplicate_obj1.name)
            bpy.data.objects.remove(duplicate_obj, do_unlink=True)
            bpy.context.view_layer.objects.active = active_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            initialTransparency()

            # 更换参照物
            thicking_temp_obj = bpy.data.objects.get(local_thickening_objects_array[objects_array_index])
            for selected_obj in bpy.data.objects:
                if (selected_obj.name == name + "LocalThickCompare"):
                    bpy.data.objects.remove(selected_obj, do_unlink=True)
            duplicate_obj = thicking_temp_obj.copy()
            duplicate_obj.data = thicking_temp_obj.data.copy()
            duplicate_obj.name = name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            elif name == '左耳':
                moveToLeft(duplicate_obj)

            # 对选中的局部加厚区域,更新完参照物之后,在此基础上根据offset参数与borderWidth参数进行加厚
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth)
            applySmooth()


            # 解决模型重叠问题
            comparename = name + "LocalThickCompare"
            compare_obj = bpy.data.objects[comparename]
            compare_obj.hide_set(True)
            compare_obj.hide_set(False)
        elif name == '左耳':
            if not is_copy_local_thickeningL:
                # 保存模型最初的状态，用于重置,并将LocalThickCopy保存到状态数组的初始化状态
                is_copy_local_thickeningL = True
                # 将当前模型状态保存进状态数组
                comparename = name + "LocalThickCopy"
                compare_obj = bpy.data.objects[comparename]
                duplicate_obj = compare_obj.copy()
                duplicate_obj.data = compare_obj.data.copy()
                duplicate_obj.animation_data_clear()
                objects_array_indexL = objects_array_indexL + 1
                duplicate_obj.name = "左耳localThick_array_objects" + str(objects_array_indexL)
                bpy.context.collection.objects.link(duplicate_obj)
                duplicate_obj.hide_set(True)
                moveToLeft(duplicate_obj)
                local_thickening_objects_arrayL.append(duplicate_obj.name)
                left_is_submit = False

            bpy.ops.object.mode_set(mode='OBJECT')                 # 将默认的顶点绘制模式切换到物体模式
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")   # 切换到选择笔刷

            initialTransparency()

            name = bpy.context.scene.leftWindowObj
            if name == '右耳':
                offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
                borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
            else:
                offset = bpy.context.scene.localThicking_offset_L  # 获取局部加厚面板中的偏移量参数
                borderWidth = bpy.context.scene.localThicking_borderWidth_L  # 获取局部加厚面板中的边界宽度参数

            # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth)
            applySmooth()


            # 将加厚之后的模型保存到状态数组中
            initialModelColor()
            active_obj = bpy.data.objects[name]
            duplicate_obj = active_obj.copy()
            duplicate_obj.data = active_obj.data.copy()
            duplicate_obj.animation_data_clear()
            bpy.context.scene.collection.objects.link(duplicate_obj)
            bpy.context.view_layer.objects.active = duplicate_obj
            # 将其颜色全部覆盖重置再保存到数组中
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
            bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
            bpy.ops.paint.vertex_color_set()
            bpy.ops.object.mode_set(mode='OBJECT')
            duplicate_obj1 = duplicate_obj.copy()
            duplicate_obj1.data = duplicate_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            objects_array_indexL = objects_array_indexL + 1
            duplicate_obj1.name = "左耳localThick_array_objects" + str(objects_array_indexL)
            bpy.context.collection.objects.link(duplicate_obj1)
            duplicate_obj1.hide_set(True)
            moveToLeft(duplicate_obj1)
            local_thickening_objects_arrayL.append(duplicate_obj1.name)
            bpy.data.objects.remove(duplicate_obj, do_unlink=True)
            bpy.context.view_layer.objects.active = active_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            initialTransparency()

            # 更换参照物
            thicking_temp_obj = bpy.data.objects.get(local_thickening_objects_arrayL[objects_array_indexL])
            for selected_obj in bpy.data.objects:
                if (selected_obj.name == name + "LocalThickCompare"):
                    bpy.data.objects.remove(selected_obj, do_unlink=True)
            duplicate_obj = thicking_temp_obj.copy()
            duplicate_obj.data = thicking_temp_obj.data.copy()
            duplicate_obj.name = name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            elif name == '左耳':
                moveToLeft(duplicate_obj)

            # 对选中的局部加厚区域,更新完参照物之后,在此基础上根据offset参数与borderWidth参数进行加厚
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth)
            applySmooth()



            # 解决模型重叠问题
            comparename = name + "LocalThickCompare"
            compare_obj = bpy.data.objects[comparename]
            compare_obj.hide_set(True)
            compare_obj.hide_set(False)

        #重新绘制选中区域边界
        select_vert_index = []
        cur_obj = bpy.data.objects[name]
        if cur_obj.type == 'MESH':
            me = cur_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            color_lay = bm.verts.layers.float_color["Color"]
            for vert in bm.verts:
                colvert = vert[color_lay]
                if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                    select_vert_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()
        draw_border_curve(select_vert_index)

        bpy.context.scene.var = 7
        global thicken_modal_start
        if not thicken_modal_start:
            thicken_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("Local_Thickening_Thicken_invoke")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global thicken_modal_start

        if context.area:
            context.area.tag_redraw()

        if bpy.context.screen.areas[0].spaces.active.context == 'OUTPUT':
            if get_mirror_context():
                print('Local_Thickening_Thicken_finish')
                thicken_modal_start = False
                set_mirror_context(False)
                return {'FINISHED'}

            if bpy.context.scene.var == 7:
                if (is_mouse_on_object(context, event)):
                    if event.type == 'MOUSEMOVE':
                        showThickness(context, event)      # 鼠标位于模型上时，显示模型上鼠标指针处位置的厚度
                else:
                    if MyHandleClass._handler:
                        MyHandleClass.remove_handler()         # 鼠标不在模型上时，移除厚度显示
                return {'PASS_THROUGH'}
            else:
                if bpy.context.scene.var in get_process_var_list("局部加厚"):
                    print("Local_Thickening_Thicken_finish")
                    thicken_modal_start = False
                    return {'FINISHED'}
        else:
            if get_switch_time() != None and now() - get_switch_time() > 0.3 and get_switch_flag():
                print("Local_Thickening_Thicken_finish")
                thicken_modal_start = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class Local_Thickening_Submit(bpy.types.Operator):
    bl_idname = "obj.localthickeningsubmit"
    bl_label = "提交做出的加厚修改"

    def invoke(self, context, event):
        bpy.context.scene.var = 8

        self.execute(context)
        return {'FINISHED'}


    def execute(self, context):
        global left_is_submit,right_is_submit,operator_obj
        global prev_localthick_area_index,prev_localthick_area_indexL
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            prev_localthick_area_index = []
        elif name == '左耳':
            prev_localthick_area_indexL = []
        #保存局部加厚中选中的顶点信息并将全局变量重置
        localThickSaveInfo()
        # 将当前激活模型由透明状态切换为非透明状态并将模型中选中的局部加厚区域重置
        initialModelColor()
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        # 删除局部加厚中的圆环
        border_obj = bpy.data.objects.get(name + "LocalThickAreaClassificationBorder")
        if (border_obj != None):
            bpy.data.objects.remove(border_obj, do_unlink=True)

        if name == '左耳':
            left_is_submit = True
        else:
            right_is_submit = True

        # 根据当前激活物体复制出物体将LocalThickCompare和LocalThickCopy替换
        active_obj = bpy.data.objects[name]
        localthickcompare_name = name + "LocalThickCompare"
        localthickcompare_obj = bpy.data.objects.get(localthickcompare_name)
        if (localthickcompare_obj != None):
            bpy.data.objects.remove(localthickcompare_obj, do_unlink=True)
        localthickcopy_name = name + "LocalThickCopy"
        localthickcopy_obj = bpy.data.objects.get(localthickcopy_name)
        if (localthickcopy_obj != None):
            bpy.data.objects.remove(localthickcopy_obj, do_unlink=True)
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "LocalThickCopy"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "LocalThickCompare"
        bpy.context.collection.objects.link(duplicate_obj)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)

        # 将激活物体设置为左/右耳
        name = bpy.context.scene.leftWindowObj
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj

        return {'FINISHED'}


class MyTool_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.jiahou_reset"
    bl_label = "局部加厚重置"
    bl_description = (
        "重置模型，将模型全部用遮罩覆盖"
    )
    bl_icon = "ops.mesh.bevel"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool2_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.jiahou_reset2"
    bl_label = "局部加厚重置"
    bl_description = (
        "重置模型，将模型全部用遮罩覆盖"
    )
    bl_icon = "ops.mesh.bevel"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool3_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addarea"
    bl_label = "增大局部区域"
    bl_description = (
        "使用鼠标拖动增大局部区域"
    )
    bl_icon = "ops.mesh.rip"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningaddarea", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool4_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addarea2"
    bl_label = "增大局部区域"
    bl_description = (
        "使用鼠标拖动增大局部区域"
    )
    bl_icon = "ops.mesh.rip"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningaddarea", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool5_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.reduecearea"
    bl_label = "缩小局部区域"
    bl_description = (
        "使用鼠标拖动缩小局部区域"
    )
    bl_icon = "ops.mesh.extrude_region_shrink_fatten"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningreducearea", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool6_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.reducearea2"
    bl_label = "缩小局部区域"
    bl_description = (
        "使用鼠标拖动缩小局部区域"
    )
    bl_icon = "ops.mesh.extrude_region_shrink_fatten"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningreducearea", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool7_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.jiahouthickening"
    bl_label = "局部加厚"
    bl_description = (
        "加厚选中的区域"
    )
    bl_icon = "ops.mesh.extrude_manifold"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningthick", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool8_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.jiahouthickening2"
    bl_label = "局部加厚"
    bl_description = (
        "加厚选中的区域"
    )
    bl_icon = "ops.mesh.extrude_manifold"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningthick", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool9_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.submit"
    bl_label = "提交"
    bl_description = (
        "确认所作的改变"
    )
    bl_icon = "ops.mesh.extrude_faces_move"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool10_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.submit2"
    bl_label = "提交"
    bl_description = (
        "确认所作的改变"
    )
    bl_icon = "ops.mesh.extrude_faces_move"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool11_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.localthickeningjingxiang"
    bl_label = "镜像"
    bl_description = (
        "镜像加厚区域"
    )
    bl_icon = "ops.mesh.dupli_extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningjingxiang", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool12_JiaHou(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.localthickeningjingxiang2"
    bl_label = "局部加厚镜像"
    bl_description = (
        "镜像加厚区域"
    )
    bl_icon = "ops.mesh.dupli_extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("obj.localthickeningjingxiang", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


    # 注册类


_classes = [
    Local_Thickening_Reset,
    Local_Thickening_AddArea,
    Local_Thickening_ReduceArea,
    Local_Thickening_Thicken,
    Local_Thickening_Submit,
    Local_Thickening_Mirror,
]


def register_jiahou_tools():
    bpy.utils.register_tool(MyTool_JiaHou, separator=True, group=False)
    bpy.utils.register_tool(MyTool3_JiaHou, separator=True, group=False, after={MyTool_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool5_JiaHou, separator=True, group=False, after={MyTool3_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool7_JiaHou, separator=True, group=False, after={MyTool5_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool9_JiaHou, separator=True, group=False, after={MyTool7_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool11_JiaHou, separator=True, group=False, after={MyTool9_JiaHou.bl_idname})

    bpy.utils.register_tool(MyTool2_JiaHou, separator=True, group=False)
    bpy.utils.register_tool(MyTool4_JiaHou, separator=True, group=False, after={MyTool2_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool6_JiaHou, separator=True, group=False, after={MyTool4_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool8_JiaHou, separator=True, group=False, after={MyTool6_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool10_JiaHou, separator=True, group=False, after={MyTool8_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool12_JiaHou, separator=True, group=False, after={MyTool10_JiaHou.bl_idname})


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_JiaHou, separator=True, group=False)
    # bpy.utils.register_tool(MyTool3_JiaHou, separator=True, group=False, after={MyTool_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool5_JiaHou, separator=True, group=False, after={MyTool3_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool7_JiaHou, separator=True, group=False, after={MyTool5_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool9_JiaHou, separator=True, group=False, after={MyTool7_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool11_JiaHou,separator=True, group=False,after={MyTool9_JiaHou.bl_idname})
    #
    # bpy.utils.register_tool(MyTool2_JiaHou, separator=True, group=False)
    # bpy.utils.register_tool(MyTool4_JiaHou, separator=True, group=False, after={MyTool2_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool6_JiaHou, separator=True, group=False, after={MyTool4_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool8_JiaHou, separator=True, group=False, after={MyTool6_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool10_JiaHou, separator=True, group=False, after={MyTool8_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool12_JiaHou,separator=True, group=False,after={MyTool10_JiaHou.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_JiaHou)
    bpy.utils.unregister_tool(MyTool3_JiaHou)
    bpy.utils.unregister_tool(MyTool5_JiaHou)
    bpy.utils.unregister_tool(MyTool7_JiaHou)
    bpy.utils.unregister_tool(MyTool9_JiaHou)
    bpy.utils.unregister_tool(MyTool11_JiaHou)

    bpy.utils.unregister_tool(MyTool2_JiaHou)
    bpy.utils.unregister_tool(MyTool4_JiaHou)
    bpy.utils.unregister_tool(MyTool6_JiaHou)
    bpy.utils.unregister_tool(MyTool8_JiaHou)
    bpy.utils.unregister_tool(MyTool10_JiaHou)
    bpy.utils.unregister_tool(MyTool12_JiaHou)