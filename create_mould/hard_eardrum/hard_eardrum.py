from ..bottom_ring import bottom_cut
from ...tool import getOverride, moveToRight, moveToLeft, convert_to_mesh
import bpy
import bmesh

is_timer_modifier_start = False      #防止 定时器(完成重拓扑操作后为重拓扑后的物体添加修改器控制其平滑度)添加过多

# 定时器 检测重拓扑操作是否完成   完成重拓扑操作后为重拓扑后的物体添加修改器控制其平滑度
class TimerAddModifierAfterQmesh(bpy.types.Operator):
    bl_idname = "object.timer_add_modifier_after_qmesh"
    bl_label = "在重拓扑完成后为重拓扑后的物体添加平滑修改器"

    __timer = None

    def execute(self, context):
        op_cls = TimerAddModifierAfterQmesh
        op_cls.__timer = context.window_manager.event_timer_add(
            0.1, window=context.window)
        global is_timer_modifier_start  # 防止添加多余的定时器
        is_timer_modifier_start = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        op_cls = TimerAddModifierAfterQmesh
        global is_timer_modifier_start
        mould_type = bpy.context.scene.muJuTypeEnum
        lowest_z_co = bpy.context.scene.yingErMoLowestZCo
        cur_obj = bpy.data.objects["右耳"]
        cur_obj_name = cur_obj.name
        if context.area:
            context.area.tag_redraw()
        if(mould_type == "OP2"):                       #判断创建模具模块中选项是否为硬耳膜
        # if(True):
            if event.type == 'TIMER':
                obj = bpy.data.objects.get("Retopo_"+cur_obj.name)
                if(bpy.data.objects.get("Retopo_"+cur_obj.name) != None):               #判断重拓扑是否完成
                    cur_obj_qmesh = bpy.data.objects.get("Retopo_"+cur_obj.name)        #将原物体删除,将重拓扑后的物体名称改为原物体
                    bpy.data.objects.remove(cur_obj, do_unlink=True)
                    cur_obj_qmesh.name = cur_obj_name
                    moveToRight(cur_obj_qmesh)
                    bottom_smooth(lowest_z_co)                 #为重拓扑完成后的物体添加平滑修改器
                    bpy.ops.geometry.color_attribute_add(name="Color", color=(1, 0.319, 0.133, 1))
                    bpy.data.objects['右耳'].data.materials.clear()
                    bpy.data.objects['右耳'].data.materials.append(bpy.data.materials['Yellow'])
                    is_timer_modifier_start = False     #重拓扑完成且添加修改器后,退出该定时器
                    context.window_manager.event_timer_remove(op_cls.__timer)
                    op_cls.__timer = None
                    return {'FINISHED'}
            return {'PASS_THROUGH'}
        else:
            is_timer_modifier_start = False
            return {'FINISHED'}
        return {'PASS_THROUGH'}





#通过面板参数调整硬耳膜底面平滑度
def CreateMouldHardDrumSmooth(self,context):
    bl_description = "创建模具中的硬耳膜,平滑其底部边缘"

    obj = bpy.data.objects["右耳"]
    smooth = round(bpy.context.scene.yingErMoSheRuPianYi, 1)
    override = getOverride()
    with bpy.context.temp_override(**override):
        modifier_name = "HardEarDrumModifier"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:  # TODO  优化：   将创建修改器放到加厚的invoke中，应用修改器放到提交中
                target_modifier = modifier
        if (target_modifier != None):
            bpy.context.object.modifiers["HardEarDrumModifier"].factor = 0.8
            bpy.context.object.modifiers["HardEarDrumModifier"].iterations = int(smooth * 10)

def bottom_fill():
    bpy.ops.object.mode_set(mode='EDIT')

    #减少循环边中点数并补面
    bpy.ops.mesh.remove_doubles(threshold=0.42)
    bpy.ops.mesh.edge_face_add()

    # 使用qmesh重拓扑并优化平面光滑度
    bpy.context.scene.qremesher.adapt_quad_count = True
    bpy.context.scene.qremesher.use_vertex_color = False
    bpy.context.scene.qremesher.use_materials = False
    bpy.context.scene.qremesher.use_normals = False
    bpy.context.scene.qremesher.autodetect_hard_edges = False
    bpy.context.scene.qremesher.target_count = 2000
    bpy.context.scene.qremesher.adaptive_size = 50
    bpy.ops.qremesher.remesh()

    bpy.ops.object.mode_set(mode='OBJECT')



