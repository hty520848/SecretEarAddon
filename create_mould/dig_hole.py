import bpy
import bmesh
import math

from ..tool import moveToRight, convert_to_mesh, subdivide, newColor,set_vert_group,delete_vert_group,extrude_border_by_vertex_groups

template_hole_border_list = [
        [(2.8853964805603027, 0.4101182222366333, -2.189441442489624),
         (3.3255696296691895, 0.36404111981391907, -2.146667242050171),
         (-0.30866485834121704, -2.850980520248413, 1.5502721071243286),
         (2.486687183380127, -11.494535446166992, 1.9102506637573242),
         (2.0880603790283203, -11.500195503234863, 1.8400760889053345),
         (8.901923179626465, -8.247642517089844, 0.358041912317276),
         (8.531580924987793, -8.551643371582031, 0.589188814163208),
         (8.222832679748535, -8.850412368774414, 0.7685110569000244),
         (7.180397033691406, -0.5499098896980286, -1.8933708667755127),
         (-0.31550607085227966, -3.8248534202575684, 1.9483779668807983),
         (-0.2887880802154541, -3.419914484024048, 1.7999277114868164),
         (-0.36505699157714844, -2.3441123962402344, 1.289108395576477),
         (-0.4659070074558258, -1.5442283153533936, 0.8250491619110107),
         (-0.0017805307870730758, 0.15065717697143555, -0.8871479034423828),
         (0.23410017788410187, 0.2778822183609009, -1.22979736328125),
         (1.6470829248428345, 0.4266273081302643, -2.078875780105591),
         (1.9776779413223267, 0.42839565873146057, -2.1318206787109375),
         (4.381636142730713, -11.070513725280762, 2.000833749771118),
         (4.659547328948975, -10.969983100891113, 1.9816408157348633),
         (4.103724956512451, -11.17104434967041, 2.020026683807373),
         (3.629101514816284, -11.303123474121094, 2.0225398540496826),
         (3.116962194442749, -11.41571044921875, 1.9865667819976807),
         (2.8018245697021484, -11.455122947692871, 1.9484087228775024),
         (1.7106260061264038, -11.488141059875488, 1.7549333572387695),
         (1.4035511016845703, -11.44681453704834, 1.6674162149429321),
         (1.0860390663146973, -11.388254165649414, 1.6360796689987183),
         (0.7244064211845398, -11.28388786315918, 1.619248628616333),
         (0.37410053610801697, -11.164377212524414, 1.6131107807159424),
         (-0.09667432308197021, -10.95070743560791, 1.628804087638855),
         (-0.3126576542854309, -10.768959045410156, 1.6460107564926147),
         (-0.5286409258842468, -10.587210655212402, 1.6632177829742432),
         (-0.695584237575531, -10.370667457580566, 1.688022494316101),
         (-0.8625275492668152, -10.15412425994873, 1.7128269672393799),
         (-1.0506280660629272, -9.805254936218262, 1.7556469440460205),
         (-1.125162959098816, -9.51084041595459, 1.8016459941864014),
         (-1.199697732925415, -9.216426849365234, 1.8476449251174927),
         (-1.2311891317367554, -8.9541015625, 1.8881157636642456),
         (-1.2626806497573853, -8.69177532196045, 1.9285866022109985),
         (-1.2681102752685547, -8.424629211425781, 1.9714587926864624),
         (-1.2735399007797241, -8.15748405456543, 2.014331102371216),
         (-1.2463886737823486, -7.889660835266113, 2.0550525188446045),
         (-1.219237208366394, -7.621838569641113, 2.0957741737365723),
         (-1.1295251846313477, -7.105725288391113, 2.1707825660705566),
         (-1.0619677305221558, -6.736398220062256, 2.2123637199401855),
         (-0.9640082716941833, -6.362497806549072, 2.251429796218872),
         (-0.8368555903434753, -5.873559474945068, 2.280885696411133),
         (-0.7448409795761108, -5.555164337158203, 2.2763733863830566),
         (-0.6528263092041016, -5.236769199371338, 2.2718613147735596),
         (-0.5279838442802429, -4.813018321990967, 2.216787576675415),
         (-0.4120212495326996, -4.362090587615967, 2.1189656257629395),
         (-0.3637636601924896, -4.093472480773926, 2.0336718559265137),
         (-0.29872646927833557, -3.1354475021362305, 1.6750998497009277),
         (-0.33686092495918274, -2.597546339035034, 1.4196902513504028),
         (-0.40317437052726746, -2.0589568614959717, 1.128426194190979),
         (-0.4412917196750641, -1.773801565170288, 0.9677438735961914),
         (-0.4905223548412323, -1.314655065536499, 0.6823543906211853),
         (-0.509739339351654, -1.039628267288208, 0.5004377961158752),
         (-0.497809499502182, -0.7501310706138611, 0.2816048562526703),
         (-0.4090016484260559, -0.4032859802246094, -0.049981262534856796),
         (-0.2533641755580902, -0.10116395354270935, -0.43260082602500916),
         (-0.12757234275341034, 0.024746611714363098, -0.6598743796348572),
         (0.4375281035900116, 0.3087237775325775, -1.4138281345367432),
         (0.6409559845924377, 0.33956533670425415, -1.5978587865829468),
         (0.9348462224006653, 0.37115660309791565, -1.7718604803085327),
         (1.228736400604248, 0.40274783968925476, -1.9458621740341187),
         (2.3082728385925293, 0.43016406893730164, -2.184765577316284),
         (2.596834659576416, 0.4201411306858063, -2.187103748321533),
         (3.7878856658935547, 0.32853201031684875, -2.1093435287475586),
         (4.125622749328613, 0.27226701378822327, -2.0813424587249756),
         (4.514798641204834, 0.19113081693649292, -2.051593780517578),
         (5.028316974639893, 0.05931154638528824, -2.0244457721710205),
         (5.409165859222412, -0.04477712884545326, -2.0059077739715576),
         (5.775270938873291, -0.18061143159866333, -1.9749901294708252),
         (6.137139797210693, -0.2762967646121979, -1.9648491144180298),
         (6.632904052734375, -0.3998373746871948, -1.950049638748169),
         (6.906650543212891, -0.4748736321926117, -1.9217102527618408),
         (7.6282877922058105, -0.674257755279541, -1.8384487628936768),
         (7.894538879394531, -0.7500078678131104, -1.791310429573059),
         (8.160789489746094, -0.8257579803466797, -1.744172215461731),
         (8.49102783203125, -0.9521677494049072, -1.676059603691101),
         (8.821266174316406, -1.0785775184631348, -1.6079471111297607),
         (9.219926834106445, -1.2890386581420898, -1.4752562046051025),
         (9.568485260009766, -1.5813112258911133, -1.3301082849502563),
         (9.783793449401855, -1.815122365951538, -1.2288365364074707),
         (9.999101638793945, -2.048933744430542, -1.127564549446106),
         (10.15397834777832, -2.2738194465637207, -1.0625317096710205),
         (10.308856010437012, -2.4987049102783203, -0.9974988698959351),
         (10.454792976379395, -2.7943925857543945, -0.9424135088920593),
         (10.600729942321777, -3.0900802612304688, -0.8873281478881836),
         (10.704858779907227, -3.404905080795288, -0.8421863317489624),
         (10.808988571166992, -3.7197296619415283, -0.7970446348190308),
         (10.868935585021973, -4.088950157165527, -0.7475707530975342),
         (10.852592468261719, -4.3564019203186035, -0.7119873762130737),
         (10.836249351501465, -4.62385368347168, -0.6764039993286133),
         (10.757363319396973, -4.9628586769104, -0.6249297261238098),
         (10.67847728729248, -5.301864147186279, -0.5734554529190063),
         (10.532631874084473, -5.719794273376465, -0.5057758688926697),
         (10.362929344177246, -6.176027774810791, -0.4367324709892273),
         (10.165715217590332, -6.57064151763916, -0.35228556394577026),
         (9.945511817932129, -6.96938943862915, -0.24909700453281403),
         (9.777541160583496, -7.196122169494629, -0.16083399951457977),
         (9.609570503234863, -7.422854900360107, -0.07257097959518433),
         (9.438155174255371, -7.643651008605957, 0.027227934449911118),
         (9.266737937927246, -7.864447116851807, 0.12702684104442596),
         (9.084330558776855, -8.056044578552246, 0.24253438413143158),
         (7.972419738769531, -9.0227632522583, 0.8989120721817017),
         (7.67950439453125, -9.264887809753418, 1.0489065647125244),
         (7.2922515869140625, -9.571784019470215, 1.2182799577713013),
         (7.0709075927734375, -9.731637954711914, 1.3071364164352417),
         (6.849564552307129, -9.891491889953613, 1.3959929943084717),
         (6.440310955047607, -10.144017219543457, 1.5454614162445068),
         (5.99176025390625, -10.392298698425293, 1.6902598142623901),
         (5.557992458343506, -10.602473258972168, 1.7972913980484009),
         (5.135578155517578, -10.77627944946289, 1.900503158569336)]
        ,
        [(5.1540207862854, 10.04935359954834, 0.871610701084137),
         (5.489427089691162, 10.337018013000488, 0.7700390815734863),
         (10.432452201843262, 10.210299491882324, -1.215494155883789),
         (10.83508586883545, 9.93639087677002, -1.3256770372390747),
         (13.219825744628906, 5.946351528167725, -1.9485108852386475),
         (13.287093162536621, 5.643983364105225, -1.9082683324813843),
         (8.978720664978027, 1.5046120882034302, -2.0296261310577393),
         (9.22154712677002, 1.4054243564605713, -1.9772294759750366),
         (7.996615886688232, 2.0006864070892334, -2.191647529602051),
         (7.615887641906738, 2.273918628692627, -2.2123470306396484),
         (13.325121879577637, 5.166855812072754, -1.8150743246078491),
         (4.55108642578125, 5.380911827087402, -1.0070266723632812),
         (4.700413227081299, 5.221728801727295, -1.2026917934417725),
         (11.79575252532959, 8.907498359680176, -1.5496121644973755),
         (12.089133262634277, 8.483067512512207, -1.6471259593963623),
         (12.936256408691406, 3.11427903175354, -1.4707328081130981),
         (13.152559280395508, 6.248720169067383, -1.9887537956237793),
         (6.796470642089844, 3.000788450241089, -2.144437313079834),
         (6.999114990234375, 2.8077967166900635, -2.1787805557250977),
         (7.271368503570557, 2.5607690811157227, -2.1986207962036133),
         (6.5938262939453125, 3.1937804222106934, -2.1100940704345703),
         (6.24948263168335, 3.5237386226654053, -2.0730392932891846),
         (6.077794551849365, 3.72615909576416, -2.0380477905273438),
         (5.906106948852539, 3.928579568862915, -2.0030558109283447),
         (5.62520694732666, 4.278584957122803, -1.9076392650604248),
         (5.441606044769287, 4.480424404144287, -1.7948106527328491),
         (5.258005619049072, 4.6822638511657715, -1.6819820404052734),
         (5.055065631866455, 4.8803324699401855, -1.5369199514389038),
         (4.877739429473877, 5.05103063583374, -1.3698058128356934),
         (4.401759624481201, 5.54009485244751, -0.8113616108894348),
         (4.304929256439209, 5.71158504486084, -0.6243059039115906),
         (4.208098888397217, 5.88307523727417, -0.4372502565383911),
         (4.128162384033203, 6.090743541717529, -0.2571350634098053),
         (4.048225402832031, 6.298411846160889, -0.07701990008354187),
         (3.999915838241577, 6.584788799285889, 0.1389693021774292),
         (3.9689316749572754, 7.007093906402588, 0.3894351124763489),
         (3.997763156890869, 7.459195137023926, 0.6052589416503906),
         (4.073484897613525, 7.895407199859619, 0.7756137251853943),
         (4.203928470611572, 8.370356559753418, 0.9203855395317078),
         (4.315412998199463, 8.73204231262207, 0.9756742715835571),
         (4.440387725830078, 9.063740730285645, 0.9937011003494263),
         (4.624541759490967, 9.357077598571777, 0.9819271564483643),
         (4.886559963226318, 9.722155570983887, 0.9482949376106262),
         (5.924116611480713, 10.566515922546387, 0.6015768051147461),
         (6.204587459564209, 10.67816162109375, 0.48598432540893555),
         (6.50722074508667, 10.795068740844727, 0.35671883821487427),
         (6.978979587554932, 10.914407730102539, 0.15357612073421478),
         (7.3109636306762695, 10.973533630371094, -0.0034595902543514967),
         (7.6470947265625, 10.996980667114258, -0.15865473449230194),
         (8.031455039978027, 11.003750801086426, -0.3337521553039551),
         (8.27637004852295, 10.984748840332031, -0.447441965341568),
         (8.521285057067871, 10.965746879577637, -0.5611317753791809),
         (8.879874229431152, 10.914358139038086, -0.7073158621788025),
         (9.2312593460083, 10.806490898132324, -0.8494518399238586),
         (9.567578315734863, 10.665939331054688, -0.9540994763374329),
         (10.007702827453613, 10.457480430603027, -1.0924991369247437),
         (11.054071426391602, 9.74561595916748, -1.3841454982757568),
         (11.273056983947754, 9.554841995239258, -1.4426140785217285),
         (11.556925773620605, 9.235825538635254, -1.506927251815796),
         (12.233916282653809, 8.2650146484375, -1.710333228111267),
         (12.378698348999023, 8.046961784362793, -1.7735404968261719),
         (12.50847339630127, 7.818454742431641, -1.8293536901474),
         (12.638248443603516, 7.589947700500488, -1.8851667642593384),
         (12.753807067871094, 7.332008361816406, -1.9300791025161743),
         (12.869364738464355, 7.074069499969482, -1.974991798400879),
         (13.030679702758789, 6.640178203582764, -2.000643730163574),
         (13.316868782043457, 4.667758464813232, -1.7134828567504883),
         (13.276873588562012, 4.178807735443115, -1.6424648761749268),
         (13.213165283203125, 3.9063220024108887, -1.5990707874298096),
         (13.149458885192871, 3.633836269378662, -1.555676817893982),
         (13.04285717010498, 3.3740575313568115, -1.5132046937942505),
         (12.784831047058105, 2.8489561080932617, -1.4538333415985107),
         (12.633406639099121, 2.5836334228515625, -1.436933994293213),
         (12.407732009887695, 2.298487663269043, -1.4444390535354614),
         (12.18205738067627, 2.0133419036865234, -1.45194411277771),
         (11.969108581542969, 1.852078914642334, -1.4643185138702393),
         (11.756159782409668, 1.690815806388855, -1.4766929149627686),
         (11.358255386352539, 1.4964816570281982, -1.5159059762954712),
         (10.98694896697998, 1.3830664157867432, -1.5756442546844482),
         (10.615641593933105, 1.2696512937545776, -1.6353824138641357),
         (10.197554588317871, 1.2492377758026123, -1.727401852607727),
         (9.773791313171387, 1.2921645641326904, -1.8356046676635742),
         (9.497668266296387, 1.3487944602966309, -1.9064170122146606),
         (8.735892295837402, 1.60379958152771, -2.0820226669311523),
         (8.35289478302002, 1.7919079065322876, -2.1469480991363525)]

    ]

