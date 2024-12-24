'''
    此文件为全局参数，需放在调用文件的同级目录下
    使用参数时，在对应文件import该文件即可访问修改
    规则如下
    1.设定变量时，必须给定变量初始值
    2.命名变量时，名字必须使用蛇形命名，并加上对应使用的功能的前缀 如qiege_is_moving (正在移动)，尽量使用英文
    3.每个变量必须有注释说明其作用
    4.定义变量时，按所需功能分块

    禁止使用 a，b，c此类无意义的命名！！！！
    禁止使用 a，b，c此类无意义的命名！！！！
    禁止使用 a，b，c此类无意义的命名！！！！
'''
import bpy

'''
    通用变量
'''

# 设置mirror变量， 用于在两种模式间切换，保证在运行的过程中上一个正在运行的modal退出
is_mirror_context = False  # 是否处在镜像的状态

def set_mirror_context(value):
    global is_mirror_context
    is_mirror_context = value


def get_mirror_context():
    global is_mirror_context
    return is_mirror_context

switch_flag = True   # 标记当前切换是否结束
switch_time = None   # 记录切换结束的时间

def set_switch_time(time):
    global switch_time
    switch_time = time


def get_switch_time():
    global switch_time
    return switch_time


def set_switch_flag(value):
    global switch_flag
    switch_flag = value


def get_switch_flag():
    global switch_flag
    return switch_flag

# 用字典存储各个流程中正在运行未退出的var值
damo_var_list = [1, 2, 3]
jiahou_var_list = [5, 6, 7]
qiege_var_list = [55, 56]
create_mould_var_list = [19, 20, 21]
sound_canal_var_list = [23]
vent_canal_var_list = [26]
handle_var_list = [14]
label_var_list = [41]
casting_var_list = []
support_var_list = [77]
sprue_var_list = [87]
cut_mould_var_list = []
last_damo_var_list = [111, 112, 113]
process_modals = {
    "打磨": damo_var_list,
    "局部加厚": jiahou_var_list,
    "切割": qiege_var_list,
    "创建模具": create_mould_var_list,
    "传声孔": sound_canal_var_list,
    "通气孔": vent_canal_var_list,
    "耳膜附件": handle_var_list,
    "编号": label_var_list,
    "铸造法软耳模": casting_var_list,
    "支撑": support_var_list,
    "排气孔": sprue_var_list,
    "切割模具": cut_mould_var_list,
    "后期打磨": last_damo_var_list
}

# 用字典存储各个流程中各个modal的var值
damo_var_all_list = [1, 2, 3, 4]
jiahou_var_all_list = [5, 6, 7, 8, 9]
qiege_var_all_list = [55, 56, 57, 58]
create_mould_var_all_list = [19, 20, 21]
sound_canal_var_all_list = [23, 24, 25]
vent_canal_var_all_list = [26, 27, 28]
handle_var_all_list = [13, 14, 16]
label_var_all_list = [40, 41, 43]
casting_var_all_list = [100, 101]
support_var_all_list = [76, 77, 78]
sprue_var_all_list = [86, 87, 89]
cut_mould_var_all_list = [90, 91]
last_damo_var_all_list = [111, 112, 113, 114]

var_in_process_modals = {
    "打磨": damo_var_all_list,
    "局部加厚": jiahou_var_all_list,
    "切割": qiege_var_all_list,
    "创建模具": create_mould_var_all_list,
    "传声孔": sound_canal_var_all_list,
    "通气孔": vent_canal_var_all_list,
    "耳膜附件": handle_var_all_list,
    "编号": label_var_all_list,
    "铸造法软耳模": casting_var_all_list,
    "支撑": support_var_all_list,
    "排气孔": sprue_var_all_list,
    "切割模具": cut_mould_var_all_list,
    "后期打磨": last_damo_var_all_list
}

processing_stage_dict = {
    "RENDER": "打磨",
    "OUTPUT": "局部加厚",
    "VIEW_LAYER": "切割",
    "SCENE": "创建模具",
    "WORLD": "传声孔",
    "COLLECTION": "通气孔",
    "OBJECT": "耳膜附件",
    "MODIFIER": "编号",
    "PARTICLES": "铸造法软耳模",
    "PHYSICS": "支撑",
    "CONSTRAINT": "排气孔",
    "MATERIAL": "切割模具",
    "TEXTURE": "后期打磨"
}

def get_process_var_list(process):
    global var_in_process_modals
    return var_in_process_modals[process]


