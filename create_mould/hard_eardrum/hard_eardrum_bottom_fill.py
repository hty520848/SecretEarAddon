import bpy
import mathutils
import bmesh
import math
import numpy as np
from ...tool import moveToRight, moveToLeft
import copy
import datetime
from mathutils import Vector


hard_eardrum_vert_index5 = []           #分段存储硬耳膜平滑中用于Smooth函数的顶点索引
hard_eardrum_vert_index6 = []           #分段存储硬耳膜平滑中用于Smooth函数的顶点索引
hard_eardrum_vert_index7 = []           #分段存储硬耳膜平滑中用于Smooth函数的顶点索引


def getIndex5():
    global hard_eardrum_vert_index5
    return hard_eardrum_vert_index5

def getIndex6():
    global hard_eardrum_vert_index6
    return hard_eardrum_vert_index6

def getIndex7():
    global hard_eardrum_vert_index7
    return hard_eardrum_vert_index7

def hard_bottom_fill():
    main_obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.remove_doubles(threshold=0.5)
    bm = bmesh.from_edit_mesh(main_obj.data)
    origin_face_num = len(bm.faces)

    # 补面前复制一个物体用于还原
    name = main_obj.name
    obj_reset = bpy.data.objects.get(name+'BottomFillReset')
    if (obj_reset):
        bpy.data.objects.remove(obj_reset, do_unlink=True)

    duplicate_obj = main_obj.copy()
    duplicate_obj.data = main_obj.data.copy()
    duplicate_obj.name = name + 'BottomFillReset'
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)

    border_verts = [v for v in bm.verts if v.select]
    count = int(len(border_verts) / 2) + 2
    ori_count = count



    # 选取起始点和相邻点
    bpy.ops.mesh.select_all(action='DESELECT')
    start_vert = min(border_verts, key=lambda v: v.co.y)
    start_vert.select = True

    for edge in start_vert.link_edges:
        for vert in edge.verts:
            if vert != start_vert and vert in border_verts:
                vert.select = True

    # 先补一个面,再循环补面
    bpy.ops.mesh.edge_face_add()
    start_vert.select = False
    while (count > 0):
        bpy.ops.mesh.edge_face_add()
        count = count - 1

    new_face_num = len(bm.faces)
    # if origin_face_num == new_face_num:
    #     print("没补面")
    #     bpy.ops.mesh.select_all(action='DESELECT')
    #     bpy.ops.object.mode_set(mode='OBJECT')
    #     return

    # 补面失败，还原到补面前
    if(new_face_num - origin_face_num < ori_count-3 ):
        print('补面不完整')
        print('新增面数',new_face_num - origin_face_num)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # 删除原有物体
        bpy.data.objects.remove(main_obj, do_unlink=True)
        obj_reset = bpy.data.objects.get(name+'BottomFillReset')
        obj_reset.name = name
        obj_reset.hide_set(False)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_reset
        obj_reset.select_set(True)
        return

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')
    for obj in bpy.data.objects:
        if obj.select_get() and obj != main_obj:
            inner_obj = obj
            break
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = inner_obj
    inner_obj.name = main_obj.name + "底部边界"

    # 细分
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    edges = [e for e in bm.edges if e.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='EDGE')
    for e in edges:
        if not e.is_boundary:
            e.select_set(True)
    bpy.ops.mesh.subdivide(number_cuts=12, ngon=False, quadcorner='INNERVERT')

    # 平滑
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    verts = [v for v in bm.verts if v.select]
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='VERT')
    for v in verts:
        if v.is_boundary:
            v.select_set(True)
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in verts:
        if not v.is_boundary:
            v.select_set(True)
    inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')

    for i in range(0, 30):
        laplacian_smooth(inner_index, 1)

    # 选中最外圈的顶点
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.select_mode(type='VERT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    verts = [v for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    for v in verts:
        if not v.is_boundary:
            v.select_set(True)
    # 2024/05/28 这行简化网格导致了破面
    # bpy.ops.mesh.remove_doubles(threshold=0.5)
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 沿法线凹陷
    concavity_extend_list = [0.5, 0.8, 1.3, 2]
    prev_vertex_index = []  # 记录选中内圈时已经选中过的顶点
    new_vertex_index = []  # 记录新选中的内圈顶点,当无新选中的内圈顶点时,说明底部平面的所有内圈顶点都已经被选中的,结束循环
    cur_vertex_index = []  # 记录扩散区域后当前选中的顶点
    inner_circle_index = -1  # 判断当前选中顶点的圈数,根据圈数确定往里走的距离
    index_normal_dict = dict()  # 由于移动一圈顶点后，剩下的顶点的法向会变，导致突出方向出现问题，所以需要存一下初始的方向

    obj = inner_obj
    if (obj != None):
        # 初始化集合
        if obj.type == 'MESH':
            # 获取当前激活物体的网格数据
            me = obj.data
            # 创建bmesh对象
            bm = bmesh.new()
            # 将网格数据复制到bmesh对象
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            # 根据面板参数设置偏移值
            for vert in bm.verts:
                if (vert.select == True):
                    prev_vertex_index.append(vert.index)
                index_normal_dict[vert.index] = vert.normal[0:3]
            bm.to_mesh(me)
            bm.free()
        # 初始化集合使得其能够进入while循环
        new_vertex_index.append(0)
        # print("初始化长度:", len(prev_vertex_index))
        # print("初始化长度:", len(new_vertex_index))
        while (len(new_vertex_index) != 0):
            # while(inner_circle_index <= 6):
            inner_circle_index += 1
            # print("当前圈数:", inner_circle_index)
            # 根据当前选中顶点扩散得到新选中的顶点
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_more()
            bpy.ops.object.mode_set(mode='OBJECT')
            # 根据之前记录的选中顶点数组将之前顶点取消选中,使得只有新增的内圈顶点被选中
            cur_vertex_index.clear()
            if obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                for vert in bm.verts:
                    if (vert.select == True):
                        cur_vertex_index.append(vert.index)
                bm.to_mesh(me)
                bm.free()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            result = [x for x in cur_vertex_index if x not in prev_vertex_index]
            # 将集合new_vertex_index_set清空并将新选中的内圈顶点保存到集合中
            new_vertex_index.clear()
            new_vertex_index = result
            if obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                for vert_index in new_vertex_index:
                    vert = bm.verts[vert_index]
                    vert.select_set(True)
                bm.to_mesh(me)
                bm.free()
            # 新选中的内圈顶点沿着法线向内放缩
            if obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                # todo 为了不让平滑边缘出现锐角，前几圈往外突，后几圈才内凹
                if inner_circle_index < 3:
                    dir = -1.5
                else:
                    dir = 1
                step = (1 - 0.9 ** (inner_circle_index + 1)) * 5 * dir
                # 根据面板参数设置偏移值
                for vert in bm.verts:
                    if (vert.select == True):
                        dir = index_normal_dict[vert.index]
                        vert.co[0] -= dir[0] * step
                        vert.co[1] -= dir[1] * step
                        vert.co[2] -= dir[2] * step
                bm.to_mesh(me)
                bm.free()
            # 更新集合prev_vertex_index_set
            prev_vertex_index.extend(new_vertex_index)
            # print("新增顶点数:", len(new_vertex_index))
            # print("保存之前的顶点数:", len(prev_vertex_index))

    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='OBJECT')
    me = obj.data
    bm = bmesh.new()
    me = obj.data
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        if not v.is_boundary:
            v.select_set(True)
    inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    for _ in range(0, 10):
        laplacian_smooth(inner_index, 1)

    # 合并两个物体
    main_obj.select_set(True)
    inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    # bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.context.scene.leftWindowObj == '右耳':
        pianyi = bpy.context.scene.yingErMoSheRuPianYiR
    else:
        pianyi = bpy.context.scene.yingErMoSheRuPianYiL
    if pianyi > 0.4:
        hard_eardrum_smooth()
    else:
        # 平滑初始化
        smooth_initial()

