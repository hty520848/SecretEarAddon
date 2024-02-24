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
from .support import *
from .create_mould.create_mould import *
from .create_mould.frame_style_eardrum.frame_style_eardrum import *
from .utils.utils import *
import time

prev_properties_context = None  # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来

is_msgbus_start = False         #模块切换操作符是否启动

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

class SwitchTest(bpy.types.Operator):
    bl_idname = "object.switchtestfunc"
    bl_label = "功能测试"

    def invoke(self, context, event):
        # 复制一份挖孔前的模型以备用
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        apply_frame_style_eardrum_template()
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

        workspace = context.window.workspace.name

        if workspace == '布局':
            current_tab = bpy.context.screen.areas[1].spaces.active.context
        elif workspace == '布局.001':
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

                # 左右窗口切换
                if (current_tab == 'MATERIAL'):
                    print('MATERIAL')
                    print('prev_context',prev_properties_context)
                    override1 =getOverride()
                    with bpy.context.temp_override(**override1):
                        active_obj = bpy.context.active_object
                        print('active_obj',active_obj.name)
                        bpy.ops.object.hide_collection(collection_index=2,  extend=False,toggle=True)
                        bpy.ops.object.hide_collection(collection_index=1,  extend=False,toggle=True)
                        active_layer_collection = bpy.context.view_layer.active_layer_collection
                        print('active_colletion',active_layer_collection.name)
                        if active_layer_collection.name == 'Right':
                            my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Left')
                            bpy.context.view_layer.active_layer_collection = my_layer_collection
                        elif active_layer_collection.name == 'Left':
                            my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Right')
                            bpy.context.view_layer.active_layer_collection = my_layer_collection
                        override2 =getOverride2()    
                        with bpy.context.temp_override(**override2):
                            active_obj = bpy.context.active_object
                            print('active_obj',active_obj.name)
                            bpy.ops.object.hide_collection(collection_index=2,  extend=False,toggle=True)
                            bpy.ops.object.hide_collection(collection_index=1,  extend=False,toggle=True)
                    if prev_properties_context == None:
                        if workspace == '布局':
                            bpy.context.screen.areas[1].spaces.active.context = 'RENDER'
                        elif workspace == '布局.001':
                            bpy.context.screen.areas[0].spaces.active.context = 'RENDER'
                    else:
                        if workspace == '布局':
                            bpy.context.screen.areas[1].spaces.active.context = prev_properties_context
                        elif workspace == '布局.001':
                            bpy.context.screen.areas[0].spaces.active.context = prev_properties_context

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
                    elif (prev_properties_context == 'PHYSICS'):
                        print("SupportToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
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
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
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
                    elif (prev_properties_context == 'PHYSICS'):
                        print("SupportToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
                            backToDamo()


                elif (current_tab == 'VIEW_LAYER'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()  # 局部加厚完成
                            frontToQieGe()  # 切割初始化
                    elif (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("damoToQieGe")
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
                    elif (prev_properties_context == 'PHYSICS'):
                        print("SupportToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
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
                    elif (prev_properties_context == 'PHYSICS'):
                        print("SupportToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
                            backToLabel()

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
                    elif (prev_properties_context == 'PHYSICS'):
                        print("SupportToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
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
                    elif (prev_properties_context == 'PHYSICS'):
                        print("SupportToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
                            backToHandle()


                elif (current_tab == 'PHYSICS'):
                    if (prev_properties_context == 'OUTPUT'):
                        print("LocalThickToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToSupport()
                    elif (prev_properties_context == 'RENDER' or prev_properties_context == None):
                        print("DamoToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToSupport()
                    elif (prev_properties_context == 'VIEW_LAYER'):
                        print("QieGeToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToSupport()
                    elif (prev_properties_context == 'MODIFIER'):
                        print("LabelToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            frontToSupport()
                    elif (prev_properties_context == 'SCENE'):
                        print("CreateMouldToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCreateMould()
                            frontToSupport()
                    elif (prev_properties_context == 'OBJECT'):
                        print("HandleToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromHandle()
                            frontToSupport()

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
    SwitchTest,
    MsgbusCallBack
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
