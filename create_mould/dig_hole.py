import bpy
import bmesh
import math
from .bottom_ring import *


def re_color(target_object_name, color):
    '''为模型重新上色'''
    # 遍历场景中的所有对象，并根据名称选择目标物体
    for obj in bpy.context.view_layer.objects:
        if obj.name == target_object_name:
            break
    me = obj.data
    # 创建bmesh对象
    bm = bmesh.new()
    # 将网格数据复制到bmesh对象
    bm.from_mesh(me)
    color_lay = bm.verts.layers.float_color["Color"]
    for vert in bm.verts:
        colvert = vert[color_lay]
        colvert.x = color[0]
        colvert.y = color[1]
        colvert.z = color[2]
    bm.to_mesh(me)
    bm.free()


# 获取VIEW_3D区域的上下文
def getOverride():
    area_type = 'VIEW_3D'  # change this to use the correct Area Type context you want to process in
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


def calculate_angle(x, y):
    # 计算原点与给定坐标点之间的角度（弧度）
    angle_radians = math.atan2(y, x)

    # 将弧度转换为角度
    angle_degrees = math.degrees(angle_radians)

    # 将角度限制在 [0, 360) 范围内
    angle_degrees = (angle_degrees + 360) % 360

    return angle_degrees


# 获取洞边界顶点
def get_hole_border():
    # todo 将来调整模板圆环位置后，要记录调整后的以下两个参数，若有记录，读取记录， 没有则读取套用的模板本身的参数
    template_highest_point = (-10.3860, 2.6070, 11.9604)
    template_hole_border = [[7.338379859924316, -5.862774848937988, 0.7202240228652954],
                            [7.849408149719238, -5.707961082458496, 0.40795600414276123],
                            [8.258149147033691, -5.335421085357666, 0.12842300534248352],
                            [8.650062561035156, -4.858377933502197, -0.13991700112819672],
                            [9.196954727172852, -4.649575233459473, -0.39277899265289307],
                            [9.694442749023438, -4.461720943450928, -0.6017889976501465],
                            [10.115421295166016, -4.334434986114502, -0.7619550228118896],
                            [10.25745964050293, -4.012752056121826, -0.8646799921989441],
                            [10.280521392822266, -3.477174997329712, -0.9893149733543396],
                            [10.443737030029297, -2.944866895675659, -1.1533299684524536],
                            [10.51608657836914, -2.3596010208129883, -1.3094420433044434],
                            [10.839353561401367, -1.8106169700622559, -1.4478310346603394],
                            [11.08953857421875, -1.3848520517349243, -1.5355499982833862],
                            [11.429405212402344, -1.1244930028915405, -1.5547709465026855],
                            [11.843839645385742, -0.8071449995040894, -1.5648839473724365],
                            [12.016929626464844, -0.26334699988365173, -1.614657998085022],
                            [12.077463150024414, 0.2156679928302765, -1.6588499546051025],
                            [12.125349044799805, 0.5923720002174377, -1.686553955078125],
                            [12.033475875854492, 0.9820020198822021, -1.6991820335388184],
                            [11.793926239013672, 1.4262330532073975, -1.7181570529937744],
                            [11.235639572143555, 1.7780810594558716, -1.7873239517211914],
                            [10.581174850463867, 2.1221859455108643, -1.8897180557250977],
                            [9.70166015625, 2.2232189178466797, -2.056765079498291],
                            [8.841083526611328, 2.404064893722534, -2.2124550342559814],
                            [8.11883544921875, 2.775521993637085, -2.278057098388672],
                            [7.333474159240723, 3.1163699626922607, -2.309739112854004],
                            [6.57452917098999, 2.4722979068756104, -2.605103015899658],
                            [6.150479793548584, 1.5380769968032837, -2.8771069049835205],
                            [6.198465824127197, 1.116042971611023, -2.9134249687194824],
                            [6.1321330070495605, 0.7766069769859314, -2.9008290767669678],
                            [6.097750186920166, 0.5043280124664307, -2.8221120834350586],
                            [6.079043865203857, 0.2038400024175644, -2.6544439792633057],
                            [6.042016983032227, -0.17445899546146393, -2.3666319847106934],
                            [5.972057819366455, -0.6411150097846985, -1.9470369815826416],
                            [5.891582012176514, -1.0893770456314087, -1.5141030550003052],
                            [5.596625804901123, -1.4150830507278442, -1.1346269845962524],
                            [5.10732889175415, -1.6871709823608398, -0.7331510186195374],
                            [4.5576171875, -2.0143210887908936, -0.21290400624275208],
                            [4.086201190948486, -2.069567918777466, -0.0062790000811219215],
                            [3.758096933364868, -2.2478060722351074, 0.25060999393463135],
                            [3.410011053085327, -2.428014039993286, 0.4730350077152252],
                            [3.1120290756225586, -2.5258359909057617, 0.5893139839172363],
                            [2.801137924194336, -2.3587911128997803, 0.46365800499916077],
                            [2.3733999729156494, -2.196897029876709, 0.35527899861335754],
                            [1.8776520490646362, -2.11257004737854, 0.3363550007343292],
                            [1.3763329982757568, -2.098680019378662, 0.4000459909439087],
                            [0.9107959866523743, -2.1870980262756348, 0.5583469867706299],
                            [0.48207899928092957, -2.3902781009674072, 0.8053200244903564],
                            [0.10060799866914749, -2.660612106323242, 1.077185034751892],
                            [-0.1900549978017807, -2.9030449390411377, 1.2811779975891113],
                            [-0.5458639860153198, -2.9828929901123047, 1.379459023475647],
                            [-0.9545109868049622, -3.059187889099121, 1.4694759845733643],
                            [-1.4072450399398804, -3.067126989364624, 1.535709023475647],
                            [-1.926406979560852, -3.0284690856933594, 1.601835012435913],
                            [-2.512316942214966, -3.0071980953216553, 1.6862620115280151],
                            [-3.227828025817871, -2.991887092590332, 1.808266043663025],
                            [-3.7576959133148193, -2.7804200649261475, 1.91668701171875],
                            [-4.154615879058838, -2.6542561054229736, 2.045593023300171],
                            [-4.515868186950684, -2.560009002685547, 2.2083659172058105],
                            [-4.7881879806518555, -2.5085880756378174, 2.37385892868042],
                            [-5.007626056671143, -2.6476919651031494, 2.5461668968200684],
                            [-5.242921829223633, -2.818492889404297, 2.754564046859741],
                            [-5.311514854431152, -3.1795949935913086, 2.776510000228882],
                            [-5.375397205352783, -3.6186020374298096, 2.7722508907318115],
                            [-5.536499977111816, -4.033476829528809, 2.8427369594573975],
                            [-5.600813865661621, -4.365960121154785, 2.8419361114501953],
                            [-5.660264015197754, -4.681072235107422, 2.821871042251587],
                            [-5.801436901092529, -5.039475917816162, 2.819679021835327],
                            [-5.66968297958374, -5.36105489730835, 2.6266989707946777],
                            [-5.540844917297363, -5.714690208435059, 2.462515115737915],
                            [-5.333346843719482, -6.034933090209961, 2.2956809997558594],
                            [-5.040788173675537, -6.29486083984375, 2.130837917327881],
                            [-4.675589084625244, -6.535347938537598, 1.9788739681243896],
                            [-4.1771111488342285, -6.805477142333984, 1.8375409841537476],
                            [-3.7051639556884766, -7.212640762329102, 1.725443959236145],
                            [-3.2914021015167236, -7.481159210205078, 1.6656759977340698],
                            [-2.71470308303833, -7.596796035766602, 1.6776440143585205],
                            [-1.8389430046081543, -7.73986291885376, 1.7412739992141724],
                            [-1.1002529859542847, -8.155942916870117, 1.7827340364456177],
                            [-0.4658670127391815, -8.312891006469727, 1.873242974281311],
                            [0.047345999628305435, -8.532315254211426, 1.96206796169281],
                            [0.6318119764328003, -8.72334098815918, 2.0937819480895996],
                            [1.1851199865341187, -8.684911727905273, 2.249558925628662],
                            [1.6045290231704712, -8.82608699798584, 2.3289239406585693],
                            [1.9806090593338013, -8.511796951293945, 2.412830114364624],
                            [2.4124081134796143, -8.343935012817383, 2.4641380310058594],
                            [2.6982619762420654, -8.189682006835938, 2.4709908962249756],
                            [2.9044549465179443, -8.265378952026367, 2.4585280418395996],
                            [3.2437970638275146, -8.180220603942871, 2.415637969970703],
                            [3.85475492477417, -8.187894821166992, 2.319901943206787],
                            [4.618321895599365, -7.9768218994140625, 2.15950608253479],
                            [4.878734111785889, -7.460276126861572, 2.072840929031372],
                            [5.135480880737305, -6.999353885650635, 1.9580949544906616],
                            [5.461822986602783, -6.5446319580078125, 1.7880879640579224],
                            [5.867766857147217, -6.156250953674316, 1.5690100193023682],
                            [6.299261093139648, -5.934805870056152, 1.32333505153656]]

    active_obj = bpy.context.active_object
    if active_obj.type == 'MESH':
        # 获取网格数据
        me = active_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        bm2 = bm.copy()
        bm.verts.ensure_lookup_table()

        vert_order_by_z = []
        for vert in bm.verts:
            vert_order_by_z.append(vert)
        # 按z坐标倒序排列
        vert_order_by_z.sort(key=lambda vert: vert.co[2], reverse=True)
        highest_vert = vert_order_by_z[0]

        # 用于计算模板旋转
        # 特别注意，因为导入时候，每个模型的角度不同，所以要将模型最高点（即耳道顶部）x，y轴坐标旋转到模板位置
        angle_template = calculate_angle(template_highest_point[0], template_highest_point[1])
        angle_now = calculate_angle(highest_vert.co[0], highest_vert.co[1])
        rotate_angle = angle_now - angle_template

        dig_border = []  # 被选择的挖孔顶点

        for template_hole_border_point in template_hole_border:  # 通过向z负方向投射找到边界
            # 根据模板旋转的角度，边界顶点也做相应的旋转
            xx = template_hole_border_point[0] * math.cos(math.radians(rotate_angle)) - template_hole_border_point[
                1] * math.sin(math.radians(rotate_angle))
            yy = template_hole_border_point[0] * math.sin(math.radians(rotate_angle)) + template_hole_border_point[
                1] * math.cos(math.radians(rotate_angle))
            origin = (xx, yy, 10)
            direction = (0, 0, -1)
            hit, loc, normal, index = active_obj.ray_cast(origin, direction)
            if hit:
                dig_border.append((loc[0], loc[1], loc[2]))

        order_hole_border_vert = get_order_border_vert(dig_border)

        # 挖洞的边界
        hole_border_co = []
        # 该变量存储布尔切割的圆柱体的底部
        cut_cylinder_buttom_co = []
        for vert in order_hole_border_vert:
            # 先直接用原坐标，后续尝试法向向外走一段
            co = vert
            hole_border_co.append([co[0], co[1], co[2]])
            cut_cylinder_buttom_co.append([co[0], co[1], -3])

        draw_hole_border_curve(order_hole_border_vert, "HoleBorderCurve", 0.18)
        draw_hole_border_curve(cut_cylinder_buttom_co, "HoleCutCylinderBottom", 0)
        bpy.ops.object.mode_set(mode='OBJECT')
        return cut_cylinder_buttom_co