def hard_eardrum_smooth():
    # 根据物体ForSmooth复制出一份物体用来平滑回退,每次调整平滑参数都会根据该物体重新复制出一份物体用于平滑
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    hard_eardrum_smooth_name = name + "HardEarDrumForSmooth"
    hard_eardrum_smooth_obj = bpy.data.objects.get(hard_eardrum_smooth_name)
    if (hard_eardrum_smooth_obj != None):
        bpy.data.objects.remove(hard_eardrum_smooth_obj, do_unlink=True)
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = obj.name + "HardEarDrumForSmooth"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)

    try:
        name = bpy.context.scene.leftWindowObj + 'HardEarDrumForSmooth'
        obj = bpy.data.objects[name]
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.name = obj.name + "Copy"
        duplicate_obj.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate_obj)
        if bpy.context.scene.leftWindowObj == '右耳':
            moveToRight(duplicate_obj)
        else:
            moveToLeft(duplicate_obj)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = duplicate_obj
        duplicate_obj.select_set(True)

        # 保留平滑前的边界用于倒角
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.separate(type='SELECTED')
        # for obj in bpy.data.objects:
        #     if obj.select_get() and obj != duplicate_obj:
        #         origin_border_obj = obj
        #         break
        # origin_border_obj.name = name + "OriginBorder"
        # bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = duplicate_obj
        # duplicate_obj.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        if bpy.context.scene.leftWindowObj == '右耳':
            pianyi = bpy.context.scene.yingErMoSheRuPianYiR
        else:
            pianyi = bpy.context.scene.yingErMoSheRuPianYiL
        bpy.ops.hardeardrum.smooth(width=pianyi, center_border_group_name='BottomOuterBorderVertex')

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
        duplicate_obj.name = bpy.context.scene.leftWindowObj

    except:
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'HardEarDrumForSmoothCopy'):
            bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'HardEarDrumForSmoothCopy'], do_unlink=True)
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'HardEarDrumForSmoothCopyBridgeBorder'):
            bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'HardEarDrumForSmoothCopyBridgeBorder'], do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
        bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        print('底部平滑失败')


