import bpy
import bmesh
import blf
import math
import os
import mathutils
from tool import newColor, moveToLeft, moveToRight
from utils.utils import utils_get_order_border_vert, utils_draw_curve
from .create_mould.soft_eardrum.thickness_and_fill import get_cut_plane, plane_cut, delete_useless_part

import datetime
import io
from contextlib import redirect_stdout

datetime.datetime.now()
stdout = io.StringIO()
with redirect_stdout(stdout):
    pass
del stdout

# 记录左右窗口不同的切换逻辑
# prev_properties_context_right = "RENDER"  # 保存Properties窗口切换时上次Properties窗口中的上下文,记录由哪个模式切换而来
# prev_properties_context_left = "RENDER"

# is_right_changed = (prev_properties_context_right != current_tab) and context.scene.leftWindowObj == "右耳"
# is_left_changed = (prev_properties_context_left != current_tab) and context.scene.leftWindowObj == "左耳"
# if (is_right_changed or is_left_changed):

# if is_right_changed:
#     print(f'Previous RTab: {prev_properties_context_right}')
#     print(f'Current Tab: {current_tab}')
# elif is_left_changed:
#     print(f'Previous LTab: {prev_properties_context_left}')
#     print(f'Current Tab: {current_tab}')

# if context.scene.leftWindowObj == "右耳":
#     prev_properties_context_right = current_tab
# else:
#     prev_properties_context_left = current_tab

# if (workspace != prev_workspace):
#     if context.scene.leftWindowObj == "右耳":
#         bpy.context.screen.areas[1].spaces.active.context = prev_properties_context_right
#     else:
#         bpy.context.screen.areas[1].spaces.active.context = prev_properties_context_left


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

# col.operator("huier.switch", text = "切换窗口")


def getOverride():
    # 获取所有的窗口
    override = []
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        # 在所有的窗口中找到3D视图
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                # print('宽度',area.width)
                if (area.spaces.active.use_local_collections == False):
                    # 设置local collection
                    area.spaces.active.use_local_collections = True
                ride = {
                    'window': window,
                    'screen': screen,
                    'area': area,
                    'region': [region for region in area.regions if region.type == 'WINDOW'][0],
                }
                override.append(ride)

    return override[0], override[1]


def hide():
    override1, override2 = getOverride()
    with bpy.context.temp_override(**override2):
        bpy.ops.object.hide_collection(collection_index=2, extend=False)

    with bpy.context.temp_override(**override1):
        bpy.ops.object.hide_collection(collection_index=1, extend=False)


if __name__ == "__main__":
    hide()


def get_change_parameters():
    tar_obj = bpy.data.objects['右耳']
    ori_obj_R = bpy.data.objects['TemplateEarR']
    ori_obj_L = bpy.data.objects['TemplateEarL']

    # 获取模型最高点
    origin_highest_vert_index_R = get_highest_vert(ori_obj_R)
    origin_highest_vert_index_L = get_highest_vert(ori_obj_L)
    target_highest_vert_index = get_highest_vert(tar_obj)

    origin_highest_vert_R = ori_obj_R.data.vertices[origin_highest_vert_index_R].co @ ori_obj_R.matrix_world
    origin_highest_vert_L = ori_obj_L.data.vertices[origin_highest_vert_index_L].co @ ori_obj_R.matrix_world
    target_highest_vert = tar_obj.data.vertices[target_highest_vert_index].co @ tar_obj.matrix_world
    # 计算旋转角度
    angle_origin_R = calculate_angle(
        origin_highest_vert_R[0], origin_highest_vert_R[1])
    angle_origin_L = calculate_angle(
        origin_highest_vert_L[0], origin_highest_vert_L[1])
    angle_target = calculate_angle(
        target_highest_vert[0], target_highest_vert[1])
    rotate_angle_R = angle_target - angle_origin_R
    rotate_angle_L = angle_target - angle_origin_L

    return rotate_angle_R, rotate_angle_L


def get_highest_vert(obj):
    # 获取网格数据
    me = obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    return vert_order_by_z[0].index


def calculate_angle(x, y):
    # 弧度
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees


