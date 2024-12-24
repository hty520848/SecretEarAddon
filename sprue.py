import bpy
import bmesh
import re
import mathutils
import time
from .tool import *
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
from .parameter import get_switch_time, set_switch_time, get_switch_flag, set_switch_flag, check_modals_running,\
    get_mirror_context, set_mirror_context, get_process_var_list


prev_on_object = False    # 判断鼠标在模型上与否的状态是否改变
prev_on_objectL = False

prev_on_sprue = False     # 判断鼠标在排气孔上与否的状态是否改变
prev_on_sprueL = False

prev_on_sphere = False    #判断鼠标是否在附件球体上
prev_on_sphereL = False

is_on_rotate = False      #是否处于旋转的鼠标状态,用于 附件三维旋转鼠标行为和附件平面旋转拖动鼠标行为之间的切换
is_on_rotateL = False

sprue_info_save = []    #保存已经提交过的sprue信息,用于模块切换时的初始化
sprue_info_saveL = []
sprue_index = -1 # 数组指针，指向排气孔状态数组中当前访问状态的排气孔，用于单步撤回操作
sprue_indexL = -1

is_sprueAdd_modal_start = False         #在启动下一个modal前必须将上一个modal关闭,防止modal开启过多过于卡顿
is_sprueAdd_modal_startL = False


def newColor(id, r, g, b, is_transparency, transparency_degree):
    mat = newMaterial(id)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.inputs[0].default_value = (r, g, b, 1)
    shader.inputs[6].default_value = 0.46
    shader.inputs[7].default_value = 0
    shader.inputs[9].default_value = 0.472
    shader.inputs[14].default_value = 1
    shader.inputs[15].default_value = 0.105
    links.new(shader.outputs[0], output.inputs[0])
    if is_transparency:
        mat.blend_method = "BLEND"
        shader.inputs[21].default_value = transparency_degree
    return mat


# 判断鼠标是否在物体上,排气孔
def is_mouse_on_sprue(context, event):
    name = bpy.context.scene.leftWindowObj
    name_outer = name + "CylinderOuter"
    name_inside = name + "CylinderInside"
    cylinder_outer_obj = bpy.data.objects.get(name_outer)
    cylinder_inside_obj = bpy.data.objects.get(name_inside)
    if (cylinder_outer_obj != None and cylinder_inside_obj != None):
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
        mwi = cylinder_outer_obj.matrix_world.inverted()
        mwi_start = mwi @ start
        mwi_end = mwi @ end
        mwi_dir = mwi_end - mwi_start

        # 确定光线和对象的相交
        mwi1 = cylinder_inside_obj.matrix_world.inverted()
        mwi_start1 = mwi1 @ start
        mwi_end1 = mwi1 @ end
        mwi_dir1 = mwi_end1 - mwi_start1

        if cylinder_outer_obj.type == 'MESH' and cylinder_inside_obj.type == 'MESH':
                mesh = cylinder_outer_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

                _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

                mesh1 = cylinder_inside_obj.data
                bm1 = bmesh.new()
                bm1.from_mesh(mesh1)
                tree1 = mathutils.bvhtree.BVHTree.FromBMesh(bm1)

                _, _, fidx1, _ = tree1.ray_cast(mwi_start1, mwi_dir1, 2000.0)

                if (fidx is not None) or (fidx1 is not None):
                    is_on_object = True  # 如果发生交叉，将变量设为True
        return is_on_object
    return False

# 判断鼠标是否在排气孔旋转圆球上
def is_mouse_on_sphere(context, event):
    name = bpy.context.scene.leftWindowObj
    plane_name = name + 'Plane'
    plane_obj = bpy.data.objects.get(plane_name)
    if (plane_obj != None):
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        region, space = get_region_and_space(
            context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
        )
        rv3d = space.region_3d
        coord_3d = plane_obj.location
        # 将三维坐标转换为二维坐标
        coord_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, coord_3d)
        if (coord_2d != None):
            plane_x, plane_y = coord_2d
            dis = math.sqrt(math.fabs(plane_x - mouse_x) ** 2 + math.fabs(plane_y - mouse_y) ** 2)
            if (dis <= 372):
                return True
            else:
                return False
    return False

# 判断鼠标是否在物体上,模型
def is_mouse_on_object(context, event):
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    if(obj != None):
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
def is_changed_sprue(context, event):
    ori_name = bpy.context.scene.leftWindowObj
    name = bpy.context.scene.leftWindowObj + "CylinderOuter"
    obj = bpy.data.objects.get(name)
    if (obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_sprue  # 之前鼠标是否在物体上
        global prev_on_sprueL
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
        if ori_name == '右耳':
            if (curr_on_object != prev_on_sprue):
                prev_on_sprue = curr_on_object
                return True
            else:
                return False
        elif ori_name == '左耳':
            if (curr_on_object != prev_on_sprueL):
                prev_on_sprueL = curr_on_object
                return True
            else:
                return False

    return False


# 判断鼠标状态是否发生改变,圆球
def is_changed_sphere(context, event):
    global prev_on_sphere  # 之前鼠标是否在物体上
    global prev_on_sphereL  # 之前鼠标是否在物体上

    name = bpy.context.scene.leftWindowObj
    curr_on_object = is_mouse_on_sphere(context, event)

    if name == '右耳':
        if (curr_on_object != prev_on_sphere):
            prev_on_sphere = curr_on_object
            return True
        else:
            return False
    elif name == '左耳':
        if (curr_on_object != prev_on_sphereL):
            prev_on_sphereL = curr_on_object
            return True
        else:
            return False

# 判断鼠标状态是否发生改变,模型
def is_changed(context, event):
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    if(obj != None):
        curr_on_object = False  # 当前鼠标是否在物体上,初始化为False
        global prev_on_object  # 之前鼠标是否在物体上
        global prev_on_objectL
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
        if name == '右耳':
            if (curr_on_object != prev_on_object):
                prev_on_object = curr_on_object
                return True
            else:
                return False
        elif name == '左耳':
            if (curr_on_object != prev_on_objectL):
                prev_on_objectL = curr_on_object
                return True
            else:
                return False
    return False

def sprue_forward():
    '''
    添加多个排气孔的时候,向后切换的排气孔状态
    '''
    global sprue_index
    global sprue_indexL
    global sprue_info_save
    global sprue_info_saveL
    # bpy.context.scene.var = 0
    name = bpy.context.scene.leftWindowObj
    sprue_index_cur = None
    sprue_info_save_cur = None
    size = None
    print("进入sprue_forward")
    if (name == "右耳"):
        sprue_index_cur = sprue_index
        sprue_info_save_cur = sprue_info_save
        size = len(sprue_info_save)
    elif (name == "左耳"):
        sprue_index_cur = sprue_indexL
        sprue_info_save_cur = sprue_info_saveL
        size = len(sprue_info_saveL)
    print("当前指针:", sprue_index_cur)
    print("数组大小:",size)
    if (sprue_index_cur + 1 < size):
        sprue_index_cur = sprue_index_cur +1
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            sprue_index = sprue_index + 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            sprue_indexL = sprue_indexL + 1
        #将当前激活的左右耳模型使用reset还原
        sprueReset()
        #根据sprue_index_cur重新添加sprue
        for i in range(sprue_index_cur):
            sprueInfo = sprue_info_save_cur[i]
            offset = sprueInfo.offset
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            # 添加Sprue并提交
            print("添加排气孔",i)
            sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
        #最后一个排气孔并不提交
        sprueInfo = sprue_info_save_cur[sprue_index_cur]
        offset = sprueInfo.offset
        l_x = sprueInfo.l_x
        l_y = sprueInfo.l_y
        l_z = sprueInfo.l_z
        r_x = sprueInfo.r_x
        r_y = sprueInfo.r_y
        r_z = sprueInfo.r_z
        # 添加一个sprue,激活鼠标行为
        bpy.ops.object.spruebackforwardadd('INVOKE_DEFAULT')
        # 设计问题,点击加号调用bpy.ops.object.sprueadd('INVOKE_DEFAULT')添加附件的时候,sprue_index也会自增加一,但此处调用不需要自增,因此再减一
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            sprue_index = sprue_index - 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            sprue_indexL = sprue_indexL - 1
        # 获取添加后的Sprue,并根据参数设置调整offset
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        if (name == "右耳"):
            bpy.context.scene.paiQiKongOffset = offset
        elif (name == "左耳"):
            bpy.context.scene.paiQiKongOffsetL = offset
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj


def sprue_backup():
    '''
    添加多个排气孔的时候,回退切换排气孔状态
    '''
    global sprue_index
    global sprue_indexL
    global sprue_info_save
    global sprue_info_saveL
    # bpy.context.scene.var = 0
    name = bpy.context.scene.leftWindowObj
    sprue_index_cur = None
    sprue_info_save_cur = None
    size = None
    print("进入sprue_backup")
    if (name == "右耳"):
        sprue_index_cur = sprue_index
        sprue_info_save_cur = sprue_info_save
        size = len(sprue_info_save)
    elif (name == "左耳"):
        sprue_index_cur = sprue_indexL
        sprue_info_save_cur = sprue_info_saveL
        size = len(sprue_info_saveL)
    print("当前指针:", sprue_index_cur)
    print("数组大小:", size)
    if (sprue_index_cur > 0):
        sprue_index_cur = sprue_index_cur -1
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            sprue_index = sprue_index - 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            sprue_indexL = sprue_indexL - 1
        # 将当前激活的左右耳模型使用reset还原
        sprueReset()
        # 根据sprue_index_cur重新添加sprue
        for i in range(sprue_index_cur):
            sprueInfo = sprue_info_save_cur[i]
            offset = sprueInfo.offset
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            # 添加Sprue并提交
            print("添加排气孔", i)
            sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
        # 最后一个排气孔并不提交
        sprueInfo = sprue_info_save_cur[sprue_index_cur]
        offset = sprueInfo.offset
        l_x = sprueInfo.l_x
        l_y = sprueInfo.l_y
        l_z = sprueInfo.l_z
        r_x = sprueInfo.r_x
        r_y = sprueInfo.r_y
        r_z = sprueInfo.r_z
        # 添加一个sprue,激活鼠标行为
        bpy.ops.object.spruebackforwardadd('INVOKE_DEFAULT')
        # 设计问题,点击加号调用bpy.ops.object.sprueadd('INVOKE_DEFAULT')添加附件的时候,sprue_index也会自增加一,但此处调用不需要自增,因此再减一
        if (name == "右耳"):
            # 设置替换数组中指针的指向
            sprue_index = sprue_index - 1
        elif (name == "左耳"):
            # 设置替换数组中指针的指向
            sprue_indexL = sprue_indexL - 1
        # 获取添加后的Sprue,并根据参数设置调整offset
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        if (name == "右耳"):
            bpy.context.scene.paiQiKongOffset = offset
        elif (name == "左耳"):
            bpy.context.scene.paiQiKongOffsetL = offset
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj





# 获取鼠标在右耳上的坐标
def cal_co(context, event):
    '''
    返回鼠标点击位置的坐标，没有相交则返回-1
    :return: 相交的坐标
    '''

    name = bpy.context.scene.leftWindowObj
    active_obj = bpy.data.objects[name]
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

            co, normal, _, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if co is not None and normal is not None:
                return co, normal  # 如果发生交叉，返回坐标的值

    return -1, -1


def sprue_fit_rotate(normal,location):
    '''
    将排气孔移动到位置location并将连界面与向量normal对齐垂直
    '''
    #获取排气孔平面(排气孔的父物体)
    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    #新建一个空物体根据向量normal建立一个局部坐标系
    empty = bpy.data.objects.new("CoordinateSystem", None)
    bpy.context.collection.objects.link(empty)
    empty.location = (0, 0, 0)
    rotation_matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()  # 将法线作为局部坐标系的z轴
    empty.matrix_world = rotation_matrix
    # 记录该局部坐标系在全局坐标系中的角度并将该空物体删除
    empty_rotation_x = empty.rotation_euler[0]
    empty_rotation_y = empty.rotation_euler[1]
    empty_rotation_z = empty.rotation_euler[2]
    bpy.data.objects.remove(empty, do_unlink=True)
    # 将排气孔摆正对齐
    if(plane_obj != None):
        plane_obj.location = location
        plane_obj.rotation_euler[0] = empty_rotation_x
        plane_obj.rotation_euler[1] = empty_rotation_y
        plane_obj.rotation_euler[2] = empty_rotation_z

def initialSprueTransparency():
    newColor("SprueTransparency", 1, 0.319, 0.133, 1, 0.01)  # 创建材质
    # mat = newShader("SprueTransparency")  # 创建材质
    # mat.blend_method = "BLEND"
    # mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.01


def frontToSprue():
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_on_rotate = False
    elif (name == "左耳"):
        is_on_rotateL = False

    name = bpy.context.scene.leftWindowObj
    casting_compare_obj = bpy.data.objects.get(name + "CastingCompare")
    if(casting_compare_obj != None):
        all_objs = bpy.data.objects
        name = bpy.context.scene.leftWindowObj
        for selected_obj in all_objs:
            if (selected_obj.name == name + "SprueReset" or selected_obj.name == name + "CastingCompareSprueReset"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)


        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "SprueReset"
        bpy.context.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.hide_set(True)

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects[castingname]
        duplicate_obj1 = casting_obj.copy()
        duplicate_obj1.data = casting_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = castingname + "SprueReset"
        bpy.context.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)
        duplicate_obj1.hide_set(True)

        initial()