def pipe_cut():
    # 分离出管道
    bpy.ops.mesh.separate(type='SELECTED')

    active_obj = bpy.context.active_object

    for obj in bpy.data.objects:
        if obj.select_get() and obj != active_obj:
            pipe_obj = obj
            break

    # 清理自相交网格
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    pipe_obj.select_set(True)
    bpy.context.view_layer.objects.active = pipe_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.delete(type='FACE')
    # bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')

    # 切割
    bpy.ops.object.mode_set(mode='OBJECT')
    pipe_obj.select_set(True)
    active_obj.select_set(True)
    bpy.context.view_layer.objects.active = active_obj

    # 使用布尔插件
    bpy.ops.object.booltool_auto_difference()
    bpy.ops.object.mode_set(mode='EDIT')


def bridge_border(pianyi):
    origin_border_obj = bpy.data.objects[bpy.context.scene.leftWindowObj + "HardEarDrumForSmoothOriginBorder"]
    main_obj = bpy.context.active_object
    # 保存当前顶点组
    main_obj.vertex_groups.new(name="StepCutOuter")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.object.vertex_group_select()

    # 分离出内外边界进行桥接
    bm = bmesh.from_edit_mesh(main_obj.data)
    bm.verts.ensure_lookup_table()
    all_border_vert_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.verts[all_border_vert_index[0]].select = True

    bpy.ops.mesh.select_linked(delimit=set())
    part_1_index = [v.index for v in bm.verts if v.select]
    part_2_index = [v.index for v in bm.verts if not v.select]
    if len(part_1_index) > len(part_2_index):
        inner_part_set = set(part_2_index)
        outer_part_set = set(part_1_index)
    else:
        inner_part_set = set(part_1_index)
        outer_part_set = set(part_2_index)
    bpy.ops.mesh.select_all(action='DESELECT')

    for v in bm.verts:
        if v.is_boundary and v.index in inner_part_set:
            v.select_set(True)
    bpy.ops.mesh.remove_doubles(threshold=0.1)
    inner_border_index = [v.index for v in bm.verts if v.select]
    inner_border_num = len(inner_border_index)

    main_obj.vertex_groups.new(name="StepCutInner")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='StepCutOuter')
    bpy.ops.object.vertex_group_remove_from()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='StepCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')

    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != main_obj.name:
                outer_border_obj = obj
    outer_border_obj.select_set(False)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='StepCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_more()
    main_obj.vertex_groups.new(name="StepCutOuterBridge")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    resample_mesh(outer_border_obj, inner_border_num)
    # 重新设置顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    outer_border_obj.vertex_groups.new(name="StepCutOuter")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')

    # 重采样最初的边界
    resample_mesh(origin_border_obj, inner_border_num)
    # 重新设置顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    origin_border_obj.vertex_groups.new(name="BottomOuterBorderVertex")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')


    # 合并四个物体
    bpy.ops.object.select_all(action='DESELECT')
    main_obj.select_set(True)
    outer_border_obj.select_set(True)
    origin_border_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()

    # 进行桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='StepCutOuterBridge')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='StepCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='StepCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
    bpy.ops.mesh.looptools_bridge(cubic_strength=1, interpolation='cubic', loft=False, loft_loop=False, min_width=0,
                                  mode='shortest', remove_faces=True, reverse=False, segments=1, twist=0)
    bpy.ops.mesh.select_mode(type='VERT')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bevel(offset=pianyi * 0.8, segments=int(pianyi / 0.1))
    bpy.ops.object.mode_set(mode='OBJECT')

    # 删除创建的顶点组
    step_cut_inner_group = main_obj.vertex_groups.get("StepCutInner")
    if (step_cut_inner_group != None):
        main_obj.vertex_groups.remove(step_cut_inner_group)
    step_cut_outer_group = main_obj.vertex_groups.get("StepCutOuter")
    if (step_cut_outer_group != None):
        main_obj.vertex_groups.remove(step_cut_outer_group)
    step_cut_bridge_group = main_obj.vertex_groups.get("StepCutOuterBridge")
    if (step_cut_bridge_group != None):
        main_obj.vertex_groups.remove(step_cut_bridge_group)