def rotate():
    # 获取场景中的选中对象
    obj_R = bpy.data.objects['TemplateEarR']
    obj_L = bpy.data.objects['TemplateEarL']
    rotate_angle_R, rotate_angle_L = get_change_parameters()
    # 假设选中对象存在
    if obj_R:
        # 定义旋转角度（以弧度为单位）
        rotate_angle_R = math.radians(rotate_angle_R)  # 将角度转换为弧度
        # 设置旋转角度
        obj_R.rotation_euler[2] += rotate_angle_R  # 在 Z 轴上添加旋转角度
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_R
        obj_R.select_set(True)
        bpy.ops.object.transform_apply(
            location=False, rotation=True, scale=False, isolate_users=True)

    if obj_L:
        rotate_angle_L = math.radians(rotate_angle_L)  # 将角度转换为弧度
        obj_L.rotation_euler[2] += rotate_angle_L  # 在 Z 轴上添加旋转角度
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_L
        obj_L.select_set(True)
        bpy.ops.object.transform_apply(
            location=False, rotation=True, scale=False, isolate_users=True)


def judge():
    files_dir = os.path.join(os.path.dirname(__file__))
    path_EarR = os.path.join(files_dir, "TemplateEarR.stl")
    path_EarL = os.path.join(files_dir, "TemplateEarL.stl")
    bpy.ops.wm.stl_import(filepath=path_EarR)
    bpy.ops.wm.stl_import(filepath=path_EarL)
    rotate()
    lowest_plane_border_T, _ = get_cut_border(0.25, '右耳')
    lowest_plane_border_R, _ = get_cut_border(0.25, 'TemplateEarR')
    lowest_plane_border_L, _ = get_cut_border(0.25, 'TemplateEarL')
    draw_cut_border_curve(get_order_border_vert(
        lowest_plane_border_T), 'TargetEar', 0.1)
    draw_cut_border_curve(get_order_border_vert(
        lowest_plane_border_R), 'RightEar', 0.1)
    draw_cut_border_curve(get_order_border_vert(
        lowest_plane_border_L), 'LeftEar', 0.1)
    # order_border_vert_T = get_order_border_vert(lowest_plane_border_T)
    # order_border_vert_R = get_order_border_vert(lowest_plane_border_R)
    # order_border_vert_L = get_order_border_vert(lowest_plane_border_L)
    # vertices_T = find_max_distance_vertex(order_border_vert_T)
    # vertices_R = find_max_distance_vertex(order_border_vert_R)
    # vertices_L = find_max_distance_vertex(order_border_vert_L)
    # print(vertices_T)
    # print(vertices_R)
    # print(vertices_L)


def find_max_distance_vertex(vertices):
    max_distance = 0
    max_distance_index = None

    # 遍历顶点坐标列表
    for i in range(len(vertices) - 1):
        # 计算相邻顶点之间的距离
        distance = math.dist(vertices[i], vertices[i+1])

        # 如果当前距离大于记录的最大距离，则更新最大距离及其对应的下标
        if distance > max_distance:
            max_distance = distance
            max_distance_index = i

    temp_distance = math.dist(vertices[0], vertices[len(vertices) - 1])
    if temp_distance > max_distance:
        max_distance = temp_distance
        max_distance_index = len(vertices) - 1

    return vertices[max_distance_index]


def get_plane_height(high_percent, name):
    # high_percent 0.25
    obj = bpy.data.objects[name]

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    vert_order_by_z = []
    for vert in bm.verts:
        vert_order_by_z.append(vert)
    # 按z坐标倒序排列
    vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
    highest_vert = vert_order_by_z[0]
    lowest_vert = vert_order_by_z[-1]
    origin_z_co = lowest_vert.co[2] + high_percent * \
        (highest_vert.co[2] - lowest_vert.co[2])

    return origin_z_co


