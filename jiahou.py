import bpy
import bmesh
import re
import sys
import mathutils
from .tool import *
from math import *
from datetime import *
from pynput import mouse
from mathutils import Vector
from enum import auto
from ssl import DER_cert_to_PEM_cert
from multiprocessing import context
from bpy_extras import view3d_utils
from bpy.types import WorkSpaceTool

prev_on_object = False            # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体

is_copy_local_thickening = False  # 判断加厚状态，值为True时为未提交，值为False为提交后或重置后(未处于加厚预览状态)
                                  #主要用于加厚按钮中，第一次加厚初始化状态数组。局部加厚模块切换时的状态判断
is_copy_local_thickeningL = False

local_thickening_objects_array = []          # 保存局部加厚功能中每一步加厚时物体的状态，用于单步撤回
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

local_thickening_mouse_listener = None                #添加鼠标监听
left_mouse_release = False                            #鼠标左键是否松开,鼠标左键松开之后若局部加厚区域发生变化,则执行自动加厚
left_mouse_press = False                              # 鼠标左键是否按下,鼠标从模型上移开之后点击鼠标之后再切换到物体模式的公共鼠标行为,防止闪退,
right_mouse_press = False                             # 鼠标右键是否按下,鼠标从模型上移开之后点击鼠标之后再切换到物体模式的公共鼠标行为,防止闪退
middle_mouse_press = False                            # 鼠标中键是否按下,鼠标从模型上移开之后点击鼠标之后再切换到物体模式的公共鼠标行为,防止闪退


# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]

    is_on_object = False  # 初始化变量

    if context.area:
        context.area.tag_redraw()
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
        if (context.mode == 'OBJECT' or context.mode == "PAINT_VERTEX"):
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

    if context.area:
        context.area.tag_redraw()

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
        if (context.mode == 'OBJECT' or context.mode == "PAINT_VERTEX"):
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
    mat = newShader("Yellow")
    name = bpy.context.scene.leftWindowObj
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


#添加的鼠标监听中,鼠标点击绑定的函数
def on_click(x, y, button, pressed):
    global left_mouse_release
    global left_mouse_press
    global right_mouse_press
    global middle_mouse_press

    if button == mouse.Button.left and pressed:
        left_mouse_press = True
    elif button == mouse.Button.left and not pressed:
        left_mouse_press = False
        left_mouse_release = True

    if button == mouse.Button.right and pressed:
        right_mouse_press = True
    elif button == mouse.Button.right and not pressed:
        right_mouse_press = False

    if button == mouse.Button.middle and pressed:
        middle_mouse_press = True
    elif button == mouse.Button.middle and not pressed:
        middle_mouse_press = False