def frontFromSprue():
    name = bpy.context.scene.leftWindowObj
    casting_compare_obj = bpy.data.objects.get(name + "CastingCompare")
    if (casting_compare_obj != None):
        # 若模型上存在未提交的排气孔,则记录信息并提交该字体
        sprueSubmit()


        name = bpy.context.scene.leftWindowObj
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        #存在未提交的Sprue和Plane时
        if (sprue_inner_obj != None):
            bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
        if (sprue_outer_obj != None):
            bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
        if (sprue_inside_obj != None):
            bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
        if (sprue_inner_offset_compare_obj != None):
            bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
        if (sprue_outer_offset_compare_obj != None):
            bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
        if (sprue_inside_offset_compare_obj != None):
            bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)
        if (plane_obj != None):
            bpy.data.objects.remove(plane_obj, do_unlink=True)
        # 删除排气孔对比物
        for obj in bpy.data.objects:
            if (name == "右耳"):
                pattern = r'右耳SprueCompare'
                if re.match(pattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)
            elif (name == "左耳"):
                pattern = r'左耳SprueCompare'
                if re.match(pattern, obj.name):
                    bpy.data.objects.remove(obj, do_unlink=True)

        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "SprueReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects[castingname]
        castingresetname = castingname + "SprueReset"
        ori_casting_obj = bpy.data.objects.get(castingresetname)
        if (ori_casting_obj == None):
            ori_casting_obj = bpy.data.objects.get(name + "CastingCompareSupportLast")
            if(ori_casting_obj == None):
                ori_casting_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if(ori_casting_obj != None):
            bpy.data.objects.remove(casting_obj, do_unlink=True)
            duplicate_obj1 = ori_casting_obj.copy()
            duplicate_obj1.data = ori_casting_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = castingname
            bpy.context.scene.collection.objects.link(duplicate_obj1)
            if (name == "右耳"):
                moveToRight(duplicate_obj1)
            elif (name == "左耳"):
                moveToLeft(duplicate_obj1)
            duplicate_obj1.select_set(False)

        all_objs = bpy.data.objects
        for selected_obj in all_objs:
            if (selected_obj.name == name + "SprueReset"  or selected_obj.name == name + "CastingCompareSprueReset"
                    or selected_obj.name == name + "SprueLast"):
                bpy.data.objects.remove(selected_obj, do_unlink=True)


    #调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj

def backToSprue():
    global is_on_rotate
    global is_on_rotateL
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        is_on_rotate = False
    elif (name == "左耳"):
        is_on_rotateL = False

    # 删除可能存在的排气孔对比物
    name = bpy.context.scene.leftWindowObj
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    exist_SprueReset = False
    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SprueReset"):
            exist_SprueReset = True
    if (exist_SprueReset):
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        resetname = name + "SprueReset"
        ori_obj = bpy.data.objects[resetname]
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects.get(castingname)
        castingresetname = castingname + "SprueReset"
        ori_casting_obj = bpy.data.objects.get(castingresetname)
        if (ori_casting_obj == None):
            ori_casting_obj = bpy.data.objects.get(name + "CastingCompareSupportLast")
            if(ori_casting_obj == None):
                ori_casting_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if (ori_casting_obj != None):
            bpy.data.objects.remove(casting_obj, do_unlink=True)
            duplicate_obj1 = ori_casting_obj.copy()
            duplicate_obj1.data = ori_casting_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = castingname
            bpy.context.scene.collection.objects.link(duplicate_obj1)
            if (name == "右耳"):
                moveToRight(duplicate_obj1)
            elif (name == "左耳"):
                moveToLeft(duplicate_obj1)
            duplicate_obj1.select_set(False)

        initial()
    else:
        name = bpy.context.scene.leftWindowObj
        obj = bpy.data.objects[name]
        lastname = name + "SupportLast"
        last_obj = bpy.data.objects.get(lastname)
        if (last_obj != None):
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "CastingLast") != None):
            lastname = name + "CastingLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "LabelLast") != None):
            lastname = name + "LabelLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "HandleLast") != None):
            lastname = name + "HandleLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "MouldLast") != None):
            lastname = name + "MouldLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "QieGeLast") != None):
            lastname = name + "QieGeLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        elif (bpy.data.objects.get(name + "LocalThickLast") != None):
            lastname = name + "LocalThickLast"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        else:
            lastname = name + "DamoCopy"
            last_obj = bpy.data.objects.get(lastname)
            ori_obj = last_obj.copy()
            ori_obj.data = last_obj.data.copy()
            ori_obj.animation_data_clear()
            ori_obj.name = name + "SprueReset"
            bpy.context.collection.objects.link(ori_obj)
            if (name == "右耳"):
                moveToRight(ori_obj)
            elif (name == "左耳"):
                moveToLeft(ori_obj)
            ori_obj.hide_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)
        duplicate_obj = ori_obj.copy()
        duplicate_obj.data = ori_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        duplicate_obj.select_set(True)
        bpy.context.view_layer.objects.active = duplicate_obj

        castingname = name + "CastingCompare"
        casting_obj = bpy.data.objects.get(castingname)
        castingresetname = castingname + "SprueReset"
        ori_casting_obj = bpy.data.objects.get(castingresetname)
        if (ori_casting_obj == None):
            ori_casting_obj = bpy.data.objects.get(name + "CastingCompareSupportLast")
            if (ori_casting_obj == None):
                ori_casting_obj = bpy.data.objects.get(name + "CastingCompareLast")
        if (ori_casting_obj != None):
            bpy.data.objects.remove(casting_obj, do_unlink=True)
            duplicate_obj1 = ori_casting_obj.copy()
            duplicate_obj1.data = ori_casting_obj.data.copy()
            duplicate_obj1.animation_data_clear()
            duplicate_obj1.name = castingname
            bpy.context.scene.collection.objects.link(duplicate_obj1)
            if (name == "右耳"):
                moveToRight(duplicate_obj1)
            elif (name == "左耳"):
                moveToLeft(duplicate_obj1)
            duplicate_obj1.select_set(False)

        initial()


def backFromSprue():

    # 提交附件并保存附件信息
    sprueSubmit()

    all_objs = bpy.data.objects
    name = bpy.context.scene.leftWindowObj
    for selected_obj in all_objs:
        if (selected_obj.name == name + "SprueLast"):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    duplicate_obj1 = obj.copy()
    duplicate_obj1.data = obj.data.copy()
    duplicate_obj1.animation_data_clear()
    duplicate_obj1.name = name + "SprueLast"
    bpy.context.collection.objects.link(duplicate_obj1)
    if (name == "右耳"):
        moveToRight(duplicate_obj1)
    elif (name == "左耳"):
        moveToLeft(duplicate_obj1)
    duplicate_obj1.hide_set(True)

    # 调用公共鼠标行为
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    # 将激活物体设置为左/右耳
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj





