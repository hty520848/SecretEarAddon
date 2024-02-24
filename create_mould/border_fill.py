import bpy
import bmesh
import math
from contextlib import redirect_stdout
import io
from ..utils.utils import utils_re_color


def get_different_vert(after_bm, before_bm):
    different_vert_co = []
    different_vert_index = []
    before_co = []
    for vert in before_bm.verts:
        before_co.append(vert.co)

    for vert in after_bm.verts:
        if vert.co not in before_co:
            different_vert_co.append(vert.co)
            different_vert_index.append(vert.index)

    return different_vert_index, different_vert_co


def get_up_center_point(selected_verts_co):
    size = len(selected_verts_co)
    center = [0, 0, 0]
    for vert in selected_verts_co:
        center[0] += vert[0]
        center[1] += vert[1]
        center[2] += vert[2]

    center[0] /= size
    center[1] /= size
    center[2] /= size

    return center


def extrude_border(border_co, bm):
    bpy.ops.mesh.select_all(action='DESELECT')

    outside_border_vert = []
    for v in bm.verts:
        if v.co in border_co:
            outside_border_vert.append(v)

    # 选中边界的边
    outside_edges = set()
    # 遍历选中的顶点
    for vert in outside_border_vert:
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in outside_border_vert and edge.verts[1] in outside_border_vert:
                outside_edges.add(edge)

    for v in outside_border_vert:
        v.select_set(True)

    for edge in outside_edges:
        edge.select_set(True)

    # 复制选中的顶点并沿着各自的法线方向移动
    bpy.ops.mesh.duplicate()

    # 获取所有选中的顶点
    inside_border_vert = [v for v in bm.verts if v.select]
    inside_border_vert_index = [v.index for v in inside_border_vert]
    inside_edges = [e for e in bm.edges if e.select]
    thickness = bpy.context.scene.zongHouDu
    for i, vert in enumerate(inside_border_vert):
        vert.co -= outside_border_vert[i].normal * thickness  # 沿法线方向移动

    # 重新选中外边界
    for v in outside_border_vert:
        v.select_set(True)

    for edge in outside_edges:
        edge.select_set(True)

    bpy.ops.mesh.bridge_edge_loops()

    return inside_border_vert_index, inside_border_vert, inside_edges


def remove_doubles(threshold, inside_border_vert, inside_edges, bm):
    # 为了防止问题，桥接完了再简化合并顶点
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in inside_border_vert:
        v.select_set(True)
    for e in inside_edges:
        e.select_set(True)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # any printing or operator output within this block
        # will go into 'stdout'
        bpy.ops.mesh.remove_doubles(threshold=threshold)
    del stdout

    inside_border_vert = [v for v in bm.verts if v.select]

    return inside_border_vert


def fill_inner_border(up_inner_border, bottom_inner_border, target_bm):
    bpy.ops.mesh.select_all(action='DESELECT')
    # 选中上内边界的边
    up_inner_edges = set()
    # 遍历选中的顶点
    for vert in up_inner_border:
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in up_inner_border and edge.verts[1] in up_inner_border:
                up_inner_edges.add(edge)

    # 选中上内边界
    for v in up_inner_border:
        v.select_set(True)

    for edge in up_inner_edges:
        edge.select_set(True)

    # 选中下内边界的边
    bottom_inner_edges = set()
    # 遍历选中的顶点
    for vert in bottom_inner_border:
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in bottom_inner_border and edge.verts[1] in bottom_inner_border:
                bottom_inner_edges.add(edge)

        # 选中上内边界
    for v in bottom_inner_border:
        v.select_set(True)

    for edge in bottom_inner_edges:
        edge.select_set(True)
    # 桥接上下内边界
    bpy.ops.mesh.bridge_edge_loops()


def recover_and_refill():
    '''
    为了调整厚度后重新桥接
    '''
    # 恢复到桥接前
    bpy.data.objects.remove(bpy.data.objects["右耳"], do_unlink=True)

    cur_obj = bpy.data.objects["右耳OriginForFill"]
    cur_obj.hide_set(False)
    cur_obj.name = "右耳"
    bpy.context.view_layer.objects.active = cur_obj

    # 将切割和挖洞后形成的新顶点沿发现向内移动生成面,并得到用于平滑的顶点组
    getSmoothVertexGroup()

    # 根据内边缘顶点桥接补面生成内壁
    border_fill()

    applySmooth()

    utils_re_color("右耳", (1, 0.319, 0.133))


