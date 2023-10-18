import bpy


class LocalOrGlobalAddArea(bpy.types.Operator):
    bl_idname = "obj.addarea"
    bl_label = "AddArea"

    def execute(self, context):
        # 进入雕刻模式
        bpy.ops.object.mode_set(mode="SCULPT")
        # bpy.ops.object.mode_set(mode="SCULPT")
        # 进入遮罩模式，笔刷方向设置为扩大区域
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Mask")
        bpy.data.brushes["Mask"].direction = "ADD"
        return {'FINISHED'}


class LocalOrGlobalReduceArea(bpy.types.Operator):
    bl_idname = "obj.reducearea"
    bl_label = "ReduceArea"

    # @classmethod
    # def poll(cls,context):
    #     return context.active_object is not None

    def execute(self, context):
        # 进入雕刻模式
        bpy.ops.object.mode_set(mode="SCULPT")
        # 进入遮罩模式，笔刷方向设置为缩小区域
        bpy.ops.wm.tool_set_by_id(name="built_brush.Mask")
        bpy.data.brushes["Mask"].direction = "SUBTRACT"
        return {'FINISHED'}

    # def invoke(self,context,event):
    #     #进入遮罩模式,笔刷方向设置为缩小区域
    #     bpy.ops.wm.tool_set_by_id(name="builtin_brush.Mask")
    #     bpy.data.brushes["Mask"].direction="SUBTRACT"
    #     context.window_manager.modal_handler_add(self)
    #     return {'RUNNING_MODAL'}

    # def modal(self,context,event):

    #     # self.execute(context)

    #     if event.type=="RIGHTMOUSE":
    #         return {'CANCELLED'}

    #     return {'RUNNING_MODAL'}


# class LocalOrGlobalJiaHou(bpy.types.Operator):

class LocalOrGlobalJiaHou(bpy.types.Operator):
    bl_idname = "obj.jiahou"
    bl_label = "JiaHou"

    def execute(self, context):
        # 进入雕刻模式
        bpy.ops.object.mode_set(mode="SCULPT")
        # 提取所框选的遮罩
        bpy.ops.mesh.paint_mask_extract()
        # 将偏移量设为1，向外加厚
        bpy.data.objects["Mesh"].modifiers["geometry_extract_solidify"].offset = 1
        bpy.data.objects["Mesh"].modifiers["geometry_extract_solidify"].thickness += 1

        return {'FINISHED'}


# 注册类
_classes = [
    LocalOrGlobalAddArea,
    LocalOrGlobalReduceArea,
    LocalOrGlobalJiaHou,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
