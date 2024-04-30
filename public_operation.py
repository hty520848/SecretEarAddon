import bpy
import blf
from .jiahou import frontToLocalThickening, frontFromLocalThickening, backFromLocalThickening, backToLocalThickening, \
    backup, forward
from .damo import backFromDamo, backToDamo
from .qiege import frontToQieGe, frontFromQieGe, backFromQieGe, backToQieGe
from .label import frontToLabel, frontFromLabel, backFromLabel, backToLabel
from .handle import frontToHandle, frontFromHandle, backFromHandle, backToHandle
from .support import frontToSupport, frontFromSupport, backFromSupport, backToSupport
from .sprue import frontToSprue, frontFromSprue, backFromSprue, backToSprue, submitSprue
from .create_mould.create_mould import frontToCreateMould, frontFromCreateMould, backToCreateMould, backFromCreateMould
from .create_mould.frame_style_eardrum.frame_style_eardrum import apply_frame_style_eardrum_template
from .sound_canal import frontToSoundCanal, frontFromSoundCanal, backFromSoundCanal, backToSoundCanal
from .vent_canal import frontToVentCanal, frontFromVentCanal, backFromVentCanal, backToVentCanal
from .casting import frontToCasting, frontFromCasting, backFromCasting, backToCasting
from .tool import getOverride, getOverride2, get_layer_collection
from .judge.judge import judge
from .utils.utils import utils_re_color


prev_properties_context = "RENDER"  # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来

is_msgbus_start = False  # 模块切换操作符是否启动

is_msgbus_start2 = False


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
    "DATA": "导出STL",
    "MATERIAL": "布局切换",
    "TEXTURE": "后期打磨"
}

prev_workspace = '布局'


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