def createSprue():
    #导入排气孔相关物体
    script_dir = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.join(script_dir, "stl\\CylinderInner.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    relative_path = os.path.join(script_dir, "stl\\CylinderInside.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    relative_path = os.path.join(script_dir, "stl\\CylinderOuter.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    relative_path = os.path.join(script_dir, "stl\\SpruePlane.stl")
    bpy.ops.wm.stl_import(filepath=relative_path)
    # # 导入排气孔模块中的圆球,主要用于鼠标模式切换,当三维旋转状态开启的时候,鼠标在圆球上的时候,调用三维旋转鼠标行为,否则调用公共鼠标行为
    # bpy.ops.mesh.primitive_uv_sphere_add(segments=30, ring_count=30, radius=10, enter_editmode=False, align='WORLD',
    #                                      location=(0, 0, 1.8), scale=(1, 1, 1))
    obj = bpy.data.objects.get("CylinderOuter")
    obj1 = bpy.data.objects.get("CylinderInside")
    obj2 = bpy.data.objects.get("CylinderInner")
    plane = bpy.data.objects.get("SpruePlane")
    # sphere_obj = bpy.data.objects.get("Sphere")

    #重命名
    name = bpy.context.scene.leftWindowObj
    obj.name = name + "CylinderOuter"          #排气孔外壁
    obj1.name = name + "CylinderInside"        #小圆柱作为内芯,提交后将其删除
    obj2.name = name + "CylinderInner"         #排气孔内壁
    plane.name = name + "Plane"
    # sphere_obj.name = name + "SprueSphere"

    #将导入物体原点设置为几何中心
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.select_all(action='DESELECT')
    obj1.select_set(state=True)
    bpy.context.view_layer.objects.active = obj1
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.select_all(action='DESELECT')
    obj2.select_set(state=True)
    bpy.context.view_layer.objects.active = obj2
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.select_all(action='DESELECT')
    plane.select_set(state=True)
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')


    #为内外壁和内芯添加红色材质
    red_material = newColor("Red", 1, 0, 0, 0, 1)
    bpy.context.view_layer.objects.active = obj
    obj.data.materials.clear()
    obj.data.materials.append(red_material)
    bpy.context.view_layer.objects.active = obj1
    obj1.data.materials.clear()
    obj1.data.materials.append(red_material)
    bpy.context.view_layer.objects.active = obj2
    obj2.data.materials.clear()
    obj2.data.materials.append(red_material)
    #为平面添加透明材质
    bpy.context.view_layer.objects.active = plane
    initialSprueTransparency()
    plane.data.materials.clear()
    plane.data.materials.append(bpy.data.materials['SprueTransparency'])
    # # 为圆球添加透明效果
    # bpy.context.view_layer.objects.active = sphere_obj
    # initialSprueTransparency()
    # sphere_obj.data.materials.clear()
    # sphere_obj.data.materials.append(bpy.data.materials['SprueTransparency'])

    #将内外壁复制出来一份作为参数offset偏移的对比物
    cylinder_outer_compare_offset_obj = obj.copy()
    cylinder_outer_compare_offset_obj.data = obj.data.copy()
    cylinder_outer_compare_offset_obj.animation_data_clear()
    cylinder_outer_compare_offset_obj.name = name + "CylinderOuterOffsetCompare"
    bpy.context.collection.objects.link(cylinder_outer_compare_offset_obj)
    # cylinder_outer_compare_offset_obj.hide_set(True)
    cylinder_inner_compare_offset_obj = obj2.copy()
    cylinder_inner_compare_offset_obj.data = obj2.data.copy()
    cylinder_inner_compare_offset_obj.animation_data_clear()
    cylinder_inner_compare_offset_obj.name = name + "CylinderInnerOffsetCompare"
    bpy.context.collection.objects.link(cylinder_inner_compare_offset_obj)
    # cylinder_inner_compare_offset_obj.hide_set(True)
    cylinder_inside_compare_offset_obj = obj1.copy()
    cylinder_inside_compare_offset_obj.data = obj1.data.copy()
    cylinder_inside_compare_offset_obj.animation_data_clear()
    cylinder_inside_compare_offset_obj.name = name + "CylinderInsideOffsetCompare"
    bpy.context.collection.objects.link(cylinder_inside_compare_offset_obj)
    # cylinder_inside_compare_offset_obj.hide_set(True)


    #将排气孔内外壁和内芯绑定为一组,外壁作为父物体,提交时统一处理
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj1.select_set(True)
    obj2.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    obj1.select_set(False)
    obj2.select_set(False)

    #将排气孔内外壁,内外壁对比物和平面绑定为一组,平面为父物体,提交时统一处理
    cylinder_outer_compare_offset_obj.select_set(True)
    cylinder_inner_compare_offset_obj.select_set(True)
    cylinder_inside_compare_offset_obj.select_set(True)
    obj.select_set(True)
    # sphere_obj.select_set(True)
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
    obj.select_set(False)
    # sphere_obj.select_set(False)
    #内外壁对比物隐藏
    cylinder_outer_compare_offset_obj.hide_set(True)
    cylinder_inner_compare_offset_obj.hide_set(True)
    cylinder_inside_compare_offset_obj.hide_set(True)

    if (name == "右耳"):
        moveToRight(plane)
        moveToRight(obj)
        moveToRight(obj1)
        moveToRight(obj2)
        moveToRight(cylinder_outer_compare_offset_obj)
        moveToRight(cylinder_inner_compare_offset_obj)
        moveToRight(cylinder_inside_compare_offset_obj)
        # moveToRight(sphere_obj)
    elif (name == "左耳"):
        moveToLeft(plane)
        moveToLeft(obj)
        moveToLeft(obj1)
        moveToLeft(obj2)
        moveToLeft(cylinder_outer_compare_offset_obj)
        moveToLeft(cylinder_inner_compare_offset_obj)
        moveToLeft(cylinder_inside_compare_offset_obj)
        # moveToLeft(sphere_obj)


# def saveInfo():
#     '''
#     #在sprue提交前会保存sprue的相关信息
#     '''
#     global sprue_info_save
#     global sprue_info_saveL
#
#     name = bpy.context.scene.leftWindowObj
#     planename = name + "Plane"
#     plane_obj = bpy.data.objects.get(planename)
#     offset = None
#     if name == '右耳':
#         offset = bpy.context.scene.paiQiKongOffset
#     elif name == '左耳':
#         offset = bpy.context.scene.paiQiKongOffsetL
#     l_x = plane_obj.location[0]
#     l_y = plane_obj.location[1]
#     l_z = plane_obj.location[2]
#     r_x = plane_obj.rotation_euler[0]
#     r_y = plane_obj.rotation_euler[1]
#     r_z = plane_obj.rotation_euler[2]
#
#     sprue_info = SprueInfoSave(offset,l_x,l_y,l_z,r_x,r_y,r_z)
#     if name == '右耳':
#         sprue_info_save.append(sprue_info)
#     elif name == '左耳':
#         sprue_info_saveL.append(sprue_info)


def updateInfo():
    '''
       #单步撤回过程中若更改过排气孔位置信息,则在数组中更新该信息,若未添加过该字体信息,则将该字体信息保存
    '''
    global sprue_index
    global sprue_indexL
    global sprue_info_save
    global sprue_info_saveL

    name = bpy.context.scene.leftWindowObj
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    if(plane_obj != None):
        offset = None
        if name == '右耳':
            offset = bpy.context.scene.paiQiKongOffset
        elif name == '左耳':
            offset = bpy.context.scene.paiQiKongOffsetL
        l_x = plane_obj.location[0]
        l_y = plane_obj.location[1]
        l_z = plane_obj.location[2]
        r_x = plane_obj.rotation_euler[0]
        r_y = plane_obj.rotation_euler[1]
        r_z = plane_obj.rotation_euler[2]

        sprue_info = SprueInfoSave(offset,l_x,l_y,l_z,r_x,r_y,r_z)
        if name == '右耳':
            if (sprue_index < len(sprue_info_save)):
                sprue_info_save[sprue_index] = sprue_info
            elif (sprue_index == len(sprue_info_save)):
                sprue_info_save.append(sprue_info)
        elif name == '左耳':
            if (sprue_indexL < len(sprue_info_saveL)):
                sprue_info_saveL[sprue_indexL] = sprue_info
            elif (sprue_indexL == len(sprue_info_saveL)):
                sprue_info_saveL.append(sprue_info)

def initial():
    ''''
    切换到排气孔模块的时候,根据之前保存的字体信息进行初始化,恢复之前添加的排气孔状态
    '''
    global sprue_index
    global sprue_indexL
    global sprue_info_save
    global sprue_info_saveL
    name = bpy.context.scene.leftWindowObj
    # 对于数组中保存的sprue信息,前n-1个先添加后提交,最后一个添加不提交
    if name == '右耳':
        if (len(sprue_info_save) > 0):
            for i in range(len(sprue_info_save) - 1):
                sprueInfo = sprue_info_save[i]
                offset = sprueInfo.offset
                l_x = sprueInfo.l_x
                l_y = sprueInfo.l_y
                l_z = sprueInfo.l_z
                r_x = sprueInfo.r_x
                r_y = sprueInfo.r_y
                r_z = sprueInfo.r_z
                # 添加Sprue并提交
                sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
            sprueInfo = sprue_info_save[len(sprue_info_save) - 1]
            offset = sprueInfo.offset
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            # 添加一个sprue,激活鼠标行为
            bpy.ops.object.sprueswitch('INVOKE_DEFAULT')
            bpy.ops.object.spruebackforwardadd('INVOKE_DEFAULT')
            # 获取添加后的Sprue,并根据参数设置调整offset
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.paiQiKongOffset = offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
            # 将附件数组指针置为末尾
            sprue_index = len(sprue_info_save) - 1
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
    elif name == '左耳':
        if (len(sprue_info_saveL) > 0):
            for i in range(len(sprue_info_saveL) - 1):
                sprueInfo = sprue_info_saveL[i]
                offset = sprueInfo.offset
                l_x = sprueInfo.l_x
                l_y = sprueInfo.l_y
                l_z = sprueInfo.l_z
                r_x = sprueInfo.r_x
                r_y = sprueInfo.r_y
                r_z = sprueInfo.r_z
                # 添加Sprue并提交
                sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z)
            sprueInfo = sprue_info_saveL[len(sprue_info_saveL) - 1]
            offset = sprueInfo.offset
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            # 添加一个sprue,激活鼠标行为
            bpy.ops.object.sprueswitch('INVOKE_DEFAULT')
            bpy.ops.object.spruebackforwardadd('INVOKE_DEFAULT')
            # 获取添加后的Sprue,并根据参数设置调整offset
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            bpy.context.scene.paiQiKongOffsetL = offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
            # 将附件数组指针置为末尾
            sprue_indexL = len(sprue_info_saveL) - 1
        else:
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")

    #将旋转中心设置为左右耳模型
    cur_obj = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    # spherename = name + "SprueSphere"
    # sphere_obj = bpy.data.objects.get(spherename)
    # if (sphere_obj != None and name == '右耳' and is_on_rotate):
    #     sphere_obj.select_set(True)
    # if (sphere_obj != None and name == '左耳' and is_on_rotateL):
    #     sphere_obj.select_set(True)
    cur_obj.select_set(True)
    bpy.context.view_layer.objects.active = cur_obj



def sprueInitial(offset, l_x, l_y, l_z, r_x, r_y, r_z):
    '''
    根据状态数组中保存的信息,生成一个排气孔
    模块切换时,根据提交时保存的信息,添加sprue进行初始化,先根据信息添加sprue,之后再将sprue提交。与submit函数相比,提交时不必保存sprue信息。
    '''

    # 添加一个新的Sprue
    addSprue()

    name = bpy.context.scene.leftWindowObj
    sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # spherename = name + "SprueSphere"
    # sphere_obj = bpy.data.objects.get(spherename)

    obj_outer = bpy.data.objects.get(name)
    obj_inner = bpy.data.objects.get(name + "CastingCompare")

    if name == '右耳':
        bpy.context.scene.paiQiKongOffset = offset
    elif name == '左耳':
        bpy.context.scene.paiQiKongOffsetL = offset
    plane_obj.location[0] = l_x
    plane_obj.location[1] = l_y
    plane_obj.location[2] = l_z
    plane_obj.rotation_euler[0] = r_x
    plane_obj.rotation_euler[1] = r_y
    plane_obj.rotation_euler[2] = r_z

    # # 1.将排气孔的内壁选中与右耳Compare做布尔的并集
    # # 将排气孔内壁复制出一份用于后续操作(使用Bool Tool将字体铸造法和模型合并之后,字体铸造法模型会被自动删除)
    # sprue_inner_name = sprue_inner_obj.name
    # sprue_inner_obj_temp = sprue_inner_obj.copy()
    # sprue_inner_obj_temp.data = sprue_inner_obj.data.copy()
    # sprue_inner_obj_temp.animation_data_clear()
    # bpy.context.collection.objects.link(sprue_inner_obj_temp)
    # if (name == "右耳"):
    #     moveToRight(sprue_inner_obj_temp)
    # elif (name == "左耳"):
    #     moveToLeft(sprue_inner_obj_temp)
    # # 为排气孔内壁选中并重新计算法线,提高切割的成功率
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_inner_obj.select_set(True)
    # bpy.context.view_layer.objects.active = sprue_inner_obj
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.normals_make_consistent(inside=False)
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # obj_inner.select_set(True)
    # bpy.context.view_layer.objects.active = obj_inner
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.normals_make_consistent(inside=False)
    # bpy.ops.object.mode_set(mode='OBJECT')
    # # 为铸造法内壁添加布尔修改器,与排气孔内壁合并
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_inner_obj.select_set(True)
    # obj_inner.select_set(True)
    # bpy.context.view_layer.objects.active = obj_inner
    # bpy.ops.object.booltool_auto_union()
    # sprue_inner_obj_temp.name = sprue_inner_name
    # sprue_inner_obj = sprue_inner_obj_temp
    # # modifierSprueUnionInner = obj_inner.modifiers.new(name="SprueUnionInner", type='BOOLEAN')
    # # modifierSprueUnionInner.object = sprue_inner_obj
    # # modifierSprueUnionInner.operation = 'UNION'
    # # modifierSprueUnionInner.solver = 'FAST'
    # # bpy.ops.object.modifier_apply(modifier="SprueUnionInner")
    #
    #
    #
    # # 2.将排气孔的内芯选中与右耳做布尔的差集,内芯插入模型的部分会和右耳合并形成一块内凹的区域,这块顶点处于选中的状态,直接将其删除在右耳上得到一个孔
    # # 将铸造法内部物体顶点取消选中
    # bpy.ops.object.select_all(action='DESELECT')
    # obj_inner.select_set(True)
    # bpy.context.view_layer.objects.active = obj_inner
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    # # 将软耳膜支撑内芯尺寸缩小一些并将顶点选中
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_inside_obj.select_set(True)
    # bpy.context.view_layer.objects.active = sprue_inside_obj
    # sprue_inside_obj.scale[0] = 0.9
    # sprue_inside_obj.scale[1] = 0.9
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    # # 将排气孔内芯复制出一份用于后续操作(使用Bool Tool将字体铸造法和模型合并之后,字体铸造法模型会被自动删除)
    # sprue_inside_name = sprue_inside_obj.name
    # sprue_inside_obj_temp = sprue_inside_obj.copy()
    # sprue_inside_obj_temp.data = sprue_inside_obj.data.copy()
    # sprue_inside_obj_temp.animation_data_clear()
    # bpy.context.collection.objects.link(sprue_inside_obj_temp)
    # if (name == "右耳"):
    #     moveToRight(sprue_inside_obj_temp)
    # elif (name == "左耳"):
    #     moveToLeft(sprue_inside_obj_temp)
    # # 为铸造法内壁添加布尔修改器,与软耳膜支撑内芯做差集
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_inside_obj.select_set(True)
    # obj_inner.select_set(True)
    # bpy.context.view_layer.objects.active = obj_inner
    # bpy.ops.object.booltool_auto_difference()
    # sprue_inside_obj_temp.name = sprue_inside_name
    # sprue_inside_obj = sprue_inside_obj_temp
    # # obj_inner.select_set(True)
    # # bpy.context.view_layer.objects.active = obj_inner
    # # modifierSprueDifferenceInside = obj_inner.modifiers.new(name="SprueDifferenceInside", type='BOOLEAN')
    # # modifierSprueDifferenceInside.object = sprue_inside_obj
    # # modifierSprueDifferenceInside.operation = 'DIFFERENCE'
    # # modifierSprueDifferenceInside.solver = 'FAST'
    # # bpy.ops.object.modifier_apply(modifier="SprueDifferenceInside")
    # # 将选中的顶点直接删除在模型上得到软耳膜支撑的孔洞
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_less()
    # bpy.ops.mesh.delete(type='VERT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # # 3.将排气孔的内芯选中与右耳Compare做布尔的差集,内芯插入模型的部分会和右耳Compare合并形成一块内凹的区域,这块顶点处于选中的状态,直接将其删除在右耳上得到一个孔
    # bpy.ops.object.select_all(action='DESELECT')
    # obj_outer.select_set(True)
    # bpy.context.view_layer.objects.active = obj_outer
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    # obj_outer.select_set(False)
    # # 将软耳膜支撑内芯尺寸恢复正常并将顶点选中
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_inside_obj.select_set(True)
    # bpy.context.view_layer.objects.active = sprue_inside_obj
    # sprue_inside_obj.scale[0] = 1
    # sprue_inside_obj.scale[1] = 1
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    # # 将排气孔内芯复制出一份用于后续操作(使用Bool Tool将字体铸造法和模型合并之后,字体铸造法模型会被自动删除)
    # sprue_inside_name = sprue_inside_obj.name
    # sprue_inside_obj_temp = sprue_inside_obj.copy()
    # sprue_inside_obj_temp.data = sprue_inside_obj.data.copy()
    # sprue_inside_obj_temp.animation_data_clear()
    # bpy.context.collection.objects.link(sprue_inside_obj_temp)
    # if (name == "右耳"):
    #     moveToRight(sprue_inside_obj_temp)
    # elif (name == "左耳"):
    #     moveToLeft(sprue_inside_obj_temp)
    # # 为铸造法外壁添加布尔修改器,与软耳膜支撑内芯做差集
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_inside_obj.select_set(True)
    # obj_outer.select_set(True)
    # bpy.context.view_layer.objects.active = obj_outer
    # bpy.ops.object.booltool_auto_difference()
    # sprue_inside_obj_temp.name = sprue_inside_name
    # sprue_inside_obj = sprue_inside_obj_temp
    # # # 为铸造法内壁添加布尔修改器,与软耳膜支撑内芯做差集
    # # obj_outer.select_set(True)
    # # bpy.context.view_layer.objects.active = obj_outer
    # # modifierSupportDifferenceInside = obj_outer.modifiers.new(name="SupportDifferenceInside", type='BOOLEAN')
    # # modifierSupportDifferenceInside.object = sprue_inside_obj
    # # modifierSupportDifferenceInside.operation = 'DIFFERENCE'
    # # modifierSupportDifferenceInside.solver = 'FAST'
    # # bpy.ops.object.modifier_apply(modifier="SupportDifferenceInside")
    # # 将选中的顶点直接删除在模型上得到软耳膜支撑的孔洞
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_less()
    # bpy.ops.mesh.delete(type='VERT')
    # bpy.ops.object.mode_set(mode='OBJECT')
    #
    # # 4.将排气孔外壁与右耳模型做差集,得到排气孔的对比物体。 # 由于排气孔物体和透明的右耳外壳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比
    # # 将排气孔外壁复制一份用于布尔生成排气孔对比物
    # sprue_outer_compare_name = name + "SprueCompare"
    # sprue_outer_compare_obj = sprue_outer_obj.copy()
    # sprue_outer_compare_obj.data = sprue_outer_obj.data.copy()
    # sprue_outer_compare_obj.animation_data_clear()
    # bpy.context.collection.objects.link(sprue_outer_compare_obj)
    # sprue_outer_compare_obj.name = sprue_outer_compare_name
    # if (name == "右耳"):
    #     moveToRight(sprue_outer_compare_obj)
    # elif (name == "左耳"):
    #     moveToLeft(sprue_outer_compare_obj)
    # # 将排气孔对比物的位置移动到与排气孔外壁的位置相同(由于排气孔相关物体都在父物体平面下随着父物体的位置改变而改变,因此其位置信息仍为导入时的为位置,不能直接通过location设置其位置)
    # me = sprue_outer_compare_obj.data
    # bm = bmesh.new()
    # bm.from_mesh(me)
    # bm.verts.ensure_lookup_table()
    # ori_sprue_me = sprue_outer_obj.data
    # ori_sprue_bm = bmesh.new()
    # ori_sprue_bm.from_mesh(ori_sprue_me)
    # ori_sprue_bm.verts.ensure_lookup_table()
    # for vert in bm.verts:
    #     vert.co = ori_sprue_bm.verts[vert.index].co
    # bm.to_mesh(me)
    # bm.free()
    # ori_sprue_bm.free()
    # # 将复制出来的排气孔外壁对比物与右耳做布尔差集,将其切割为所需的形状
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_outer_compare_obj.select_set(True)
    # bpy.context.view_layer.objects.active = sprue_outer_compare_obj
    # modifierSprueCompareDifference = sprue_outer_compare_obj.modifiers.new(name="SprueCompareDifference",
    #                                                                        type='BOOLEAN')
    # modifierSprueCompareDifference.object = obj_outer
    # modifierSprueCompareDifference.operation = 'DIFFERENCE'
    # modifierSprueCompareDifference.solver = 'FAST'
    # bpy.ops.object.modifier_apply(modifier="SprueCompareDifference")
    #
    #
    # # 5.将排气孔的外壁与右耳做布尔的并集
    # # sprue_outer_obj.select_set(True)
    # # bpy.context.view_layer.objects.active = sprue_outer_obj
    # # # 先将排气孔外壁选中,使得其与铸造法外壳合并后被选中分离
    # # bpy.ops.object.mode_set(mode='EDIT')
    # # bpy.ops.mesh.select_all(action='SELECT')
    # # bpy.ops.object.mode_set(mode='OBJECT')
    # # sprue_outer_obj.select_set(False)
    # # obj_outer.select_set(True)
    # # bpy.context.view_layer.objects.active = obj_outer
    # # # 由于排气孔之前的模块存在布尔操作,会有其他顶点被选中,因此先将模型上选中顶点给取消选中
    # # bpy.ops.object.mode_set(mode='EDIT')
    # # bpy.ops.mesh.select_all(action='DESELECT')
    # # bpy.ops.object.mode_set(mode='OBJECT')
    # # 将排气孔外壁复制出一份用于后续操作(使用Bool Tool将字体铸造法和模型合并之后,字体铸造法模型会被自动删除)
    # sprue_outer_name = sprue_outer_obj.name
    # sprue_outer_obj_temp = sprue_outer_obj.copy()
    # sprue_outer_obj_temp.data = sprue_outer_obj.data.copy()
    # sprue_outer_obj_temp.animation_data_clear()
    # bpy.context.collection.objects.link(sprue_outer_obj_temp)
    # if (name == "右耳"):
    #     moveToRight(sprue_outer_obj_temp)
    # elif (name == "左耳"):
    #     moveToLeft(sprue_outer_obj_temp)
    # # 为铸造法外壳添加布尔修改器,与排气孔外壳合并
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_outer_obj.select_set(True)
    # obj_outer.select_set(True)
    # bpy.context.view_layer.objects.active = obj_outer
    # bpy.ops.object.booltool_auto_union()
    # sprue_outer_obj_temp.name = sprue_outer_name
    # sprue_outer_obj = sprue_outer_obj_temp
    # # #为铸造法外壳添加布尔修改器,与排气孔外壳合并
    # # modifierSprueUnionOuter = obj_outer.modifiers.new(name="SprueUnionOuter", type='BOOLEAN')
    # # modifierSprueUnionOuter.object = sprue_outer_obj
    # # modifierSprueUnionOuter.operation = 'UNION'
    # # modifierSprueUnionOuter.solver = 'FAST'
    # # bpy.ops.object.modifier_apply(modifier="SprueUnionOuter")
    # # # 由于排气孔物体和透明的右耳外壳合并后变为透明,因此需要设置一个不透明的参照物,与合并后的右耳对比,布尔合并后的顶点会被选中,将这些顶点复制一份并分离为独立的物体
    # # bpy.ops.object.mode_set(mode='EDIT')
    # # bpy.ops.mesh.duplicate()
    # # bpy.ops.mesh.separate(type='SELECTED')
    # # bpy.ops.object.mode_set(mode='OBJECT')
    # # sprue_compare_obj = bpy.data.objects.get(name + ".001")
    # # if (sprue_compare_obj != None):
    # #     sprue_compare_obj.name = name + "SprueCompare"
    # #     yellow_material = newColor("yellow", 1, 0.319, 0.133, 0, 1)
    # #     sprue_compare_obj.data.materials.clear()
    # #     sprue_compare_obj.data.materials.append(yellow_material)
    # #     if (name == "右耳"):
    # #         moveToRight(sprue_compare_obj)
    # #     elif (name == "左耳"):
    # #         moveToLeft(sprue_compare_obj)
    #
    # # 删除父物体平面之后,排气孔对比物体会恢复到初始位置,需要保存为位置信息
    # bpy.ops.object.select_all(action='DESELECT')
    # plane_obj.select_set(True)
    # bpy.context.view_layer.objects.active = plane_obj
    # bpy.ops.view3d.snap_cursor_to_active()  # 将3D游标位置设置为激活物体的原点位置
    # bpy.ops.object.select_all(action='DESELECT')
    # sprue_outer_compare_obj.select_set(True)
    # bpy.context.view_layer.objects.active = sprue_outer_compare_obj
    # bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')  # 将排气孔对比物的原点位置设置为游标位置,即平面的原点位置
    # sprue_outer_compare_obj.location = plane_obj.location  # 将排气孔位置信息设置为平面位置信息
    # sprue_outer_compare_obj.rotation_euler = plane_obj.rotation_euler
    # bpy.ops.view3d.snap_cursor_to_center()  # 将游标位置恢复为世界中心
    # sprue_compare_yellow_material = newColor("SprueCompareYellow", 1, 0.319, 0.133, 1, 0.4)  # 将排气孔对比物设置为模型的颜色
    # sprue_outer_compare_obj.data.materials.clear()
    # sprue_outer_compare_obj.data.materials.append(sprue_compare_yellow_material)

    # 为排气孔外壁添加顶点组保存 排气孔外壁的边缘顶点
    # 选中这些顶点补面,用于后续的布尔切割合并
    bpy.ops.object.select_all(action='DESELECT')
    sprue_outer_obj.select_set(True)
    bpy.context.view_layer.objects.active = sprue_outer_obj
    sprue_outer_top_edge_vertex = sprue_outer_obj.vertex_groups.get("SprueOuterTopEdge")
    if (sprue_outer_top_edge_vertex != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="SprueOuterTopEdge")
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    sprue_outer_top_edge_vertex = sprue_outer_obj.vertex_groups.new(name="SprueOuterTopEdge")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.object.vertex_group_set_active(group="SprueOuterTopEdge")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.edge_face_add()  # 选中这些顶点补面,将软耳膜外部支撑变为封闭物体用于后续的布尔切割合并
    bpy.ops.object.mode_set(mode='OBJECT')
    # 为排气孔内壁添加顶点组保存 排气孔内壁的边缘顶点
    # 选中这些顶点补面,用于后续的布尔切割合并
    bpy.ops.object.select_all(action='DESELECT')
    sprue_inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = sprue_inner_obj
    sprue_inner_top_edge_vertex = sprue_inner_obj.vertex_groups.get("SprueInnerTopEdge")
    if (sprue_inner_top_edge_vertex != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="SprueInnerTopEdge")
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    sprue_inner_top_edge_vertex = sprue_inner_obj.vertex_groups.new(name="SprueInnerTopEdge")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.object.vertex_group_set_active(group="SprueInnerTopEdge")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.edge_face_add()  # 选中这些顶点补面,将软耳膜外部支撑变为封闭物体用于后续的布尔切割合并
    bpy.ops.object.mode_set(mode='OBJECT')

    # 将排气孔外壁与左右耳合并
    bpy.ops.object.select_all(action='DESELECT')
    obj_outer.select_set(True)
    bpy.context.view_layer.objects.active = obj_outer
    bpy.ops.object.mode_set(mode='EDIT')  # 将模型上的顶点全部取消选中
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bool_modifier = obj_outer.modifiers.new(name="SprueOuterUnionBooleanModifier", type='BOOLEAN')
    bool_modifier.operation = 'UNION'
    bool_modifier.solver = 'FAST'
    bool_modifier.object = sprue_outer_obj
    bpy.ops.object.modifier_apply(modifier="SprueOuterUnionBooleanModifier", single_user=True)
    bpy.ops.object.mode_set(mode='EDIT')  # 布尔合并前左右耳模型上没有顶点被选中,排气孔外壁上边缘被选中
    bpy.ops.mesh.delete(type='ONLY_FACE')  # 布尔合并后排气孔外壁边缘顶点被选中,将面删除
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # 将排气孔内壁与左右耳Casting合并
    bpy.ops.object.select_all(action='DESELECT')
    obj_inner.select_set(True)
    bpy.context.view_layer.objects.active = obj_inner
    bpy.ops.object.mode_set(mode='EDIT')  # 将模型上的顶点全部取消选中
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bool_modifier = obj_inner.modifiers.new(name="SprueInnerUnionBooleanModifier", type='BOOLEAN')
    bool_modifier.operation = 'UNION'
    bool_modifier.solver = 'FAST'
    bool_modifier.object = sprue_inner_obj
    bpy.ops.object.modifier_apply(modifier="SprueInnerUnionBooleanModifier", single_user=True)
    bpy.ops.object.mode_set(mode='EDIT')  # 布尔合并前左右耳模型上没有顶点被选中,排气孔外壁上边缘被选中
    bpy.ops.mesh.delete(type='ONLY_FACE')  # 布尔合并后排气孔外壁边缘顶点被选中,将面删除
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


    # 删除排气管相关物体
    bpy.data.objects.remove(plane_obj, do_unlink=True)
    # bpy.data.objects.remove(sphere_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
    bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)

    # 将当前激活物体设置为左右耳模型
    bpy.ops.object.select_all(action='DESELECT')
    obj_outer.select_set(True)
    bpy.context.view_layer.objects.active = obj_outer

    # 合并后Sprue会被去除材质,因此需要重置一下模型颜色为黄色
    utils_re_color(name, (1, 0.319, 0.133))



