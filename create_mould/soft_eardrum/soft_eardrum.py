import bpy
import bmesh

from . import thickness_and_fill
from ..normal_projection import normal_projection_to_darw_bottom_ring
from ..normal_projection import normal_projection_to_darw_cut_plane,get_highest_vert
from ..bottom_ring import soft_eardrum_bottom_cut
from .thickness_and_fill import soft_eardrum
from .thickness_and_fill import reset_to_after_cut
from .thickness_and_fill import reset_and_refill,set_finish
from .thickness_and_fill import refill_submit
from ...utils.utils import *
from ..frame_style_eardrum.frame_style_eardrum import recover_and_remind_border
from ...tool import convert_to_mesh, set_vert_group, moveToRight
from pynput import mouse

is_timer_modifier_start = False  # 防止 定时器(完成重拓扑操作后为重拓扑后的物体添加修改器控制其平滑度)添加过多

prev_softear_thickness = 1.5  # 判断软耳膜厚度参数是否更新

thickness_update = False      #厚度参数更新并且鼠标左键松开,将该参数置为True,TimerSoftEarDrumThicknessUpdate操作符监听到之后会启动重拓扑并进行平滑初始化
mouse_listener = None         #

def on_click(x, y, button, pressed):
    # 鼠标点击事件处理函数
    if button == mouse.Button.left and not pressed:
        houDuUpdateCompleled = bpy.context.scene.zongHouDuUpdateCompleled
        thickness = bpy.context.scene.zongHouDu
        mould_type = bpy.context.scene.muJuTypeEnum
        global thickness_update
        global prev_softear_thickness
        global mouse_listener
        if (mould_type == "OP1"  and houDuUpdateCompleled and (thickness != prev_softear_thickness)):
            thickness_update = True
            prev_softear_thickness = thickness




class TimerSoftEarDrumThicknessUpdate(bpy.types.Operator):
    bl_idname = "object.timer_softeardrum_thickness_update"
    bl_label = "检测参数软耳膜厚度,根据参数更新厚度"

    __timer = None

    def execute(self, context):
        op_cls = TimerSoftEarDrumThicknessUpdate


        global mouse_listener
        if(mouse_listener == None):
            mouse_listener = mouse.Listener(
                on_click=on_click
            )
            # 启动监听器
            mouse_listener.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TimerSoftEarDrumThicknessUpdate
        mould_type = bpy.context.scene.muJuTypeEnum
        # thickness = bpy.context.scene.zongHouDu
        # global prev_softear_thickness
        global thickness_update
        global mouse_listener
        #处于创建磨具的软而莫从时,该modal才运行,否则退出
        if (mould_type == "OP1" and bpy.context.screen.areas[1].spaces.active.context == 'SCENE'):
            if (thickness_update == True):
                thickness_update = False
                try:
                    refill_submit()
                    soft_eardrum_smooth_initial()
                except:
                    print("软耳膜厚度参数初始化失败")
                    bpy.ops.object.mode_set(mode='OBJECT')
                    reset_to_after_cut()
                    utils_re_color("右耳", (1, 1, 0))
                    utils_re_color("右耳huanqiecompare", (1, 1, 0))
                return {'PASS_THROUGH'}
            return {'PASS_THROUGH'}
        else:
            if (mouse_listener != None):
                mouse_listener.stop()
                mouse_listener = None
            return {'FINISHED'}
        return {'PASS_THROUGH'}


