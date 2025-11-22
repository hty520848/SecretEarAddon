"""
用于存放外壳模块切换不同模板时用到的函数
"""


import bpy
from .shell_eardrum_bottom_fill import generateShell, resetCircleCutPlane, set_circle_location_and_rotation, \
    set_battery_location_and_rotation, createBatteryAndPlane, useMiddleTrous, top_circle_cut, shell_bottom_fill, \
    top_circle_smooth, middle_circle_cut, join_outer_and_inner, shell_battery_plane_cut, copy_model_for_bottom_curve, \
    generate_border_curve
from ..hard_eardrum.hard_eardrum_cut import init_hard_cut
from .shell_canal import reset_shellcanal
from ...tool import moveToRight, moveToLeft
from ...parameters_for_templates import set_right_shell_template_plane_border, set_left_shell_template_plane_border, \
    set_right_shell_template_border, set_left_shell_template_border
from ..parameters_for_create_mould import set_right_shell_plane_border, set_left_shell_plane_border, \
    set_right_shell_border, set_left_shell_border


def change_different_shell_type():
    # 大致流程：回退到进入外壳模块前，根据不同的模板设置不同的参数然后进行切割和桥接
    set_template_parameter()
    # recover_and_delete_ori_obj()
    # generateShell()

    name = bpy.context.scene.leftWindowObj
    battery_plane_snap_curve_obj = bpy.data.objects.get(name + "batteryPlaneSnapCurve")
    plane_border_z = battery_plane_snap_curve_obj.data.vertices[0].co.z

    # 删除不同模板中需要替换的物体
    object_list = [name + 'shellBattery',name + 'batteryPlaneSnapCurve', name + 'shellBatteryPlane',
                   name + "ShellOuterCutBatteryPlane"]
    curve_list = [name + "meshBottomRingBorderR", name + "BottomRingBorderR",
                  name + 'PlaneBorderCurve', name + 'meshPlaneBorderCurve']
    delete_useless_object(object_list)
    delete_useless_object(curve_list)

    # 重置为最原始的模型
    obj = bpy.data.objects.get(name + "OriginForCreateMouldR")
    duplicate_obj = obj.copy()
    duplicate_obj.data = obj.data.copy()
    duplicate_obj.name = name + "OriginForCreateMouldRCopy"
    duplicate_obj.animation_data_clear()
    # 将复制的物体加入到场景集合中
    bpy.context.scene.collection.objects.link(duplicate_obj)
    duplicate_obj.hide_set(False)
    if name == '右耳':
        moveToRight(duplicate_obj)
    elif name == '左耳':
        moveToLeft(duplicate_obj)
    bpy.data.objects.remove(bpy.data.objects.get(name), do_unlink=True)
    duplicate_obj.name = name

    upper_template_border, plane_template_border = get_template_border_parameter()
    for idx, template_border in enumerate(plane_template_border):
        plane_template_border[idx] = (template_border[0], template_border[1], plane_border_z)
    if name == '右耳':
        set_right_shell_template_border(upper_template_border)
        set_right_shell_template_plane_border(plane_template_border)
        set_right_shell_border([])
        set_right_shell_plane_border([])
    elif name == '左耳':
        set_left_shell_template_border(upper_template_border)
        set_left_shell_template_plane_border(plane_template_border)
        set_left_shell_border([])
        set_left_shell_plane_border([])

    # 重新切割上半部分
    if len(upper_template_border) == 0:
        generate_border_curve()
        if name == '右耳':
            bpy.context.scene.curveadjustR = False
        elif name == '左耳':
            bpy.context.scene.curveadjustL = False
    else:
        init_hard_cut(upper_template_border)
        if name == '右耳':
            bpy.context.scene.curveadjustR = True
        elif name == '左耳':
            bpy.context.scene.curveadjustL = True
    copy_model_for_bottom_curve()

    # 根据不同的模板导入不同的电池仓
    createBatteryAndPlane(None, None)
    # 重新切割生成内壁并桥接上下部分
    useMiddleTrous()
    top_circle_cut()
    shell_bottom_fill()
    top_smooth_success = top_circle_smooth()
    middle_smooth_success = middle_circle_cut()
    join_outer_and_inner(top_smooth_success and middle_smooth_success)
    shell_battery_plane_cut()