def sprueReset():
    # 存在未提交排气孔时
    name = bpy.context.scene.leftWindowObj
    sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    # sprue_compare_obj = bpy.data.objects.get(name + "SprueCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # spherename = name + "SprueSphere"
    # sphere_obj = bpy.data.objects.get(spherename)
    # 存在未提交的Sprue,SprueCompare和Plane时
    if (sprue_inner_obj != None):
        bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
    if (sprue_outer_obj != None):
        bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
    if (sprue_inside_obj != None):
        bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
    if (sprue_inner_offset_compare_obj != None):
        bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
    if (sprue_outer_offset_compare_obj != None):
        bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
    if (sprue_inside_offset_compare_obj != None):
        bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)
    # if (sprue_compare_obj != None):
    #     bpy.data.objects.remove(sprue_compare_obj, do_unlink=True)
    if (plane_obj != None):
        bpy.data.objects.remove(plane_obj, do_unlink=True)
    # if (sphere_obj != None):
    #     bpy.data.objects.remove(sphere_obj, do_unlink=True)
    # 删除排气孔对比物
    for obj in bpy.data.objects:
        if (name == "右耳"):
            pattern = r'右耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
        elif (name == "左耳"):
            pattern = r'左耳SprueCompare'
            if re.match(pattern, obj.name):
                bpy.data.objects.remove(obj, do_unlink=True)
    # 将SprueReset复制并替代当前操作模型,将CastingCompareSprueReset复制并替代CastingCompare
    oriname = bpy.context.scene.leftWindowObj
    ori_obj = bpy.data.objects.get(oriname)                   #右耳
    oricastingname= name + "CastingCompare"
    ori_casting_obj = bpy.data.objects.get(oricastingname)    #铸造法内层物体
    copyname = name + "SprueReset"
    ori_copy_obj = bpy.data.objects.get(copyname)             #右耳reset物体
    castingcopyname = name + "CastingCompareSprueReset"                   #铸造法内层reset物体
    ori_casting_copy_obj = bpy.data.objects.get(castingcopyname)
    if (ori_obj != None and ori_casting_obj != None and ori_copy_obj != None and ori_casting_copy_obj != None):
        #将CastingCompare还原
        bpy.data.objects.remove(ori_casting_obj, do_unlink=True)
        duplicate_obj1 = ori_casting_copy_obj.copy()
        duplicate_obj1.data = ori_casting_copy_obj.data.copy()
        duplicate_obj1.animation_data_clear()
        duplicate_obj1.name = oricastingname
        bpy.context.collection.objects.link(duplicate_obj1)
        if (name == "右耳"):
            moveToRight(duplicate_obj1)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj1)

        #将右耳还原
        bpy.data.objects.remove(ori_obj, do_unlink=True)
        duplicate_obj = ori_copy_obj.copy()
        duplicate_obj.data = ori_copy_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = oriname
        bpy.context.collection.objects.link(duplicate_obj)
        if (name == "右耳"):
            moveToRight(duplicate_obj)
        elif (name == "左耳"):
            moveToLeft(duplicate_obj)
        bpy.context.view_layer.objects.active = duplicate_obj