def get_process_finish(var, process):
    global process_modals
    global soft_modal_start
    global shell_modal_start
    if var in process_modals[process] or (process == '创建模具' and (soft_modal_start or shell_modal_start)):
        return True
    else:
        return False


def check_modals_running(var, context):
    global process_modals
    global processing_stage_dict
    process = processing_stage_dict[context]
    if var in process_modals[process]:
        return True
    else:
        return False


"""
创建模具（除了硬耳膜之外的模具类型都存在多个modal并行的情况，统一管理）
"""

soft_modal_start = False   # 软耳模(框架式）modal是否开始
shell_modal_start = False  # 外壳modal是否开始

def set_soft_modal_start(value):
    global soft_modal_start
    soft_modal_start = value


def get_soft_modal_start():
    global soft_modal_start
    return soft_modal_start


def set_shell_modal_start(value):
    global shell_modal_start
    shell_modal_start = value


def get_shell_modal_start():
    global shell_modal_start
    return shell_modal_start


point_qiehuan_modal_start = False
drag_curve_modal_start = False
smooth_curve_modal_start = False

def set_point_qiehuan_modal_start(value):
    global point_qiehuan_modal_start
    point_qiehuan_modal_start = value


def get_point_qiehuan_modal_start():
    global point_qiehuan_modal_start
    return point_qiehuan_modal_start


def set_drag_curve_modal_start(value):
    global drag_curve_modal_start
    drag_curve_modal_start = value


def get_drag_curve_modal_start():
    global drag_curve_modal_start
    return drag_curve_modal_start


def set_smooth_curve_modal_start(value):
    global smooth_curve_modal_start
    smooth_curve_modal_start = value


def get_smooth_curve_modal_start():
    global smooth_curve_modal_start
    return smooth_curve_modal_start

########## 第三方鼠标库相关，第三方鼠标库会造成进程闪退，现弃用 ##########
# from pynput import mouse
# left_mouse_press = False  # 鼠标左键是否按下
# left_mouse_release = False  # 鼠标左键是否释放, 用于局部加厚模块左键释放后执行自动加厚
# right_mouse_press = False  # 鼠标右键是否按下
# middle_mouse_press = False  # 鼠标中键是否按下
# mouse_listener = None  # 添加鼠标监听
#
# mouse_x_y_flag = False    # 鼠标左键按下的时候,通过该标志,记录鼠标按下的位置
# start_update = False      # 调用旋转按钮的时候,是否开始更新号角管的位置信息
#
# def start_mouse_listener():
#     global mouse_listener
#     mouse_listener = mouse.Listener(on_click=on_click)
#     mouse_listener.start()
#
#
# def stop_mouse_listener():
#     global mouse_listener
#     mouse_listener.stop()
#
#
# def on_click(x, y, button, pressed):
#     global left_mouse_press
#     global left_mouse_release
#     global right_mouse_press
#     global middle_mouse_press
#     global mouse_x_y_flag
#     global start_update
#     # 鼠标点击事件处理函数
#     if button == mouse.Button.left and pressed:
#         left_mouse_press = True
#         mouse_x_y_flag = True
#     elif button == mouse.Button.left and not pressed:
#         left_mouse_release = True
#         left_mouse_press = False
#         mouse_x_y_flag = False
#         start_update = False
#
#     if button == mouse.Button.right and pressed:
#         right_mouse_press = True
#     elif button == mouse.Button.right and not pressed:
#         right_mouse_press = False
#
#     if button == mouse.Button.middle and pressed:
#         middle_mouse_press = True
#     elif button == mouse.Button.middle and not pressed:
#         middle_mouse_press = False
#
#
# def get_left_mouse_press():
#     global left_mouse_press
#     return left_mouse_press
#
#
# def get_left_mouse_release():
#     global left_mouse_release
#     return left_mouse_release
#
#
# def get_right_mouse_press():
#     global right_mouse_press
#     return right_mouse_press
#
#
# def get_middle_mouse_press():
#     global middle_mouse_press
#     return middle_mouse_press
#
#
# def set_left_mouse_release(value):
#     global left_mouse_release
#     left_mouse_release = value
#
# def set_mouse_x_y_flag(value):
#     global mouse_x_y_flag
#     mouse_x_y_flag = value
#
#
# def get_mouse_x_y_flag():
#     global mouse_x_y_flag
#     return mouse_x_y_flag
#
#
# def set_start_update(value):
#     global start_update
#     start_update = value
#
#
# def get_start_update():
#     global start_update
#     return start_update

'''
    打磨
'''



'''
    加厚
'''



'''
    切割
'''