# 前面的打磨功能切换到 局部加厚模式时
def frontToLocalThickening():
    global switch_selected_vertex_index
    global switch_selected_vertex_indexL
    global objects_array_index
    global objects_array_indexL
    global is_copy_local_thickening
    global is_copy_local_thickeningL
    global left_is_submit,right_is_submit
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickening == True):
            objects_array_index = 0
        else:
            objects_array_index = -1
    elif (name == "左耳"):
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickeningL == True):
            objects_array_indexL = 0
        else:
            objects_array_indexL = -1

    #进入该模块的时候,将左/右耳设置为当前激活物体
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


    # 若存在LocalThickCopy,则将其删除并重新生成
    all_objs = bpy.data.objects
    active_obj = bpy.data.objects[name]
    name = active_obj.name
    for selected_obj in all_objs:
        if (selected_obj.name == name+"LocalThickCopy" or selected_obj.name == name+"LocalThickCompare"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    # 根据当前激活物体复制得到用于重置的LocalThickCopy和初始时的参照物LocalThickCompare
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

    # 添加监听
    global local_thickening_mouse_listener
    if(local_thickening_mouse_listener == None):
        local_thickening_mouse_listener = mouse.Listener(
            on_click=on_click
        )
        # 启动监听器
        local_thickening_mouse_listener.start()


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
        #重置状态数组
        is_copy_local_thickeningL = False
        local_thickening_objects_arrayL = []
        objects_array_indexL = -1
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
        # 重置状态数组
        is_copy_local_thickening = False
        local_thickening_objects_array = []
        objects_array_index = -1
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
    name = active_obj.name
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


    #将添加的鼠标监听删除
    global local_thickening_mouse_listener
    if (local_thickening_mouse_listener != None):
        local_thickening_mouse_listener.stop()
        local_thickening_mouse_listener = None

    #若未做任何操作,将初始化变为透明的物体变为不透明的实体
    initialModelColor()

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
    handle_obj = bpy.data.objects.get(name + "软耳膜附件Casting")
    label_obj = bpy.data.objects.get(name + "LabelPlaneForCasting")
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (label_obj != None):
        bpy.data.objects.remove(label_obj, do_unlink=True)



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

    # 删除支撑和排气孔中可能存在的对比物体
    soft_support_compare_obj = bpy.data.objects.get(name + "SoftSupportCompare")
    if (soft_support_compare_obj != None):
        bpy.data.objects.remove(soft_support_compare_obj, do_unlink=True)
    hard_support_compare_obj = bpy.data.objects.get(name + "ConeCompare")
    if (hard_support_compare_obj != None):
        bpy.data.objects.remove(hard_support_compare_obj, do_unlink=True)
    sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    if (sprue_compare_obj != None):
        bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)

    name = bpy.context.scene.leftWindowObj
    switch_selected_vertex_index_cur = None
    if (name == "右耳"):
        switch_selected_vertex_index_cur = switch_selected_vertex_index
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickening == True):
            objects_array_index = 0
        else:
            objects_array_index = -1
    elif (name == "左耳"):
        switch_selected_vertex_index_cur = switch_selected_vertex_indexL
        # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
        if (is_copy_local_thickeningL == True):
            objects_array_indexL = 0
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

        # 根据LocalThickCopy复制得到LocalThickCompare
        duplicate_obj1 = ori_obj.copy()
        duplicate_obj1.data = ori_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = name + "LocalThickCompare"
        bpy.context.scene.collection.objects.link(duplicate_obj1)
        if name=='右耳':
            moveToRight(duplicate_obj1)
        elif name=='左耳':
            moveToLeft(duplicate_obj1)

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

    # 添加监听
    global local_thickening_mouse_listener
    if (local_thickening_mouse_listener == None):
        local_thickening_mouse_listener = mouse.Listener(
            on_click=on_click
        )
        # 启动监听器
        local_thickening_mouse_listener.start()

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
    submit = None
    if name == '左耳':
        submit = left_is_submit
        # 重置状态数组
        is_copy_local_thickeningL = False
        local_thickening_objects_arrayL = []
        objects_array_indexL = -1
    else:
        submit = right_is_submit
        # 重置状态数组
        is_copy_local_thickening = False
        local_thickening_objects_array = []
        objects_array_index = -1
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

    #将加厚的区域应用拉普拉斯修改器应用
    if (submit == False):
        applySmooth()

    # 将当前模型的预览提交
    utils_re_color(name, (1, 0.319, 0.133))
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    bpy.ops.paint.vertex_color_set()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
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

    # 将添加的鼠标监听删除
    global local_thickening_mouse_listener
    if (local_thickening_mouse_listener != None):
        local_thickening_mouse_listener.stop()
        local_thickening_mouse_listener = None

    # 若未做任何操作,将初始化变为透明的物体变为不透明的实体
    initialModelColor()
    #切换到后续模块的时候,颜色显示改为RGB
    change_mat_mould(0)

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
            cur_obj = local_thickening_objects_array[objects_array_index]
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            objects_array_indexL = objects_array_indexL - 1
            # 从状态数组中获取替换物体,再将作为对比的物体删除
            cur_obj = local_thickening_objects_arrayL[objects_array_indexL]
        active_obj = bpy.data.objects[name]
        name = active_obj.name
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
        active_obj = bpy.data.objects[name]
        comparename = active_obj.name + "LocalThickCompare"
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
        # thickening_offset_borderwidth(0, borderWidth, True)
        thickening_reset()
        thickening_offset_borderwidth(offset, borderWidth, False)


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
            cur_obj = local_thickening_objects_array[objects_array_index]
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            objects_array_indexL = objects_array_indexL + 1
            # 从状态数组中获取替换物体,再将作为对比的物体删除
            cur_obj = local_thickening_objects_arrayL[objects_array_indexL]
        active_obj = bpy.data.objects[name]
        name = active_obj.name
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
        active_obj = bpy.data.objects[name]
        comparename = active_obj.name + "LocalThickCompare"
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
        # thickening_offset_borderwidth(0, borderWidth, True)
        thickening_reset()
        thickening_offset_borderwidth(offset, borderWidth, False)



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
    name = active_obj.name
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
    name = active_obj.name
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

    # 重新根据offset和borderwidth对模型进行加厚
    thickening_reset()
    initialTransparency()
    thickening_offset_borderwidth(offset, borderWidth, False)



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
        copyname = name + "LocalThickCopy"
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
    name = bpy.context.scene.leftWindowObj
    #将选中顶点取消选中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 当前激活物体
    cur_obj = bpy.data.objects.get(name)
    select_vert = []         #存储模型上选中的局部加厚区域顶点的索引
    if(cur_obj != None and cur_obj.type == 'MESH'):
        # 获取当前激活物体的网格数据
        me = cur_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                select_vert.append(vert)

        #扩大选中的顶点区域,便于拉普拉斯平滑修改器进行平滑
        add_select_vert = []
        select_vert_index = []  # 被选择顶点的顶点索引,主要是用于指定顶点组
        add_select_vert.extend(select_vert)
        for i in range(2):  # 将选中区域扩大两圈
            for vert in select_vert:
                for edge in vert.link_edges:
                    v1 = edge.verts[0]
                    v2 = edge.verts[1]
                    link_vert = v1 if v1 != vert else v2
                    if not (link_vert in select_vert):
                        add_select_vert.append(link_vert)
            for vert in add_select_vert:  # 根据扩大区域重置选择区域
                if not (vert in select_vert):
                    select_vert.append(vert)
        for vert in select_vert:  # 根据选中区域得到选中区域的顶点索引并存储到集合中
            select_vert_index.append(vert.index)
            vert.select_set(True)


        for _ in range(5):
            # Create a list to store new vertex positions
            new_positions = [None] * len(bm.verts)

            smooth_vert = [v for v in bm.verts if v.select]

            # Compute new vertex positions based on the Laplacian operator
            for v in smooth_vert:
                if not v.is_boundary:
                    avg_neighbor_pos = sum((e.other_vert(v).co for e in v.link_edges), v.co * 0) / len(v.link_edges)
                    new_positions[v.index] = v.co + 0.5 * (avg_neighbor_pos - v.co)
                else:
                    new_positions[v.index] = v.co

            # Update vertex positions
            for v in smooth_vert:
                v.co = new_positions[v.index]

        bm.to_mesh(me)
        bm.free()

        # 将选中顶点取消选中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')




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
        is_copy_local_thickeningL = False
        # 重置局部加厚中保存模型各个状态的数组
        local_thickening_objects_arrayL = []
        objects_array_indexL = -1

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
        is_copy_local_thickening = False
        # 重置局部加厚中保存模型各个状态的数组
        local_thickening_objects_array = []
        objects_array_index = -1

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
def thickening_offset_borderwidth(offset, borderWidth, reset):
    global objects_array_index
    global objects_array_indexL
    global local_thickening_objects_array
    global local_thickening_objects_arrayL

    objects_array_index_cur = None

    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        objects_array_index_cur = objects_array_index
    elif name == '左耳':
        objects_array_index_cur = objects_array_indexL

    if(borderWidth == 0):
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

    continuous_area = get_continuous_area(select_vert_index, borderWidth)

    # 执行加厚操作
    active_obj = bpy.data.objects[name]
    if active_obj.type == 'MESH':
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        # 获取厚度对比物体的网格激活物体
        copyname = name + "LocalThickCopy"
        ori_obj = bpy.data.objects[copyname]
        ori_me = ori_obj.data
        ori_bm = bmesh.new()
        ori_bm.from_mesh(ori_me)
        ori_bm.verts.ensure_lookup_table()

        # 状态数组中的当前物体,局部加厚参数更新时,在已加厚的基础上再根据参数加厚
        copyname = name + "LocalThickCompare"
        compare_obj = bpy.data.objects[copyname]
        thicking_me = compare_obj.data
        thciking_bm = bmesh.new()
        thciking_bm.from_mesh(thicking_me)
        thciking_bm.verts.ensure_lookup_table()

        # 依次处理每个连续区域,根据原区域的最高点与offset参数和borderWidth参数进行加厚
        area_index = 0
        while (area_index < len(continuous_area)):
            select_area = continuous_area[area_index]
            # 在已加厚的基础上再根据更新的参数进行加厚,寻找该连续区域加厚前的offset最大值
            max_offset = -inf
            if (objects_array_index_cur >= 0):
                for vert_index in select_area.inner_vert_index:
                    offset_temp = (thciking_bm.verts[vert_index].co - ori_bm.verts[vert_index].co).length  # 计算两个向量坐标之间的距离
                    if (offset_temp > max_offset):
                        max_offset = offset_temp
            if (max_offset == -inf):
                max_offset = 0

            # 先将选中顶点位置重置为原始位置再根据offset与max_offset重新加厚
            for vert_index in select_area.inner_vert_index:
                if (reset == False):
                    vert = bm.verts[vert_index]
                    vert.co = ori_bm.verts[vert_index].co
                    vert.co += vert.normal.normalized() * (offset + max_offset)
                else:
                    vert = bm.verts[vert_index]
                    vert.co = ori_bm.verts[vert_index].co
            for vert_index in select_area.out_vert_index:
                if (reset == False):
                    vert = bm.verts[vert_index]
                    vert.co = ori_bm.verts[vert_index].co
                    vert.co += vert.normal.normalized() * (offset + max_offset) * (
                                select_area.distance_dic[vert_index] / borderWidth)
                else:
                    vert = bm.verts[vert_index]
                    vert.co = ori_bm.verts[vert_index].co
            area_index += 1

        bm.to_mesh(me)
        bm.free()