is_subdivide = False  # 判断曲线是否已经细分，防止曲线的点太少移动时穿模

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


# 对顶点进行排序用于画圈
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
            distance = math.sqrt((vert[0] - now_vert_co[0]) ** 2 + (vert[1] - now_vert_co[1]) ** 2)  # 计算欧几里得距离
            if distance < min_distance:
                min_distance = distance
                now_vert = vert
        if min_distance > 3 and len(unprocessed_vertex) < 0.1 * size:
            finish = True
    return order_border_vert


# 绘制曲线
def draw_border_curve(order_border_co, name, depth):
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
        moveToRight(bpy.context.active_object)

        # 为圆环上色
        newColor('blue', 0, 0, 1, 1, 1)
        bpy.context.active_object.data.materials.append(bpy.data.materials['blue'])
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = active_obj



def darw_cylinder(outer_dig_border, inner_dig_border):
    order_outer_dig_border = get_order_border_vert(outer_dig_border)
    order_inner_dig_border = get_order_border_vert(inner_dig_border)
    order_outer_top = []
    order_outer_bottom = []
    order_inner_top = []
    order_inner_bottom = []

    for v in order_outer_dig_border:
        order_outer_top.append((v[0], v[1], 10))
        order_outer_bottom.append((v[0], v[1], v[2] - 0.2))
    for v in order_inner_dig_border:
        order_inner_bottom.append((v[0], v[1], -5))
        order_inner_top.append((v[0], v[1], v[2] + 1))

    draw_border_curve(order_outer_dig_border, "HoleBorderCurve", 0.18)
    draw_border_curve(order_outer_dig_border, "CylinderOuter", 0)
    draw_border_curve(order_inner_dig_border, "CylinderInner", 0)

    draw_border_curve(order_outer_top, "CylinderOuterTop", 0)
    draw_border_curve(order_outer_bottom, "CylinderOuterBottom", 0)

    draw_border_curve(order_inner_top, "CylinderInnerTop", 0)
    draw_border_curve(order_inner_bottom, "CylinderInnerBottom", 0)
    for obj in bpy.data.objects:
        obj.select_set(False)
    # 转换为网格，用于后续桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterTop"]
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuterTop"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuter"]
    bpy.data.objects["CylinderOuter"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuter"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterBottom"]
    bpy.data.objects["CylinderOuterBottom"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderOuterBottom"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerTop"]
    bpy.data.objects["CylinderInnerTop"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInnerTop"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInner"]
    bpy.data.objects["CylinderInner"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInner"].select_set(False)

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerBottom"]
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.data.objects["CylinderInnerBottom"].select_set(False)

    # 分段桥接出一个圆柱
    # 边合并边设置顶点组用于后续方便选择
    # 上段圆柱合并与桥接
    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderOuterTop"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_top_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuterTop", cylinder_top_index)

    # 合并1，2段
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.data.objects["CylinderOuter"].select_set(True)
    bpy.ops.object.join()
    # 获取第二段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_outer_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuter", cylinder_outer_index)

    # 合并2，3段
    bpy.data.objects["CylinderOuterTop"].select_set(True)
    bpy.data.objects["CylinderOuterBottom"].select_set(True)
    bpy.ops.object.join()
    # 获取第三段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderOuterTop"].data)
    cylinder_inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderOuterBottom", cylinder_inner_index)

    # 依次桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderOuterTop')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderOuterBottom')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')

    # 修改切割圆柱名称
    bpy.data.objects["CylinderOuterTop"].name = "CylinderForOuterDig"
    bpy.data.objects["CylinderForOuterDig"].select_set(False)

    # 下段圆柱合并于桥接

    bpy.context.view_layer.objects.active = bpy.data.objects["CylinderInnerBottom"]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_top_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInnerBottom", cylinder_top_index)

    # 合并1，2段
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.data.objects["CylinderInner"].select_set(True)
    bpy.ops.object.join()
    # 获取第二段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_outer_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInner", cylinder_outer_index)

    # 合并2，3段
    bpy.data.objects["CylinderInnerBottom"].select_set(True)
    bpy.data.objects["CylinderInnerTop"].select_set(True)
    bpy.ops.object.join()
    # 获取第三段顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bm = bmesh.from_edit_mesh(bpy.data.objects["CylinderInnerBottom"].data)
    cylinder_inner_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    set_vert_group("CylinderInnerTop", cylinder_inner_index)

    # 依次桥接
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderInnerTop')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CylinderInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CylinderInnerBottom')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.select_all(action='SELECT')

    # 修改切割圆柱名称
    bpy.data.objects["CylinderInnerBottom"].name = "CylinderForInnerDig"
    bpy.data.objects["CylinderForInnerDig"].select_set(False)

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]
    bpy.data.objects["右耳"].select_set(True)


