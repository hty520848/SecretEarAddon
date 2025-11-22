import bpy
import bmesh
import math
import mathutils
from mathutils import Vector
from ...tool import moveToRight, moveToLeft

def copy_model_for_top_circle_cut():
    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    # 根据当前蓝线切割后的模型复制出一份物体用于调整顶部圆环的角度时回退重新切割
    shell_for_top_circle_cut_obj = bpy.data.objects.get(name + "shellObjForTopCircleCut")  # TODO 后期作外壳模块切换时记得将该物体删除
    if (shell_for_top_circle_cut_obj != None):
        bpy.data.objects.remove(shell_for_top_circle_cut_obj, do_unlink=True)
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellObjForTopCircleCut"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)


def copy_curve_and_resample(curve_name, resample_number, vertex_group_name):
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(curve_name)
    curve_obj = obj.copy()
    curve_obj.data = obj.data.copy()
    curve_obj.animation_data_clear()
    curve_obj.name = curve_name + "Copy"
    curve_obj.hide_set(False)
    bpy.context.collection.objects.link(curve_obj)

    if (name == "右耳"):
        moveToRight(curve_obj)
    elif (name == "左耳"):
        moveToLeft(curve_obj)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = curve_obj
    curve_obj.select_set(True)
    curve_obj.data.bevel_depth = 0

    modifier = curve_obj.modifiers.new(name="Resample", type='NODES')
    bpy.ops.node.new_geometry_node_group_assign()
    node_tree = bpy.data.node_groups[0]
    node_links = node_tree.links
    input_node = node_tree.nodes[0]
    output_node = node_tree.nodes[1]
    resample_node = node_tree.nodes.new("GeometryNodeResampleCurve")
    resample_node.inputs[2].default_value = resample_number
    node_links.new(input_node.outputs[0], resample_node.inputs[0])
    node_links.new(resample_node.outputs[0], output_node.inputs[0])
    bpy.ops.object.convert(target='MESH')
    bpy.data.node_groups.remove(node_tree)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
    curve_obj.vertex_groups.new(name=vertex_group_name)
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')
    return curve_obj


def subdivide_edges(bm, upper_vertex_group, bottom_vertex_group, subdivide_number, subdivide_vertex_group):
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=upper_vertex_group)
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group=bottom_vertex_group)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_mode(type='EDGE')
    edges = [e for e in bm.edges if e.select]
    bpy.ops.mesh.region_to_loop()
    border_edges = [e for e in bm.edges if e.select]
    subdivide_edges = [e for e in edges if e not in border_edges]
    bpy.ops.mesh.select_all(action='DESELECT')
    for e in subdivide_edges:
        e.select_set(True)
    bpy.ops.mesh.subdivide(number_cuts=subdivide_number, ngon=False, quadcorner='INNERVERT')

    bpy.ops.mesh.select_mode(type='VERT')
    verts = [v for v in bm.verts if v.select]
    bpy.ops.mesh.region_to_loop()
    border_verts = [v for v in bm.verts if v.select]
    subdivide_verts = [v for v in verts if v not in border_verts]
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in subdivide_verts:
        v.select_set(True)
    bpy.ops.object.vertex_group_set_active(group=upper_vertex_group)
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group=bottom_vertex_group)
    bpy.ops.object.vertex_group_remove_from()
    bpy.context.active_object.vertex_groups.new(name=subdivide_vertex_group)
    bpy.ops.object.vertex_group_assign()


def judge_normals():
    obj_mesh = bmesh.from_edit_mesh(bpy.context.active_object.data)
    verts = [v for v in obj_mesh.verts if v.select]
    sum = 0
    for v in verts:
        sum += v.normal[2]
    return sum < 0


