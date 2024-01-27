from multiprocessing import context
import bpy
from .tool import *
from bpy.types import WorkSpaceTool
from math import *
from mathutils import Vector
from bpy_extras import view3d_utils
from enum import auto
from ssl import DER_cert_to_PEM_cert
import mathutils
import bmesh
import re
from datetime import *
import sys

is_copy_local_thickening = False  # 判断加厚状态，值为True时为未提交，值为False为提交后或重置后(未处于加厚预览状态)
                                  #主要用于加厚按钮中，第一次加厚初始化状态数组。局部加厚模块切换时的状态判断
prev_on_object = False  # 全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体

local_thickening_objects_array = []  # 保存局部加厚功能中每一步加厚时物体的状态，用于单步撤回
objects_array_index = -1  # 数组指针，指向数组中当前需要访问状态的元素，用于单步撤回操作,指向数组中与当前激活物体相同的对象

prev_localthick_area_index = []  # 保存上次局部加厚的顶点,主要用于判断选中的局部加厚区域是否改变,在定时器的自动加厚中使用

is_timer_start = False  # 判断定时器是否已启动,若已经启动,则扩大或缩小局部加厚的invoke中不再添加定时器

switch_selected_vertex_index = []  # 用于保存当前模型的局部加厚区域,从其他模式切换到局部加厚模式时根据该区域初始化模型


is_submit = False           #判断是否提交过   主要用于局部加厚模块切换时颜色顶点索引的保存


# 获取区域和空间，鼠标行为切换相关
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


# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    active_obj = context.active_object

    is_on_object = False  # 初始化变量

    if context.area:
        context.area.tag_redraw()

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
    active_obj = context.active_object

    curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
    global prev_on_object  # 之前鼠标是否在物体上

    if context.area:
        context.area.tag_redraw()

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
    mat = newShader("Yellow")  # 创建材质
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.data.materials['Transparency'].blend_method = "BLEND"
    bpy.data.materials["Transparency"].node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2



# 前面的打磨功能切换到 局部加厚模式时
def frontToLocalThickening():
    global switch_selected_vertex_index
    global objects_array_index
    global is_copy_local_thickening
    # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
    if (is_copy_local_thickening == True):
        objects_array_index = 0
    else:
        objects_array_index = -1

    # 若存在LocalThickCopy,则将其删除并重新生成
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳LocalThickCopy" or selected_obj.name == "右耳LocalThickCompare"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    # 根据当前激活物体复制得到用于重置的LocalThickCopy和初始时的参照物LocalThickCompare
    active_obj = bpy.context.active_object
    name = active_obj.name
    duplicate_obj1 = active_obj.copy()
    duplicate_obj1.data = active_obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LocalThickCompare"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    duplicate_obj1.hide_set(False)
    duplicate_obj2 = active_obj.copy()
    duplicate_obj2.data = active_obj.data.copy()
    duplicate_obj2.animation_data_clear()
    duplicate_obj2.name = name + "LocalThickCopy"
    bpy.context.collection.objects.link(duplicate_obj2)
    duplicate_obj2.hide_set(True)  # 将LocalThickCopy隐藏
    active_obj = bpy.data.objects[name]  # 将右耳设置为当前激活物体
    bpy.context.view_layer.objects.active = active_obj

    # 根据switch_selected_vertex中保存的模型上的已选中顶点,将其置为局部加厚中已选中顶点并根据offset和borderWidth进行加厚,进行初始化处理
    active_obj = bpy.context.active_object
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
        # 绘制局部加厚区域圆环
        draw_border_curve()
    # 从当前的局部加厚切换到前面的打磨时

class Local_Thickening_Mirror(bpy.types.Operator):
    bl_idname = "obj.jingxiang"
    bl_label = "加厚镜像"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        # # 若存在LocalThickCopy,则将其删除并重新生成
        # all_objs = bpy.data.objects
        # for selected_obj in all_objs:
        #     if (selected_obj.name == "右耳LocalThickCopy" or selected_obj.name == "右耳LocalThickCompare"):
        #         bpy.data.objects.remove(selected_obj, do_unlink=True)
        # # 根据当前激活物体复制得到用于重置的LocalThickCopy和初始时的参照物LocalThickCompare
        # active_obj = bpy.context.active_object
        # name = active_obj.name
        # duplicate_obj1 = active_obj.copy()
        # duplicate_obj1.data = active_obj.data.copy()
        # duplicate_obj1.animation_data_clear()
        # duplicate_obj1.name = name + "LocalThickCompare"
        # bpy.context.collection.objects.link(duplicate_obj1)
        # duplicate_obj1.hide_set(True)
        # duplicate_obj1.hide_set(False)
        # duplicate_obj2 = active_obj.copy()
        # duplicate_obj2.data = active_obj.data.copy()
        # duplicate_obj2.animation_data_clear()
        # duplicate_obj2.name = name + "LocalThickCopy"
        # bpy.context.collection.objects.link(duplicate_obj2)
        # duplicate_obj2.hide_set(True)  # 将LocalThickCopy隐藏
        # active_obj = bpy.data.objects[name]  # 将右耳设置为当前激活物体
        # bpy.context.view_layer.objects.active = active_obj

        initialTransparency()
        offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
        borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数

        thickening_offset_borderwidth(0, 0, True)
        thickening_offset_borderwidth(offset, borderWidth, False)

        # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
        draw_border_curve()
        # 绘制局部加厚区域圆环
        draw_border_curve()

        return {'FINISHED'}

