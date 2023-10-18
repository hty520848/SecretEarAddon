import bpy
import mathutils
import bmesh
from bpy_extras import view3d_utils

from . import damo

import math
bl_info = {
    "name": "hty",
    "author": "",
    "version": (3, 0),
    "blender": (2, 80, 0),
    "location": "",
    "description": "",
    "warning": "",
    "support": "TESTING",
    "doc_url": "",
    "tracker_url": "",
    "category": "Mesh"
}


def get_region_and_space(context, area_type, region_type, space_type):
    region = None
    area = None
    space = None

    # 获取指定区域的信息
    for a in context.screen.areas:
        if a.type == area_type:
            area = a
            break
    else:
        return (None, None)
    # 获取指定区域的信息
    for r in area.regions:
        if r.type == region_type:
            region = r
            break
    # 获取指定区域的信息
    for s in area.spaces:
        if s.type == space_type:
            space = s
            break

    return (region, space)


# 选择位于鼠标光标位置的网格面的操作符
class TEST_OT_SelectMouseOveredMesh(bpy.types.Operator):

    bl_idname = "object.test_selelct_mouseovered_face"
    bl_label = "测试"
    bl_description = "test"

    # 如果为真，请选择位于鼠标光标位置的网格面
    # （如果为真，则处于模态模式）
    __running = True

    q = False
    # 在模式模式中返回真

    @classmethod
    def is_running(cls):
        return cls.__running

    def modal(self, context, event):
        op_cls = TEST_OT_SelectMouseOveredMesh
        active_obj = context.active_object

        # 重绘区域
        if context.area:
            context.area.tag_redraw()

        # 面板单击“鼠标拖动旋转对象”按钮“完成”
        # 按下时退出模态模式
        if not self.is_running():
            return {'FINISHED'}

        # 拖动鼠标时，选择鼠标光标所在的网格面
        # if event.type == 'MOUSEMOVE':
        if event.type == 'Q':
            if event.value == 'PRESS':
                op_cls.q = True

                # 获取鼠标光标的区域坐标
                mv = mathutils.Vector(
                    (event.mouse_region_x, event.mouse_region_y))

                # 单击功能区上的“窗口”区域中的
                # 获取信息和“三维视口”空间中的空间信息
                region, space = get_region_and_space(
                    context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
                )
                # 确定朝向鼠标光标位置发出的光线的方向
                ray_dir = view3d_utils.region_2d_to_vector_3d(
                    region,
                    space.region_3d,
                    mv
                )
                # 确定朝向鼠标光标位置发出的光线源
                ray_orig = view3d_utils.region_2d_to_origin_3d(
                    region,
                    space.region_3d,
                    mv
                )
                # 光线起点
                start = ray_orig
                # 光线终点
                end = ray_orig + ray_dir

                # 确定光线和对象的相交
                # 交叉判定在对象的局部坐标下进行
                # 将光线的起点和终点转换为局部坐标
                mwi = active_obj.matrix_world.inverted()
                # 光线起点
                mwi_start = mwi @ start
                print(mwi_start)
                # 光线终点
                mwi_end = mwi @ end
                # 光线方向
                mwi_dir = (mwi_end - mwi_start).normalized()

                # 取消选择对象的面
                # bpy.ops.mesh.select_all(action='DESELECT')

                # 获取活动对象
                active_obj = bpy.context.active_object
                name = bpy.context.object.name
                copyname = name + ".001"
                ori_obj = bpy.data.objects[copyname]
                orime = ori_obj.data
                oribm = bmesh.new()
                oribm.from_mesh(orime)
                # oribm.transform(ori_obj.matrix_world)
                # 确保活动对象的类型是网格
                if active_obj.type == 'MESH':
                    # 确保活动对象可编辑
                    if active_obj.mode == 'SCULPT':
                        # 获取网格数据
                        me = active_obj.data
                        # 创建bmesh对象
                        bm = bmesh.new()
                        # 将网格数据复制到bmesh对象
                        bm.from_mesh(me)
                        # bm.transform(active_obj.matrix_world)
                        # 构建BVH树
                        tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                        # 进行对象和光线交叉判定
                        co, _, fidx, dis = tree.ray_cast(mwi_start, mwi_dir)

                        # 网格和光线碰撞时
                        if fidx is not None:
                            # 在这里设置打磨的鼠标行为
                            print("select")
                            print(co)
                            min = 666
                            index = 0
                            bm.faces.ensure_lookup_table()
                            oribm.faces.ensure_lookup_table()
                            bm.faces[fidx].material_index = 1
                            # bpy.context.object.active_material_index = 1
                            # bpy.ops.object.material_slot_assign()
                            for v in bm.faces[fidx].verts:
                                vec = v.co - co
                                between = vec.dot(vec)
                                if (between <= min):
                                    min = between
                                    index = v.index
                            bm.verts.ensure_lookup_table()
                            oribm.verts.ensure_lookup_table()
                            disvec = oribm.verts[index].co - bm.verts[index].co
                            dis = disvec.dot(disvec)
                            final_dis = round(math.sqrt(dis), 2)
                            print(final_dis)
                            bm.to_mesh(me)
                            bm.free()
                        else:
                            # 在这里设置公共的鼠标行为
                            print("no select")

            if event.value == 'RELEASE':
                op_cls.q = False
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        op_cls = TEST_OT_SelectMouseOveredMesh

        if context.area.type == 'VIEW_3D':
            if not self.is_running():
                context.window_manager.modal_handler_add(self)
                op_cls.__running = True

                return {'RUNNING_MODAL'}
            else:
                op_cls.__running = False
                return {'FINISHED'}
        else:
            return {'CANCELLED'}