def resample_mesh(obj, resample_num):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='CURVE')
    # 添加几何节点修改器
    modifier = obj.modifiers.new(name="Resample", type='NODES')
    bpy.ops.node.new_geometry_node_group_assign()

    node_tree = bpy.data.node_groups[0]
    node_links = node_tree.links

    input_node = node_tree.nodes[0]
    output_node = node_tree.nodes[1]

    resample_node = node_tree.nodes.new("GeometryNodeResampleCurve")
    resample_node.inputs[2].default_value = resample_num

    node_links.new(input_node.outputs[0], resample_node.inputs[0])
    node_links.new(resample_node.outputs[0], output_node.inputs[0])

    bpy.ops.object.convert(target='MESH')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.1)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.node_groups.remove(node_tree)


def smooth_initial():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    hard_eardrum_smooth_name = name + "HardEarDrumForSmooth"
    hard_eardrum_smooth_obj = bpy.data.objects.get(hard_eardrum_smooth_name)
    if (hard_eardrum_smooth_obj != None):
        bpy.data.objects.remove(hard_eardrum_smooth_obj, do_unlink=True)
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = obj.name + "HardEarDrumForSmooth"
    duplicate_obj.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj)
    else:
        moveToLeft(duplicate_obj)
    duplicate_obj.hide_set(True)

    name = bpy.context.scene.leftWindowObj
    hardeardrum_for_smooth_obj = bpy.data.objects.get(name + "HardEarDrumForSmooth")
    # 根据HardEarDrumForSmooth复制出一份物体用于平滑操作
    duplicate_obj1 = hardeardrum_for_smooth_obj.copy()
    duplicate_obj1.data = hardeardrum_for_smooth_obj.data.copy()
    duplicate_obj1.name = hardeardrum_for_smooth_obj.name + "HardEarDrumSmoothing"
    duplicate_obj1.animation_data_clear()
    bpy.context.scene.collection.objects.link(duplicate_obj1)
    if bpy.context.scene.leftWindowObj == '右耳':
        moveToRight(duplicate_obj1)
    else:
        moveToLeft(duplicate_obj1)
    bpy.ops.object.select_all(action='DESELECT')
    duplicate_obj1.hide_set(False)
    duplicate_obj1.select_set(True)
    bpy.context.view_layer.objects.active = duplicate_obj1

    obj = duplicate_obj1

    hard_eardrum_smooth = 0
    if (name == "右耳"):
        hard_eardrum_smooth = round(bpy.context.scene.yingErMoSheRuPianYiR, 1)
    elif (name == "左耳"):
        hard_eardrum_smooth = round(bpy.context.scene.yingErMoSheRuPianYiL, 1)

    select_vert_index = []  # 保存根据底部顶点扩散得到的顶点
    hard_eardrum_vert_index1 = []  # 保存用于底部平滑的顶点
    hard_eardrum_vert_index2 = []  # 保存用于底部平滑的顶点
    hard_eardrum_vert_index3 = []  # 保存用于底部平滑的顶点
    hard_eardrum_vert_index4 = []  # 保存用于底部平滑的顶点
    global hard_eardrum_vert_index5
    global hard_eardrum_vert_index6
    global hard_eardrum_vert_index7
    hard_eardrum_vert_index5 = []  # 保存用于smooth函数边缘平滑的顶点
    hard_eardrum_vert_index6 = []  # 保存用于smooth函数边缘平滑的顶点
    hard_eardrum_vert_index7 = []  # 保存用于smooth函数边缘平滑的顶点

    if (obj != None):
        print("硬耳膜平滑初始化开始:", datetime.datetime.now())
        # 将底部一圈顶点复制出来用于计算最短距离
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        bottom_outer_obj = bpy.data.objects.get(name + "HardEarDrumForSmooth" + "HardEarDrumSmoothing" + ".001")
        if (name == "右耳"):
            moveToRight(bottom_outer_obj)
        elif (name == "左耳"):
            moveToLeft(bottom_outer_obj)
        #将该复制出的平面设置为当前激活物体
        obj.select_set(False)
        bottom_outer_obj.select_set(True)
        bpy.context.view_layer.objects.active = bottom_outer_obj
        #选中底面复制出的一圈顶点并挤出形成一个柱面
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -0.05), "orient_type": 'GLOBAL',"orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),})
        bpy.ops.object.mode_set(mode='OBJECT')
        #将激活物体重新设置为左右耳模型
        bottom_outer_obj.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj


        # 根据底部顶点组将扩散选中的顶点保存到数组中
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.select_all(action='SELECT')
        for i in range(0,12):
            bpy.ops.mesh.select_more()
        bpy.ops.object.mode_set(mode='OBJECT')
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            for vert in bm.verts:
                if (vert.select == True):
                    select_vert_index.append(vert.index)
            bm.to_mesh(me)
            bm.free()
        print("开始计算距离:", datetime.datetime.now())
        # 根据距离选中顶点
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        hard_eardrum_vert_index = []
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            for vert_index in select_vert_index:
                vert_co = bm.verts[vert_index].co
                _, closest_co, _, _ = bottom_outer_obj.closest_point_on_mesh(vert_co)
                min_distance = math.sqrt((vert_co[0] - closest_co[0]) ** 2 + (vert_co[1] - closest_co[1]) ** 2 + (
                        vert_co[2] - closest_co[2]) ** 2)
                if(hard_eardrum_smooth < 1):
                    # 调用平滑函数分段
                    if (min_distance < 0.6):
                        hard_eardrum_vert_index5.append(vert_index)
                    if (min_distance >   0.4 and min_distance <   0.8):
                        hard_eardrum_vert_index6.append(vert_index)
                    if (min_distance < 1):
                        hard_eardrum_vert_index7.append(vert_index)
                    # 调用平滑修改器分段
                    if (min_distance <   (0.25 + 0.1)):
                        hard_eardrum_vert_index1.append(vert_index)
                    if (min_distance >   (0.25 - 0.1) and min_distance <   (0.5 + 0.1)):
                        hard_eardrum_vert_index2.append(vert_index)
                    if (min_distance >   (0.5 - 0.1) and min_distance <   (0.75 + 0.1)):
                        hard_eardrum_vert_index3.append(vert_index)
                    if (min_distance > (0.75 - 0.1) and min_distance < 1):
                        hard_eardrum_vert_index4.append(vert_index)
                else:
                    # 调用平滑函数分段
                    if (min_distance < hard_eardrum_smooth * 0.4):
                        hard_eardrum_vert_index5.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * 0.3 and min_distance < hard_eardrum_smooth * 0.6):
                        hard_eardrum_vert_index6.append(vert_index)
                    if (min_distance < hard_eardrum_smooth):
                        hard_eardrum_vert_index7.append(vert_index)
                    # 调用平滑修改器分段
                    if (min_distance < hard_eardrum_smooth * (0.25 + 0.1)):
                        hard_eardrum_vert_index1.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * (0.25 - 0.1) and min_distance < hard_eardrum_smooth * (0.5 + 0.1)):
                        hard_eardrum_vert_index2.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * (0.5 - 0.1) and min_distance < hard_eardrum_smooth * (0.75 + 0.1)):
                        hard_eardrum_vert_index3.append(vert_index)
                    if (min_distance > hard_eardrum_smooth * (0.75 - 0.1) and min_distance < hard_eardrum_smooth):
                        hard_eardrum_vert_index4.append(vert_index)

        #将用于计算距离的底部平面删除
        bpy.data.objects.remove(bottom_outer_obj, do_unlink=True)

        print("将顶点索引赋值给顶点组:", datetime.datetime.now())
        #根据顶点索引将选中的顶点保存到顶点组中
        vert_index_to_vertex_group(hard_eardrum_vert_index1, "HardEarDrumOuterVertex1")
        vert_index_to_vertex_group(hard_eardrum_vert_index2, "HardEarDrumOuterVertex2")
        vert_index_to_vertex_group(hard_eardrum_vert_index3, "HardEarDrumOuterVertex3")
        vert_index_to_vertex_group(hard_eardrum_vert_index4, "HardEarDrumOuterVertex4")

        # 设置矫正平滑顶点组
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumOuterVertex1')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumOuterVertex2')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumOuterVertex3')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='HardEarDrumOuterVertex4')
        bpy.ops.object.vertex_group_select()
        hard_eardrum_vertex = obj.vertex_groups.get("HardEarDrumOuterVertex5")
        if (hard_eardrum_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group="HardEarDrumOuterVertex5")
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        hard_eardrum_vertex = obj.vertex_groups.new(name="HardEarDrumOuterVertex5")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="HardEarDrumOuterVertex5")
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        print("创建修改器:", datetime.datetime.now())

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier4"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier4", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex4"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier4")

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier3"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier3", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex3"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth * 3)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier3")

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier2"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier2", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex2"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth * 7)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier2")

        # 创建平滑修改器,指定硬耳膜平滑顶点组
        modifier_name = "HardEarDrumModifier1"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier1", type='SMOOTH')
            modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex1"
            target_modifier = modifierHardEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = int(hard_eardrum_smooth * 10)
        bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier1")

        if hard_eardrum_smooth != 0:
            # 创建矫正平滑修改器,指定硬耳膜平滑顶点组
            modifier_name = "HardEarDrumModifier5"
            target_modifier = None
            for modifier in obj.modifiers:
                if modifier.name == modifier_name:
                    target_modifier = modifier
            if (target_modifier == None):
                modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier5", type='CORRECTIVE_SMOOTH')
                modifierHardEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
                modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex5"
                modifierHardEarDrumSmooth.scale = 0
                target_modifier = modifierHardEarDrumSmooth
            target_modifier.factor = 0.5
            target_modifier.iterations = 5
            bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier5")
            print("调用smooth平滑函数:", datetime.datetime.now())
            if(hard_eardrum_smooth < 1):
                for i in range(7):
                    laplacian_smooth(getIndex5(), 0.4 * hard_eardrum_smooth)
                for i in range(5):
                    laplacian_smooth(getIndex6(), 0.6 * hard_eardrum_smooth)
                for i in range(2):
                    laplacian_smooth(getIndex7(), 0.8 * hard_eardrum_smooth)
            else:
                for i in range(7):
                    laplacian_smooth(getIndex5(), 0.3)
                for i in range(5):
                    laplacian_smooth(getIndex6(), 0.3)
                for i in range(2):
                    laplacian_smooth(getIndex7(), 0.3)
        print("平滑初始化结束:", datetime.datetime.now())



        #平滑成功之后,用平滑后的物体替换左/右耳
        bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
        obj.name = bpy.context.scene.leftWindowObj





