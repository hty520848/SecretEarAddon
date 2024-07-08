import bpy
import blf
from .jiahou import frontToLocalThickening, frontFromLocalThickening, backFromLocalThickening, backToLocalThickening, \
    backup, forward
from .damo import backFromDamo, backToDamo, frontFromDamo, frontToDamo, set_modal_start_false
from .create_tip.qiege import frontToQieGe, frontFromQieGe, backFromQieGe, backToQieGe
from .label import frontToLabel, frontFromLabel, backFromLabel, backToLabel
from .handle import frontToHandle, frontFromHandle, backFromHandle, backToHandle
from .support import frontToSupport, frontFromSupport, backFromSupport, backToSupport
from .sprue import frontToSprue, frontFromSprue, backFromSprue, backToSprue
from .create_mould.create_mould import frontToCreateMould, frontFromCreateMould, backToCreateMould, backFromCreateMould
from .create_mould.frame_style_eardrum.frame_style_eardrum import apply_frame_style_eardrum_template
from .sound_canal import frontToSoundCanal, frontFromSoundCanal, backFromSoundCanal, backToSoundCanal
from .vent_canal import frontToVentCanal, frontFromVentCanal, backFromVentCanal, backToVentCanal
from .casting import frontToCasting, frontFromCasting, backFromCasting, backToCasting
from .last_damo import frontToLastDamo, frontFromLastDamo, last_set_modal_start_false
from .create_tip.cut_mould import frontToCutMould, frontFromCutMould
from .tool import getOverride, getOverride2, get_layer_collection, change_mat_mould

prev_properties_context = "RENDER"       # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来

before_cut_mould = "打磨"              # 保存切割模具之前的模块,用于切割模具之后判断是否回退


#主要用于左右耳窗口切换,  每次切换模块  的时候记录当前窗口的当前模块和上一个模块
switch_R_current = "RENDER"             #右耳窗口    记录右耳切换到左耳的时候,记录点击 切换 模块之前的模块
switch_R_prev = "RENDER"                #右耳窗口    记录右耳切换到左耳的时候,记录点击 切换 模块之前的模块的上一个模块
switch_L_current = "RENDER"             #左耳窗口    记录左耳切换到右耳的时候,记录点击 切换 模块之前的模块
switch_L_prev = "RENDER"                #左耳窗口    记录左耳切换到右耳的时候,记录点击 切换 模块之前的模块的上一个模块


is_fallback = False                     #主要用于判断模块是否需要回退  点击排气孔的按钮,检测是否存在铸造法;经过铸造法之后才能够使用排气孔,否则回退到之前的模块




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
    "DATA": "布局切换",
    "MATERIAL": "切割模具",
    "TEXTURE": "后期打磨"
}

# 记录顺序执行的流程列表
order_processing_list = ["打磨", "局部加厚", "切割", "创建模具", "传声孔", "通气孔", "耳膜附件", "编号",
                         "铸造法软耳模", "支撑", "排气孔", "布局切换", "切割模具", "后期打磨"]


prev_workspace = '布局'



#记录左右耳切换时,点击切换模块之前的上一个模块    主要用于点击切换模块之后设置激活的模块物体   bpy.context.screen.areas[1].spaces.active.context = right_context
#只有在点击切换模块按钮之前的时候才会赋值记录该参数的值
right_context = 'RENDER'
left_context = 'RENDER'


'''
模块切换逻辑:
    正常在单个窗口切换模块的时候,点击下面的模块按钮,通过current_tab和prev_properties_context判断当前模块和上一个模块
    左右耳之间进行切换的时候,进入 MATERIAL 模块
        通过switchR/L变量,手动为current_tab和prev_properties_context赋值,使其回退一步
        再通过right/left_context设置系统当前激活的模块,使得上一步执行完毕后再由回退的模块切换回当前模块



Demo:
    导入文件之后初始化在右耳模块,由打磨切换到环切,再由环切切换到附件模块
    点击切换按钮切花到左耳,此时默认激活再打磨模块,  '再点击切换按钮切换到右耳'
    第二次点击切换按钮由左耳切换到右耳的时候:
        进入切换的model中: current_tab为 MATERIAL,即左右耳切换,prev_properties_context为 RNDER ,即打磨模块
                        进入MATERIAL的分支语句,首先交换左右耳集合中的物体,右耳集合中为经历了环切提交后,添加了附件的物体
                        再根据switchR/L将current_tab赋值为环切模块,prev_properties_context为附件模块
                        使得右耳集合中的物体从附件回退到环切
                        根据bpy.context.screen.areas[1].spaces.active.context = right/left_context设置当前系统中激活的模块为附件
                        但是此时current_tab并未改变,下次重新进入model的时候current_tab获取当前激活模块为附件,上一个模块prev_properties_context为环切
                        系统再次从回退的环切切换到附件模块
'''







