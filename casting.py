import bpy
from bpy.types import WorkSpaceTool
from .tool import *


is_casting_submit = False            #铸造法是否提交  铸造法中厚度参数只在未提交时有效
prev_casting_thickness = 0.2         #记录铸造法厚度,模块切换时保持厚度参数


def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2

def frontToCasting():
    '''
    根据当前激活物体复制出来一份若存在CastingReset,用于该模块的重置操作与模块切换
    '''
    # 若存在CastingReset,则先将其删除
    # 根据当前激活物体,复制一份生成CastingReset
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳CastingReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "CastingReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)
    castingInitial()  # 初始化
    global prev_casting_thickness
    bpy.context.scene.ruanErMoHouDu = prev_casting_thickness


def frontFromCasting():
    # 根据CastingReset,复制出一份物体替代当前操作物体
    # 删除CastingReset与CastingLast
    # 记录加厚参数
    global prev_casting_thickness
    prev_casting_thickness = bpy.context.scene.ruanErMoHouDu

    compare_obj = bpy.data.objects.get("CastingCompare")
    if (compare_obj != None):
        bpy.data.objects.remove(compare_obj, do_unlink=True)

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    resetname = name + "CastingReset"
    ori_obj = bpy.data.objects[resetname]
    bpy.data.objects.remove(obj, do_unlink=True)
    duplicate_obj = ori_obj.copy()
    duplicate_obj.data = ori_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name
    bpy.context.scene.collection.objects.link(duplicate_obj)
    moveToRight(duplicate_obj)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳CastingReset" or selected_obj.name == "右耳CastingLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToCasting():
    # 判断是否存在CastingReset
    # 若没有CastingReset,则说明跳过了Casting模块,再直接由后面的模块返回该模块。   TODO  根据切割操作的最后状态复制出CastingReset和CastingLast
    # 若存在CastingReset,则直接将CastingReset复制一份用于替换当前操作物体
    global prev_casting_thickness
    exist_CastingReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳CastingReset"):
            exist_CastingReset = True
    if (exist_CastingReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "CastingReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        castingInitial()      #初始化
        bpy.context.scene.ruanErMoHouDu = prev_casting_thickness

    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳LabelLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳HandleLast") != None):
            lastname = "右耳HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳VentCanalLast") != None):
            lastname = "右耳VentCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳SoundCanalLast") != None):
            lastname = "右耳SoundCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "CastingReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj
        castingInitial()      #初始化
        bpy.context.scene.ruanErMoHouDu = prev_casting_thickness


def backFromCasting():
    # 将铸造法提交
    # 将提交之后的模型保存CastingLast,用于模块切换,若存在CastingLast,则先将其删除
    #记录加厚参数
    global prev_casting_thickness
    prev_casting_thickness = bpy.context.scene.ruanErMoHouDu
    castingSubmit()
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳CastingLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "CastingLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)




def castingThicknessUpdate(thickness):
    global is_casting_submit
    if(not is_casting_submit):
         # 执行加厚操作
        cur_obj = bpy.data.objects["右耳"]
        casting_compare_obj = bpy.data.objects["CastingCompare"]
        if cur_obj.type == 'MESH':
            # 获取当前激活物体的网格数据
            me = cur_obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            ori_me = casting_compare_obj.data
            ori_bm = bmesh.new()
            ori_bm.from_mesh(ori_me)
            ori_bm.verts.ensure_lookup_table()

            for vert in bm.verts:
                vert.co = ori_bm.verts[vert.index].co + ori_bm.verts[vert.index].normal.normalized() * thickness
            bm.to_mesh(me)
            bm.free()
            ori_bm.free()
#

