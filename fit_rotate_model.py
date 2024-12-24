import bpy
import bmesh
from mathutils import Vector
from math import sqrt, asin , acos, pi, degrees
import numpy as np
import datetime


def index_of( element, sequence ):
    for i, e in enumerate( sequence ):
        if e == element: return i
    return -1

# Get vertices in the face order but starting from a given vert
def following_verts_of_vert( vert, face ):
    i0 = index_of( vert, face.verts )
    i1 = (i0 + 1) % 3
    i2 = (i0 + 2) % 3
    return face.verts[i0], face.verts[i1], face.verts[i2]

def search_link( value, links, position ):
    for l in links:
        if l[position] == value: return l
    return None

# Create the oriented ring around vert
def ring_from_vert( vert ):
    vertices = []
    for face in vert.link_faces:
        i0, i1, i2 = following_verts_of_vert( vert, face )
        vertices.append( [i1, i2] )
    result = vertices[0]
    added = True
    while added and len(vertices):
        added = False
        prev = search_link( result[0], vertices, 1 )
        if prev:
            result = [prev[0]] + result
            vertices.remove( prev )
            added = True
        next = search_link( result[-1], vertices, 0 )
        if next and next[1] not in result:
            result.append( next[1] )
            vertices.remove( next )
            added = True
    return result


def curvature_along_edge( vert, other ):
    normal_diff = other.normal - vert.normal
    vert_diff = other.co - vert.co
    return normal_diff.dot( vert_diff ) / vert_diff.length_squared

def angle_between_edges( vert, other1, other2 ):
    edge1 = other1.co - vert.co
    edge2 = other2.co - vert.co
    product = edge1.cross( edge2 )
    sinus = product.length / (edge1.length * edge2.length)
    return asin( min(1.0, sinus) )

def mean_curvature_vert( vert ):
    ring = ring_from_vert( vert )
    ring_curvatures = [curvature_along_edge( vert, other ) for other in ring]
    total_angle = 0.0
    curvature = 0.0
    for i in range(len(ring)-1):
        angle = angle_between_edges( vert, ring[i], ring[i+1] )
        total_angle += angle
        curvature += angle * (ring_curvatures[i] + ring_curvatures[i+1])

    return curvature / (2.0 * total_angle)


def fitAndRotate():
    print("底面对齐之前:",datetime.datetime.now())
    fit()
    print("底面对齐之后:",datetime.datetime.now())
    rotate()
    print("旋转对齐之后:",datetime.datetime.now())

def fit():
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj = bpy.context.active_object

    #将物体几何中心对其到原点
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')


    # 复制一份模板用来删除
    fit_template_obj = obj.copy()
    fit_template_obj.data = obj.data.copy()
    fit_template_obj.animation_data_clear()
    fit_template_obj.name = "FitTemplate"
    bpy.context.collection.objects.link(fit_template_obj)

    obj.select_set(False)
    fit_template_obj.select_set(True)
    bpy.context.view_layer.objects.active = fit_template_obj

    cal_final_co(fit_template_obj,obj)




def cal_final_co(obj,target_obj):

    # 简化网格节省曲率计算时间
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=1)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')


    #将曲率比较小的平面顶点选中
    bm = bmesh.new()
    me = obj.data
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    for vert in bm.verts:
        curvature = mean_curvature_vert( vert )
        if curvature>-0.05 and curvature<0.05:
            vert.select_set(True)
    bm.to_mesh(me)
    bm.free()


    #反选,将曲率比较大的曲面顶点删除
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(obj.data)
    for vert in bm.verts:
        if vert.co[2] > 0:
            vert.select_set(True)
    bpy.ops.mesh.delete(type='VERT')

    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.delete(type='VERT')

    #获取剩余平面中面积最大的平面的索引
    bottom_plane_index = get_bottom_plane(obj)




    #将当前激活物体设置为目标物体
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)
    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj

    #将获取的最大平面与目标物体布尔合并,在目标物体上将最大平面上的顶点选中
    modifierBottomPlane = target_obj.modifiers.new(name="BottomPlane", type='BOOLEAN')
    modifierBottomPlane.object = obj
    modifierBottomPlane.operation = 'UNION'
    modifierBottomPlane.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="BottomPlane", single_user=True)


    #将目标物体上的平面顶点扩大选中并为其创建单独的坐标系
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_more()
    bpy.ops.mesh.select_more()
    bpy.ops.transform.create_orientation(use=True)
    #设置变换时仅影响原点并将创建的的坐标系与全局坐标系对齐
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.tool_settings.use_transform_data_origin = True
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
    bpy.ops.transform.transform(mode='ALIGN')

    #坐标系对齐之后将旋转全置为0,将物体摆正
    target_obj.rotation_euler[0] = 0
    target_obj.rotation_euler[1] = 0
    target_obj.rotation_euler[2] = 0

    #将目标物体上选中的顶点取消选中
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    #将创建的坐标系删除,应用全局坐标系 将之前勾选的变换仅影响原点取消
    bpy.context.scene.tool_settings.use_transform_data_origin = False
    bpy.ops.transform.delete_orientation()
    bpy.context.scene.transform_orientation_slots[0].type = 'GLOBAL'


    #将辅助用于寻找最大平面的物体删除
    # obj.hide_set(True)
    bpy.data.objects.remove(obj, do_unlink=True)



