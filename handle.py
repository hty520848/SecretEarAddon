from asyncio import Handle
from .tool import *
import bpy
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
import mathutils
import bmesh

prev_on_object = False  # 判断鼠标在模型上与否的状态是否改变

is_add_handle = False   #是否添加过附件,只能添加一个附件。  模块切换时若添加过附件,则重新切换到添加附件模块时会添加一个附件

prev_location_x = 0     #记录附件位置
prev_location_y = 0
prev_location_z = 0
prev_rotation_x = 0
prev_rotation_y = 0
prev_rotation_z = 0
prev_handle_offset = 0  #记录面板中的附件偏移量



def initialTransparency():
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01


# 判断鼠标是否在上
def is_mouse_on_handle(context, event):
    name = "Cube"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        is_on_object = False  # 初始化变量

        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
        region, space = get_region_and_space(
            context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
        )

        ray_dir = view3d_utils.region_2d_to_vector_3d(
            region,
            space.region_3d,
            mv
        )
        ray_orig = view3d_utils.region_2d_to_origin_3d(
            region,
            space.region_3d,
            mv
        )

        start = ray_orig
        end = ray_orig + ray_dir

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    is_on_object = True  # 如果发生交叉，将变量设为True
        return is_on_object
    return False


# 判断鼠标状态是否发生改变
def is_changed(context, event):
    name = "Cube"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_object  # 之前鼠标是否在物体上

        if context.area:
            context.area.tag_redraw()

        # 获取鼠标光标的区域坐标
        mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        # 获取信息和空间信息
        region, space = get_region_and_space(
            context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
        )

        ray_dir = view3d_utils.region_2d_to_vector_3d(
            region,
            space.region_3d,
            mv
        )
        ray_orig = view3d_utils.region_2d_to_origin_3d(
            region,
            space.region_3d,
            mv
        )

        start = ray_orig
        end = ray_orig + ray_dir

        # 确定光线和对象的相交
        mwi = obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        if obj.type == 'MESH':
            if (obj.mode == 'OBJECT' or obj.mode == "SCULPT"):
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                if fidx is not None:
                    curr_on_object = True  # 如果发生交叉，将变量设为True
        if (curr_on_object != prev_on_object):
            prev_on_object = curr_on_object
            return True
        else:
            return False
    return False