def frontFromLocalThickening():
    # 保存模型上选中的局部加厚区域中的顶点索引,同样保存模型上已选中点放在submit功能模块中
    global is_submit
    global switch_selected_vertex_index
    # 未提交时,保存局部加厚区域中顶点索引。若已提交,则submit按钮中已经保存该顶点索引,无序置空在重新确定顶点索引
    if (is_submit == False):
        switch_selected_vertex_index = []
        active_obj = bpy.context.active_object
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
    active_obj = bpy.context.active_object  # 将当前激活的模型替换为执行加厚操作之前的模型
    name = bpy.context.object.name
    copyname = name + "LocalThickCopy"
    ori_obj = bpy.data.objects[copyname]
    bpy.data.objects.remove(active_obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj

    # 删除场景中局部加厚相关的用于重置的LocalThickCopy和初始时的参照物LocalThickCompare
    selected_objs = bpy.data.objects
    active_object = bpy.context.active_object
    name = active_object.name
    for selected_obj in selected_objs:
        if (selected_obj.name == name + "LocalThickCompare" or selected_obj.name == name + "LocalThickCopy"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 删除局部加厚中的圆环
    draw_border_curve()


# 后面的其他功能切换到局部加厚模式时
def backToLocalThickening():
    global switch_selected_vertex_index
    global objects_array_index
    global is_copy_local_thickening
    # 进入局部加厚模块时,是否已经加厚过,初始化了状态数组的第一个模型
    if (is_copy_local_thickening == True):
        objects_array_index = 0
    else:
        objects_array_index = -1

    exist_LocalThickCopy = False

    # 判断场景中是否存在LocalThickCopy,若存在则利用该模型生成LocalThickCompare并根据LocalThickCopy进行加厚
    # 若场景中不存在LocalThickCopy,则说明未经过局部加厚操作,获取打磨模块中的DamoCopy并生成LocalThickCopy,Compare和激活物体
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳LocalThickCopy"):
            exist_LocalThickCopy = True
    if (exist_LocalThickCopy):
        # 根据LocalThickCopy复制出来一份物体用来替换当前激活物体
        name = bpy.context.active_object.name
        active_obj = bpy.data.objects[name]
        copyname = name + "LocalThickCopy"
        ori_obj = bpy.data.objects[copyname]
        bpy.data.objects.remove(active_obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        # 根据LocalThickCopy复制得到LocalThickCompare
        duplicate_obj1 = ori_obj.copy()
        duplicate_obj1.data = ori_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = name + "LocalThickCompare"
        bpy.context.scene.collection.objects.link(duplicate_obj1)

        # 根据switch_selected_vertex中保存的模型上的已选中顶点,将其置为局部加厚中已选中顶点并根据offset和borderWidth进行加厚,进行初始化处理
        active_obj = bpy.context.active_object
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
            # 绘制局部加厚区域圆环
            draw_border_curve()
    else:
        active_obj = bpy.context.active_object
        name = bpy.context.active_object.name
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
        # 删除当前激活物体并根据DamoCopy重新生成当前激活物体
        bpy.data.objects.remove(active_obj, do_unlink=True)
        duplicate_obj2 = ori_obj.copy()
        duplicate_obj2.data = ori_obj.data.copy()
        duplicate_obj2.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate_obj2)
        duplicate_obj2.name = name
        bpy.context.view_layer.objects.active = duplicate_obj2


# 从当前的局部加厚切换到后面的其他功能时
def backFromLocalThickening():
    # 保存模型上选中的局部加厚区域中的顶点索引,同样保存模型上已选中点放在submit功能模块中
    global is_submit
    global switch_selected_vertex_index
    # 未提交时,保存局部加厚区域中顶点索引。若已提交,则submit按钮中已经保存该顶点索引,无序置空在重新确定顶点索引
    if (is_submit == False):
        switch_selected_vertex_index = []
        active_obj = bpy.context.active_object
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

    # 将当前模型的预览提交
    initialModelColor()
    if bpy.context.mode == "OBJECT":
        bpy.ops.paint.vertex_paint_toggle()
    bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    bpy.ops.paint.vertex_color_set()
    if bpy.context.mode == "PAINT_VERTEX":
        bpy.ops.paint.vertex_paint_toggle()
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 删除场景中局部加厚相关的初始时的参照物LocalThickCompare
    selected_objs = bpy.data.objects
    active_object = bpy.context.active_object
    name = active_object.name
    for selected_obj in selected_objs:
        if (selected_obj.name == name + "LocalThickCompare"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)

    # 删除局部加厚中的圆环
    draw_border_curve()

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳LocalThickLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LocalThickLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)

# 获取当前激活物体上局部加厚区域是否改变
def isSelectedAreaChanged():
    global prev_localthick_area_index
    flag = False
    selected_area_vertex_index = []
    active_obj = bpy.context.active_object
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


# 判断鼠标是否在模型的局部加厚区域上
def isOnLocalThickArea(context, event):
    is_on_localthick_area = False

    # 获取鼠标光标的区域坐标                                                             鼠标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
    # 单击功能区上的“窗口”区域中的
    # 获取信息和“三维视口”空间中的空间信息
    region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
    # 确定朝向鼠标光标位置发出的光线的方向
    ray_dir = view3d_utils.region_2d_to_vector_3d(region, space.region_3d, mv)
    # 确定朝向鼠标光标位置发出的光线源
    ray_orig = view3d_utils.region_2d_to_origin_3d(region, space.region_3d, mv)
    # 光线起点
    start = ray_orig
    # 光线终点
    end = ray_orig + ray_dir

    # 确定光线和对象的相交                                                               物体
    # 交叉判定在对象的局部坐标下进行
    # 将光线的起点和终点转换为局部坐标
    active_obj = context.active_object
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
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT" or active_obj.mode == "VERTEX_PAINT"):
            me = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            # 构建BVH树
            outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
            co, _, fidx, dis = outertree.ray_cast(mwi_start, mwi_dir)
            # 网格和光线碰撞时   fidx代表鼠标射线与相交面的索引
            if fidx is not None:
                bm.faces.ensure_lookup_table()
                bm.faces[fidx].material_index = 1
                color_lay = bm.verts.layers.float_color["Color"]
                for vert in bm.faces[fidx].verts:
                    colvert = vert[color_lay]
                    if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                        is_on_localthick_area = True
                        break
    return is_on_localthick_area


def showThickness(context, event):
    # 获取鼠标光标的区域坐标                                                             鼠标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
    # 单击功能区上的“窗口”区域中的
    # 获取信息和“三维视口”空间中的空间信息
    region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
    # 确定朝向鼠标光标位置发出的光线的方向
    ray_dir = view3d_utils.region_2d_to_vector_3d(region, space.region_3d, mv)
    # 确定朝向鼠标光标位置发出的光线源
    ray_orig = view3d_utils.region_2d_to_origin_3d(region, space.region_3d, mv)
    # 光线起点
    start = ray_orig
    # 光线终点
    end = ray_orig + ray_dir

    # 确定光线和对象的相交                                                               物体
    # 交叉判定在对象的局部坐标下进行
    # 将光线的起点和终点转换为局部坐标
    active_obj = context.active_object
    mwi = active_obj.matrix_world.inverted()
    # 光线起点
    mwi_start = mwi @ start
    # 光线终点
    mwi_end = mwi @ end
    # 光线方向
    mwi_dir = mwi_end - mwi_start
    # 获取活动对象
    active_obj = bpy.context.active_object  # 操作物体
    name = active_obj.name
    copyname = name + "LocalThickCopy"  # TODO    根据最终参照物体替换
    ori_obj = bpy.data.objects[copyname]  # 作为厚度对比的源物体
    orime = ori_obj.data
    oribm = bmesh.new()
    oribm.from_mesh(orime)
    # 确保活动对象的类型是网格
    if active_obj.type == 'MESH':
        # 确保活动对象可编辑
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT" or active_obj.mode == "VERTEX_PAINT"):
            # 获取网格数据
            me = active_obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            # bm.transform(active_obj.matrix_world)
            # 构建BVH树
            outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
            # innertree = mathutils.bvhtree.BVHTree.FromBMesh(oribm)
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

                    # 先根据LocalThickCopy,将当前激活模型加厚区域打回,在根据offset和borderwidth重新加厚


def auto_thickening():
    global is_submit
    is_submit = False


    initialTransparency()
    offset = bpy.context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
    borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数

    # 将选中的局部加厚中加厚的顶点打回
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        name = bpy.context.active_object.name
        copyname = name + "LocalThickCopy"  # TODO    根据最终参照物体替换
        ori_obj = bpy.data.objects[copyname]
        ori_me = ori_obj.data
        ori_bm = bmesh.new()
        ori_bm.from_mesh(ori_me)
        ori_bm.verts.ensure_lookup_table()
        for vert in bm.verts:
            vert.co = ori_bm.verts[vert.index].co
        bm.to_mesh(me)
        bm.free()

    thickening_offset_borderwidth(0, 0, True)
    thickening_offset_borderwidth(offset, borderWidth, False)

    # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
    bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
    draw_border_curve()


# offset和borderWidth为面板参数,reset为将该局部加厚区域顶点重置会原模型高度
def thickening_offset_borderwidth(offset, borderWidth, reset):
    global objects_array_index
    global local_thickening_objects_array

    # 执行加厚操作
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        # 获取当前激活物体的网格数据
        me = active_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        # 获取厚度对比物体的网格激活物体
        name = bpy.context.active_object.name
        copyname = name + "LocalThickCopy"  # TODO    根据最终参照物体替换
        ori_obj = bpy.data.objects[copyname]
        ori_me = ori_obj.data
        ori_bm = bmesh.new()
        ori_bm.from_mesh(ori_me)
        ori_bm.verts.ensure_lookup_table()

        select_vert = []  # 被选择的顶点
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                select_vert.append(vert)

        # 将选中的顶点根据连续性保存到对象数组中,数组中每个对象中存储每个连续区域划分后的数据,包括边界点,内外圈顶点
        continuous_area = get_continuous_area(select_vert, color_lay, borderWidth)

        # 状态数组中的当前物体,局部加厚参数更新时,在已加厚的基础上再根据参数加厚
        copyname = name + "LocalThickCompare"  # TODO    根据最终参照物体替换
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
            if (objects_array_index >= 0):
                for vert in select_area.inner_vert:
                    offset_temp = (
                                thciking_bm.verts[vert.index].co - ori_bm.verts[vert.index].co).length  # 计算两个向量坐标之间的距离
                    if (offset_temp > max_offset):
                        max_offset = offset_temp
            if (max_offset == -inf):
                max_offset = 0

            # 先将选中顶点位置重置为原始位置再根据offset与max_offset重新加厚
            for vert in select_area.inner_vert:
                if (reset == False):
                    vert.co = ori_bm.verts[vert.index].co
                    vert.co += vert.normal.normalized() * (offset + max_offset)
                else:
                    vert.co = ori_bm.verts[vert.index].co
            for vert in select_area.out_vert:
                if (reset == False):
                    vert.co = ori_bm.verts[vert.index].co
                    vert.co += vert.normal.normalized() * (offset + max_offset) * (
                                select_area.distance_dic[vert.index] / borderWidth)
                else:
                    vert.co = ori_bm.verts[vert.index].co
            area_index += 1

        # 选择局部加厚区域中的顶点,不知为何执行get_continuous_area方法后,select_vert集合为空,需要重新选择
        for vert in bm.verts:
            colvert = vert[color_lay]
            if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                select_vert.append(vert)

        # 扩大选中的顶点区域,便于拉普拉斯平滑修改器进行平滑
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

        bm.to_mesh(me)
        bm.free()

        # 获取当前活动对象
        obj = bpy.context.active_object
        # 创建一个新的顶点组,并将选中的顶点指定到新创建的顶点组中
        new_vertex_group = obj.vertex_groups.get("MyVertexGroup")
        if (obj.vertex_groups.get("MyVertexGroup") == None):
            new_vertex_group = obj.vertex_groups.new(name="MyVertexGroup")
        for vert_index in select_vert_index:
            new_vertex_group.add([vert_index], 1, 'ADD')

        # 创建拉普拉斯平滑修改器,并指定作用域新创建的顶点组,应用修改器,将加厚的区域进行平滑
        modifier_name = "LaplacianSmooth"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:  # TODO  优化：   将创建修改器放到加厚的invoke中，应用修改器放到提交中
                target_modifier = modifier
        if (target_modifier == None):
            bpy.ops.object.modifier_add(type='LAPLACIANSMOOTH')
        bpy.context.active_object.modifiers["LaplacianSmooth"].vertex_group = "MyVertexGroup"
        bpy.context.active_object.modifiers["LaplacianSmooth"].lambda_border = 5
        bpy.context.active_object.modifiers["LaplacianSmooth"].lambda_factor = 10
        # bpy.ops.object.modifier_apply(modifier="LaplacianSmooth")                       #submit提交或者扩大,缩小区域时apply应用,扩大区域或缩小区域时,清除修改器,防止卡顿
        # 删除创建的顶点组
        # vertex_group_to_delete = obj.vertex_groups.get("MyVertexGroup")
        # obj.vertex_groups.remove(vertex_group_to_delete)


# 根据选中区域绘制出边界
def draw_border_curve():
    # 在这里就去判断区域
    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        # 获取当前激活物体的网格数据
        me = active_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        select_vert = []  # 被选择的顶点
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            if round(colvert.x, 3) != 1.000 and round(colvert.y, 3) != 0.319 and round(colvert.z, 3) != 0.133:
                select_vert.append(vert)

        # 将选中的顶点根据连续性保存到对象数组中,数组中每个对象中存储每个连续区域划分后的数据,包括边界点,内外圈顶点
        borderWidth = bpy.context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
        continuous_area = get_continuous_area(select_vert, color_lay, borderWidth)
        bpy.context.view_layer.objects.active = active_obj

        for obj in bpy.data.objects:
            pattern = r'BorderCurveObject'
            if re.match(pattern, obj.name):
                active_obj = bpy.context.active_object
                bpy.context.view_layer.objects.active = obj
                red_material = bpy.data.materials.new(name="Red")
                red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                bpy.context.active_object.data.materials.append(red_material)
                bpy.context.view_layer.objects.active = active_obj


def backup(context):
    global local_thickening_objects_array
    global objects_array_index
    if (objects_array_index > 0):
        # 设置替换数组中指针的指向
        objects_array_index = objects_array_index - 1
        # 从状态数组中获取替换物体,再将作为对比的物体删除
        cur_obj = local_thickening_objects_array[objects_array_index]
        active_obj = bpy.context.active_object
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
        active_obj = bpy.context.active_object
        comparename = active_obj.name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        compare_obj.hide_set(True)
        compare_obj.hide_set(False)

        offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
        borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
        # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
        thickening_offset_borderwidth(0, borderWidth, True)
        thickening_offset_borderwidth(offset, borderWidth, False)
        # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
        draw_border_curve()  # 重新绘制边界


def forward(context):
    global local_thickening_objects_array
    global objects_array_index
    size = len(local_thickening_objects_array)
    if (objects_array_index + 1 < size):
        # 设置替换数组中指针的指向
        objects_array_index = objects_array_index + 1
        # 从状态数组中获取替换物体,再将作为对比的物体删除
        cur_obj = local_thickening_objects_array[objects_array_index]
        active_obj = bpy.context.active_object
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
        active_obj = bpy.context.active_object
        comparename = active_obj.name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        compare_obj.hide_set(True)
        compare_obj.hide_set(False)

        offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
        borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
        # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
        thickening_offset_borderwidth(0, borderWidth, True)
        thickening_offset_borderwidth(offset, borderWidth, False)
        # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
        draw_border_curve()  # 重新绘制边界


class BackUp(bpy.types.Operator):
    bl_idname = "obj.undo"
    bl_label = "撤销"

    def execute(self, context):
        # 局部加厚模式下的单步撤回
        # if(bpy.context.scene.var == 5 or bpy.context.scene.var == 6 or bpy.context.scene.var == 7 or bpy.context.scene.var == 8 or bpy.context.scene.var == 9):
        # 通过bpy.context.scene.var变量判断目前处于哪个模块下，打磨，局部加厚等
        bpy.context.scene.var = 10
        if (True):
            global local_thickening_objects_array
            global objects_array_index
            if (objects_array_index > 0):
                # 设置替换数组中指针的指向
                objects_array_index = objects_array_index - 1
                # 从状态数组中获取替换物体,再将作为对比的物体删除
                cur_obj = local_thickening_objects_array[objects_array_index]
                active_obj = bpy.context.active_object
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
                active_obj = bpy.context.active_object
                comparename = active_obj.name + "LocalThickCompare"
                compare_obj = bpy.data.objects[comparename]
                compare_obj.hide_set(True)
                compare_obj.hide_set(False)

                offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
                borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
                # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
                thickening_offset_borderwidth(0, borderWidth, True)
                thickening_offset_borderwidth(offset, borderWidth, False)
                # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
                bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
                draw_border_curve()  # 重新绘制边界

        return {'FINISHED'}


class Forward(bpy.types.Operator):
    bl_idname = "obj.redo"
    bl_label = "重做"

    def execute(self, context):
        # 局部加厚模式下的单步重做
        # if(bpy.context.scene.var == 5 or bpy.context.scene.var == 6 or bpy.context.scene.var == 7 or bpy.context.scene.var == 8 or bpy.context.scene.var == 9):
        # 通过bpy.context.scene.var变量判断目前处于哪个模块下，打磨，局部加厚等
        bpy.context.scene.var = 11
        if (True):
            global local_thickening_objects_array
            global objects_array_index
            size = len(local_thickening_objects_array)
            if (objects_array_index + 1 < size):
                # 设置替换数组中指针的指向
                objects_array_index = objects_array_index + 1
                # 从状态数组中获取替换物体,再将作为对比的物体删除
                cur_obj = local_thickening_objects_array[objects_array_index]
                active_obj = bpy.context.active_object
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
                active_obj = bpy.context.active_object
                comparename = active_obj.name + "LocalThickCompare"
                compare_obj = bpy.data.objects[comparename]
                compare_obj.hide_set(True)
                compare_obj.hide_set(False)

                offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
                borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
                # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
                thickening_offset_borderwidth(0, borderWidth, True)
                thickening_offset_borderwidth(offset, borderWidth, False)
                # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
                bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
                draw_border_curve()  # 重新绘制边界

        return {'FINISHED'}


class TestFunc(bpy.types.Operator):
    bl_idname = "obj.testfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):

        # auto_thickening()
        # backFromLocalThickening(context)
        # backToLocalThickening(context)

        # if bpy.context.mode == "OBJECT":
        #     bpy.ops.paint.vertex_paint_toggle()
        # bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        # bpy.data.brushes["Draw"].color = (0.4, 1, 1)
        # bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        # bpy.ops.object.autothick
        # print("testfunc")
        # bpy.ops.object.timer_auto_thick()
        # frontFromLocalThickening()
        frontToLocalThickening()
        # backFromLocalThickening()
        # backToLocalThickening()

        return {'FINISHED'}
        # context.window_manager.modal_handler_add(self)                  #进入modal模式
        # return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TestFunc

        timer = context.window_manager.event_timer_add(0.5, window=context.window)
        if (True):
            if (bpy.context.scene.var == 5):
                pass
            else:
                context.window_manager.event_timer_remove(timer)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}

        return {'FINISHED'}