def get_lowest_point(angle_degrees, z_co, count, origin_loc, origin_normal, name):
    # 在当前平面内找到距离z轴最近的点

    active_obj = bpy.data.objects[name]

    min_distance = origin_loc[0] ** 2 + origin_loc[1] ** 2
    lowest_point = origin_loc
    lowest_normal = origin_normal
    # 投射光线的方向
    direction = (math.cos(math.radians(angle_degrees)),
                 math.sin(math.radians(angle_degrees)), 0)
    h = z_co
    while h < z_co + 1:
        origin = (0, 0, h)
        for i in range(0, count):  # 找到当前高度h的第n次交点（初始点是第几次交点就和第几次交点比）
            hit, loc, normal, _ = active_obj.ray_cast(origin, direction)
            if hit:  # 如果有交点，去找下一个交点
                origin = (loc[0] + math.cos(math.radians(angle_degrees)) / 100,
                          loc[1] + math.sin(math.radians(angle_degrees)) / 100, loc[2])
                break
        if hit:
            distance = loc[0] ** 2 + loc[1] ** 2
            # 切片距离法
            if distance < min_distance:
                min_distance = distance
                lowest_point = (loc[0], loc[1], loc[2])
                lowest_normal = normal

        h = h + 0.2

    return lowest_point, lowest_normal


def get_cut_border(high_percent, name):
    # 获取活动对象
    active_obj = bpy.data.objects[name]

    # 确保活动对象的类型是网格
    if active_obj.type == 'MESH':
        # origin z坐标后续根据比例来设置
        origin_z_co = get_plane_height(high_percent, name)
        origin = (0, 0, origin_z_co)
        # 存放最凹平面边界点
        lowest_plane_border = []
        lowest_plane_normal = []
        angle_degrees = 0
        while angle_degrees < 360:
            direction = (
                math.cos(math.radians(angle_degrees)), math.sin(math.radians(angle_degrees)), 0)  # 举例：从起点向 x 轴正方向投射光线
            hit, loc, normal, _ = active_obj.ray_cast(origin, direction)

            if hit:
                # 相交后，继续向外走，找到最外侧的交点
                # 第一次交点
                count = 1
                while hit:
                    lowest_point,  lowest_normal = get_lowest_point(angle_degrees, origin_z_co, count,
                                                                    (loc[0], loc[1],
                                                                     loc[2]),
                                                                    (normal[0], normal[1], normal[2]), name)
                    lowest_plane_border.append(lowest_point)
                    lowest_plane_normal.append(lowest_normal)
                    # 去找下一个交点
                    # 注意 这里起始位置要往前走一点，否则一直会交在同一个点
                    hit, loc, normal, _ = active_obj.ray_cast((loc[0] + math.cos(
                        math.radians(angle_degrees)) / 100, loc[1] + math.sin(
                        math.radians(angle_degrees)) / 100, loc[2]), direction)
                    # 相交次数+1
                    count = count + 1
            angle_degrees = angle_degrees + 0.5

    return lowest_plane_border, lowest_plane_normal


def get_order_border_vert(selected_verts):
    size = len(selected_verts)
    finish = False
    # 尝试使用距离最近的点
    order_border_vert = []
    now_vert = selected_verts[0]
    unprocessed_vertex = selected_verts  # 未处理顶点
    while len(unprocessed_vertex) > 1 and not finish:
        order_border_vert.append(now_vert)
        unprocessed_vertex.remove(now_vert)

        min_distance = math.inf
        now_vert_co = now_vert

        # 2024/1/2 z轴落差过大会导致问题，这里只考虑xy坐标
        for vert in unprocessed_vertex:
            distance = math.sqrt(
                (vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert
        if min_distance > 3 and len(unprocessed_vertex) < 0.1 * size:
            finish = True
    return order_border_vert


def draw_cut_border_curve(order_border_co, name, depth):
    new_node_list = list()
    for i in range(len(order_border_co)):
        if i % 2 == 1:  # 最后一个点连上去有点奇怪 所以换个方式
            new_node_list.append(order_border_co[i])
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(new_node_list) - 1)
    spline.use_cyclic_u = True
    for i, point in enumerate(new_node_list):
        spline.points[i].co = (point[0], point[1], point[2], 1)

    bpy.context.active_object.data.bevel_depth = depth
    newColor('blue', 0, 0, 1, 1, 1)
    bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
    bpy.context.view_layer.update()


if __name__ == "__main__":
    judge()


# 获取模型的y坐标范围
def getModely(name):
    # 获取目标物体的编辑模式网格
    obj_main = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj_main
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj_main.data)

    # 初始化最大距离为负无穷大
    y_max = float('-inf')
    y_min = float('inf')

    # 遍历的每个顶点并计算距离
    for vertex in bm.verts:
        y_max = max(y_max, vertex.co.z)
        y_min = min(y_min, vertex.co.z)

    # 切换回对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

    return y_max, y_min


