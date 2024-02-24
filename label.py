from os import dup
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re
from .tool import *

default_plane_size_x = 1  # 记录添加字体后平面的x轴默认尺寸,此时默认字体大小为4
default_plane_size_y = 1  # 记录添加字体后平面的y轴默认尺寸,此时默认字体大小为4

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变

label_info_save = []    #保存已经提交过的label信息,用于模块切换时的初始化


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


'''
该模式下激活物体一直为text文本,因此切换到其他模式时,应该将当前激活物体设置为右耳
该模式下当前激活物体为Panel和Text,其它已经生成的物体则以LabelText开头
'''


def frontToLabel():
    '''
    根据当前激活物体复制出来一份若存在LabelReset,用于该模块的重置操作与模块切换
    '''
    # 若存在LabelReset,则先将其删除
    # 根据当前激活物体,复制一份生成LabelReset
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳LabelReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LabelReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    initial()  # 初始化


def frontFromLabel():
    # 根据LabelReset,复制出一份物体替代当前操作物体
    # 删除LabelReset与LabelLast

    #此处提交主要时为了删除Plane和Text
    labelSubmit()

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    resetname = name + "LabelReset"
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
        if (selected_obj.name == "右耳LabelReset" or selected_obj.name == "右耳LabelLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToLabel():
    # 判断是否存在LabelReset
    # 若没有LabelReset,则说明跳过了Label模块,再直接由后面的模块返回该模块。   TODO  根据切割操作的最后状态复制出LabelReset和LabelLast
    # 若存在LabelReset,则直接将LabelReset复制一份用于替换当前操作物体
    exist_LabelReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳LabelReset"):
            exist_LabelReset = True
    if (exist_LabelReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "LabelReset"
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
        initial()      #初始化

    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳HandleLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "LabelReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        initial()      #初始化


def backFromLabel():
    # 将模型上未初始化的Label提交
    # 将提交之后的模型保存LabelLast,用于模块切换,若存在LabelLast,则先将其删除

    labelSubmit()

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳LabelLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "LabelLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)

#在label提交前会保存label的相关信息
def saveInfo():
    global label_info_save

    textname = "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)

    text = bpy.context.scene.labelText
    depth = bpy.context.scene.deep
    size = bpy.context.scene.fontSize
    style = bpy.context.scene.styleEnum
    l_x = plane_obj.location[0]
    l_y = plane_obj.location[1]
    l_z = plane_obj.location[2]
    r_x = plane_obj.rotation_euler[0]
    r_y = plane_obj.rotation_euler[1]
    r_z = plane_obj.rotation_euler[2]

    label_info = LabelInfoSave(text,depth,size,style,l_x,l_y,l_z,r_x,r_y,r_z)
    label_info_save.append(label_info)


def initial():
    global label_info_save
    #对于数组中保存的label信息,前n-1个先添加后提交,最后一个添加不提交
    if(len(label_info_save) > 0):
        for i in range(len(label_info_save)-1):
            labelInfo = label_info_save[i]
            text = labelInfo.text
            depth = labelInfo.depth
            size = labelInfo.size
            style = labelInfo.style
            l_x = labelInfo.l_x
            l_y = labelInfo.l_y
            l_z = labelInfo.l_z
            r_x = labelInfo.r_x
            r_y = labelInfo.r_y
            r_z = labelInfo.r_z
            #添加Label并提交
            labelInitial(text,depth,size,style,l_x,l_y,l_z,r_x,r_y,r_z)
        labelInfo = label_info_save[len(label_info_save)-1]
        text = labelInfo.text
        depth = labelInfo.depth
        size = labelInfo.size
        style = labelInfo.style
        l_x = labelInfo.l_x
        l_y = labelInfo.l_y
        l_z = labelInfo.l_z
        r_x = labelInfo.r_x
        r_y = labelInfo.r_y
        r_z = labelInfo.r_z
        bpy.context.scene.labelText = text
        # 先根据text信息添加一个label,激活鼠标行为
        bpy.ops.object.labeladd('INVOKE_DEFAULT')
        # 获取添加后的label,并根据参数设置其形状大小
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        bpy.context.scene.deep = depth
        bpy.context.scene.fontSize = size
        bpy.context.scene.styleEnum = style
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z


# 模块切换时,根据提交时保存的信息,添加label进行初始化,先根据信息添加label,之后再将label提交。与submit函数相比,提交时不必保存label信息。
def labelInitial(text, depth, size, style, l_x, l_y, l_z, r_x, r_y, r_z):

    # 先根据text信息添加一个label
    addLabel(text)

    # 获取添加后的label,并根据参数设置其形状大小
    name = "右耳"
    obj = bpy.data.objects.get(name)
    textname = "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    bpy.context.scene.deep = depth
    bpy.context.scene.fontSize = size
    bpy.context.scene.styleEnum = style
    plane_obj.location[0] = l_x
    plane_obj.location[1] = l_y
    plane_obj.location[2] = l_z
    plane_obj.rotation_euler[0] = r_x
    plane_obj.rotation_euler[1] = r_y
    plane_obj.rotation_euler[2] = r_z

    # 应用Label的表面形变修改器
    text_modifier_name = "SurfaceDeform"
    target_modifier = None
    for modifier in text_obj.modifiers:
        if modifier.name == text_modifier_name:
            target_modifier = modifier
    if (target_modifier != None):
        bpy.ops.object.modifier_apply(modifier="SurfaceDeform", single_user=True)
    # 应用Panel的缩裹修改器
    panel_modifier_name = "Shrinkwrap"
    target_modifier = None
    for modifier in plane_obj.modifiers:
        if modifier.name == panel_modifier_name:
            target_modifier = modifier
    if (target_modifier != None):
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap", single_user=True)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'

    # 将模型与Label根据style进行合并
    enum = bpy.types.Scene.styleEnum
    if enum == "OP1":
        bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    if enum == "OP2":
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].object = text_obj
    bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)
    bpy.context.object.data.use_auto_smooth = True

    # 删除平面和字体
    bpy.data.objects.remove(plane_obj, do_unlink=True)
    bpy.data.objects.remove(text_obj, do_unlink=True)

    # 合并后Label会被去除材质,因此需要重置一下模型颜色为黄色
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
    bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
    bpy.ops.paint.vertex_color_set()
    bpy.ops.object.mode_set(mode='OBJECT')