def copy_loft_obj_for_battery_plane_cut(loft_obj):
    # 根据当前两条蓝线桥接后的模型复制出一份物体用于电池面板的切割
    name = bpy.context.scene.leftWindowObj
    loft_obj_for_battery_plane_cut = bpy.data.objects.get(name + "shellLoftObj")  # TODO 后期作外壳模块切换时记得将该物体删除
    if (loft_obj_for_battery_plane_cut != None):
        bpy.data.objects.remove(loft_obj_for_battery_plane_cut, do_unlink=True)
    duplicate_obj = loft_obj.copy()
    duplicate_obj.data = loft_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = name + "shellLoftObj"
    bpy.context.collection.objects.link(duplicate_obj)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = duplicate_obj
    duplicate_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.edge_face_add()
    if not judge_normals():
        bpy.ops.mesh.flip_normals()
    bpy.ops.mesh.extrude_context_move(TRANSFORM_OT_translate={"value": (0, 0, 0.5), "orient_type": 'NORMAL'})
    bpy.ops.object.vertex_group_set_active(group='LoftVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate_obj.hide_set(True)


def adjust_loft_part_by_distance():
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiR
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiR
    elif (name == "左耳"):
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiL
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiL

    origin_loft_obj = bpy.data.objects.get(name + "LoftObjForSmooth")
    if origin_loft_obj:
        smooth_loft_obj = origin_loft_obj.copy()
        smooth_loft_obj.data = origin_loft_obj.data.copy()
        smooth_loft_obj.name = origin_loft_obj.name + "Copy"
        smooth_loft_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(smooth_loft_obj)
        if name == '右耳':
            moveToRight(smooth_loft_obj)
        else:
            moveToLeft(smooth_loft_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = smooth_loft_obj
        smooth_loft_obj.hide_set(False)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(smooth_loft_obj.data)
        if xiaSheRuYinZi != 0:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='ExtrudeLowerVertex')
            bpy.ops.object.vertex_group_select()
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)
            ray_cast_obj = bpy.data.objects.get(name + "MouldReset")

            for v in verts:
                direction = (v.co - center).normalized()
                hit1, loc1, _, _ = ray_cast_obj.ray_cast(center, direction)
                if not hit1:
                    continue
                else:
                    if (v.co - center).length > (loc1 - center).length:
                        v.co = loc1
                        continue
                hit2, loc2, _, _ = ray_cast_obj.ray_cast(v.co, direction)
                if not hit2:
                    continue
                else:
                    v.co = v.co + (loc2 - v.co) * xiaSheRuYinZi / 100

            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.looptools_curve(boundaries=False, influence=100, interpolation='cubic', lock_x=False,
                                         lock_y=False, lock_z=False, regular=True, restriction='none')

        if shangSheRuYinZi != 0:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='ExtrudeUpperVertex')
            bpy.ops.object.vertex_group_select()
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)
            ray_cast_obj = bpy.data.objects.get(name + "MouldReset")

            for v in verts:
                direction = (v.co - center).normalized()
                hit, loc, _, _ = ray_cast_obj.ray_cast(v.co, direction)
                if not hit:
                    continue
                else:
                    v.co = v.co + (loc - v.co) * shangSheRuYinZi / 100

            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.looptools_curve(boundaries=False, influence=100, interpolation='cubic', lock_x=False,
                                         lock_y=False, lock_z=False, regular=True, restriction='none')

        if xiaSheRuYinZi != 0 or shangSheRuYinZi != 0:
            bpy.ops.object.vertex_group_set_active(group='LoftVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=10)

        bpy.ops.object.mode_set(mode='OBJECT')
        copy_loft_obj_for_battery_plane_cut(smooth_loft_obj)
        main_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = main_obj
        main_obj.select_set(True)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        copy_model_for_top_circle_cut()


def adjust_loft_part_by_scale():
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiR
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiR
    elif (name == "左耳"):
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiL
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiL

    origin_loft_obj = bpy.data.objects.get(name + "LoftObjForSmooth")
    if origin_loft_obj:
        smooth_loft_obj = origin_loft_obj.copy()
        smooth_loft_obj.data = origin_loft_obj.data.copy()
        smooth_loft_obj.name = origin_loft_obj.name + "Copy"
        smooth_loft_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(smooth_loft_obj)
        if name == '右耳':
            moveToRight(smooth_loft_obj)
        else:
            moveToLeft(smooth_loft_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = smooth_loft_obj
        smooth_loft_obj.hide_set(False)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(smooth_loft_obj.data)
        if xiaSheRuYinZi != 0:
            scale_factor_lower = xiaSheRuYinZi / 200
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='ExtrudeLowerVertex')
            bpy.ops.object.vertex_group_select()
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)

            ray_cast_obj = bpy.data.objects.get(name + "MouldReset")
            ray_bm = bmesh.new()
            ray_bm.from_mesh(ray_cast_obj.data)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(ray_bm)
            mwi = ray_cast_obj.matrix_world.inverted()
            mwi_start = mwi @ center

            for v in verts:
                mwi_end = mwi @ v.co
                mwi_dir = mwi_end - mwi_start
                loc, normal, fidx, distance = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx:
                    actual_dis = (v.co - center).length
                    if actual_dis > distance:
                        # v.co = loc
                        continue

                v.co = v.co + (v.co - center) * scale_factor_lower
                mwi_end = mwi @ v.co
                mwi_dir = mwi_end - mwi_start

                loc, normal, fidx, distance = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx:
                    actual_dis = (v.co - center).length
                    if actual_dis > distance:
                        v.co = loc
                    # if (v.co - loc).dot(normal) < 0:
                    #     v.co = loc

            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.looptools_curve(boundaries=False, influence=100, interpolation='cubic', lock_x=False,
                                         lock_y=False, lock_z=False, regular=True, restriction='none')

        if shangSheRuYinZi != 0:
            scale_factor_upper = shangSheRuYinZi / 300
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='ExtrudeUpperVertex')
            bpy.ops.object.vertex_group_select()
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)

            ray_cast_obj = bpy.data.objects.get(name + "MouldReset")
            ray_bm = bmesh.new()
            ray_bm.from_mesh(ray_cast_obj.data)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(ray_bm)
            mwi = ray_cast_obj.matrix_world.inverted()
            mwi_start = mwi @ center

            for v in verts:
                mwi_end = mwi @ v.co
                mwi_dir = mwi_end - mwi_start
                loc, normal, fidx, distance = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx:
                    actual_dis = (v.co - center).length
                    if actual_dis > distance:
                        v.co = loc
                        continue

                v.co = v.co + (v.co - center) * scale_factor_upper
                mwi_end = mwi @ v.co
                mwi_dir = mwi_end - mwi_start
                loc, normal, fidx, distance = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx:
                    actual_dis = (v.co - center).length
                    if actual_dis > distance:
                        v.co = loc
                    # if (v.co - loc).dot(normal) < 0:
                    #     v.co = loc

            bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=2)
            # bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.looptools_curve(boundaries=False, influence=100, interpolation='cubic', lock_x=False,
                                         lock_y=False, lock_z=False, regular=True, restriction='none')

        if xiaSheRuYinZi != 0 and shangSheRuYinZi != 0:
            bpy.ops.object.vertex_group_set_active(group='LoftVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=5)

        bpy.ops.object.mode_set(mode='OBJECT')
        copy_loft_obj_for_battery_plane_cut(smooth_loft_obj)
        main_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = main_obj
        main_obj.select_set(True)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.join()
        # 在某些情况下如果合并的物体没有顶点会导致合并操作失败，需要删除这个物体
        # if bpy.data.objects.get(name + "LoftObjForSmoothCopy") is not None:
        #     bpy.data.objects.remove(bpy.data.objects.get(name + "LoftObjForSmoothCopy"), do_unlink=True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        copy_model_for_top_circle_cut()


def bridge_and_smooth():
    name = bpy.context.scene.leftWindowObj
    # if (name == "右耳"):
    #     xiaFangYangXian_offset = bpy.context.scene.xiaFangYangXianPianYiR
    #     mianban_offset = bpy.context.scene.mianBanPianYiR
    # elif (name == "左耳"):
    #     xiaFangYangXian_offset = bpy.context.scene.xiaFangYangXianPianYiL
    #     mianban_offset = bpy.context.scene.mianBanPianYiL
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bm = bmesh.from_edit_mesh(bpy.data.objects.get(name).data)
    resample_number = len([v for v in bm.verts if v.select])
    bpy.ops.object.mode_set(mode='OBJECT')

    plane_curve = copy_curve_and_resample(name + "PlaneBorderCurve", resample_number, "BottomOuterCurveVertex")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)
    plane_curve.select_set(True)
    bpy.ops.object.join()

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(bpy.data.objects.get(name).data)
    bpy.data.objects.get(name).vertex_groups.new(name="LoftVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.bridge_edge_loops(number_cuts=1, interpolation='LINEAR')
    verts = [v for v in bm.verts if v.select]
    bpy.ops.mesh.region_to_loop()
    border_verts = [v for v in bm.verts if v.select]
    unborder_verts = [v for v in verts if v not in border_verts]
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in unborder_verts:
        v.select_set(True)
    bpy.data.objects.get(name).vertex_groups.new(name="BridgeMiddleCurveVertex")
    bpy.ops.object.vertex_group_assign()

    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_select()

    # 根据面板的位置进行切割
    # circle = bpy.data.objects.get(name + "BottomCircle")
    # plane_normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
    # if plane_normal.z < 0:
    #     plane_normal = -plane_normal
    # position = circle.location - plane_normal * mianban_offset
    # bpy.ops.mesh.bisect(plane_co=position, plane_no=plane_normal)
    # bpy.data.objects.get(name).vertex_groups.new(name="BridgeMiddleCurveVertex")
    # bpy.ops.object.vertex_group_assign()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    # bpy.ops.object.vertex_group_remove_from()

    lower_verts = [v for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    upper_verts = [v for v in bm.verts if v.select]

    vert_distance = list()
    for upper_vert in upper_verts:
        min_distance = math.inf
        for lower_vert in lower_verts:
            distance = (upper_vert.co - lower_vert.co).length
            if distance < min_distance:
                min_distance = distance
        vert_distance.append(min_distance)
    average_distance = sum(vert_distance) / len(vert_distance)
    upper_cut_number = int(average_distance / 0.4)
    if upper_cut_number % 2 == 0:
        upper_cut_number += 1

    # upper_cut_number = int((xiaFangYangXian_offset + mianban_offset) / 0.2)
    # if upper_cut_number % 2 == 0:
    #     upper_cut_number += 1
    # 环切并细分上下部分，选取最中间的循环边用于缩放
    subdivide_edges(bm, 'BridgeMiddleCurveVertex', 'BottomOuterBorderVertex',
                    upper_cut_number, "ExtrudeUpperVertex")
    bpy.ops.object.vertex_group_set_active(group="ExtrudeUpperVertex")
    bpy.ops.object.vertex_group_select()
    for _ in range(0, int((upper_cut_number - 1) / 2)):
        bpy.ops.mesh.select_less()
    bpy.ops.object.vertex_group_remove()
    bpy.data.objects.get(name).vertex_groups.new(name="ExtrudeUpperVertex")
    bpy.ops.object.vertex_group_assign()
    subdivide_edges(bm, 'BridgeMiddleCurveVertex', 'BottomOuterCurveVertex',
                    upper_cut_number, "ExtrudeLowerVertex")
    bpy.ops.object.vertex_group_set_active(group="ExtrudeLowerVertex")
    bpy.ops.object.vertex_group_select()
    for _ in range(0, int((upper_cut_number - 1) / 2)):
        bpy.ops.mesh.select_less()
    bpy.ops.object.vertex_group_remove()
    bpy.data.objects.get(name).vertex_groups.new(name="ExtrudeLowerVertex")
    bpy.ops.object.vertex_group_assign()

    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BridgeMiddleCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # bm.edges.ensure_lookup_table()
    # edges = [e.index for e in bm.edges if e.select]
    # bpy.ops.mesh.region_to_loop()
    # border_edges = [e.index for e in bm.edges if e.select]
    # unborder_edges = [index for index in edges if index not in border_edges]
    # upper_cut_number = int((xiaFangYangXian_offset + mianban_offset) / 0.2)
    # if upper_cut_number % 2 == 0:
    #     upper_cut_number += 1
    # bpy.ops.mesh.loopcut_slide(
    #     MESH_OT_loopcut={"number_cuts": upper_cut_number, "smoothness": 0, "falloff": 'INVERSE_SQUARE',
    #                      "object_index": 0, "edge_index": unborder_edges[0],
    #                      "mesh_select_mode_init": (True, False, False)},
    #     TRANSFORM_OT_edge_slide={"value": 0, "single_side": False, "use_even": False, "flipped": False,
    #                              "use_clamp": True, "mirror": True, "snap": False, "snap_elements": {'FACE'},
    #                              "use_snap_project": False, "snap_target": 'CENTER', "use_snap_self": True,
    #                              "use_snap_edit": True, "use_snap_nonedit": True, "use_snap_selectable": False,
    #                              "snap_point": (0, 0, 0), "correct_uv": True, "release_confirm": True,
    #                              "use_accurate": False})
    # bpy.ops.mesh.select_mode(type='VERT')
    # bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_remove_from()
    # for _ in range(0, int((upper_cut_number - 1) / 2)):
    #     bpy.ops.mesh.select_less()
    # bpy.data.objects.get(name).vertex_groups.new(name="ExtrudeUpperVertex")
    # bpy.ops.object.vertex_group_assign()
    #
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BridgeMiddleCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # bm.edges.ensure_lookup_table()
    # edges = [e.index for e in bm.edges if e.select]
    # bpy.ops.mesh.region_to_loop()
    # border_edges = [e.index for e in bm.edges if e.select]
    # unborder_edges = [index for index in edges if index not in border_edges]
    # bpy.ops.mesh.loopcut_slide(
    #     MESH_OT_loopcut={"number_cuts": 3, "smoothness": 0, "falloff": 'INVERSE_SQUARE', "object_index": 0,
    #                      "edge_index": unborder_edges[0], "mesh_select_mode_init": (True, False, False)},
    #     TRANSFORM_OT_edge_slide={"value": 0, "single_side": False, "use_even": False, "flipped": False,
    #                              "use_clamp": True, "mirror": True, "snap": False, "snap_elements": {'FACE'},
    #                              "use_snap_project": False, "snap_target": 'CENTER', "use_snap_self": True,
    #                              "use_snap_edit": True, "use_snap_nonedit": True, "use_snap_selectable": False,
    #                              "snap_point": (0, 0, 0), "correct_uv": True, "release_confirm": True,
    #                              "use_accurate": False})
    # bpy.ops.mesh.select_mode(type='VERT')
    # bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    # bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.mesh.select_less()
    # bpy.data.objects.get(name).vertex_groups.new(name="ExtrudeLowerVertex")
    # bpy.ops.object.vertex_group_assign()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='LoftVertex')
    bpy.ops.object.vertex_group_select()
    # 分离出一份物体用于调整平滑度
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != name:
                loft_obj = obj
    if name == "右耳":
        moveToRight(loft_obj)
    elif name == "左耳":
        moveToLeft(loft_obj)
    if bpy.data.objects.get(name + "LoftObjForSmooth") != None:
        bpy.data.objects.remove(bpy.data.objects.get(name + "LoftObjForSmooth"), do_unlink=True)
    loft_obj.name = name + "LoftObjForSmooth"
    loft_obj.hide_set(True)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)

    # 根据参数对桥接部分进行平滑
    # adjust_loft_part_by_distance()
    adjust_loft_part_by_scale()



########################################################################################## 弃用
def smooth_vertex(subdivide_number):
    name = bpy.context.scene.leftWindowObj
    main_obj = bpy.data.objects.get(name)
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != name:
                loft_obj = obj
    bpy.context.view_layer.objects.active = loft_obj
    loft_obj.select_set(True)
    main_obj.select_set(False)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.select_mode(type='EDGE')
    # bpy.ops.mesh.region_to_loop()
    # bpy.ops.mesh.select_all(action='INVERT')
    # bpy.ops.mesh.subdivide(number_cuts=6, ngon=False, quadcorner='INNERVERT')
    # bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_remove_from()
    # bpy.ops.object.vertex_group_set_active(group='SmoothVertex')
    # bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='SELECT')
    extrude_vertex(subdivide_number)
    bpy.ops.mesh.vertices_smooth(factor=1, repeat=5)
    bpy.ops.object.mode_set(mode='OBJECT')
    copy_loft_obj_for_battery_plane_cut(loft_obj)

    # 合并回原物体
    loft_obj.select_set(False)
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)
    loft_obj.select_set(True)
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def extrude_vertex(subdivide_number):
    prev_vertex_index = []  # 记录选中内圈时已经选中过的顶点
    new_vertex_index = []  # 记录新选中的内圈顶点,当无新选中的内圈顶点时,说明底部平面的所有内圈顶点都已经被选中的,结束循环
    cur_vertex_index = []  # 记录扩散区域后当前选中的顶点
    inner_circle_index = -1  # 判断当前选中顶点的圈数,根据圈数确定往里走的距离
    index_normal_dict = dict()  # 由于移动一圈顶点后，剩下的顶点的法向会变，导致突出方向出现问题，所以需要存一下初始的方向

    obj = bpy.context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for vert in bm.verts:
        if vert.select:
            index_normal_dict[vert.index] = vert.normal[0:3]

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    for vert in bm.verts:
        if vert.select:
            prev_vertex_index.append(vert.index)

    # 初始化集合使得其能够进入while循环
    new_vertex_index.append(0)
    while len(new_vertex_index) != 0 and inner_circle_index <= subdivide_number - 2:
        inner_circle_index += 1
        # 根据当前选中顶点扩散得到新选中的顶点
        bpy.ops.mesh.select_more()
        # 根据之前记录的选中顶点数组将之前顶点取消选中,使得只有新增的内圈顶点被选中
        cur_vertex_index.clear()
        cur_vertex_index = [vert.index for vert in bm.verts if vert.select]
        bpy.ops.mesh.select_all(action='DESELECT')
        result = [x for x in cur_vertex_index if x not in prev_vertex_index]
        # 将集合new_vertex_index_set清空并将新选中的内圈顶点保存到集合中
        new_vertex_index.clear()
        new_vertex_index = result

        # 假设底部细分参数为6,中间有6圈,则第0,1,2,3圈step依次增加,第4,5圈再依次降低
        if inner_circle_index <= int(subdivide_number/2):
            step = (1 - 0.9 ** (inner_circle_index + 1)) * 3
        else:
            step = (1 - 0.9 ** (2 * int(subdivide_number/2) + 1 - inner_circle_index)) * 3
        # 根据面板参数设置偏移值
        for vert_index in new_vertex_index:
            dir = index_normal_dict[vert_index]
            vert = bm.verts[vert_index]
            vert.select_set(True)
            vert.co[0] += dir[0] * step
            vert.co[1] += dir[1] * step
            vert.co[2] += dir[2] * step
        # 更新集合prev_vertex_index_set
        prev_vertex_index.extend(new_vertex_index)