class TestFunc1(bpy.types.Operator):
    bl_idname = "obj.testfunc1"
    bl_label = "功能测试"

    def invoke(self, context, event):
        # auto_thickening()
        # backFromLocalThickening(context)
        # backToLocalThickening(context)

        # if bpy.context.mode == "OBJECT":
        #     bpy.ops.paint.vertex_paint_toggle()
        # bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        # bpy.data.brushes["Draw"].color = (0.4, 1, 1)
        # bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'
        # bpy.context.scene.tool_settings.unified_paint_settings.size = 100
        # bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
        # bpy.ops.object.autothick
        # print("testfunc")
        # bpy.ops.object.timer_auto_thick()
        frontFromLocalThickening()
        # frontToLocalThickening()
        # backFromLocalThickening()
        # backToLocalThickening()
        # selected_objs = bpy.data.objects
        # for selected_obj in selected_objs:
        #     print(selected_obj.name)
        return {'FINISHED'}


class InitialColor(bpy.types.Operator):
    bl_idname = "obj.initialcolor"
    bl_label = "初始化模型颜色"

    def execute(self, context):
        bpy.data.screens["Layout"].show_statusbar = False
        initialModelColor()
        return {'FINISHED'}


class InitialTransparency(bpy.types.Operator):
    bl_idname = "obj.initialtransparency"
    bl_label = "将模型变为透明"

    def execute(self, context):
        initialTransparency()
        return {'FINISHED'}


