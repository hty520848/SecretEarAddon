import bpy
from bpy.types import WorkSpaceTool

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


class qiegeTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetcut"
    bl_label = "重置切割"
    bl_description = (
        "点击完成重置操作"
    )
    bl_icon = "ops.mesh.loopcut_slide"
    bl_widget = None
    bl_keymap = (
        ("object.resetcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class qiegeTool2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishcut"
    bl_label = "完成"
    bl_description = (
        "点击完成切割操作"
    )
    bl_icon = "ops.mesh.offset_edge_loops_slide"

    bl_widget = None
    bl_keymap = (
        ("object.finishcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class qiegeTool3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrorcut"
    bl_label = "切割镜像"
    bl_description = (
        "镜像操作"
    )
    bl_icon = "ops.curve.vertex_random"

    bl_widget = None
    bl_keymap = (
        ("object.mirrorcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


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
        "在模型中上一个标签的位置处添加一个标签"
    )
    bl_icon = "ops.mesh.primitive_torus_add_gizmo"
    bl_widget = None
    bl_keymap = (
        ("object.labeladd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.labeladdinvoke", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.labeladd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
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


class MyTool_Label_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_mirror"
    bl_label = "字体镜像"
    bl_description = (
        "点击镜像字体"
    )
    bl_icon = "brush.gpencil_draw.fill"
    bl_widget = None
    bl_keymap = (
        ("object.labelmirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Label_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_mouse"
    bl_label = "双击改变字体位置"
    bl_description = (
        "添加字体后,公共鼠标行为的各种操作,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.uv_sculpt.pinch"
    bl_widget = None
    bl_keymap = (
        ("object.labeldoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_LabelInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.label_initial"
    bl_label = "标签添加初始化"
    bl_description = (
        "刚进入Label模块的时,在模型上双击位置处添加一个标签"
    )
    bl_icon = "brush.sculpt.thumb"
    bl_widget = None
    bl_keymap = (
        ("object.labelinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_reset"
    bl_label = "附件重置"
    bl_description = (
        "重置模型,清除模型上的所有附件"
    )
    bl_icon = "ops.pose.breakdowner"
    bl_widget = None
    bl_keymap = (
        ("object.handlereset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_add"
    bl_label = "附件添加"
    bl_description = (
        "在模型的上一个附件的位置上添加一个附件"
    )
    bl_icon = "ops.pose.relax"
    bl_widget = None
    bl_keymap = (
        ("object.handleadd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.handleaddinvoke", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.handleadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_submit"
    bl_label = "附件提交"
    bl_description = (
        "对于模型上所有附件提交实体化"
    )
    bl_icon = "ops.pose.push"
    bl_widget = None
    bl_keymap = (
        ("object.handlesubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle_Rotate(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_rotate"
    bl_label = "附件旋转"
    bl_description = (
        "添加附件后,调用附件三维旋转鼠标行为"
    )
    bl_icon = "brush.gpencil_draw.draw"
    bl_widget = None
    bl_keymap = (
        ("object.handlerotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_mirror"
    bl_label = "附件镜像"
    bl_description = (
        "点击镜像附件"
    )
    bl_icon = "brush.gpencil_draw.erase"
    bl_widget = None
    bl_keymap = (
        ("object.handlemirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_mouse"
    bl_label = "双击改变附件位置"
    bl_description = (
        "添加附件后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.uv_sculpt.grab"
    bl_widget = None
    bl_keymap = (
        ("object.handledoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_HandleInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_initial"
    bl_label = "附件添加初始化"
    bl_description = (
        "刚进入附件模块的时,在模型上双击位置处添加一个附件"
    )
    bl_icon = "brush.sculpt.topology"
    bl_widget = None
    bl_keymap = (
        ("object.handleinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


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
        # ("object.supportadd", {"type": 'MOUSEMOVE', "value": 'ANY'},
        #  {}),
        ("object.supportadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
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


class MyTool_Support_Rotate(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_rotate"
    bl_label = "支撑旋转"
    bl_description = (
        "添加支撑后,调用支撑三维旋转鼠标行为"
    )
    bl_icon = "brush.paint_texture.clone"
    bl_widget = None
    bl_keymap = (
        ("object.supportrotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Support_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_mirror"
    bl_label = "支撑镜像"
    bl_description = (
        "点击镜像支撑"
    )
    bl_icon = "brush.paint_texture.airbrush"
    bl_widget = None
    bl_keymap = (
        ("object.supportmirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Support_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.support_mouse"
    bl_label = "双击改变支撑位置"
    bl_description = (
        "添加支撑后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.uv_sculpt.relax"
    bl_widget = None
    bl_keymap = (
        ("object.supportdoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class addcurve_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addcurve"
    bl_label = "双击添加点"
    bl_description = (
        "使用鼠标双击添加点"
    )
    bl_icon = "ops.curves.sculpt_cut"
    bl_widget = None
    bl_keymap = (
        ("object.pointqiehuan", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class addcurve_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addcurve3"
    bl_label = "添加点操作"
    bl_description = (
        "实现鼠标双击添加点操作"
    )
    bl_icon = "ops.curves.sculpt_grow_shrink"
    bl_widget = None
    bl_keymap = (
        ("object.addcurve", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("object.addpoint", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("object.deletepoint", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class dragcurve_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.dragcurve"
    bl_label = "拖拽曲线"
    bl_description = (
        "使用鼠标拖拽曲线"
    )
    bl_icon = "ops.curves.sculpt_density"
    bl_widget = None
    bl_keymap = (
        ("object.dragcurve", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class smoothcurve_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smoothcurve"
    bl_label = "平滑曲线"
    bl_description = (
        "使用鼠标平滑曲线"
    )
    bl_icon = "ops.curves.sculpt_add"
    bl_widget = None
    bl_keymap = (
        ("object.smoothcurve", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetmould"
    bl_label = "重置创建磨具"
    bl_description = (
        "点击重置创建磨具"
    )
    bl_icon = "ops.curves.sculpt_comb"
    bl_widget = None
    bl_keymap = (
        ("object.resetmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class finishmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishmould"
    bl_label = "完成创建磨具"
    bl_description = (
        "点击完成创建磨具"
    )
    bl_icon = "ops.curves.sculpt_delete"
    bl_widget = None
    bl_keymap = (
        ("object.finishmould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class canalmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.canalmould"
    bl_label = "初始化创建通道"
    bl_description = (
        "点击在磨具上创建通道"
    )
    bl_icon = "brush.sculpt.clay_thumb"
    bl_widget = None
    bl_keymap = (
        ("object.updateshellcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class limitmould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.limitmould"
    bl_label = "限制器件不能脱出磨具范围"
    bl_description = (
        "点击限制磨具"
    )
    bl_icon = "brush.sculpt.clay_strips"
    bl_widget = None
    bl_keymap = (
        ("object.updatecollision", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrormould_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrormould"
    bl_label = "镜像创建磨具"
    bl_description = (
        "点击镜像创建磨具"
    )
    bl_icon = "brush.gpencil_draw.tint"
    bl_widget = None
    bl_keymap = (
        ("object.mirrormould", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class addsoundcanal_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addsoundcanal2"
    bl_label = "传声孔添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作"
    )
    bl_icon = "ops.curves.sculpt_smooth"
    bl_widget = None
    bl_keymap = (
        ("object.addsoundcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class addsoundcanal_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addsoundcanal3"
    bl_label = "传声孔对圆球操作"
    bl_description = (
        "传声孔对圆球移动、双击操作"
    )
    bl_icon = "ops.curves.sculpt_pinch"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("object.deletesoundcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class finishsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishsoundcanal"
    bl_label = "传声孔完成"
    bl_description = (
        "完成管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_puff"
    bl_widget = None
    bl_keymap = (
        ("object.finishsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetsoundcanal"
    bl_label = "传声孔重置"
    bl_description = (
        "重置管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_slide"
    bl_widget = None
    bl_keymap = (
        ("object.resetsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class rotatesoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.soundcanal_rotate"
    bl_label = "号角管旋转"
    bl_description = (
        "添加号角管后,调用号角管三维旋转鼠标行为"
    )
    bl_icon = "brush.paint_texture.masklort"
    bl_widget = None
    bl_keymap = (
        ("object.soundcanalrotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrorsoundcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrorsoundcanal"
    bl_label = "传声孔镜像"
    bl_description = (
        "点击镜像传声孔"
    )
    bl_icon = "ops.curve.pen"
    bl_widget = None
    bl_keymap = (
        ("object.mirrorsoundcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class addventcanal_MyTool2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addventcanal2"
    bl_label = "通气孔添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作"
    )
    bl_icon = "ops.curve.extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("object.addventcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class addventcanal_MyTool3(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.addventcanal3"
    bl_label = "通气孔对圆球操作"
    bl_description = (
        "通气孔对圆球移动、双击操作"
    )
    bl_icon = "ops.curve.draw"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("object.deleteventcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class finishventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.finishventcanal"
    bl_label = "通气孔完成"
    bl_description = (
        "完成管道的绘制"
    )
    bl_icon = "ops.curve.extrude_move"
    bl_widget = None
    bl_keymap = (
        ("object.finishventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class resetventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.resetventcanal"
    bl_label = "通气孔重置"
    bl_description = (
        "重置管道的绘制"
    )
    bl_icon = "ops.curves.sculpt_snake_hook"
    bl_widget = None
    bl_keymap = (
        ("object.resetventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class mirrorventcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.mirrorventcanal"
    bl_label = "通气孔镜像"
    bl_description = (
        "点击镜像通气孔"
    )
    bl_icon = "ops.curve.radius"
    bl_widget = None
    bl_keymap = (
        ("object.mirrorventcanal", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Casting1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_reset"
    bl_label = "铸造法重置"
    bl_description = (
        "重置模型,清除模型上的所有标签"
    )
    bl_icon = "ops.gpencil.sculpt_randomize"
    bl_widget = None
    bl_keymap = (
        ("object.castingreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Casting2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_submit"
    bl_label = "铸造法提交"
    bl_description = (
        "提交铸造法中所作的操作"
    )
    bl_icon = "ops.gpencil.sculpt_smear"
    bl_widget = None
    bl_keymap = (
        ("object.castingsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Casting3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_mirror"
    bl_label = "铸造法镜像"
    bl_description = (
        "将该模型上的铸造法操作镜像到另一个模型上"
    )
    bl_icon = "ops.gpencil.sculpt_smooth"
    bl_widget = None
    bl_keymap = (
        ("object.castingmirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )
    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_reset"
    bl_label = "排气孔重置"
    bl_description = (
        "重置模型,清除模型上的所有排气孔"
    )
    bl_icon = "brush.sculpt.clay"
    bl_widget = None
    bl_keymap = (
        ("object.spruereset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_add"
    bl_label = "排气孔添加"
    bl_description = (
        "在模型上上一个排气孔的位置处添加一个排气孔"
    )
    bl_icon = "brush.sculpt.boundary"
    bl_widget = None
    bl_keymap = (
        ("object.sprueadd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.sprueaddinvoke", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.sprueadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_submit"
    bl_label = "排气孔提交"
    bl_description = (
        "对于模型上所有排气孔提交实体化"
    )
    bl_icon = "brush.sculpt.blob"
    bl_widget = None
    bl_keymap = (
        ("object.spruesubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue_Rotate(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_rotate"
    bl_label = "排气孔旋转"
    bl_description = (
        "添加排气孔后,调用排气孔三维旋转鼠标行为"
    )
    bl_icon = "brush.paint_texture.draw"
    bl_widget = None
    bl_keymap = (
        ("object.spruerotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_mirror"
    bl_label = "排气孔镜像"
    bl_description = (
        "点击镜像排气孔"
    )
    bl_icon = "brush.paint_texture.fill"
    bl_widget = None
    bl_keymap = (
        ("object.spruemirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_mouse"
    bl_label = "双击改变排气管位置"
    bl_description = (
        "添加排气管后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.paint_texture.mask"
    bl_widget = None
    bl_keymap = (
        ("object.spruedoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_SprueInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_initial"
    bl_label = "排气孔添加初始化"
    bl_description = (
        "刚进入排气孔模块的时,在模型上双击位置处添加一个排气孔"
    )
    bl_icon = "brush.sculpt.snake_hook"
    bl_widget = None
    bl_keymap = (
        ("object.sprueinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thickening"
    bl_label = "后期加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.armature.extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("object.last_thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thickening2"
    bl_label = "后期加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.armature.extrude_cursor"
    bl_widget = None
    bl_keymap = (
        ("object.last_thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thinning"
    bl_label = "后期磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.sequencer.blade"
    bl_widget = None
    bl_keymap = (
        ("object.last_thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo4(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_thinning2"
    bl_label = "后期磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.sequencer.blade"
    bl_widget = None
    bl_keymap = (
        ("object.last_thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo5(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_smooth"
    bl_label = "后期圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "brush.paint_weight.blur"
    bl_widget = None
    bl_keymap = (
        ("object.last_smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo6(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_smooth2"
    bl_label = "后期圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "brush.paint_weight.blur"
    bl_widget = None
    bl_keymap = (
        ("object.last_smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo7(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_damo_reset"
    bl_label = "后期重置"
    bl_description = (
        "点击进行重置操作"
    )
    bl_icon = "brush.particle.puff"
    bl_widget = None
    bl_keymap = (
        ("object.last_damo_reset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyToolLastDamo8(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.last_damo_reset2"
    bl_label = "后期重置"
    bl_description = (
        "点击进行重置操作"
    )
    bl_icon = "brush.particle.puff"
    bl_widget = None
    bl_keymap = (
        ("object.last_damo_reset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class Tool_ResetCutMould(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldreset"
    bl_label = "重置模具切割"
    bl_description = (
        "点击重置模具切割"
    )
    bl_icon = "brush.paint_texture.multiply"
    bl_widget = None
    bl_keymap = (
        ("cutmould.resetcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class Tool_FinishCutMould(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldfinish"
    bl_label = "完成模具切割"
    bl_description = (
        "点击完成模具切割"
    )
    bl_icon = "brush.paint_texture.smear"
    bl_widget = None
    bl_keymap = (
        ("cutmould.finishcut", {"type": 'MOUSEMOVE', "value": 'ANY'}, {}),
    )

    def draw_settings(context, layout, tool):
        pass


class Switch_CutMould1(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldswitch1"
    bl_label = "开始切割模具"
    bl_description = (
        "点击开始切割模具"
    )
    bl_icon = "brush.paint_texture.soften"
    bl_widget = None
    bl_keymap = (
        ("cutmould.start", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class Switch_CutMould2(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "tool.cutmouldswitch2"
    bl_label = "切割模具"
    bl_description = (
        "进行切割模具"
    )
    bl_icon = "brush.paint_weight.average"
    bl_widget = None
    bl_keymap = (
        ("cutmould.finish", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("cutmould.addpoint", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("cutmould.deletepoint", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class public_add_shellcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.public_add_shellcanal"
    bl_label = "外壳管道添加控制点操作"
    bl_description = (
        "实现鼠标双击添加控制点操作和公共鼠标行为"
    )
    bl_icon = "brush.sculpt.crease"
    bl_widget = None
    bl_keymap = (
        ("object.addshellcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class delete_drag_shellcanal_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.delete_drag_shellcanal"
    bl_label = ""
    bl_description = (
        "对外壳圆球圆球移动和双击删除操作"
    )
    bl_icon = "brush.sculpt.displacement_eraser"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("object.deleteshellcanal", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class dragcube_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.drag_cube"
    bl_label = "拖拽立方体对象"
    bl_description = (
        "左键按住拖拽立方体"
    )
    bl_icon = "brush.sculpt.cloth"
    bl_widget = None
    bl_keymap = (
        # ("view3d.select", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("deselect_all", True), ], },),
        ("hide.receiverdoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("transform.translate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("transform.trackball", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None)
    )

    def draw_settings(context, layout, tool):
        pass


class adjustreceiver_MyTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.adjustreceiver"
    bl_label = "改变接收器的位置"
    bl_description = (
        "左键双击改变接收器的位置"
    )
    bl_icon = "ops.armature.bone.roll"
    bl_widget = None
    bl_keymap = (
        ("adjust.receiverdoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass


def register_tools():
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

    bpy.utils.register_tool(qiegeTool, separator=True, group=False)
    bpy.utils.register_tool(qiegeTool2, separator=True,
                            group=False, after={qiegeTool.bl_idname})
    bpy.utils.register_tool(qiegeTool3, separator=True,
                            group=False, after={qiegeTool2.bl_idname})

    bpy.utils.register_tool(MyTool_Label1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Label2, separator=True, group=False, after={MyTool_Label1.bl_idname})
    bpy.utils.register_tool(MyTool_Label3, separator=True, group=False, after={MyTool_Label2.bl_idname})
    bpy.utils.register_tool(MyTool_Label_Mirror, separator=True, group=False, after={MyTool_Label3.bl_idname})
    bpy.utils.register_tool(MyTool_Label_Mouse, separator=True, group=False, after={MyTool_Label_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_LabelInitial, separator=True, group=False, after={MyTool_Label_Mouse.bl_idname})

    bpy.utils.register_tool(MyTool_Handle1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Handle2, separator=True, group=False, after={MyTool_Handle1.bl_idname})
    bpy.utils.register_tool(MyTool_Handle3, separator=True, group=False, after={MyTool_Handle2.bl_idname})
    bpy.utils.register_tool(MyTool_Handle_Rotate, separator=True, group=False, after={MyTool_Handle3.bl_idname})
    bpy.utils.register_tool(MyTool_Handle_Mirror, separator=True, group=False, after={MyTool_Handle_Rotate.bl_idname})
    bpy.utils.register_tool(MyTool_Handle_Mouse, separator=True, group=False, after={MyTool_Handle_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_HandleInitial, separator=True, group=False, after={MyTool_Handle_Mouse.bl_idname})

    bpy.utils.register_tool(MyTool_Support1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Support2, separator=True, group=False, after={MyTool_Support1.bl_idname})
    bpy.utils.register_tool(MyTool_Support3, separator=True, group=False, after={MyTool_Support2.bl_idname})
    bpy.utils.register_tool(MyTool_Support_Rotate, separator=True, group=False, after={MyTool_Support3.bl_idname})
    bpy.utils.register_tool(MyTool_Support_Mirror, separator=True, group=False, after={MyTool_Support_Rotate.bl_idname})
    bpy.utils.register_tool(MyTool_Support_Mouse, separator=True, group=False, after={MyTool_Support_Mirror.bl_idname})

    bpy.utils.register_tool(addcurve_MyTool, separator=True, group=False)
    bpy.utils.register_tool(dragcurve_MyTool, separator=True,
                            group=False, after={addcurve_MyTool.bl_idname})
    bpy.utils.register_tool(smoothcurve_MyTool, separator=True,
                            group=False, after={dragcurve_MyTool.bl_idname})
    bpy.utils.register_tool(addcurve_MyTool3)

    bpy.utils.register_tool(resetmould_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishmould_MyTool, separator=True,
                            group=False, after={resetmould_MyTool.bl_idname})
    bpy.utils.register_tool(canalmould_MyTool, separator=True, group=False,
                            after={finishmould_MyTool.bl_idname})
    bpy.utils.register_tool(limitmould_MyTool, separator=True, group=False,
                            after={canalmould_MyTool.bl_idname})
    bpy.utils.register_tool(mirrormould_MyTool, separator=True,
                            group=False, after={limitmould_MyTool.bl_idname})

    bpy.utils.register_tool(resetsoundcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishsoundcanal_MyTool, separator=True, group=False,
                            after={resetsoundcanal_MyTool.bl_idname})
    bpy.utils.register_tool(rotatesoundcanal_MyTool, separator=True, group=False,
                            after={finishsoundcanal_MyTool.bl_idname})
    bpy.utils.register_tool(mirrorsoundcanal_MyTool, separator=True, group=False,
                            after={rotatesoundcanal_MyTool.bl_idname})
    bpy.utils.register_tool(addsoundcanal_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(addsoundcanal_MyTool3, separator=True, group=False)

    bpy.utils.register_tool(resetventcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(finishventcanal_MyTool, separator=True, group=False,
                            after={resetventcanal_MyTool.bl_idname})
    bpy.utils.register_tool(mirrorventcanal_MyTool, separator=True, group=False,
                            after={finishventcanal_MyTool.bl_idname})
    bpy.utils.register_tool(addventcanal_MyTool2, separator=True, group=False)
    bpy.utils.register_tool(addventcanal_MyTool3, separator=True, group=False)

    bpy.utils.register_tool(MyTool_Casting1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Casting2, separator=True, group=False, after={MyTool_Casting1.bl_idname})
    bpy.utils.register_tool(MyTool_Casting3, separator=True, group=False, after={MyTool_Casting2.bl_idname})

    bpy.utils.register_tool(MyTool_Sprue1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Sprue2, separator=True, group=False, after={MyTool_Sprue1.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue3, separator=True, group=False, after={MyTool_Sprue2.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Rotate, separator=True, group=False, after={MyTool_Sprue3.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Mirror, separator=True, group=False, after={MyTool_Sprue_Rotate.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Mouse, separator=True, group=False, after={MyTool_Sprue_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_SprueInitial, separator=True, group=False, after={MyTool_Sprue_Mouse.bl_idname})

    bpy.utils.register_tool(MyToolLastDamo, separator=True, group=False)
    bpy.utils.register_tool(MyToolLastDamo3, separator=True,
                            group=False, after={MyToolLastDamo.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo5, separator=True,
                            group=False, after={MyToolLastDamo3.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo7, separator=True,
                            group=False, after={MyToolLastDamo5.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo2, separator=True, group=False)
    bpy.utils.register_tool(MyToolLastDamo4, separator=True,
                            group=False, after={MyToolLastDamo2.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo6, separator=True,
                            group=False, after={MyToolLastDamo4.bl_idname})
    bpy.utils.register_tool(MyToolLastDamo8, separator=True,
                            group=False, after={MyToolLastDamo6.bl_idname})

    bpy.utils.register_tool(Tool_ResetCutMould)
    bpy.utils.register_tool(Tool_FinishCutMould, separator=True, group=False, after={Tool_ResetCutMould.bl_idname})
    bpy.utils.register_tool(Switch_CutMould1)
    bpy.utils.register_tool(Switch_CutMould2)

    bpy.utils.register_tool(public_add_shellcanal_MyTool, separator=True, group=False)
    bpy.utils.register_tool(delete_drag_shellcanal_MyTool, separator=True, group=False)

    bpy.utils.register_tool(dragcube_MyTool)
    bpy.utils.register_tool(adjustreceiver_MyTool)


def unregister_tools():
    bpy.utils.unregister_tool(MyTool)
    bpy.utils.unregister_tool(MyTool3)
    bpy.utils.unregister_tool(MyTool5)
    bpy.utils.unregister_tool(MyTool7)
    bpy.utils.unregister_tool(MyTool2)
    bpy.utils.unregister_tool(MyTool4)
    bpy.utils.unregister_tool(MyTool6)
    bpy.utils.unregister_tool(MyTool8)

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

    bpy.utils.unregister_tool(qiegeTool)
    bpy.utils.unregister_tool(qiegeTool2)
    bpy.utils.unregister_tool(qiegeTool3)

    bpy.utils.unregister_tool(MyTool_Label1)
    bpy.utils.unregister_tool(MyTool_Label2)
    bpy.utils.unregister_tool(MyTool_Label3)
    bpy.utils.unregister_tool(MyTool_Label_Mirror)
    bpy.utils.unregister_tool(MyTool_Label_Mouse)
    bpy.utils.unregister_tool(MyTool_LabelInitial)

    bpy.utils.unregister_tool(MyTool_Handle1)
    bpy.utils.unregister_tool(MyTool_Handle2)
    bpy.utils.unregister_tool(MyTool_Handle3)
    bpy.utils.unregister_tool(MyTool_Handle_Rotate)
    bpy.utils.unregister_tool(MyTool_Handle_Mirror)
    bpy.utils.unregister_tool(MyTool_Handle_Mouse)
    bpy.utils.unregister_tool(MyTool_HandleInitial)

    bpy.utils.unregister_tool(MyTool_Support1)
    bpy.utils.unregister_tool(MyTool_Support2)
    bpy.utils.unregister_tool(MyTool_Support3)
    bpy.utils.unregister_tool(MyTool_Support_Rotate)
    bpy.utils.unregister_tool(MyTool_Support_Mirror)
    bpy.utils.unregister_tool(MyTool_Support_Mouse)

    bpy.utils.unregister_tool(addcurve_MyTool)
    bpy.utils.unregister_tool(dragcurve_MyTool)
    bpy.utils.unregister_tool(smoothcurve_MyTool)
    bpy.utils.unregister_tool(addcurve_MyTool3)

    bpy.utils.unregister_tool(resetmould_MyTool)
    bpy.utils.unregister_tool(finishmould_MyTool)
    bpy.utils.unregister_tool(canalmould_MyTool)
    bpy.utils.unregister_tool(limitmould_MyTool)
    bpy.utils.unregister_tool(mirrormould_MyTool)

    bpy.utils.unregister_tool(resetsoundcanal_MyTool)
    bpy.utils.unregister_tool(finishsoundcanal_MyTool)
    bpy.utils.unregister_tool(rotatesoundcanal_MyTool)
    bpy.utils.unregister_tool(mirrorsoundcanal_MyTool)
    bpy.utils.unregister_tool(addsoundcanal_MyTool2)
    bpy.utils.unregister_tool(addsoundcanal_MyTool3)

    bpy.utils.unregister_tool(resetventcanal_MyTool)
    bpy.utils.unregister_tool(finishventcanal_MyTool)
    bpy.utils.unregister_tool(mirrorventcanal_MyTool)
    bpy.utils.unregister_tool(addventcanal_MyTool2)
    bpy.utils.unregister_tool(addventcanal_MyTool3)

    bpy.utils.unregister_tool(MyTool_Casting1)
    bpy.utils.unregister_tool(MyTool_Casting2)
    bpy.utils.unregister_tool(MyTool_Casting3)

    bpy.utils.unregister_tool(MyTool_Sprue1)
    bpy.utils.unregister_tool(MyTool_Sprue2)
    bpy.utils.unregister_tool(MyTool_Sprue3)
    bpy.utils.unregister_tool(MyTool_Sprue_Rotate)
    bpy.utils.unregister_tool(MyTool_Sprue_Mirror)
    bpy.utils.unregister_tool(MyTool_Sprue_Mouse)
    bpy.utils.unregister_tool(MyTool_SprueInitial)

    bpy.utils.unregister_tool(MyToolLastDamo)
    bpy.utils.unregister_tool(MyToolLastDamo3)
    bpy.utils.unregister_tool(MyToolLastDamo5)
    bpy.utils.unregister_tool(MyToolLastDamo7)
    bpy.utils.unregister_tool(MyToolLastDamo2)
    bpy.utils.unregister_tool(MyToolLastDamo4)
    bpy.utils.unregister_tool(MyToolLastDamo6)
    bpy.utils.unregister_tool(MyToolLastDamo8)

    bpy.utils.unregister_tool(Tool_ResetCutMould)
    bpy.utils.unregister_tool(Tool_FinishCutMould)
    bpy.utils.unregister_tool(Switch_CutMould1)
    bpy.utils.unregister_tool(Switch_CutMould2)

    bpy.utils.unregister_tool(public_add_shellcanal_MyTool)
    bpy.utils.unregister_tool(delete_drag_shellcanal_MyTool)

    bpy.utils.unregister_tool(dragcube_MyTool)
    bpy.utils.unregister_tool(adjustreceiver_MyTool)


