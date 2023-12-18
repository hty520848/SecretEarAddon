import bpy
from math import *
import bpy_extras
import mathutils
import bmesh
from bpy_extras import view3d_utils
from .jiahou import *
from .damo import *
from .qiege import *

prev_properties_context = None  # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来


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


def msgbus_callback(*args):
    '''
    hello
    '''
    global prev_properties_context

    # 结束掉之前的所有正在运行的model
    bpy.context.scene.var = 0

    current_tab = bpy.context.screen.areas[0].spaces.active.context
    print("当前激活的物体:", bpy.context.active_object.name)
    print("前面的上下文", prev_properties_context)
    print(f'Current Tab: {current_tab}')
    selected_objs = bpy.data.objects
    for selected_obj in selected_objs:
        print(selected_obj.name)
    if (current_tab == 'OUTPUT'):
        if (prev_properties_context == 'RENDER' or prev_properties_context == None):
            print("frontToLocalThick")
            override = getOverride()
            with bpy.context.temp_override(**override):
                backFromDamo()  # 打磨保存状态
                frontToLocalThickening()  # 局部加厚初始化
        elif (prev_properties_context == 'SCENE'):
            print("qieGeToLocalThick")
            override = getOverride()
            with bpy.context.temp_override(**override):
                frontFromQieGe()  # 退出切割
                backToLocalThickening()  # 局部加厚初始化
    elif (current_tab == 'RENDER'):
        if (prev_properties_context == 'OUTPUT'):
            print("LocalThickToDaMo")
            override = getOverride()
            with bpy.context.temp_override(**override):
                frontFromLocalThickening()  # 退出局部加厚
                backToDamo()  # 打磨初始化,保存到打磨保存的状态
        elif (prev_properties_context == 'SCENE'):
            print("QieGeToDamo")
            override = getOverride()
            with bpy.context.temp_override(**override):
                frontFromQieGe()  # 切割退出
                print("当前激活物体", bpy.context.active_object)
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                backToDamo()  # 打磨初始化,保存到打磨保存的状态
    elif (current_tab == 'SCENE'):
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

    print("---------")
    prev_properties_context = current_tab
    selected_objs = bpy.data.objects
    for selected_obj in selected_objs:
        print(selected_obj.name)
    print(",,,,,,")


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
    Forward1
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
