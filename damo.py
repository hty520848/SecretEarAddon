import bpy
from bpy.types import WorkSpaceTool
import bpy_extras
from .prop import *
from math import *

import mathutils
import bmesh

var = 0  # 全局变量,切换不同按钮的model

# 新建材质节点，模型颜色相关


def newMaterial(id):

    mat = bpy.data.materials.get(id)

    if mat is None:
        mat = bpy.data.materials.new(name=id)

    mat.use_nodes = True

    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()

    return mat


def newShader(id, type, r, g, b):

    mat = newMaterial(id)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')

    if type == "diffuse":
        shader = nodes.new(type='ShaderNodeBsdfDiffuse')
        nodes["Diffuse BSDF"].inputs[0].default_value = (r, g, b, 1)

    elif type == "emission":
        shader = nodes.new(type='ShaderNodeEmission')
        nodes["Emission"].inputs[0].default_value = (r, g, b, 1)
        nodes["Emission"].inputs[1].default_value = 1

    elif type == "glossy":
        shader = nodes.new(type='ShaderNodeBsdfGlossy')
        nodes["Glossy BSDF"].inputs[0].default_value = (r, g, b, 1)
        nodes["Glossy BSDF"].inputs[1].default_value = 0

    elif type == "principled":
        shader = nodes.new(type='ShaderNodeBsdfPrincipled')
        nodes["Principled BSDF"].inputs[0].default_value = (r, g, b, 0.8)
        # nodes["Glossy BSDF"].inputs[1].default_value = 0
    links.new(shader.outputs[0], output.inputs[0])
    return mat


def initialModelColor():
    mat = newShader("Blue", "principled", 0, 0.25, 1)
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.context.space_data.shading.type = 'MATERIAL'


# 打磨功能模块左侧按钮的加厚操作
class Thickening(bpy.types.Operator):
    bl_idname = "object.thickening"
    bl_label = "加厚操作"
    bl_description = "点击鼠标左键加厚模型，右键改变区域选取圆环的大小"
    __running = False  # 该操作是否完成，以完成加厚，打薄，光滑功能的实现
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    esc = False

    global var

    def invoke(self, context, event):
        global var
        var = 1
        op_cls = Thickening
        if not op_cls.__running:
            initialModelColor()  # 初始化模型颜色
            if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                bpy.ops.sculpt.sculptmode_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用加厚笔刷
            bpy.data.brushes["SculptDraw"].direction = "ADD"
            __right_mouse_down = False  # 初始化鼠标右键行为操作
            __now_mouse_x = None
            __now_mouse_y = None
            __initial_mouse_x = None
            __initial_mouse_y = None  # 锁定圆环和模型的比例
            bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
            context.window_manager.modal_handler_add(self)  # 进入modal模式
            return {'RUNNING_MODAL'}
        else:
            op_cls.__running = False
            return {'FINISHED'}

    def modal(self, context, event):
        op_cls = Thickening
        global var
        if (var == 1):
            if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    op_cls.__right_mouse_down = True
                elif event.value == 'RELEASE':  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    op_cls.__running = False
                    op_cls.__right_mouse_down = False
                return {'RUNNING_MODAL'}
            elif event.type == 'MOUSEMOVE':
                if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                    op_cls.__now_mouse_y = event.mouse_region_y
                    op_cls.__now_mouse_x = event.mouse_region_x
                    dis = int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y) +
                              fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                    bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis
                    return {'RUNNING_MODAL'}
            elif event.type == 'ESC':
                if event.value == 'PRESS':
                    op_cls.esc = True
                    print("1")
                    return {'FINISHED'}
                if event.value == 'RELEASE':
                    op_cls.esc = False
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