def get_bottom_plane(obj):
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    unprocessed_index =  [v.index for v in bm.verts]

    biggest_area_index = list()
    biggest_face_num = 0
    while unprocessed_index:
        bpy.ops.mesh.select_all(action='DESELECT')
        now_area_first_index = unprocessed_index[0]
        bm.verts[now_area_first_index].select_set(True)
        bpy.ops.mesh.select_linked(delimit=set())

        now_area_index = [v.index for v in bm.verts if v.select]
        now_area_face = [f.index for f in bm.faces if f.select]

        # if len(now_area_index) > len(biggest_area_index):
        if len(now_area_face) > biggest_face_num:

            biggest_area_index = now_area_index
            biggest_face_num = len(now_area_face)

        temp = [index for index in unprocessed_index if index not in now_area_index]
        unprocessed_index = temp

    for i in biggest_area_index:
         bm.verts[i].select_set(True)


    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


    return biggest_area_index

def get_fit_point(bottom_plane_index,obj,order_xyz):
    bottom_plane_vert = list()
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for i in bottom_plane_index:
        bottom_plane_vert.append(bm.verts[i])
    bottom_plane_vert.sort(key=lambda vert: vert.co[order_xyz], reverse=True)
    return bottom_plane_vert[0].index,bottom_plane_vert[-1].index


def get_rotation_matrix_y(p1, p2):
    # 计算两个点的向量
    vec = p2 - p1

    # 计算两个点之间的夹角
    angle_y = -np.arctan2(vec[2], vec[0])  # 逆时针旋转

    # 绕y轴旋转使得两个点的y坐标为0
    rotation_matrix_y = np.array([[np.cos(angle_y), 0, -np.sin(angle_y)],
                                   [0, 1, 0],
                                   [np.sin(angle_y), 0, np.cos(angle_y)]])

    return rotation_matrix_y

def get_rotation_matrix_x(p1, p2):
   # 计算两点之间的向量
    vec = p2 - p1

    # 计算两点之间的夹角
    angle_x = np.arctan2(vec[1], vec[2])  # 逆时针旋转

    # 创建围绕x轴旋转的旋转矩阵
    rotation_matrix_x = np.array([[1, 0, 0],
                                  [0, np.cos(angle_x), np.sin(angle_x)],
                                  [0, -np.sin(angle_x), np.cos(angle_x)]])

    return rotation_matrix_x


def rotate():
    obj = bpy.data.objects.get("ExampleR")       #用于对齐的标准模板
    obj1 = bpy.context.active_object


    #获取标准模板和当前物体中的最高顶点的(x,y)坐标
    p1 = getMaxZVertexCo(obj)
    p2 = getMaxZVertexCo(obj1)
    max_z_y = p2[1]

    #计算二者最高点坐标之间的角度并根据该角度旋转z轴并应用
    angle_red = getRotateAngle(p1,p2)
    if(max_z_y > 0 ):
        obj1.rotation_euler[2] += angle_red
    else:
        obj1.rotation_euler[2] -= angle_red
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)


def getMaxZVertexCo(obj):

    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.mode_set(mode='OBJECT')

    max_z_co = None

    bm = bmesh.new()
    me = obj.data
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    max_z = float('inf')
    max_z_index = None

    for vert in bm.verts:
        if vert.co[2] < max_z:
            max_z = vert.co[2]
            max_z_index = vert.index

    bm.verts[max_z_index].select_set(True)
    max_z_co = [bm.verts[max_z_index].co[0],bm.verts[max_z_index].co[1]]
    print("最大值:",max_z)
    print("坐标",max_z_co)
    bm.to_mesh(me)
    bm.free()

    return max_z_co



def getRotateAngle(p1,p2):
    a1, b1 = p1
    a2, b2 = p2
    dot_product = a1 * a2 + b1 * b2
    magnitude1 = sqrt(a1**2 + b1**2)
    magnitude2 = sqrt(a2**2 + b2**2)

    cos_theta = dot_product / (magnitude1 * magnitude2)
    angle_rad = round(acos(cos_theta),2)
    angle_deg = round(degrees(angle_rad),2)
    print(angle_rad)
    print(angle_deg)


    return angle_rad