def addLabel(text):
    '''
    根据text生成一个新的Label标签,生成的Label名称默认为Text,平面名称默认为Plane。添加的表面形变修改器和缩裹修改器需要在提交的时候应用
    '''
    global default_plane_size_x
    global default_plane_size_y

    enum = bpy.context.scene.styleEnum
    bpy.context.scene.deep = 1
    bpy.context.scene.fontSize = 4

    # 添加字体,字体名称默认为Text
    bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(-16, 8, 4), scale=(1, 1, 1))
    bpy.context.object.data.align_x = 'CENTER'
    bpy.context.object.data.align_y = 'CENTER'
    # 加载中文字体,并将该字体应用到文本中
    bpy.ops.font.open(filepath="C:\\Windows\\Fonts\\Deng.ttf", relative_path=True)  # TODO    字体文件位置
    text_object = bpy.data.objects.get("Text")
    font_data = bpy.data.fonts.get("DengXian Regular")
    if text_object and text_object.type == 'FONT' and font_data is not None:
        text_object.data.font = font_data
    bpy.context.object.data.extrude = 0.4
    textname = "Text"
    text_obj = bpy.data.objects[textname]
    bpy.context.view_layer.objects.active = text_obj
    # 将文本复制到剪贴板
    text_to_paste = text
    bpy.context.window_manager.clipboard = text_to_paste
    # 切换到编辑模式,选中现有内容并删除,再将文本内容替换为粘贴板中内容
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.font.select_all()
    bpy.ops.font.text_paste()
    # 切换到物体模式,将字体网格化
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.convert(target='MESH')

    # 添加平面,平面名称默认为Panel
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(-16, 8, 4), scale=(1, 0.4, 1))

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    textname = "Text"
    text_obj = bpy.data.objects[textname]
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]

    # 将平面大小尺寸设置为文本的平面大小尺寸
    text_x = text_obj.dimensions.x
    text_y = text_obj.dimensions.y
    plane_x = plane_obj.dimensions.x
    plane_y = plane_obj.dimensions.y
    scale_x = text_x / plane_x
    scale_y = text_y / plane_y
    plane_obj.scale[0] = scale_x
    plane_obj.scale[1] = scale_y
    default_plane_size_x = scale_x
    default_plane_size_y = scale_y

    if enum == "OP1":
        # 为字体添加红色材质
        bpy.context.view_layer.objects.active = text_obj
        red_material = bpy.data.materials.new(name="Red")
        red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
        text_obj.data.materials.clear()
        text_obj.data.materials.append(red_material)
    elif enum == "OP2":
        # 为字体添加青色材质
        bpy.context.view_layer.objects.active = text_obj
        red_material = bpy.data.materials.new(name="Red")
        red_material.diffuse_color = (0, 0.4, 1.0, 1.0)
        text_obj.data.materials.clear()
        text_obj.data.materials.append(red_material)
    # 为字体添加细分修改器并应用。对字体添加表面形变修改器，将目标绑定为平面
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'
    bpy.context.object.modifiers["Subdivision"].levels = 3
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    bpy.ops.object.modifier_add(type='SURFACE_DEFORM')
    bpy.context.object.modifiers["SurfaceDeform"].target = plane_obj
    bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
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
    # 为平面添加细分修改器并应用
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'
    bpy.context.object.modifiers["Subdivision"].levels = 3
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    # 对平面添加缩裹修改器,将目标绑定为右耳
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
    bpy.context.object.modifiers["Shrinkwrap"].use_positive_direction = False
    bpy.context.object.modifiers["Shrinkwrap"].cull_face = 'BACK'
    bpy.context.object.modifiers["Shrinkwrap"].target = obj

    # 将平面设置为字体的父物体。对父物体平面进行位移和大小缩放操作时，子物体字体会其改变
    bpy.context.view_layer.objects.active = plane_obj
    text_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    text_obj.select_set(False)

    # 设置字体初始位置                               #TODO   改变了字体 y轴处的位置,需要修复该bug
    plane_obj.location[0] = -9.7  # TODO    Label初始位置应该为鼠标双击的位置
    plane_obj.location[1] = -6.0
    plane_obj.location[2] = 3.2


