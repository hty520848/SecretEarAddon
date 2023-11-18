import bpy
import mathutils
import bmesh
from bpy_extras import view3d_utils
import blf

import math

font_info = {
    "font_id": 0,
    "handler": None,
}

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

    __running = True

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
        if event.type == 'MOUSEMOVE':
            # if event.type == 'Q':
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
            # 光线终点
            mwi_end = mwi @ end
            # 光线方向
            mwi_dir = mwi_end - mwi_start

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
            # innermw = ori_obj.matrix_world
            # innermw_inv = innermw.inverted()
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
                    outertree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                    # innertree = mathutils.bvhtree.BVHTree.FromBMesh(oribm)
                    # 进行对象和光线交叉判定
                    co, _, fidx, dis = outertree.ray_cast(
                        mwi_start, mwi_dir)
                    # 网格和光线碰撞时
                    if fidx is not None:
                        min = 666
                        index = 0
                        bm.faces.ensure_lookup_table()
                        oribm.faces.ensure_lookup_table()
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
                        # 判断当前顶点与原顶点的位置关系
                        # origin = innermw_inv @ cl
                        # dest = innermw_inv @ co
                        # direc = dest - origin
                        # maxdis = math.sqrt(direc.dot(direc))
                        # _, _, fidx2, _ = innertree.ray_cast(
                        #     origin, direc, maxdis)
                        origin_vec = oribm.verts[index].normal
                        flag = origin_vec.dot(disvec)
                        if flag > 0:
                            final_dis *= -1
                        MyHandleClass.remove_handler()
                        MyHandleClass.add_handler(
                            draw_callback_px, (None, final_dis))
                        # print(final_dis)
                        # 遍历顶点，根据厚度设置颜色
                        color_lay = bm.verts.layers.float_color["Color"]
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            bm.verts.ensure_lookup_table()
                            oribm.verts.ensure_lookup_table()
                            index_color = vert.index
                            disvec_color = oribm.verts[index_color].co - \
                                bm.verts[index_color].co
                            dis_color = disvec_color.dot(disvec_color)
                            thickness = round(math.sqrt(dis_color), 2)
                            # origin_color = innermw_inv @ cl
                            # dest_color = innermw_inv @ vert.co
                            # direc_color = dest_color - origin_color
                            # maxdis_color = math.sqrt(
                            #     direc_color.dot(direc_color))
                            # _, _, fidx3, _ = innertree.ray_cast(
                            #     origin_color, direc_color, maxdis_color)
                            origin_veccol = oribm.verts[index_color].normal
                            flag_color = origin_veccol.dot(disvec_color)
                            if flag_color > 0:
                                thickness *= -1

                            if (context.scene.localLaHouDu):
                                maxHoudu = context.scene.maxLaHouDu
                                minHoudu = context.scene.minLaHouDu
                                if (thickness > maxHoudu or thickness < minHoudu):
                                    # print("原坐标：",oribm.verts[index_color].co)
                                    # print("现坐标：",bm.verts[index_color].co)
                                    # 应该绘制的厚度
                                    if thickness > maxHoudu:
                                        lenth = maxHoudu
                                    elif thickness < minHoudu:
                                        lenth = minHoudu * (-1)
                                    # print("实际厚度：",thickness)
                                    # print("理论厚度：",lenth)
                                    # 根据厚度修改坐标
                                    bm.verts[index_color].co = oribm.verts[index_color].co - \
                                        disvec_color.normalized()*lenth
                                    # print("原坐标：",oribm.verts[index_color].co)
                                    # print("现坐标：",bm.verts[index_color].co)
                                    disvec_color = oribm.verts[index_color].co - \
                                        bm.verts[index_color].co
                                    dis_color = disvec_color.dot(
                                        disvec_color)
                                    thickness = round(
                                        math.sqrt(dis_color), 2)
                                    origin_veccol = oribm.verts[index_color].normal
                                    flag_color = origin_veccol.dot(
                                        disvec_color)
                                    if flag_color > 0:
                                        thickness *= -1
                                    # print("修改后的厚度：",thickness)

                            color = round(thickness / 0.8, 2)
                            if color >= 1:
                                color = 1
                            if color <= -1:
                                color = -1
                            if thickness >= 0:
                                colvert.x = color
                                colvert.y = 1 - color
                                colvert.z = 0
                            else:
                                colvert.x = 0
                                colvert.y = 1 + color
                                colvert.z = color * (-1)
                        bm.to_mesh(me)
                        bm.free()
                    else:
                        color_lay = bm.verts.layers.float_color["Color"]
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            colvert.x = 0
                            colvert.y = 0.25
                            colvert.z = 1
                        bm.to_mesh(me)
                        bm.free()
                        # print("no select")

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        op_cls = TEST_OT_SelectMouseOveredMesh

        if context.area.type == 'VIEW_3D':
            if not self.is_running():
                context.window_manager.modal_handler_add(self)
                op_cls.__running = True
                active_obj = bpy.context.active_object
                me = active_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bpy.ops.geometry.color_attribute_add()

                bpy.context.space_data.shading.light = 'MATCAP'
                bpy.context.space_data.shading.color_type = 'VERTEX'

                # color_lay = bm.verts.layers.float_color["Color"]
                # for vert in bm.verts:
                #     colvert = vert[color_lay]
                #     colvert.x = 0
                #     colvert.y = 0.25
                #     colvert.z = 1
                return {'RUNNING_MODAL'}
            else:
                op_cls.__running = False
                bpy.ops.geometry.color_attribute_remove()
                MyHandleClass.remove_handler()
                context.area.tag_redraw()
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


class MyHandleClass:
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


def draw_callback_px(self, thickness):
    """Draw on the viewports"""

    # BLF drawing routine
    font_id = font_info["font_id"]
    blf.position(font_id, 1500, 80, 0)
    blf.size(font_id, 50)
    rounded_number = round(thickness, 2)
    blf.draw(font_id, str(rounded_number)+"mm")


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
