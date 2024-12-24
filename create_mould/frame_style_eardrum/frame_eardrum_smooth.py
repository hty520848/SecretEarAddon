import bpy
import bmesh
import datetime
from ...tool import moveToLeft, moveToRight, newColor
import math

#分段存储框架式耳膜平滑中用于Smooth函数的顶点索引
frame_eardrum_outer_vert_index1 = []
frame_eardrum_outer_vert_index2 = []
frame_eardrum_outer_vert_index3 = []

frame_eardrum_inner_vert_index1 = []
frame_eardrum_inner_vert_index2 = []
frame_eardrum_inner_vert_index3 = []

def getFrameEarDrumOuterIndex1():
    global frame_eardrum_outer_vert_index1
    return frame_eardrum_outer_vert_index1

def getFrameEarDrumOuterIndex2():
    global frame_eardrum_outer_vert_index2
    return frame_eardrum_outer_vert_index2

def getFrameEarDrumOuterIndex3():
    global frame_eardrum_outer_vert_index3
    return frame_eardrum_outer_vert_index3

def getFrameEarDrumInnerIndex1():
    global frame_eardrum_inner_vert_index1
    return frame_eardrum_inner_vert_index1

def getFrameEarDrumInnerIndex2():
    global frame_eardrum_inner_vert_index2
    return frame_eardrum_inner_vert_index2

def getFrameEarDrumInnerIndex3():
    global frame_eardrum_inner_vert_index3
    return frame_eardrum_inner_vert_index3


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
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    select_vert = list()
    for index in smooth_index:
        select_vert.append(bm.verts[index])

    for v in select_vert:
        final_co = v.co * 0
        if len(v.link_edges) == 0:
            continue
        for edge in v.link_edges:
            # 确保获取的顶点不是当前顶点
            link_vert = edge.other_vert(v)
            final_co += link_vert.co
        final_co /= len(v.link_edges)
        v.co = v.co + factor * (final_co - v.co)


def frame_eardrum_bottom_fill():
    '''
    对框架式耳膜内外壁的切割底部进行补面
    '''
    #将框架式耳膜内外壁之间的底部分离出来
    name = bpy.context.scene.leftWindowObj
    # main_obj = bpy.data.objects.get(name)
    main_obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
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
    inner_obj.name = name + "FrameBottom"
    if name == '右耳':
        moveToRight(inner_obj)
    elif name == '左耳':
        moveToLeft(inner_obj)

    # 将分离出的底面细分
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(inner_obj.data)
    edges = [e for e in bm.edges if e.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='EDGE')
    for e in edges:
        if not e.is_boundary:
            e.select_set(True)
    bpy.ops.mesh.subdivide(number_cuts=6, ngon=False, quadcorner='INNERVERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 计算框架式耳膜外边缘平滑的分组距离并设置顶点组
    frame_eardrum_outer_smooth = 0
    if (name == "右耳"):
        frame_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiR, 1)
    elif (name == "左耳"):
        frame_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiL, 1)

    # 外边界平滑不为0的时候,将框架式耳膜底面的外边界沿法线挤出向下走使其凸起
    if (frame_eardrum_outer_smooth != 0):
        extrudeOuterVertex(frame_eardrum_outer_smooth)

    #将分离出的底面与框架式耳膜模型合并
    bpy.ops.object.select_all(action='DESELECT')
    inner_obj.select_set(True)
    main_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return main_obj