# 打磨功能模块左侧按钮的减薄操作
class Thinning(bpy.types.Operator):
    bl_idname = "object.thinning"
    bl_label = "减薄操作"
    bl_description = "点击鼠标左键减薄模型，右键改变区域选取圆环的大小"
    __running = False  # 该操作是否完成，以完成加厚，打薄，光滑功能的实现
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    esc = False

    def invoke(self, context, event):
        global var
        var = 2
        op_cls = Thinning
        if not op_cls.__running:
            initialModelColor()  # 初始化模型颜色
            if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                bpy.ops.sculpt.sculptmode_toggle()
            # bpy.context.brush.direction="SUBTRACT"
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")  # 调用减薄笔刷
            # bpy.data.brushes["SculptDraw"].direction="SUBTRACT"
            __right_mouse_down = False  # 初始化鼠标右键行为操作
            __now_mouse_x = None
            __now_mouse_y = None
            __initial_mouse_x = None
            __initial_mouse_y = None  # 锁定圆环和模型的比例
            bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
            context.window_manager.modal_handler_add(self)  # 进入modal模式
            return {'RUNNING_MODAL'}
        else:
            op_cls.__running = False
            return {'FINISHED'}

    def modal(self, context, event):
        op_cls = Thinning
        global var
        if (var == 2):
            if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    op_cls.__right_mouse_down = True
                elif event.value == 'RELEASE':
                    op_cls.__running = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    op_cls.__right_mouse_down = False
                return {'RUNNING_MODAL'}
            elif event.type == 'MOUSEMOVE':
                if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                    op_cls.__now_mouse_y = event.mouse_region_y
                    op_cls.__now_mouse_x = event.mouse_region_x
                    dis = int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y) +
                              fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                    bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis
                    return {'RUNNING_MODAL'}
            elif event.type == 'ESC':
                if event.value == 'PRESS':
                    op_cls.esc = True
                    print("1")
                    return {'FINISHED'}
                if event.value == 'RELEASE':
                    op_cls.esc = False
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


# 打磨功能模块左侧按钮的光滑操作
class Smooth(bpy.types.Operator):
    bl_idname = "object.smooth"
    bl_label = "光滑操作"
    bl_description = "点击鼠标左键光滑模型，右键改变区域选取圆环的大小"
    __running = False  # 该操作是否完成，以完成加厚，打薄，光滑功能的实现
    # 自定义的鼠标右键行为参数
    __right_mouse_down = False  # 按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x = None  # 鼠标移动时的位置
    __now_mouse_y = None
    __initial_mouse_x = None  # 点击鼠标右键的初始位置
    __initial_mouse_y = None

    esc = False

    def invoke(self, context, event):
        op_cls = Smooth
        global var
        var = 3
        if not op_cls.__running:
            initialModelColor()  # 初始化模型颜色
            if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
                bpy.ops.sculpt.sculptmode_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")  # 调用光滑笔刷
            __right_mouse_down = False  # 初始化鼠标右键行为操作
            __now_mouse_x = None
            __now_mouse_y = None
            __initial_mouse_x = None
            __initial_mouse_y = None  # 锁定圆环和模型的比例
            bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'
            context.window_manager.modal_handler_add(self)  # 进入modal模式
            return {'RUNNING_MODAL'}
        else:
            op_cls.__running = False
            return {'FINISHED'}
    # def execute(self,context):          #执行光滑操作
    #    bpy.context.space_data.shading.type = 'MATERIAL'
    #    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")
    #    return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = Smooth
        global var
        if (var == 3):
            if event.type == 'RIGHTMOUSE':  # 点击鼠标右键，改变区域选取圆环的大小
                if event.value == 'PRESS':  # 按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                    op_cls.__initial_mouse_x = event.mouse_region_x
                    op_cls.__initial_mouse_y = event.mouse_region_y
                    op_cls.__right_mouse_down = True
                elif event.value == 'RELEASE':
                    op_cls.__running = False  # 松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小
                    op_cls.__right_mouse_down = False
                return {'RUNNING_MODAL'}
            elif event.type == 'MOUSEMOVE':
                if op_cls.__right_mouse_down:  # 鼠标右键按下时，鼠标移动改变圆环大小
                    op_cls.__now_mouse_y = event.mouse_region_y
                    op_cls.__now_mouse_x = event.mouse_region_x
                    dis = int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y) +
                              fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                    bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size = dis
                    return {'RUNNING_MODAL'}
            elif event.type == 'ESC':
                if event.value == 'PRESS':
                    op_cls.esc = True
                    print("1")
                    return {'FINISHED'}
                if event.value == 'RELEASE':
                    op_cls.esc = False
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