def recover_and_delete_ori_obj():
    """
    删除现有的电池仓、蓝线吸附平面、底部平面、圆环、蓝线等
    """
    name = bpy.context.scene.leftWindowObj
    recover_flag = False
    for obj in bpy.context.view_layer.objects:
        if obj.name == name + "OriginForCreateMouldR":
            recover_flag = True
            break
    if recover_flag:
        # 删除之前模板中的存在的物体和已经记录的数据
        reset_shellcanal()
        resetCircleCutPlane()
        public_object_list = [name, name + "meshBottomRingBorderR", name + "BottomRingBorderR",
                              name + "meshPlaneBorderCurve", name + "PlaneBorderCurve", name + "shellInnerObj"]
        cubes_obj_list = [name + "cube1", name + "cube2", name + "cube3", name + "move_cube1", name + "move_cube2",
                          name + "move_cube3", name + "littleShellCube1", name + "littleShellCube2",
                          name + "littleShellCube3", name + "receiver", name + "ReceiverPlane",
                          name + "littleShellCube4", name + "littleShellCylinder1", name + "littleShellCylinder2"]
        delete_useless_object(public_object_list)
        delete_useless_object(cubes_obj_list)

        if name == '右耳':
            set_right_shell_template_border([])
            set_right_shell_template_plane_border([])
        elif name == '左耳':
            set_left_shell_template_border([])
            set_left_shell_template_plane_border([])

        # 将最开始复制出来的OriginForCreateMould名称改为模型名称
        obj.hide_set(False)
        obj.name = name

        bpy.context.view_layer.objects.active = obj
        # 恢复完后重新复制一份
        cur_obj = bpy.context.active_object
        duplicate_obj = cur_obj.copy()
        duplicate_obj.data = cur_obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = cur_obj.name + "OriginForCreateMouldR"
        bpy.context.collection.objects.link(duplicate_obj)
        duplicate_obj.hide_set(True)
        if name == '右耳':
            moveToRight(duplicate_obj)
        elif name == '左耳':
            moveToLeft(duplicate_obj)


def set_template_parameter():
    name = bpy.context.scene.leftWindowObj

    battery_loc = None
    battery_rot = None
    battery_obj = bpy.data.objects.get(name + "shellBattery")
    if battery_obj:
        battery_loc = battery_obj.location.copy()
        battery_rot = battery_obj.rotation_euler.copy()
    set_battery_location_and_rotation(name, battery_loc, battery_rot)   # 设置电池仓的位置和旋转角度

    # set_circle_location_and_rotation()  # 设置圆环的位置和旋转角度


def get_template_border_parameter():
    upper_template_border = get_upper_template_border()  # 获得上部蓝线的参数
    plane_template_border = get_plane_template_border()  # 获得下部蓝线的参数
    return upper_template_border, plane_template_border


def get_upper_template_border():
    enum = bpy.context.scene.HuierTypeEnum  # 获取当前选择的模板类型
    name = bpy.context.scene.leftWindowObj
    if enum == 'OP1':  # 默认
        return []
    elif enum == 'OP2':  # ITC
        if name == '右耳':
            global ITC_upper_template_border_right
            return ITC_upper_template_border_right
        elif name == '左耳':
            global ITC_upper_template_border_left
            return ITC_upper_template_border_left
    elif enum == 'OP3':  # HS
        pass


def get_plane_template_border():
    enum = bpy.context.scene.HuierTypeEnum  # 获取当前选择的模板类型
    name = bpy.context.scene.leftWindowObj
    if enum == 'OP1':  # 默认
        return []
    elif enum == 'OP2':  # ITC
        if name == '右耳':
            global ITC_plane_template_border_right
            return ITC_plane_template_border_right
        elif name == '左耳':
            global ITC_plane_template_border_left
            return ITC_plane_template_border_left
    elif enum == 'OP3':  # HS
        pass


def delete_useless_object(need_to_delete_model_name_list):
    for selected_obj in bpy.data.objects:
        if (selected_obj.name in need_to_delete_model_name_list):
            bpy.data.objects.remove(selected_obj, do_unlink=True)
    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=False)


