from asyncio import Handle
from venv import create
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re
from .tool import *

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变

is_add_support = False   #是否添加过支撑,只能添加一个支撑

prev_location_x = 0     #记录支撑位置
prev_location_y = 0
prev_location_z = 0
prev_rotation_x = 0
prev_rotation_y = 0
prev_rotation_z = 0

enum = "OP1"           #支撑类型
offset = 0             #支撑偏移量

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
    name = "右耳"  # TODO      右耳为导入的模型名称
    obj = bpy.data.objects[name]

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
    mwi = obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if obj.type == 'MESH':
        if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


# 判断鼠标状态是否发生改变
def is_changed(context, event):
    name = "右耳"  # TODO     右耳为导入的模型名称
    obj = bpy.data.objects[name]

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
    mwi = obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if obj.type == 'MESH':
        if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
            mesh = obj.data
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


def frontToSupport():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SupportReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    supportInitial


def frontFromSupport():
    supportSaveInfo
    conename = "Cone"
    cone_obj = bpy.data.objects.get(conename)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (cone_obj != None):
        bpy.data.objects.remove(cone_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)

    name = "右耳"  # TODO    根据导入文件名称更改Support
    obj = bpy.data.objects[name]
    resetname = name + "SupportReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportReset" or selected_obj.name == "右耳SupportLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToSupport():
    exist_SupportReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportReset"):
            exist_SupportReset = True
    if (exist_SupportReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "SupportReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        supportInitial
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳LabelLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳HandleLast") != None):
            lastname = "右耳HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SupportReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        supportInitial

def backFromSupport():

    supportSaveInfo
    supportSubmit()

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳SupportLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SupportLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)


def createHardMouldSupport():
    '''
        用平面切去圆锥的一角，创建出硬耳膜支撑
    '''
    bpy.ops.mesh.primitive_cone_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.scale[0] = 3
    bpy.context.object.scale[1] = 3
    bpy.context.object.scale[2] = 3

    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, 1), scale=(1, 1, 1))
    bpy.context.object.scale[0] = 3
    bpy.context.object.scale[1] = 3
    bpy.context.object.scale[2] = 3

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    conename = "Cone"
    cone_obj = bpy.data.objects.get(conename)

    #反转平面的法线方向
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')
    #添加修改器,使用平面将圆锥切割成支撑
    bpy.context.view_layer.objects.active = cone_obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["Boolean"].object = plane_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    #减去平面多余的部分
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers["Boolean"].object = cone_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    #将支撑上下翻转，防止其吸附到内壁上
    bpy.context.view_layer.objects.active = cone_obj
    bpy.context.object.rotation_euler[1] = 3.14159
    bpy.context.object.location[2] = 2


def createSoftMouldSupport():
    '''
        用平面切去圆锥的一角，创建出硬耳膜支撑
    '''
    bpy.ops.mesh.primitive_cone_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.scale[0] = 3
    bpy.context.object.scale[1] = 3
    bpy.context.object.scale[2] = 6

    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, 3), scale=(1, 1, 1))
    bpy.context.object.scale[0] = 3
    bpy.context.object.scale[1] = 3
    bpy.context.object.scale[2] = 3

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    conename = "Cone"
    cone_obj = bpy.data.objects.get(conename)

    #反转平面的法线方向
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')
    #添加修改器,使用平面将圆锥切割成支撑
    bpy.context.view_layer.objects.active = cone_obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["Boolean"].object = plane_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    #减去平面多余的部分
    bpy.context.view_layer.objects.active = plane_obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers["Boolean"].object = cone_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    #将支撑上下翻转，防止其吸附到内壁上
    bpy.context.view_layer.objects.active = cone_obj
    bpy.context.object.rotation_euler[1] = 3.14159
    bpy.context.object.location[2] = 6

def supportSaveInfo():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global enum
    global offset

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    #记录附件位置信息
    if(plane_obj != None):
        prev_location_x = plane_obj.location[0]
        prev_location_y = plane_obj.location[1]
        prev_location_z = plane_obj.location[2]
        prev_rotation_x = plane_obj.rotation_euler[0]
        prev_rotation_y = plane_obj.rotation_euler[1]
        prev_rotation_z = plane_obj.rotation_euler[2]
        enum = bpy.context.scene.zhiChengTypeEnum
        offset = bpy.context.scene.zhiChengOffset


def supportInitial():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global enum
    global offset
    global is_add_support

    is_add_support = True

    if(is_add_support == True):
        addSupport()
        # 将Plane激活并选中
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        plane_obj.location[0] = prev_location_x
        plane_obj.location[1] = prev_location_y
        plane_obj.location[2] = prev_location_z
        plane_obj.rotation_euler[0] = prev_rotation_x
        plane_obj.rotation_euler[1] = prev_rotation_y
        plane_obj.rotation_euler[2] = prev_rotation_z
        bpy.context.scene.zhiChengTypeEnum = enum
        bpy.context.scene.zhiChengOffset = offset  
        bpy.ops.object.supportadd('INVOKE_DEFAULT')