def cal_number(percent, name):
    y_max, y_min = getModely(name)
    initY = y_min + (y_max - y_min) * percent
    bm = bmesh.new()
    objdata = bpy.data.objects[name].data
    bm.from_mesh(objdata)
    selected_verts = [v.co for v in bm.verts if round(v.co.y, 2) < round(
        initY, 2) + 0.1 and round(v.co.y, 2) > round(initY, 2) - 0.1]
    return len(selected_verts)


def judge2():
    for i in range(1, 10):
        len_T = cal_number(i / 10, '右耳')
        len_R = cal_number(i / 10, 'TemplateEarR')
        len_L = cal_number(i / 10, 'TemplateEarL')
        print(len_T, len_R, len_L)


class MsgbusCallBack2(bpy.types.Operator):
    bl_idname = "object.msgbuscallback2"
    bl_label = "绘制文本"

    def invoke(self, context, event):
        print("绘制文本invoke")
        global is_msgbus_start2
        is_msgbus_start2 = True
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        self.draw_left()
        subscribe_to3 = (bpy.types.Space, "region") #先获得region再通过region注册
        bpy.msgbus.subscribe_rna(
            key=subscribe_to3,
            owner=object(),
            args=(1, 2, 3),
            notify=msgbus_callback3,
        )

    def draw_left(self):
        """Draw on the viewports"""
        # BLF drawing routine
        if bpy.context.window.workspace.name == '布局':
            override = getOverrideMain()
            region = override['region']
            if region.x == 0:
                PublicHandleClass.remove_handler()
                if bpy.context.scene.leftWindowObj == "右耳":
                    PublicHandleClass.add_handler(
                        draw_callback_Red, (None, region.width - 100, region.height - 100, "R"))
                elif bpy.context.scene.leftWindowObj == "左耳":
                    PublicHandleClass.add_handler(
                        draw_callback_Blue, (None, region.width - 100, region.height - 100, "L"))
                # blf.color(0, 0.0, 0.0, 0.0, 1.0)
                # blf.position(font_id, region.width - 100, region.height - 100, 0)
                # blf.size(font_id, 50)
                # blf.draw(font_id, text)
        elif bpy.context.window.workspace.name == '布局.001':
            override = getOverrideMain()
            region = override['region']
            # override2 = getOverrideMain2()
            # region2 = override2['region']
            if region.x == 0:
                PublicHandleClass.remove_handler()
                if bpy.context.scene.leftWindowObj == "右耳":
                    PublicHandleClass.add_handler(
                        draw_callback_Red, (None, region.width - 100, region.height - 100, "R"))
                elif bpy.context.scene.leftWindowObj == "左耳":
                    PublicHandleClass.add_handler(
                        draw_callback_Blue, (None, region.width - 100, region.height - 100, "L"))
            # if region2.x != 0:
            #     PublicHandleClass.remove_handler()
            #     PublicHandleClass.add_handler(draw_callback_Red, (None, region2.width - 100, region2.height - 100, "L"))


class MsgbusCallBack3(bpy.types.Operator):
    bl_idname = "object.msgbuscallback3"
    bl_label = "区域大小变化"

    def invoke(self, context, event):
        print("区域大小变化invoke")
        self.excute(context, event)
        return {'FINISHED'}

    def excute(self, context, event):
        override = getOverrideMain()
        region = override['region']
        if region.x == 0:
            PublicHandleClass.remove_handler()
            if bpy.context.scene.leftWindowObj == "右耳":
                PublicHandleClass.add_handler(
                    draw_callback_Red, (None, region.width - 100, region.height - 100, "R"))
            elif bpy.context.scene.leftWindowObj == "左耳":
                PublicHandleClass.add_handler(
                    draw_callback_Blue, (None, region.width - 100, region.height - 100, "L"))


font_info_public = {
    "font_id": 0,
    "handler": None,
}