def vert_index_to_vertex_group(vert_index_list, vertex_group_name):
    '''
    针对当前激活的物体,根据给出的顶点组名称,创建一个顶点组,并将顶点索引中的顶点加入到该顶点组中
    '''

    # 将满足距离的顶点选中:
    obj = bpy.context.active_object
    if(obj != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            for vert_index in vert_index_list:
                vert = bm.verts[vert_index]
                vert.select_set(True)
            bm.to_mesh(me)
            bm.free()
        # 根据底部边缘顶点扩大范围得到用于底部平滑的顶点组
        hard_eardrum_vertex = obj.vertex_groups.get(vertex_group_name)
        if (hard_eardrum_vertex != None):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group=vertex_group_name)
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        hard_eardrum_vertex = obj.vertex_groups.new(name=vertex_group_name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group=vertex_group_name)
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')


def laplacian_smooth(smooth_index, factor):
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='OBJECT')
    me = obj.data
    bm = bmesh.new()
    me = obj.data
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    select_vert = list()
    for index in smooth_index:
        select_vert.append(bm.verts[index])

    ori_co_dict = dict()
    for v in select_vert:
        ori_co_dict[v.index] = v.co

    for v in select_vert:
        final_co = v.co * 0
        for edge in v.link_edges:
            # 确保获取的顶点不是当前顶点
            link_vert = edge.other_vert(v)
            final_co += link_vert.co
        final_co /= len(v.link_edges)
        v.co = v.co + factor * (final_co - v.co)

    bm.to_mesh(obj.data)
    bm.free()