# 对顶点进行排序用于画圈
def get_order_border_vert(selected_verts):
    # 尝试使用距离最近的点
    order_border_vert = []
    now_vert = selected_verts[0]
    unprocessed_vertex = selected_verts  # 未处理顶点
    while len(unprocessed_vertex) > 1:
        order_border_vert.append(now_vert)
        unprocessed_vertex.remove(now_vert)

        min_distance = math.inf
        now_vert_co = now_vert

        for vert in unprocessed_vertex:
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2 + (
                    vert[2] - now_vert_co[2]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert

    return order_border_vert


# 绘制曲线
def draw_hole_border_curve(order_border_co, name, depth):
    active_obj = bpy.context.active_object
    new_node_list = list()
    for i in range(len(order_border_co)):
        if i % 2 == 0:
            new_node_list.append(order_border_co[i])
    # 创建一个新的曲线对象
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # 添加一个曲线样条
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(new_node_list) - 1)
    spline.use_cyclic_u = True

    # 设置每个点的坐标
    for i, point in enumerate(new_node_list):
        spline.points[i].co = (point[0], point[1], point[2], 1)

    # 更新场景
    # 这里可以自行调整数值
    # 解决上下文问题
    override = getOverride()
    with bpy.context.temp_override(**override):
        bpy.context.active_object.data.bevel_depth = depth

        # 为圆环上色
        color_matercal = bpy.data.materials.new(name="HoleBorderColor")
        color_matercal.diffuse_color = (0.0, 0.0, 1.0, 1.0)
        bpy.context.active_object.data.materials.append(color_matercal)

        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj


# 将HoleCutCylinderBottom转化为圆柱用于挖孔
def translate_circle_to_cylinder():
    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name == "HoleCutCylinderBottom":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')
    # 切换回编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill()
    bpy.ops.mesh.extrude_region_move(
        # todo 50为挤出高度，先写死，后续根据边界最高最低点调整
        TRANSFORM_OT_translate={"value": (0, 0, 50)}
    )
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.hide_set(True)


# 使用布尔修改器
def boolean_cut():
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    # 获取活动对象
    obj = bpy.context.active_object

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigHole"].object = bpy.data.objects["HoleCutCylinderBottom"]
    bpy.context.object.modifiers["DigHole"].solver = 'FAST'


# 删除布尔后多余的部分
def delete_useless_part(cut_cylinder_buttom_co):
    # 重新将布尔切割完成的物体转换为网格
    for obj in bpy.data.objects:
        obj.select_set(False)
        # todo 这里要调整名字
        if obj.name == "右耳":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

    # bpy.ops.object.convert(target='MESH')
    bpy.ops.object.modifier_apply(modifier="DigHole",single_user=True)

    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    # 获取活动对象的数据
    obj = bpy.context.active_object
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)

    # 选择对应的顶点
    for vert in bm.verts:
        # 坐标值为float，有精度误差，这里取5位小数的四舍五入，尽量避免删除不该删除的点导致的破面
        # todo -3是因为圆柱底部写死了，后续要调整
        if (round(vert.co[2], 5) == -3):
            vert.select_set(True)

    # 执行删除操作
    bpy.ops.mesh.delete(type='VERT')
    bmesh.update_edit_mesh(mesh)

    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')


# 挖孔
def dig_hole():
    # 复制一份挖孔前的模型以备用
    cur_obj = bpy.context.active_object
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForCreateMould"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)

    # 绘制曲线
    cut_cylinder_buttom_co = get_hole_border()
    # 生成切割用的圆柱体
    translate_circle_to_cylinder()
    # 创建布尔修改器
    boolean_cut()
    # 删除差值后，底部多余的顶点
    delete_useless_part(cut_cylinder_buttom_co)