'''
ITC模板
'''
ITC_upper_template_border_right = [(-8.3632, 8.3359, 6.1874), (-8.2323, 8.4704, 6.0139), (-8.1007, 8.6029, 5.8395),
                        (-7.9584, 8.7118, 5.6573), (-7.813, 8.8183, 5.4762), (-7.6508, 8.8559, 5.2825),
                        (-7.4793, 8.8714, 5.0937), (-7.3022, 8.8808, 4.9098), (-7.118, 8.8724, 4.7329),
                        (-6.927, 8.8528, 4.5643), (-6.7318, 8.8385, 4.4), (-6.5327, 8.8329, 4.2398),
                        (-6.3295, 8.8346, 4.0849), (-6.1162, 8.8651, 3.9477), (-5.9022, 8.899, 3.8122),
                        (-5.6865, 8.9338, 3.6796), (-5.4703, 8.9736, 3.5493), (-5.2526, 9.0165, 3.4227),
                        (-5.0321, 9.06, 3.301), (-4.8103, 9.1066, 3.1829), (-4.5882, 9.1577, 3.0673),
                        (-4.3652, 9.2111, 2.9546), (-4.1423, 9.2682, 2.8434), (-3.917, 9.3232, 2.736),
                        (-3.6908, 9.3785, 2.6307), (-3.4639, 9.4342, 2.5272), (-3.2364, 9.4904, 2.4253),
                        (-3.0065, 9.543, 2.327), (-2.7746, 9.5928, 2.2318), (-2.5415, 9.6412, 2.139),
                        (-2.3068, 9.6871, 2.0489), (-2.069, 9.7268, 1.9641), (-1.8291, 9.7615, 1.8831),
                        (-1.5857, 9.7865, 1.8098), (-1.3396, 9.8029, 1.7429), (-1.0931, 9.8187, 1.6771),
                        (-0.8443, 9.8229, 1.6194), (-0.5947, 9.823, 1.5646), (-0.3439, 9.8129, 1.517),
                        (-0.0927, 9.7931, 1.4745), (0.1581, 9.7638, 1.4351), (0.4076, 9.7204, 1.4009),
                        (0.6545, 9.6635, 1.3685), (0.8971, 9.5888, 1.3399), (1.1353, 9.5021, 1.3076),
                        (1.3641, 9.3915, 1.2817), (1.5828, 9.261, 1.2612), (1.7916, 9.1147, 1.2442),
                        (1.9922, 8.9573, 1.2286), (2.1798, 8.7838, 1.2253), (2.3639, 8.6067, 1.2196),
                        (2.5377, 8.4195, 1.2239), (2.7017, 8.224, 1.237), (2.8538, 8.02, 1.26),
                        (2.9988, 7.8111, 1.2849), (3.1315, 7.5946, 1.3137), (3.2563, 7.3728, 1.3371),
                        (3.3515, 7.1382, 1.3716), (3.4228, 6.8951, 1.4048), (3.471, 6.6458, 1.4328),
                        (3.4936, 6.3926, 1.4572), (3.4924, 6.138, 1.478), (3.4742, 5.8838, 1.4936),
                        (3.4322, 5.6324, 1.5116), (3.3836, 5.382, 1.5245), (3.3192, 5.1352, 1.54),
                        (3.2592, 4.887, 1.5502), (3.1973, 4.6393, 1.56), (3.1326, 4.3924, 1.571),
                        (3.0651, 4.1468, 1.5844), (3.0261, 3.8946, 1.5959), (2.9727, 3.6457, 1.6158),
                        (2.9379, 3.3939, 1.642), (2.9089, 3.1426, 1.6776), (2.8849, 2.8925, 1.7238),
                        (2.8589, 2.6449, 1.7814), (2.8354, 2.4, 1.8505), (2.8164, 2.1579, 1.9297),
                        (2.7997, 1.918, 2.0161), (2.7743, 1.6914, 2.1251), (2.7314, 1.5005, 2.2889),
                        (2.6699, 1.3252, 2.4641), (2.5874, 1.1636, 2.6436), (2.4825, 1.0132, 2.8215),
                        (2.3681, 0.8713, 3.0005), (2.244, 0.7388, 3.1794), (2.0909, 0.6167, 3.3435),
                        (1.9302, 0.4991, 3.5036), (1.765, 0.3867, 3.6629), (1.5953, 0.2809, 3.8219),
                        (1.42, 0.1833, 3.9801), (1.2474, 0.0946, 4.1463), (1.0718, 0.0162, 4.3145),
                        (0.8951, -0.0512, 4.4863), (0.7203, -0.1072, 4.6639), (0.5371, -0.1535, 4.8359),
                        (0.3486, -0.1912, 5.0042), (0.1609, -0.2202, 5.1751), (-0.0333, -0.2433, 5.3396),
                        (-0.2327, -0.2612, 5.4984), (-0.4336, -0.2737, 5.6557), (-0.6411, -0.283, 5.8045),
                        (-0.8489, -0.2875, 5.9531), (-1.0601, -0.2889, 6.097), (-1.2767, -0.2884, 6.2325),
                        (-1.4957, -0.2848, 6.3642), (-1.7194, -0.2793, 6.4876), (-1.9454, -0.27, 6.6064),
                        (-2.1754, -0.2569, 6.7168), (-2.4094, -0.2383, 6.8178), (-2.6444, -0.21, 6.9141),
                        (-2.881, -0.1709, 7.0022), (-3.1193, -0.1199, 7.0789), (-3.3573, -0.0555, 7.1457),
                        (-3.5957, 0.0203, 7.1972), (-3.8325, 0.1076, 7.2371), (-4.0657, 0.2066, 7.2704),
                        (-4.2959, 0.3146, 7.2952), (-4.5219, 0.432, 7.3171), (-4.7452, 0.5553, 7.3309),
                        (-4.966, 0.6837, 7.3384), (-5.1826, 0.819, 7.3475), (-5.3969, 0.9581, 7.3529),
                        (-5.6085, 1.1012, 7.3585), (-5.8181, 1.2474, 7.3645), (-6.0265, 1.3951, 7.3674),
                        (-6.2333, 1.545, 7.3762), (-6.4396, 1.6958, 7.3816), (-6.6431, 1.8504, 7.3817),
                        (-6.8445, 2.0076, 7.3819), (-7.0432, 2.1684, 7.3822), (-7.2379, 2.3338, 7.3879),
                        (-7.4282, 2.504, 7.3973), (-7.6133, 2.6801, 7.4042), (-7.7929, 2.8617, 7.4114),
                        (-7.9682, 3.047, 7.4264), (-8.1387, 3.2371, 7.4322), (-8.296, 3.438, 7.4467),
                        (-8.4452, 3.6451, 7.4584), (-8.5867, 3.8578, 7.4665), (-8.72, 4.0758, 7.4704),
                        (-8.8447, 4.2988, 7.4723), (-8.9589, 4.5274, 7.4721), (-9.0596, 4.7622, 7.4685),
                        (-9.1437, 5.0034, 7.4615), (-9.2128, 5.2493, 7.4587), (-9.2632, 5.4996, 7.4483),
                        (-9.2987, 5.7525, 7.4389), (-9.3214, 6.0069, 7.4318), (-9.3329, 6.2622, 7.4276),
                        (-9.3229, 6.5164, 7.4044), (-9.2976, 6.7686, 7.3719), (-9.2605, 7.019, 7.3375),
                        (-9.1923, 7.2518, 7.2573), (-9.1159, 7.4826, 7.1788), (-9.0155, 7.6869, 7.0629),
                        (-8.8982, 7.8591, 6.915), (-8.7668, 7.9752, 6.7291), (-8.6305, 8.0861, 6.5436),
                        (-8.4939, 8.2014, 6.3609)]

