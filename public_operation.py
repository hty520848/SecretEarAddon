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
from .sound_canal import *
from .vent_canal import *
from .casting import *
from .utils.utils import *
import time

prev_properties_context_right = "RENDER"  # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来
prev_properties_context_left = "RENDER"

is_msgbus_start = False  # 模块切换操作符是否启动

is_pause = False

processing_stage_dict = {
    "RENDER": "打磨",
    "OUTPUT": "局部加厚",
    "VIEW_LAYER": "切割",
    "SCENE": "创建模具",
    "WORLD": "传声孔",
    "COLLECTION": "通气孔",
    "OBJECT": "耳膜附件",
    "MODIFIER": "编号",
    "PARTICLES": "铸造法软耳模",
    "PHYSICS": "支撑",
    "CONSTRAINT": "排气孔",
    "DATA": "后期打磨",
    "MATERIAL": "布局切换"
}

def get_prev_properties_context_right():
    global prev_properties_context_right
    return prev_properties_context_right

def set_pause(pause):
    global is_pause
    is_pause = pause

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
        global prev_properties_context_right
        global prev_properties_context_left
        global processing_stage_dict
        global is_pause

        workspace = context.window.workspace.name

        if not is_pause:
            if workspace == '布局':
                current_tab = bpy.context.screen.areas[0].spaces.active.context
            elif workspace == '布局.001':
                current_tab = bpy.context.screen.areas[0].spaces.active.context
            name = "右耳"  # TODO 导入物体的名称
            obj = bpy.data.objects.get(name)
            if (obj != None):
                is_right_changed = (prev_properties_context_right != current_tab) and context.scene.leftWindowObj == "右耳"
                is_left_changed = (prev_properties_context_left != current_tab) and context.scene.leftWindowObj == "左耳"
                if (is_right_changed or is_left_changed):
                    bpy.context.scene.var = 0
                    if is_right_changed:
                        print(f'Previous RTab: {prev_properties_context_right}')
                        print(f'Current Tab: {current_tab}')
                    elif is_left_changed:
                        print(f'Previous LTab: {prev_properties_context_left}')
                        print(f'Current Tab: {current_tab}')
                    # print("切换前场景中存在的文件:")
                    # print("~~~~~~~~~~~~~~~~~~~")
                    # selected_objs = bpy.data.objects
                    # for selected_obj in selected_objs:
                    #     print(selected_obj.name)
                    # print("~~~~~~~~~~~~~~~~~~~")
                    # print("-------------------")
                    # 左右窗口切换
                    if (current_tab == 'MATERIAL'):
                        # print('MATERIAL')
                        # print('prev_context', prev_properties_context_right)
                        override1 = getOverride()
                        with bpy.context.temp_override(**override1):
                            active_obj = bpy.context.active_object
                            print('active_obj', active_obj.name)
                            bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
                            bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                            active_layer_collection = bpy.context.view_layer.active_layer_collection
                            print('active_colletion', active_layer_collection.name)
                            if active_layer_collection.name == 'Right':
                                my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Left')
                                bpy.context.view_layer.active_layer_collection = my_layer_collection
                            elif active_layer_collection.name == 'Left':
                                my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Right')
                                bpy.context.view_layer.active_layer_collection = my_layer_collection
                            override2 = getOverride2()
                            with bpy.context.temp_override(**override2):
                                active_obj = bpy.context.active_object
                                print('active_obj', active_obj.name)
                                bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
                                bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                        
                        # 交换左右窗口物体
                        tar_obj = context.scene.leftWindowObj
                        ori_obj = context.scene.rightWindowObj
                        context.scene.leftWindowObj = ori_obj
                        context.scene.rightWindowObj = tar_obj

                        # 将激活物体换成右边的物体
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = bpy.data.objects[ori_obj]
                        bpy.data.objects[ori_obj].select_set(True)

                        # 将流程置为上一个操作的流程
                        if workspace == '布局':
                            # bpy.context.screen.areas[0].spaces.active.context = prev_properties_context_right
                            if context.scene.leftWindowObj == "右耳":
                                bpy.context.screen.areas[0].spaces.active.context = prev_properties_context_right
                                current_tab = prev_properties_context_right
                            else:
                                bpy.context.screen.areas[0].spaces.active.context = prev_properties_context_left
                                current_tab = prev_properties_context_left
                            
                        elif workspace == '布局.001':
                            # bpy.context.screen.areas[0].spaces.active.context = prev_properties_context_right
                            if context.scene.leftWindowObj == "右耳":
                                bpy.context.screen.areas[0].spaces.active.context = prev_properties_context_right
                                current_tab = prev_properties_context_right
                            else:
                                bpy.context.screen.areas[0].spaces.active.context = prev_properties_context_left
                                current_tab = prev_properties_context_left
                            

                    # 模块切换
                    current_process = processing_stage_dict[current_tab]
                    if context.scene.leftWindowObj == "右耳":
                        prev_process = processing_stage_dict[prev_properties_context_right]
                    else:
                        prev_process = processing_stage_dict[prev_properties_context_left]
                    if (current_process == '局部加厚'):
                        if (prev_process == '打磨'):
                            print("DamoToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()  # 打磨保存状态
                                frontToLocalThickening()  # 局部加厚初始化
                        elif (prev_process == '切割'):
                            print("qieGeToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromQieGe()  # 退出切割
                                backToLocalThickening()  # 局部加厚初始化
                        elif (prev_process == '编号'):
                            print("labelToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToLocalThickening()
                        elif (prev_process == '创建模具'):
                            print("createMouldToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCreateMould()
                                backToLocalThickening()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromHandle()
                                backToLocalThickening()
                        elif (prev_process == '支撑'):
                            print("SupportToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToLocalThickening()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSoundCanal()
                                backToLocalThickening()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromVentCanal()
                                backToLocalThickening()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToLocalThick")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToLocalThickening()



                    elif (current_process == '打磨'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToDaMo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLocalThickening()  # 退出局部加厚
                                backToDamo()  # 打磨初始化,保存到打磨保存的状态
                        elif (prev_process == '切割'):
                            print("QieGeToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromQieGe()  # 切割退出
                                # print("当前激活物体", bpy.context.active_object)
                                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                                backToDamo()  # 打磨初始化,保存到打磨保存的状态
                        elif (prev_process == '编号'):
                            print("labelToDaMo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToDamo()
                        elif (prev_process == '创建模具'):
                            print("createMouldToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCreateMould()
                                backToDamo()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromHandle()
                                backToDamo()
                        elif (prev_process == '支撑'):
                            print("SupportToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToDamo()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSoundCanal()
                                backToDamo()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromVentCanal()
                                backToDamo()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToDamo")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToDamo()


                    elif (current_process == '切割'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()  # 局部加厚完成
                                frontToQieGe()  # 切割初始化
                        elif (prev_process == '打磨'):
                            print("damoToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()  # 打磨保存状态
                                frontToQieGe()  # 切割初始化
                        elif (prev_process == '编号'):
                            print("labelToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToQieGe()
                        elif (prev_process == '创建模具'):
                            print("createMouldToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCreateMould()
                                backToQieGe()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromHandle()
                                backToQieGe()
                        elif (prev_process == '支撑'):
                            print("SupportToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToQieGe()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSoundCanal()
                                backToQieGe()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromVentCanal()
                                backToQieGe()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToQieGe")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToQieGe()


                    elif (current_process == '编号'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()  # 局部加厚完成
                                frontToLabel()
                        elif (prev_process == '打磨'):
                            print("DamoToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()  # 打磨保存状态
                                frontToLabel()
                        elif (prev_process == '切割'):
                            print("QieGeToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToLabel()
                        elif (prev_process == '创建模具'):
                            print("createMouldToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCreateMould()
                                frontToLabel()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromHandle()
                                frontToLabel()
                        elif (prev_process == '支撑'):
                            print("SupportToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToLabel()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromSoundCanal()
                                frontToLabel()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromVentCanal()
                                frontToLabel()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToLabel")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToLabel()

                    elif (current_process == '创建模具'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()
                                frontToCreateMould()
                        elif (prev_process == '打磨'):
                            print("DamoToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()
                                frontToCreateMould()
                        elif (prev_process == '切割'):
                            print("QieGeToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToCreateMould()
                        elif (prev_process == '编号'):
                            print("LabelToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToCreateMould()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromHandle()
                                backToCreateMould()
                        elif (prev_process == '支撑'):
                            print("SupportToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToCreateMould()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSoundCanal()
                                backToCreateMould()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromVentCanal()
                                backToCreateMould()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToCreateMould")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToCreateMould()


                    elif (current_process == '耳膜附件'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()
                                frontToHandle()
                        elif (prev_process == '打磨'):
                            print("DamoToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()
                                frontToHandle()
                        elif (prev_process == '切割'):
                            print("QieGeToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToHandle()
                        elif (prev_process == '编号'):
                            print("LabelToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToHandle()
                        elif (prev_process == '创建模具'):
                            print("CreateMouldToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCreateMould()
                                frontToHandle()
                        elif (prev_process == '支撑'):
                            print("SupportToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToHandle()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromSoundCanal()
                                frontToHandle()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromVentCanal()
                                frontToHandle()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToHandle")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToHandle()


                    elif (current_process == '支撑'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()
                                frontToSupport()
                        elif (prev_process == '打磨'):
                            print("DamoToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()
                                frontToSupport()
                        elif (prev_process == '切割'):
                            print("QieGeToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToSupport()
                        elif (prev_process == '编号'):
                            print("LabelToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                frontToSupport()
                        elif (prev_process == '创建模具'):
                            print("CreateMouldToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCreateMould()
                                frontToSupport()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromHandle()
                                frontToSupport()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromSoundCanal()
                                frontToSupport()
                        elif (prev_process == '通气孔'):
                            print("SoundCanalToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromVentCanal()
                                frontToSupport()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToSupport")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCasting()
                                frontToSupport()

                    elif (current_process == '传声孔'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()
                                frontToSoundCanal()
                        elif (prev_process == '打磨'):
                            print("DamoToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()
                                frontToSoundCanal()
                        elif (prev_process == '切割'):
                            print("QieGeToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToSoundCanal()
                        elif (prev_process == '编号'):
                            print("LabelToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToSoundCanal()
                        elif (prev_process == '创建模具'):
                            print("CreateMouldToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCreateMould()
                                frontToSoundCanal()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromHandle()
                                backToSoundCanal()
                        elif (prev_process == '支撑'):
                            print("SupportToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToSoundCanal()
                        elif (prev_process == '通气孔'):
                            print("VentCanalToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromVentCanal()
                                backToSoundCanal()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToSoundCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToSoundCanal()

                    elif (current_process == '通气孔'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()
                                frontToVentCanal()
                        elif (prev_process == '打磨'):
                            print("DamoToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()
                                frontToVentCanal()
                        elif (prev_process == '切割'):
                            print("QieGeToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToVentCanal()
                        elif (prev_process == '编号'):
                            print("LabelToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromLabel()
                                backToVentCanal()
                        elif (prev_process == '创建模具'):
                            print("CreateMouldToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCreateMould()
                                frontToVentCanal()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromHandle()
                                backToVentCanal()
                        elif (prev_process == '支撑'):
                            print("SupportToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToVentCanal()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromSoundCanal()
                                frontToVentCanal()
                        elif (prev_process == '铸造法软耳模'):
                            print("CastingToVentCanal")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromCasting()
                                backToVentCanal()

                    elif (current_process == '铸造法软耳模'):
                        if (prev_process == '局部加厚'):
                            print("LocalThickToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLocalThickening()
                                frontToCasting()
                        elif (prev_process == '打磨'):
                            print("DamoToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromDamo()
                                frontToCasting()
                        elif (prev_process == '切割'):
                            print("QieGeToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromQieGe()
                                frontToCasting()
                        elif (prev_process == '编号'):
                            print("LabelToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromLabel()
                                frontToCasting()
                        elif (prev_process == '创建模具'):
                            print("CreateMouldToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromCreateMould()
                                frontToCasting()
                        elif (prev_process == '耳膜附件'):
                            print("HandleToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromHandle()
                                frontToCasting()
                        elif (prev_process == '支撑'):
                            print("SupportToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                frontFromSupport()
                                backToCasting()
                        elif (prev_process == '传声孔'):
                            print("SoundCanalToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromSoundCanal()
                                frontToCasting()
                        elif (prev_process == '通气孔'):
                            print("VentCanalToCasting")
                            override = getOverride()
                            with bpy.context.temp_override(**override):
                                backFromVentCanal()
                                frontToCasting()
                    # print("-------------------")
                    # print("切换后场景中存在的文件:")
                    # print("~~~~~~~~~~~~~~~~~~~")
                    # selected_objs = bpy.data.objects
                    # for selected_obj in selected_objs:
                    #     print(selected_obj.name)
                    # print("~~~~~~~~~~~~~~~~~~~")

            if context.scene.leftWindowObj == "右耳":
                prev_properties_context_right = current_tab
            else:
                prev_properties_context_left = current_tab

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