def sprueSubmit():
    #  sprue_obj为排气孔物体,  sprue_offset_compare为隐藏的排气孔物体,用于偏移量参照,创建排气孔时一同创建   sprue_compare则作为对比,因为sprue_obj在提交后会变透明

    name = bpy.context.scene.leftWindowObj
    sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    planename = name + "Plane"
    plane_obj = bpy.data.objects.get(planename)
    # spherename = name + "SprueSphere"
    # sphere_obj = bpy.data.objects.get(spherename)

    obj_outer = bpy.data.objects.get(name)
    obj_inner = bpy.data.objects.get(name + "CastingCompare")


    # 存在未提交的Sprue,SprueCompare和Plane时
    if (sprue_inner_obj != None and sprue_outer_obj != None and  sprue_inside_obj != None and plane_obj != None
            and  sprue_inner_offset_compare_obj != None and sprue_outer_offset_compare_obj != None
            and sprue_inside_offset_compare_obj != None and  obj_outer != None and obj_inner != None):

        # 先将该Sprue的相关信息保存下来,用于模块切换时的初始化。
        # saveInfo()

        # 为排气孔外壁添加顶点组保存 排气孔外壁的边缘顶点
        # 选中这些顶点补面,用于后续的布尔切割合并
        bpy.ops.object.select_all(action='DESELECT')
        sprue_outer_obj.select_set(True)
        bpy.context.view_layer.objects.active = sprue_outer_obj
        sprue_outer_top_edge_vertex = sprue_outer_obj.vertex_groups.get("SprueOuterTopEdge")
        if (sprue_outer_top_edge_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="SprueOuterTopEdge")
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        sprue_outer_top_edge_vertex = sprue_outer_obj.vertex_groups.new(name="SprueOuterTopEdge")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.object.vertex_group_set_active(group="SprueOuterTopEdge")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.edge_face_add()  # 选中这些顶点补面,将软耳膜外部支撑变为封闭物体用于后续的布尔切割合并
        bpy.ops.object.mode_set(mode='OBJECT')
        # 为排气孔内壁添加顶点组保存 排气孔内壁的边缘顶点
        # 选中这些顶点补面,用于后续的布尔切割合并
        bpy.ops.object.select_all(action='DESELECT')
        sprue_inner_obj.select_set(True)
        bpy.context.view_layer.objects.active = sprue_inner_obj
        sprue_inner_top_edge_vertex = sprue_inner_obj.vertex_groups.get("SprueInnerTopEdge")
        if (sprue_inner_top_edge_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="SprueInnerTopEdge")
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        sprue_inner_top_edge_vertex = sprue_inner_obj.vertex_groups.new(name="SprueInnerTopEdge")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.object.vertex_group_set_active(group="SprueInnerTopEdge")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.edge_face_add()  # 选中这些顶点补面,将软耳膜外部支撑变为封闭物体用于后续的布尔切割合并
        bpy.ops.object.mode_set(mode='OBJECT')

        # 将排气孔外壁与左右耳合并
        bpy.ops.object.select_all(action='DESELECT')
        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer
        bpy.ops.object.mode_set(mode='EDIT')                 # 将模型上的顶点全部取消选中
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bool_modifier = obj_outer.modifiers.new(name="SprueOuterUnionBooleanModifier", type='BOOLEAN')
        bool_modifier.operation = 'UNION'
        bool_modifier.solver = 'FAST'
        bool_modifier.object = sprue_outer_obj
        bpy.ops.object.modifier_apply(modifier="SprueOuterUnionBooleanModifier", single_user=True)
        bpy.ops.object.mode_set(mode='EDIT')                # 布尔合并前左右耳模型上没有顶点被选中,排气孔外壁上边缘被选中
        bpy.ops.mesh.delete(type='ONLY_FACE')               # 布尔合并后排气孔外壁边缘顶点被选中,将面删除
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # 将排气孔内壁与左右耳Casting合并
        bpy.ops.object.select_all(action='DESELECT')
        obj_inner.select_set(True)
        bpy.context.view_layer.objects.active = obj_inner
        bpy.ops.object.mode_set(mode='EDIT')                 # 将模型上的顶点全部取消选中
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bool_modifier = obj_inner.modifiers.new(name="SprueInnerUnionBooleanModifier", type='BOOLEAN')
        bool_modifier.operation = 'UNION'
        bool_modifier.solver = 'FAST'
        bool_modifier.object = sprue_inner_obj
        bpy.ops.object.modifier_apply(modifier="SprueInnerUnionBooleanModifier", single_user=True)
        bpy.ops.object.mode_set(mode='EDIT')               # 布尔合并前左右耳模型上没有顶点被选中,排气孔外壁上边缘被选中
        bpy.ops.mesh.delete(type='ONLY_FACE')              # 布尔合并后排气孔外壁边缘顶点被选中,将面删除
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        #删除排气管相关物体
        bpy.data.objects.remove(plane_obj, do_unlink=True)
        # bpy.data.objects.remove(sphere_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inner_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_outer_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inside_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inner_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_outer_offset_compare_obj, do_unlink=True)
        bpy.data.objects.remove(sprue_inside_offset_compare_obj, do_unlink=True)


        #将当前激活物体设置为左右耳模型
        bpy.ops.object.select_all(action='DESELECT')
        obj_outer.select_set(True)
        bpy.context.view_layer.objects.active = obj_outer

        # 合并后Sprue会被去除材质,因此需要重置一下模型颜色为黄色
        utils_re_color(name, (1, 0.319, 0.133))
        if obj_outer.vertex_groups.get('TransformBorder') != None:
            transform_obj_name = bpy.context.scene.leftWindowObj + "SprueReset"
            transform_normal(transform_obj_name, [])


def addSprue():

    createSprue()

    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects[name]
    planename = name + "Plane"
    plane_obj = bpy.data.objects[planename]

    # 设置吸附
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {'FACE'}
    bpy.context.scene.tool_settings.snap_target = 'MEDIAN'
    bpy.context.scene.tool_settings.use_snap_align_rotation = True

    # 设置附件初始位置
    plane_obj.location[0] = 10
    plane_obj.location[1] = 10
    plane_obj.location[2] = 10


class SprueInfoSave(object):
    '''
    保存提交前的每个Sprue信息
    '''
    def __init__(self,offset,l_x,l_y,l_z,r_x,r_y,r_z):
        self.offset = offset
        self.l_x = l_x
        self.l_y = l_y
        self.l_z = l_z
        self.r_x = r_x
        self.r_y = r_y
        self.r_z = r_z