def boolean_dig():
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigOuterHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigOuterHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigOuterHole"].object = bpy.data.objects["CylinderForOuterDig"]
    bpy.context.object.modifiers["DigOuterHole"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="DigOuterHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_outer_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpOuterBorderVertex", up_outer_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("OuterHoleBorderVertex", up_outer_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigInnerHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigInnerHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigInnerHole"].object = bpy.data.objects["CylinderForInnerDig"]
    bpy.context.object.modifiers["DigInnerHole"].solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="DigInnerHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_inner_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpInnerBorderVertex", up_inner_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("InnerHoleBorderVertex", up_inner_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # 桥接上下边界
    bpy.ops.object.vertex_group_set_active(group='InnerHoleBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.object.vertex_group_set_active(group='OuterHoleBorderVertex')
    bpy.ops.object.vertex_group_select()

    bpy.ops.mesh.bridge_edge_loops()

    # 删除辅助用的物体
    bpy.data.objects.remove(bpy.data.objects["CylinderForInnerDig"], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["CylinderForOuterDig"], do_unlink=True)

    delete_vert_group("InnerHoleBorderVertex")
    delete_vert_group("OuterHoleBorderVertex")

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


# 获取洞边界顶点
def get_hole_border(template_highest_point, template_hole_border, number):
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

        curve_name = 'HoleBorderCurve' + str(number)
        draw_border_curve(order_hole_border_vert, curve_name, 0.18)
        darw_cylinder_bottom(order_hole_border_vert)

        bpy.ops.object.mode_set(mode='OBJECT')


def dig_hole():
    # 复制切割补面完成后的物体
    cur_obj = bpy.data.objects["右耳"]
    duplicate_obj = cur_obj.copy()
    duplicate_obj.data = cur_obj.data.copy()
    duplicate_obj.animation_data_clear()
    duplicate_obj.name = cur_obj.name + "OriginForDigHole"
    bpy.context.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(True)
    moveToRight(duplicate_obj)

    # todo 将来调整模板圆环位置后，要记录调整后的以下两个参数，若有记录，读取记录， 没有则读取套用的模板本身的参数
    template_highest_point = (-10.3681, 2.2440, 12.1771)
    
    global template_hole_border_list
    global is_subdivide
    number = len(template_hole_border_list)
    for template_hole_border in template_hole_border_list:
        get_hole_border(template_highest_point, template_hole_border, number)
        translate_circle_to_cylinder()
        # 创建布尔修改器
        boolean_cut()
        local_curve_name = 'HoleBorderCurve' + str(number)
        local_mesh_name = 'mesh' + local_curve_name
        if not is_subdivide:
            if number == 1:
                is_subdivide = True
            subdivide(local_curve_name, 1)
        convert_to_mesh(local_curve_name, local_mesh_name, 0.18)  # 重新生成网格
        number -= 1

    # for obj in bpy.data.objects:
    #     if obj.name == 'HoleBorderCurve':
    #         obj.name = 'HoleBorderCurve1'
    #         subdivide('HoleBorderCurve1', 3)
    #         convert_to_mesh('HoleBorderCurve1', 'meshHoleBorderCurve1', 0.18)

    #     if obj.name == 'HoleBorderCurve.001':
    #         obj.name = 'HoleBorderCurve2'
    #         subdivide('HoleBorderCurve2', 3)
    #         convert_to_mesh('HoleBorderCurve2', 'meshHoleBorderCurve2', 0.18)

    bpy.context.view_layer.objects.active = bpy.data.objects["右耳"]


def darw_cylinder_bottom(order_hole_border_vert):
    # 该变量存储布尔切割的圆柱体的底部
    cut_cylinder_buttom_co = []
    for vert in order_hole_border_vert:
        # 先直接用原坐标，后续尝试法向向外走一段
        co = vert
        cut_cylinder_buttom_co.append([co[0], co[1], co[2] - 1])
    draw_border_curve(cut_cylinder_buttom_co, "HoleCutCylinderBottom", 0)


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
        TRANSFORM_OT_translate={"value": (0, 0, 12)}
    )
    bpy.ops.mesh.select_all(action='SELECT')
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
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 添加一个修饰器
    modifier = obj.modifiers.new(name="DigHole", type='BOOLEAN')
    bpy.context.object.modifiers["DigHole"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["DigHole"].object = bpy.data.objects["HoleCutCylinderBottom"]
    bpy.context.object.modifiers["DigHole"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="DigHole", single_user=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    up_outer_border_index = [v.index for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')
    # 用于平滑的顶点组，包含所有孔边界顶点
    set_vert_group("UpOuterBorderVertex", up_outer_border_index)
    # 用于上下桥接的顶点组，只包含当前孔边界
    set_vert_group("HoleBorderVertex", up_outer_border_index)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='FACE')

    # 删除辅助用的物体
    bpy.data.objects.remove(bpy.data.objects["HoleCutCylinderBottom"], do_unlink=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    extrude_border_by_vertex_groups("HoleBorderVertex", "UpInnerBorderVertex")
    delete_vert_group("HoleBorderVertex")

def frame_clear_border_list():
    global template_hole_border_list
    template_hole_border_list = [ ]

def frame_set_border_list(border_list):
    global template_hole_border_list
    template_hole_border_list.append(border_list)

def frame_get_border_list():
    global template_hole_border_list
    return template_hole_border_list



'''
    以下函数已弃用
'''


def draw_hole_border_curve(order_border_co, name, depth):
    pass


#
#
# # 删除布尔后多余的部分
def delete_useless_part(cut_cylinder_buttom_co):
    pass