#获取鼠标在右耳上的坐标
def cal_co(context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :return: 相交的坐标
    '''

    active_obj = bpy.data.objects["右耳"]
    co = []

    # 获取鼠标光标的区域坐标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )
    ray_dir = view3d_utils.region_2d_to_vector_3d(
        region,
        space.region_3d,
        mv
    )
    ray_orig = view3d_utils.region_2d_to_origin_3d(
        region,
        space.region_3d,
        mv
    )

    start = ray_orig
    end = ray_orig + ray_dir

    # 确定光线和对象的相交
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if active_obj.type == 'MESH':
        if active_obj.mode == 'OBJECT':
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            co, _, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None:
                return co  # 如果发生交叉，返回坐标的值

    return -1

def frontToHandle():
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳HandleReset"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "HandleReset"
    bpy.context.collection.objects.link(duplicate_obj1)
    moveToRight(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    initial()


def frontFromHandle():
    saveInfo()
    handlename = "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (handle_compare_obj != None):
        bpy.data.objects.remove(handle_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)


    #还原透明材质
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2

    name = "右耳"  # TODO    根据导入文件名称更改Handle
    obj = bpy.data.objects[name]
    resetname = name + "HandleReset"
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
        if (selected_obj.name == "右耳HandleReset" or selected_obj.name == "右耳HandleLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)


def backToHandle():
    exist_HandleReset = False
    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳HandleReset"):
            exist_HandleReset = True
    if (exist_HandleReset):
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        resetname = name + "HandleReset"
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

        initial()
    else:
        name = "右耳"  # TODO    根据导入文件名称更改
        obj = bpy.data.objects[name]
        lastname = "右耳VentCanalLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳SoundCanalLast") != None):
            lastname = "右耳SoundCanalLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳MouldLast") != None):
            lastname = "右耳MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳QieGeLast") != None):
            lastname = "右耳QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get("右耳LocalThickLast") != None):
            lastname = "右耳LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
            bpy.context.collection.objects.link(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = "右耳DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "HandleReset"
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

        initial()

def backFromHandle():

    saveInfo()
    handleSubmit()

    # 还原透明材质
    mat = newShader("Transparency")  # 创建材质
    mat.blend_method = "BLEND"
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.2

    all_objs = bpy.data.objects
    for selected_obj in all_objs:
        if (selected_obj.name == "右耳HandleLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "HandleLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    duplicate_obj1.hide_set(True)


def saveInfo():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global prev_handle_offset

    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    #记录附件位置信息
    if(plane_obj != None):
        prev_location_x = plane_obj.location[0]
        prev_location_y = plane_obj.location[1]
        prev_location_z = plane_obj.location[2]
        prev_rotation_x = plane_obj.rotation_euler[0]
        prev_rotation_y = plane_obj.rotation_euler[1]
        prev_rotation_z = plane_obj.rotation_euler[2]
        prev_handle_offset = bpy.context.scene.erMoFuJianOffset



def initial():
    global prev_location_x
    global prev_location_y
    global prev_location_z
    global prev_rotation_x
    global prev_rotation_y
    global prev_rotation_z
    global prev_handle_offset
    global is_add_handle
    if(is_add_handle == True):
        addHandle()
        # 将Plane激活并选中
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        plane_obj.location[0] = prev_location_x
        plane_obj.location[1] = prev_location_y
        plane_obj.location[2] = prev_location_z
        plane_obj.rotation_euler[0] = prev_rotation_x
        plane_obj.rotation_euler[1] = prev_rotation_y
        plane_obj.rotation_euler[2] = prev_rotation_z
        bpy.ops.object.handleadd('INVOKE_DEFAULT')
        bpy.context.scene.erMoFuJianOffset = prev_handle_offset
    else:
        bpy.ops.wm.tool_set_by_id(name="my_tool.handle_add")






def handleReset():
    # 存在未提交Handle时,删除Handle和Plane
    handlename = "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 存在未提交的Handle,HandleCompare和Plane时
    if (handle_obj != None):
        bpy.data.objects.remove(handle_obj, do_unlink=True)
    if (handle_compare_obj != None):
        bpy.data.objects.remove(handle_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    #将面板参数重置
    bpy.context.scene.erMoFuJianOffset = 0
    # 将HandleReset复制并替代当前操作模型
    oriname = "右耳"  # TODO    右耳最终需要替换为导入时的文件名  右耳HandleReset同理
    ori_obj = bpy.data.objects.get(oriname)
    copyname = "右耳HandleReset"
    copy_obj = bpy.data.objects.get(copyname)
    if (ori_obj != None and copy_obj != None):
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = copy_obj.copy()
        duplicate_obj.data = copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)


def handleSubmit():
    name = "右耳"
    obj = bpy.data.objects.get(name)
    handlename = "Cube"
    handle_obj = bpy.data.objects.get(handlename)
    handlecomparename = "Cube.001"
    handle_compare_obj = bpy.data.objects.get(handlecomparename)
    planename = "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # 存在未提交的Handle和Plane时
    if (handle_obj != None and plane_obj != None):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = handle_obj
        bpy.ops.object.modifier_apply(modifier="Boolean", single_user=True)

        bpy.data.objects.remove(plane_obj, do_unlink=True)
        bpy.data.objects.remove(handle_obj, do_unlink=True)
        bpy.data.objects.remove(handle_compare_obj, do_unlink=True)

        # 合并后Handle会被去除材质,因此需要重置一下模型颜色为黄色
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["Draw"].color = (1, 0.6, 0.4)
        bpy.ops.paint.vertex_color_set()
        bpy.ops.object.mode_set(mode='OBJECT')


def addHandle():
    # 添加平面Plane和附件Cube
    # bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(-20, 6, 1), scale=(1, 1, 1))
    # bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(-20, 6, 1), scale=(1, 1, 1))
    bpy.ops.wm.stl_import(filepath="C:\\Users\\28712\Desktop\\耳膜附件\\软耳膜附件.stl")
    bpy.ops.wm.stl_import(filepath="C:\\Users\\28712\Desktop\\耳膜附件\\软耳膜附件.stl")
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(-100, -100, 0), scale=(4, 1.6, 1))

    name = "右耳"  # TODO    根据导入文件名称更改
    obj = bpy.data.objects[name]
    cubename = "软耳膜附件"
    cube_obj = bpy.data.objects[cubename]
    cube_obj.name = "Cube"
    cube_obj.location[0] = -100
    cube_obj.location[1] = -100
    moveToRight(cube_obj)
    cubecomparename = "软耳膜附件.001"
    cube_compare_obj = bpy.data.objects[cubecomparename]
    cube_compare_obj.name = "Cube.001"
    cube_compare_obj.location[0] = -100
    cube_compare_obj.location[1] = -100
    moveToRight(cube_compare_obj)
    planename = "Plane"
    plane_obj = bpy.data.objects[planename]
    plane_obj.scale[0] = 4
    plane_obj.scale[1] = 1.6
    moveToRight(plane_obj)

    # 为附件添加材质
    bpy.context.view_layer.objects.active = cube_obj
    red_material = bpy.data.materials.new(name="Red")
    red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    cube_obj.data.materials.clear()
    cube_obj.data.materials.append(red_material)

    # 将作为对比的附件变透明
    bpy.context.view_layer.objects.active = cube_compare_obj
    initialTransparency()
    cube_compare_obj.data.materials.clear()
    cube_compare_obj.data.materials.append(bpy.data.materials['Transparency'])



    # 为平面添加透明效果
    bpy.context.view_layer.objects.active = plane_obj
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
    # plane_obj.data.materials.clear()
    # plane_obj.data.materials.append(mat)
    # bpy.data.materials['Transparency'].blend_method = "BLEND"
    # bpy.data.materials["Transparency"].node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.1
    initialTransparency()
    plane_obj.data.materials.clear()
    plane_obj.data.materials.append(bpy.data.materials['Transparency'])

    #将平面设置为附件的父物体。对父物体平面进行位移和大小缩放操作时，子物体字体会其改变
    bpy.context.view_layer.objects.active = plane_obj
    cube_obj.select_set(True)
    cube_compare_obj.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    cube_obj.select_set(False)
    cube_compare_obj.select_set(False)
    plane_obj.select_set(False)
    bpy.context.view_layer.objects.active = plane_obj
    plane_obj.select_set(True)

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    # 设置附件初始位置
    plane_obj.location[0] = 10  # TODO    Label初始位置应该为鼠标双击的位置
    plane_obj.location[1] = 10
    plane_obj.location[2] = 10

    plane_obj.scale[0] = 2
    plane_obj.scale[1] = 0.8
    plane_obj.scale[2] = 0.5


class HandleReset(bpy.types.Operator):
    bl_idname = "object.handlereset"
    bl_label = "附件重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 13
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_add_handle
        is_add_handle = False
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        saveInfo()
        handleReset()
        bpy.ops.wm.tool_set_by_id(name="my_tool.handle_add")
        return {'FINISHED'}


class HandleAdd(bpy.types.Operator):
    bl_idname = "object.handleadd"
    bl_label = "添加附件"

    def invoke(self, context, event):

        bpy.context.scene.var = 14
        global is_add_handle
        global prev_handle_offset
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if (not is_add_handle):
            is_add_handle = True
            addHandle()
            bpy.context.scene.erMoFuJianOffset = prev_handle_offset
            # 将Plane激活并选中
            planename = "Plane"
            plane_obj = bpy.data.objects.get(planename)
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            co = cal_co(context, event)
            if(co != -1):
                plane_obj.location = co

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        cubename = "Cube"
        handle_obj = bpy.data.objects.get(cubename)
        planename = "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = "右耳"
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if (bpy.context.scene.var == 14):
            if (is_mouse_on_handle(context, event) and is_changed(context, event)):
                # 调用handle的鼠标行为,将附件设置为选中的颜色
                yellow_material = bpy.data.materials.new(name="Yellow")
                yellow_material.diffuse_color = (1.0, 1.0, 0.0, 1.0)
                handle_obj.data.materials.clear()
                handle_obj.data.materials.append(yellow_material)
                bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                plane_obj.select_set(True)
                bpy.context.view_layer.objects.active = plane_obj
                cur_obj.select_set(False)
            elif ((not is_mouse_on_handle(context, event)) and is_changed(context, event)):
                # 调用公共鼠标行为,将附件设置为默认颜色
                red_material = bpy.data.materials.new(name="Red")
                red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                handle_obj.data.materials.clear()
                handle_obj.data.materials.append(red_material)
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                cur_obj.select_set(True)
                bpy.context.view_layer.objects.active = cur_obj
                plane_obj.select_set(False)
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}


class HandleSubmit(bpy.types.Operator):
    bl_idname = "object.handlesubmit"
    bl_label = "附件提交"

    def invoke(self, context, event):
        bpy.context.scene.var = 15
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        saveInfo()
        handleSubmit()
        return {'FINISHED'}


class MyTool_Handle1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_reset"
    bl_label = "附件重置"
    bl_description = (
        "重置模型,清除模型上的所有附件"
    )
    bl_icon = "ops.pose.breakdowner"
    bl_widget = None
    bl_keymap = (
        ("object.handlereset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_add"
    bl_label = "附件添加"
    bl_description = (
        "在模型上添加一个附件"
    )
    bl_icon = "ops.pose.relax"
    bl_widget = None
    bl_keymap = (
        # ("object.handleadd", {"type": 'MOUSEMOVE', "value": 'ANY'},
        #  {}),
        ("object.handleadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Handle3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.handle_submit"
    bl_label = "附件提交"
    bl_description = (
        "对于模型上所有附件提交实体化"
    )
    bl_icon = "ops.pose.push"
    bl_widget = None
    bl_keymap = (
        ("object.handlesubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    HandleReset,
    HandleAdd,
    HandleSubmit
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool_Handle1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Handle2, separator=True, group=False, after={MyTool_Handle1.bl_idname})
    bpy.utils.register_tool(MyTool_Handle3, separator=True, group=False, after={MyTool_Handle2.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Handle1)
    bpy.utils.unregister_tool(MyTool_Handle2)
    bpy.utils.unregister_tool(MyTool_Handle3)