def labelDepthUpdate(depth):
    '''
    根据面板深度参数设置字体高度
    '''
    textname = "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 先将平面和字体移到模型之外,在调整字体高度,避免字体变形
    if (plane_obj != None):
        plane_obj_location_x = plane_obj.location[0]
        plane_obj_location_y = plane_obj.location[1]
        plane_obj_location_z = plane_obj.location[2]
        plane_obj.location[0] = -100000
        plane_obj.location[1] = -100000
        plane_obj.location[2] = -100000
        # 设置字体厚度
        if (text_obj != None):
            text_obj.scale[2] = depth
        plane_obj.location[0] = plane_obj_location_x
        plane_obj.location[1] = plane_obj_location_y
        plane_obj.location[2] = plane_obj_location_z


def labelSizeUpdate(size):
    '''
    根据面板字体尺寸参数设置字体大小
    '''
    # 字体大小以4为基准,大一号字体,扩大1.25倍,小一号字体,缩小0.8倍
    global default_plane_size_x
    global default_plane_size_y
    scale_x = default_plane_size_x
    scale_y = default_plane_size_y
    if (size >= 4):
        scale_x = scale_x * (1.25 ** (size - 4))
        scale_y = scale_y * (1.25 ** (size - 4))
    else:
        scale_x = scale_x * (0.8 ** (4 - size))
        scale_y = scale_y * (0.8 ** (4 - size))
    # 更改plane的尺寸,作为其子物体的text也会随之改变
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (plane_obj != None):
        plane_obj.scale[0] = scale_x
        plane_obj.scale[1] = scale_y


def labelTextUpdate(text):
    '''
    根据面板标签名称参数设置字体内容
    '''
    # 先删除当前的label,并记录当前Label的位置
    textname = "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    plane_obj_location_x = 0
    plane_obj_location_y = 0
    plane_obj_location_z = 0
    if (text_obj != None):
        bpy.data.objects.remove(text_obj, do_unlink=True)
    if (plane_obj != None):
        plane_obj_location_x = plane_obj.location[0]
        plane_obj_location_y = plane_obj.location[1]
        plane_obj_location_z = plane_obj.location[2]
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        # 将属性面板中的text属性值读取到剪切板中生成新的label
    addLabel(text)
    # 将Plane激活并选中,将其位置设置为名称更改前的上一个Label的位置
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (plane_obj_location_x != 0 and plane_obj_location_y != 0 and plane_obj_location_z != 0):
        plane_obj.location[0] = plane_obj_location_x
        plane_obj.location[1] = plane_obj_location_y
        plane_obj.location[2] = plane_obj_location_z
    plane_obj.select_set(True)
    bpy.context.view_layer.objects.active = plane_obj


def labelSubmit():
    '''
    提交操作,应用修改器,将Plane删除并将Text实体化
    '''
    enum = bpy.context.scene.styleEnum

    name = "右耳"
    obj = bpy.data.objects.get(name)
    textname = "Text"
    text_obj = bpy.data.objects.get(textname)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 存在未提交的Label和Plane时
    if (text_obj != None and plane_obj != None):
        #先将该Label的相关信息保存下来,用于模块切换时的初始化。
        saveInfo()

        # 应用Label的表面形变修改器
        text_modifier_name = "SurfaceDeform"
        target_modifier = None
        for modifier in text_obj.modifiers:
            if modifier.name == text_modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="SurfaceDeform",single_user=True)
        # 应用Panel的缩裹修改器
        panel_modifier_name = "Shrinkwrap"
        target_modifier = None
        for modifier in plane_obj.modifiers:
            if modifier.name == panel_modifier_name:
                target_modifier = modifier
        if (target_modifier != None):
            bpy.ops.object.modifier_apply(modifier="Shrinkwrap",single_user=True)

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        #将模型与Label根据style进行合并
        if enum == "OP1":
            bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
        if enum == "OP2":
            bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = text_obj
        bpy.ops.object.modifier_apply(modifier="Boolean",single_user=True)
        bpy.context.object.data.use_auto_smooth = True

        #删除平面和字体
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(text_obj, do_unlink=True)

        #合并后Label会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')