ITC_upper_template_border_left = []

# TODO: 后续优化
ITC_plane_template_border_right = [(-1.9092, -1.1074), (-2.5704, -1.1423), (-3.3903, -1.1299),
                         (-4.2591, -1.0712), (-5.118, -0.9819), (-5.9593, -0.8794),
                         (-6.735, -0.7757), (-7.4781, -0.7034), (-8.2048, -0.6858),
                         (-8.9249, -0.7401), (-9.6296, -0.8768), (-10.2857, -1.1052),
                         (-10.8446, -1.443), (-11.2603, -1.911), (-11.5066, -2.5079),
                         (-11.5835, -3.1947), (-11.455, -3.9106), (-11.2477, -4.6152),
                         (-10.9405, -5.2946), (-10.5395, -5.9367), (-10.0552, -6.5389),
                         (-9.5169, -7.1247), (-8.9412, -7.7158), (-8.3301, -8.3243),
                         (-7.7324, -8.9772), (-7.1711, -9.6791), (-6.6503, -10.4159),
                         (-6.1392, -11.1521), (-5.5721, -11.845), (-4.9009, -12.4273),
                         (-4.1373, -12.9346), (-3.2542, -13.2158), (-2.3616, -13.4348),
                         (-1.4687, -13.5498), (-0.6106, -13.5366), (0.1717, -13.4574),
                         (0.9413, -13.2739), (1.7584, -12.8914), (2.59, -12.4003),
                         (3.367, -11.8491), (4.0109, -11.218), (4.5251, -10.5239),
                         (4.8851, -9.7668), (5.1643, -8.9735), (5.3895, -8.1396),
                         (5.5368, -7.2383), (5.6312, -6.3142), (5.6509, -5.4309),
                         (5.5386, -4.6439), (5.3557, -3.9087), (5.136, -3.198),
                         (4.8532, -2.5263), (4.471, -1.9159), (3.9988, -1.3627),
                         (3.4195, -0.885), (2.6964, -0.5302), (1.8636, -0.3338),
                         (1.0098, -0.4008), (0.2106, -0.524), (-0.4739, -0.6993),
                         (-1.0091, -0.8795), (-1.4384, -1.021)]

ITC_plane_template_border_left = []