class TimerSoftEarDrumAddModifierAfterQmesh(bpy.types.Operator):
    bl_idname = "object.timer_softeardrum_add_modifier_after_qmesh"
    bl_label = "在重拓扑完成后为重拓扑后的物体添加平滑修改器"

    __timer = None

    def execute(self, context):
        op_cls = TimerSoftEarDrumAddModifierAfterQmesh
        op_cls.__timer = context.window_manager.event_timer_add(
            0.1, window=context.window)

        for obj in bpy.data.objects:
            obj.select_set(False)

        cur_obj_name = "Retopo_右耳"
        compare_obj_name = "右耳"
        cur_obj = bpy.data.objects.get(cur_obj_name)
        compare_obj = bpy.data.objects.get(compare_obj_name)
        compare_obj.select_set(True)
        bpy.context.view_layer.objects.active = compare_obj

        # 将当前激活的物体重拓扑
        bpy.context.scene.qremesher.autodetect_hard_edges = False
        bpy.context.scene.qremesher.use_normals = False
        bpy.context.scene.qremesher.use_materials = False
        bpy.context.scene.qremesher.use_vertex_color = False
        bpy.context.scene.qremesher.adapt_quad_count = False
        bpy.context.scene.qremesher.adaptive_size = 100
        bpy.context.scene.qremesher.target_count = 3000
        bpy.ops.qremesher.remesh()
        bpy.context.scene.zongHouDuUpdateCompleled = False

        global is_timer_modifier_start  # 防止添加多余的定时器
        is_timer_modifier_start = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TimerSoftEarDrumAddModifierAfterQmesh
        global is_timer_modifier_start
        mould_type = bpy.context.scene.muJuTypeEnum
        cur_obj = bpy.data.objects["右耳"]
        cur_obj_name = cur_obj.name
        if context.area:
            context.area.tag_redraw()
        if (mould_type == "OP1"):  # 判断创建模具模块中选项是否为软耳膜
            if event.type == 'TIMER':
                obj = bpy.data.objects.get("Retopo_" + cur_obj.name)
                if (bpy.data.objects.get("Retopo_" + cur_obj.name) != None):  # 判断重拓扑是否完成
                    bpy.context.scene.zongHouDuUpdateCompleled = True
                    cur_obj_name = "Retopo_右耳"
                    compare_obj_name = "右耳"
                    cur_obj = bpy.data.objects.get(cur_obj_name)
                    compare_obj = bpy.data.objects.get(compare_obj_name)
                    compare_obj.select_set(True)
                    compare_obj.hide_set(False)
                    bpy.context.view_layer.objects.active = compare_obj

                    if (cur_obj != None and compare_obj != None):
                        compare_obj.name = "右耳Previous"  # 重拓扑前的右耳
                        cur_obj.name = "右耳"  # 重拓扑后的右耳

                        moveToRight(cur_obj)

                        prev_bottom_inner_vertex_index = []  # 存储重拓扑前的底部内圈顶点的索引
                        prev_bottom_outer_vertex_index = []  # 存储重拓扑前的底部外圈顶点的索引
                        select_vertex_index = []  # 存储重拓扑后的选择锐边后选中的顶点

                        # 将当前激活物体设置为重拓扑前的物体
                        cur_obj.select_set(False)
                        compare_obj.select_set(True)
                        bpy.context.view_layer.objects.active = compare_obj
                        soft_eardrum_bottom_inner_vertex = compare_obj.vertex_groups.get("BottomInnerBorderVertex")
                        soft_eardrum_bottom_outer_vertex = compare_obj.vertex_groups.get("BottomOuterBorderVertex")
                        if (soft_eardrum_bottom_outer_vertex != None and soft_eardrum_bottom_inner_vertex != None):
                            # 将内圈顶点索引存储到数组中
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                            bpy.ops.object.vertex_group_select()
                            bpy.ops.object.mode_set(mode='OBJECT')
                            if compare_obj.type == 'MESH':
                                compare_me = compare_obj.data
                                compare_bm = bmesh.new()
                                compare_bm.from_mesh(compare_me)
                                compare_bm.verts.ensure_lookup_table()
                                for vert in compare_bm.verts:
                                    if (vert.select == True):
                                        prev_bottom_inner_vertex_index.append(vert.index)
                                compare_bm.free()
                            # 将外圈顶点索引存储到数组中
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                            bpy.ops.object.vertex_group_select()
                            bpy.ops.object.mode_set(mode='OBJECT')
                            if compare_obj.type == 'MESH':
                                compare_me = compare_obj.data
                                compare_bm = bmesh.new()
                                compare_bm.from_mesh(compare_me)
                                compare_bm.verts.ensure_lookup_table()
                                for vert in compare_bm.verts:
                                    if (vert.select == True):
                                        prev_bottom_outer_vertex_index.append(vert.index)
                                compare_bm.free()

                        # 将当前激活物体设置为重拓扑后的物体
                        compare_obj.select_set(False)
                        cur_obj.select_set(True)
                        bpy.context.view_layer.objects.active = cur_obj
                        # 选择锐边
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.mesh.edges_select_sharp()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # 将重拓扑后选中的锐边后的顶点索引存储到数组中
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert in bm.verts:
                                if (vert.select == True):
                                    select_vertex_index.append(vert.index)
                            bm.free()

                        # # 对于选中的锐边,只将内圈顶点保持选中
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.select_all(action='DESELECT')
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        # if cur_obj.type == 'MESH' and compare_obj.type == 'MESH':
                        #     me = cur_obj.data
                        #     bm = bmesh.new()
                        #     bm.from_mesh(me)
                        #     bm.verts.ensure_lookup_table()
                        #     compare_me = compare_obj.data
                        #     compare_bm = bmesh.new()
                        #     compare_bm.from_mesh(compare_me)
                        #     compare_bm.verts.ensure_lookup_table()
                        #     for vert_index in select_vertex_index:
                        #         vert = bm.verts[vert_index]
                        #         min_distance = math.inf
                        #         for compare_vert_index in prev_bottom_inner_vertex_index:
                        #             vert_compare = compare_bm.verts[compare_vert_index]
                        #             distance = math.sqrt(
                        #                 (vert.co[0] - vert_compare.co[0]) ** 2 + (
                        #                             vert.co[1] - vert_compare.co[1]) ** 2 + (
                        #                         vert.co[2] - vert_compare.co[2]) ** 2)
                        #             if (distance < min_distance):
                        #                 min_distance = distance
                        #         if (min_distance < 0.5):
                        #             vert.select_set(True)
                        #     bm.to_mesh(me)
                        #     bm.free()
                        #     compare_bm.free()
                        # # 对于重拓扑后的物体,创建顶点组并指定底部内边顶点
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        # soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumBottomInnerVertex")
                        # if (soft_eardrum_bottom_inner_vertex == None):
                        #     soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.new(
                        #         name="SoftEarDrumBottomInnerVertex")
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.select_more()
                        # bpy.ops.mesh.select_more()
                        # bpy.ops.mesh.select_more()
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomInnerVertex')
                        # bpy.ops.object.vertex_group_assign()
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        #
                        # # 对于选中的锐边,只将外圈顶点保持选中
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.select_all(action='DESELECT')
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        # if cur_obj.type == 'MESH' and compare_obj.type == 'MESH':
                        #     me = cur_obj.data
                        #     bm = bmesh.new()
                        #     bm.from_mesh(me)
                        #     bm.verts.ensure_lookup_table()
                        #     compare_me = compare_obj.data
                        #     compare_bm = bmesh.new()
                        #     compare_bm.from_mesh(compare_me)
                        #     compare_bm.verts.ensure_lookup_table()
                        #     for vert_index in select_vertex_index:
                        #         vert = bm.verts[vert_index]
                        #         min_distance = math.inf
                        #         for compare_vert_index in prev_bottom_outer_vertex_index:
                        #             vert_compare = compare_bm.verts[compare_vert_index]
                        #             distance = math.sqrt(
                        #                 (vert.co[0] - vert_compare.co[0]) ** 2 + (
                        #                             vert.co[1] - vert_compare.co[1]) ** 2 + (
                        #                         vert.co[2] - vert_compare.co[2]) ** 2)
                        #             if (distance < min_distance):
                        #                 min_distance = distance
                        #         if (min_distance < 0.5):
                        #             vert.select_set(True)
                        #     bm.to_mesh(me)
                        #     bm.free()
                        #     compare_bm.free()
                        # # 对于重拓扑后的物体,创建顶点组并指定底部外边顶点
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        # soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumBottomOuterVertex")
                        # if (soft_eardrum_bottom_outer_vertex == None):
                        #     soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.new(
                        #         name="SoftEarDrumBottomOuterVertex")
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.select_more()
                        # bpy.ops.mesh.select_more()
                        # bpy.ops.mesh.select_more()
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomOuterVertex')
                        # bpy.ops.object.vertex_group_assign()
                        # bpy.ops.object.mode_set(mode='OBJECT')

                        # 对于选中的锐边,只将内圈顶点保持选中
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        if cur_obj.type == 'MESH' and compare_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            compare_me = compare_obj.data
                            compare_bm = bmesh.new()
                            compare_bm.from_mesh(compare_me)
                            compare_bm.verts.ensure_lookup_table()
                            for vert_index in select_vertex_index:
                                vert = bm.verts[vert_index]
                                min_distance = math.inf
                                for compare_vert_index in prev_bottom_inner_vertex_index:
                                    vert_compare = compare_bm.verts[compare_vert_index]
                                    distance = math.sqrt(
                                        (vert.co[0] - vert_compare.co[0]) ** 2 + (
                                                vert.co[1] - vert_compare.co[1]) ** 2 + (
                                                vert.co[2] - vert_compare.co[2]) ** 2)
                                    if (distance < min_distance):
                                        min_distance = distance
                                if (min_distance < 0.3):
                                    vert.select_set(True)
                            bm.to_mesh(me)
                            bm.free()
                            compare_bm.free()
                        # 对于重拓扑后的物体,创建顶点组并指定底部内边顶点
                        bpy.ops.object.mode_set(mode='OBJECT')
                        soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumBottomInnerVertex")
                        if (soft_eardrum_bottom_inner_vertex == None):
                            soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.new(
                                name="SoftEarDrumBottomInnerVertex")
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomInnerVertex')
                        bpy.ops.object.vertex_group_assign()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # 根据选中的底部内边顶点,选中内侧区域
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        # soft_eardrum_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerVertex")
                        # if (soft_eardrum_inner_vertex == None):
                        #     soft_eardrum_inner_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumInnerVertex")
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.loop_to_region()
                        # bpy.ops.mesh.select_all(action='INVERT')
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
                        # bpy.ops.object.vertex_group_assign()
                        # bpy.ops.object.mode_set(mode='OBJECT')

                        # 对于选中的锐边,只将外圈顶点保持选中
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        if cur_obj.type == 'MESH' and compare_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            compare_me = compare_obj.data
                            compare_bm = bmesh.new()
                            compare_bm.from_mesh(compare_me)
                            compare_bm.verts.ensure_lookup_table()
                            for vert_index in select_vertex_index:
                                vert = bm.verts[vert_index]
                                min_distance = math.inf
                                for compare_vert_index in prev_bottom_outer_vertex_index:
                                    vert_compare = compare_bm.verts[compare_vert_index]
                                    distance = math.sqrt(
                                        (vert.co[0] - vert_compare.co[0]) ** 2 + (
                                                vert.co[1] - vert_compare.co[1]) ** 2 + (
                                                vert.co[2] - vert_compare.co[2]) ** 2)
                                    if (distance < min_distance):
                                        min_distance = distance
                                if (min_distance < 0.5):
                                    vert.select_set(True)
                            bm.to_mesh(me)
                            bm.free()
                            compare_bm.free()
                        # 对于重拓扑后的物体,创建顶点组并指定底部外边顶点
                        bpy.ops.object.mode_set(mode='OBJECT')
                        soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumBottomOuterVertex")
                        if (soft_eardrum_bottom_outer_vertex == None):
                            soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.new(
                                name="SoftEarDrumBottomOuterVertex")
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomOuterVertex')
                        bpy.ops.object.vertex_group_assign()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # # 根据选中的底部外边顶点,选中外侧区域
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        # soft_eardrum_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterVertex")
                        # if (soft_eardrum_outer_vertex == None):
                        #     soft_eardrum_outer_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumOuterVertex")
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.loop_to_region()
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
                        # bpy.ops.object.vertex_group_assign()
                        # bpy.ops.object.mode_set(mode='OBJECT')

                        softear_inner_vertex_index = []  # 存储重拓扑之后需要平滑的内部顶点
                        softear_inner_bottom_vertex_index = []  # 存储重拓扑后的底部内顶点

                        # 根据底部内圈顶点,扩大选中区域
                        bpy.ops.object.mode_set(mode='OBJECT')
                        soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerSmoothVertex")
                        if (soft_eardrum_bottom_inner_vertex == None):
                            soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.new(
                                name="SoftEarDrumInnerSmoothVertex")
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomInnerVertex')
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # 顶点扩散后只选择里底部内边顶点距离小于1.5的顶点,防止内部顶点选择的范围过大
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert in bm.verts:
                                if (vert.select == True):
                                    softear_inner_bottom_vertex_index.append(vert.index)
                            bm.free()
                        bpy.ops.object.mode_set(mode='EDIT')
                        for i in range(20):
                            bpy.ops.mesh.select_more()
                            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomOuterVertex')
                            bpy.ops.object.vertex_group_deselect()
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomOuterVertex')
                        # bpy.ops.object.vertex_group_select()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert in bm.verts:
                                if (vert.select == True):
                                    softear_inner_vertex_index.append(vert.index)
                            bm.free()
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert_index in softear_inner_vertex_index:
                                vert = bm.verts[vert_index]
                                min_distance = math.inf
                                for compare_vert_index in softear_inner_bottom_vertex_index:
                                    vert_compare = bm.verts[compare_vert_index]
                                    distance = math.sqrt(
                                        (vert.co[0] - vert_compare.co[0]) ** 2 + (
                                                vert.co[1] - vert_compare.co[1]) ** 2 + (
                                                vert.co[2] - vert_compare.co[2]) ** 2)
                                    if (distance < min_distance):
                                        min_distance = distance
                                if (min_distance < 3):
                                    vert.select_set(True)
                            bm.to_mesh(me)
                            bm.free()
                            compare_bm.free()
                        bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
                        # bpy.ops.object.vertex_group_deselect()
                        bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerSmoothVertex')
                        bpy.ops.object.vertex_group_assign()
                        bpy.ops.object.mode_set(mode='OBJECT')



                        softear_outer_vertex_index = []  # 存储重拓扑之后需要平滑的外部顶点
                        softear_outer_bottom_vertex_index = []  # 存储重拓扑后的底部外顶点


                        # 根据底部外圈顶点,扩大选中区域
                        bpy.ops.object.mode_set(mode='OBJECT')
                        soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterSmoothVertex")
                        if (soft_eardrum_bottom_outer_vertex == None):
                            soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.new(
                                name="SoftEarDrumOuterSmoothVertex")
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomOuterVertex')
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        #顶点扩散后只选择里底部外边顶点距离小于1.5的顶点,防止外部顶点选择的范围过大
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert in bm.verts:
                                if (vert.select == True):
                                    softear_outer_bottom_vertex_index.append(vert.index)
                            bm.free()
                        bpy.ops.object.mode_set(mode='EDIT')
                        for i in range(20):
                            bpy.ops.mesh.select_more()
                            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomInnerVertex')
                            bpy.ops.object.vertex_group_deselect()
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomInnerVertex')
                        # bpy.ops.object.vertex_group_select()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert in bm.verts:
                                if (vert.select == True):
                                    softear_outer_vertex_index.append(vert.index)
                            bm.free()
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        if cur_obj.type == 'MESH':
                            me = cur_obj.data
                            bm = bmesh.new()
                            bm.from_mesh(me)
                            bm.verts.ensure_lookup_table()
                            for vert_index in softear_outer_vertex_index:
                                vert = bm.verts[vert_index]
                                min_distance = math.inf
                                for compare_vert_index in softear_outer_bottom_vertex_index:
                                    vert_compare = bm.verts[compare_vert_index]
                                    distance = math.sqrt(
                                        (vert.co[0] - vert_compare.co[0]) ** 2 + (
                                                    vert.co[1] - vert_compare.co[1]) ** 2 + (
                                                vert.co[2] - vert_compare.co[2]) ** 2)
                                    if (distance < min_distance):
                                        min_distance = distance
                                if (min_distance < 3):
                                    vert.select_set(True)
                            bm.to_mesh(me)
                            bm.free()
                            compare_bm.free()
                        bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
                        # bpy.ops.object.vertex_group_deselect()
                        bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterSmoothVertex')
                        bpy.ops.object.vertex_group_assign()
                        bpy.ops.object.mode_set(mode='OBJECT')


                        # 添加平滑修改器
                        outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYi, 1)
                        modifier_name = "SoftEarDrumOuterSmoothModifier"
                        target_modifier = None
                        for modifier in cur_obj.modifiers:
                            if modifier.name == modifier_name:
                                target_modifier = modifier
                        if (target_modifier == None):
                            bpy.ops.object.modifier_add(type='SMOOTH')
                            # bpy.ops.object.modifier_add(type='LAPLACIANSMOOTH')
                            # bpy.context.object.modifiers["LaplacianSmooth"].lambda_factor = 1.61
                            bpy.context.object.modifiers["Smooth"].vertex_group = "SoftEarDrumOuterSmoothVertex"
                            hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                            hard_eardrum_modifier.name = "SoftEarDrumOuterSmoothModifier"
                            # hard_eardrum_modifier = bpy.context.object.modifiers["LaplacianSmooth"]
                            # hard_eardrum_modifier.name = "SoftEarDrumOuterSmoothModifier"
                        bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].factor = 0.6
                        bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].iterations = int(
                            outer_smooth * 10)
                        # bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].lambda_factor = 0.6
                        # bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].iterations = int(
                        #     outer_smooth * 30)

                        inner_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYi, 1)
                        modifier_name = "SoftEarDrumInnerSmoothModifier"
                        target_modifier = None
                        for modifier in cur_obj.modifiers:
                            if modifier.name == modifier_name:
                                target_modifier = modifier
                        if (target_modifier == None):
                            bpy.ops.object.modifier_add(type='SMOOTH')
                            bpy.context.object.modifiers["Smooth"].vertex_group = "SoftEarDrumInnerSmoothVertex"
                            hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                            hard_eardrum_modifier.name = "SoftEarDrumInnerSmoothModifier"
                        bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].factor = 1.8
                        bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].iterations = int(
                            inner_smooth * 10)

                        # 删除重拓扑之前的右耳
                        bpy.data.objects.remove(compare_obj, do_unlink=True)
                    bpy.ops.geometry.color_attribute_add(name="Color", color=(1, 0.319, 0.133, 1))
                    bpy.data.objects['右耳'].data.materials.clear()
                    bpy.data.objects['右耳'].data.materials.append(bpy.data.materials['Yellow'])
                    is_timer_modifier_start = False  # 重拓扑完成且添加修改器后,退出该定时器
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                    return {'FINISHED'}
            return {'PASS_THROUGH'}
        else:
            is_timer_modifier_start = False
            return {'FINISHED'}
        return {'PASS_THROUGH'}


