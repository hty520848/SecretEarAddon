from asyncio import Handle
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh
import re

is_in_handle = False

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变


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


def toHandle():
    global is_in_handle
    if (not is_in_handle):
        bpy.ops.object.handleadd('INVOKE_DEFAULT')
    is_in_handle = True


def addHandle():
    # 添加平面Plane和附件Cube
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(-20, 6, 1), scale=(1, 1, 1))
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(-20, 6, 0), scale=(1, 1, 1))

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    cubename = "Cube"
    cube_obj = bpy.data.objects[cubename]
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]

    # 为附件添加材质
    bpy.context.view_layer.objects.active = cube_obj
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    cube_obj.data.materials.clear()
    cube_obj.data.materials.append(red_material)

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
    cube_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    cube_obj.select_set(False)
    plane_obj.select_set(False)
    bpy.context.view_layer.objects.active = plane_obj
    plane_obj.select_set(True)

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    # 设置附件初始位置
    plane_obj.location[0] = -9.7  # TODO    Label初始位置应该为鼠标双击的位置
    plane_obj.location[1] = -6.0
    plane_obj.location[2] = 3.2


class HandleAdd(bpy.types.Operator):
    bl_idname = "object.handleadd"
    bl_label = "添加附件"

    def invoke(self, context, event):

        bpy.context.scene.var = 13
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        addHandle()
        # 将Plane激活并选中
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if (bpy.context.scene.var == 13):
            if (is_mouse_on_object(context, event) and is_changed(context, event)):
                # 调用label的鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
            elif ((not is_mouse_on_object(context, event)) and is_changed(context, event)):
                # 调用公共鼠标行为
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}

        # 注册类


_classes = [
    HandleAdd
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
