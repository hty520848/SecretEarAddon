import bpy
import bmesh


def init_thickness():
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    obj = bpy.context.active_object

    modifier = obj.modifiers.new(name="Thickness", type='SOLIDIFY')
    bpy.context.object.modifiers["Thickness"].solidify_mode = 'NON_MANIFOLD'
    bpy.context.object.modifiers["Thickness"].thickness = 0.1
    bpy.context.object.modifiers["Thickness"].nonmanifold_merge_threshold = 0.35