border_vert_co_and_normal = [((-4.802972793579102, 1.2865580320358276, 1.4337680339813232), (0.7056613564491272, 0.35171788930892944, 0.6150906682014465)), ((-4.850949287414551, 1.6650691032409668, 1.1557999849319458), (0.5864775776863098, 0.5615808367729187, 0.5836703181266785)), ((-4.89892578125, 2.0435800552368164, 0.8778319954872131), (0.6284376978874207, 0.6016121506690979, 0.4930809438228607)), ((-5.001494407653809, 2.2676501274108887, 0.631729006767273), (0.612186074256897, 0.6983122825622559, 0.37092873454093933)), ((-5.104063034057617, 2.491719961166382, 0.3856259882450104), (0.45674723386764526, 0.8463339805603027, 0.2740449607372284)), ((-5.224207878112793, 2.620975971221924, 0.17150849103927612), (0.44924405217170715, 0.8715528845787048, 0.19640611112117767)), ((-5.344353199005127, 2.750231981277466, -0.04260899871587753), (0.4434084892272949, 0.8685756921768188, 0.22128106653690338)), ((-5.484708786010742, 2.8513293266296387, -0.2834309935569763), (0.37104126811027527, 0.9196418523788452, 0.1287914514541626)), ((-5.625064849853516, 2.9524269104003906, -0.5242530107498169), (0.44167566299438477, 0.8908599615097046, 0.10626000910997391)), ((-5.886534690856934, 3.060694456100464, -0.7247725129127502), (0.2857891023159027, 0.9582637548446655, -0.007437936495989561)), ((-6.148004055023193, 3.168962001800537, -0.9252920150756836), (0.37720444798469543, 0.926067590713501, -0.010750268585979939)), ((-6.410432815551758, 3.2108700275421143, -1.3029694557189941), (0.32283255457878113, 0.9410142302513123, -0.10134756565093994)), ((-6.672861099243164, 3.2527780532836914, -1.6806470155715942), (0.28901857137680054, 0.9451103806495667, -0.15242937207221985)), ((-6.972126483917236, 3.1902451515197754, -2.134895086288452), (0.20349115133285522, 0.9506797194480896, -0.23409268260002136)), ((-7.271391868591309, 3.1277120113372803, -2.5891430377960205), (0.07040536403656006, 0.9273724555969238, -0.3674553334712982)), ((-7.513186454772949, 2.9922585487365723, -2.861318588256836), (0.025254525244235992, 0.907964289188385, -0.41828587651252747)), ((-7.75498104095459, 2.8568050861358643, -3.1334939002990723), (-0.050494663417339325, 0.8752436637878418, -0.4810393452644348)), ((-8.04397964477539, 2.6642074584960938, -3.327111005783081), (-0.14545808732509613, 0.8088243007659912, -0.5697764158248901)), ((-8.332977294921875, 2.4716100692749023, -3.52072811126709), (-0.2165660262107849, 0.7185913324356079, -0.6608522534370422)), ((-8.345941543579102, 2.170583486557007, -3.8161351680755615), (-0.26609259843826294, 0.686501681804657, -0.6766905784606934)), ((-8.358905792236328, 1.8695570230484009, -4.111542224884033), (-0.3505690395832062, 0.5687888264656067, -0.7440299987792969)), ((-8.513494491577148, 1.484413504600525, -4.265854835510254), (-0.4209718406200409, 0.4579717218875885, -0.7829716801643372)), ((-8.668083190917969, 1.099269986152649, -4.420167922973633), (-0.4372994303703308, 0.3967200219631195, -0.8070826530456543)), ((-8.640608787536621, 0.6668524742126465, -4.618765830993652), (-0.461576908826828, 0.32328280806541443, -0.8260961771011353)), ((-8.613134384155273, 0.23443500697612762, -4.81736421585083), (-0.4820954501628876, 0.3326626121997833, -0.8105058073997498)), ((-8.652962684631348, -0.2676050364971161, -4.942889213562012), (-0.49436071515083313, 0.2245737463235855, -0.8397465348243713)), ((-8.692790985107422, -0.769645094871521, -5.068414688110352), (-0.5243605375289917, 0.1685664802789688, -0.8346444368362427)), ((-8.702037811279297, -1.2812399864196777, -5.1356658935546875), (-0.5384766459465027, 0.10586203634738922, -0.8359642028808594)), ((-8.711284637451172, -1.792834997177124, -5.202917098999023), (-0.5312774777412415, 0.06489511579275131, -0.8447088003158569)), ((-8.696965217590332, -2.299046039581299, -5.213533878326416), (-0.5383806824684143, 0.015626894310116768, -0.842556893825531)), ((-8.682645797729492, -2.8052570819854736, -5.224150657653809), (-0.5352063775062561, -0.04008246213197708, -0.8437698483467102)), ((-8.651420593261719, -3.295145034790039, -5.180590629577637), (-0.5379471182823181, -0.09892958402633667, -0.837153434753418)), ((-8.620196342468262, -3.7850329875946045, -5.137031078338623), (-0.5299504995346069, -0.14370262622833252, -0.835764467716217)), ((-8.58063793182373, -4.249050140380859, -5.043765068054199), (-0.527368426322937, -0.20061218738555908, -0.8256133198738098)), ((-8.5410795211792, -4.713067531585693, -4.950498580932617), (-0.5333150029182434, -0.23933249711990356, -0.8113539218902588)), ((-8.509292602539062, -5.148116111755371, -4.828071594238281), (-0.5160081386566162, -0.2810913026332855, -0.8091496825218201)), ((-8.477506637573242, -5.583164215087891, -4.705644607543945), (-0.5160081386566162, -0.2810913026332855, -0.8091496825218201)), ((-8.463420867919922, -5.9895477294921875, -4.561941146850586), (-0.5040926933288574, -0.3078767955303192, -0.8069091439247131)), ((-8.449336051940918, -6.395931243896484, -4.418238162994385), (-0.5189944505691528, -0.30293208360671997, -0.7992976903915405)), ((-8.464125633239746, -6.776724338531494, -4.26744270324707), (-0.5189944505691528, -0.30293208360671997, -0.7992976903915405)), ((-8.478915214538574, -7.157517433166504, -4.116646766662598), (-0.5227915644645691, -0.29016992449760437, -0.8015549182891846)), ((-8.527915000915527, -7.513703346252441, -3.9650144577026367), (-0.5485059022903442, -0.25594890117645264, -0.7960097789764404)), ((-8.57691478729248, -7.869889736175537, -3.8133819103240967), (-0.5485059022903442, -0.25594890117645264, -0.7960097789764404)), ((-8.658731460571289, -8.199283599853516, -3.658155918121338), (-0.5386260747909546, -0.24208682775497437, -0.8070167303085327)), ((-8.740548133850098, -8.528676986694336, -3.5029296875), (-0.5599127411842346, -0.21939460933208466, -0.7989766597747803)), ((-8.849875450134277, -8.829421997070312, -3.338350296020508), (-0.5673314332962036, -0.23411789536476135, -0.789508581161499)), ((-8.959202766418457, -9.130166053771973, -3.1737711429595947), (-0.5764210224151611, -0.2210836410522461, -0.7866770625114441)), ((-9.091482162475586, -9.402400970458984, -2.9963881969451904), (-0.5873741507530212, -0.21224182844161987, -0.7809897661209106)), ((-9.223760604858398, -9.674635887145996, -2.819005250930786), (-0.6031798124313354, -0.241075336933136, -0.7603004574775696)), ((-9.365373611450195, -9.916717529296875, -2.6092424392700195), (-0.643012523651123, -0.2735303044319153, -0.7153432965278625)), ((-9.506987571716309, -10.15880012512207, -2.399479627609253), (-0.6884558200836182, -0.32096123695373535, -0.6503940224647522)), ((-9.628091812133789, -10.362039566040039, -2.1443874835968018), (-0.6670001745223999, -0.3398086726665497, -0.6630540490150452)), ((-9.749197006225586, -10.565279006958008, -1.889295220375061), (-0.7149556279182434, -0.40484094619750977, -0.5700371265411377)), ((-9.816837310791016, -10.708763122558594, -1.531976342201233), (-0.8145397305488586, -0.46979841589927673, -0.3403150737285614)), ((-9.884476661682129, -10.85224723815918, -1.1746574640274048), (-0.852986216545105, -0.5119249224662781, -0.10172201693058014)), ((-9.81039047241211, -10.886908531188965, -0.7993086576461792), (-0.8440667986869812, -0.5278517007827759, 0.09446579217910767)), ((-9.73630428314209, -10.92156982421875, -0.4239598214626312), (-0.8123735785484314, -0.5132998824119568, 0.27671724557876587)), ((-9.561388969421387, -10.874468803405762, -0.09027417004108429), (-0.7708175182342529, -0.4907895028591156, 0.4061600863933563)), ((-9.386473655700684, -10.827367782592773, 0.24341148138046265), (-0.6435025930404663, -0.4569549262523651, 0.614081859588623)), ((-9.160194396972656, -10.72799301147461, 0.5025469064712524), (-0.5835634469985962, -0.41756126284599304, 0.6964884996414185)), ((-8.933914184570312, -10.628618240356445, 0.7616823315620422), (-0.5271477103233337, -0.41555872559547424, 0.7412329316139221)), ((-8.685538291931152, -10.503093719482422, 0.9769312143325806), (-0.43704620003700256, -0.4085356891155243, 0.8013047575950623)), ((-8.437162399291992, -10.377568244934082, 1.1921800374984741), (-0.39628782868385315, -0.39002227783203125, 0.8311669826507568)), ((-8.198686599731445, -10.130550384521484, 1.3744029998779297), (-0.3292449414730072, -0.3872893452644348, 0.8611648678779602)), ((-7.960209846496582, -9.883532524108887, 1.5566259622573853), (-0.20565053820610046, -0.3594288229942322, 0.9102300405502319)), ((-7.763178825378418, -9.55428695678711, 1.6999495029449463), (-0.09203721582889557, -0.3255007565021515, 0.9410517811775208)), ((-7.566147804260254, -9.225042343139648, 1.8432730436325073), (-0.09184397757053375, -0.32379934191703796, 0.9416574239730835)), ((-7.275588512420654, -8.732134819030762, 2.0116240978240967), (-0.024923626333475113, -0.34840360283851624, 0.9370131492614746)), ((-6.985029220581055, -8.239227294921875, 2.1799750328063965), (0.177141010761261, -0.3686177730560303, 0.9125470519065857)), ((-6.840060710906982, -7.827841758728027, 2.309640407562256), (0.17568717896938324, -0.39340582489967346, 0.9024222493171692)), ((-6.69509220123291, -7.41645622253418, 2.4393060207366943), (0.2941754162311554, -0.3351239264011383, 0.8950714468955994)), ((-6.380501747131348, -6.961999893188477, 2.4755663871765137), (0.3331519067287445, -0.2914734184741974, 0.8966901302337646)), ((-6.065911769866943, -6.507544040679932, 2.511826992034912), (0.43619757890701294, -0.2677990794181824, 0.8590781688690186)), ((-6.033568382263184, -6.150696754455566, 2.6042964458465576), (0.43668580055236816, -0.257413387298584, 0.8619998693466187)), ((-6.001224994659424, -5.793849945068359, 2.696765899658203), (0.49267104268074036, -0.31287434697151184, 0.8120251297950745)), ((-5.830744743347168, -5.237461090087891, 2.7593183517456055), (0.5299533009529114, -0.2660769522190094, 0.805203378200531)), ((-5.660264015197754, -4.681072235107422, 2.821871042251587), (0.5571715235710144, -0.22435612976551056, 0.7995150089263916)), ((-5.598381996154785, -4.357274532318115, 2.832304000854492), (0.6085063815116882, -0.11959598958492279, 0.7844851016998291)), ((-5.536499977111816, -4.033476829528809, 2.8427369594573975), (0.6751633882522583, -0.15206144750118256, 0.7218252420425415)), ((-5.424007415771484, -3.6065359115600586, 2.8096234798431396), (0.682133674621582, -0.13362984359264374, 0.7189135551452637)), ((-5.311514854431152, -3.1795949935913086, 2.776510000228882), (0.7036362886428833, -0.1270987093448639, 0.6991008520126343)), ((-5.203734397888184, -2.6449875831604004, 2.7138404846191406), (0.6828091144561768, -0.05143789201974869, 0.7287837862968445)), ((-5.095953941345215, -2.110379934310913, 2.6511709690093994), (0.6858744025230408, -0.02046900801360607, 0.7274320721626282)), ((-5.042038440704346, -1.7422568798065186, 2.5800564289093018), (0.75200355052948, 0.020847942680120468, 0.6588292717933655)), ((-4.988122940063477, -1.3741339445114136, 2.508941888809204), (0.7565066814422607, 0.07121051847934723, 0.6500974297523499)), ((-4.875306129455566, -1.1043944358825684, 2.354776382446289), (0.6828516125679016, 0.09428378194570541, 0.7244475483894348)), ((-4.762488842010498, -0.8346549868583679, 2.200611114501953), (0.7053607702255249, 0.12876784801483154, 0.697054386138916)), ((-4.817227363586426, -0.4567815065383911, 2.140001058578491), (0.7392163276672363, 0.15584875643253326, 0.6551872491836548)), ((-4.8719658851623535, -0.07890799641609192, 2.0793910026550293), (0.6600677967071533, 0.3113294243812561, 0.683655321598053)), ((-4.804237365722656, 0.17898300290107727, 1.9095665216445923), (0.7156108021736145, 0.23674148321151733, 0.6571563482284546)), ((-4.736508846282959, 0.43687400221824646, 1.7397420406341553), (0.6467862725257874, 0.27638718485832214, 0.7108289003372192)), ((-4.769741058349609, 0.8617160320281982, 1.5867550373077393), (0.7124989628791809, 0.22760158777236938, 0.6637338995933533))]