# 定时器 在扩大或缩小局部加厚区域模式下添加该定时器,每隔一段时间自动检测是否需要加厚,当不再扩大或缩小区域的笔刷上时,退出
class TimerAutoThick(bpy.types.Operator):
    bl_idname = "object.timer_auto_thick"
    bl_label = "自动加厚"

    __timer = None

    def execute(self, context):
        op_cls = TimerAutoThick
        op_cls.__timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        global is_timer_start  # 防止添加多余的定时器
        is_timer_start = True
        print("timerbegin")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TimerAutoThick

        global is_timer_start  # 防止添加多余的定时器
        if context.area:
            context.area.tag_redraw()
        if (bpy.context.scene.var == 5):
            if event.type == 'TIMER':
                if ((not isOnLocalThickArea(context, event)) and isSelectedAreaChanged()):
                    draw_border_curve()  # 根据选中区域绘制出边界
                    auto_thickening()
                    draw_border_curve()
            return {'PASS_THROUGH'}
        elif (bpy.context.scene.var == 6):
            if event.type == 'TIMER':
                if ((isOnLocalThickArea(context, event)) and isSelectedAreaChanged()):
                    draw_border_curve()  # 根据选中区域绘制出边界
                    auto_thickening()
                    draw_border_curve()
            return {'PASS_THROUGH'}
        else:
            is_timer_start = False
            print("timerend")
            return {'FINISHED'}
        return {'PASS_THROUGH'}