def supportReset():
    # 存在未提交支撑时,删除Cone和Plane
    support_name = "Cone"
    support_obj = bpy.data.objects.get(support_name)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 存在未提交的Support和Plane时
    if (support_obj != None):
        bpy.data.objects.remove(support_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    # 将SupportReset复制并替代当前操作模型
    oriname = "右耳"  # TODO    右耳最终需要替换为导入时的文件名  右耳SupportReset同理
    ori_obj = bpy.data.objects.get(oriname)
    copyname = "右耳SupportReset"
    copy_obj = bpy.data.objects.get(copyname)
    if (ori_obj != None and copy_obj != None):
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = copy_obj.copy()
        duplicate_obj.data = copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)


def supportSubmit():
    name = "右耳"
    obj = bpy.data.objects.get(name)
    support_name = "Cone"
    support_obj = bpy.data.objects.get(support_name)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 存在未提交的Support和Plane时
    if (support_obj != None and plane_obj != None):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = support_obj
        bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(support_obj, do_unlink=True)

        # 合并后Support会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')


def addSupport():
    # 添加平面Plane和支撑Cone
    global enum
    if enum == "OP1":
        createHardMouldSupport()
    elif enum == "OP2":
        createSoftMouldSupport()
   
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    support_name = "Cone"
    support_obj = bpy.data.objects[support_name]
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]

    # 为附件添加材质
    bpy.context.view_layer.objects.active = support_obj
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    support_obj.data.materials.clear()
    support_obj.data.materials.append(red_material)

    # 为平面添加透明效果
    bpy.context.view_layer.objects.active = plane_obj
    mat = bpy.data.materials.get("Transparency")
    if mat is None:
        mat = bpy.data.materials.new(name="Transparency")
    mat.use_nodes = True
    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    color = nodes.new(type="ShaderNodeVertexColor")
    links.new(color.outputs[0], nodes["Principled BSDF"].inputs[0])
    links.new(shader.outputs[0], output.inputs[0])
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(mat)
    bpy.data.materials['Transparency'].blend_method = "BLEND"
    bpy.data.materials["Transparency"].node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2

    ##将平面设置为附件的父物体。对父物体平面进行位移和大小缩放操作时，子物体字体会其改变
    bpy.context.view_layer.objects.active = plane_obj
    support_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    support_obj.select_set(False)
    plane_obj.select_set(False)
    bpy.context.view_layer.objects.active = plane_obj
    plane_obj.select_set(True)

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    # 设置附件初始位置
    plane_obj.location[0] = 10  # TODO    Label初始位置应该为鼠标双击的位置
    plane_obj.location[1] = 10
    plane_obj.location[2] = 10



class SupportTest(bpy.types.Operator):
    bl_idname = "object.supporttestfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):
        createHardMouldSupport()
        return {'FINISHED'}

class SupportTest1(bpy.types.Operator):
    bl_idname = "object.supporttestfunc1"
    bl_label = "功能测试"

    def invoke(self, context, event):
        createSoftMouldSupport()
        return {'FINISHED'}

class SupportReset(bpy.types.Operator):
    bl_idname = "object.supportreset"
    bl_label = "支撑重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 16
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_add_support
        is_add_support = False
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        supportReset()
        return {'FINISHED'}


class SupportAdd(bpy.types.Operator):
    bl_idname = "object.supportadd"
    bl_label = "添加支撑"

    def invoke(self, context, event):

        bpy.context.scene.var = 17
        global is_add_support
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if (not is_add_support):
            is_add_support = True
            addSupport()
            # 将Plane激活并选中
            planename = "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if (bpy.context.scene.var == 17):
            if (is_mouse_on_object(context, event) and is_changed(context, event)):
                # 调用handle的鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                # 调用公共鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class SupportSubmit(bpy.types.Operator):
    bl_idname = "object.supportsubmit"
    bl_label = "支撑提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 18
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        supportSubmit()
        return {'FINISHED'}


class MyTool_Support1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_reset"
    bl_label = "支撑重置"
    bl_description = (
        "重置模型,清除模型上的所有支撑"
    )
    bl_icon = "ops.transform.bone_envelope"
    bl_widget = None
    bl_keymap = (
        ("object.supportreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Support2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_add"
    bl_label = "支撑添加"
    bl_description = (
        "在模型上添加一个支撑"
    )
    bl_icon = "ops.transform.bone_size"
    bl_widget = None
    bl_keymap = (
        ("object.supportadd", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Support3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_submit"
    bl_label = "支撑提交"
    bl_description = (
        "对于模型上所有支撑提交实体化"
    )
    bl_icon = "ops.transform.edge_slide"
    bl_widget = None
    bl_keymap = (
        ("object.supportsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    SupportReset,
    SupportAdd,
    SupportSubmit,
    SupportTest,
    SupportTest1
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_Support1, separator=True, group=False)
    # bpy.utils.register_tool(MyTool_Support2, separator=True, group=False, after={MyTool_Support1.bl_idname})
    # bpy.utils.register_tool(MyTool_Support3, separator=True, group=False, after={MyTool_Support2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    # bpy.utils.unregister_tool(MyTool_Support1)
    # bpy.utils.unregister_tool(MyTool_Support2)
    # bpy.utils.unregister_tool(MyTool_Support3)