origin_highest_vert = (-10.5040, 2.6564, 11.9506)

def soft_cut():
    global border_vert_co_and_normal, origin_highest_vert
    normal_projection_to_darw_cut_plane(origin_highest_vert, border_vert_co_and_normal)
    soft_eardrum()
    convert_to_mesh('BottomRingBorderR', 'meshBottomRingBorderR', 0.18)

def soft_fill():
    thickness_and_fill.soft_eardrum()
    utils_re_color("右耳", (1, 0.319, 0.133))
    set_finish(False)

def apply_soft_eardrum_template():
    cut_success = True
    fill_success = True

    global border_vert_co_and_normal,origin_highest_vert

    try:
        normal_projection_to_darw_cut_plane(origin_highest_vert, border_vert_co_and_normal)
        soft_eardrum()
        convert_to_mesh('BottomRingBorderR', 'meshBottomRingBorderR', 0.18)
    except:
        cut_success = False

    if not cut_success:
        print("切割出错")
        recover_and_remind_border()
        utils_re_color("右耳", (1, 1, 0))
        utils_re_color("右耳huanqiecompare", (1, 1, 0))
    else:
        try:
            thickness_and_fill.soft_eardrum()
            # soft_eardrum_smooth_initial()
            # bpy.ops.object.timer_softeardrum_thickness_update()
            utils_re_color("右耳", (1, 0.319, 0.133))
        except:
            fill_success = False

        if not fill_success:
            bpy.ops.object.mode_set(mode='OBJECT')
            reset_to_after_cut()
            utils_re_color("右耳", (1, 1, 0))
            utils_re_color("右耳huanqiecompare", (1, 1, 0))

    return cut_success and fill_success
    # return True