# 在不同模式间切换时选择不同的材质
def change_mat_mould(type):
    #  type=0 RGB模式， type=1 顶点颜色模式
    mat = bpy.data.materials.get('Yellow')
    if mat:
        if type == 0:
            is_initial = False
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for node in nodes:
                if node.name == 'RGB':
                    is_initial = True
            if not is_initial:
                new_node = nodes.new(type="ShaderNodeRGB")
                new_node.outputs[0].default_value = (1.0, 0.319, 0.133, 1)
            for link in links:
                links.remove(link)
            links.new(nodes["RGB"].outputs[0], nodes["Principled BSDF"].inputs[0])
            links.new(nodes["Principled BSDF"].outputs[0], nodes["Material Output"].inputs[0])

        elif type == 1:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for link in links:
                links.remove(link)
            links.new(nodes["Color Attribute"].outputs[0], nodes["Principled BSDF"].inputs[0])
            links.new(nodes["Principled BSDF"].outputs[0], nodes["Material Output"].inputs[0])


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
        global processing_stage_dict
        global prev_workspace

        workspace = context.window.workspace.name

        current_tab = bpy.context.screen.areas[0].spaces.active.context
        name = "右耳"  # TODO 导入物体的名称
        obj = bpy.data.objects.get(name)
        if (obj != None):
            if (prev_properties_context != current_tab):
                context.window.cursor_warp(context.window.width // 2, context.window.height // 2)
                bpy.context.scene.var = 0

                # 重新上色
                # utils_re_color(bpy.context.scene.leftWindowObj, (1, 0.319, 0.133))
                # 左右耳切换时不改变
                if current_tab != 'MATERIAL':
                    # 在打磨和局部加厚模块时材质展示方式为顶点颜色
                    if (current_tab == 'RENDER' or current_tab == 'OUTPUT'):
                        change_mat_mould(1)
                    # 其余模块的材质展示方式为RGB颜色
                    else:
                        change_mat_mould(0)

                # 模块切换时根据不同的模块呈现不同的展示模式
                mat = bpy.data.materials.get("Yellow")

                # 支撑和排气孔默认展示模式为透明
                if (current_tab == 'PARTICLES' or current_tab == 'PHYSICS' or current_tab == 'CONSTRAINT'):
                    mat.blend_method = 'BLEND'
                    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                    bpy.context.scene.transparent3Enum = 'OP3'
                # 其余模块的材质展示方式为不透明
                else:
                    mat.blend_method = 'OPAQUE'
                    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                    bpy.context.scene.transparent3Enum = 'OP1'

                print(f'Previous Tab: {prev_properties_context}')
                print(f'Current Tab: {current_tab}')
                print("切换前场景中存在的文件:")
                print("~~~~~~~~~~~~~~~~~~~")
                selected_objs = bpy.data.objects
                for selected_obj in selected_objs:
                    print(selected_obj.name)
                print("~~~~~~~~~~~~~~~~~~~")
                print("-------------------")

                # 窗口切换时同步context
                if (workspace != prev_workspace):
                    print('窗口切换')
                    print('current_tab', current_tab)
                    print('prev_tab', prev_properties_context)
                    bpy.context.screen.areas[1].spaces.active.context = prev_properties_context

                if (current_tab == 'MATERIAL'):
                    print('MATERIAL')
                    print('prev_context', prev_properties_context)
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

                    bpy.context.screen.areas[0].spaces.active.context = prev_properties_context
                    current_tab = prev_properties_context


                    # 交换左右窗口物体
                    tar_obj = context.scene.leftWindowObj
                    ori_obj = context.scene.rightWindowObj
                    context.scene.leftWindowObj = ori_obj
                    context.scene.rightWindowObj = tar_obj
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = bpy.data.objects[ori_obj]
                    bpy.data.objects[ori_obj].select_set(True)

                    # 绘制字体
                    draw_font()

                # 模块切换
                current_process = processing_stage_dict[current_tab]
                prev_process = processing_stage_dict[prev_properties_context]

                if (current_process == '打磨'):
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
                            backToDamo()  # 打磨初始化,保存到打磨保存的状态
                    elif (prev_process == '创建模具'):
                        print("createMouldToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCreateMould()
                            backToDamo()
                    elif (prev_process == '编号'):
                        print("labelToDaMo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
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
                        print("VentCanalToDamo")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
                            backToDamo()


                elif (current_process == '局部加厚'):
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
                        print("VentCanalToLocalThick")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
                            backToLocalThickening()






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
                        print("VentCanalToQieGe")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
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
                        print("VentCanalToLabel")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
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
                            # 测试了从打磨到创建模具
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
                        print("VentCanalToCreateMould")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
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
                        print("VentCanalToHandle")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
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
                            backFromLabel()
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
                        print("VentCanalToSupport")
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
                    elif (prev_process == '排气孔'):
                        print("SprueToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
                            backToSupport()

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
                    elif (prev_process == '排气孔'):
                        print("SprueToSoundCanal")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
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
                    elif (prev_process == '排气孔'):
                        print("SprueToVentCanal")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
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
                    elif (prev_process == '排气孔'):
                        print("SprueToCasting")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
                            backToCasting()

                elif (current_process == '排气孔'):
                    if (prev_process == '局部加厚'):
                        print("LocalThickToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToSprue()
                    elif (prev_process == '打磨'):
                        print("DamoToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToSprue()
                    elif (prev_process == '切割'):
                        print("QieGeToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToSprue()
                    elif (prev_process == '编号'):
                        print("LabelToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLabel()
                            frontToSprue()
                    elif (prev_process == '创建模具'):
                        print("CreateMouldToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCreateMould()
                            frontToSprue()
                    elif (prev_process == '耳膜附件'):
                        print("HandleToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromHandle()
                            frontToSprue()
                    elif (prev_process == '支撑'):
                        print("SupportToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSupport()
                            frontToSprue()
                    elif (prev_process == '传声孔'):
                        print("SoundCanalToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSoundCanal()
                            frontToSprue()
                    elif (prev_process == '通气孔'):
                        print("VentCanalToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromVentCanal()
                            frontToSprue()
                    elif (prev_process == '铸造法软耳模'):
                        print("CastingToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCasting()
                            frontToSprue()


                elif (current_process == '导出STL'):
                    context.window.cursor_warp(context.window.width // 2, (context.window.height // 2) + 60);
                    # 弹出导出面板
                    bpy.ops.screen.userpref_show(section='SYSTEM')

                print("-------------------")
                print("切换后场景中存在的文件:")
                print("~~~~~~~~~~~~~~~~~~~")
                selected_objs = bpy.data.objects
                for selected_obj in selected_objs:
                    print(selected_obj.name)
                print("~~~~~~~~~~~~~~~~~~~")

                prev_properties_context = current_tab

                prev_workspace = workspace

        return {'PASS_THROUGH'}


class MsgbusCallBack2(bpy.types.Operator):
    bl_idname = "object.msgbuscallback2"
    bl_label = "绘制文本"

    def invoke(self, context, event):
        print("绘制文本invoke")
        global is_msgbus_start2
        is_msgbus_start2 = True
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        draw_font()
        # judge_flag = judge()
        # if not judge_flag:
        #     bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
        # bpy.data.objects['右耳'].select_set(True)


font_info_public = {
    "font_id": 0,
    "handler": None,
}


def draw_font():
    """Draw on the viewports"""
    # BLF drawing routine
    if bpy.context.window.workspace.name == '布局':
        override = getOverrideMain()
        region = override['region']
        if region.x == 0:
            PublicHandleClass.remove_handler()
            if bpy.context.scene.leftWindowObj == "右耳":
                PublicHandleClass.add_handler(
                    draw_callback_Red, (None, region.width - 100, region.height - 100, "R"))
                bpy.context.scene.activecollecion = '右耳'
            elif bpy.context.scene.leftWindowObj == "左耳":
                PublicHandleClass.add_handler(
                    draw_callback_Blue, (None, region.width - 100, region.height - 100, "L"))
                bpy.context.scene.activecollecion = '左耳'
            # blf.color(0, 0.0, 0.0, 0.0, 1.0)
            # blf.position(font_id, region.width - 100, region.height - 100, 0)
            # blf.size(font_id, 50)
            # blf.draw(font_id, text)

    elif bpy.context.window.workspace.name == '布局.001':
        override = getOverrideMain()
        region = override['region']
        # override2 = getOverrideMain2()
        # region2 = override2['region']
        if region.x == 0:
            PublicHandleClass.remove_handler()
            if bpy.context.scene.leftWindowObj == "右耳":
                PublicHandleClass.add_handler(
                    draw_callback_Red, (None, region.width - 100, region.height - 100, "R"))
                bpy.context.scene.activecollecionMirror = '右耳'
            elif bpy.context.scene.leftWindowObj == "左耳":
                PublicHandleClass.add_handler(
                    draw_callback_Blue, (None, region.width - 100, region.height - 100, "L"))
                bpy.context.scene.activecollecionMirror = '左耳'
        # if region2.x != 0:
        #     PublicHandleClass.remove_handler()
        #     PublicHandleClass.add_handler(draw_callback_Red, (None, region2.width - 100, region2.height - 100, "L"))


def draw_callback_Red(self, x, y, text):
    """Draw on the viewports"""
    # BLF drawing routine
    font_id = font_info_public["font_id"]
    blf.color(font_id, 1.0, 0.0, 0.0, 1.0)
    blf.position(font_id, x, y, 0)
    blf.size(font_id, 50)
    blf.draw(font_id, text)


def draw_callback_Blue(self, x, y, text):
    """Draw on the viewports"""
    # BLF drawing routine
    font_id = font_info_public["font_id"]
    blf.color(font_id, 0.0, 0.0, 1.0, 1.0)
    blf.position(font_id, x, y, 0)
    blf.size(font_id, 50)
    blf.draw(font_id, text)


class PublicHandleClass:
    _handler = None

    @classmethod
    def add_handler(cls, function, args=()):
        cls._handler = bpy.types.SpaceView3D.draw_handler_add(
            function, args, 'WINDOW', 'POST_PIXEL'
        )

    @classmethod
    def remove_handler(cls):
        if cls._handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(cls._handler, 'WINDOW')
            cls._handler = None


def getOverrideMain():
    # change this to use the correct Area Type context you want to process in
    area_type = 'VIEW_3D'
    areas = [
        area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(
            f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override


def getOverrideMain2():
    # change this to use the correct Area Type context you want to process in
    area_type = 'VIEW_3D'
    areas = [
        area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(
            f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[1],
        'region': [region for region in areas[1].regions if region.type == 'WINDOW'][0],
    }

    return override


class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "3D Model"

    my_string: bpy.props.StringProperty(name="", default="左右耳识别错误")

    def execute(self, context):
        pass
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        context.window.cursor_warp(context.window.width // 2, context.window.height // 2)
        return wm.invoke_props_dialog(self)




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


def msgbus_callback2(*args):
    global is_msgbus_start2
    if (not is_msgbus_start2):
        bpy.ops.object.msgbuscallback2('INVOKE_DEFAULT')


subscribe_to2 = (bpy.types.Object, "name")

bpy.msgbus.subscribe_rna(
    key=subscribe_to2,
    owner=object(),
    args=(1, 2, 3),
    notify=msgbus_callback2,
)

# 注册类
_classes = [
    BackUp1,
    Forward1,
    SwitchTest,
    MsgbusCallBack,
    MsgbusCallBack2,
    DialogOperator,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