class SprueReset(bpy.types.Operator):
    bl_idname = "object.spruereset"
    bl_label = "排气孔重置"

    def invoke(self, context, event):
        bpy.context.scene.var = 86
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        global is_on_rotate
        global is_on_rotateL
        global sprue_index
        global sprue_indexL
        global sprue_info_save
        global sprue_info_saveL
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            is_on_rotate = False
            sprue_index = -1
            sprue_info_save = []
        elif name == '左耳':
            is_on_rotateL = False
            sprue_indexL = -1
            sprue_info_saveL = []

        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        # sprueSaveInfo()
        sprueReset()
        bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
        return {'FINISHED'}

class SprueBackForwardAdd(bpy.types.Operator):
    bl_idname = "object.spruebackforwardadd"
    bl_label = "单步撤回过程中添加排气孔"

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        #
        # global sprue_index
        # global sprue_indexL
        # global sprue_info_save
        # global sprue_info_saveL
        # name = bpy.context.scene.leftWindowObj
        # sprue_info_save_cur = None
        # if name == '右耳':
        #     sprue_info_save_cur = sprue_info_save
        # elif name == '左耳':
        #     sprue_info_save_cur = sprue_info_saveL
        #
        # #将可能存在的排气孔先提交
        # sprueSubmit()
        # # 双击添加过一个排气孔之后,才能够继续添加排气孔
        # if (len(sprue_info_save_cur) == 0):
        #     bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
        #     return {'FINISHED'}
        # #添加排气孔
        # addSprue()
        # # 将Plane激活并选中
        # name = bpy.context.scene.leftWindowObj
        # planename = name + "Plane"
        # plane_obj = bpy.data.objects.get(planename)
        # cur_obj = bpy.data.objects.get(name)
        # bpy.ops.object.select_all(action='DESELECT')
        # plane_obj.select_set(True)
        # bpy.context.view_layer.objects.active = plane_obj
        # #将排气孔位置设置为上一个排气孔的位置
        # sprueInfo = sprue_info_save_cur[len(sprue_info_save_cur) - 1]
        # if name == '右耳':
        #     sprue_index = sprue_index + 1
        #     print("添加排气孔后:", sprue_index)
        # elif name == '左耳':
        #     sprue_indexL = sprue_indexL + 1
        #     print("添加排气孔后:", sprue_indexL)
        # l_x = sprueInfo.l_x
        # l_y = sprueInfo.l_y
        # l_z = sprueInfo.l_z
        # r_x = sprueInfo.r_x
        # r_y = sprueInfo.r_y
        # r_z = sprueInfo.r_z
        # plane_obj.location[0] = l_x
        # plane_obj.location[1] = l_y
        # plane_obj.location[2] = l_z
        # plane_obj.rotation_euler[0] = r_x
        # plane_obj.rotation_euler[1] = r_y
        # plane_obj.rotation_euler[2] = r_z
        # #设置旋转中心
        # bpy.ops.object.select_all(action='DESELECT')
        # cur_obj.select_set(True)
        # bpy.context.view_layer.objects.active = cur_obj
        #
        # if bpy.context.scene.var != 80:
        #     bpy.context.scene.var = 80
        #     context.window_manager.modal_handler_add(self)
        #     print("spruebackforwordadd_modal_invoke")
        # return {'RUNNING_MODAL'}

    def execute(self, context):
        global sprue_index
        global sprue_indexL
        global sprue_info_save
        global sprue_info_saveL
        name = bpy.context.scene.leftWindowObj
        sprue_info_save_cur = None
        if name == '右耳':
            sprue_info_save_cur = sprue_info_save
        elif name == '左耳':
            sprue_info_save_cur = sprue_info_saveL

        # 将可能存在的排气孔先提交
        sprueSubmit()
        # 双击添加过一个排气孔之后,才能够继续添加排气孔
        if (len(sprue_info_save_cur) == 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
            return {'FINISHED'}
        # 添加排气孔
        addSprue()
        # 将Plane激活并选中
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        # 将排气孔位置设置为上一个排气孔的位置
        sprueInfo = sprue_info_save_cur[len(sprue_info_save_cur) - 1]
        if name == '右耳':
            sprue_index = sprue_index + 1
            print("添加排气孔后:", sprue_index)
        elif name == '左耳':
            sprue_indexL = sprue_indexL + 1
            print("添加排气孔后:", sprue_indexL)
        l_x = sprueInfo.l_x
        l_y = sprueInfo.l_y
        l_z = sprueInfo.l_z
        r_x = sprueInfo.r_x
        r_y = sprueInfo.r_y
        r_z = sprueInfo.r_z
        plane_obj.location[0] = l_x
        plane_obj.location[1] = l_y
        plane_obj.location[2] = l_z
        plane_obj.rotation_euler[0] = r_x
        plane_obj.rotation_euler[1] = r_y
        plane_obj.rotation_euler[2] = r_z
        # 设置旋转中心
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj

    def modal(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        is_on_rotate_cur = False
        if (name == '右耳'):
            is_on_rotate_cur = is_on_rotate
        elif (name == '左耳'):
            is_on_rotate_cur = is_on_rotateL
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if bpy.context.screen.areas[0].spaces.active.context == 'CONSTRAINT':
            if (bpy.context.scene.var == 80):
                # 在数组中更新附件的信息
                updateInfo()
                if(not is_on_rotate_cur):
                    if(sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                            # 调用sprue的鼠标行为
                            yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(yellow_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(yellow_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                        elif ((not is_mouse_on_object(context, event)) and (is_changed_sprue(context, event) or is_changed(context, event))):
                            # 调用公共鼠标行为
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                elif(is_on_rotate_cur):
                    if (sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                                is_changed_sphere(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用sprue的三维旋转鼠标行为
                            yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(yellow_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(yellow_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                        elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用公共鼠标行为
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                return {'PASS_THROUGH'}
            else:
                print("spruebackforwordadd_modal_finished")
                return {'FINISHED'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                print("spruebackforwordadd_modal_finished")
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class SprueAddInvoke(bpy.types.Operator):
    bl_idname = "object.sprueaddinvoke"
    bl_label = "调用sprueadd操作类,添加排气孔(在上一个modal结束后再调用新的modal,防止modal开启过多造成卡顿)"

    def invoke(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            is_on_rotate = False
        elif (name == "左耳"):
            is_on_rotateL = False

        bpy.context.scene.var = 81
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global is_sprueAdd_modal_start
        global is_sprueAdd_modal_startL
        name = bpy.context.scene.leftWindowObj
        if (name == '右耳'):
            if (not is_sprueAdd_modal_start):
                is_sprueAdd_modal_start = True
                bpy.ops.object.sprueadd('INVOKE_DEFAULT')
                return {'FINISHED'}
        elif (name == '左耳'):
            if (not is_sprueAdd_modal_startL):
                is_sprueAdd_modal_startL = True
                bpy.ops.object.sprueadd('INVOKE_DEFAULT')
                return {'FINISHED'}
        return {'PASS_THROUGH'}




class SprueAdd(bpy.types.Operator):
    bl_idname = "object.sprueadd"
    bl_label = "点击加号按钮添加排气孔"

    def invoke(self, context, event):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

        # global is_sprueAdd_modal_start
        # global is_sprueAdd_modal_startL
        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        #
        # global sprue_index
        # global sprue_indexL
        # global sprue_info_save
        # global sprue_info_saveL
        # name = bpy.context.scene.leftWindowObj
        # sprue_index_cur = None
        # sprue_info_save_cur = None
        # if name == '右耳':
        #     sprue_index_cur = sprue_index
        #     sprue_info_save_cur = sprue_info_save
        #     is_sprueAdd_modal_start = True
        # elif name == '左耳':
        #     sprue_index_cur = sprue_indexL
        #     sprue_info_save_cur = sprue_info_saveL
        #     is_sprueAdd_modal_startL = True
        #
        # #将可能存在的排气孔先提交
        # sprueSubmit()
        # # 双击添加过一个排气孔之后,才能够继续添加排气孔
        # if (len(sprue_info_save_cur) == 0):
        #     bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
        #     if (name == "右耳"):
        #         is_sprueAdd_modal_start = False
        #     elif (name == "左耳"):
        #         is_sprueAdd_modal_startL = False
        #     return {'FINISHED'}
        # if(sprue_index_cur == len(sprue_info_save_cur) - 1):
        #     #添加排气孔
        #     addSprue()
        #     # 将Plane激活并选中
        #     name = bpy.context.scene.leftWindowObj
        #     planename = name + "Plane"
        #     plane_obj = bpy.data.objects.get(planename)
        #     cur_obj = bpy.data.objects.get(name)
        #     bpy.ops.object.select_all(action='DESELECT')
        #     plane_obj.select_set(True)
        #     bpy.context.view_layer.objects.active = plane_obj
        #     #将排气孔位置设置为上一个排气孔的位置
        #     sprueInfo = sprue_info_save_cur[len(sprue_info_save_cur) - 1]
        #     if name == '右耳':
        #         sprue_index = sprue_index + 1
        #         print("添加排气孔后:", sprue_index)
        #     elif name == '左耳':
        #         sprue_indexL = sprue_indexL + 1
        #         print("添加排气孔后:", sprue_indexL)
        #     l_x = sprueInfo.l_x
        #     l_y = sprueInfo.l_y
        #     l_z = sprueInfo.l_z
        #     r_x = sprueInfo.r_x
        #     r_y = sprueInfo.r_y
        #     r_z = sprueInfo.r_z
        #     offset = sprueInfo.offset
        #     plane_obj.location[0] = l_x
        #     plane_obj.location[1] = l_y
        #     plane_obj.location[2] = l_z
        #     plane_obj.rotation_euler[0] = r_x
        #     plane_obj.rotation_euler[1] = r_y
        #     plane_obj.rotation_euler[2] = r_z
        #     if name == '右耳':
        #         bpy.context.scene.paiQiKongOffset = offset
        #     elif name == '左耳':
        #         bpy.context.scene.paiQiKongOffsetL = offset
        #     #设置旋转中心
        #     bpy.ops.object.select_all(action='DESELECT')
        #     cur_obj.select_set(True)
        #     bpy.context.view_layer.objects.active = cur_obj
        #
        #     if bpy.context.scene.var != 87:
        #         bpy.context.scene.var = 87
        #         context.window_manager.modal_handler_add(self)
        #         print("sprueadd_modal_invoke")
        #     return {'RUNNING_MODAL'}

    def execute(self, context):
        global is_sprueAdd_modal_start
        global is_sprueAdd_modal_startL
        global sprue_index
        global sprue_indexL
        global sprue_info_save
        global sprue_info_saveL
        name = bpy.context.scene.leftWindowObj
        sprue_index_cur = None
        sprue_info_save_cur = None
        if name == '右耳':
            sprue_index_cur = sprue_index
            sprue_info_save_cur = sprue_info_save
            # is_sprueAdd_modal_start = True
        elif name == '左耳':
            sprue_index_cur = sprue_indexL
            sprue_info_save_cur = sprue_info_saveL
            # is_sprueAdd_modal_startL = True

        # 将可能存在的排气孔先提交
        sprueSubmit()
        # 双击添加过一个排气孔之后,才能够继续添加排气孔
        if (len(sprue_info_save_cur) == 0):
            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
            if (name == "右耳"):
                is_sprueAdd_modal_start = False
            elif (name == "左耳"):
                is_sprueAdd_modal_startL = False
            return {'FINISHED'}
        if (sprue_index_cur == len(sprue_info_save_cur) - 1):
            # 添加排气孔
            addSprue()
            # 将Plane激活并选中
            name = bpy.context.scene.leftWindowObj
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            cur_obj = bpy.data.objects.get(name)
            bpy.ops.object.select_all(action='DESELECT')
            plane_obj.select_set(True)
            bpy.context.view_layer.objects.active = plane_obj
            # 将排气孔位置设置为上一个排气孔的位置
            sprueInfo = sprue_info_save_cur[len(sprue_info_save_cur) - 1]
            if name == '右耳':
                sprue_index = sprue_index + 1
                print("添加排气孔后:", sprue_index)
            elif name == '左耳':
                sprue_indexL = sprue_indexL + 1
                print("添加排气孔后:", sprue_indexL)
            l_x = sprueInfo.l_x
            l_y = sprueInfo.l_y
            l_z = sprueInfo.l_z
            r_x = sprueInfo.r_x
            r_y = sprueInfo.r_y
            r_z = sprueInfo.r_z
            offset = sprueInfo.offset
            plane_obj.location[0] = l_x
            plane_obj.location[1] = l_y
            plane_obj.location[2] = l_z
            plane_obj.rotation_euler[0] = r_x
            plane_obj.rotation_euler[1] = r_y
            plane_obj.rotation_euler[2] = r_z
            if name == '右耳':
                bpy.context.scene.paiQiKongOffset = offset
            elif name == '左耳':
                bpy.context.scene.paiQiKongOffsetL = offset
            # 设置旋转中心
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            if context.scene.var != 87:
                bpy.ops.object.sprueswitch('INVOKE_DEFAULT')

    # def modal(self, context, event):
    #     global is_on_rotate
    #     global is_on_rotateL
    #     global is_sprueAdd_modal_start
    #     global is_sprueAdd_modal_startL
    #     name = bpy.context.scene.leftWindowObj
    #     is_on_rotate_cur = False
    #     if (name == '右耳'):
    #         is_on_rotate_cur = is_on_rotate
    #     elif (name == '左耳'):
    #         is_on_rotate_cur = is_on_rotateL
    #     sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    #     sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    #     sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    #     sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    #     sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    #     sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    #     planename = name + "Plane"
    #     plane_obj = bpy.data.objects.get(planename)
    #     cur_obj_name = name
    #     cur_obj = bpy.data.objects.get(cur_obj_name)
    #     if bpy.context.screen.areas[0].spaces.active.context == 'CONSTRAINT':
    #         if (bpy.context.scene.var == 87):
    #             # 在数组中更新附件的信息
    #             updateInfo()
    #             if(not is_on_rotate_cur):
    #                 if(sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
    #                         # 调用sprue的鼠标行为
    #                         yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(yellow_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(yellow_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #                     elif ((not is_mouse_on_object(context, event)) and (is_changed_sprue(context, event) or is_changed(context, event))):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #             elif(is_on_rotate_cur):
    #                 if (sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
    #                             is_changed_sphere(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用sprue的三维旋转鼠标行为
    #                         yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(yellow_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(yellow_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #                     elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #             return {'PASS_THROUGH'}
    #         else:
    #             if (name == "右耳"):
    #                 is_sprueAdd_modal_start = False
    #             elif (name == "左耳"):
    #                 is_sprueAdd_modal_startL = False
    #             print("sprueadd_modal_finished")
    #             return {'FINISHED'}
    #
    #     else:
    #         if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
    #             print("sprueadd_modal_finished")
    #             if (name == "右耳"):
    #                 is_sprueAdd_modal_start = False
    #             elif (name == "左耳"):
    #                 is_sprueAdd_modal_startL = False
    #             set_switch_time(None)
    #             now_context = bpy.context.screen.areas[0].spaces.active.context
    #             if not check_modals_running(bpy.context.scene.var, now_context):
    #                 bpy.context.scene.var = 0
    #             return {'FINISHED'}
    #         return {'PASS_THROUGH'}


class SprueInitialAdd(bpy.types.Operator):
    bl_idname = "object.sprueinitialadd"
    bl_label = "进入附件模块初始化双击添加排气孔"

    def invoke(self, context, event):
        self.add_spure(context, event)
        return {'FINISHED'}

        # # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        # bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        # global sprue_index
        # global sprue_indexL
        #
        # #添加排气孔
        # addSprue()
        # # 将Plane激活并选中
        # name = bpy.context.scene.leftWindowObj
        # planename = name + "Plane"
        # plane_obj = bpy.data.objects.get(planename)
        # cur_obj = bpy.data.objects.get(name)
        # bpy.ops.object.select_all(action='DESELECT')
        # plane_obj.select_set(True)
        # bpy.context.view_layer.objects.active = plane_obj
        # #将添加的排气孔位置设置未双击的位置
        # co, normal = cal_co(context, event)
        # if (co != -1):
        #     sprue_fit_rotate(normal, co)
        # # 添加完最初的一个附件之后,将指针置为0
        # if (name == '右耳'):
        #     sprue_index = 0
        #     print("初始化添加后的指针:", sprue_index)
        # elif (name == '左耳'):
        #     sprue_indexL = 0
        #     print("初始化添加后的指针:", sprue_indexL)
        # #设置旋转中心
        # bpy.ops.object.select_all(action='DESELECT')
        # cur_obj.select_set(True)
        # bpy.context.view_layer.objects.active = cur_obj
        #
        # if bpy.context.scene.var != 88:
        #     bpy.context.scene.var = 88
        #     context.window_manager.modal_handler_add(self)
        #     print("sprueinitialadd_modal_initial")
        # return {'RUNNING_MODAL'}

    def add_spure(self, context, event):
        global sprue_index
        global sprue_indexL

        # 添加排气孔
        addSprue()
        # 将Plane激活并选中
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        # 将添加的排气孔位置设置未双击的位置
        co, normal = cal_co(context, event)
        if (co != -1):
            sprue_fit_rotate(normal, co)
        # 添加完最初的一个附件之后,将指针置为0
        if (name == '右耳'):
            sprue_index = 0
            print("初始化添加后的指针:", sprue_index)
        elif (name == '左耳'):
            sprue_indexL = 0
            print("初始化添加后的指针:", sprue_indexL)
        # 设置旋转中心
        bpy.ops.object.select_all(action='DESELECT')
        cur_obj.select_set(True)
        bpy.context.view_layer.objects.active = cur_obj
        bpy.ops.object.sprueswitch('INVOKE_DEFAULT')

    # def modal(self, context, event):
    #     global is_on_rotate
    #     global is_on_rotateL
    #     name = bpy.context.scene.leftWindowObj
    #     is_on_rotate_cur = False
    #     if (name == '右耳'):
    #         is_on_rotate_cur = is_on_rotate
    #     elif (name == '左耳'):
    #         is_on_rotate_cur = is_on_rotateL
    #     sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
    #     sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
    #     sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
    #     sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
    #     sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
    #     sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
    #     planename = name + "Plane"
    #     plane_obj = bpy.data.objects.get(planename)
    #     cur_obj_name = name
    #     cur_obj = bpy.data.objects.get(cur_obj_name)
    #     if bpy.context.screen.areas[0].spaces.active.context == 'CONSTRAINT':
    #         if (bpy.context.scene.var == 88):
    #             # 在数组中更新附件的信息
    #             updateInfo()
    #             if(not is_on_rotate_cur):
    #                 if(sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
    #                         # 调用sprue的鼠标行为
    #                         yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(yellow_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(yellow_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #                     elif ((not is_mouse_on_object(context, event)) and (is_changed_sprue(context, event) or is_changed(context, event))):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #             elif(is_on_rotate_cur):
    #                 if (sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
    #                     if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
    #                             is_changed_sphere(context, event) or is_changed(context, event))):
    #                         # 公共鼠标行为加双击移动附件位置
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                     elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用sprue的三维旋转鼠标行为
    #                         yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(yellow_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(yellow_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(yellow_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    #                         plane_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = plane_obj
    #                         cur_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #                     elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
    #                         # 调用公共鼠标行为
    #                         red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
    #                         # sprue_inner_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inner_obj
    #                         sprue_inner_obj.data.materials.clear()
    #                         sprue_inner_obj.data.materials.append(red_material)
    #                         # sprue_outer_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_outer_obj
    #                         sprue_outer_obj.data.materials.clear()
    #                         sprue_outer_obj.data.materials.append(red_material)
    #                         # sprue_inside_obj.select_set(True)
    #                         # bpy.context.view_layer.objects.active = sprue_inside_obj
    #                         sprue_inside_obj.data.materials.clear()
    #                         sprue_inside_obj.data.materials.append(red_material)
    #                         bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    #                         cur_obj.select_set(True)
    #                         bpy.context.view_layer.objects.active = cur_obj
    #                         plane_obj.select_set(False)
    #                         sprue_inner_obj.select_set(False)
    #                         sprue_outer_obj.select_set(False)
    #                         sprue_inside_obj.select_set(False)
    #             return {'PASS_THROUGH'}
    #         else:
    #             print("sprueinitialadd_modal_finished")
    #             return {'FINISHED'}
    #
    #     else:
    #         if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
    #             print("sprueinitialadd_modal_finished")
    #             set_switch_time(None)
    #             now_context = bpy.context.screen.areas[0].spaces.active.context
    #             if not check_modals_running(bpy.context.scene.var, now_context):
    #                 bpy.context.scene.var = 0
    #             return {'FINISHED'}
    #         return {'PASS_THROUGH'}


class SprueSwitch(bpy.types.Operator):
    bl_idname = "object.sprueswitch"
    bl_label = "排气孔鼠标行为"

    def invoke(self, context, event):
        global is_sprueAdd_modal_start, is_sprueAdd_modal_startL
        bpy.context.scene.var = 87
        # if not is_sprueAdd_modal_start and not is_sprueAdd_modal_startL:
        #     name = bpy.context.scene.leftWindowObj
        #     if name == '右耳':
        #         is_sprueAdd_modal_start = True
        #     elif name == '左耳':
        #         is_sprueAdd_modal_startL = True
        #     context.window_manager.modal_handler_add(self)
        #     print("sprueswitch_modal_invoke")
        if not is_sprueAdd_modal_start:
            is_sprueAdd_modal_start = True
            context.window_manager.modal_handler_add(self)
            print("sprueswitch_modal_invoke")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        override1 = getOverride()
        area = override1['area']

        global is_on_rotate
        global is_on_rotateL
        global is_sprueAdd_modal_start, is_sprueAdd_modal_startL
        name = bpy.context.scene.leftWindowObj
        is_on_rotate_cur = False
        if (name == '右耳'):
            is_on_rotate_cur = is_on_rotate
        elif (name == '左耳'):
            is_on_rotate_cur = is_on_rotateL
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        cur_obj_name = name
        cur_obj = bpy.data.objects.get(cur_obj_name)
        if bpy.context.screen.areas[0].spaces.active.context == 'CONSTRAINT':
            if get_mirror_context():
                print('sprueswitch_modal_finished')
                is_sprueAdd_modal_start = False
                set_mirror_context(False)
                return {'FINISHED'}
            if (event.mouse_x < area.width and area.y < event.mouse_y < area.y + area.height and bpy.context.scene.var == 87):
                if event.type == 'WHEELUPMOUSE':
                    if name == '右耳':
                        bpy.context.scene.paiQiKongOffset += 0.05
                    else:
                        bpy.context.scene.paiQiKongOffsetL += 0.05
                    return {'RUNNING_MODAL'}
                elif event.type == 'WHEELDOWNMOUSE':
                    if name == '右耳':
                        bpy.context.scene.paiQiKongOffset -= 0.05
                    else:
                        bpy.context.scene.paiQiKongOffsetL -= 0.05
                    return {'RUNNING_MODAL'}

                # 在数组中更新附件的信息
                updateInfo()
                if(not is_on_rotate_cur):
                    if(sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_sprue(context, event) and (is_changed_sprue(context, event) or is_changed(context, event))):
                            # 调用sprue的鼠标行为
                            yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(yellow_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(yellow_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                        elif ((not is_mouse_on_object(context, event)) and (is_changed_sprue(context, event) or is_changed(context, event))):
                            # 调用公共鼠标行为
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                elif(is_on_rotate_cur):
                    if (sprue_inner_obj != None and sprue_outer_obj != None and sprue_inside_obj != None):
                        if (is_mouse_on_object(context, event) and not is_mouse_on_sphere(context, event) and (
                                is_changed_sphere(context, event) or is_changed(context, event))):
                            # 公共鼠标行为加双击移动附件位置
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_mouse")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                        elif (is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用sprue的三维旋转鼠标行为
                            yellow_material = newColor("SprueYellow", 1, 1, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(yellow_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(yellow_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(yellow_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
                            plane_obj.select_set(True)
                            bpy.context.view_layer.objects.active = plane_obj
                            cur_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                        elif (not is_mouse_on_sphere(context, event) and is_changed_sphere(context, event)):
                            # 调用公共鼠标行为
                            red_material = newColor("SprueRed", 1, 0, 0, 0, 1)
                            # sprue_inner_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inner_obj
                            sprue_inner_obj.data.materials.clear()
                            sprue_inner_obj.data.materials.append(red_material)
                            # sprue_outer_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_outer_obj
                            sprue_outer_obj.data.materials.clear()
                            sprue_outer_obj.data.materials.append(red_material)
                            # sprue_inside_obj.select_set(True)
                            # bpy.context.view_layer.objects.active = sprue_inside_obj
                            sprue_inside_obj.data.materials.clear()
                            sprue_inside_obj.data.materials.append(red_material)
                            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                            cur_obj.select_set(True)
                            bpy.context.view_layer.objects.active = cur_obj
                            plane_obj.select_set(False)
                            sprue_inner_obj.select_set(False)
                            sprue_outer_obj.select_set(False)
                            sprue_inside_obj.select_set(False)
                return {'PASS_THROUGH'}

            elif bpy.context.scene.var != 87 and bpy.context.scene.var in get_process_var_list("排气孔"):
                print("sprueswitch_modal_finished")
                is_sprueAdd_modal_start = False
                # if (name == "右耳"):
                #     is_sprueAdd_modal_start = False
                # elif (name == "左耳"):
                #     is_sprueAdd_modal_startL = False
                return {'FINISHED'}

            else:
                return {'PASS_THROUGH'}

        else:
            if get_switch_time() != None and time.time() - get_switch_time() > 0.3 and get_switch_flag():
                print("sprueswitch_modal_finished")
                is_sprueAdd_modal_start = False
                # if (name == "右耳"):
                #     is_sprueAdd_modal_start = False
                # elif (name == "左耳"):
                #     is_sprueAdd_modal_startL = False
                set_switch_time(None)
                now_context = bpy.context.screen.areas[0].spaces.active.context
                if not check_modals_running(bpy.context.scene.var, now_context):
                    bpy.context.scene.var = 0
                return {'FINISHED'}
            return {'PASS_THROUGH'}


class SprueSubmit(bpy.types.Operator):
    bl_idname = "object.spruesubmit"
    bl_label = "排气孔提交"

    def invoke(self, context, event):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        if (name == "右耳"):
            is_on_rotate = False
        elif (name == "左耳"):
            is_on_rotateL = False

        bpy.context.scene.var = 89
        # 调用公共鼠标行为按钮,避免自定义按钮因多次移动鼠标触发多次自定义的Operator
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        # sprueSaveInfo()
        sprueSubmit()
        return {'FINISHED'}

class SprueRotate(bpy.types.Operator):
    bl_idname = "object.spruerotate"
    bl_label = "鼠标的三维旋转状态"

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global is_on_rotate
        global is_on_rotateL
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        # spherename = name + "SprueSphere"
        # sphere_obj = bpy.data.objects.get(spherename)
        # if (plane_obj != None and sphere_obj != None):
        if (plane_obj != None):
            if(name == '右耳'):
                is_on_rotate = not is_on_rotate
                # if(is_on_rotate == True):
                #     sphere_obj.select_set(True)
                # else:
                #     sphere_obj.select_set(False)
            elif(name == '左耳'):
                is_on_rotateL = not is_on_rotateL
                # if (is_on_rotateL == True):
                #     sphere_obj.select_set(True)
                # else:
                #     sphere_obj.select_set(False)
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}

class SprueDoubleClick(bpy.types.Operator):
    bl_idname = "object.spruedoubleclick"
    bl_label = "双击改变排气管位置"

    def invoke(self, context, event):
        # 将Plane激活并选中,位置设置为双击的位置
        name = bpy.context.scene.leftWindowObj
        planename = name + "Plane"
        plane_obj = bpy.data.objects.get(planename)
        plane_obj.select_set(True)
        bpy.context.view_layer.objects.active = plane_obj
        co, normal = cal_co(context, event)
        if (co != -1):
            sprue_fit_rotate(normal,co)
            # plane_obj.location = co
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}


class SprueMirror(bpy.types.Operator):
    bl_idname = 'object.spruemirror'
    bl_label = '排气孔镜像'

    def invoke(self, context, event):
        print('进入镜像了')
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global sprue_info_saveL, sprue_info_save
        global sprue_indexL, sprue_index

        left_obj = bpy.data.objects.get(context.scene.leftWindowObj)
        right_obj = bpy.data.objects.get(context.scene.rightWindowObj)

        # 只操作一个耳朵时，不执行镜像
        if left_obj == None or right_obj == None:
            return {'FINISHED'}

        tar_obj_name = bpy.context.scene.leftWindowObj
        tar_obj = bpy.data.objects[tar_obj_name]

        workspace = context.window.workspace.name

        if tar_obj_name == '左耳':
            ori_sprue_info = sprue_info_save
            tar_sprue_info = sprue_info_saveL
        else:
            ori_sprue_info = sprue_info_saveL
            tar_sprue_info = sprue_info_save

        # 只在双窗口下执行镜像
        if len(ori_sprue_info) != 0 and len(tar_sprue_info) == 0:
            tar_info = ori_sprue_info[0]
            offset, l_x, l_y, l_z, r_x, r_y, r_z = tar_info.offset, tar_info.l_x, -tar_info.l_y, tar_info.l_z, tar_info.r_x, tar_info.r_y, tar_info.r_z
            # 将附件数组指针置为末尾
            if tar_obj_name == '左耳':
                sprue_indexL = -1
            else:
                sprue_index = -1
            bpy.ops.object.sprueinitialadd('INVOKE_DEFAULT')
            # 获取添加后的Handle,并根据参数设置调整offset
            planename = tar_obj_name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            if plane_obj is not None:
                plane_obj.location[0] = l_x
                plane_obj.location[1] = l_y
                plane_obj.location[2] = l_z
                plane_obj.rotation_euler[0] = r_x
                plane_obj.rotation_euler[1] = r_y
                plane_obj.rotation_euler[2] = r_z

                bm = bmesh.new()
                bm.from_mesh(tar_obj.data)

                closest_vertex = None
                min_distance = float('inf')
                target_point = mathutils.Vector((l_x,l_y,l_z))

                for vert in bm.verts:
                    # 将顶点坐标转换到世界坐标系
                    vertex_world = tar_obj.matrix_world @ vert.co
                    distance = (vertex_world - target_point).length
                    if distance < min_distance:
                        min_distance = distance
                        closest_vertex = vert
                closest_vertex_world = tar_obj.matrix_world @ closest_vertex.co
                closest_vertex_normal = tar_obj.matrix_world.to_3x3() @ closest_vertex.normal

                sprue_fit_rotate(closest_vertex_normal, closest_vertex_world)
                if tar_obj_name == '左耳':
                    bpy.context.scene.paiQiKongOffsetL = offset
                elif tar_obj_name == '右耳':
                    bpy.context.scene.paiQiKongOffset = offset
                bm.free()

        if context.scene.var != 87:
            bpy.ops.object.sprueswitch('INVOKE_DEFAULT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")




class MyTool_Sprue1(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_reset"
    bl_label = "排气孔重置"
    bl_description = (
        "重置模型,清除模型上的所有排气孔"
    )
    bl_icon = "brush.sculpt.clay"
    bl_widget = None
    bl_keymap = (
        ("object.spruereset", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_add"
    bl_label = "排气孔添加"
    bl_description = (
        "在模型上上一个排气孔的位置处添加一个排气孔"
    )
    bl_icon = "brush.sculpt.boundary"
    bl_widget = None
    bl_keymap = (
        ("object.sprueadd", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.sprueaddinvoke", {"type": 'MOUSEMOVE', "value": 'ANY'}, None),
        # ("object.sprueadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        # ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        # ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


class MyTool_Sprue3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_submit"
    bl_label = "排气孔提交"
    bl_description = (
        "对于模型上所有排气孔提交实体化"
    )
    bl_icon = "brush.sculpt.blob"
    bl_widget = None
    bl_keymap = (
        ("object.spruesubmit", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Sprue_Rotate(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_rotate"
    bl_label = "排气孔旋转"
    bl_description = (
        "添加排气孔后,调用排气孔三维旋转鼠标行为"
    )
    bl_icon = "brush.paint_texture.draw"
    bl_widget = None
    bl_keymap = (
        ("object.spruerotate", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Sprue_Mirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_mirror"
    bl_label = "排气孔镜像"
    bl_description = (
        "点击镜像排气孔"
    )
    bl_icon = "brush.paint_texture.fill"
    bl_widget = None
    bl_keymap = (
        ("object.spruemirror", {"type": 'MOUSEMOVE', "value": 'ANY'},
         {}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_Sprue_Mouse(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_mouse"
    bl_label = "双击改变排气管位置"
    bl_description = (
        "添加排气管后,在模型上双击,附件移动到双击位置"
    )
    bl_icon = "brush.paint_texture.mask"
    bl_widget = None
    bl_keymap = (
        ("object.spruedoubleclick", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("view3d.view_roll", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None)
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool_SprueInitial(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.sprue_initial"
    bl_label = "排气孔添加初始化"
    bl_description = (
        "刚进入排气孔模块的时,在模型上双击位置处添加一个排气孔"
    )
    bl_icon = "brush.sculpt.snake_hook"
    bl_widget = None
    bl_keymap = (
        ("object.sprueinitialadd", {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK'}, None),
        ("view3d.rotate", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("view3d.move", {"type": 'RIGHTMOUSE', "value": 'PRESS'}, None),
        ("view3d.dolly", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        pass


# 注册类
_classes = [
    SprueReset,
    SprueBackForwardAdd,
    SprueAddInvoke,
    SprueAdd,
    SprueInitialAdd,
    SprueSubmit,
    SprueDoubleClick,
    SprueRotate,
    SprueMirror,
    SprueSwitch
]


def register_sprue_tools():
    bpy.utils.register_tool(MyTool_Sprue1, separator=True, group=False)
    bpy.utils.register_tool(MyTool_Sprue2, separator=True, group=False, after={MyTool_Sprue1.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue3, separator=True, group=False, after={MyTool_Sprue2.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Rotate, separator=True, group=False, after={MyTool_Sprue3.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Mirror, separator=True, group=False, after={MyTool_Sprue_Rotate.bl_idname})
    bpy.utils.register_tool(MyTool_Sprue_Mouse, separator=True, group=False, after={MyTool_Sprue_Mirror.bl_idname})
    bpy.utils.register_tool(MyTool_SprueInitial, separator=True, group=False, after={MyTool_Sprue_Mouse.bl_idname})


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # bpy.utils.register_tool(MyTool_Sprue1, separator=True, group=False)
    # bpy.utils.register_tool(MyTool_Sprue2, separator=True, group=False, after={MyTool_Sprue1.bl_idname})
    # bpy.utils.register_tool(MyTool_Sprue3, separator=True, group=False, after={MyTool_Sprue2.bl_idname})
    # bpy.utils.register_tool(MyTool_Sprue_Rotate, separator=True, group=False, after={MyTool_Sprue3.bl_idname})
    # bpy.utils.register_tool(MyTool_Sprue_Mirror, separator=True, group=False, after={MyTool_Sprue_Rotate.bl_idname})
    # bpy.utils.register_tool(MyTool_Sprue_Mouse, separator=True, group=False, after={MyTool_Sprue_Mirror.bl_idname})
    # bpy.utils.register_tool(MyTool_SprueInitial, separator=True, group=False, after={MyTool_Sprue_Mouse.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool_Sprue1)
    bpy.utils.unregister_tool(MyTool_Sprue2)
    bpy.utils.unregister_tool(MyTool_Sprue3)
    bpy.utils.unregister_tool(MyTool_Sprue_Rotate)
    bpy.utils.unregister_tool(MyTool_Sprue_Mirror)
    bpy.utils.unregister_tool(MyTool_Sprue_Mouse)
    bpy.utils.unregister_tool(MyTool_SprueInitial)