def castingInitial():
    global is_casting_submit
    is_casting_submit = False

    cur_obj = bpy.data.objects["右耳"]

    #复制出一份模型作为对比,将复制的物体加入到场景集合中
    compare_obj = bpy.data.objects.get("CastingCompare")
    if (compare_obj != None):
        bpy.data.objects.remove(compare_obj, do_unlink=True)
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.name = "CastingCompare"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    cur_obj.select_set(False)
    duplicate_obj.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj
    #为对比物体添加红色材质
    duplicate_obj.select_set(True)
    cur_obj.select_set(False)
    bpy.context.view_layer.objects.active = duplicate_obj
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    duplicate_obj.data.materials.clear()
    duplicate_obj.data.materials.append(red_material)
    #为当前操作物体添加透明材质
    duplicate_obj.select_set(False)
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj
    # mat = bpy.data.materials.get("Transparency")
    # if mat is None:
    #     mat = bpy.data.materials.new(name="Transparency")
    # mat.use_nodes = True
    # if mat.node_tree:
    #     mat.node_tree.links.clear()
    #     mat.node_tree.nodes.clear()
    # nodes = mat.node_tree.nodes
    # links = mat.node_tree.links
    # output = nodes.new(type='ShaderNodeOutputMaterial')
    # shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    # color = nodes.new(type="ShaderNodeVertexColor")
    # links.new(color.outputs[0], nodes["Principled BSDF"].inputs[0])
    # links.new(shader.outputs[0], output.inputs[0])
    # cur_obj.data.materials.clear()
    # cur_obj.data.materials.append(mat)
    # bpy.data.materials['Transparency'].blend_method = "BLEND"
    # bpy.data.materials["Transparency"].node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2
    initialTransparency()
    cur_obj.data.materials.clear()
    cur_obj.data.materials.append(bpy.data.materials['Transparency'])

    #为操作物体添加实体化修改器,通过参数实现铸造厚度
    # modifier_name = "CastingModifier"
    # target_modifier = None
    # for modifier in cur_obj.modifiers:
    #     if modifier.name == modifier_name:
    #         target_modifier = modifier
    # if (target_modifier == None):
    #     bpy.ops.object.modifier_add(type='SOLIDIFY')
    #     hard_eardrum_modifier = bpy.context.object.modifiers["Solidify"]
    #     hard_eardrum_modifier.name = "CastingModifier"
    # bpy.context.object.modifiers["CastingModifier"].offset = 1
    # bpy.context.object.modifiers["CastingModifier"]

    #通过法线放缩实现铸造厚度
    casting_compare_obj = bpy.data.objects["CastingCompare"]
    if cur_obj.type == 'MESH':
        # 获取当前激活物体的网格数据
        me = cur_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        ori_me = casting_compare_obj.data
        ori_bm = bmesh.new()
        ori_bm.from_mesh(ori_me)
        ori_bm.verts.ensure_lookup_table()

        for vert in bm.verts:
            vert.co = ori_bm.verts[vert.index].co + ori_bm.verts[vert.index].normal.normalized() * 0.2
        bm.to_mesh(me)
        bm.free()
        ori_bm.free()




def castingSubmit():
    global is_casting_submit
    is_casting_submit = True
    #将对比物材质由红色改为黄色
    compare_obj = bpy.data.objects.get("CastingCompare")
    if (compare_obj != None):
        compare_obj = bpy.data.objects["CastingCompare"]
        compare_obj.select_set(True)
        bpy.context.view_layer.objects.active = compare_obj
        bpy.ops.geometry.color_attribute_add(name="Color", color=(1, 0.319, 0.133, 1))
        bpy.data.objects['CastingCompare'].data.materials.clear()
        bpy.data.objects['CastingCompare'].data.materials.append(bpy.data.materials['Yellow'])




class CastingReset(bpy.types.Operator):
    bl_idname = "object.castingreset"
    bl_label = "铸造法重置"

    def invoke(self, context, event):

        bpy.context.scene.var = 100
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        #将铸造法厚度重置为默认值,若铸造法已经提交,则重新初始化
        global prev_casting_thickness
        prev_casting_thickness = 0.2
        bpy.context.scene.ruanErMoHouDu = 0.2
        return {'FINISHED'}




class CastingSubmit(bpy.types.Operator):
    bl_idname = "object.castingsubmit"
    bl_label = "铸造法提交"

    def invoke(self, context, event):
        bpy.context.scene.var == 101
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        print("铸造法提交")
        castingSubmit()
        return {'FINISHED'}









class MyTool_Casting1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_reset"
    bl_label = "铸造法重置"
    bl_description = (
        "重置模型,清除模型上的所有标签"
    )
    bl_icon = "ops.gpencil.sculpt_randomize"
    bl_widget = None
    bl_keymap = (
        ("object.castingreset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Casting2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_submit"
    bl_label = "铸造法提交"
    bl_description = (
        "提交铸造法中所作的操作"
    )
    bl_icon = "ops.gpencil.sculpt_smear"
    bl_widget = None
    bl_keymap = (
        ("object.castingsubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Casting3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.casting_mirror"
    bl_label = "铸造法镜像"
    bl_description = (
        "将该模型上的铸造法操作镜像到另一个模型上"
    )
    bl_icon = "ops.gpencil.sculpt_smooth"
    bl_widget = None
    def draw_settings(context, layout, tool):
        pass

    # 注册类
_classes = [
    CastingReset,
    CastingSubmit
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_Casting1, separator=True, group=False)
    # bpy.utils.register_tool(MyTool_Casting2, separator=True, group=False, after={MyTool_Casting1.bl_idname})
    # bpy.utils.register_tool(MyTool_Casting3, separator=True, group=False, after={MyTool_Casting2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    # bpy.utils.unregister_tool(MyTool_Casting1)
    # bpy.utils.unregister_tool(MyTool_Casting2)
    # bpy.utils.unregister_tool(MyTool_Casting3)