# UI
class TEST_PT_SelectMouseOveredMesh(bpy.types.Panel):

    bl_label = "测试用例"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "test"
    # bl_context = "mesh_edit"

    def draw(self, context):
        op_cls = TEST_OT_SelectMouseOveredMesh
        layout = self.layout
        if not op_cls.is_running():
            layout.operator(op_cls.bl_idname, text="开始", icon='PLAY')
        else:
            layout.operator(op_cls.bl_idname, text="结束", icon='PAUSE')


classes = [
    TEST_OT_SelectMouseOveredMesh,
    TEST_PT_SelectMouseOveredMesh,
]

# 设置世界颜色
# bpy.context.scene.world.use_nodes = False
# bpy.context.space_data.shading.background_type = 'WORLD'
# bpy.context.scene.world.color = (0.63, 0.95, 1)

# 新增材质
# obj = bpy.data.objects["Cube"]
# material_slots = obj.material_slots
# bpy.ops.object.material_slot_add()
# for m in material_slots:
#   material = m.material
#   if material == None:
#       obj.active_material = bpy.data.materials['Material']

# import bpy
# import random
# # 获取活动对象
# obj = bpy.context.active_object
# # 获取所有顶点组
# vgroups = obj.vertex_groups


# bpy.ops.object.editmode_toggle()
# for i in range(len(vgroups)):
#     selected_vgroup = vgroups[i]

#     # 检查顶点组是否存在
#     if selected_vgroup is not None:
#         # 获取网格数据
#         mesh = obj.data

#         # 选择指定名称的顶点组所属的网格
#         bpy.ops.object.mode_set(mode='OBJECT')
#         bpy.ops.object.select_all(action='DESELECT')
#         obj.select_set(True)
#         bpy.context.view_layer.objects.active = obj
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.vertex_group_set_active(group=selected_vgroup.name)
#         bpy.ops.object.vertex_group_select()
#         bpy.ops.object.mode_set(mode='OBJECT')
#         # 赋予颜色
#         bpy.ops.paint.vertex_paint_toggle()
#         bpy.context.object.data.use_paint_mask = True
#         bpy.data.brushes["Draw"].color = (random.random(),random.random(),random.random())
#         bpy.ops.paint.vertex_color_set()
#         bpy.ops.object.editmode_toggle()

def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