def draw_callback_Red(self, x, y, text):
    """Draw on the viewports"""
    # BLF drawing routine
    font_id = font_info_public["font_id"]
    blf.color(font_id, 1.0, 0.0, 0.0, 1.0)
    blf.position(font_id, x, y, 0)
    blf.size(font_id, 50)
    blf.draw(font_id, text)


def draw_callback_Blue(self, x, y, text):
    """Draw on the viewports"""
    # BLF drawing routine
    font_id = font_info_public["font_id"]
    blf.color(font_id, 0.0, 0.0, 1.0, 1.0)
    blf.position(font_id, x, y, 0)
    blf.size(font_id, 50)
    blf.draw(font_id, text)


class PublicHandleClass:
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


def getOverrideMain():
    # change this to use the correct Area Type context you want to process in
    area_type = 'VIEW_3D'
    areas = [
        area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(
            f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override


def getOverrideMain2():
    # change this to use the correct Area Type context you want to process in
    area_type = 'VIEW_3D'
    areas = [
        area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(
            f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[1],
        'region': [region for region in areas[1].regions if region.type == 'WINDOW'][0],
    }

    return override


def msgbus_callback2(*args):
    global is_msgbus_start2
    if (not is_msgbus_start2):
        bpy.ops.object.msgbuscallback2('INVOKE_DEFAULT')


subscribe_to2 = (bpy.types.Object, "name")

bpy.msgbus.subscribe_rna(
    key=subscribe_to2,
    owner=object(),
    args=(1, 2, 3),
    notify=msgbus_callback2,
)


def msgbus_callback3(*args):
    bpy.ops.object.msgbuscallback3('INVOKE_DEFAULT')

def getOverride():
    area_type = 'PROPERTIES'  # change this to use the correct Area Type context you want to process in
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    return override

def getOverride2():
    area_type = 'VIEW_3D'  # change this to use the correct Area Type context you want to process in
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[1],
        'region': [region for region in areas[1].regions if region.type == 'WINDOW'][0],
    }

    return override

def getOverride3():
    area_type = 'VIEW_3D'  # change this to use the correct Area Type context you want to process in
    areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

    if len(areas) <= 0:
        raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

    override = {
        'window': bpy.context.window,
        'screen': bpy.context.window.screen,
        'area': areas[2],
        'region': [region for region in areas[2].regions if region.type == 'WINDOW'][0],
    }

    return override

class HUIER_OT_closearea(bpy.types.Operator):
    bl_idname = "obj.closearea"
    bl_label = "关闭区域"
    
    def execute(self, context):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.screen.area_close()
        
        return {'FINISHED'}

class HUIER_OT_addarea(bpy.types.Operator):
    bl_idname = "obj.addarea"
    bl_label = "新增区域"
    
    def execute(self, context):
        override = getOverride2()
        with bpy.context.temp_override(**override):
           bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.5, cursor=(0, 0))
        
        override = getOverride3()
        with bpy.context.temp_override(**override):
           bpy.context.area.ui_type = 'PROPERTIES'

        return {'FINISHED'}
    

# 在不同模式间切换时选择不同的材质
def change_mat_mould(type):
    #  type=0 RGB模式， type=1 顶点颜色模式
    mat = bpy.data.materials.get('Yellow')
    if mat:
        if type == 0:
            is_initial = False
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for node in nodes:
                if node.name == 'RGB':
                    is_initial = True
            if not is_initial:
               new_node = nodes.new(type="ShaderNodeRGB")
               new_node.outputs[0].default_value = (1.0, 0.319, 0.133, 1)
            for link in links:
                links.remove(link)
            links.new(nodes["RGB"].outputs[0], nodes["Principled BSDF"].inputs[0])
            links.new(nodes["Principled BSDF"].outputs[0], nodes["Material Output"].inputs[0])

        elif type == 1:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for link in links:
                links.remove(link)
            links.new(nodes["Color Attribute"].outputs[0], nodes["Principled BSDF"].inputs[0])
            links.new(nodes["Principled BSDF"].outputs[0], nodes["Material Output"].inputs[0])
            
if __name__ == "__main__":
    change_mat_mould(0)

def subdivide_after_boolean():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    bpy.ops.object.vertex_group_select()
    bm_compare = bmesh.from_edit_mesh(bpy.data.objects['右耳'].data)
    bm_compare_vert = [v for v in bm_compare.verts if v.select]


    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0, 0)})
    # bpy.ops.transform.edge_slide(value=-0.5)
    
    bm = bmesh.from_edit_mesh(bpy.data.objects['右耳'].data)
    bm_vert = [v for v in bm.verts if v.select]
    edges = bm_vert[0].link_edges
    for edge in edges:
        if edge.other_vert(bm_vert[0]) in bm_compare_vert:
            bm.edges.ensure_lookup_table()
            print(edge.index)
            index = edge.index
   
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":8, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":index, "mesh_select_mode_init":(True, False, False)}, 
                               TRANSFORM_OT_edge_slide={"value":0, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'FACE'}, 
                                                        "use_snap_project":False, "snap_target":'CENTER', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, 
                                                        "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})
    
