import bpy
from math import *
import bpy_extras
import mathutils
import bmesh
from bpy_extras import view3d_utils
from .jiahou import *
from .damo import *
from .qiege import *
from .label import *
from .handle import *
from .create_mould.create_mould import *
from .utils.utils import *
import time

prev_properties_context = None  # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来

is_msgbus_start = False  # 模块切换操作符是否启动

processing_stage_dict = {
    "OUTPUT": "局部加厚",
    "RENDER": "打磨",
    "SCENE": "切割",
    "WORLD": "创建模具",
}


class BackUp1(bpy.types.Operator):
    bl_idname = "obj.undo1"
    bl_label = "撤销"

    def execute(self, context):
        # 局部加厚模式下的单步撤回
        backup(context)
        return {'FINISHED'}


class Forward1(bpy.types.Operator):
    bl_idname = "obj.redo1"
    bl_label = "重做"

    def execute(self, context):
        # 局部加厚模式下的单步重做
        # if(bpy.context.scene.var == 5 or bpy.context.scene.var == 6 or bpy.context.scene.var == 7 or bpy.context.scene.var == 8 or bpy.context.scene.var == 9):
        forward(context)

        return {'FINISHED'}


class MsgbusCallBack(bpy.types.Operator):
    bl_idname = "object.msgbuscallback"
    bl_label = "功能切换"

    def invoke(self, context, event):
        print("模块切换invoke")
        global is_msgbus_start
        is_msgbus_start = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global prev_properties_context
        current_tab = bpy.context.screen.areas[0].spaces.active.context

        name = "右耳"  # TODO 导入物体的名称
        obj = bpy.data.objects.get(name)
        if (obj != None):
            if (prev_properties_context != current_tab):

                bpy.context.scene.var = 0

                print("前面的上下文", prev_properties_context)
                print(f'Current Tab: {current_tab}')
                selected_objs = bpy.data.objects
                for selected_obj in selected_objs:
                    print(selected_obj.name)

                if (current_tab == 'OUTPUT'):
                    if (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("DamoToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()  # 打磨保存状态
                            frontToLocalThickening()  # 局部加厚初始化
                    elif (prev_properties_context == 'VIEW_LAYER'):
                        print("qieGeToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromQieGe()  # 退出切割
                            backToLocalThickening()  # 局部加厚初始化
                    elif (prev_properties_context == 'MODIFIER'):
                        print("labelToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            backToLocalThickening()
                    elif (prev_properties_context == 'SCENE'):
                        print("createMouldToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCreateMould()
                            backToLocalThickening()
                    elif (prev_properties_context == 'OBJECT'):
                        print("HandleToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromHandle()
                            backToLocalThickening()

                elif (current_tab == 'RENDER'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToDaMo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLocalThickening()  # 退出局部加厚
                            backToDamo()  # 打磨初始化,保存到打磨保存的状态
                    elif (prev_properties_context == 'VIEW_LAYER'):
                        print("QieGeToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromQieGe()  # 切割退出
                            print("当前激活物体", bpy.context.active_object)
                            bpy.ops.wm.tool_set_by_id(
                                name="builtin.select_box")
                            backToDamo()  # 打磨初始化,保存到打磨保存的状态
                    elif (prev_properties_context == 'MODIFIER'):
                        print("labelToDaMo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            backToDamo()
                    elif (prev_properties_context == 'SCENE'):
                        print("createMouldToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCreateMould()
                            backToDamo()
                    elif (prev_properties_context == 'OBJECT'):
                        print("HandleToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromHandle()
                            backToDamo()

                elif (current_tab == 'VIEW_LAYER'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()  # 局部加厚完成
                            frontToQieGe()  # 切割初始化
                    elif (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("RenderToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()  # 打磨保存状态
                            frontToQieGe()  # 切割初始化
                    elif (prev_properties_context == 'MODIFIER'):
                        print("labelToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            backToQieGe()
                    elif (prev_properties_context == 'SCENE'):
                        print("createMouldToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCreateMould()
                            backToQieGe()
                    elif (prev_properties_context == 'OBJECT'):
                        print("HandleToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromHandle()
                            backToQieGe()

                elif (current_tab == 'MODIFIER'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()  # 局部加厚完成
                            frontToLabel()
                    elif (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("DamoToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()  # 打磨保存状态
                            frontToLabel()
                    elif (prev_properties_context == 'VIEW_LAYER'):
                        print("QieGeToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToLabel()
                    elif (prev_properties_context == 'SCENE'):
                        print("createMouldToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCreateMould()
                            frontToLabel()
                    elif (prev_properties_context == 'OBJECT'):
                        print("HandleToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromHandle()
                            frontToLabel()

                elif (current_tab == 'SCENE'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToCreateMould()
                    elif (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("DamoToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToCreateMould()
                    elif (prev_properties_context == 'VIEW_LAYER'):
                        print("QieGeToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToCreateMould()
                    elif (prev_properties_context == 'MODIFIER'):
                        print("LabelToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            backToCreateMould()
                    elif (prev_properties_context == 'OBJECT'):
                        print("HandleToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromHandle()
                            backToCreateMould()

                elif (current_tab == 'OBJECT'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToHandle()
                    elif (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("DamoToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToHandle()
                    elif (prev_properties_context == 'VIEW_LAYER'):
                        print("QieGeToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToHandle()
                    elif (prev_properties_context == 'MODIFIER'):
                        print("LabelToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            backToHandle()
                    elif (prev_properties_context == 'SCENE'):
                        print("CreateMouldToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCreateMould()
                            frontToHandle()

                print("---------")
                selected_objs = bpy.data.objects
                for selected_obj in selected_objs:
                    print(selected_obj.name)
                print(",,,,,,")

        prev_properties_context = current_tab

        return {'PASS_THROUGH'}


def msgbus_callback(*args):
    global is_msgbus_start
    if (not is_msgbus_start):
        bpy.ops.object.msgbuscallback('INVOKE_DEFAULT')


# 监听属性
subscribe_to = bpy.types.SpaceProperties, 'context'

# 发布订阅，监听context变化
bpy.msgbus.subscribe_rna(
    key=subscribe_to,
    owner=object(),
    args=(1, 2, 3),
    notify=msgbus_callback,
)

# 注册类
_classes = [
    BackUp1,
    Forward1,
    MsgbusCallBack
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