def getSmoothVertexGroup():
    # 将获取到的顶点加入到顶点组中
    name = "右耳"  # TODO    根据导入文件名称更改
    ori_obj = bpy.data.objects[name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForFill"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)

    # 最初始的，未挖孔与切割的为 XXXOriginForCreateMouldR
    origin_obj = bpy.data.objects["右耳OriginForCreateMouldR"]
    # 获取网格数据
    origin_mesh = origin_obj.data
    # 创建bmesh对象
    origin_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    origin_bm.from_mesh(origin_mesh)
    origin_bm.verts.ensure_lookup_table()

    # 挖孔后的物体为 XXXOriginForCutR
    dig_after_obj = bpy.data.objects["右耳OriginForCutR"]
    # 获取网格数据
    dig_after_mesh = dig_after_obj.data
    # 创建bmesh对象
    dig_after_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    dig_after_bm.from_mesh(dig_after_mesh)
    dig_after_bm.verts.ensure_lookup_table()

    # 挖孔,切割后的物体为 XXXOriginForFill
    fill_before_obj = bpy.data.objects["右耳OriginForFill"]
    # 获取网格数据
    fill_before_mesh = fill_before_obj.data
    # 创建bmesh对象
    fill_before_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    fill_before_bm.from_mesh(fill_before_mesh)
    fill_before_bm.verts.ensure_lookup_table()

    target_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    target_mesh = target_obj.data
    target_bm = bmesh.from_edit_mesh(target_mesh)

    # 获取上边界顶点
    _, up_border_co = get_different_vert(dig_after_bm, origin_bm)
    outer_border_index, _ = get_different_vert(fill_before_bm, origin_bm)
    bottom_outer_border_index, bottom_border_co = get_different_vert(fill_before_bm, dig_after_bm)
    up_outer_border_index = list(set(outer_border_index) - set(bottom_outer_border_index))

    up_inner_border_index, up_inner_border, up_inner_edge = extrude_border(up_border_co, target_bm)
    bottom_inner_border_index, bottom_inner_border, bottom_inner_edge = extrude_border(bottom_border_co, target_bm)

    bpy.ops.object.mode_set(mode='OBJECT')
    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    if (up_outer_border_vertex == None):
        up_outer_border_vertex = ori_obj.vertex_groups.new(name="UpOuterBorderVertex")
    for vert_index in up_outer_border_index:
        up_outer_border_vertex.add([vert_index], 1, 'ADD')

    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    if (bottom_outer_border_vertex == None):
        bottom_outer_border_vertex = ori_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    for vert_index in bottom_outer_border_index:
        bottom_outer_border_vertex.add([vert_index], 1, 'ADD')

    up_inner_border_vertex = ori_obj.vertex_groups.get("UpInnerBorderVertex")
    if (up_inner_border_vertex == None):
        up_inner_border_vertex = ori_obj.vertex_groups.new(name="UpInnerBorderVertex")
    for vert_index in up_inner_border_index:
        up_inner_border_vertex.add([vert_index], 1, 'ADD')

    bottom_inner_border_vertex = ori_obj.vertex_groups.get("BottomInnerBorderVertex")
    if (bottom_inner_border_vertex == None):
        bottom_inner_border_vertex = ori_obj.vertex_groups.new(name="BottomInnerBorderVertex")
    for vert_index in bottom_inner_border_index:
        bottom_inner_border_vertex.add([vert_index], 1, 'ADD')


def applySmooth():
    ori_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_all(action='DESELECT')

    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    if (up_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.remove_doubles(threshold=0.8)

    bpy.ops.mesh.select_all(action='DESELECT')
    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    if (up_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    up_inner_border_vertex = ori_obj.vertex_groups.get("UpInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    if (up_inner_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.subdivide()

    bpy.ops.mesh.select_all(action='DESELECT')
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bottom_inner_border_vertex = ori_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.subdivide()

    bpy.ops.mesh.select_all(action='SELECT')

    up_inner_border_vertex = ori_obj.vertex_groups.get("UpInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    if (up_inner_border_vertex != None):
        bpy.ops.object.vertex_group_deselect()
    bottom_inner_border_vertex = ori_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.object.vertex_group_deselect()
    bpy.ops.object.vertex_group_deselect()
    bottom_outer_border_vertex = ori_obj.vertex_groups.get("BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    if (bottom_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()
    up_outer_border_vertex = ori_obj.vertex_groups.get("UpOuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpOuterBorderVertex')
    if (up_outer_border_vertex != None):
        bpy.ops.object.vertex_group_select()

    outer_border_vertex = ori_obj.vertex_groups.get("OuterBorderVertex")
    if (outer_border_vertex == None):
        outer_border_vertex = ori_obj.vertex_groups.new(name="OuterBorderVertex")
    outer_border_vertex = ori_obj.vertex_groups.get("OuterBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='OuterBorderVertex')
    if (outer_border_vertex != None):
        bpy.ops.object.vertex_group_assign()

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.modifier_add(type='SMOOTH')
    bpy.context.object.modifiers["Smooth"].vertex_group = "OuterBorderVertex"
    bpy.ops.object.modifier_add(type='SMOOTH')
    bpy.context.object.modifiers["Smooth.001"].vertex_group = "OuterBorderVertex"
    bpy.context.object.modifiers["Smooth.001"].invert_vertex_group = True


def border_fill():
    target_obj = bpy.data.objects["右耳"]
    bpy.ops.object.mode_set(mode='EDIT')
    target_mesh = target_obj.data
    target_bm = bmesh.from_edit_mesh(target_mesh)

    # 根据顶点组获取上下内边缘点
    up_inner_border = []
    bottom_inner_border = []

    up_inner_border_vertex = target_obj.vertex_groups.get("UpInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='UpInnerBorderVertex')
    if (up_inner_border_vertex != None):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        up_inner_border = [v for v in target_bm.verts if v.select]
    bottom_inner_border_vertex = target_obj.vertex_groups.get("BottomInnerBorderVertex")
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
    if (bottom_inner_border_vertex != None):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bottom_inner_border = [v for v in target_bm.verts if v.select]

    # 简化合并顶点
    # up_inner_border = remove_doubles(0.8, up_inner_border, up_inner_edge, target_bm)
    # bottom_inner_border = remove_doubles(0.8, bottom_inner_border, bottom_inner_edge, target_bm)

    fill_inner_border(up_inner_border, bottom_inner_border, target_bm)

    # 2024/1/20 改为先桥接再合并
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # any printing or operator output within this block
        # will go into 'stdout'
        # 2024/1/29 补面的褶皱暂时处理
        bpy.ops.mesh.remove_doubles(threshold=2)
    del stdout

    bmesh.update_edit_mesh(target_mesh)

    bpy.ops.object.mode_set(mode='OBJECT')


def hard_eardrum_extrude_border():
    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.data.objects["ExampleR"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForFill"
    bpy.context.collection.objects.link(duplicate_obj)

    duplicate_obj.hide_set(True)

    # 挖孔后的物体为 XXXOriginForCutR
    dig_after_obj = bpy.data.objects["ExampleROriginForCutR"]
    # 获取网格数据
    dig_after_mesh = dig_after_obj.data
    # 创建bmesh对象
    dig_after_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    dig_after_bm.from_mesh(dig_after_mesh)
    dig_after_bm.verts.ensure_lookup_table()

    # 挖孔,切割后的物体为 XXXOriginForFill
    fill_before_obj = bpy.data.objects["ExampleROriginForFill"]
    # 获取网格数据
    fill_before_mesh = fill_before_obj.data
    # 创建bmesh对象
    fill_before_bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    fill_before_bm.from_mesh(fill_before_mesh)
    fill_before_bm.verts.ensure_lookup_table()

    target_obj = bpy.data.objects["ExampleR"]
    bpy.ops.object.mode_set(mode='EDIT')
    target_mesh = target_obj.data
    target_bm = bmesh.from_edit_mesh(target_mesh)

    bottom_border_co = get_different_vert(fill_before_bm, dig_after_bm)

    bottom_inner_border, bottom_inner_edge = extrude_border(bottom_border_co, target_bm)

    bpy.ops.mesh.select_all(action='DESELECT')
    for v in bottom_inner_border:
        v.select_set(True)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        # any printing or operator output within this block
        # will go into 'stdout'
        bpy.ops.mesh.remove_doubles(threshold=1)
    del stdout

    bmesh.update_edit_mesh(target_mesh)

    bpy.ops.object.mode_set(mode='OBJECT')