# init_thickness()

def judge_normals():
    cut_plane = bpy.data.objects["CutPlane"]
    cut_plane_mesh = bmesh.from_edit_mesh(cut_plane.data)
    sum = 0
    for v in cut_plane_mesh.verts:
        sum += v.normal[2]
    return sum < 0


def get_cut_plane():
    # 外边界顶点组
    bpy.data.objects["右耳"].select_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    cut_plane_outer = bpy.data.objects["CutPlane"]
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_outer.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Outer", vert_index)

    # 中间边界顶点组
    bpy.data.objects["CutPlane"].select_set(False)
    cut_plane_center = bpy.data.objects["Center"]
    bpy.context.view_layer.objects.active = cut_plane_center
    cut_plane_center.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_center.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Center", vert_index)

    # 内边界顶点组
    bpy.data.objects["Center"].select_set(False)
    cut_plane_inner = bpy.data.objects["Inner"]
    bpy.context.view_layer.objects.active = cut_plane_inner
    cut_plane_inner.select_set(True)
    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cut_plane_inner.data)
    vert_index = [v.index for v in bm.verts]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("Inner", vert_index)

    # 合并
    bpy.context.view_layer.objects.active = cut_plane_outer
    cut_plane_outer.select_set(True)
    cut_plane_center.select_set(True)
    cut_plane_inner.select_set(True)
    bpy.ops.object.join()

    # 拼接成面
    bpy.ops.object.mode_set(mode='EDIT')
    # 最内补面
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.edge_face_add()
    # 桥接内中边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Inner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='Center')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    # 桥接中外边界
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='Outer')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='Center')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='SELECT')
    if judge_normals():
        bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects["CutPlane"].select_set(False)
    main_obj = bpy.data.objects["右耳"]
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)