def extrudeOuterVertex(outer_smooth):
    '''
    将框架式耳膜底部的顶点根据外边缘平滑参数的大小向内走一段距离形成向内的凸起
    '''
    """ 将顶点沿法线凹陷 """
    prev_vertex_index = []  # 记录选中内圈时已经选中过的顶点
    new_vertex_index = []  # 记录新选中的内圈顶点,当无新选中的内圈顶点时,说明底部平面的所有内圈顶点都已经被选中的,结束循环
    cur_vertex_index = []  # 记录扩散区域后当前选中的顶点
    inner_circle_index = -1  # 判断当前选中顶点的圈数,根据圈数确定往里走的距离
    index_normal_dict = dict()  # 由于移动一圈顶点后，剩下的顶点的法向会变，导致突出方向出现问题，所以需要存一下初始的方向

    name = bpy.context.scene.leftWindowObj
    inner_obj = bpy.data.objects.get(name + "FrameBottom")
    obj = inner_obj
    if (obj != None):
        #将底面的外边界点选中
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.mode_set(mode='OBJECT')
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
        while (len(new_vertex_index) != 0 and inner_circle_index <= 4):
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
                # 为了不让平滑边缘出现锐角，前几圈往外突，后几圈才内凹
                #            if inner_circle_index < 3:
                #                dir = -1.5
                #            else:
                dir = -0.6                               #外边缘平滑参数为2时,dir为-0.6
                if(outer_smooth != 0):
                    dir = -0.6 * (outer_smooth / 2)
                #底部细分参数为6,中间有6圈,第0,1,2,3圈step依次增加,第4,5圈再依次降低
                if(inner_circle_index != 4 and inner_circle_index != 5):
                    step = (1 - 0.9 ** (inner_circle_index + 1)) * 2 * dir
                elif(inner_circle_index == 4):
                    step = (1 - 0.9 ** (3)) * 2 * dir
                else:
                    step = (1 - 0.9 ** (2)) * 2 * dir
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


def frame_extrude_smooth_initial():
    '''
    处理框架式耳膜内外边缘切割后桥接得到的底面
    根据面板的内外边缘参数决定底面外边缘向内挤出的距离,对内外边缘进行平滑
    '''

    name = bpy.context.scene.leftWindowObj
    cur_obj = bpy.data.objects.get(name)
    frame_eardrum_smooth_name = name + "FrameEarDrumForSmooth"
    frameeardrum_for_smooth_obj = bpy.data.objects.get(frame_eardrum_smooth_name)
    
    try:
        if(cur_obj != None and frameeardrum_for_smooth_obj != None):
            duplicate_obj = frameeardrum_for_smooth_obj.copy()
            duplicate_obj.data = frameeardrum_for_smooth_obj.data.copy()
            duplicate_obj.animation_data_clear()
            duplicate_obj.name = name + "FrameEarDrumForSmoothing"
            bpy.context.scene.collection.objects.link(duplicate_obj)
            if bpy.context.scene.leftWindowObj == '右耳':
                moveToRight(duplicate_obj)
            else:
                moveToLeft(duplicate_obj)
            bpy.ops.object.select_all(action='DESELECT')
            duplicate_obj.hide_set(False)
            duplicate_obj.select_set(True)
            bpy.context.view_layer.objects.active = duplicate_obj
    
            #对于框架式耳膜切割后形成的内外边缘桥接得到的底面,根据外边缘平滑参数的大小决定底面向内挤出的大小
            obj = frame_eardrum_bottom_fill()
    
            # 设置新的内外区域顶点组
            frame_eardrum_vertex = obj.vertex_groups.get('OuterVertexNew')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('OuterVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='OuterVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='Inner')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            frame_eardrum_vertex = obj.vertex_groups.get('InnerVertexNew')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('InnerVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='InnerVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='Inner')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='Inner')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            # bpy.ops.mesh.select_less()
            # bpy.ops.mesh.select_less()
            # bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            # 将桥接后的顶点细分并将顶点指定到顶点组BottomBorderVertex
            frame_eardrum_vertex = obj.vertex_groups.get('BottomBorderVertex')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomBorderVertex')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomBorderVertex')
            bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            # bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            # 设置新的内外边缘平滑顶点组   原本的边缘顶点组包含了细分后的顶点
            frame_eardrum_vertex = obj.vertex_groups.get('BottomOuterBorderVertexNew')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomOuterBorderVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomOuterBorderVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            frame_eardrum_vertex = obj.vertex_groups.get('BottomInnerBorderVertexNew')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerBorderVertexNew')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerBorderVertexNew')
            bpy.ops.object.mode_set(mode='EDIT')
            # bpy.ops.mesh.select_all(action='DESELECT')
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_select()
            # bpy.ops.mesh.select_more()
            # bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            # bpy.ops.object.vertex_group_deselect()
            # bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            # bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.select_less()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            frame_eardrum_vertex = obj.vertex_groups.get('BottomOuterSmooth')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomOuterSmooth')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomOuterSmooth')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterSmooth')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            frame_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            #定义内边缘平滑顶点组
            frame_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth1')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth1')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth1')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            frame_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth2')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth2')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth2')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterSmooth')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            frame_eardrum_vertex = obj.vertex_groups.get('BottomInnerSmooth3')
            if (frame_eardrum_vertex != None):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_set_active('BottomInnerSmooth3')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
            frame_eardrum_vertex = obj.vertex_groups.new(name='BottomInnerSmooth3')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertex')
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth3')
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.mode_set(mode='OBJECT')
    
            # 调用平滑修改器函数进行平滑,内外边缘平滑
            frame_smooth_initial()

    except:
        print("框架式边缘平滑失败")
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'FrameEarDrumForSmoothing'):
            bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'FrameEarDrumForSmoothing'],
                                    do_unlink=True)
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj + 'FrameEarDrumForSmoothing.001'):
            bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj + 'FrameEarDrumForSmoothing.001'],
                                    do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
        bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(True)
        if bpy.data.materials.get("error_yellow") == None:
            mat = newColor("error_yellow", 1, 1, 0, 0, 1)
            mat.use_backface_culling = False
        bpy.data.objects[name].data.materials.clear()
        bpy.data.objects[name].data.materials.append(bpy.data.materials["error_yellow"])


