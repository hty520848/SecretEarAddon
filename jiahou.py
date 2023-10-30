import bpy
import bmesh

# 新建材质节点，模型颜色相关


def newMaterial(id):

    mat = bpy.data.materials.get(id)

    if mat is None:
        mat = bpy.data.materials.new(name=id)

    mat.use_nodes = True

    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()

    return mat


def newShader(id, type, r, g, b):

    mat = newMaterial(id)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')

    if type == "diffuse":
        shader = nodes.new(type='ShaderNodeBsdfDiffuse')
        nodes["Diffuse BSDF"].inputs[0].default_value = (r, g, b, 1)

    elif type == "emission":
        shader = nodes.new(type='ShaderNodeEmission')
        nodes["Emission"].inputs[0].default_value = (r, g, b, 1)
        nodes["Emission"].inputs[1].default_value = 1

    elif type == "glossy":
        shader = nodes.new(type='ShaderNodeBsdfGlossy')
        nodes["Glossy BSDF"].inputs[0].default_value = (r, g, b, 1)
        nodes["Glossy BSDF"].inputs[1].default_value = 0

    elif type == "principled":
        shader = nodes.new(type='ShaderNodeBsdfPrincipled')
        nodes["Principled BSDF"].inputs[0].default_value = (r, g, b, 0.8)
        # nodes["Glossy BSDF"].inputs[1].default_value = 0
    links.new(shader.outputs[0], output.inputs[0])
    return mat


def initialModelColor():
    mat = newShader("Blue1", "principled", 0, 0.25, 1)  # 初始化模型颜色
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.context.space_data.shading.type = 'MATERIAL'
    bpy.context.scene.world.use_nodes = False  # 初始化背景颜色
    bpy.context.space_data.shading.background_type = 'WORLD'
    bpy.context.scene.world.color = (0.787, 0.871, 1)


def initialTransparency():
    mat = newShader("Blue2", "principled", 0, 0.25, 1)
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.context.space_data.shading.type = 'MATERIAL'
    # 模型材料透明度
    bpy.data.materials['Blue2'].blend_method = "BLEND"
    bpy.data.materials["Blue2"].node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.5


class InitialColor(bpy.types.Operator):
    bl_idname = "obj.initialcolor"
    bl_label = "初始化模型颜色"

    def execute(self, context):
        # bpy.data.screens["Layout"].show_statusbar = False

        bpy.ops.geometry.color_attribute_add()
        bpy.context.space_data.shading.light = 'MATCAP'
        bpy.context.space_data.shading.color_type = 'VERTEX'
        active_obj = bpy.context.active_object
        me = active_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            colvert.x = 0
            colvert.y = 0.25
            colvert.z = 1
        bm.to_mesh(me)
        bm.free()

        # initialModelColor()
        return {'FINISHED'}


class InitialTransparency(bpy.types.Operator):
    bl_idname = "obj.initialtransparency"
    bl_label = "将模型变为透明"

    def execute(self, context):
        initialTransparency()
        return {'FINISHED'}


class LocalReset(bpy.types.Operator):
    bl_idname = "obj.localreset"
    bl_label = "重置选中区域"

    def execute(self, context):
        if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()
        # 将物体用遮罩填充，由于遮罩区域无法操作，因此非遮罩区域就是选中的局部加厚区域
        bpy.ops.paint.mask_flood_fill(mode='VALUE', value=1)
        return {'FINISHED'}


class AddArea(bpy.types.Operator):
    bl_idname = "obj.addarea"
    bl_label = "扩大选中区域"

    def execute(self, context):
        if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(
            name="builtin_brush.Mask")  # 进入遮罩模式，笔刷方向设置为扩大区域
        bpy.data.brushes["Mask"].direction = "SUBTRACT"  # 减小遮罩区域，相当于扩大局部加厚区域
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为100
        return {'FINISHED'}


class ReduceArea(bpy.types.Operator):
    bl_idname = "obj.reducearea"
    bl_label = "减小选中区域"

    def execute(self, context):
        if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(
            name="built_brush.Mask")  # 进入遮罩模式，笔刷方向设置为缩小区域
        bpy.data.brushes["Mask"].direction = "ADD"  # 扩大遮罩区域，相当于缩小局部加厚区域
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为100
        return {'FINISHED'}


class LocalThickening(bpy.types.Operator):
    bl_idname = "obj.local_thickening"
    bl_label = "localThickening"

    def invoke(self, context, event):

        # 获取当前选中的物体
        selected_obj = context.active_object

        # 复制物体
        duplicate_obj = selected_obj.copy()
        duplicate_obj.data = selected_obj.data.copy()
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)
        # 将当前激活的物体变透明
        initialTransparency()

        if bpy.context.mode == "OBJECT":  # 将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Inflate")  # 调用膨胀模式笔刷

        bpy.context.scene.tool_settings.unified_paint_settings.size = 100  # 将用于框选区域的圆环半径设置为100

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        pass
        return {'FINISHED'}


class LocalSubmit(bpy.types.Operator):
    bl_idname = "obj.local_submit"
    bl_label = "localSubmit"

    def execute(self, context):

        selected_objs = bpy.data.objects
        active_object = bpy.context.active_object
        for selected_obj in selected_objs:  # 删除用于对比的未被激活的模型
            if (selected_obj != active_object):
                bpy.data.objects.remove(selected_obj, do_unlink=True)
        initialModelColor()  # 恢复模型最初的颜色，将激活的模型变为非透明
        if bpy.context.mode == "OBJECT":  # 清楚框选区域进行重置
            bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.paint.mask_flood_fill(mode='VALUE', value=1)
        return {'FINISHED'}


# 注册类
_classes = [
    InitialColor,
    InitialTransparency,
    LocalReset,
    AddArea,
    ReduceArea,
    LocalThickening,
    LocalSubmit
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