def bevel_loft_part():
    name = bpy.context.scene.leftWindowObj
    if (name == "右耳"):
        xiaFangYangXian_offset = bpy.context.scene.xiaFangYangXianPianYiR
        mianban_offset = bpy.context.scene.mianBanPianYiR
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiR
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiR
    elif (name == "左耳"):
        xiaFangYangXian_offset = bpy.context.scene.xiaFangYangXianPianYiL
        mianban_offset = bpy.context.scene.mianBanPianYiL
        shangSheRuYinZi = bpy.context.scene.shangSheRuYinZiL
        xiaSheRuYinZi = bpy.context.scene.xiaSheRuYinZiL

    origin_loft_obj = bpy.data.objects.get(name + "LoftObjForSmooth")
    if origin_loft_obj:
        smooth_loft_obj = origin_loft_obj.copy()
        smooth_loft_obj.data = origin_loft_obj.data.copy()
        smooth_loft_obj.name = origin_loft_obj.name + "Copy"
        smooth_loft_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(smooth_loft_obj)
        if name == '右耳':
            moveToRight(smooth_loft_obj)
        else:
            moveToLeft(smooth_loft_obj)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = smooth_loft_obj
        smooth_loft_obj.hide_set(False)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(smooth_loft_obj.data)
        bm.verts.ensure_lookup_table()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='OriginBridgeVertex')
        origin_verts = [v.index for v in bm.verts if v.select]

        if xiaSheRuYinZi != 0:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            bpy.ops.object.vertex_group_select()
            scale_factor_lower = xiaSheRuYinZi / 100
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)

            ray_cast_obj = bpy.data.objects.get(name + "MouldReset")
            ray_bm = bmesh.new()
            ray_bm.from_mesh(ray_cast_obj.data)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(ray_bm)
            mwi = ray_cast_obj.matrix_world.inverted()
            mwi_start = mwi @ center

            for v in verts:
                v.co = v.co + (v.co - center) * scale_factor_lower
                mwi_end = mwi @ v.co
                mwi_dir = mwi_end - mwi_start

                loc, normal, fidx, distance = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx:
                    actual_dis = (v.co - center).length
                    if actual_dis > distance:
                        for edge in v.link_edges:
                            if edge.other_vert(v).index not in origin_verts:
                                v.co = edge.other_vert(v).co

            # if shangSheRuYinZi != 0:
            #     bpy.ops.transform.resize(value=(scale_factor_lower, scale_factor_lower, scale_factor_lower),
            #                              orient_type='GLOBAL',
            #                              orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
            #                              mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
            #                              proportional_size=1, use_proportional_connected=False,
            #                              use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'},
            #                              use_snap_project=False, snap_target='CENTER', use_snap_self=True,
            #                              use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)`
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.looptools_curve(boundaries=False, influence=100, interpolation='cubic', lock_x=False,
                                         lock_y=False, lock_z=True, regular=True, restriction='none')

        if shangSheRuYinZi != 0:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='ScaleCurveVertex')
            bpy.ops.object.vertex_group_select()
            scale_factor_upper = shangSheRuYinZi / 100
            verts = [v for v in bm.verts if v.select]
            center = sum((v.co for v in verts), Vector()) / len(verts)

            ray_cast_obj = bpy.data.objects.get(name + "MouldReset")
            ray_bm = bmesh.new()
            ray_bm.from_mesh(ray_cast_obj.data)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(ray_bm)
            mwi = ray_cast_obj.matrix_world.inverted()
            mwi_start = mwi @ center

            for v in verts:
                v.co = v.co + (v.co - center) * scale_factor_upper
                mwi_end = mwi @ v.co
                mwi_dir = mwi_end - mwi_start

                loc, normal, fidx, distance = tree.ray_cast(mwi_start, mwi_dir, 2000.0)
                if fidx:
                    actual_dis = (v.co - center).length
                    if actual_dis > distance:
                        for edge in v.link_edges:
                            if edge.other_vert(v).index not in origin_verts:
                                v.co = edge.other_vert(v).co

            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
            # bpy.ops.object.vertex_group_select()
            # selected_verts = [v for v in bm.verts if v.select]
            # for v in selected_verts:
            #     for edge in v.link_edges:
            #         if edge.other_vert(v) not in verts:
            #             other_vert = edge.other_vert(v)
            #             v.co += (other_vert.co - v.co) * shangSheRuYinZi / 100

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='MiddleCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='VERT')

        subdivide_edges(bm, 'ScaleCurveVertex', 'BottomOuterBorderVertex',
                        int((xiaFangYangXian_offset + mianban_offset) / 0.2))
        subdivide_edges(bm, 'ScaleCurveVertex', 'BottomOuterCurveVertex', 6)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='ScaleCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.looptools_curve(boundaries=False, influence=100, interpolation='cubic', lock_x=False,
                                     lock_y=False, lock_z=True, regular=True, restriction='none')
        # 用中间的蓝线进行倒角
        # bpy.ops.object.vertex_group_set_active(group='ScaleCurveVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=80,
        #                    segments=int((xiaFangYangXian_offset + mianban_offset + 1) / 0.2), release_confirm=True)
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_remove_from()
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
        # bpy.ops.object.vertex_group_remove_from()

        bpy.ops.object.mode_set(mode='OBJECT')
        copy_loft_obj_for_battery_plane_cut(smooth_loft_obj)

        main_obj = bpy.data.objects.get(name)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = main_obj
        main_obj.select_set(True)
        smooth_loft_obj.select_set(True)
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        copy_model_for_top_circle_cut()


