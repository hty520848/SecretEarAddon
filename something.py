'''
Description: 
Date: 2024-01-11 19:03:07
LastEditTime: 2024-01-11 22:38:07
FilePath: /SecretEarAddon/something.py
'''
import bpy
import bmesh
from mathutils import Vector

bool_modifier2 = object.modifiers.new(
    name="shendu", type="SOLIDIFY")
bool_modifier2.use_rim_only = True
bool_modifier2.use_quality_normals = True
bool_modifier2.offset = 1
bool_modifier2.thickness = bpy.context.scene.qiegewaiBianYuan


def smooth_stepcut():
    pianyi = bpy.context.scene.qiegewaiBianYuan
    obj = bpy.data.objects['右耳']
    name = obj.name
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name + "pinghua"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    scene = bpy.context.scene
    scene.collection.objects.link(duplicate_obj)
    bpy.context.view_layer.objects.active = duplicate_obj
    bpy.ops.object.modifier_apply(modifier="step cut", single_user=True)
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects["右耳pinghua"].data)
    bm.faces.ensure_lookup_table()
    for i in range(len(bm.faces)-1, len(bm.faces)-11, -1):
        bm.faces[i].select = True
    bm.to_mesh(bpy.data.objects["右耳pinghua"].data)
    bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.remove_doubles(threshold=pianyi)
    bpy.ops.mesh.extrude_region_shrink_fatten(
        TRANSFORM_OT_shrink_fatten={"value": pianyi})
    bpy.ops.mesh.bevel(offset=pianyi, segments=8)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 获取直线对象
    curve_object = bpy.data.objects["BottomRingBorderR"]
    # 获取目标物体
    target_object = bpy.data.objects["右耳"]
    # 获取数据
    curve_data = curve_object.data
    target_mesh = target_object.data

    # 将曲线的每个顶点吸附到目标物体的表面
    for spline in curve_data.splines:
        for point in spline.points:
            # 获取顶点原位置
            vertex_co = curve_object.matrix_world @ Vector(point.co[0:3])

            # 计算顶点在目标物体面上的 closest point
            _, closest_co, _, _ = target_object.closest_point_on_mesh(
                vertex_co)

            # 将顶点位置设置为 closest point
            point.co[0:3] = closest_co
            point.co[3] = 0

    # # 创建一个新的集合
    # collection = bpy.data.collections.new("MyCollection")

    # # 将新的集合添加到场景中
    # bpy.context.scene.collection.children.link(collection)

    # # 获取当前场景
    # scene = bpy.context.scene

    # # 遍历场景中的所有集合
    # for collection in scene.collection.children:
    #     if collection.name == "MyCollection":
    #         bpy.context.view_layer.active_layer_collection =  bpy.context.view_layer.layer_collection.children[collection.name]

    # # 获取要删除的集合
    # collection = bpy.data.collections.get("MyCollection")

    # # 如果集合存在，则删除它
    # if collection:
    #     bpy.data.collections.remove(collection)
