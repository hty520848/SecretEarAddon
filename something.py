import bpy
import bmesh

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