def bridge_bottom_curve():
    name = bpy.context.scene.leftWindowObj
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bm = bmesh.from_edit_mesh(bpy.data.objects.get(name).data)
    resample_number = len([v for v in bm.verts if v.select])
    bpy.ops.object.mode_set(mode='OBJECT')

    plane_curve = copy_curve_and_resample(name + "PlaneBorderCurve", resample_number, "BottomOuterCurveVertex")
    middle_curve = copy_curve_and_resample(name + "MiddleBaseCurve", resample_number, "MiddleCurveVertex")
    bottom_curve = copy_curve_and_resample(name + "BottomBaseCurve", resample_number, "BottomCurveVertex")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)
    plane_curve.select_set(True)
    middle_curve.select_set(True)
    bottom_curve.select_set(True)
    bpy.ops.object.join()

    # 首先根据两条蓝线桥接，并根据红环的位置切割出中间的用于收缩或扩大的循环边
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.data.objects.get(name).vertex_groups.new(name="LoftVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    # 生成中间用于缩放的循环边
    circle = bpy.data.objects.get(name + "BottomCircle")
    normal = circle.matrix_world.to_3x3() @ circle.data.polygons[0].normal
    if normal.z < 0:
        normal = -normal
    if name == "右耳":
        mianban_offset = bpy.context.scene.mianBanPianYiR
    elif name == "左耳":
        mianban_offset = bpy.context.scene.mianBanPianYiL
    position = circle.location - normal * mianban_offset
    bpy.ops.mesh.bisect(plane_co=position,plane_no=normal)
    bpy.data.objects.get(name).vertex_groups.new(name="ScaleCurveVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_more()
    bpy.data.objects.get(name).vertex_groups.new(name="OriginBridgeVertex")
    bpy.ops.object.vertex_group_assign()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='ScaleCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='MiddleCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomCurveVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='LoftVertex')
    bpy.ops.object.vertex_group_select()
    # 分离出一份物体用于调整平滑度
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != name:
                loft_obj = obj
    if name == "右耳":
        moveToRight(loft_obj)
    elif name == "左耳":
        moveToLeft(loft_obj)
    if bpy.data.objects.get(name + "LoftObjForSmooth") != None:
        bpy.data.objects.remove(bpy.data.objects.get(name + "LoftObjForSmooth"), do_unlink=True)
    loft_obj.name = name + "LoftObjForSmooth"
    loft_obj.hide_set(True)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects.get(name)
    bpy.data.objects.get(name).select_set(True)

    # 根据参数对桥接部分进行倒角平滑
    bevel_loft_part()

    # 细分桥接出的部分并向外挤出
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.object.vertex_group_set_active(group='BottomOuterCurveVertex')
    # bpy.ops.object.vertex_group_select()
    # offset = mianban_offset + xiaFangYangXian_offset
    # subdivide_number = int(offset/0.2)
    # bpy.ops.mesh.bridge_edge_loops(number_cuts=subdivide_number, interpolation='LINEAR')
    # # bpy.ops.mesh.bridge_edge_loops(number_cuts=subdivide_number, interpolation='SURFACE',smoothness=xiaSheRuYinZi / 100,
    # #                                profile_shape_factor=0)
    # smooth_vertex(subdivide_number)
    # copy_model_for_top_circle_cut()