def extrude_retopo(name, border_vert_group_name, width):
    obj = bpy.data.objects[name]
    # 复制一份物体用于投射到物体上
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name + 'compare'
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.collection.objects.link(duplicate_obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=border_vert_group_name)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.2)

    bm = bmesh.from_edit_mesh(obj.data)

    bottom_border_co = [v.co for v in bm.verts if v.select]
    bottom_border_co = utils_get_order_border_vert(bottom_border_co)

    # 先根据偏移值进行法向挤出并切割
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, 2), "orient_type":'NORMAL'})

    temp_co = [v.co for v in bm.verts if v.select]
    temp_co = utils_get_order_border_vert(temp_co)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    ceil_border_co = list()
    ceil_border_normal = list()
    for co in temp_co:
        _, closest_co, closest_normal, _ = duplicate_obj.closest_point_on_mesh(mathutils.Vector(co))
        ceil_border_co.append(closest_co[0:3])
        ceil_border_normal.append(closest_normal[0:3])

    plane_center_border_co = list()
    plane_inner_border_co = list()
    plane_outer_border_co = list()
    for index, co in enumerate(ceil_border_co):
        plane_center_border_co.append(co)
        plane_inner_border_co.append((co[0] - ceil_border_normal[index][0]* 0.5, co[1] - ceil_border_normal[index][1]* 0.5,
                                      co[2] - ceil_border_normal[index][2]* 0.5))
        plane_outer_border_co.append((co[0] + ceil_border_normal[index][0]* 0.6, co[1] + ceil_border_normal[index][1]* 0.6,
                                      co[2] + ceil_border_normal[index][2]* 0.6))

    utils_draw_curve(plane_center_border_co, "Center", 0)
    utils_draw_curve(plane_inner_border_co, "Inner", 0)
    utils_draw_curve(plane_outer_border_co, "CutPlane", 0)

    # 与软耳膜相同，切掉要重拓扑的部分
    get_cut_plane()
    plane_cut(border_vert_group_name)
    delete_useless_part(border_vert_group_name)

    # 挤出
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    for i in range(1, 4):
        bm = bmesh.from_edit_mesh(obj.data)  
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, -0.5), "orient_type":'NORMAL'})
        temp_vertex = [v for v in bm.verts if v.select]
        for v in temp_vertex:
            _, closest_co, _, _ = duplicate_obj.closest_point_on_mesh(mathutils.Vector(v.co))
            v.co = closest_co

    bpy.ops.object.mode_set(mode='OBJECT')


    retopo_border_co = list()
    # 圆滑
    for border_co in retopo_border_co:
        iterations = 20
        while iterations:
            iterations -= 1
            for idx, _ in enumerate(border_co):
                if idx == 0:
                    border_co[idx] = average_locations(border_co[-1], border_co[1])
                elif idx == len(border_co) - 1:
                    border_co[idx] = average_locations(border_co[-2], border_co[0])
                else:
                    border_co[idx] = average_locations(border_co[idx - 1], border_co[idx + 1])

def average_locations(list1, list2):
    return [(list1[0]+list2[0])/2, (list1[1]+list2[1])/2, (list1[2]+list2[2])/2]