def bottom_smooth(lowest_z_co):
    #根据模型中顶点在z轴上的最低值,获取底面附近用于平滑的顶点。将顶点索引存储在该数组中
    hard_eardrum_smooth_vertex_index = []
    obj = bpy.data.objects["右耳"]
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    for vert in bm.verts:
        if ((vert.co[2] > lowest_z_co - 1.5) and (vert.co[2] < lowest_z_co + 1.5)):
            hard_eardrum_smooth_vertex_index.append(vert.index)

    # 根据获取的顶点索引数组创建顶点组
    bpy.ops.object.mode_set(mode='OBJECT')
    hard_eardrum_border_vertex = obj.vertex_groups.get("HardEarDrumBorderVertex")
    if (hard_eardrum_border_vertex == None):
        hard_eardrum_border_vertex = obj.vertex_groups.new(name="HardEarDrumBorderVertex")
    for vert_index in hard_eardrum_smooth_vertex_index:
        hard_eardrum_border_vertex.add([vert_index], 1, 'ADD')

    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # hard_eardrum_border_vertex = obj.vertex_groups.get("HardEarDrumBorderVertex")
    # bpy.ops.object.vertex_group_set_active(group='HardEarDrumBorderVertex')
    # if (hard_eardrum_border_vertex != None):
    #     bpy.ops.object.vertex_group_select()

    # 创建平滑修改器,指定硬耳膜平滑顶点组
    modifier_name = "HardEarDrumModifier"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:  # TODO  优化：   将创建修改器放到加厚的invoke中，应用修改器放到提交中
            target_modifier = modifier
    if (target_modifier == None):
        bpy.ops.object.modifier_add(type='SMOOTH')
        bpy.context.object.modifiers["Smooth"].vertex_group = "HardEarDrumBorderVertex"
        hard_eardrum_modifier = bpy.context.object.modifiers["Smooth"]
        hard_eardrum_modifier.name = "HardEarDrumModifier"
    bpy.context.object.modifiers["HardEarDrumModifier"].factor = 0.8
    bpy.context.object.modifiers["HardEarDrumModifier"].iterations = 2


def apply_hard_eardrum_template():
    # 硬耳膜底部切割
    high_percent = 0.25
    lowest_z_co = bottom_cut(high_percent)
    bpy.context.scene.yingErMoLowestZCo = lowest_z_co
    bpy.ops.object.mode_set(mode='EDIT')   #选中切割后的循环边
    cur_obj = bpy.data.objects["右耳"]
    bottom_outer_border_vertex = cur_obj.vertex_groups.get("BottomOuterBorderVertex")
    if(bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.mode_set(mode='OBJECT')
    # 底部切割后补面                         #TODO      补面过程有顿挫感,先复制出一份模型作为对比,在将当前模型透明过隐藏补面过程,补面完成后再将该模型实体化并删除复制的模型
    # active_obj = bpy.context.active_object
    # duplicate_obj = active_obj.copy()
    # duplicate_obj.data = active_obj.data.copy()
    # duplicate_obj.name = "HardDrumFillCompare"
    # duplicate_obj.animation_data_clear()
    # bpy.context.scene.collection.objects.link(duplicate_obj)
    # duplicate_obj.select_set(state=False)
    pass  # TODO 将当前模型变透明
    bottom_fill()                                      #底面切割后补面并且重拓扑
    convert_to_mesh('BottomRingBorderR', 'meshBottomRingBorderR', 0.18)
    pass  # TODO 将模型由透明变为非透明
    # bpy.data.objects.remove(duplicate_obj, do_unlink=True)
    # # 解决重拓扑的异步问题   添加平滑修改器,指定硬耳膜平滑顶点组,且可通过面板参数调整平滑度
    # # bottom_smooth(-5.2)
    bpy.ops.object.timer_add_modifier_after_qmesh()
    bpy.ops.object.mode_set(mode='OBJECT')






_classes = [
    TimerAddModifierAfterQmesh
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)