class BackUp(bpy.types.Operator):
    bl_idname = "obj.undo1"
    bl_label = "撤销"

    def execute(self, context):
        # 局部加厚模式下的单步撤回
        backup(context)
        return {'FINISHED'}


class Forward(bpy.types.Operator):
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
    
# 标记当前切换是否结束
flag = True
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
        global prev_workspace,left_context,right_context

        global switch_R_current
        global switch_R_prev
        global switch_L_current
        global switch_L_prev
        global flag
        global is_fallback
        global order_processing_list
        global before_cut_mould

        workspace = context.window.workspace.name
        current_tab = bpy.context.screen.areas[0].spaces.active.context
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        if (obj != None):
            if (prev_properties_context != current_tab and flag):
                # 正在切换
                flag = False
                # context.window.cursor_warp(context.window.width // 2, context.window.height // 2)

                #将所有模块的model都关闭
                bpy.context.scene.var = 0

                # 重新上色
                # utils_re_color(bpy.context.scene.leftWindowObj, (1, 0.319, 0.133))
                # 在打磨和局部加厚模块时材质展示方式为顶点颜色
                if (current_tab == 'RENDER' or current_tab == 'OUTPUT'):
                    change_mat_mould(1)
                # 其余模块的材质展示方式为RGB颜色
                else:
                    change_mat_mould(0)

                # 模块切换时根据不同的模块呈现不同的展示模式
                mat = bpy.data.materials.get("Yellow")

                # 铸造法默认展示模式为透明
                if (current_tab == 'PARTICLES'):
                    mat.blend_method = 'BLEND'
                    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                    bpy.context.scene.transparent3Enum = 'OP3'
                # 排气孔默认展示模式为透明
                elif (current_tab == 'CONSTRAINT'):
                    mat.blend_method = 'BLEND'
                    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                    bpy.context.scene.transparent3Enum = 'OP3'
                # 软耳膜支撑显示为透明,硬耳膜支撑显示为非透明
                elif (current_tab == 'PHYSICS'):
                    name = bpy.context.scene.leftWindowObj
                    casting_name = name + "CastingCompare"
                    casting_compare_obj = bpy.data.objects.get(casting_name)
                    if(casting_compare_obj != None):
                        mat.blend_method = 'BLEND'
                        mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                        bpy.context.scene.transparent3Enum = 'OP3'
                # 其余模块的材质展示方式为不透明
                else:
                    mat.blend_method = 'OPAQUE'
                    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                    bpy.context.scene.transparent3Enum = 'OP1'


                print("--------------------------------------------------------------------------------")
                print(f'Previous Tab: {prev_properties_context}')
                print(f'Current Tab: {current_tab}')
                print("切换前场景中存在的文件:")
                print("~~~~~~~~~~~~~~~~~~~")
                selected_objs = bpy.data.objects
                for selected_obj in selected_objs:
                    print(selected_obj.name)
                print("~~~~~~~~~~~~~~~~~~~")

                # 窗口切换时同步context
                if (workspace != prev_workspace):
                    print('窗口切换')
                    print('current_tab', current_tab)
                    print('prev_tab', prev_properties_context)
                    bpy.context.screen.areas[0].spaces.active.context = prev_properties_context
                    bpy.context.screen.areas[0].spaces.active.context = prev_properties_context


                #点击左右耳切换模块的按钮
                if (current_tab == 'DATA'):
                    rightWindowObj = bpy.data.objects.get("右耳")
                    leftWindowObj = bpy.data.objects.get("左耳")
                    if leftWindowObj != None and rightWindowObj != None:
                        print('DATA')
                        print('prev_context', prev_properties_context)
                        is_fallback = True
                        override1 = getOverride()
                        with bpy.context.temp_override(**override1):
                            #切换窗口中的物体:  左边大窗口和右边小窗口两个窗口中有两个公共集合(左耳集合和右耳集合)
                            #初始的时候左边大窗口中右耳集合被显示出来,左耳集合被隐藏;右边小窗口中左耳集合被显示出来,右耳集合被隐藏
                            #点击切换按钮后每个窗口中显示和隐藏的集合会反转,将隐藏的显示出来,显示的隐藏起来,达到交换窗口物体的目的
                            bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
                            bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                            active_layer_collection = bpy.context.view_layer.active_layer_collection
                            # print('active_colletion', active_layer_collection.name)
                            if active_layer_collection.name == 'Right':
                                my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Left')
                                bpy.context.view_layer.active_layer_collection = my_layer_collection
                            elif active_layer_collection.name == 'Left':
                                my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Right')
                                bpy.context.view_layer.active_layer_collection = my_layer_collection
                            override2 = getOverride2()
                            with bpy.context.temp_override(**override2):
                                active_obj = bpy.context.active_object
                                # print('active_obj', active_obj.name)
                                bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
                                bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)



                        #此时的name表示的是切换之前的集合物体
                        name = context.scene.leftWindowObj
                        if name =='右耳':
                            right_context = prev_properties_context
                            bpy.context.screen.areas[0].spaces.active.context = left_context
                            bpy.context.screen.areas[0].spaces.active.context = left_context
                        else:
                            left_context = prev_properties_context
                            bpy.context.screen.areas[0].spaces.active.context = right_context
                            bpy.context.screen.areas[0].spaces.active.context = right_context
                        print('left_context',left_context)
                        print('right_context',right_context)


                        # 交换左右窗口物体(两个集合隐藏与显示的反转)
                        #leftWindowObj 和 rightWindowObj 分别记录左边大窗口和右边小窗口中操作的集合(左耳还是右耳)
                        tar_obj = context.scene.leftWindowObj
                        ori_obj = context.scene.rightWindowObj
                        context.scene.leftWindowObj = ori_obj
                        context.scene.rightWindowObj = tar_obj
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = bpy.data.objects[ori_obj]
                        bpy.data.objects[ori_obj].select_set(True)


                        #此时的name表示的是切换之后窗口中的集合物体
                        #点击切换模块按钮之后,根据之前左右耳切换中保存的记录switchR/L重置current_tab,prev_properties_context
                        #比如点击切换之前右耳由 切割模块切换到附件模块 再点击切换按钮;之后由左耳切回到右耳的时候
                        #重置重置current_tab,prev_properties_context,让物体由附件切回环切,再由环切切换回附件,使得附件的model被激活能够操作
                        name = context.scene.leftWindowObj  # 点击切换模块之后 左边大窗口中存储操作的物体
                        if (name == "右耳"):
                            current_tab = switch_R_current
                            prev_properties_context = switch_R_current
                        elif (name == "左耳"):
                            current_tab = switch_L_current
                            prev_properties_context = switch_L_current

                        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                        print("左右耳模块切换之后重置的current_tab",prev_properties_context)
                        print("current_tab:",current_tab)
                        print("prev_properties_context:",prev_properties_context)
                        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


                        # 绘制字体
                        draw_font()

                    else:
                        if leftWindowObj == None:
                            now_context = prev_properties_context
                            bpy.context.screen.areas[0].spaces.active.context = now_context
                            bpy.context.screen.areas[0].spaces.active.context = now_context
                            current_tab = prev_properties_context
                        else:
                            now_context = prev_properties_context
                            bpy.context.screen.areas[0].spaces.active.context = now_context
                            bpy.context.screen.areas[0].spaces.active.context = now_context
                            current_tab = prev_properties_context


                # if (current_tab == 'DATA'):
                #     #将导出菜单变量设置为True,弹出导出菜单
                #     # 重置current_tab,prev_properties_context,让物体能够从导出按钮切换回之前的模块并且激活其modal
                #     name = context.scene.leftWindowObj
                #     #记录点击导出按钮前的上一个模块,将改模块提交
                #     submit_process = None
                #     if (name == "右耳"):
                #         current_tab = switch_R_current
                #         prev_properties_context = switch_R_current
                #         bpy.context.screen.areas[1].spaces.active.context = switch_R_current
                #         bpy.context.screen.areas[0].spaces.active.context = switch_R_current
                #         submit_process = processing_stage_dict[switch_R_current]
                #     elif (name == "左耳"):
                #         current_tab = switch_L_current
                #         prev_properties_context = switch_L_current
                #         bpy.context.screen.areas[1].spaces.active.context = switch_L_current
                #         bpy.context.screen.areas[0].spaces.active.context = switch_L_current
                #         submit_process = processing_stage_dict[switch_L_current]
                #     if (submit_process == '打磨'):
                #         pass
                #     elif(submit_process == '局部加厚'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.obj.localthickeningsubmit('INVOKE_DEFAULT')
                #     elif (submit_process == '切割'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.finishcut('INVOKE_DEFAULT')
                #     elif (submit_process == '创建模具'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.handlesubmit('INVOKE_DEFAULT')
                #     elif (submit_process == '传声孔'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.finishsoundcanal('INVOKE_DEFAULT')
                #     elif (submit_process == '通气孔'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.finishventcanal('INVOKE_DEFAULT')
                #     elif (submit_process == '耳膜附件'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.handlesubmit('INVOKE_DEFAULT')
                #     elif (submit_process == '编号'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.labelsubmit('INVOKE_DEFAULT')
                #     elif (submit_process == '铸造法软耳模'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.castingsubmit('INVOKE_DEFAULT')
                #             # 为铸造法外壳添加透明材质
                #             name = bpy.context.scene.leftWindowObj
                #             casting_name = name + "CastingCompare"
                #             casting_compare_obj = bpy.data.objects.get(casting_name)
                #             if (casting_compare_obj != None):
                #                 mat.blend_method = 'BLEND'
                #                 mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                #                 bpy.context.scene.transparent3Enum = 'OP3'
                #     elif (submit_process == '支撑'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.supportsubmit('INVOKE_DEFAULT')
                #             # 为铸造法外壳添加透明材质
                #             name = bpy.context.scene.leftWindowObj
                #             casting_name = name + "CastingCompare"
                #             casting_compare_obj = bpy.data.objects.get(casting_name)
                #             if (casting_compare_obj != None):
                #                 mat.blend_method = 'BLEND'
                #                 mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                #                 bpy.context.scene.transparent3Enum = 'OP3'
                #     elif (submit_process == '排气孔'):
                #         override = getOverride()
                #         with bpy.context.temp_override(**override):
                #             bpy.ops.object.spruesubmit('INVOKE_DEFAULT')
                #             #为铸造法外壳添加透明材质
                #             mat.blend_method = 'BLEND'
                #             mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                #             bpy.context.scene.transparent3Enum = 'OP3'
                #     elif(submit_process == '后期打磨'):
                #         pass
                #     #打开文件导出窗口
                #     context.window.cursor_warp(context.window.width // 2, (context.window.height // 2) + 60)
                #     bpy.ops.screen.userpref_show(section='SYSTEM')

                # 点击导出的按钮，进行切割
                if (current_tab == 'DATA'):
                    pass



                # 点击排气孔的按钮,检测是否存在铸造法;经过铸造法之后才能够使用排气孔,否则回退到之前的模块
                if (current_tab == 'CONSTRAINT'):
                    name = bpy.context.scene.leftWindowObj
                    castingname = name + "CastingCompare"
                    casting_obj = bpy.data.objects.get(castingname)
                    # 经过铸造法模块后才能使用排气孔模块
                    if (casting_obj == None):
                        #弹出消息提示,需要先经过铸造法流程才能够添加排气孔
                        bpy.ops.object.sprue_dialog_operator('INVOKE_DEFAULT')
                        # 重置current_tab,prev_properties_context,让物体能够从导出按钮切换回之前的模块并且激活其modal
                        # 记录点击导出按钮前的上一个模块,将该模块重新激活
                        if (name == "右耳"):
                            is_fallback = True
                            current_tab = switch_R_current
                            prev_properties_context = switch_R_current
                            bpy.context.screen.areas[0].spaces.active.context = switch_R_current
                            bpy.context.screen.areas[0].spaces.active.context = switch_R_current
                        elif (name == "左耳"):
                            is_fallback = True
                            current_tab = switch_L_current
                            prev_properties_context = switch_L_current
                            bpy.context.screen.areas[0].spaces.active.context = switch_L_current
                            bpy.context.screen.areas[0].spaces.active.context = switch_L_current


                #切换到  左右耳切换  未经铸造法切换到排气孔   切换到后期打磨  等模块的时候
                #需要回退到当前模块并且激活model
                if(is_fallback):
                    is_fallback = False
                    submit_process = processing_stage_dict[current_tab]
                    if (submit_process == '打磨'):
                        change_mat_mould(1)
                        set_modal_start_false()
                    elif (submit_process == '局部加厚'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLocalThickening()
                            frontToLocalThickening()
                    elif (submit_process == '切割'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromQieGe()
                            frontToQieGe()
                    elif (submit_process == '创建模具'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCreateMould()
                            frontToCreateMould()
                    elif (submit_process == '传声孔'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSoundCanal()
                            frontToSoundCanal()
                    elif (submit_process == '通气孔'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromVentCanal()
                            frontToVentCanal()
                    elif (submit_process == '耳膜附件'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromHandle()
                            frontToHandle()
                    elif (submit_process == '编号'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLabel()
                            frontToLabel()
                    elif (submit_process == '铸造法软耳模'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCasting()
                            frontToCasting()
                    elif (submit_process == '支撑'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSupport()
                            frontToSupport()
                            # 为铸造法外壳添加透明材质
                            name = bpy.context.scene.leftWindowObj
                            casting_name = name + "CastingCompare"
                            casting_compare_obj = bpy.data.objects.get(casting_name)
                            if (casting_compare_obj != None):
                                mat.blend_method = 'BLEND'
                                mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                                bpy.context.scene.transparent3Enum = 'OP3'
                    elif (submit_process == '排气孔'):
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromSprue()
                            frontToSprue()
                            # 为铸造法外壳添加透明材质
                            mat.blend_method = 'BLEND'
                            mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
                            bpy.context.scene.transparent3Enum = 'OP3'

                    elif (submit_process == '后期打磨'):
                        last_set_modal_start_false()





                # 模块切换
                current_process = processing_stage_dict[current_tab]
                prev_process = processing_stage_dict[prev_properties_context]

                if (current_process == '打磨'):
                    if (prev_process == '局部加厚'):
                        print("LocalThickToDaMo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLocalThickening()
                            backToDamo()
                    elif (prev_process == '切割'):
                        print("QieGeToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromQieGe()
                            backToDamo()
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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToDamo()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            frontToDamo()


                elif (current_process == '局部加厚'):
                    if (prev_process == '打磨'):
                        print("DamoToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToLocalThickening()
                    elif (prev_process == '切割'):
                        print("qieGeToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromQieGe()
                            backToLocalThickening()
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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToLocalThick")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToLocalThickening()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToLocalThick")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('局部加厚')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToLocalThickening()  # 回退
                            if index_before < index_after:
                                frontToLocalThickening()  # 保留

                elif (current_process == '切割'):
                    if (prev_process == '局部加厚'):
                        print("LocalThickToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToQieGe()
                    elif (prev_process == '打磨'):
                        print("damoToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToQieGe()
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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToQieGe")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToQieGe()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToQieGe")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('切割')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToQieGe()  # 回退
                            if index_before < index_after:
                                frontToQieGe()  # 保留


                elif (current_process == '编号'):
                    if (prev_process == '局部加厚'):
                        print("LocalThickToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToLabel()
                    elif (prev_process == '打磨'):
                        print("DamoToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToLabel")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToLabel()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToLabel")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('编号')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToLabel()  # 回退
                            if index_before < index_after:
                                frontToLabel()  # 保留

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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToCreateMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToCreateMould()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToCreateMould")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('创建模具')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToCreateMould()  # 回退
                            if index_before < index_after:
                                frontToCreateMould()  # 保留


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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToHandle")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToHandle()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToHandle")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('耳膜附件')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToHandle()  # 回退
                            if index_before < index_after:
                                frontToHandle()  # 保留

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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToSupport")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToSupport()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToSupport")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('支撑')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToSupport()  # 回退
                            if index_before < index_after:
                                frontToSupport()  # 保留

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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToSoundCanal")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToSoundCanal()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToSoundCanal")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('传声孔')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToSoundCanal()  # 回退
                            if index_before < index_after:
                                frontToSoundCanal()  # 保留

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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToVentCanal")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToVentCanal()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToVentCanal")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('通气孔')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToVentCanal()  # 回退
                            if index_before < index_after:
                                frontToVentCanal()  # 保留


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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToCasting")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToCasting()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToCasting")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('铸造法软耳模')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToCasting()  # 回退
                            if index_before < index_after:
                                frontToCasting()  # 保留

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
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToSprue")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            backToSprue()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToSprue")
                        index_before = order_processing_list.index(before_cut_mould)
                        index_after = order_processing_list.index('切割')
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            if index_before >= index_after:
                                backToSprue()  # 回退
                            if index_before < index_after:
                                frontToSprue()  # 保留

                elif (current_process == '后期打磨'):
                    if (prev_process == '局部加厚'):
                        print("LocalThickToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToLastDamo()
                    elif (prev_process == '打磨'):
                        print("DamoToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToLastDamo()
                    elif (prev_process == '切割'):
                        print("QieGeToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToLastDamo()
                    elif (prev_process == '编号'):
                        print("LabelToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLabel()
                            frontToLastDamo()
                    elif (prev_process == '创建模具'):
                        print("CreateMouldToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCreateMould()
                            frontToLastDamo()
                    elif (prev_process == '耳膜附件'):
                        print("HandleToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromHandle()
                            frontToLastDamo()
                    elif (prev_process == '支撑'):
                        print("SupportToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSupport()
                            frontToLastDamo()
                    elif (prev_process == '传声孔'):
                        print("SoundCanalToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSoundCanal()
                            frontToLastDamo()
                    elif (prev_process == '通气孔'):
                        print("VentCanalToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromVentCanal()
                            frontToLastDamo()
                    elif (prev_process == '铸造法软耳模'):
                        print("CastingToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCasting()
                            frontToLastDamo()
                    elif (prev_process == '排气孔'):
                        print("SprueToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSprue()
                            frontToLastDamo()
                    elif (prev_process == '切割模具'):
                        print("CutMouldToLastDamo")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromCutMould()
                            frontToLastDamo()

                elif (current_process == '切割模具'):
                    before_cut_mould = prev_process
                    if (prev_process == '局部加厚'):
                        print("LocalThickToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLocalThickening()
                            frontToCutMould()
                    elif (prev_process == '打磨'):
                        print("DamoToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromDamo()
                            frontToCutMould(1)
                    elif (prev_process == '切割'):
                        print("QieGeToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromQieGe()
                            frontToCutMould()
                    elif (prev_process == '编号'):
                        print("LabelToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromLabel()
                            frontToCutMould()
                    elif (prev_process == '创建模具'):
                        print("CreateMouldToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCreateMould()
                            frontToCutMould()
                    elif (prev_process == '耳膜附件'):
                        print("HandleToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromHandle()
                            frontToCutMould()
                    elif (prev_process == '支撑'):
                        print("SupportToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSupport()
                            frontToCutMould()
                    elif (prev_process == '传声孔'):
                        print("SoundCanalToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSoundCanal()
                            frontToCutMould()
                    elif (prev_process == '通气孔'):
                        print("VentCanalToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromVentCanal()
                            frontToCutMould()
                    elif (prev_process == '铸造法软耳模'):
                        print("CastingToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromCasting()
                            frontToCutMould()
                    elif (prev_process == '排气孔'):
                        print("SprueToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            backFromSprue()
                            frontToCutMould()
                    elif (prev_process == '后期打磨'):
                        print("LastDamoToCutMould")
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            frontFromLastDamo()
                            frontToCutMould()


                print("-------------------")
                print("切换后场景中存在的文件:")
                print("~~~~~~~~~~~~~~~~~~~")
                selected_objs = bpy.data.objects
                for selected_obj in selected_objs:
                    print(selected_obj.name)
                print("~~~~~~~~~~~~~~~~~~~")


                #记录当前窗口的当前模块和上一个模块
                name = bpy.context.scene.leftWindowObj
                if (name == "右耳"):
                    switch_R_prev = prev_properties_context
                    switch_R_current = current_tab
                elif (name == "左耳"):
                    switch_L_prev = prev_properties_context
                    switch_L_current = current_tab
                prev_properties_context = current_tab

                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("切换当前模块:", switch_R_current)
                print("切换上一个模块:", switch_R_prev)
                print("切换当前模块:", switch_L_current)
                print("切换上一个模块:", switch_L_prev)
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("--------------------------------------------------------------------------------")
                prev_workspace = workspace
                # 切换结束
                flag = True


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
        bpy.ops.object.createmouldinit('INVOKE_DEFAULT')
        bpy.ops.object.createmouldcut('INVOKE_DEFAULT')
        bpy.ops.object.createmouldfill('INVOKE_DEFAULT')
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

class SprueDialogOperator(bpy.types.Operator):
    bl_idname = "object.sprue_dialog_operator"
    bl_label = "3D Model"

    my_string: bpy.props.StringProperty(name="", default="需先为物体加上铸造法外壳才能添加排气孔")

    def execute(self, context):
        pass
        return {'FINISHED'}

    def invoke(self, context, event):
        print("排气孔弹窗")
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
    BackUp,
    Forward,
    SwitchTest,
    MsgbusCallBack,
    MsgbusCallBack2,
    DialogOperator,
    SprueDialogOperator,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