def resample_coords(coords, factor):

    segments = len(coords) * factor

    if len(coords) < 2:
        return coords

    arch_len = 0
    cumulative_lengths = [0]  # TODO: make this the right size and dont append

    for i in range(0, len(coords) - 1):
        v0 = coords[i]
        v1 = coords[i + 1]
        V = v1 - v0
        arch_len += V.length
        cumulative_lengths.append(arch_len)

    v0 = coords[-1]
    v1 = coords[0]
    V = v1 - v0
    arch_len += V.length
    cumulative_lengths.append(arch_len)
    segments += 1

    new_coords = [[None]] * segments

    n = 0

    for i in range(0, segments):
        desired_length_raw = i  / segments * arch_len
        if desired_length_raw > arch_len:
            desired_length = desired_length_raw - arch_len
        elif desired_length_raw < 0:
            desired_length = arch_len + desired_length_raw  # this is the end, + a negative number
        else:
            desired_length = desired_length_raw

        for j in range(n, len(coords) + 1):

            if cumulative_lengths[j] > desired_length:
                break

        extra = desired_length - cumulative_lengths[j- 1]

        if j == len(coords):
            new_coords[i] = coords[j - 1] + extra * (coords[0] - coords[j - 1]).normalized()
        else:
            new_coords[i] = coords[j - 1] + extra * (coords[j] - coords[j - 1]).normalized()

    return new_coords

def smooth_stepcut(obj_name):
    pianyi = bpy.context.scene.qiegewaiBianYuan  # 获取偏移值
    # 复制一份物体并应用布尔修改器用于平滑
    obj = bpy.data.objects[obj_name]
    name = obj.name
    old_obj = bpy.data.objects[obj_name + 'ceqieCompare']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[old_obj]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.edges_select_sharp()
    bm = bmesh.from_edit_mesh(old_obj.data)
    edges_old = [edge for edge in bm.edges if edge.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    bm.free()

    if bpy.data.objects.get(name + 'stepcutpinghua') != None:
        bpy.data.objects.remove(bpy.data.objects[name + 'stepcutpinghua'], do_unlink=True)
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name + "stepcutpinghua"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[duplicate_obj]
    bpy.data.objects[duplicate_obj].select_set(True)
    # 修改器左右耳用同一个名字可能会有问题
    bpy.ops.object.modifier_apply(modifier="step cut", single_user=True)
    # 选中需要操作的外圈循环边
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.edges_select_sharp()
    bm = bmesh.from_edit_mesh(duplicate_obj.data)
    edges = [edge for edge in bm.edges if edge.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    for edge in edges:
        if edge not in edges_old:
            edge.select_set(True)
    bm.free()
    
    # 进行offset cut操作
    bpy.ops.huier.offset_cut(width=pianyi)
    bpy.ops.mesh.bevel(offset=pianyi, segments=8)
    bpy.ops.object.mode_set(mode='OBJECT')
    if not bpy.data.objects[name].hide_get():
        bpy.data.objects[name].hide_set(True)
        bpy.data.objects[name + 'stepcutpinghua'].hide_set(False)


# 用于保存顶点坐标更改的字典
vertex_changes = {}

# 定义处理函数
def handle_depsgraph_update_post(scene):
    global vertex_changes

    # 获取活动对象
    obj = bpy.context.active_object

    # 检查对象是否存在且处于雕刻模式下
    if obj and obj.mode == 'SCULPT':
        # 获取对象的网格数据
        mesh = obj.data

        # 遍历每个顶点
        for vert in mesh.vertices:
            # 检查顶点是否在更改字典中
            if vert.index not in vertex_changes:
                # 如果不在字典中，则将其添加，并记录初始坐标
                vertex_changes[vert.index] = vert.co.copy()
            else:
                # 如果在字典中，则检查坐标是否发生更改
                if vert.co != vertex_changes[vert.index]:
                    # 如果坐标更改了，则打印顶点索引和新坐标
                    print("Vertex Index:", vert.index)
                    print("New Coordinates:", vert.co)
                    # 更新更改字典中的坐标
                    vertex_changes[vert.index] = vert.co.copy()

# 注册事件处理程序
bpy.app.handlers.depsgraph_update_post.append(handle_depsgraph_update_post)