# Property窗口打磨操作
class huier_OT_damo(bpy.types.Operator):

    bl_idname = "object.damo"
    bl_label = "加厚耳模"
    bl_description = "使用鼠标拖动加厚耳模"

    __running = False

    q = False

    @classmethod
    def is_running(cls):
        return cls.__running

    def invoke(self, context, event):
        if not self.is_running():
            op_cls = huier_OT_damo
            op_cls.__running = True
            obj = bpy.context.active_object
            md = obj.modifiers.new("jiahou", "SOLIDIFY")
            md.use_rim_only = True
            md.use_quality_normals = True
            md.offset = 1
            md.thickness = context.scene.laHouDU
            context.window_manager.modal_handler_add(self)
            MyHandleClass.add_handler(
                draw_callback_px, (None, context.scene.laHouDU))
            return {'RUNNING_MODAL'}
        else:
            op_cls = huier_OT_damo
            op_cls.__running = False
            MyHandleClass.remove_handler()
            return {'FINISHED'}

    def modal(self, context, event):
        op_cls = huier_OT_damo
        if event.type == 'Q':
            if event.value == 'PRESS':
                op_cls.q = True
                # inner = bpy.context.object
                # outer = (ob for ob in bpy.context.selected_objects if ob != inner).__next__()

                inner = bpy.data.objects["右耳"]
                outer = bpy.data.objects["右耳.001"]
                inner_bm = bmesh_copy_from_object(inner)
                outer_bm = bmesh_copy_from_object(outer)

                inner_tree = mathutils.bvhtree.BVHTree.FromBMesh(inner_bm)
                outer_tree = mathutils.bvhtree.BVHTree.FromBMesh(outer_bm)

                cl = mathutils.Vector((0, 0, 0))

                innermw = inner.matrix_world
                innermw_inv = innermw.inverted()

                sum = 0

                for v in outer_bm.verts:
                    origin = innermw_inv @ cl
                    dest = innermw_inv @ v.co
                    direc = (dest - origin).normalized()

                    res, co, no, index = inner_tree.ray_cast(origin, direc)
                    if res:
                        print(res)
                        print(co)
                        print(no)
                        print(index)

                        # co_adj = innermw @ co
                        co_adj = innermw @ res
                        print(index)
                        between = co_adj.dot(co_adj)
                        sum += between
                    else:
                        print(res)

                print(sum)

            if event.value == 'RELEASE':
                op_cls.q = False
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}


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
        ("object.thickening", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {}),
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
        ("object.thickening", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {}),
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
        ("object.thinning", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {}),
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
        ("object.thinning", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {}),
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
        ("object.smooth", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {}),
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
        ("object.smooth", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


def bmesh_copy_from_object(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    bm.transform(obj.matrix_world)

    return bm


# 注册类
_classes = [
    Thickening,
    Thinning,
    Smooth,
    huier_OT_damo,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool, separator=True, group=False)
    bpy.utils.register_tool(MyTool3, separator=True,
                            group=False, after={MyTool.bl_idname})
    bpy.utils.register_tool(MyTool5, separator=True,
                            group=False, after={MyTool3.bl_idname})

    bpy.utils.register_tool(MyTool2, separator=True, group=False)
    bpy.utils.register_tool(MyTool4, separator=True,
                            group=False, after={MyTool2.bl_idname})
    bpy.utils.register_tool(MyTool6, separator=True,
                            group=False, after={MyTool4.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool)
    bpy.utils.unregister_tool(MyTool3)
    bpy.utils.unregister_tool(MyTool5)

    bpy.utils.unregister_tool(MyTool2)
    bpy.utils.unregister_tool(MyTool4)
    bpy.utils.unregister_tool(MyTool6)