def plane_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    # 获取活动对象
    obj = bpy.context.active_object


    utils_bool_difference(obj.name, "CutPlane")

    # 获取下边界顶点用于挤出
    bpy.ops.object.mode_set(mode='EDIT')
    # 创建bmesh对象
    bm = bmesh.from_edit_mesh(bpy.data.objects["右耳"].data)
    bottom_outer_border_index = [v.index for v in bm.verts if v.select]
    # bpy.ops.mesh.delete(type='FACE')

    ori_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 将下边界加入顶点组
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')


def soft_eardrum_smooth_initial1():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    cur_obj_name = "右耳"
    cur_obj = bpy.data.objects.get(cur_obj_name)

    if (cur_obj != None):
        soft_eardrum_bottom_inner_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
        soft_eardrum_bottom_outer_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
        if (soft_eardrum_bottom_outer_vertex != None and soft_eardrum_bottom_inner_vertex != None):
            bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerVertex")
            if (soft_eardrum_outer_vertex == None):
                soft_eardrum_outer_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumInnerVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.loop_to_region()
            bpy.ops.mesh.loop_to_region(select_bigger=False)
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.mode_set(mode='OBJECT')
            soft_eardrum_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterVertex")
            if (soft_eardrum_inner_vertex == None):
                soft_eardrum_inner_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumOuterVertex")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.subdivide()
            bpy.ops.mesh.subdivide(number_cuts=2)
            bpy.ops.mesh.remove_doubles(threshold=0.15)
            bpy.ops.object.mode_set(mode='OBJECT')

            bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
            bottom_innner_border_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
            if (bottom_outer_border_vertex != None and bottom_innner_border_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.mode_set(mode='OBJECT')

                # 将选中的顶点范围扩大
                bpy.ops.object.mode_set(mode='EDIT')
                for i in range(6):
                    bpy.ops.mesh.select_more()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='OBJECT')
                soft_eardrum_select_vertex = cur_obj.vertex_groups.get("SoftEarDrumSelectVertex")
                if (soft_eardrum_select_vertex == None):
                    soft_eardrum_select_vertex = cur_obj.vertex_groups.new(name="SoftEarDrumSelectVertex")
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumSelectVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

                # 添加平滑修改器
                modifier_name = "SoftEarDrumOuterSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "BottomOuterBorderVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumOuterSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].factor = 1.6
                bpy.context.object.modifiers["SoftEarDrumOuterSmoothModifier"].iterations = 2

                modifier_name = "SoftEarDrumInnerSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "BottomInnerBorderVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumInnerSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].factor = 1.6
                bpy.context.object.modifiers["SoftEarDrumInnerSmoothModifier"].iterations = 2

                modifier_name = "SoftEarDrumAllInnerSmoothModifier"
                target_modifier = None
                for modifier in cur_obj.modifiers:
                    if modifier.name == modifier_name:
                        target_modifier = modifier
                if (target_modifier == None):
                    bpy.ops.object.modifier_add(type='SMOOTH')
                    bpy.context.object.modifiers["Smooth"].vertex_group = "SoftEarDrumInnerVertex"
                    hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
                    hard_eardrum_modifier.name = "SoftEarDrumAllInnerSmoothModifier"
                bpy.context.object.modifiers["SoftEarDrumAllInnerSmoothModifier"].factor = 0.8
                bpy.context.object.modifiers["SoftEarDrumAllInnerSmoothModifier"].iterations = 16