class Local_Thickening_Reset(bpy.types.Operator):
    bl_idname = "obj.localthickeningreset"
    bl_label = "重置模型"

    def invoke(self, context, event):
        self.execute(context)
        if bpy.context.mode == "PAINT_VERTEX":  # 将默认的顶点绘制模式切换到物体模式
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

    def execute(self, context):

        global is_copy_local_thickening

        global local_thickening_objects_array
        global objects_array_index
        bpy.context.scene.var = 9

        # 重置状态数组
        local_thickening_objects_array = []  # 重置局部加厚中保存模型各个状态的数组
        objects_array_index = -1
        is_copy_local_thickening = False

        # 根据LocalThickCopy复制出一份物体用来将参照物LocalThickCompare为最初的模型
        active_obj = bpy.context.active_object
        name = bpy.context.object.name
        for selected_obj in bpy.data.objects:
            if (selected_obj.name == name + "LocalThickCompare"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        copyname = name + "LocalThickCopy"  # TODO  LocalThickCopy
        ori_obj = bpy.data.objects[copyname]
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "LocalThickCompare"
        scene = bpy.context.scene  # 将其颜色全部覆盖重置再保存到数组中
        scene.collection.objects.link(duplicate_obj)

        # 根据LocalThickCopy复制出一份物体并替换为当前激活物体
        active_obj = bpy.context.active_object  # 将当前激活的模型替换为执行加厚操作之前的模型
        name = bpy.context.object.name
        copyname = name + "LocalThickCopy"  # TODO  LocalThickCopy
        ori_obj = bpy.data.objects[copyname]
        bpy.data.objects.remove(active_obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        scene = bpy.context.scene  # 将其颜色全部覆盖重置再保存到数组中
        scene.collection.objects.link(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj

        draw_border_curve()  # 删除局部加厚中的圆环

        return {'FINISHED'}


class Local_Thickening_AddArea(bpy.types.Operator):
    bl_idname = "obj.localthickeningaddarea"
    bl_label = "增大局部加厚区域"

    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    def invoke(self, context, event):

        global is_timer_start
        bpy.context.scene.var = 5
        op_cls = Local_Thickening_AddArea
        print("Local_Thickening_AddArea_invoke")
        if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到顶点绘制模式
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用自由线笔刷
        bpy.data.brushes["Draw"].color = (0.4, 1, 1)  # 设置笔刷颜色,该颜色用于扩大局部加厚区域
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'  # 衰减设置为常量
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为100
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例
        if bpy.context.mode == "PAINT_VERTEX":  # 将默认的顶点绘制模式切换到物体模式
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式，执行公共鼠标行为
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作，通过鼠标右键控制圆环大小
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
        # 开启定时器,局部加厚区域扩大时,自动加厚
        if (is_timer_start == False):
            bpy.ops.object.timer_auto_thick()
        context.window_manager.modal_handler_add(self)  # 进入modal模式
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_AddArea

        if (bpy.context.scene.var == 5):
            if (is_mouse_on_object(context, event)):
                if (is_changed(context, event)):
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到顶点绘制模式
                        bpy.ops.paint.vertex_paint_toggle()
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用自由线笔刷
                if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                    if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        op_cls.__right_mouse_down = True
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}
                elif event.type == 'MOUSEMOVE':
                    if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis
                    showThickness(context, event)  # 鼠标位于模型上时，显示模型上鼠标指针处的厚度
                    time = datetime.now().strftime("%f")
                    if int(time[-2:]) % 3 == 0:
                        draw_border_curve()  # 根据选中区域绘制出边界
                        # auto_thickening()
                        # draw_border_curve()
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                if bpy.context.mode == "PAINT_VERTEX":  # 将默认的顶点绘制模式切换到物体模式
                    bpy.ops.paint.vertex_paint_toggle()
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择笔刷
                MyHandleClass.remove_handler()  # 鼠标不在模型上时，移除厚度显示

            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class Local_Thickening_ReduceArea(bpy.types.Operator):
    bl_idname = "obj.localthickeningreducearea"
    bl_label = "减小局部加厚区域"

    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    def invoke(self, context, event):

        global is_timer_start
        bpy.context.scene.var = 6
        op_cls = Local_Thickening_ReduceArea
        print("Local_Thickening_AddArea_invoke")
        if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到顶点绘制模式
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 设置笔刷颜色,该颜色用于缩小局部加厚区域
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)  # 调用自由线笔刷
        bpy.data.brushes["Draw"].curve_preset = 'CONSTANT'  # 衰减设置为常量
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为100
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  # 锁定圆环和模型的比例
        if bpy.context.mode == "VERTEX_PAINT":  # 将默认的顶点绘制模式切换到物体模式
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择模式，执行公共鼠标行为
        op_cls.__right_mouse_down = False  # 初始化鼠标右键行为操作，通过鼠标右键控制圆环大小
        op_cls.__now_mouse_x = None
        op_cls.__now_mouse_y = None
        op_cls.__initial_mouse_x = None
        op_cls.__initial_mouse_y = None
        # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
        # 开启定时器,局部加厚区域缩小时,自动加厚
        if (is_timer_start == False):
            bpy.ops.object.timer_auto_thick()
        context.window_manager.modal_handler_add(self)  # 进入modal模式
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_ReduceArea

        if (bpy.context.scene.var == 6):
            if (is_mouse_on_object(context, event)):
                if (is_changed(context, event)):
                    if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到顶点绘制模式
                        bpy.ops.paint.vertex_paint_toggle()
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用自由线笔刷
                if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                    if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x = event.mouse_region_x
                        op_cls.__initial_mouse_y = event.mouse_region_y
                        op_cls.__right_mouse_down = True
                    elif event.value == 'RELEASE':
                        op_cls.__right_mouse_down = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    return {'RUNNING_MODAL'}
                elif event.type == 'MOUSEMOVE':
                    if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y = event.mouse_region_y
                        op_cls.__now_mouse_x = event.mouse_region_x
                        dis = int(sqrt(fabs(op_cls.__now_mouse_y - op_cls.__initial_mouse_y) * fabs(
                            op_cls.__now_mouse_y - op_cls.__initial_mouse_y) + fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x) * fabs(
                            op_cls.__now_mouse_x - op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis
                    showThickness(context, event)  # 鼠标位于模型上时，显示模型上鼠标指针处的厚度
                    time = datetime.now().strftime("%f")
                    if int(time[-2:]) % 2 == 0:
                        draw_border_curve()  # 根据选中区域绘制出边界
                        # auto_thickening()
                        # draw_border_curve()
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                if bpy.context.mode == "PAINT_VERTEX":  # 将默认的顶点绘制模式切换到物体模式
                    bpy.ops.paint.vertex_paint_toggle()
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择笔刷
                MyHandleClass.remove_handler()  # 鼠标不在模型上时，移除厚度显示
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class Local_Thickening_Thicken(bpy.types.Operator):
    bl_idname = "obj.localthickeningthick"
    bl_label = "对选中的加厚区域进行加厚,透明预览"

    def invoke(self, context, event):

        bpy.context.scene.var = 7
        op_cls = Local_Thickening_Thicken
        print("localThickening_invoke")

        global is_copy_local_thickening  # 用于再第一次加厚时,将LocalThickCopy复制下来并保存以初始化状态数组
        global local_thickening_objects_array  # 将模型最初的状态保存到状态数组中
        global objects_array_index
        global is_submit

        if not is_copy_local_thickening:
            # 保存模型最初的状态，用于重置,并将LocalThickCopy保存到状态数组的初始化状态
            is_copy_local_thickening = True
            # copy_object_jiahou(context)
            # 将当前模型状态保存进状态数组
            name = bpy.context.active_object.name
            comparename = name + "LocalThickCopy"  # TODO    根据最终参照物体替换
            compare_obj = bpy.data.objects[comparename]
            duplicate_obj = compare_obj.copy()
            duplicate_obj.data = compare_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = "localThick_array_objects"
            local_thickening_objects_array.append(duplicate_obj)
            objects_array_index = objects_array_index + 1
            is_submit = False

        if bpy.context.mode == "PAINT_VERTEX":  # 将默认的顶点绘制模式切换到物体模式
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")  # 切换到选择笔刷

        initialTransparency()

        offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
        borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数

        # 对选中的局部加厚区域，根据offset参数与borderWidth参数进行加厚
        thickening_offset_borderwidth(0, borderWidth, True)
        thickening_offset_borderwidth(offset, borderWidth, False)

        draw_border_curve()  # 更新圆环材质

        # 将加厚之后的模型保存到状态数组中
        initialModelColor()
        # 防止保存到状态数组中的模型存在修改器,使得在撤销或重做后出现卡顿现象
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)
        active_obj = bpy.context.active_object
        duplicate_obj = active_obj.copy()
        duplicate_obj.data = active_obj.data.copy()
        duplicate_obj.animation_data_clear()
        scene = bpy.context.scene  # 将其颜色全部覆盖重置再保存到数组中
        scene.collection.objects.link(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj
        if bpy.context.mode == "OBJECT":
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        duplicate_obj1 = duplicate_obj.copy()
        duplicate_obj1.data = duplicate_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        local_thickening_objects_array.append(duplicate_obj1)
        objects_array_index = objects_array_index + 1
        bpy.data.objects.remove(duplicate_obj, do_unlink=True)
        bpy.context.view_layer.objects.active = active_obj
        if bpy.context.mode == "PAINT_VERTEX":
            bpy.ops.paint.vertex_paint_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        initialTransparency()

        # 更换参照物
        thicking_temp_obj = local_thickening_objects_array[objects_array_index]
        for selected_obj in bpy.data.objects:
            if (selected_obj.name == "右耳" + "LocalThickCompare"):  # TODO   导入文件时使用全局变量保存文件名
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        duplicate_obj = thicking_temp_obj.copy()
        duplicate_obj.data = thicking_temp_obj.data.copy()
        duplicate_obj.name = active_obj.name + "LocalThickCompare"
        bpy.context.collection.objects.link(duplicate_obj)

        # 对选中的局部加厚区域,更新完参照物之后,在此基础上根据offset参数与borderWidth参数进行加厚
        thickening_offset_borderwidth(0, borderWidth, True)
        thickening_offset_borderwidth(offset, borderWidth, False)

        draw_border_curve()  # 更新圆环材质

        # 将加厚函数中添加的修改器应用并删除该修改器,防止卡顿
        bpy.ops.object.modifier_apply(modifier="LaplacianSmooth",single_user=True)

        # 解决模型重叠问题
        active_obj = bpy.context.active_object
        comparename = active_obj.name + "LocalThickCompare"
        compare_obj = bpy.data.objects[comparename]
        compare_obj.hide_set(True)
        compare_obj.hide_set(False)

        context.window_manager.modal_handler_add(self)  # 进入modal模式
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Local_Thickening_ReduceArea

        if (bpy.context.scene.var == 7):
            if (is_mouse_on_object(context, event)):
                if event.type == 'MOUSEMOVE':
                    showThickness(context, event)  # 鼠标位于模型上时，显示模型上鼠标指针处位置的厚度
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                MyHandleClass.remove_handler()  # 鼠标不在模型上时，移除厚度显示
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class Local_Thickening_Submit(bpy.types.Operator):
    bl_idname = "obj.localthickeningsubmit"
    bl_label = "提交做出的加厚修改"

    def execute(self, context):

        global is_copy_local_thickening
        global local_thickening_objects_array
        global objects_array_index
        global switch_selected_vertex_index
        global is_submit

        bpy.context.scene.var = 8
        is_copy_local_thickening = False
        is_submit = True

        # 重置局部加厚中保存模型各个状态的数组
        local_thickening_objects_array = []
        objects_array_index = -1

        # 提交前将模型中局部加厚的点索引给保存下来
        switch_selected_vertex_index = []
        active_obj = bpy.context.active_object
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

        # #将加厚函数中添加的修改器应用并删除该修改器
        # bpy.ops.object.modifier_apply(modifier="LaplacianSmooth")
        # 删除创建的顶点组
        obj = bpy.context.active_object
        vertex_group_to_delete = obj.vertex_groups.get("MyVertexGroup")
        if (vertex_group_to_delete != None):
            obj.vertex_groups.remove(vertex_group_to_delete)

        if (bpy.context.scene.var == 8):
            # 将当前激活模型由透明状态切换为非透明状态并将模型中选中的局部加厚区域重置
            initialModelColor()
            if bpy.context.mode == "OBJECT":
                bpy.ops.paint.vertex_paint_toggle()
            bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
            bpy.ops.paint.vertex_color_set()
            if bpy.context.mode == "PAINT_VERTEX":
                bpy.ops.paint.vertex_paint_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            draw_border_curve()  # 将局部加厚区域中的圆环删除
        return {'FINISHED'}



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
    bl_idname = "my_tool.vertexpainttest"
    bl_label = "顶点绘制测试"
    bl_description = (
        "确认所作的改变"
    )
    bl_icon = "ops.mesh.extrude_faces_move"
    bl_widget = None
    bl_keymap = (
        ("obj.testfunc", {"type": 'RIGHTMOUSE', "value": 'PRESS'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

    # 注册类


_classes = [
    InitialColor,
    InitialTransparency,
    Local_Thickening_Reset,
    Local_Thickening_AddArea,
    Local_Thickening_ReduceArea,
    Local_Thickening_Thicken,
    Local_Thickening_Submit,
    Local_Thickening_Mirror,
    BackUp,
    Forward,
    TestFunc,
    TestFunc1,
    TimerAutoThick
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_JiaHou, separator=True, group=False)
    # bpy.utils.register_tool(MyTool3_JiaHou, separator=True, group=False, after={MyTool_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool5_JiaHou, separator=True, group=False, after={MyTool3_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool7_JiaHou, separator=True, group=False, after={MyTool5_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool9_JiaHou, separator=True, group=False, after={MyTool7_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool11_JiaHou,separator=True, group=False,after={MyTool9_JiaHou.bl_idname})

    # bpy.utils.register_tool(MyTool2_JiaHou, separator=True, group=False)
    # bpy.utils.register_tool(MyTool4_JiaHou, separator=True, group=False, after={MyTool2_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool6_JiaHou, separator=True, group=False, after={MyTool4_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool8_JiaHou, separator=True, group=False, after={MyTool6_JiaHou.bl_idname})
    # bpy.utils.register_tool(MyTool10_JiaHou, separator=True, group=False, after={MyTool8_JiaHou.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    # bpy.utils.unregister_tool(MyTool_JiaHou)
    # bpy.utils.unregister_tool(MyTool3_JiaHou)
    # bpy.utils.unregister_tool(MyTool5_JiaHou)
    # bpy.utils.unregister_tool(MyTool7_JiaHou)
    # bpy.utils.unregister_tool(MyTool9_JiaHou)
    # bpy.utils.unregister_tool(MyTool11_JiaHou)

    # bpy.utils.unregister_tool(MyTool2_JiaHou)
    # bpy.utils.unregister_tool(MyTool4_JiaHou)
    # bpy.utils.unregister_tool(MyTool6_JiaHou)
    # bpy.utils.unregister_tool(MyTool8_JiaHou)
    # bpy.utils.unregister_tool(MyTool10_JiaHou)