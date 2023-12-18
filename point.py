import bpy

class TEST_OT_doubleclick(bpy.types.Operator):

    bl_idname = "object.doubleclick"
    bl_label = "测试"
    bl_description = "test"

    __running = False

    @classmethod
    def is_running(cls):
        return cls.__running

    def modal(self, context, event):
        op_cls = TEST_OT_doubleclick
        active_obj = context.active_object

        # 重绘区域
        if context.area:
            context.area.tag_redraw()

        if not self.is_running():
            return {'FINISHED'}

        if event.type == 'LEFTMOUSE' and event.value == 'DOUBLE_CLICK':
             print('left mouse double click')

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        op_cls = TEST_OT_doubleclick
        
        if not self.is_running():
            context.window_manager.modal_handler_add(self)
            op_cls.__running = True
            return {'RUNNING_MODAL'}

        else:
            op_cls.__running = False
            return {'FINISHED'}



# UI
class TEST_PT_doubleclick(bpy.types.Panel):

    bl_label = "测试用例"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "test"
    
    def draw(self, context):
        op_cls = TEST_OT_doubleclick
        layout = self.layout
        if not op_cls.is_running():
            layout.operator(op_cls.bl_idname, text="开始", icon='PLAY')
        else:
            layout.operator(op_cls.bl_idname, text="结束", icon='PAUSE')
            
bpy.utils.register_class(TEST_OT_doubleclick)
bpy.utils.register_class(TEST_PT_doubleclick)