class LabelTest(bpy.types.Operator):
    bl_idname = "object.labeltestfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):
        addLabel("HDU")


        return {'FINISHED'}


class LabelTest1(bpy.types.Operator):
    bl_idname = "object.labeltestfunc1"
    bl_label = "功能测试"

    def invoke(self, context, event):
        labelSubmit()

        return {'FINISHED'}

#保存提交前的每个Label信息
class LabelInfoSave(object):
    def __init__(self,text,depth,size,style,l_x,l_y,l_z,r_x,r_y,r_z):
        self.text = text
        self.depth = depth
        self.size = size
        self.style = style
        self.l_x = l_x
        self.l_y = l_y
        self.l_z = l_z
        self.r_x = r_x
        self.r_y = r_y
        self.r_z = r_z





class LabelReset(bpy.types.Operator):
    bl_idname = "object.labelreset"
    bl_label = "标签重置"

    def invoke(self, context, event):

        bpy.context.scene.var = 10
        global label_info_save
        label_info_save = []

        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):

        # 存在未提交Label时,删除Text和Plane
        textname = "Text"
        text_obj = bpy.data.objects.get(textname)
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        # 存在未提交的Label和Plane时
        if (text_obj != None):
            bpy.data.objects.remove(text_obj, do_unlink=True)
        if (plane_obj != None):
            bpy.data.objects.remove(plane_obj, do_unlink=True)
        # 将LabelCopy复制并替代当前操作模型
        oriname = "右耳"  # TODO    右耳最终需要替换为导入时的文件名  右耳LabelCopy同理
        ori_obj = bpy.data.objects.get(oriname)
        copyname = "右耳LabelReset"
        copy_obj = bpy.data.objects.get(copyname)
        if (ori_obj != None and copy_obj != None):
            bpy.data.objects.remove(ori_obj, do_unlink=True)
            duplicate_obj = copy_obj.copy()
            duplicate_obj.data = copy_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = oriname
            bpy.context.collection.objects.link(duplicate_obj)
        return {'FINISHED'}


class LabelAdd(bpy.types.Operator):
    bl_idname = "object.labeladd"
    bl_label = "添加标签"

    def invoke(self, context, event):

        bpy.context.scene.var = 11
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        # 若模型上存在未提交的Label,则先将其提交
        labelSubmit()
        # 创建新的Label
        labelText = bpy.context.scene.labelText
        addLabel(labelText)
        # 将Plane激活并选中
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if (bpy.context.scene.var == 11):
            if (is_mouse_on_object(context, event) and is_changed(context, event)):
                # 调用label的鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                # 调用公共鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class LabelSubmit(bpy.types.Operator):
    bl_idname = "object.labelsubmit"
    bl_label = "标签提交"

    def invoke(self, context, event):
        bpy.context.scene.var == 12
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        labelSubmit()
        return {'FINISHED'}


class MyTool_Label1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_reset"
    bl_label = "标签重置"
    bl_description = (
        "重置模型,清除模型上的所有标签"
    )
    bl_icon = "ops.mesh.polybuild_hover"
    bl_widget = None
    bl_keymap = (
        ("object.labelreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Label2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_add"
    bl_label = "标签添加"
    bl_description = (
        "在模型上添加一个标签"
    )
    bl_icon = "ops.mesh.primitive_torus_add_gizmo"
    bl_widget = None
    bl_keymap = (
        ("object.labeladd", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Label3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_submit"
    bl_label = "标签提交"
    bl_description = (
        "对于模型上所有标签提交实体化"
    )
    bl_icon = "ops.mesh.primitive_cone_add_gizmo"
    bl_widget = None
    bl_keymap = (
        ("object.labelsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    LabelReset,
    LabelAdd,
    LabelSubmit,
    LabelTest,
    LabelTest1
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_Label1, separator=True, group=False)
    # bpy.utils.register_tool(MyTool_Label2, separator=True, group=False, after={MyTool_Label1.bl_idname})
    # bpy.utils.register_tool(MyTool_Label3, separator=True, group=False, after={MyTool_Label2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    # bpy.utils.unregister_tool(MyTool_Label1)
    # bpy.utils.unregister_tool(MyTool_Label2)
    # bpy.utils.unregister_tool(MyTool_Label3)