def soft_eardrum_smooth_initial():
    # cur_obj_name = "Retopo_右耳"
    # compare_obj_name = "右耳"
    # cur_obj = bpy.data.objects.get(cur_obj_name)
    # compare_obj = bpy.data.objects.get(compare_obj_name)
    # compare_obj.select_set(True)
    # bpy.context.view_layer.objects.active = compare_obj
    #
    # #将当前激活的物体重拓扑
    # bpy.context.scene.qremesher.autodetect_hard_edges = False
    # bpy.context.scene.qremesher.use_normals = False
    # bpy.context.scene.qremesher.use_materials = False
    # bpy.context.scene.qremesher.use_vertex_color = False
    # bpy.context.scene.qremesher.adapt_quad_count = False
    # bpy.context.scene.qremesher.adaptive_size = 100
    # bpy.context.scene.qremesher.target_count = 2000
    # bpy.ops.qremesher.remesh()

    bpy.ops.object.timer_softeardrum_add_modifier_after_qmesh()


# 将平滑所使用的顶点组和修改器全部应用
def soft_eardrum_smooth_submit():
    cur_obj_name = "右耳"
    cur_obj = bpy.data.objects.get(cur_obj_name)
    bpy.context.view_layer.objects.active = cur_obj
    if (cur_obj != None):
        # 应用平滑磨具中所使用的所有平滑修改器
        apply_modifier_name = ["SoftEarDrumOuterSmoothModifier", "SoftEarDrumInnerSmoothModifier"]
        target_modifier = None
        for modifier in cur_obj.modifiers:
            if modifier.name in apply_modifier_name:
                modifier_name = modifier.name
                bpy.ops.object.modifier_apply(modifier=modifier_name, single_user=True)
        # 删除平滑磨具中所使用到的所有平滑顶点组
        bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
        if (bottom_outer_border_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        bottom_inner_border_vertex = cur_obj.vertex_groups.get("BottomInnerBorderVertex")
        if (bottom_inner_border_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_ear_drum_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterVertex")
        if (soft_ear_drum_outer_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_ear_drum_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerVertex")
        if (soft_ear_drum_inner_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_ear_drum_bottom_outer_vertex = cur_obj.vertex_groups.get("SoftEarDrumBottomOuterVertex")
        if (soft_ear_drum_bottom_outer_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomOuterVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_ear_drum_bottom_inner_vertex = cur_obj.vertex_groups.get("SoftEarDrumBottomInnerVertex")
        if (soft_ear_drum_bottom_inner_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumBottomInnerVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_ear_drum_outer_smooth_vertex = cur_obj.vertex_groups.get("SoftEarDrumOuterSmoothVertex")
        if (soft_ear_drum_outer_smooth_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumOuterSmoothVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        soft_ear_drum_inner_smooth_vertex = cur_obj.vertex_groups.get("SoftEarDrumInnerSmoothVertex")
        if (soft_ear_drum_inner_smooth_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='SoftEarDrumInnerSmoothVertex')
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')


def judge_if_need_invert():
    obj = bpy.data.objects["右耳"]
    bm = bmesh.from_edit_mesh(obj.data)

    # 获取最低点
    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2])
    return not vert_order_by_z[0].select


def delete_useless_part():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.loop_to_region(select_bigger=True)

    obj = bpy.data.objects["右耳"]
    bm = bmesh.from_edit_mesh(obj.data)
    select_vert = [v.index for v in bm.verts if v.select]
    if not len(select_vert) == len(bm.verts):  # 如果相等，说明切割成功了，不需要删除多余部分
        # 判断最低点是否被选择
        invert_flag = judge_if_need_invert()

        if not invert_flag:
            # 不需要反转，直接删除面即可
            bpy.ops.mesh.delete(type='FACE')
        else:
            # 反转一下，删除顶点
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

    # 最后，删一下边界的直接的面
    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = bpy.data.objects["右耳"].vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 最后删掉没用的CutPlane
    # bpy.data.objects.remove(bpy.data.objects["CutPlane"], do_unlink=True)


def soft_clear_co_and_normal():
    global border_vert_co_and_normal
    border_vert_co_and_normal = []


def soft_set_co_and_normal(co, normal):
    global border_vert_co_and_normal
    border_vert_co_and_normal.append((co, normal))

def soft_set_highest_vert():
    global origin_highest_vert
    origin_highest_vert = get_highest_vert("右耳OriginForFitPlace")


def soft_eardrum():
    get_cut_plane()
    plane_cut()
    delete_useless_part()


_classes = [
    TimerSoftEarDrumAddModifierAfterQmesh,
    TimerSoftEarDrumThicknessUpdate
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