# 局部加厚镜像
class Local_Thickening_Mirror(bpy.types.Operator):
    bl_idname = "obj.localthickeningjingxiang"
    bl_label = "将右耳加厚区域镜像到左耳"

    def invoke(self, context, event):
        bpy.context.scene.var = 30
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global switch_selected_vertex_index, switch_selected_vertex_indexL, operator_obj
        global left_is_submit, right_is_submit

        name = bpy.context.scene.leftWindowObj
        workspace = context.window.workspace.name

        # 只有在双窗口下执行镜像
        try:
            if workspace == '布局.001':

                active_obj = bpy.data.objects[name]
                name = active_obj.name
                if name == '左耳':
                    is_submit = left_is_submit
                else:
                    is_submit = right_is_submit

                # 判断是否提交修改,未提交时才可镜像
                if not is_submit:
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

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj_left
                    obj_left.select_set(True)

                    # 若存在LocalThickCopy,则将其删除并重新生成
                    all_objs = bpy.data.objects
                    for selected_obj in all_objs:
                        if (
                                selected_obj.name == tar_obj + "LocalThickCopy" or selected_obj.name == tar_obj + "LocalThickCompare"):
                            bpy.data.objects.remove(selected_obj, do_unlink=True)

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
                    duplicate_obj1.hide_set(True)
                    duplicate_obj1.hide_set(False)
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
                    active_obj = bpy.data.objects[name]  # 将右耳设置为当前激活物体
                    bpy.context.view_layer.objects.active = active_obj

                    # y轴镜像
                    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                             orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))

                    if obj_right.type == 'MESH':
                        left_me = obj_left.data
                        left_bm = bmesh.new()
                        left_bm.from_mesh(left_me)

                    print('before num', len(selected_vertex_index))

                    rotate_angle, height_difference = get_change_parameters()
                    print('rotate_angle', rotate_angle)
                    print('height_difference', height_difference)

                    # 计算投影点
                    for i in selected_vertex_index:
                        face_index = normal_ray_cast(i, rotate_angle, height_difference)
                        if face_index is not None:
                            left_bm.faces.ensure_lookup_table()
                            face = left_bm.faces[face_index]
                            face_verts = face.verts
                            for vert in face_verts:
                                if vert.index not in cast_vertex_index:
                                    cast_vertex_index.append(vert.index)

                    print('初始投射点', len(cast_vertex_index))

                    # 投射点数量过少
                    if len(cast_vertex_index) < len(selected_vertex_index) * 0.9:
                        # 填充中心未被选中的点
                        for index in cast_vertex_index:
                            left_bm.verts.ensure_lookup_table()
                            vert = left_bm.verts[index]
                            # 遍历这些顶点的相邻节点
                            for edge in vert.link_edges:
                                # 获取边的顶点
                                v1 = edge.verts[0]
                                v2 = edge.verts[1]
                                # 确保获取的顶点不是当前顶点
                                link_vert = v1 if v1 != vert else v2
                                if link_vert.index not in cast_vertex_index:
                                    edge_num = len(link_vert.link_edges)
                                    num = 0
                                    for edge in link_vert.link_edges:
                                        v1 = edge.verts[0]
                                        v2 = edge.verts[1]
                                        link = v1 if v1 != link_vert else v2
                                        if link.index in cast_vertex_index:
                                            num += 1
                                    if num >= edge_num - 3:
                                        cast_vertex_index.append(link_vert.index)

                        print('增加边缘点后', len(cast_vertex_index))

                    if len(cast_vertex_index) > len(selected_vertex_index) * 1.2:
                        # 去除边界点
                        for index in cast_vertex_index:
                            left_bm.verts.ensure_lookup_table()
                            vert = left_bm.verts[index]
                            vert.select_set(True)

                        border_vert_index = []
                        for index in cast_vertex_index:
                            left_bm.verts.ensure_lookup_table()
                            vert = left_bm.verts[index]
                            #    print('sel',vert.select)
                            # 遍历这些顶点的相邻节点
                            for edge in vert.link_edges:
                                # 获取边的顶点
                                v1 = edge.verts[0]
                                v2 = edge.verts[1]
                                # 确保获取的顶点不是当前顶点
                                link_vert = v1 if v1 != vert else v2
                                if link_vert.select == False and index not in border_vert_index:
                                    border_vert_index.append(index)

                        print('boder num', len(border_vert_index))
                        for index in border_vert_index:
                            if index in cast_vertex_index:
                                cast_vertex_index.remove(index)

                        print('去除边界点后', len(cast_vertex_index))

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
                    if name == '右耳':
                        offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
                        borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
                    else:
                        offset = bpy.context.scene.localThicking_offset_L  # 获取局部加厚面板中的偏移量参数
                        borderWidth = bpy.context.scene.localThicking_borderWidth_L  # 获取局部加厚面板中的边界宽度参数

                    # thickening_offset_borderwidth(0, 0, True)
                    thickening_reset()
                    thickening_offset_borderwidth(offset, borderWidth, False)

                    # 镜像还原
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj_left
                    obj_left.select_set(True)
                    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                             orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))

        except:
            print('镜像出错')

        return {'FINISHED'}


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
            # 重置状态数组
            local_thickening_objects_array = []  # 重置局部加厚中保存模型各个状态的数组
            objects_array_index = -1
            is_copy_local_thickening = False
        elif name == '左耳':
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

    __right_mouse_down = False        # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None              # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None          # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __initial_radius = None           # 圆环初始大小

    __object_mode = None             # 当前应该处于物体模式,该标志为True,需要切换为物体模式调用公共鼠标行为
    __vertex_paint_mode = None       # 当前应该处于顶点绘制模式,该标志为True,切换到顶点绘制模式调用颜色笔刷
    __flag = None

    def invoke(self, context, event):
        op_cls = Local_Thickening_AddArea

        bpy.context.scene.var = 5

        op_cls.__right_mouse_down = False                       # 初始化鼠标右键行为操作，通过鼠标右键控制圆环大小
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_radius = None

        op_cls.__object_mode = False
        op_cls.__vertex_paint_mode = False
        op_cls.__flag = False

        print("Local_Thickening_AddArea_invoke")

        bpy.ops.object.mode_set(mode='VERTEX_PAINT')            # 将默认的物体模式切换到顶点绘制模式
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")    # 调用自由线笔刷
        bpy.data.brushes["Draw"].color = (0.4, 1, 1)            # 设置笔刷颜色,该颜色用于扩大局部加厚区域
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'      # 衰减设置为常量
        bpy.ops.object.mode_set(mode='OBJECT')                  # 将默认的顶点绘制模式切换到物体模式
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")    # 切换到选择模式，执行公共鼠标行为

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_AddArea
        name = bpy.context.scene.leftWindowObj
        global left_mouse_release
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 5):
            if (left_mouse_release):                            # 鼠标左键松开后,若局部加厚区域发生变化后,执行自动加厚
                if(isSelectedAreaChanged()):
                    auto_thickening()
                    left_mouse_release = False

            if (is_mouse_on_object(context, event)):            # 鼠标位于模型上的时候
                if (is_changed(context, event)):                # 鼠标从空白处移动到模型上,切换到顶点绘制模式调用颜色笔刷
                    if(not left_mouse_press):
                        if bpy.context.mode == "OBJECT":
                            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                        op_cls.__vertex_paint_mode = False
                        op_cls.__object_mode = False

                        bpy.context.scene.tool_settings.sculpt.show_brush = True
                        if name == '右耳':  # 设置圆环大小
                            radius = context.scene.localThicking_circleRedius
                        else:
                            radius = context.scene.localThicking_circleRedius_L
                        bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例
                    else:
                        op_cls.__vertex_paint_mode = True
                        op_cls.__object_mode = False

                if (op_cls.__vertex_paint_mode == True and not left_mouse_press):
                    op_cls.__vertex_paint_mode = False
                    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")

                    bpy.context.scene.tool_settings.sculpt.show_brush = True
                    if name == '右耳':  # 设置圆环大小
                        radius = context.scene.localThicking_circleRedius
                    else:
                        radius = context.scene.localThicking_circleRedius_L
                    bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                    bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例

                if event.type == 'RIGHTMOUSE':      # 点击鼠标右键，改变区域选取圆环的大小
                    if event.value == 'PRESS':      # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        op_cls.__right_mouse_down = True
                        op_cls.__initial_radius = bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False   # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小

                elif event.type == 'MOUSEMOVE':
                    if op_cls.__right_mouse_down:    # 鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)))
                        op = 1                                                     # 上移扩大，下移缩小
                        if (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            op = -1
                        radius = min(max(op_cls.__initial_radius+dis*op, 50), 200)   # 圆环大小  [50,200]
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = radius
                        if name == '右耳':
                            context.scene.localThicking_circleRedius = radius       # 保存改变的圆环大小
                        else:
                            context.scene.localThicking_circleRedius_L = radius
                    showThickness(context, event)     # 添加厚度显示,鼠标位于模型上时，显示模型上鼠标指针处的厚度

            # 鼠标不在模型上的时候,从模型上切换到空白区域的时候,切换到顶点绘制模式调用颜色笔刷,移除厚度显示
            elif (not is_mouse_on_object(context, event)):
                if is_changed(context, event):
                    if(not left_mouse_press):
                        bpy.context.scene.tool_settings.sculpt.show_brush = False
                        op_cls.__vertex_paint_mode = False
                        op_cls.__object_mode = False
                        MyHandleClass.remove_handler()
                    else:
                        op_cls.__object_mode = True
                        op_cls.__vertex_paint_mode = False

                if (op_cls.__object_mode == True and not left_mouse_press):
                    bpy.context.scene.tool_settings.sculpt.show_brush = False
                    op_cls.__object_mode = False
                    MyHandleClass.remove_handler()

                if (op_cls.__object_mode == False and bpy.context.mode == 'PAINT_VERTEX' and event.mouse_x > 60 and
                        (left_mouse_press or middle_mouse_press or right_mouse_press)):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

                if event.value == 'RELEASE' and op_cls.__right_mouse_down:  # 鼠标不在模型上,圆环移到物体外，不再改变圆环大小
                    op_cls.__right_mouse_down = False

            # 切换到镜像布局的时候,自动保存选中的顶点,用于镜像操作
            if (context.window.workspace.name == '布局.001'):
                saveSelected()

            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class Local_Thickening_ReduceArea(bpy.types.Operator):
    bl_idname = "obj.localthickeningreducearea"
    bl_label = "减小局部加厚区域"

    __right_mouse_down = False                               # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None                                     # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None                                 # 点击鼠标右键的初始位置
    __initial_mouse_y = None
    __initial_radius = None                                  # 圆环初始大小

    def invoke(self, context, event):
        op_cls = Local_Thickening_ReduceArea

        bpy.context.scene.var = 6

        op_cls.__right_mouse_down = False                    # 初始化鼠标右键行为操作，通过鼠标右键控制圆环大小
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        op_cls.__initial_radius = None

        print("Local_Thickening_ReduceArea_invoke")
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')         # 将默认的物体模式切换到顶点绘制模式
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw") # 设置笔刷颜色,该颜色用于缩小局部加厚区域
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)       # 调用自由线笔刷
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'   # 衰减设置为常量
        bpy.ops.object.mode_set(mode='OBJECT')               # 将默认的顶点绘制模式切换到物体模式
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box") # 切换到选择模式，执行公共鼠标行为

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_ReduceArea
        name = bpy.context.scene.leftWindowObj
        global left_mouse_release
        global left_mouse_press
        global middle_mouse_press
        global right_mouse_press

        override1 = getOverride()
        area = override1['area']

        if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 6):
            if (left_mouse_release):                                     #鼠标左键松开后,若局部加厚区域发生变化后,执行自动加厚
                if (isSelectedAreaChanged()):
                    auto_thickening()
                    left_mouse_release = False
            if (is_mouse_on_object(context, event)):
                if (is_changed(context, event)):
                    if bpy.context.mode == "OBJECT":                      # 将默认的物体模式切换到顶点绘制模式,调用颜色绘制笔刷
                        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                    if name == '右耳':                                     # 设置圆环初始大小
                        radius = context.scene.localThicking_circleRedius
                    else:
                        radius = context.scene.localThicking_circleRedius_L
                    bpy.context.scene.tool_settings.unified_paint_settings.size = int(radius)
                    bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例
                if event.type=='RIGHTMOUSE':                               #点击鼠标右键，改变区域选取圆环的大小
                    if event.value=='PRESS':                               #按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x=event.mouse_region_x
                        op_cls.__initial_mouse_y=event.mouse_region_y
                        op_cls.__right_mouse_down=True
                        op_cls.__initial_radius = bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size
                    elif event.value=='RELEASE':
                        op_cls.__right_mouse_down=False                    #松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                elif event.type == 'MOUSEMOVE':
                    if op_cls.__right_mouse_down:                          #鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y=event.mouse_region_y
                        op_cls.__now_mouse_x=event.mouse_region_x
                        dis=int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)))
                        # 上移扩大，下移缩小
                        op = 1
                        if (op_cls.__now_mouse_y < op_cls.__initial_mouse_y):
                            op = -1
                        # 设置圆环大小范围【50，200】
                        radius = min(max(op_cls.__initial_radius+dis*op,50),200)
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = radius
                        # 保存改变的圆环大小
                        if name == '右耳':
                            context.scene.localThicking_circleRedius = radius
                        else:
                            context.scene.localThicking_circleRedius_L = radius
                    showThickness(context, event)                          # 添加厚度显示,鼠标位于模型上时，显示模型上鼠标指针处的厚度
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                if bpy.context.mode == "PAINT_VERTEX":                     # 将默认的顶点绘制模式切换到物体模式,使用公共鼠标行为
                    bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                MyHandleClass.remove_handler()                             # 鼠标不在模型上时，移除厚度显示
            
            # 圆环移到物体外，不再改变圆环大小
            elif(not is_mouse_on_object(context,event)):
                if event.value == 'RELEASE' and op_cls.__right_mouse_down:
                    op_cls.__right_mouse_down=False

            # 切换到镜像布局的时候,自动保存选中的顶点,用于镜像操作
            if (context.window.workspace.name == '布局.001'):
                saveSelected()

            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class Local_Thickening_Thicken(bpy.types.Operator):
    bl_idname = "obj.localthickeningthick"
    bl_label = "对选中的加厚区域进行加厚,透明预览"

    def invoke(self, context, event):

        bpy.context.scene.var = 7

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
                duplicate_obj.name = "localThick_array_objects"
                local_thickening_objects_array.append(duplicate_obj)
                objects_array_index = objects_array_index + 1
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
            thickening_offset_borderwidth(offset, borderWidth, False)

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
            local_thickening_objects_array.append(duplicate_obj1)
            objects_array_index = objects_array_index + 1
            bpy.data.objects.remove(duplicate_obj, do_unlink=True)
            bpy.context.view_layer.objects.active = active_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            initialTransparency()

            # 更换参照物
            thicking_temp_obj = local_thickening_objects_array[objects_array_index]
            name = active_obj.name
            for selected_obj in bpy.data.objects:
                if (selected_obj.name == name + "LocalThickCompare"):
                    bpy.data.objects.remove(selected_obj, do_unlink=True)
            duplicate_obj = thicking_temp_obj.copy()
            duplicate_obj.data = thicking_temp_obj.data.copy()
            duplicate_obj.name = active_obj.name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            elif name == '左耳':
                moveToLeft(duplicate_obj)

            # 对选中的局部加厚区域,更新完参照物之后,在此基础上根据offset参数与borderWidth参数进行加厚
            # thickening_offset_borderwidth(0, borderWidth, True)
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth, False)


            # 解决模型重叠问题
            active_obj = bpy.data.objects[name]
            comparename = active_obj.name + "LocalThickCompare"
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
                duplicate_obj.name = "localThick_array_objects"
                local_thickening_objects_arrayL.append(duplicate_obj)
                objects_array_indexL = objects_array_indexL + 1
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
            thickening_offset_borderwidth(offset, borderWidth, False)


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
            local_thickening_objects_arrayL.append(duplicate_obj1)
            objects_array_indexL = objects_array_indexL + 1
            bpy.data.objects.remove(duplicate_obj, do_unlink=True)
            bpy.context.view_layer.objects.active = active_obj
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            initialTransparency()

            # 更换参照物
            thicking_temp_obj = local_thickening_objects_arrayL[objects_array_indexL]
            name = active_obj.name
            for selected_obj in bpy.data.objects:
                if (selected_obj.name == name + "LocalThickCompare"):
                    bpy.data.objects.remove(selected_obj, do_unlink=True)
            duplicate_obj = thicking_temp_obj.copy()
            duplicate_obj.data = thicking_temp_obj.data.copy()
            duplicate_obj.name = active_obj.name + "LocalThickCompare"
            bpy.context.collection.objects.link(duplicate_obj)
            if name == '右耳':
                moveToRight(duplicate_obj)
            elif name == '左耳':
                moveToLeft(duplicate_obj)

            # 对选中的局部加厚区域,更新完参照物之后,在此基础上根据offset参数与borderWidth参数进行加厚
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth, False)



            # 解决模型重叠问题
            active_obj = bpy.data.objects[name]
            comparename = active_obj.name + "LocalThickCompare"
            compare_obj = bpy.data.objects[comparename]
            compare_obj.hide_set(True)
            compare_obj.hide_set(False)


        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if (bpy.context.scene.var == 7):
            if (is_mouse_on_object(context, event)):
                if event.type == 'MOUSEMOVE':
                    showThickness(context, event)      # 鼠标位于模型上时，显示模型上鼠标指针处位置的厚度
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                MyHandleClass.remove_handler()         # 鼠标不在模型上时，移除厚度显示
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


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
        #将模型上加厚的区域应用拉普拉斯平滑函数,优化平滑效果
        applySmooth()

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

        active_obj = bpy.data.objects[name]
        name = active_obj.name
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


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_JiaHou, separator=True, group=False)
    bpy.utils.register_tool(MyTool3_JiaHou, separator=True, group=False, after={MyTool_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool5_JiaHou, separator=True, group=False, after={MyTool3_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool7_JiaHou, separator=True, group=False, after={MyTool5_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool9_JiaHou, separator=True, group=False, after={MyTool7_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool11_JiaHou,separator=True, group=False,after={MyTool9_JiaHou.bl_idname})

    bpy.utils.register_tool(MyTool2_JiaHou, separator=True, group=False)
    bpy.utils.register_tool(MyTool4_JiaHou, separator=True, group=False, after={MyTool2_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool6_JiaHou, separator=True, group=False, after={MyTool4_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool8_JiaHou, separator=True, group=False, after={MyTool6_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool10_JiaHou, separator=True, group=False, after={MyTool8_JiaHou.bl_idname})
    bpy.utils.register_tool(MyTool12_JiaHou,separator=True, group=False,after={MyTool10_JiaHou.bl_idname})


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