import bpy
import blf
import mathutils
import bpy_extras
from bpy_extras import view3d_utils
import bmesh

font_info = {
    "font_id": 0,
    "handler": None,
}


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
    blf.position(font_id, 1300, 80, 0)
    blf.size(font_id, 50)
    rounded_number = round(thickness, 2)
    blf.draw(font_id, str(rounded_number)+"mm")

# 获取区域和空间，鼠标行为切换相关


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


# 判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    active_obj = context.active_object

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
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object


# 判断鼠标状态是否发生改变
def is_changed(context, event):
    active_obj = context.active_object

    curr_on_object = False             # 当前鼠标是否在物体上,初始化为False
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
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                curr_on_object = True                     # 如果发生交叉，将变量设为True
    if (curr_on_object != prev_on_object):
        prev_on_object = curr_on_object
        return True
    else:
        return False

# 判断鼠标在哪个物体上


def is_mouse_on_which_object(context, event):
    sphere1 = bpy.data.objects["mysphere1"]
    sphere2 = bpy.data.objects["mysphere2"]
    sphere3 = bpy.data.objects["mysphere3"]
    sphere4 = bpy.data.objects["mysphere4"]

    is_on_object = 5  # 初始化变量

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
    mwi = sphere1.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if sphere1.type == 'MESH':
        if (sphere1.mode == 'OBJECT'):
            mesh = sphere1.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = 1  
                return is_on_object
    
    mwi2 = sphere2.matrix_world.inverted()
    mwi_start2 = mwi2 @ start
    mwi_end2 = mwi2 @ end
    mwi_dir2 = mwi_end2 - mwi_start2

    if sphere2.type == 'MESH':
        if (sphere2.mode == 'OBJECT'):
            mesh = sphere2.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start2, mwi_dir2, 2000.0)

            if fidx is not None:
                is_on_object = 2
                return is_on_object

    mwi3 = sphere3.matrix_world.inverted()
    mwi_start3 = mwi3 @ start
    mwi_end3 = mwi3 @ end
    mwi_dir3 = mwi_end3 - mwi_start3

    if sphere3.type == 'MESH':
        if (sphere3.mode == 'OBJECT'):
            mesh = sphere3.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start3, mwi_dir3, 2000.0)

            if fidx is not None:
                is_on_object = 3
                return is_on_object
            
    mwi4 = sphere4.matrix_world.inverted()
    mwi_start4 = mwi4 @ start
    mwi_end4 = mwi4 @ end
    mwi_dir4 = mwi_end4 - mwi_start4

    if sphere4.type == 'MESH':
        if (sphere4.mode == 'OBJECT'):
            mesh = sphere4.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start4, mwi_dir4, 2000.0)

            if fidx is not None:
                is_on_object = 4
                return is_on_object

    return is_on_object
