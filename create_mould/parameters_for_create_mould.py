'''
该文件用于存储创建模具将会用到的一些全局变量
包括但不限于模板参数
每个变量需要编写get，set函数用于存取
'''


from ..global_manager import global_manager
def register_parameter_for_create_mould_globals():
    global right_hard_eardrum_adjust_border
    global left_hard_eardrum_adjust_border
    global right_soft_eardrum_adjust_border
    global left_soft_eardrum_adjust_border
    global right_frame_style_eardrum_adjust_border
    global left_frame_style_eardrum_adjust_border
    global right_frame_style_hole_border
    global left_frame_style_hole_border
    global right_shell_border
    global left_shell_border
    global right_shell_plane_border
    global left_shell_plane_border
    global_manager.register('right_hard_eardrum_adjust_border', right_hard_eardrum_adjust_border)
    global_manager.register('left_hard_eardrum_adjust_border', left_hard_eardrum_adjust_border)
    global_manager.register('right_soft_eardrum_adjust_border', right_soft_eardrum_adjust_border)
    global_manager.register('left_soft_eardrum_adjust_border', left_soft_eardrum_adjust_border)
    global_manager.register('right_frame_style_eardrum_adjust_border', right_frame_style_eardrum_adjust_border)
    global_manager.register('left_frame_style_eardrum_adjust_border', left_frame_style_eardrum_adjust_border)
    global_manager.register('right_frame_style_hole_border', right_frame_style_hole_border)
    global_manager.register('left_frame_style_hole_border', left_frame_style_hole_border)
    global_manager.register('right_shell_border', right_shell_border)
    global_manager.register('left_shell_border', left_shell_border)
    global_manager.register('right_shell_plane_border', right_shell_plane_border)
    global_manager.register('left_shell_plane_border', left_shell_plane_border)


'''
硬耳膜
'''

# 右耳调整蓝线后的数据
right_hard_eardrum_adjust_border = []


def get_right_hard_eardrum_border():
    global right_hard_eardrum_adjust_border
    return right_hard_eardrum_adjust_border


def set_right_hard_eardrum_border(val):
    global right_hard_eardrum_adjust_border
    right_hard_eardrum_adjust_border = val


# 左耳调整蓝线后的数据
left_hard_eardrum_adjust_border = []


def get_left_hard_eardrum_border():
    global left_hard_eardrum_adjust_border
    return left_hard_eardrum_adjust_border


def set_left_hard_eardrum_border(val):
    global left_hard_eardrum_adjust_border
    left_hard_eardrum_adjust_border = val


'''
软耳膜
'''

# 右耳调整蓝线后的数据
right_soft_eardrum_adjust_border = []


def get_right_soft_eardrum_border():
    global right_soft_eardrum_adjust_border
    return right_soft_eardrum_adjust_border


def set_right_soft_eardrum_border(val):
    global right_soft_eardrum_adjust_border
    right_soft_eardrum_adjust_border = val


# 左耳调整蓝线后的数据
left_soft_eardrum_adjust_border = []


def get_left_soft_eardrum_border():
    global left_soft_eardrum_adjust_border
    return left_soft_eardrum_adjust_border


def set_left_soft_eardrum_border(val):
    global left_soft_eardrum_adjust_border
    left_soft_eardrum_adjust_border = val


'''
框架式耳膜
'''

# 右耳调整蓝线后的数据
right_frame_style_eardrum_adjust_border = []


def get_right_frame_style_eardrum_border():
    global right_frame_style_eardrum_adjust_border
    return right_frame_style_eardrum_adjust_border


def set_right_frame_style_eardrum_border(val):
    global right_frame_style_eardrum_adjust_border
    right_frame_style_eardrum_adjust_border = val


# 左耳调整蓝线后的数据
left_frame_style_eardrum_adjust_border = []


def get_left_frame_style_eardrum_border():
    global left_frame_style_eardrum_adjust_border
    return left_frame_style_eardrum_adjust_border


def set_left_frame_style_eardrum_border(val):
    global left_frame_style_eardrum_adjust_border
    left_frame_style_eardrum_adjust_border = val


right_frame_style_hole_border = []


def get_right_frame_style_hole_border():
    global right_frame_style_hole_border
    return right_frame_style_hole_border


def set_right_frame_style_hole_border(val):
    global right_frame_style_hole_border
    right_frame_style_hole_border = val


left_frame_style_hole_border = []


def get_left_frame_style_hole_border():
    global left_frame_style_hole_border
    return left_frame_style_hole_border


def set_left_frame_style_hole_border(val):
    global left_frame_style_hole_border
    left_frame_style_hole_border = val


'''
常规外壳
'''

right_shell_border = []

def get_right_shell_border():
    global right_shell_border
    return right_shell_border


def set_right_shell_border(val):
    global right_shell_border
    right_shell_border = val


left_shell_border = []

def get_left_shell_border():
    global left_shell_border
    return left_shell_border


def set_left_shell_border(val):
    global left_shell_border
    left_shell_border = val


right_shell_plane_border = []

def get_right_shell_plane_border():
    global right_shell_plane_border
    return right_shell_plane_border


def set_right_shell_plane_border(val):
    global right_shell_plane_border
    right_shell_plane_border = val


left_shell_plane_border = []

def get_left_shell_plane_border():
    global left_shell_plane_border
    return left_shell_plane_border


def set_left_shell_plane_border(val):
    global left_shell_plane_border
    left_shell_plane_border = val