def frame_smooth_initial():
    name = bpy.context.scene.leftWindowObj
    obj = bpy.data.objects.get(name + "FrameEarDrumForSmoothing")
    #计算框架式耳膜外边缘平滑的分组距离并设置顶点组
    frame_eardrum_outer_smooth = 0
    if (name == "右耳"):
        frame_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiR, 1)
    elif (name == "左耳"):
        frame_eardrum_outer_smooth = round(bpy.context.scene.waiBianYuanSheRuPianYiL, 1)

    select_vert_index = []  # 保存根据底部顶点扩散得到的顶点
    frame_eardrum_vert_index1 = []  # 保存用于底部平滑的顶点
    frame_eardrum_vert_index2 = []  # 保存用于底部平滑的顶点
    frame_eardrum_vert_index3 = []  # 保存用于底部平滑的顶点
    frame_eardrum_vert_index4 = []  # 保存用于底部平滑的顶点
    global frame_eardrum_outer_vert_index1
    global frame_eardrum_outer_vert_index2
    global frame_eardrum_outer_vert_index3
    frame_eardrum_outer_vert_index1 = []  # 保存用于smooth函数边缘平滑的顶点
    frame_eardrum_outer_vert_index2 = []  # 保存用于smooth函数边缘平滑的顶点
    frame_eardrum_outer_vert_index3 = []  # 保存用于smooth函数边缘平滑的顶点

    print("框架式耳膜平滑初始化开始:", datetime.datetime.now())
    # 将底部一圈顶点复制出来用于计算最短距离
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    bottom_outer_obj = bpy.data.objects.get(name + "FrameEarDrumForSmoothing" + ".001")
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
    bpy.ops.object.vertex_group_set_active(group='BottomOuterBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.select_all(action='SELECT')
    for i in range(0,12):
        bpy.ops.mesh.select_more()
    bpy.ops.object.vertex_group_set_active(group='InnerVertexNew')
    bpy.ops.object.vertex_group_deselect()
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
            if(frame_eardrum_outer_smooth < 0.5):
                # 调用平滑函数分段
                if (min_distance < 0.6):
                    frame_eardrum_outer_vert_index1.append(vert_index)
                if (min_distance > 0.4 and min_distance < 0.8):
                    frame_eardrum_outer_vert_index2.append(vert_index)
                if (min_distance < 1):
                    frame_eardrum_outer_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < (0.25 + 0.1)):
                    frame_eardrum_vert_index1.append(vert_index)
                if (min_distance > (0.25 - 0.1) and min_distance < (0.5 + 0.1)):
                    frame_eardrum_vert_index2.append(vert_index)
                if (min_distance > (0.5 - 0.1) and min_distance < (0.75 + 0.1)):
                    frame_eardrum_vert_index3.append(vert_index)
                if (min_distance > (0.75 - 0.1) and min_distance < 1):
                    frame_eardrum_vert_index4.append(vert_index)
            else:
                # 调用平滑函数分段
                if (min_distance < frame_eardrum_outer_smooth * 0.4):
                    frame_eardrum_outer_vert_index1.append(vert_index)
                if (min_distance > frame_eardrum_outer_smooth * 0.3 and min_distance < frame_eardrum_outer_smooth * 0.6):
                    frame_eardrum_outer_vert_index2.append(vert_index)
                if (min_distance < frame_eardrum_outer_smooth):
                    frame_eardrum_outer_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < frame_eardrum_outer_smooth * (0.25 + 0.1)):
                    frame_eardrum_vert_index1.append(vert_index)
                if (min_distance > frame_eardrum_outer_smooth * (0.25 - 0.1) and min_distance < frame_eardrum_outer_smooth * (0.5 + 0.1)):
                    frame_eardrum_vert_index2.append(vert_index)
                if (min_distance > frame_eardrum_outer_smooth * (0.5 - 0.1) and min_distance < frame_eardrum_outer_smooth * (0.75 + 0.1)):
                    frame_eardrum_vert_index3.append(vert_index)
                if (min_distance > frame_eardrum_outer_smooth * (0.75 - 0.1) and min_distance < frame_eardrum_outer_smooth):
                    frame_eardrum_vert_index4.append(vert_index)

    #将用于计算距离的底部平面删除
    bpy.data.objects.remove(bottom_outer_obj, do_unlink=True)

    print("将顶点索引赋值给顶点组:", datetime.datetime.now())
    #根据顶点索引将选中的顶点保存到顶点组中
    vert_index_to_vertex_group(frame_eardrum_vert_index1, "FrameEarDrumOuterVertex1")
    vert_index_to_vertex_group(frame_eardrum_vert_index2, "FrameEarDrumOuterVertex2")
    vert_index_to_vertex_group(frame_eardrum_vert_index3, "FrameEarDrumOuterVertex3")
    vert_index_to_vertex_group(frame_eardrum_vert_index4, "FrameEarDrumOuterVertex4")
    # vert_index_to_vertex_group(select_vert_index, "FrameEarDrumOuterVertex10")

    # 设置矫正平滑顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumOuterVertex1')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumOuterVertex2')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumOuterVertex3')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumOuterVertex4')
    bpy.ops.object.vertex_group_select()
    frame_eardrum_vertex = obj.vertex_groups.get("FrameEarDrumOuterVertex5")
    if (frame_eardrum_vertex != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="FrameEarDrumOuterVertex5")
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    frame_eardrum_vertex = obj.vertex_groups.new(name="FrameEarDrumOuterVertex5")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group="FrameEarDrumOuterVertex5")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    #计算框架式耳膜内边缘平滑的分组距离并设置顶点组
    frame_eardrum_inner_smooth = 0
    if (name == "右耳"):
        frame_eardrum_inner_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYiR, 1)
    elif (name == "左耳"):
        frame_eardrum_inner_smooth = round(bpy.context.scene.neiBianYuanSheRuPianYiL, 1)

    select_vert_index = []  # 保存根据底部顶点扩散得到的顶点
    frame_eardrum_vert_index1 = []  # 保存用于底部平滑的顶点
    frame_eardrum_vert_index2 = []  # 保存用于底部平滑的顶点
    frame_eardrum_vert_index3 = []  # 保存用于底部平滑的顶点
    frame_eardrum_vert_index4 = []  # 保存用于底部平滑的顶点
    global frame_eardrum_inner_vert_index1
    global frame_eardrum_inner_vert_index2
    global frame_eardrum_inner_vert_index3
    frame_eardrum_inner_vert_index1 = []  # 保存用于smooth函数边缘平滑的顶点
    frame_eardrum_inner_vert_index2 = []  # 保存用于smooth函数边缘平滑的顶点
    frame_eardrum_inner_vert_index3 = []  # 保存用于smooth函数边缘平滑的顶点

    print("框架式耳膜平滑初始化开始:", datetime.datetime.now())
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # 将底部一圈顶点复制出来用于计算最短距离
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    bottom_inner_obj = bpy.data.objects.get(name + "FrameEarDrumForSmoothing" + ".001")
    if (name == "右耳"):
        moveToRight(bottom_inner_obj)
    elif (name == "左耳"):
        moveToLeft(bottom_inner_obj)
    # 将该复制出的平面设置为当前激活物体
    obj.select_set(False)
    bottom_inner_obj.select_set(True)
    bpy.context.view_layer.objects.active = bottom_inner_obj
    # 选中底面复制出的一圈顶点并挤出形成一个柱面
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -0.05), "orient_type": 'GLOBAL',
                                                            "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), })
    bpy.ops.object.mode_set(mode='OBJECT')
    # 将激活物体重新设置为左右耳模型
    bottom_inner_obj.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 根据底部顶点组将扩散选中的顶点保存到数组中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerBorderVertexNew')
    bpy.ops.object.vertex_group_select()
    for i in range(0, 12):
        bpy.ops.mesh.select_more()
    bpy.ops.object.vertex_group_set_active(group='OuterVertexNew')
    bpy.ops.object.vertex_group_deselect()
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
    if obj.type == 'MESH':
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for vert_index in select_vert_index:
            vert_co = bm.verts[vert_index].co
            _, closest_co, _, _ = bottom_inner_obj.closest_point_on_mesh(vert_co)
            min_distance = math.sqrt((vert_co[0] - closest_co[0]) ** 2 + (vert_co[1] - closest_co[1]) ** 2 + (
                    vert_co[2] - closest_co[2]) ** 2)
            if(frame_eardrum_inner_smooth < 0.5):
                # 调用平滑函数分段
                if (min_distance < 0.6):
                    frame_eardrum_inner_vert_index1.append(vert_index)
                if (min_distance > 0.4 and min_distance < 0.8):
                    frame_eardrum_inner_vert_index2.append(vert_index)
                if (min_distance < 1):
                    frame_eardrum_inner_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < (0.25 + 0.1)):
                    frame_eardrum_vert_index1.append(vert_index)
                if (min_distance > (0.25 - 0.1) and min_distance < (0.5 + 0.1)):
                    frame_eardrum_vert_index2.append(vert_index)
                if (min_distance > (0.5 - 0.1) and min_distance < (0.75 + 0.1)):
                    frame_eardrum_vert_index3.append(vert_index)
                if (min_distance > (0.75 - 0.1) and min_distance < 1):
                    frame_eardrum_vert_index4.append(vert_index)
            else:
                # 调用平滑函数分段
                if (min_distance < frame_eardrum_inner_smooth * 0.4):
                    frame_eardrum_inner_vert_index1.append(vert_index)
                if (min_distance > frame_eardrum_inner_smooth * 0.3 and min_distance < frame_eardrum_inner_smooth * 0.6):
                    frame_eardrum_inner_vert_index2.append(vert_index)
                if (min_distance < frame_eardrum_inner_smooth):
                    frame_eardrum_inner_vert_index3.append(vert_index)
                # 调用平滑修改器分段
                if (min_distance < frame_eardrum_inner_smooth * (0.25 + 0.1)):
                    frame_eardrum_vert_index1.append(vert_index)
                if (min_distance > frame_eardrum_inner_smooth * (0.25 - 0.1) and min_distance < frame_eardrum_inner_smooth * (0.5 + 0.1)):
                    frame_eardrum_vert_index2.append(vert_index)
                if (min_distance > frame_eardrum_inner_smooth * (0.5 - 0.1) and min_distance < frame_eardrum_inner_smooth * (0.75 + 0.1)):
                    frame_eardrum_vert_index3.append(vert_index)
                if (min_distance > frame_eardrum_inner_smooth * (0.75 - 0.1) and min_distance < frame_eardrum_inner_smooth):
                    frame_eardrum_vert_index4.append(vert_index)

    # 将用于计算距离的底部平面删除
    bpy.data.objects.remove(bottom_inner_obj, do_unlink=True)

    print("将顶点索引赋值给顶点组:", datetime.datetime.now())
    # 根据顶点索引将选中的顶点保存到顶点组中
    vert_index_to_vertex_group(frame_eardrum_vert_index1, "FrameEarDrumInnerVertex1")
    vert_index_to_vertex_group(frame_eardrum_vert_index2, "FrameEarDrumInnerVertex2")
    vert_index_to_vertex_group(frame_eardrum_vert_index3, "FrameEarDrumInnerVertex3")
    vert_index_to_vertex_group(frame_eardrum_vert_index4, "FrameEarDrumInnerVertex4")

    # 设置矫正平滑顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumInnerVertex1')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumInnerVertex2')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumInnerVertex3')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='FrameEarDrumInnerVertex4')
    bpy.ops.object.vertex_group_select()
    frame_eardrum_vertex = obj.vertex_groups.get("FrameEarDrumInnerVertex5")
    if (frame_eardrum_vertex != None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="FrameEarDrumInnerVertex5")
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    frame_eardrum_vertex = obj.vertex_groups.new(name="FrameEarDrumInnerVertex5")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group="FrameEarDrumInnerVertex5")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    #外边缘平滑
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomOuterSmooth')
    bpy.ops.object.vertex_group_select()
    if(frame_eardrum_outer_smooth != 0):
        bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=int(frame_eardrum_outer_smooth * 2), wait_for_input=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    #内边缘平滑
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth')
    bpy.ops.object.vertex_group_select()
    if (frame_eardrum_inner_smooth != 0):
        bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=int(frame_eardrum_inner_smooth * 2), wait_for_input=False)
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth1')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.vertices_smooth(factor=frame_eardrum_inner_smooth/4, repeat=8, wait_for_input=False)
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth2')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.vertices_smooth(factor=frame_eardrum_inner_smooth/5, repeat=8, wait_for_input=False)
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_set_active(group='BottomInnerSmooth3')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.vertices_smooth(factor=frame_eardrum_inner_smooth/7, repeat=8, wait_for_input=False)
    bpy.ops.object.mode_set(mode='OBJECT')


    # print("创建修改器:", datetime.datetime.now())
    # modifier_name = "FrameEarDrumModifier10"
    # target_modifier = None
    # for modifier in obj.modifiers:
    #     if modifier.name == modifier_name:
    #         target_modifier = modifier
    # if (target_modifier == None):
    #     modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier10", type='SMOOTH')
    #     modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumOuterVertex10"
    #     target_modifier = modifierFrameEarDrumSmooth
    # target_modifier.factor = 0.8
    # target_modifier.iterations = int(frame_eardrum_outer_smooth * 3)
    # bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier10")
    # 创建平滑修改器,指定框架式耳膜外边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier4"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier4", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumOuterVertex4"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.4
    target_modifier.iterations = int(frame_eardrum_outer_smooth)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier4")

    # 创建平滑修改器,指定框架式耳膜外边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier3"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier3", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumOuterVertex3"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.4
    target_modifier.iterations = int(frame_eardrum_outer_smooth * 3)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier3")

    # 创建平滑修改器,指定框架式耳膜外边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier2"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier2", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumOuterVertex2"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.5
    target_modifier.iterations = int(frame_eardrum_outer_smooth * 5)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier2")

    # 创建平滑修改器,指定框架式耳膜外边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier1"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier1", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumOuterVertex1"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.6
    target_modifier.iterations = int(frame_eardrum_outer_smooth * 7)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier1")

    # 创建平滑修改器,指定框架式耳膜内边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier4"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier4", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumInnerVertex4"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.3
    target_modifier.iterations = int(frame_eardrum_inner_smooth)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier4")

    # 创建平滑修改器,指定框架式耳膜内边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier3"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier3", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumInnerVertex3"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.3
    target_modifier.iterations = int(frame_eardrum_inner_smooth * 3)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier3")

    # 创建平滑修改器,指定框架式耳膜内边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier2"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier2", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumInnerVertex2"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.4
    target_modifier.iterations = int(frame_eardrum_inner_smooth * 7)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier2")

    # 创建平滑修改器,指定框架式耳膜内边缘平滑顶点组
    modifier_name = "FrameEarDrumModifier1"
    target_modifier = None
    for modifier in obj.modifiers:
        if modifier.name == modifier_name:
            target_modifier = modifier
    if (target_modifier == None):
        modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier1", type='SMOOTH')
        modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumInnerVertex1"
        target_modifier = modifierFrameEarDrumSmooth
    target_modifier.factor = 0.6
    target_modifier.iterations = int(frame_eardrum_inner_smooth * 10)
    bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier1")

    if frame_eardrum_outer_smooth != 0:
        # 创建矫正平滑修改器,指定框架式耳膜外边缘平滑顶点组
        modifier_name = "FrameEarDrumModifier5"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier5", type='CORRECTIVE_SMOOTH')
            modifierFrameEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
            modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumOuterVertex5"
            modifierFrameEarDrumSmooth.scale = 0
            target_modifier = modifierFrameEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = 10
        bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier5")
        print("调用smooth平滑函数:", datetime.datetime.now())
        bpy.ops.object.mode_set(mode='EDIT')
        if(frame_eardrum_outer_smooth < 0.5):
            # for i in range(7):
            #     laplacian_smooth(getFrameEarDrumOuterIndex1(), 0.4 * frame_eardrum_outer_smooth)
            # for i in range(5):
            #     laplacian_smooth(getFrameEarDrumOuterIndex2(), 0.6 * frame_eardrum_outer_smooth)
            for i in range(1):
                laplacian_smooth(getFrameEarDrumOuterIndex3(), 0.8 * frame_eardrum_outer_smooth)
        else:
            # for i in range(7):
            #     laplacian_smooth(getFrameEarDrumOuterIndex1(), 0.6)
            # for i in range(5):
            #     laplacian_smooth(getFrameEarDrumOuterIndex2(), 0.5)
            for i in range(1):
                laplacian_smooth(getFrameEarDrumOuterIndex3(), 0.4)
        bpy.ops.object.mode_set(mode='OBJECT')

    if frame_eardrum_inner_smooth != 0:
        # 创建矫正平滑修改器,指定框架式耳膜内边缘平滑顶点组
        modifier_name = "FrameEarDrumModifier5"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:
                target_modifier = modifier
        if (target_modifier == None):
            modifierFrameEarDrumSmooth = obj.modifiers.new(name="FrameEarDrumModifier5", type='CORRECTIVE_SMOOTH')
            modifierFrameEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
            modifierFrameEarDrumSmooth.vertex_group = "FrameEarDrumInnerVertex5"
            modifierFrameEarDrumSmooth.scale = 0
            target_modifier = modifierFrameEarDrumSmooth
        target_modifier.factor = 0.5
        target_modifier.iterations = 5
        bpy.ops.object.modifier_apply(modifier="FrameEarDrumModifier5")
        print("调用smooth平滑函数:", datetime.datetime.now())
        bpy.ops.object.mode_set(mode='EDIT')
        if (frame_eardrum_inner_smooth < 0.5):
            # for i in range(7):
            #     laplacian_smooth(getFrameEarDrumInnerIndex1(), 0.4 * frame_eardrum_inner_smooth)
            # for i in range(5):
            #     laplacian_smooth(getFrameEarDrumInnerIndex2(), 0.6 * frame_eardrum_inner_smooth)
            for i in range(2):
                laplacian_smooth(getFrameEarDrumInnerIndex3(), 0.8 * frame_eardrum_inner_smooth)
        else:
            # for i in range(7):
            #     laplacian_smooth(getFrameEarDrumInnerIndex1(), 0.6)
            # for i in range(5):
            #     laplacian_smooth(getFrameEarDrumInnerIndex2(), 0.5)
            for i in range(2):
                laplacian_smooth(getFrameEarDrumInnerIndex3(), 0.4)
        bpy.ops.object.mode_set(mode='OBJECT')
    print("平滑初始化结束:", datetime.datetime.now())

    #平滑成功之后,用平滑后的物体替换左/右耳
    bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
    obj.name = bpy.context.scene.leftWindowObj
