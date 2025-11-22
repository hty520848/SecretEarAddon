import bpy.props

from .damo import get_is_dialog, set_previous_thicknessL, set_previous_thicknessR
from .jiahou import *
from .create_tip.qiege import *
from .create_tip.cut_mould import get_color_mode
from .label import *
from .support import *
from .create_mould.parameters_for_create_mould import set_right_soft_eardrum_border, set_left_soft_eardrum_border, \
    get_left_soft_eardrum_border, get_right_soft_eardrum_border, set_right_frame_style_eardrum_border, \
    set_left_frame_style_eardrum_border, get_left_frame_style_eardrum_border, get_right_frame_style_eardrum_border
from .create_mould.soft_eardrum.thickness_and_fill import reset_and_refill, re_smooth, soft_smooth_initial, \
    soft_smooth_initial1, soft_extrude_smooth_initial, refill_after_cavity_smooth, refill_after_upper_smooth, \
    reset_to_after_cut, set_finish, draw_cut_plane_upper, soft_offset_cut_smooth, soft_step_modifier_smooth
from .create_mould.frame_style_eardrum.frame_style_eardrum_dig_hole import dig_hole, reset_and_dig_and_refill
from .create_mould.frame_style_eardrum.frame_fill_inner_face import recover_and_refill
from .create_mould.frame_style_eardrum.frame_eardrum_smooth import frame_extrude_smooth_initial
from .create_mould.hard_eardrum.hard_eardrum_bottom_fill import smooth_initial, hard_eardrum_smooth
from .create_mould.shell_eardrum.shell_canal import updateshellCanalState, updateshellCanalOffset, \
    updateshellCanalDiameter, updateshellCanalThickness
from .create_mould.shell_eardrum.shell_eardrum_bottom_fill import useMiddleTrous, update_top_circle_cut, \
    update_middle_circle_offset, update_middle_circle_cut, update_xiafangxian, update_mianban, \
    update_top_circle_smooth, update_middle_circle_smooth, reset_after_bottom_curve_change, update_smooth_factor, \
    adjust_region_width, adjust_thickness, change_battery_shape
from .create_mould.shell_eardrum.shell_eardrum_template import change_different_shell_type
from .create_mould.create_mould import recover, get_type, set_type, create_mould_cut, create_mould_fill
from .sound_canal import initial_hornpipe, update_hornpipe_offset, update_hornpipe_enum, convert_soundcanal
from .vent_canal import convert_ventcanal
from .casting import castingThicknessUpdate
from .parameter import update_template_selection
from .back_and_forward import record_state, get_is_processing_undo_redo
from .tool import track_time, reset_time_tracker

import os

import datetime

font_info = {
    "font_id": 0,
    "handler": None,
}


def My_Properties():
    # 全局变量,多个模块的文件共享该全局变量,各个模式的按钮都会有一个var值,当该按钮处于其对应的值时,会运行其操作符,不再其对应值时,会自动结束该操作符
    # 默认var值为0,各个操作符都未启动
    # todo:整理每个模块中var的值，按照模块顺序+按钮顺序编号（比如打磨加厚为11，局部加厚缩小为22），保证不重复
    # todo:考虑重置modal是否需要设置var值
    # 打磨模块:       打磨加厚按钮: 1        打磨打薄按钮:  2      打磨平滑按钮:  3       打磨重置按钮:  4
    # 局部加厚模块:    局部加厚扩大区域: 5    局部加厚缩小区域: 6    局部加厚加厚: 7    局部加厚提交: 8   局部加厚重置: 9
    # 切割模块:       环切modal: 55   侧切modal: 56   完成切割: 57   重置切割: 58
    # 创建模具模块:    点加蓝线: 19     拖拽蓝线: 20   平滑蓝线:  21   重置模具: 32    确认模具: 31
    # 通气孔模块:      通气孔鼠标行为modal: 23    通气孔提交: 24   通气孔重置: 25
    # 传声孔模块:      传声孔鼠标行为modal: 26    传声孔提交: 27   传声孔重置: 28
    # 附件模块:        附件重置: 13    附件初始化双击: 15   添加附件: 14(防止开启多个modal: 18)   附件单步撤回和前进: 17  附件提交: 16
    # 附件模块:        附件重置: 13    附件鼠标行为: 14   附件提交: 16
    # 字体模块:        字体重置: 40    字体初始化双击: 42   添加字体: 41(防止开启多个modal: 45)   字体单步撤回和前进: 44  字体提交: 43
    # 字体模块:        字体重置: 40    字体鼠标行为: 41   字体提交: 43
    # 铸造法模块:      铸造法重置: 100    铸造法提交: 101
    # 支撑模块:       支撑重置: 76    支撑提交: 78     支撑鼠标行为:77
    # 排气孔模块:     排气孔重置: 86  排气孔初始化双击: 88   添加排气孔: 87(防止开启多个modal: 81)  附件单步撤回和前进: 80  排气孔提交: 89
    # 排气孔模块:      排气孔重置: 86    排气孔鼠标行为: 87   排气孔提交: 89
    # 切割磨具模块:    切割模具重置: 90    切割模具完成: 91
    # 后期打磨模块:    打磨加厚按钮: 111       打磨打薄按钮:  112     打磨平滑按钮:  113      打磨重置按钮:  114
    bpy.types.Scene.var = bpy.props.IntProperty(
        name="var", default=0, description="每个模块的按钮都会对应一个var值,用于结束按钮的modal"
    )

    bpy.types.Scene.pressfinish = bpy.props.BoolProperty(
        name="pressfinish", default=False)

    # 记录左右窗口中的物体是左耳还是右耳
    bpy.types.Scene.leftWindowObj = bpy.props.StringProperty(name="",
                                                             description="左窗口物体",
                                                             default="右耳",
                                                             maxlen=1024)

    bpy.types.Scene.rightWindowObj = bpy.props.StringProperty(name="",
                                                              description="右窗口物体",
                                                              default="左耳",
                                                              maxlen=1024)

    # 记录当前操作窗口的活动集合
    bpy.types.Scene.activecollecion = bpy.props.StringProperty(name="",
                                                               description="活动集合",
                                                               default="右耳",
                                                               maxlen=1024)

    bpy.types.Scene.activecollecionMirror = bpy.props.StringProperty(name="",
                                                                     description="镜像活动集合",
                                                                     default="右耳",
                                                                     maxlen=1024)

    # 打磨操作属性      蜡厚度，局部蜡厚度限制，最大蜡厚度，最小蜡厚度
    bpy.types.Scene.laHouDUR = bpy.props.FloatProperty(
        name="laHouDUR", min=-2.0, max=2.0, step=5,
        description="调整蜡厚度的大小", update=Houdu)
    bpy.types.Scene.laHouDUL = bpy.props.FloatProperty(
        name="laHouDUL", min=-2.0, max=2.0, step=5,
        description="调整蜡厚度的大小", update=Houdu)
    bpy.types.Scene.localLaHouDuR = bpy.props.BoolProperty(
        name="localLaHouDu", default=False, update=record_prop_value)
    bpy.types.Scene.maxLaHouDuR = bpy.props.FloatProperty(
        name="maxLaHouDu", min=-1.0, max=1.0, step=1, default=0.5,
        description="最大蜡厚度的值", update=record_prop_value)
    bpy.types.Scene.minLaHouDuR = bpy.props.FloatProperty(
        name="minLaHouDu", min=-1.0, max=1.0, step=1, default=-0.5,
        description="最小蜡厚度的值", update=record_prop_value)
    bpy.types.Scene.damo_circleRadius_R = bpy.props.FloatProperty(
        name="damo_circleRadius", default=50)
    bpy.types.Scene.damo_strength_R = bpy.props.FloatProperty(
        name="damo_strength_R", default=0.5)
    bpy.types.Scene.damo_scale_strength_R = bpy.props.FloatProperty(
        name="damo_scale_strength_R", min=0.1, max=10, step=10, default=1,
        description="调整笔刷的强度", update=scale_strength)
    bpy.types.Scene.localLaHouDuL = bpy.props.BoolProperty(
        name="localLaHouDuL", default=False, update=record_prop_value)
    bpy.types.Scene.maxLaHouDuL = bpy.props.FloatProperty(
        name="maxLaHouDuL", min=-1.0, max=1.0, step=1, default=0.5,
        description="最大蜡厚度的值", update=record_prop_value)
    bpy.types.Scene.minLaHouDuL = bpy.props.FloatProperty(
        name="minLaHouDuL", min=-1.0, max=1.0, step=1, default=-0.5,
        description="最小蜡厚度的值", update=record_prop_value)
    bpy.types.Scene.damo_circleRadius_L = bpy.props.FloatProperty(
        name="damo_circleRadius_L", default=50)
    bpy.types.Scene.damo_strength_L = bpy.props.FloatProperty(
        name="damo_strength_L", default=0.5)
    bpy.types.Scene.damo_scale_strength_L = bpy.props.FloatProperty(
        name="damo_scale_strength_L", min=0.1, max=10, step=10, default=1,
        description="调整笔刷的强度", update=scale_strength)

    # 局部或整体加厚    偏移值，边框宽度
    # 右耳属性
    bpy.types.Scene.localThicking_offset = bpy.props.FloatProperty(
        name="localThicking_offset", min=0, max=3.0, default=0.2, update=LocalThickeningOffsetUpdate)
    bpy.types.Scene.localThicking_borderWidth = bpy.props.FloatProperty(
        name="localThicking_borderWidth", min=0, max=5.0, default=5, update=LocalThickeningBorderWidthUpdate)
    bpy.types.Scene.localThicking_circleRedius = bpy.props.FloatProperty(
        name="localThicking_circleRedius", default=50)
    bpy.types.Scene.is_thickening_completed = bpy.props.BoolProperty(
        name="is_thickening_completed")  # 防止局部加厚中的参数更新过快使得加厚参数调用的过于频繁,使得物体发生形变
    # 左耳属性
    bpy.types.Scene.localThicking_offset_L = bpy.props.FloatProperty(
        name="localThicking_offset_L", min=0, max=3.0, default=0.2, update=LocalThickeningOffsetUpdate_L)
    bpy.types.Scene.localThicking_borderWidth_L = bpy.props.FloatProperty(
        name="localThicking_borderWidth_L", min=0, max=5.0, default=5, update=LocalThickeningBorderWidthUpdate_L)
    bpy.types.Scene.localThicking_circleRedius_L = bpy.props.FloatProperty(
        name="localThicking_circleRedius_L", default=50)
    bpy.types.Scene.is_thickening_completed_L = bpy.props.BoolProperty(
        name="is_thickening_completed_L")  # 防止局部加厚中的参数更新过快使得加厚参数调用的过于频繁,使得物体发生形变

    # 点面切割属性
    # 右耳属性
    bpy.types.Scene.qieGeTypeEnumR = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '平面切割', ''),
            ('OP2', '阶梯状切割', '')],
        update=qiegeenum
    )
    bpy.types.Scene.qiegesheRuPianYiR = bpy.props.FloatProperty(
        name="sheRuPianYi", min=0.0, max=3, step=10, default=1, update=sheru)

    bpy.types.Scene.qiegewaiBianYuanR = bpy.props.FloatProperty(
        name="qiegewaiBianYuanR", min=0.1, max=1,
        step=10, update=stepcutoutborder, default=0.2)
    bpy.types.Scene.qiegeneiBianYuanR = bpy.props.FloatProperty(
        name="qiegeneiBianYuanR", min=1, max=3, step=10, update=stepcutinnerborder, default=1)
    # 左耳属性
    bpy.types.Scene.qieGeTypeEnumL = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '平面切割', ''),
            ('OP2', '阶梯状切割', '')],
        update=qiegeenum
    )
    bpy.types.Scene.qiegesheRuPianYiL = bpy.props.FloatProperty(
        name="sheRuPianYi", min=0.0, max=3, step=10, default=1, update=sheru)

    bpy.types.Scene.qiegewaiBianYuanL = bpy.props.FloatProperty(
        name="qiegewaiBianYuanL", min=0.1, max=1,
        step=10, update=stepcutoutborder, default=0.2)
    bpy.types.Scene.qiegeneiBianYuanL = bpy.props.FloatProperty(
        name="qiegeneiBianYuanL", min=1, max=3, step=10, update=stepcutinnerborder, default=1)

    # 参数、模具面板切换
    bpy.types.Scene.tabEnum = bpy.props.EnumProperty(
        name="tab",
        description='参数面板和模板选择面板切换',
        items=[
            ('参数', '参数', ''),
            ('模板', '模板', '')],
        # default = '模板'
    )

    bpy.types.Scene.use_template_HDU = bpy.props.BoolProperty(
        name="Use_Hdu", default=True, update=update_template_selection)
    # bpy.types.Scene.showHuier = bpy.props.BoolProperty(
    #     name="showMenu", default=False, update=update_showhuier)

    # 新建菜单属性

    bpy.types.Scene.newMuban = bpy.props.BoolProperty(
        name="newMuban", default=True)

    # 右耳文件
    bpy.types.Scene.rightEar_path = bpy.props.StringProperty(name="右耳输入",
                                                             description="右耳",
                                                             default="",
                                                             maxlen=1024,
                                                             subtype="FILE_PATH",
                                                             update=matchLeftEarFile)

    # 左耳文件
    bpy.types.Scene.leftEar_path = bpy.props.StringProperty(name="左耳输入",
                                                            description="左耳",
                                                            default="",
                                                            maxlen=1024,
                                                            subtype="FILE_PATH",
                                                            update=matchRightEarFile)
    # 自动文件匹配选项
    bpy.types.Scene.autoMatch = bpy.props.BoolProperty(
        name="autoMatch", default=True)

    # 导出STL属性

    # 勾选右耳
    bpy.types.Scene.tickRight = bpy.props.BoolProperty(
        name="tickRight", default=True)
    # 勾选左耳
    bpy.types.Scene.tickLeft = bpy.props.BoolProperty(
        name="tickLeft", default=True)

    bpy.types.Scene.expRightEar_path = bpy.props.StringProperty(name="",
                                                                description="右耳输出",
                                                                default="",
                                                                maxlen=1024,
                                                                subtype="FILE_PATH")

    bpy.types.Scene.expLeftEar_path = bpy.props.StringProperty(name="",
                                                               description="左耳输出",
                                                               default="",
                                                               maxlen=1024,
                                                               subtype="FILE_PATH")

    # 保存选项
    bpy.types.Scene.expSave = bpy.props.BoolProperty(
        name="expSace", default=True)
    # 关闭选项
    bpy.types.Scene.expClose = bpy.props.BoolProperty(
        name="expClose", default=True)

    bpy.types.Scene.hasregistertool = bpy.props.BoolProperty(
        name="hasregistertool", default=False)

    # sed文件
    bpy.types.Scene.expSedFile_path = bpy.props.StringProperty(name="",
                                                               description="Sed模板",
                                                               default="",
                                                               maxlen=1024,
                                                               subtype="FILE_PATH")

    bpy.types.Scene.origin_expSedFile_path = bpy.props.StringProperty(name="",
                                                               description="暂存的Sed模板",
                                                               default="",
                                                               maxlen=1024,
                                                               subtype="FILE_PATH")

    # bpy.types.Scene.use_saved_expSedFile =  bpy.props.BoolProperty(
    #     name="use_saved_expSedFile", default=False)
    #
    # bpy.types.Scene.saved_expSedFile_path = bpy.props.StringProperty(name="打开文件",
    #                                                            description="保存的Sed文件",
    #                                                            default="",
    #                                                            maxlen=1024,
    #                                                            subtype="FILE_PATH")

    # 另存为模板属性
    # 模板描述
    bpy.types.Scene.save_desc = bpy.props.StringProperty(name="",
                                                         description="模板描述",
                                                         default="",
                                                         maxlen=1024)

    # 左耳模型属性是否保存
    bpy.types.Scene.leftDamo = bpy.props.BoolProperty(
        name="leftDamo", default=True)
    
    bpy.types.Scene.leftJiahou = bpy.props.BoolProperty(
        name="leftJiahou", default=True)

    bpy.types.Scene.leftQiege = bpy.props.BoolProperty(
        name="leftQiege", default=True)

    bpy.types.Scene.leftChuangjianmoju = bpy.props.BoolProperty(
        name="leftChuangjianmoju", default=True)

    bpy.types.Scene.leftChuanshengkong = bpy.props.BoolProperty(
        name="leftChuanshengkong", default=False)

    bpy.types.Scene.leftBianhao = bpy.props.BoolProperty(
        name="leftbianhao", default=False)

    bpy.types.Scene.leftZhicheng = bpy.props.BoolProperty(
        name="leftZhicheng", default=False)

    # 右耳模型属性是否保存
    bpy.types.Scene.rightDamo = bpy.props.BoolProperty(
        name="rightDamo", default=True)
    
    bpy.types.Scene.rightJiahou = bpy.props.BoolProperty(
        name="rightJiahou", default=True)

    bpy.types.Scene.rightQiege = bpy.props.BoolProperty(
        name="rightQiege", default=True)

    bpy.types.Scene.rightChuangjianmoju = bpy.props.BoolProperty(
        name="rightChuangjianmoju", default=True)

    bpy.types.Scene.rightChuanshengkong = bpy.props.BoolProperty(
        name="rightChuanshengkong", default=False)

    bpy.types.Scene.rightBianhao = bpy.props.BoolProperty(
        name="rightbianhao", default=False)
    
    bpy.types.Scene.rightZhicheng = bpy.props.BoolProperty(
        name="rightZhicheng", default=False)

    # 模板属性
    bpy.types.Scene.muJuNameEnum = bpy.props.StringProperty(name="",
                                                            description="",
                                                            default="常规外壳",
                                                            maxlen=1024)
    # bpy.types.Scene.HuierNameEnum = bpy.props.StringProperty(name="",
    #                                                          description="",
    #                                                          default="default",
    #                                                          maxlen=1024)

    bpy.types.Scene.muJuTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '软耳模', '', 'RUANERMO', 1),
            ('OP2', '硬耳膜', '', 'YINGERMO', 2),
            ('OP3', '常规外壳', '', 'CHANGGUI', 3),
            ('OP4', '框架式耳膜', '', 'KUANGJIA', 4),
            ('OP5', '一体外壳', '', 'YITI', 5),
            ('OP6', '实心面板', '', 'SHIXIN', 6)],
        update=ChangeMouldType,
        default='OP3'
    )
    # bpy.types.Scene.HuierTypeEnum = bpy.props.EnumProperty(
    #     name="",
    #     description='this is option',
    #     items=[
    #         ('OP1', 'default', '', '', 1),
    #         ('OP2', 'ITC', '', '', 2),
    #         ('OP3', 'HS', '', '', 3)],
    #     update=ChangeHuierType,
    #     default='OP1'
    # )

    # 用于记录创建模具的初始化状态，主要用于不同类型的模具初始化参数
    bpy.types.Scene.createmouldinitR = bpy.props.BoolProperty(
        name="createmouldinitR", default=False)
    bpy.types.Scene.createmouldinitL = bpy.props.BoolProperty(
        name="createmouldinitL", default=False)

    # 用于记录外壳模块是否处在更新的状态，用于控制内外部边缘平滑的频繁更新
    # bpy.types.Scene.shellupdateR = bpy.props.BoolProperty(
    #     name="shellupdateR", default=False)
    # bpy.types.Scene.shellupdateL = bpy.props.BoolProperty(
    #     name="shellupdateL", default=False)

    # 用于记录外壳模块的蓝线是否被调整过
    bpy.types.Scene.curveadjustR = bpy.props.BoolProperty(
        name="curveadjustR", default=False)
    bpy.types.Scene.curveadjustL = bpy.props.BoolProperty(
        name="curveadjustL", default=False)

    # 创建模具属性
    bpy.types.Scene.neiBianJiXianR = bpy.props.BoolProperty(
        name="neiBianJiXianR", default=False, update=HoleBorder)
    bpy.types.Scene.waiBianYuanSheRuPianYiR = bpy.props.FloatProperty(
        name="waiBianYuanSheRuPianYiR", min=0.0, max=5.0, default=0, update=CreateMouldOuterSmooth)
    bpy.types.Scene.neiBianYuanSheRuPianYiR = bpy.props.FloatProperty(
        name="neiBianYuanSheRuPianYiR", min=0.0, max=5.0, default=0, update=CreateMouldInnerSmooth)

    bpy.types.Scene.zongHouDuR = bpy.props.FloatProperty(
        name="zongHouDuR", min=0.5, max=3.0, default=2, update=CreateMouldThicknessUpdate)
    bpy.types.Scene.zongHouDuUpdateCompleledR = bpy.props.BoolProperty(
        name="zongHouDuUpdateCompleledR", default=True)
    bpy.types.Scene.jiHuoBianYuanHouDuR = bpy.props.BoolProperty(
        name="jiHuoBianYuanHouDuR", update=ShellRegionWidthUpdate)
    bpy.types.Scene.waiBuHouDuR = bpy.props.FloatProperty(
        name="waiBuHouDuR", min=0.1, max=3, step=10, default=1, update=ShellThicknessUpdate)
    bpy.types.Scene.waiBuQuYuKuanDuR = bpy.props.FloatProperty(
        name="waiBuQuYuKuanDuR", min=0.1, max=10, step=10, default=5, update=ShellRegionWidthUpdate)
    bpy.types.Scene.zhongJianHouDuR = bpy.props.FloatProperty(
        name="zhongJianHouDuR", min=0.1, max=3, step=10, default=1, update=ShellThicknessUpdate)
    bpy.types.Scene.shiFouShiYongNeiBuR = bpy.props.BoolProperty(
        name="shiFouShiYongNeiBuR", default=True, update=ShellRegionWidthUpdate)
    bpy.types.Scene.zhongJianQuYuKuanDuR = bpy.props.FloatProperty(
        name="zhongJianQuYuKuanDuR", min=0.1, max=10, step=10, default=5, update=ShellRegionWidthUpdate)
    bpy.types.Scene.neiBuHouDuR = bpy.props.FloatProperty(
        name="neiBuHouDuR", min=0.1, max=3, step=10, default=1, update=ShellThicknessUpdate)

    bpy.types.Scene.neiBianJiXianL = bpy.props.BoolProperty(
        name="neiBianJiXianL", default=False, update=HoleBorder)
    bpy.types.Scene.waiBianYuanSheRuPianYiL = bpy.props.FloatProperty(
        name="waiBianYuanSheRuPianYiL", min=0.0, max=5.0, default=0, update=CreateMouldOuterSmooth)
    bpy.types.Scene.neiBianYuanSheRuPianYiL = bpy.props.FloatProperty(
        name="neiBianYuanSheRuPianYiL", min=0.0, max=5.0, default=0, update=CreateMouldInnerSmooth)

    bpy.types.Scene.zongHouDuL = bpy.props.FloatProperty(
        name="zongHouDuL", min=0.5, max=3.0, default=2, update=CreateMouldThicknessUpdate)
    bpy.types.Scene.zongHouDuUpdateCompleledL = bpy.props.BoolProperty(
        name="zongHouDuUpdateCompleledL", default=True)
    bpy.types.Scene.jiHuoBianYuanHouDuL = bpy.props.BoolProperty(
        name="jiHuoBianYuanHouDuL", update=ShellRegionWidthUpdate)
    bpy.types.Scene.waiBuHouDuL = bpy.props.FloatProperty(
        name="waiBuHouDuL", min=0.1, max=3, step=10, default=1, update=ShellThicknessUpdate)
    bpy.types.Scene.waiBuQuYuKuanDuL = bpy.props.FloatProperty(
        name="waiBuQuYuKuanDuL", min=0.1, max=10, step=10, default=5, update=ShellRegionWidthUpdate)
    bpy.types.Scene.zhongJianHouDuL = bpy.props.FloatProperty(
        name="zhongJianHouDuL", min=0.1, max=3, step=10, default=1, update=ShellThicknessUpdate)
    bpy.types.Scene.shiFouShiYongNeiBuL = bpy.props.BoolProperty(
        name="shiFouShiYongNeiBuL", default=True, update=ShellRegionWidthUpdate)
    bpy.types.Scene.zhongJianQuYuKuanDuL = bpy.props.FloatProperty(
        name="zhongJianQuYuKuanDuL", min=0.1, max=10, step=10, default=5, update=ShellRegionWidthUpdate)
    bpy.types.Scene.neiBuHouDuL = bpy.props.FloatProperty(
        name="neiBuHouDuL", min=0.1, max=3, step=10, default=1, update=ShellThicknessUpdate)

    bpy.types.Scene.mianBanTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('ITC', 'ITC', ''),
            ('CIC', 'CIC', ''),
            ('ITE', 'ITE', '')],
        default='ITC',
        update=update_battery_shape
    )
    bpy.types.Scene.jieShouQiTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', 'REC31570', '')]
    )
    bpy.types.Scene.jieShouQiKaiGuanTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '外置套管', '')]
    )
    bpy.types.Scene.buJianBTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', 'E7111', '')]
    )

    bpy.types.Scene.yingErMoSheRuPianYiL = bpy.props.FloatProperty(
        name="yingErMoSheRuPianYi", min=0.0, max=3.0, step=10, default=0, update=CreateMouldHardDrumSmooth)
    bpy.types.Scene.yingErMoSheRuPianYiR = bpy.props.FloatProperty(
        name="yingErMoSheRuPianYi", min=0.0, max=3.0, step=10, default=0, update=CreateMouldHardDrumSmooth)

    # 外壳蓝线相关
    bpy.types.Scene.mianBanPianYiR = bpy.props.FloatProperty(
        name="mianBanPianYiR", min=0.0, max=5, step=10, default=1, update=mianBanPianYi)
    bpy.types.Scene.xiaFangYangXianPianYiR = bpy.props.FloatProperty(
        name="xiaFangYangXianPianYiR", min=0.0, max=5, step=10, default=1, update=xiaFangYangXianPianYi)
    bpy.types.Scene.shangSheRuYinZiR = bpy.props.FloatProperty(
        name="shangSheRuYinZiR", min=0, max=100, step=100, default=15, update=smooth_loft_part)
    bpy.types.Scene.xiaSheRuYinZiR = bpy.props.FloatProperty(
        name="xiaSheRuYinZiR", min=0, max=100, step=100, default=15, update=smooth_loft_part)

    # 上部切割面板
    bpy.types.Scene.shiFouShangBuQieGeMianBanR = bpy.props.BoolProperty(
        name="shiFouShangBuQieGeMianBanR", default=False, update=UpperPlane)
    bpy.types.Scene.shangBuQieGeMianBanPianYiR = bpy.props.FloatProperty(
        name="shangBuQieGeMianBanPianYiR", min=0.0, max=3,
        step=10, update=upper_border_smooth, default=1)

    # 空腔面板
    # bpy.types.Scene.shiFouKongQiangMianBanR = bpy.props.BoolProperty(
    #     name="shiFouKongQiangMianBanR", default=True)
    bpy.types.Scene.KongQiangMianBanTypeEnumR = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '使用红环切割', ''),
            ('OP2', '根据上部红环切割', ''),
            ('OP3', '不切割', '')],
        default='OP1',
        update=kongQianMianBanTypeUpdate
    )
    bpy.types.Scene.KongQiangMianBanSheRuPianYiR = bpy.props.FloatProperty(
        name="KongQiangMianBanSheRuPianYiR", min=0.0, max=3,
        step=10, update=soft_eardrum_cavity_border, default=1)
    bpy.types.Scene.ShangBuQieGeBanPianYiR = bpy.props.FloatProperty(
        name="ShangBuQieGeBanPianYiR", min=0.0, max=5.0, default=2, update=shangBuQieGeBanPianYiUpdate)

    # 暂时不用
    bpy.types.Scene.gongXingMianBanR = bpy.props.FloatProperty(
        name="gongXingMianBanR", min=-1.0, max=1.0)
    bpy.types.Scene.gongKuanR = bpy.props.FloatProperty(
        name="gongKuanR", min=-1.0, max=1.0)
    bpy.types.Scene.gongGaoR = bpy.props.FloatProperty(
        name="gongGaoR", min=-1.0, max=1.0)

    # 外壳管道参数
    bpy.types.Scene.useShellCanalR = bpy.props.BoolProperty(
        name="useShellCanalR", default=True, update=updateShellCanal)
    bpy.types.Scene.shellCanalDiameterR = bpy.props.FloatProperty(
        name="shellCanalDiameterR", min=0.1, max=5.0, default=1, update=updateShellCanalDiameter)
    bpy.types.Scene.shellCanalThicknessR = bpy.props.FloatProperty(
        name="shellCanalThicknessR", min=0.1, max=5.0, default=1, update=updateShellCanalThickness)
    bpy.types.Scene.shellCanalOffsetR = bpy.props.FloatProperty(
        name="shellCanalOffsetR", min=0.0, max=3.0, default=0.1, update=updateCanalOffset)
    bpy.types.Scene.innerShellCanalOffsetR = bpy.props.FloatProperty(
        name="innerShellCanalOffsetR", min=0, max=3.0, default=0.5)
    bpy.types.Scene.outerShellCanalOffsetR = bpy.props.FloatProperty(
        name="outerShellCanalOffsetR", min=0, max=3.0, default=0.5)

    # 外壳蓝线相关
    bpy.types.Scene.mianBanPianYiL = bpy.props.FloatProperty(
        name="mianBanPianYiL", min=0.0, max=5, step=10, default=1, update=mianBanPianYi)
    bpy.types.Scene.xiaFangYangXianPianYiL = bpy.props.FloatProperty(
        name="xiaFangYangXianPianYiL", min=0.0, max=5, step=10, default=1, update=xiaFangYangXianPianYi)
    bpy.types.Scene.shangSheRuYinZiL = bpy.props.FloatProperty(
        name="shangSheRuYinZiL", min=0, max=100, step=100, default=15, update=smooth_loft_part)
    bpy.types.Scene.xiaSheRuYinZiL = bpy.props.FloatProperty(
        name="xiaSheRuYinZiL", min=0, max=100, step=100, default=15, update=smooth_loft_part)

    # 上部切割面板
    bpy.types.Scene.shiFouShangBuQieGeMianBanL = bpy.props.BoolProperty(
        name="shiFouShangBuQieGeMianBanL", default=False, update=UpperPlane)
    bpy.types.Scene.shangBuQieGeMianBanPianYiL = bpy.props.FloatProperty(
        name="shangBuQieGeMianBanPianYiL", min=0.0, max=3,
        step=10, update=upper_border_smooth, default=1)

    # 空腔面板
    # bpy.types.Scene.shiFouKongQiangMianBanL = bpy.props.BoolProperty(
    #     name="shiFouKongQiangMianBanL", default=True)
    bpy.types.Scene.KongQiangMianBanTypeEnumL = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '使用红环切割', ''),
            ('OP2', '根据上部红环切割', ''),
            ('OP3', '不切割', '')],
        default='OP1',
        update=kongQianMianBanTypeUpdate
    )
    bpy.types.Scene.KongQiangMianBanSheRuPianYiL = bpy.props.FloatProperty(
        name="KongQiangMianBanSheRuPianYiL", min=0.0, max=3,
        step=10, update=soft_eardrum_cavity_border, default=1)
    bpy.types.Scene.ShangBuQieGeBanPianYiL = bpy.props.FloatProperty(
        name="ShangBuQieGeBanPianYiL", min=0.0, max=5.0, default=2, update=shangBuQieGeBanPianYiUpdate)

    # 暂时不用
    bpy.types.Scene.gongXingMianBanL = bpy.props.FloatProperty(
        name="gongXingMianBanL", min=-1.0, max=1.0)
    bpy.types.Scene.gongKuanL = bpy.props.FloatProperty(
        name="gongKuanL", min=-1.0, max=1.0)
    bpy.types.Scene.gongGaoL = bpy.props.FloatProperty(
        name="gongGaoL", min=-1.0, max=1.0)

    # 外壳管道参数
    bpy.types.Scene.useShellCanalL = bpy.props.BoolProperty(
        name="useShellCanalL", default=True, update=updateShellCanal)
    bpy.types.Scene.shellCanalDiameterL = bpy.props.FloatProperty(
        name="shellCanalDiameterL", min=0.1, max=5.0, default=1, update=updateShellCanalDiameter)
    bpy.types.Scene.shellCanalThicknessL = bpy.props.FloatProperty(
        name="shellCanalThicknessL", min=0.1, max=5.0, default=1, update=updateShellCanalThickness)
    bpy.types.Scene.shellCanalOffsetL = bpy.props.FloatProperty(
        name="shellCanalOffsetL", min=0.0, max=3.0, default=0.1, update=updateCanalOffset)
    bpy.types.Scene.innerShellCanalOffsetL = bpy.props.FloatProperty(
        name="innerShellCanalOffsetL", min=0, max=3.0, default=0.5)
    bpy.types.Scene.outerShellCanalOffsetL = bpy.props.FloatProperty(
        name="outerShellCanalOffsetL", min=0, max=3.0, default=0.5)

    # 传声孔      管道平滑      传声管道直径         激活   管道形状  偏移
    # 右属性
    bpy.types.Scene.gaunDaoPinHua = bpy.props.BoolProperty(
        name="gaunDaoPinHua", default=True)
    bpy.types.Scene.chuanShenGuanDaoZhiJing = bpy.props.FloatProperty(
        name="chuanShenGuanDaoZhiJing", min=0.2, max=10, step=10,
        default=2, update=soundcanalupdate)
    # bpy.types.Scene.active = bpy.props.BoolProperty(name="active")
    bpy.types.Scene.chuanShenKongOffset = bpy.props.FloatProperty(
        name="chuanShenKongOffset", min=-50.0, max=50.0, update=soundcanalHornpipeOffset)
    bpy.types.Scene.soundcancalShapeEnum = bpy.props.EnumProperty(
        name="",
        description='传声孔的形状',
        items=[
            ('OP1', '普通管道', ''),
            ('OP2', '号角管', ''), ],
        update=soundcanalShape
    )
    # 左耳属性
    bpy.types.Scene.gaunDaoPinHua_L = bpy.props.BoolProperty(
        name="gaunDaoPinHua_L", default=True)
    bpy.types.Scene.chuanShenGuanDaoZhiJing_L = bpy.props.FloatProperty(
        name="chuanShenGuanDaoZhiJing_L", min=0.2, max=10, step=10,
        default=2, update=soundcanalupdate)
    # bpy.types.Scene.active = bpy.props.BoolProperty(name="active")
    bpy.types.Scene.chuanShenKongOffset_L = bpy.props.FloatProperty(
        name="chuanShenKongOffset_L", min=-50, max=50, update=soundcanalHornpipeOffset)
    bpy.types.Scene.soundcancalShapeEnum_L = bpy.props.EnumProperty(
        name="",
        description='传声孔的形状',
        items=[
            ('OP1', '普通管道', ''),
            ('OP2', '号角管', ''), ],
        update=soundcanalShape
    )

    # 通气孔     通气管道直径
    # 右
    bpy.types.Scene.tongQiGuanDaoZhiJing = bpy.props.FloatProperty(
        name="tongQiGuanDaoZhiJing", min=0.2, max=10, step=10,
        default=1, update=ventcanalupdate)
    # 左
    bpy.types.Scene.tongQiGuanDaoZhiJing_L = bpy.props.FloatProperty(
        name="tongQiGuanDaoZhiJing_L", min=0.2, max=10, step=10,
        default=1, update=ventcanalupdate)

    # 耳膜附件      耳膜附件类型    偏移
    bpy.types.Scene.erMoFuJianOffset = bpy.props.FloatProperty(
        name="erMoFuJianOffset", min=-5.0, max=5.0, update=HandleOffsetUpdate)
    bpy.types.Scene.erMoFuJianTypeEnum = bpy.props.EnumProperty(
        name="",
        description='handle耳膜附件的类型',
        items=[
            ('OP1', '耳膜附件', ''),
        ]
    )
    bpy.types.Scene.erMoFuJianOffsetL = bpy.props.FloatProperty(
        name="erMoFuJianOffsetL", min=-5.0, max=5.0, update=HandleOffsetUpdate)
    bpy.types.Scene.erMoFuJianTypeEnumL = bpy.props.EnumProperty(
        name="",
        description='handle耳膜附件的类型',
        items=[
            ('OP1', '耳膜附件', ''),
        ]
    )

    # 编号
    bpy.types.Scene.labelText = bpy.props.StringProperty(
        name="labelText", description="Enter label text here", default="HuiEr", update=LabelTextUpdate)
    bpy.types.Scene.fontSize = bpy.props.IntProperty(
        name="fontSize", min=1, max=8, default=4, update=LabelSizeUpdate)
    bpy.types.Scene.deep = bpy.props.FloatProperty(
        name="deep", min=0.0, max=3.0, default=1.0, update=LabelDepthUpdate)
    bpy.types.Scene.styleEnum = bpy.props.EnumProperty(
        name="",
        description='编号的风格',
        items=[
            ('OP1', '内嵌', ''),
            ('OP2', '外凸', ''), ],
        update=LabelEnum
    )
    bpy.types.Scene.labelTextL = bpy.props.StringProperty(
        name="labelTextL", description="Enter label text here", default="HuiEr", update=LabelTextUpdate)
    bpy.types.Scene.fontSizeL = bpy.props.IntProperty(
        name="fontSizeL", min=1, max=8, default=4, update=LabelSizeUpdate)
    bpy.types.Scene.deepL = bpy.props.FloatProperty(
        name="deepL", min=0.0, max=3.0, default=1.0, update=LabelDepthUpdate)
    bpy.types.Scene.styleEnumL = bpy.props.EnumProperty(
        name="",
        description='编号的风格',
        items=[
            ('OP1', '内嵌', ''),
            ('OP2', '外凸', ''), ],
        update=LabelEnum
    )

    # 软耳模厚度       厚度类型    软耳模厚度
    bpy.types.Scene.ruanErMoHouDu = bpy.props.FloatProperty(
        name="ruanErMoHouDu", min=0.2, max=3.0, update=CastingThicknessUpdate)
    bpy.types.Scene.ruanErMoTypeEnum = bpy.props.EnumProperty(
        name="ruanErMoTypeEnum",
        description='',
        items=[
            ('OP1', '偏移曲面', ''),
            ('OP2', '无', ''), ]
    )
    bpy.types.Scene.ruanErMoHouDuL = bpy.props.FloatProperty(
        name="ruanErMoHouDuL", min=0.2, max=3.0, update=CastingThicknessUpdate)
    bpy.types.Scene.ruanErMoTypeEnumL = bpy.props.EnumProperty(
        name="ruanErMoTypeEnumL",
        description='',
        items=[
            ('OP1', '偏移曲面', ''),
            ('OP2', '无', ''), ]
    )

    # 支撑        支撑类型     偏移
    bpy.types.Scene.zhiChengOffset = bpy.props.FloatProperty(
        name="zhiChengOffset", min=-1.0, max=1.0, update=SupportOffsetUpdate)
    bpy.types.Scene.zhiChengTypeEnum = bpy.props.EnumProperty(
        name="",
        description='',
        items=[
            ('OP1', '硬耳模支撑', ''),
            ('OP2', '软耳膜支撑', ''), ],
        update=SupportEnum
    )
    bpy.types.Scene.zhiChengOffsetL = bpy.props.FloatProperty(
        name="zhiChengOffsetL", min=-1.0, max=1.0, update=SupportOffsetUpdate)
    bpy.types.Scene.zhiChengTypeEnumL = bpy.props.EnumProperty(
        name="",
        description='',
        items=[
            ('OP1', '硬耳模支撑', ''),
            ('OP2', '软耳膜支撑', ''), ],
        update=SupportEnum
    )

    # 排气孔        排气孔类型     偏移
    bpy.types.Scene.paiQiKongOffset = bpy.props.FloatProperty(
        name="paiQiKongOffset", min=-1.0, max=1.0, update=SprueOffsetUpdate)
    bpy.types.Scene.paiQiKongTypeEnum = bpy.props.EnumProperty(
        name="",
        description='',
        items=[
            ('OP1', '排气孔', ''), ]
    )
    bpy.types.Scene.paiQiKongOffsetL = bpy.props.FloatProperty(
        name="paiQiKongOffsetL", min=-1.0, max=1.0, update=SprueOffsetUpdate)
    bpy.types.Scene.paiQiKongTypeEnumL = bpy.props.EnumProperty(
        name="",
        description='',
        items=[
            ('OP1', '排气孔', ''), ]
    )

    bpy.types.Scene.transparent1R = bpy.props.BoolProperty(
        name="transparent1", default=False, update=show_transparent1)
    bpy.types.Scene.transparent2R = bpy.props.BoolProperty(
        name="transparent2", default=False, update=show_transparent2)
    bpy.types.Scene.transparent3R = bpy.props.BoolProperty(
        name="transparent3", default=False, update=show_transparent3)
    bpy.types.Scene.transparent1L = bpy.props.BoolProperty(
        name="transparent1", default=False, update=show_transparent1)
    bpy.types.Scene.transparent2L = bpy.props.BoolProperty(
        name="transparent2", default=False, update=show_transparent2)
    bpy.types.Scene.transparent3L = bpy.props.BoolProperty(
        name="transparent3", default=False, update=show_transparent3)

    bpy.types.Scene.transparent1EnumR = bpy.props.EnumProperty(
        name="transparent1Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent1,
        default='OP1'
    )
    bpy.types.Scene.transparentper1EnumR = bpy.props.EnumProperty(
        name="transparentper1Enum",
        description='',
        items=[
            ('0.2', "20%", ""),
            ('0.4', "40%", ""),
            ('0.6', "60%", ""),
            ('0.8', "80%", "")
        ],
        update=update_transparentper1,
        default='0.6'
    )
    bpy.types.Scene.transparent1EnumL = bpy.props.EnumProperty(
        name="transparent1Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent1,
        default='OP1'
    )
    bpy.types.Scene.transparentper1EnumL = bpy.props.EnumProperty(
        name="transparentper1Enum",
        description='',
        items=[
            ('0.2', "20%", ""),
            ('0.4', "40%", ""),
            ('0.6', "60%", ""),
            ('0.8', "80%", "")
        ],
        update=update_transparentper1,
        default='0.6'
    )
    bpy.types.Scene.transparent2EnumR = bpy.props.EnumProperty(
        name="transparent2Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent2,
        default='OP1'
    )
    bpy.types.Scene.transparentper2EnumR = bpy.props.EnumProperty(
        name="transparentper2Enum",
        description='',
        items=[
            ('0.2', "20%", ""),
            ('0.4', "40%", ""),
            ('0.6', "60%", ""),
            ('0.8', "80%", "")
        ],
        update=update_transparentper2,
        default='0.6'
    )
    bpy.types.Scene.transparent2EnumL = bpy.props.EnumProperty(
        name="transparent2Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent2,
        default='OP1'
    )
    bpy.types.Scene.transparentper2EnumL = bpy.props.EnumProperty(
        name="transparentper2Enum",
        description='',
        items=[
            ('0.2', "20%", ""),
            ('0.4', "40%", ""),
            ('0.6', "60%", ""),
            ('0.8', "80%", "")
        ],
        update=update_transparentper2,
        default='0.6'
    )
    bpy.types.Scene.transparent3EnumR = bpy.props.EnumProperty(
        name="transparent3Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent3,
        default='OP1'
    )
    bpy.types.Scene.transparentper3EnumR = bpy.props.EnumProperty(
        name="transparentper3Enum",
        description='',
        items=[
            ('0.2', "20%", ""),
            ('0.4', "40%", ""),
            ('0.6', "60%", ""),
            ('0.8', "80%", "")
        ],
        update=update_transparentper3,
        default='0.6'
    )
    bpy.types.Scene.transparent3EnumL = bpy.props.EnumProperty(
        name="transparent3Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent3,
        default='OP1'
    )
    bpy.types.Scene.transparentper3EnumL = bpy.props.EnumProperty(
        name="transparentper3Enum",
        description='',
        items=[
            ('0.2', "20%", ""),
            ('0.4', "40%", ""),
            ('0.6', "60%", ""),
            ('0.8', "80%", "")
        ],
        update=update_transparentper3,
        default='0.6'
    )

    bpy.types.Scene.cutmouldpianyiR = bpy.props.FloatProperty(
        name="cutmouldpianyiR", min=0, max=4.0, default=1.0, step=10)
    bpy.types.Scene.cutmouldpianyiL = bpy.props.FloatProperty(
        name="cutmouldpianyiL", min=0, max=4.0, default=1.0, step=10)

    bpy.types.Scene.earname = bpy.props.StringProperty(
        name="earname")

    bpy.types.Scene.lastprocess = bpy.props.StringProperty(
        name="lastprocess")

    bpy.types.Scene.needrecord = bpy.props.BoolProperty(
        name="needrecord", default=True)


def record_prop_value(self, context):
    bl_description = "记录当前属性值"
    if get_is_processing_undo_redo():
        return
    record_state()


def Houdu(self, context):
    bl_description = "调整蜡厚度的值"
    if get_is_processing_undo_redo():
        return
    name = context.scene.leftWindowObj
    active_object = bpy.data.objects[name]
    ori_name = name + 'OriginForShow'
    reset_name = name + 'DamoReset'
    if name == '右耳':
        thickness = context.scene.laHouDUR
    elif name == '左耳':
        thickness = context.scene.laHouDUL

    ori_obj = bpy.data.objects[ori_name]
    reset_obj = bpy.data.objects[reset_name]
    is_dialog = get_is_dialog()
    if is_dialog:
        return
    is_same_thickness = True
    vert_thickness = (active_object.data.vertices[0].co - ori_obj.data.vertices[0].co).length
    for vert in active_object.data.vertices:
        if vert_thickness != (active_object.data.vertices[vert.index].co - ori_obj.data.vertices[vert.index].co).length:
            is_same_thickness = False
            break
    if active_object.type == 'MESH' and bpy.data.objects.get(reset_name) != None:
        if is_same_thickness:
            me = active_object.data
            reset_me = reset_obj.data

            ori_me = ori_obj.data
            ori_bm = bmesh.new()
            ori_bm.from_mesh(ori_me)
            ori_bm.verts.ensure_lookup_table()

            for vert in ori_bm.verts:
                vert.co = ori_bm.verts[vert.index].co + ori_bm.verts[vert.index].normal.normalized() * thickness

            ori_bm.to_mesh(me)
            ori_bm.to_mesh(reset_me)
            ori_bm.free()
            if name == '右耳':
                set_previous_thicknessR(thickness)
            elif name == '左耳':
                set_previous_thicknessL(thickness)
            record_state()
        else:
            bpy.ops.object.damo_operator('INVOKE_DEFAULT')


def scale_strength(self, context):
    if context.scene.leftWindowObj == '右耳':
        radius = context.scene.damo_circleRadius_R
        if context.scene.var == 1 or context.scene.var == 2:
            bpy.data.brushes["SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_R
        elif context.scene.var == 3:
            bpy.data.brushes["Smooth"].strength = 25 / radius * context.scene.damo_scale_strength_R
    elif context.scene.leftWindowObj == '左耳':
        radius = context.scene.damo_circleRadius_L
        if context.scene.var == 1 or context.scene.var == 2:
            bpy.data.brushes["SculptDraw"].strength = 25 / radius * context.scene.damo_scale_strength_L
        elif context.scene.var == 3:
            bpy.data.brushes["Smooth"].strength = 25 / radius * context.scene.damo_scale_strength_L


# def update_showhdu(self, context):
#     if self.showHdu:
#         self.showHuier = False
#
#
# def update_showhuier(self, context):
#     if self.showHuier:
#         self.showHdu = False


# 环切舍入偏移函数
def sheru(self, context):
    bl_description = "环切舍入偏移"
    if get_is_processing_undo_redo():
        return
    operator_obj = context.scene.leftWindowObj
    if operator_obj == '右耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiR
    elif operator_obj == '左耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiL
    override = getOverride()
    with bpy.context.temp_override(**override):
        smooth_circlecut(operator_obj, pianyi)
        record_state()


def another_filename(filename):
    # 检查文件名是否以'L.stl'结尾
    if filename.endswith('L.stl'):
        # 如果是，将'L.stl'替换为'R.stl'
        return filename.replace('L.stl', 'R.stl')
    # 检查文件名是否以'R.stl'结尾
    elif filename.endswith('R.stl'):
        # 如果是，将'R.stl'替换为'L.stl'
        return filename.replace('R.stl', 'L.stl')
    # 检查文件名是否以'L.STL'结尾
    elif filename.endswith('L.STL'):
        # 如果是，将'L.STL'替换为'R.STL'
        return filename.replace('L.STL', 'R.STL')
    # 检查文件名是否以'R.STL'结尾
    elif filename.endswith('R.STL'):
        # 如果是，将'R.stl'替换为'L.stl'
        return filename.replace('R.STL', 'L.STL')


# 选择一个文件后，匹配另一个
def matchLeftEarFile(self, context):
    file_path = context.scene.rightEar_path
    # 获取文件所在的目录
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(file_path)

    if filename.endswith('R.stl'):
        # 构造ExampleR.stl的路径
        left_filename = another_filename(filename)
        # print('left',left_filename)
        if left_filename:
            example_l_path = os.path.join(directory, left_filename)
            left_path = context.scene.leftEar_path
            # 是否存在
            if os.path.isfile(
                    example_l_path) and context.scene.autoMatch and example_l_path != file_path and left_path == "":
                print("左耳文件匹配成功")
                context.scene.leftEar_path = example_l_path
            elif context.scene.autoMatch and left_path != "":
                print("左耳文件已存在")

    elif filename.endswith('R.STL'):
        # 构造ExampleR.stl的路径
        left_filename = another_filename(filename)
        # print('left',left_filename)
        if left_filename:
            example_l_path = os.path.join(directory, left_filename)
            left_path = context.scene.leftEar_path
            # 是否存在
            if os.path.isfile(
                    example_l_path) and context.scene.autoMatch and example_l_path != file_path and left_path == "":
                print("左耳文件匹配成功")
                context.scene.leftEar_path = example_l_path
            elif context.scene.autoMatch and left_path != "":
                print("左耳文件已存在")


def matchRightEarFile(self, context):
    file_path = context.scene.leftEar_path
    # 获取文件所在的目录
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(file_path)

    if filename.endswith('L.stl'):
        # 构造ExampleR.stl的路径
        right_filename = another_filename(filename)
        if right_filename:
            example_r_path = os.path.join(directory, right_filename)
            right_path = context.scene.rightEar_path
            # 是否存在
            if os.path.isfile(
                    example_r_path) and context.scene.autoMatch and example_r_path != file_path and right_path == "":
                print("右耳文件匹配成功")
                context.scene.rightEar_path = example_r_path
            elif context.scene.autoMatch and right_path != "":
                print("右耳文件已存在")

    elif filename.endswith('L.STL'):
        # 构造ExampleR.stl的路径
        right_filename = another_filename(filename)
        if right_filename:
            example_r_path = os.path.join(directory, right_filename)
            right_path = context.scene.rightEar_path
            # 是否存在
            if os.path.isfile(
                    example_r_path) and context.scene.autoMatch and example_r_path != file_path and right_path == "":
                print("右耳文件匹配成功")
                context.scene.rightEar_path = example_r_path
            elif context.scene.autoMatch and right_path != "":
                print("右耳文件已存在")


# 切割模式切换
def qiegeenum(self, context):
    bl_description = "选择切割方式"
    # 当前主窗口物体
    name = context.scene.leftWindowObj
    if name == '右耳':
        enum = bpy.context.scene.qieGeTypeEnumR
    elif name == '左耳':
        enum = bpy.context.scene.qieGeTypeEnumL

    if enum == "OP1":
        quitStepCut(name)
        override = getOverride()
        with bpy.context.temp_override(**override):
            initCircle(name)
    if enum == "OP2":
        quitCut(name)
        override = getOverride()
        with bpy.context.temp_override(**override):
            initPlane(name)


def stepcutoutborder(self, context):
    bl_description = "侧切外边缘舍入偏移"
    if context.scene.leftWindowObj == '右耳':
        pianyi = bpy.context.scene.qiegewaiBianYuanR
    elif context.scene.leftWindowObj == '左耳':
        pianyi = bpy.context.scene.qiegewaiBianYuanL
    smooth_obj_name = context.scene.leftWindowObj + 'stepcutpinghua'
    if bpy.data.objects.get(smooth_obj_name) != None:
        override = getOverride()
        with bpy.context.temp_override(**override):
            smooth_stepcut(smooth_obj_name, pianyi)


# 侧切偏移函数
def stepcutinnerborder(self, context):
    bl_description = "侧切内边缘舍入偏移"
    if context.scene.leftWindowObj == '右耳':
        pianyi = bpy.context.scene.qiegeneiBianYuanR
    elif context.scene.leftWindowObj == '左耳':
        pianyi = bpy.context.scene.qiegeneiBianYuanL
    plane_name = context.scene.leftWindowObj + 'StepCutplane'
    if bpy.data.objects.get(plane_name) != None:
        bpy.data.objects[plane_name].modifiers["smooth"].width = pianyi
        override = getOverride()
        with bpy.context.temp_override(**override):
            apply_stepcut(context.scene.leftWindowObj)


# 回调函数，根据绑定的属性值更改选中区域的厚度
def LocalThickeningOffsetUpdate(self, context):
    bl_description = "更新选中区域中加厚的厚度"
    if get_is_processing_undo_redo():
        return

    offset = context.scene.localThicking_offset
    borderWidth = context.scene.localThicking_borderWidth
    is_thickening_completed = context.scene.is_thickening_completed  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        context.scene.is_thickening_completed = True
        thickening_reset()
        thickening_offset_borderwidth(offset, borderWidth)
        applySmooth()
        context.scene.is_thickening_completed = False
        record_state()


# 左耳
def LocalThickeningOffsetUpdate_L(self, context):
    bl_description = "更新选中区域中加厚的厚度_L"
    if get_is_processing_undo_redo():
        return

    offset = context.scene.localThicking_offset_L
    borderWidth = context.scene.localThicking_borderWidth_L
    is_thickening_completed = context.scene.is_thickening_completed_L  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        # 根据更新后的参数重新进行加厚
        context.scene.is_thickening_completed_L = True
        thickening_reset()
        thickening_offset_borderwidth(offset, borderWidth)
        applySmooth()
        context.scene.is_thickening_completed_L = False
        record_state()


def LocalThickeningBorderWidthUpdate(self, context):
    bl_description = "更新选中区域中的过渡区域"
    if get_is_processing_undo_redo():
        return

    offset = context.scene.localThicking_offset
    borderWidth = context.scene.localThicking_borderWidth
    is_thickening_completed = context.scene.is_thickening_completed  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        context.scene.is_thickening_completed = True
        thickening_reset()
        thickening_offset_borderwidth(offset, borderWidth)
        applySmooth()
        context.scene.is_thickening_completed = False
        record_state()


# 左耳
def LocalThickeningBorderWidthUpdate_L(self, context):
    bl_description = "更新选中区域中的过渡区域左耳"
    if get_is_processing_undo_redo():
        return

    offset = context.scene.localThicking_offset_L
    borderWidth = context.scene.localThicking_borderWidth_L
    is_thickening_completed = context.scene.is_thickening_completed_L  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变
    if (not is_thickening_completed):
        # 根据更新后的参数重新进行加厚
        context.scene.is_thickening_completed_L = True
        thickening_reset()
        thickening_offset_borderwidth(offset, borderWidth)
        applySmooth()
        context.scene.is_thickening_completed_L = False
        record_state()


def ChangeMouldName(self, context):
    enum_name = bpy.context.scene.muJuNameEnum
    # if enum_name == "OP1":
    #     bpy.context.scene.muJuTypeEnum = 'OP1'
    # if enum_name == "OP2":
    #     bpy.context.scene.muJuTypeEnum = 'OP2'
    # if enum_name == "OP3":
    #     bpy.context.scene.muJuTypeEnum = 'OP3'
    # if enum_name == "OP4":
    #     bpy.context.scene.muJuTypeEnum = 'OP4'
    # if enum_name == "OP5":
    #     bpy.context.scene.muJuTypeEnum = 'OP5'
    # if enum_name == "OP6":
    #     bpy.context.scene.muJuTypeEnum = 'OP6'


# ('OP1', '软耳模', '', 'URL', 1),
# ('OP2', '硬耳膜', '', 'URL', 2),
# ('OP3', '常规外壳', '', 'URL', 3),
# ('OP4', '框架式耳膜', '', 'URL', 4),
# ('OP5', '一体外壳', '', 'URL', 5),
# ('OP6', '实心面板', '', 'URL', 6)
def ChangeMouldType(self, context):
    bl_description = "切换模板"
    if get_is_processing_undo_redo():
        return
    enum = bpy.context.scene.muJuTypeEnum
    enum_name = bpy.context.scene.muJuNameEnum

    # 同步改变模型名称属性
    if enum == "OP1":
        bpy.context.scene.muJuNameEnum = '软耳模'
    if enum == "OP2":
        bpy.context.scene.muJuNameEnum = '硬耳膜'
    if enum == "OP3":
        bpy.context.scene.muJuNameEnum = '常规外壳'
    if enum == "OP4":
        bpy.context.scene.muJuNameEnum = '框架式耳膜'
    if enum == "OP5":
        bpy.context.scene.muJuNameEnum = '一体外壳'
    if enum == "OP6":
        bpy.context.scene.muJuNameEnum = '实心面板'

    # 重置回最开始
    override = getOverride()
    if override != None:
        with bpy.context.temp_override(**override):
            last_eunm = get_type()
            if context.scene.leftWindowObj == '右耳':
                bpy.context.scene.createmouldinitR = False
            elif context.scene.leftWindowObj == '左耳':
                bpy.context.scene.createmouldinitL = False
            if (last_eunm == 'OP1' and enum == 'OP4') or (last_eunm == 'OP4' and enum == 'OP1'):
                name = bpy.context.scene.leftWindowObj
                set_type(enum)
                reset_to_after_cut()
                torus_obj = [name + "Circle", name + "Torus", name + "UpperCircle", name + "UpperTorus"]
                delete_useless_object(torus_obj)
                if last_eunm == 'OP1':
                    if context.scene.leftWindowObj == '右耳':
                        set_left_soft_eardrum_border(get_left_frame_style_eardrum_border())
                    else:
                        set_right_soft_eardrum_border(get_right_frame_style_eardrum_border())
                elif last_eunm == 'OP4':
                    for obj in bpy.data.objects:
                        if re.match(name + 'HoleBorderCurve', obj.name) is not None:
                            bpy.data.objects.remove(obj, do_unlink=True)
                    for obj in bpy.data.objects:
                        if re.match(name + 'meshHoleBorderCurve', obj.name) is not None:
                            bpy.data.objects.remove(obj, do_unlink=True)
                    if context.scene.leftWindowObj == '右耳':
                        set_left_frame_style_eardrum_border(get_left_soft_eardrum_border())
                    else:
                        set_right_frame_style_eardrum_border(get_right_soft_eardrum_border())
                create_mould_fill()
            else:
                recover_flag = recover(last_eunm, restart=False)
                set_type(enum)
                create_mould_cut()
            record_state()

            # if enum == "OP1":
            #     print("软耳模")
            #     success = apply_soft_eardrum_template()
            #     bpy.context.scene.neiBianJiXian = False
            # if enum == "OP2":
            #     print("硬耳膜")
            #     apply_hard_eardrum_template()
            #     bpy.context.scene.neiBianJiXian = False
            # if enum == "OP3":
            #     print("一体外壳")
            # if enum == "OP4":
            #     print("框架式耳膜")
            #     apply_frame_style_eardrum_template()
            #     bpy.context.scene.neiBianJiXian = True
            # if enum == "OP5":
            #     print("常规外壳")
            # if enum == "OP6":
            #     print("实心面板")


# def ChangeHuierType(self, context):
#     bl_description = "切换Huier模板"
#     muju_enum = bpy.context.scene.muJuTypeEnum
#     enum = bpy.context.scene.HuierTypeEnum
#     enum_name = bpy.context.scene.HuierNameEnum
#
#     override = getOverride()
#     if override != None:
#         with bpy.context.temp_override(**override):
#             if muju_enum == 'OP3':
#                 # 同步改变模型名称属性
#                 if enum == "OP1":
#                     bpy.context.scene.HuierNameEnum = 'default'
#                     change_different_shell_type()
#                 if enum == "OP2":
#                     bpy.context.scene.HuierNameEnum = 'ITC'
#                     change_different_shell_type()
#                 if enum == "OP3":
#                     bpy.context.scene.HuierNameEnum = 'HS'


def CreateMouldThicknessUpdate(self, context):
    bl_description = "更新创建模具中的总厚度"
    if get_is_processing_undo_redo():
        return
    enum = bpy.context.scene.muJuTypeEnum
    override = getOverride()
    if context.scene.leftWindowObj == '右耳':
        createmouldinit = bpy.context.scene.createmouldinitR
    elif context.scene.leftWindowObj == '左耳':
        createmouldinit = bpy.context.scene.createmouldinitL
    if createmouldinit:
        # 根据不同的模具执行不同的逻辑
        if enum == "OP1":
            with bpy.context.temp_override(**override):
                reset_and_refill()
        elif enum == "OP4":
            with bpy.context.temp_override(**override):
                # recover_and_refill()
                reset_and_refill()
        elif enum == "OP3":
            with bpy.context.temp_override(**override):
                adjust_region_width()
        record_state()


def CreateMouldOuterSmooth(self, context):
    bl_description = "创建模具后,平滑其外边缘"
    if get_is_processing_undo_redo():
        return
    enum = bpy.context.scene.muJuTypeEnum

    # 根据不同的模具执行不同的逻辑
    if enum == "OP1":
        override = getOverride()
        with bpy.context.temp_override(**override):
            soft_extrude_smooth_initial()
            # soft_offset_cut_smooth()
            record_state()
    elif enum == "OP4":
        override = getOverride()
        with bpy.context.temp_override(**override):
            soft_extrude_smooth_initial()
            # frame_extrude_smooth_initial()
            # recover_and_refill()
            record_state()


def CreateMouldInnerSmooth(self, context):
    bl_description = "创建模具后,平滑其内边缘"
    if get_is_processing_undo_redo():
        return

    enum = bpy.context.scene.muJuTypeEnum

    # 根据不同的模具执行不同的逻辑
    if enum == "OP1":
        override = getOverride()
        with bpy.context.temp_override(**override):
            soft_extrude_smooth_initial()
            # soft_offset_cut_smooth()
            # soft_step_modifier_smooth()
            # re_smooth("右耳InnerOrigin", "右耳InnerRetopo", "右耳OuterRetopo", "BottomInnerBorderVertex", bpy.context.scene.neiBianYuanSheRuPianYi)
            record_state()
    elif enum == "OP4":
        override = getOverride()
        with bpy.context.temp_override(**override):
            soft_extrude_smooth_initial()
            # frame_extrude_smooth_initial()
            # recover_and_refill()
            record_state()


# 软耳模空腔面板边缘平滑
def soft_eardrum_cavity_border(self, context):
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        enum = bpy.context.scene.muJuTypeEnum
        if (enum == 'OP1' or enum == 'OP4'):
            refill_after_cavity_smooth()
            record_state()
        elif (enum == 'OP3'):
            # if context.scene.leftWindowObj == '右耳':
            #     shellupdate = bpy.context.scene.shellupdateR
            # elif context.scene.leftWindowObj == '左耳':
            #     shellupdate = bpy.context.scene.shellupdateL
            # if not shellupdate:
            update_middle_circle_smooth()
            record_state()


def kongQianMianBanTypeUpdate(self, context):
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    if context.scene.leftWindowObj == '右耳':
        createmouldinit = bpy.context.scene.createmouldinitR
    elif context.scene.leftWindowObj == '左耳':
        createmouldinit = bpy.context.scene.createmouldinitL
    if createmouldinit:
        with bpy.context.temp_override(**override):
            enum = bpy.context.scene.muJuTypeEnum
            if (enum == 'OP3'):
                useMiddleTrous()
                update_top_circle_cut()
                record_state()


def shangBuQieGeBanPianYiUpdate(self, context):
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        enum = bpy.context.scene.muJuTypeEnum
        if (enum == 'OP3'):
            update_middle_circle_offset()
            update_middle_circle_cut()
            record_state()


# 上部切割面板边缘平滑
def upper_border_smooth(self, context):
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        enum = bpy.context.scene.muJuTypeEnum
        if (enum == 'OP1' or enum == 'OP4'):
            refill_after_upper_smooth()
            record_state()
        if (enum == 'OP3'):
            # if context.scene.leftWindowObj == '右耳':
            #     shellupdate = bpy.context.scene.shellupdateR
            # elif context.scene.leftWindowObj == '左耳':
            #     shellupdate = bpy.context.scene.shellupdateL
            # if not shellupdate:
            update_top_circle_smooth()
            record_state()


# 是否启用上部切割面板
def UpperPlane(self, context):
    if get_is_processing_undo_redo():
        return
    enum = bpy.context.scene.muJuTypeEnum
    if enum == 'OP1' or enum == 'OP4':
        if context.scene.leftWindowObj == '右耳':
            shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanR
            createmouldinit = bpy.context.scene.createmouldinitR
            neibianjixian = bpy.context.scene.neiBianJiXianR
        elif context.scene.leftWindowObj == '左耳':
            shangbuqiege = bpy.context.scene.shiFouShangBuQieGeMianBanL
            createmouldinit = bpy.context.scene.createmouldinitL
            neibianjixian = bpy.context.scene.neiBianJiXianL

        if createmouldinit:
            if shangbuqiege:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    set_finish(True)
                    draw_cut_plane_upper(context.scene.leftWindowObj)
                    if neibianjixian:
                        reset_and_dig_and_refill()
                    else:
                        reset_and_refill()
                    set_finish(False)
                    record_state()
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    name = bpy.context.scene.leftWindowObj
                    if bpy.data.objects.get(name + 'UpperTorus') != None:
                        bpy.data.objects.remove(bpy.data.objects[name + 'UpperTorus'], do_unlink=True)
                    if bpy.data.objects.get(name + 'UpperCircle') != None:
                        bpy.data.objects.remove(bpy.data.objects[name + 'UpperCircle'], do_unlink=True)
                    if bpy.data.objects.get(name + 'InnerSmooth') != None:
                        bpy.data.objects.remove(bpy.data.objects[name + 'InnerSmooth'], do_unlink=True)
                    set_finish(True)
                    if neibianjixian:
                        reset_and_dig_and_refill()
                    else:
                        reset_and_refill()
                    set_finish(False)
                    record_state()


# 是否启用边缘蓝线（框架式耳膜中的挖孔蓝线）
def HoleBorder(self, context):
    if get_is_processing_undo_redo():
        return
    enum = bpy.context.scene.muJuTypeEnum
    if enum == 'OP1' or enum == 'OP4':
        if context.scene.leftWindowObj == '右耳':
            neibianjixian = bpy.context.scene.neiBianJiXianR
            createmouldinit = bpy.context.scene.createmouldinitR
        elif context.scene.leftWindowObj == '左耳':
            neibianjixian = bpy.context.scene.neiBianJiXianL
            createmouldinit = bpy.context.scene.createmouldinitL

        if createmouldinit:
            if neibianjixian:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    reset_and_dig_and_refill()
                    record_state()
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    name = bpy.context.scene.leftWindowObj
                    for obj in bpy.data.objects:
                        if re.match(name + 'HoleBorderCurve', obj.name) is not None:
                            bpy.data.objects.remove(obj, do_unlink=True)
                    for obj in bpy.data.objects:
                        if re.match(name + 'meshHoleBorderCurve', obj.name) is not None:
                            bpy.data.objects.remove(obj, do_unlink=True)
                    reset_and_refill()
                    record_state()


# 通过面板参数调整硬耳膜底面平滑度
def CreateMouldHardDrumSmooth(self, context):
    if get_is_processing_undo_redo():
        return
    bl_description = "创建模具中的硬耳膜,平滑其底部边缘"

    override = getOverride()
    with bpy.context.temp_override(**override):
        track_time("参数调整平滑开始:")
        name = bpy.context.scene.leftWindowObj
        reset_obj = bpy.data.objects.get(name + "HardEarDrumForSmooth")

        if reset_obj:
            if bpy.context.scene.leftWindowObj == '右耳':
                pianyi = bpy.context.scene.yingErMoSheRuPianYiR
            else:
                pianyi = bpy.context.scene.yingErMoSheRuPianYiL
            if pianyi > 0.4:
                # 用offset_cut平滑
                hard_eardrum_smooth()
            elif 0 < pianyi <= 0.4:
                # 用平滑修改器平滑，避免偏移太小时offset_cut管道切割不成功的情况
                smooth_initial()
            else:
                obj = reset_obj.copy()
                obj.data = reset_obj.data.copy()
                obj.name = reset_obj.name + "HardEarDrumTemp"
                obj.animation_data_clear()
                bpy.context.scene.collection.objects.link(obj)
                if bpy.context.scene.leftWindowObj == '右耳':
                    moveToRight(obj)
                else:
                    moveToLeft(obj)
                obj.hide_set(False)
                bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
                obj.name = bpy.context.scene.leftWindowObj

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.context.active_object.data.use_auto_smooth = True
                bpy.context.object.data.auto_smooth_angle = 3.14159
                bpy.ops.object.modifier_add(type='DATA_TRANSFER')
                bpy.context.object.modifiers["DataTransfer"].object = bpy.data.objects[
                    bpy.context.scene.leftWindowObj + "ForBottomFillReset"]
                bpy.context.object.modifiers["DataTransfer"].vertex_group = "BottomOuterBorderVertex"
                bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
                bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'CUSTOM_NORMAL'}
                bpy.context.object.modifiers["DataTransfer"].loop_mapping = 'POLYINTERP_LNORPROJ'
                bpy.ops.object.modifier_apply(modifier="DataTransfer", single_user=True)
            record_state()
        track_time("参数调整平滑结束:")
        reset_time_tracker()


def xiaFangYangXianPianYi(self, context):
    bl_description = "更新下放线的偏移"
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        update_xiafangxian()
        record_state()


def mianBanPianYi(self, context):
    bl_description = "更新面板的偏移"
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        update_mianban()
        record_state()


def smooth_loft_part(self, context):
    bl_description = "更新放样部分的平滑度"
    if get_is_processing_undo_redo():
        return
    # if context.scene.leftWindowObj == '右耳':
    #     shellupdate = bpy.context.scene.shellupdateR
    # elif context.scene.leftWindowObj == '左耳':
    #     shellupdate = bpy.context.scene.shellupdateL
    # if not shellupdate:
    override = getOverride()
    with bpy.context.temp_override(**override):
        update_smooth_factor()
        record_state()


def ShellThicknessUpdate(self, context):
    bl_description = "更新外壳的分段厚度"
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        adjust_thickness()
        record_state()


def ShellRegionWidthUpdate(self, context):
    bl_description = "更新外壳的分段厚度"
    if get_is_processing_undo_redo():
        return
    if context.scene.leftWindowObj == '右耳':
        createmouldinit = bpy.context.scene.createmouldinitR
    elif context.scene.leftWindowObj == '左耳':
        createmouldinit = bpy.context.scene.createmouldinitL
    if createmouldinit:
        override = getOverride()
        with bpy.context.temp_override(**override):
            adjust_region_width()
            record_state()

def update_battery_shape(self, context):
    bl_description = "更新电池仓的类型"
    if get_is_processing_undo_redo():
        return

    override = getOverride()
    with bpy.context.temp_override(**override):
        change_battery_shape()
        record_state()


def updateShellCanal(self, context):
    bl_description = "是否开启管道功能"
    if get_is_processing_undo_redo():
        return

    override = getOverride()
    with bpy.context.temp_override(**override):
        updateshellCanalState()
        record_state()


def updateShellCanalDiameter(self, context):
    bl_description = "更新外壳管道的直径"
    if get_is_processing_undo_redo():
        return

    override = getOverride()
    with bpy.context.temp_override(**override):
        updateshellCanalDiameter()
        record_state()


def updateShellCanalThickness(self, context):
    bl_description = "更新管道外壳的厚度"
    if get_is_processing_undo_redo():
        return

    override = getOverride()
    with bpy.context.temp_override(**override):
        updateshellCanalThickness()
        record_state()


def updateCanalOffset(self, context):
    bl_description = "更新管道外壳的偏移"
    if get_is_processing_undo_redo():
        return

    override = getOverride()
    with bpy.context.temp_override(**override):
        updateshellCanalOffset()
        record_state()


def HandleOffsetUpdate(self, context):
    bl_description = "耳膜附件的偏移值,控制耳膜附件与耳膜的距离"
    if get_is_processing_undo_redo():
        return

    name = bpy.context.scene.leftWindowObj
    handle_offset = None
    if name == '右耳':
        handle_offset = bpy.context.scene.erMoFuJianOffset
    elif name == '左耳':
        handle_offset = bpy.context.scene.erMoFuJianOffsetL

    # 更新耳膜附件到耳膜的距离
    override = getOverride()
    with bpy.context.temp_override(**override):
        name = bpy.context.scene.leftWindowObj
        handle_obj = bpy.data.objects.get(name + "Cube")
        plane_obj = bpy.data.objects.get(name + "Plane")
        handle_compare_obj = bpy.data.objects.get(name + "Cube.001")
        if (handle_obj != None and plane_obj != None and handle_compare_obj != None):
            if handle_obj.type == 'MESH' and plane_obj.type == 'MESH' and handle_compare_obj.type == 'MESH':
                # 获取当前激活物体的网格数据
                me = handle_obj.data
                # 创建bmesh对象
                bm = bmesh.new()
                # 将网格数据复制到bmesh对象
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()

                ori_handle_me = handle_compare_obj.data
                ori_handle_bm = bmesh.new()
                ori_handle_bm.from_mesh(ori_handle_me)
                ori_handle_bm.verts.ensure_lookup_table()

                plane_me = plane_obj.data
                plane_bm = bmesh.new()
                plane_bm.from_mesh(plane_me)
                plane_bm.verts.ensure_lookup_table()

                # 获取平面法向
                plane_vert0 = plane_bm.verts[0]
                plane_vert1 = plane_bm.verts[1]
                plane_vert2 = plane_bm.verts[2]
                point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
                point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
                point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
                # 计算两个向量
                vector1 = point2 - point1
                vector2 = point3 - point1
                # 计算法向量
                normal = vector1.cross(vector2)
                # 根据面板参数设置偏移值
                for vert in bm.verts:
                    vert.co = ori_handle_bm.verts[vert.index].co + normal.normalized() * handle_offset
                    # vert.co += normal.normalized() * handle_offset

                bm.to_mesh(me)
                bm.free()
                ori_handle_bm.free()
                record_state()


def LabelTextUpdate(self, context):
    bl_description = "更新标签中的文本内容"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    labelText = None
    if name == '右耳':
        labelText = bpy.context.scene.labelText
    elif name == '左耳':
        labelText = bpy.context.scene.labelTextL
    # 将属性面板中的text属性值读取到剪切板中生成新的label
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelTextUpdate(labelText)
        record_state()


def LabelSizeUpdate(self, context):
    bl_description = "更新文本中字体的大小"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    size = None
    if name == '右耳':
        size = bpy.context.scene.fontSize
    elif name == '左耳':
        size = bpy.context.scene.fontSizeL
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelSizeUpdate(size)
        record_state()


def LabelDepthUpdate(self, context):
    bl_description = "更新文本中字体的高度"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    depth = None
    if name == '右耳':
        depth = bpy.context.scene.deep
    elif name == '左耳':
        depth = bpy.context.scene.deepL
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelDepthUpdate(depth)
        record_state()


def LabelEnum(self, context):
    bl_description = "切换Label的类型风格"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    enum = None
    if name == '右耳':
        enum = bpy.context.scene.styleEnum
    elif name == '左耳':
        enum = bpy.context.scene.styleEnumL
    if enum == "OP1":
        override = getOverride()
        with bpy.context.temp_override(**override):
            name = bpy.context.scene.leftWindowObj
            textname = name + "Text"
            text_obj = bpy.data.objects.get(textname)
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            if (text_obj != None and text_obj != None):
                bpy.context.view_layer.objects.active = text_obj
                red_material = newColor("Red", 1, 0, 0, 0, 1)
                text_obj.data.materials.clear()
                text_obj.data.materials.append(red_material)
                bpy.context.view_layer.objects.active = plane_obj
                record_state()
    if enum == "OP2":
        override = getOverride()
        with bpy.context.temp_override(**override):
            name = bpy.context.scene.leftWindowObj
            textname = name + "Text"
            text_obj = bpy.data.objects.get(textname)
            planename = name + "Plane"
            plane_obj = bpy.data.objects.get(planename)
            if (text_obj != None and text_obj != None):
                bpy.context.view_layer.objects.active = text_obj
                green_material = newColor("Blue", 0, 0.4, 1, 0, 1)
                text_obj.data.materials.clear()
                text_obj.data.materials.append(green_material)
                bpy.context.view_layer.objects.active = plane_obj
                record_state()


def CastingThicknessUpdate(self, context):
    bl_description = "更新铸造法厚度"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    thickness = None
    if name == '右耳':
        thickness = bpy.context.scene.ruanErMoHouDu
    elif name == '左耳':
        thickness = bpy.context.scene.ruanErMoHouDuL
    override = getOverride()
    with bpy.context.temp_override(**override):
        castingThicknessUpdate(thickness)
        record_state()


def SupportEnum(self, context):
    bl_description = "切换支撑的类型"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    enum = None
    if name == '右耳':
        enum = bpy.context.scene.zhiChengTypeEnum
    elif name == '左耳':
        enum = bpy.context.scene.zhiChengTypeEnumL
    # 添加硬耳膜支撑
    if enum == "OP1":
        override = getOverride()
        with bpy.context.temp_override(**override):
            supportSaveInfo()
            supportReset()
            supportInitial()

    # 添加软耳膜支撑
    if enum == "OP2":
        override = getOverride()
        with bpy.context.temp_override(**override):
            supportSaveInfo()
            supportReset()
            supportInitial()
            record_state()


def SupportOffsetUpdate(self, context):
    bl_description = "更新支撑沿法线的偏移值"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    support_enum = None
    support_offset = None
    if name == '右耳':
        support_enum = bpy.context.scene.zhiChengTypeEnum
        support_offset = bpy.context.scene.zhiChengOffset
    elif name == '左耳':
        support_enum = bpy.context.scene.zhiChengTypeEnumL
        support_offset = bpy.context.scene.zhiChengOffsetL
    override = getOverride()
    with bpy.context.temp_override(**override):
        if (support_enum == "OP1"):
            name = bpy.context.scene.leftWindowObj
            support_obj = bpy.data.objects.get(name + "Cone")
            plane_obj = bpy.data.objects.get(name + "Plane")
            support_compare_obj = bpy.data.objects.get(name + "ConeOffsetCompare")
            if (support_obj != None and plane_obj != None and support_compare_obj != None):
                if support_obj.type == 'MESH' and plane_obj.type == 'MESH' and support_compare_obj.type == 'MESH':
                    # 获取当前激活物体的网格数据
                    me = support_obj.data
                    # 创建bmesh对象
                    bm = bmesh.new()
                    # 将网格数据复制到bmesh对象
                    bm.from_mesh(me)
                    bm.verts.ensure_lookup_table()

                    ori_support_me = support_compare_obj.data
                    ori_support_bm = bmesh.new()
                    ori_support_bm.from_mesh(ori_support_me)
                    ori_support_bm.verts.ensure_lookup_table()

                    plane_me = plane_obj.data
                    plane_bm = bmesh.new()
                    plane_bm.from_mesh(plane_me)
                    plane_bm.verts.ensure_lookup_table()

                    # 获取平面法向
                    plane_vert0 = plane_bm.verts[0]
                    plane_vert1 = plane_bm.verts[1]
                    plane_vert2 = plane_bm.verts[2]
                    point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
                    point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
                    point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
                    # 计算两个向量
                    vector1 = point2 - point1
                    vector2 = point3 - point1
                    # 计算法向量
                    normal = vector1.cross(vector2)
                    # 根据面板参数设置偏移值
                    for vert in bm.verts:
                        vert.co = ori_support_bm.verts[vert.index].co + normal.normalized() * support_offset

                    bm.to_mesh(me)
                    bm.free()
                    ori_support_bm.free()
                    record_state()
        elif (support_enum == "OP2"):
            name = bpy.context.scene.leftWindowObj
            soft_support_inner_obj = bpy.data.objects.get(name + "SoftSupportInner")
            soft_support_outer_obj = bpy.data.objects.get(name + "SoftSupportOuter")
            soft_support_inside_obj = bpy.data.objects.get(name + "SoftSupportInside")
            soft_support_inner_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInnerOffsetCompare")
            soft_support_outer_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportOuterOffsetCompare")
            soft_support_inside_offset_compare_obj = bpy.data.objects.get(name + "SoftSupportInsideOffsetCompare")
            plane_obj = bpy.data.objects.get(name + "Plane")
            if (soft_support_inner_obj != None and soft_support_outer_obj != None and soft_support_inside_obj != None
                    and soft_support_inner_offset_compare_obj != None and soft_support_outer_offset_compare_obj != None
                    and soft_support_inside_offset_compare_obj != None and plane_obj != None):
                if soft_support_outer_obj.type == 'MESH' and plane_obj.type == 'MESH' and soft_support_outer_offset_compare_obj.type == 'MESH':

                    me = soft_support_outer_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(me)
                    bm.verts.ensure_lookup_table()
                    ori_sprue_me = soft_support_outer_offset_compare_obj.data
                    ori_sprue_bm = bmesh.new()
                    ori_sprue_bm.from_mesh(ori_sprue_me)
                    ori_sprue_bm.verts.ensure_lookup_table()

                    me1 = soft_support_inner_obj.data
                    bm1 = bmesh.new()
                    bm1.from_mesh(me1)
                    bm1.verts.ensure_lookup_table()
                    ori_sprue_me1 = soft_support_inner_offset_compare_obj.data
                    ori_sprue_bm1 = bmesh.new()
                    ori_sprue_bm1.from_mesh(ori_sprue_me1)
                    ori_sprue_bm1.verts.ensure_lookup_table()

                    me2 = soft_support_inside_obj.data
                    bm2 = bmesh.new()
                    bm2.from_mesh(me2)
                    bm2.verts.ensure_lookup_table()
                    ori_sprue_me2 = soft_support_inside_offset_compare_obj.data
                    ori_sprue_bm2 = bmesh.new()
                    ori_sprue_bm2.from_mesh(ori_sprue_me2)
                    ori_sprue_bm2.verts.ensure_lookup_table()

                    plane_me = plane_obj.data
                    plane_bm = bmesh.new()
                    plane_bm.from_mesh(plane_me)
                    plane_bm.verts.ensure_lookup_table()

                    # 获取平面法向
                    plane_vert0 = plane_bm.verts[0]
                    plane_vert1 = plane_bm.verts[1]
                    plane_vert2 = plane_bm.verts[2]
                    point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
                    point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
                    point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
                    # 计算两个向量
                    vector1 = point2 - point1
                    vector2 = point3 - point1
                    # 计算法向量
                    normal = vector1.cross(vector2)
                    # 根据面板参数设置偏移值
                    for vert in bm.verts:
                        vert.co = ori_sprue_bm.verts[vert.index].co + normal.normalized() * support_offset
                    for vert in bm1.verts:
                        vert.co = ori_sprue_bm1.verts[vert.index].co + normal.normalized() * support_offset
                    for vert in bm2.verts:
                        vert.co = ori_sprue_bm2.verts[vert.index].co + normal.normalized() * support_offset
                    bm.to_mesh(me)
                    bm.free()
                    ori_sprue_bm.free()
                    bm1.to_mesh(me1)
                    bm1.free()
                    ori_sprue_bm1.free()
                    bm2.to_mesh(me2)
                    bm2.free()
                    ori_sprue_bm2.free()
                    record_state()


def SprueOffsetUpdate(self, context):
    bl_description = "更新排气孔沿法线的偏移值"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    sprue_offset = None
    if name == '右耳':
        sprue_offset = bpy.context.scene.paiQiKongOffset
    elif name == '左耳':
        sprue_offset = bpy.context.scene.paiQiKongOffsetL
    override = getOverride()
    with bpy.context.temp_override(**override):
        name = bpy.context.scene.leftWindowObj
        sprue_inner_obj = bpy.data.objects.get(name + "CylinderInner")
        sprue_outer_obj = bpy.data.objects.get(name + "CylinderOuter")
        sprue_inside_obj = bpy.data.objects.get(name + "CylinderInside")
        sprue_inner_offset_compare_obj = bpy.data.objects.get(name + "CylinderInnerOffsetCompare")
        sprue_outer_offset_compare_obj = bpy.data.objects.get(name + "CylinderOuterOffsetCompare")
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name + "CylinderInsideOffsetCompare")
        plane_obj = bpy.data.objects.get(name + "Plane")
        if (sprue_outer_obj != None and sprue_inner_obj != None and sprue_inside_obj != None
                and sprue_outer_offset_compare_obj != None and sprue_inner_offset_compare_obj != None
                and sprue_inside_offset_compare_obj != None and plane_obj != None):
            if sprue_outer_obj.type == 'MESH' and plane_obj.type == 'MESH' and sprue_outer_offset_compare_obj.type == 'MESH':

                me = sprue_outer_obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                ori_sprue_me = sprue_outer_offset_compare_obj.data
                ori_sprue_bm = bmesh.new()
                ori_sprue_bm.from_mesh(ori_sprue_me)
                ori_sprue_bm.verts.ensure_lookup_table()

                me1 = sprue_inner_obj.data
                bm1 = bmesh.new()
                bm1.from_mesh(me1)
                bm1.verts.ensure_lookup_table()
                ori_sprue_me1 = sprue_inner_offset_compare_obj.data
                ori_sprue_bm1 = bmesh.new()
                ori_sprue_bm1.from_mesh(ori_sprue_me1)
                ori_sprue_bm1.verts.ensure_lookup_table()

                me2 = sprue_inside_obj.data
                bm2 = bmesh.new()
                bm2.from_mesh(me2)
                bm2.verts.ensure_lookup_table()
                ori_sprue_me2 = sprue_inside_offset_compare_obj.data
                ori_sprue_bm2 = bmesh.new()
                ori_sprue_bm2.from_mesh(ori_sprue_me2)
                ori_sprue_bm2.verts.ensure_lookup_table()

                plane_me = plane_obj.data
                plane_bm = bmesh.new()
                plane_bm.from_mesh(plane_me)
                plane_bm.verts.ensure_lookup_table()

                # 获取平面法向
                plane_vert0 = plane_bm.verts[0]
                plane_vert1 = plane_bm.verts[1]
                plane_vert2 = plane_bm.verts[2]
                point1 = mathutils.Vector((plane_vert0.co[0], plane_vert0.co[1], plane_vert0.co[2]))
                point2 = mathutils.Vector((plane_vert1.co[0], plane_vert1.co[1], plane_vert1.co[2]))
                point3 = mathutils.Vector((plane_vert2.co[0], plane_vert2.co[1], plane_vert2.co[2]))
                # 计算两个向量
                vector1 = point2 - point1
                vector2 = point3 - point1
                # 计算法向量
                normal = vector1.cross(vector2)
                # 根据面板参数设置偏移值
                for vert in bm.verts:
                    vert.co = ori_sprue_bm.verts[vert.index].co + normal.normalized() * sprue_offset
                for vert in bm1.verts:
                    vert.co = ori_sprue_bm1.verts[vert.index].co + normal.normalized() * sprue_offset
                for vert in bm2.verts:
                    vert.co = ori_sprue_bm2.verts[vert.index].co + normal.normalized() * sprue_offset
                bm.to_mesh(me)
                bm.free()
                ori_sprue_bm.free()
                bm1.to_mesh(me1)
                bm1.free()
                ori_sprue_bm1.free()
                bm2.to_mesh(me2)
                bm2.free()
                ori_sprue_bm2.free()
                record_state()


def soundcanalupdate(self, context):
    bl_description = "更新传声孔的直径大小"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        diameter = bpy.context.scene.chuanShenGuanDaoZhiJing
    else:
        diameter = bpy.context.scene.chuanShenGuanDaoZhiJing_L
    for obj in bpy.data.objects:
        if obj.name == name + 'soundcanal':
            obj.data.bevel_depth = diameter / 2
    convert_soundcanal()
    record_state()


def soundcanalShape(self, context):
    bl_description = "普通管道和号角管之间的切换"
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        update_hornpipe_enum()
        record_state()


def soundcanalHornpipeOffset(self, context):
    bl_description = "号角管偏移"
    if get_is_processing_undo_redo():
        return
    override = getOverride()
    with bpy.context.temp_override(**override):
        # 先根据面板的offset参数和管道末端红球位置找到 偏移点,将号角管在偏移点出摆正对齐
        update_hornpipe_offset()
        record_state()


def ventcanalupdate(self, context):
    bl_description = "更新通气孔的直径大小"
    if get_is_processing_undo_redo():
        return
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        diameter = bpy.context.scene.tongQiGuanDaoZhiJing
    else:
        diameter = bpy.context.scene.tongQiGuanDaoZhiJing_L
    for obj in bpy.data.objects:
        if obj.name == name + 'ventcanal':
            obj.data.bevel_depth = diameter / 2
    # 更新网格数据
    convert_ventcanal()
    record_state()


def appendmaterial(type, name, material_name, percent):
    obj = bpy.data.objects.get(name)

    if obj:
        if type == 'OP1':  # 自动，一般为实体
            obj.data.materials.clear()
            obj.data.materials.append(bpy.data.materials.get(material_name))
            changealpha(material_name, 1)
        elif type == 'OP2':  # 不透明
            obj.data.materials.clear()
            obj.data.materials.append(bpy.data.materials.get(material_name))
            changealpha(material_name, 1)
        elif type == "OP3":  # 透明
            obj.data.materials.clear()
            obj.data.materials.append(bpy.data.materials.get(material_name))
            changealpha(material_name, percent)


def changealpha(material_name, alpha):
    mat = bpy.data.materials.get(material_name)

    if mat:
        if alpha == 1:
            mat.blend_method = 'OPAQUE'
            mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
        else:
            mat.blend_method = 'BLEND'
            mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = alpha


# 最原始的模型
def show_transparent1(self, context):
    name = context.scene.leftWindowObj + 'OriginForShow'
    obj = bpy.data.objects.get(name)
    if context.scene.leftWindowObj == '右耳':
        is_show = context.scene.transparent1R
        type = context.scene.transparent1EnumR
        percent = 1 - float(bpy.context.scene.transparentper1EnumR)
        mat_name = "tran_green_r"
    elif context.scene.leftWindowObj == '左耳':
        is_show = context.scene.transparent1L
        type = context.scene.transparent1EnumL
        percent = 1 - float(bpy.context.scene.transparentper1EnumL)
        mat_name = "tran_green_l"

    if obj and is_show:
        if obj.hide_get():
            obj.hide_set(False)
        appendmaterial(type, name, mat_name, percent)
    elif obj and not is_show:
        if not obj.hide_get():
            obj.hide_set(True)


def update_transparent1(self, context):
    name = context.scene.leftWindowObj + 'OriginForShow'
    obj = bpy.data.objects.get(name)
    if obj:
        if context.scene.leftWindowObj == '右耳' and context.scene.transparent1R:
            type = context.scene.transparent1EnumR
            percent = 1 - float(bpy.context.scene.transparentper1EnumR)
            appendmaterial(type, name, "tran_green_r", percent)
        elif context.scene.leftWindowObj == '左耳' and context.scene.transparent1L:
            type = context.scene.transparent1EnumL
            percent = 1 - float(bpy.context.scene.transparentper1EnumL)
            appendmaterial(type, name, "tran_green_l", percent)


def update_transparentper1(self, context):
    name = context.scene.leftWindowObj + 'OriginForShow'
    obj = bpy.data.objects.get(name)
    if obj:
        if context.scene.leftWindowObj == '右耳' and context.scene.transparent1R:
            percent = 1 - float(context.scene.transparentper1EnumR)
            changealpha("tran_green_r", percent)
        elif context.scene.leftWindowObj == '左耳' and context.scene.transparent1L:
            percent = 1 - float(context.scene.transparentper1EnumL)
            changealpha("tran_green_l", percent)


# 完成打磨后的模型
def show_transparent2(self, context):
    if ((bpy.context.screen.areas[0].spaces.active.context == 'RENDER') or
            (bpy.context.screen.areas[0].spaces.active.context == 'MATERIAL' and get_color_mode() == 1)):
        name = context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        if name == '右耳':
            is_show = context.scene.transparent2R
            type = context.scene.transparent2EnumR
            mat_name = "YellowR"
            percent = 1 - float(bpy.context.scene.transparentper2EnumR)
        elif name == '左耳':
            is_show = context.scene.transparent2L
            type = context.scene.transparent2EnumL
            mat_name = "YellowL"
            percent = 1 - float(bpy.context.scene.transparentper2EnumL)

    else:
        name = context.scene.leftWindowObj + 'WaxForShow'
        obj = bpy.data.objects.get(name)
        if context.scene.leftWindowObj == '右耳':
            is_show = context.scene.transparent2R
            type = context.scene.transparent2EnumR
            mat_name = "tran_blue_r"
            percent = 1 - float(bpy.context.scene.transparentper2EnumR)
        elif context.scene.leftWindowObj == '左耳':
            is_show = context.scene.transparent2L
            type = context.scene.transparent2EnumL
            mat_name = "tran_blue_l"
            percent = 1 - float(bpy.context.scene.transparentper2EnumL)

    if obj and is_show:
        if obj.hide_get():
            obj.hide_set(False)
        appendmaterial(type, name, mat_name, percent)
    elif obj and not is_show:
        if not obj.hide_get():
            obj.hide_set(True)


def update_transparent2(self, context):
    if ((bpy.context.screen.areas[0].spaces.active.context == 'RENDER') or
            (bpy.context.screen.areas[0].spaces.active.context == 'MATERIAL' and get_color_mode() == 1)):
        name = context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        if name == '右耳':
            is_show = context.scene.transparent2R
            type = context.scene.transparent2EnumR
            percent = 1 - float(bpy.context.scene.transparentper2EnumR)
            mat_name = "YellowR"
        elif name == '左耳':
            is_show = context.scene.transparent2L
            type = context.scene.transparent2EnumL
            percent = 1 - float(bpy.context.scene.transparentper2EnumL)
            mat_name = "YellowL"

    else:
        name = context.scene.leftWindowObj + 'WaxForShow'
        obj = bpy.data.objects.get(name)
        if context.scene.leftWindowObj == '右耳':
            is_show = context.scene.transparent2R
            type = context.scene.transparent2EnumR
            percent = 1 - float(bpy.context.scene.transparentper2EnumR)
            mat_name = "tran_blue_r"
        elif context.scene.leftWindowObj == '左耳':
            is_show = context.scene.transparent2L
            type = context.scene.transparent2EnumL
            percent = 1 - float(bpy.context.scene.transparentper2EnumL)
            mat_name = "tran_blue_l"

    if obj and is_show:
        appendmaterial(type, name, mat_name, percent)


def update_transparentper2(self, context):
    if ((bpy.context.screen.areas[0].spaces.active.context == 'RENDER') or
            (bpy.context.screen.areas[0].spaces.active.context == 'MATERIAL' and get_color_mode() == 1)):
        name = context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        if name == '右耳':
            is_show = context.scene.transparent2R
            percent = 1 - float(context.scene.transparentper2EnumR)
            mat_name = "YellowR"
        elif name == '左耳':
            is_show = context.scene.transparent2L
            percent = 1 - float(context.scene.transparentper2EnumL)
            mat_name = "YellowL"

    else:
        name = context.scene.leftWindowObj + 'WaxForShow'
        obj = bpy.data.objects.get(name)
        if context.scene.leftWindowObj == '右耳':
            is_show = context.scene.transparent2R
            percent = 1 - float(context.scene.transparentper2EnumR)
            mat_name = "tran_blue_r"
        elif context.scene.leftWindowObj == '左耳':
            is_show = context.scene.transparent2L
            percent = 1 - float(context.scene.transparentper2EnumL)
            mat_name = "tran_blue_l"

    if obj and is_show:
        changealpha(mat_name, percent)


# 正在操作的模型
def show_transparent3(self, context):
    current_tab = bpy.context.screen.areas[0].spaces.active.context
    # 从打磨切到切割模具
    if current_tab == 'MATERIAL' and get_color_mode() == 1:
        name = context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        if bpy.data.objects.get(name + 'cutmouldforshow') != None:
            bpy.data.objects.remove(bpy.data.objects[name + 'cutmouldforshow'], do_unlink=True)
        duplicate_obj = obj.copy()
        duplicate_obj.data = obj.data.copy()
        duplicate_obj.animation_data_clear()
        duplicate_obj.name = name + "cutmouldforshow"
        bpy.context.collection.objects.link(duplicate_obj)
        obj = duplicate_obj

        if name == '右耳':
            is_show = context.scene.transparent3R
            type = context.scene.transparent3EnumR
            mat = newMaterial("cutmould_yellow_r")
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            output = nodes.new(type='ShaderNodeOutputMaterial')
            shader = nodes.new(type='ShaderNodeBsdfPrincipled')
            shader.inputs[0].default_value = (1, 0.319, 0.133, 1)
            links.new(shader.outputs[0], output.inputs[0])
            mat_name = "cutmould_yellow_r"
            percent = 1 - float(bpy.context.scene.transparentper3EnumR)
            moveToRight(duplicate_obj)
            # obj.data.materials.append(bpy.data.materials.get("YellowR"))
            obj.hide_set(True)

        elif name == '左耳':
            is_show = context.scene.transparent3L
            type = context.scene.transparent3EnumL
            mat = newMaterial("cutmould_yellow_l")
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            output = nodes.new(type='ShaderNodeOutputMaterial')
            shader = nodes.new(type='ShaderNodeBsdfPrincipled')
            shader.inputs[0].default_value = (1, 0.319, 0.133, 1)
            links.new(shader.outputs[0], output.inputs[0])
            mat_name = "cutmould_yellow_l"
            percent = 1 - float(bpy.context.scene.transparentper3EnumL)
            moveToLeft(duplicate_obj)
            # obj.data.materials.append(bpy.data.materials.get("YellowL"))
            obj.hide_set(True)

        name = obj.name

    # 在打磨模块
    elif current_tab == 'RENDER':
        return

    else:
        name = context.scene.leftWindowObj
        obj = bpy.data.objects.get(name)
        if name == '右耳':
            is_show = context.scene.transparent3R
            type = context.scene.transparent3EnumR
            percent = 1 - float(bpy.context.scene.transparentper3EnumR)
            mat_name = "YellowR"
            if (current_tab == 'OUTPUT'):
                name = name + "LocalThickCompare"
        elif name == '左耳':
            is_show = context.scene.transparent3L
            type = context.scene.transparent3EnumL
            percent = 1 - float(bpy.context.scene.transparentper3EnumL)
            mat_name = "YellowL"
            if (current_tab == 'OUTPUT'):
                name = name + "LocalThickCompare"

    if obj and is_show:
        if obj.hide_get():
            obj.hide_set(False)
        appendmaterial(type, name, mat_name, percent)
    elif obj and not is_show:
        if not obj.hide_get():
            obj.hide_set(True)


def update_transparent3(self, context):
    '''
        物体处于Auto状态下,是否透明取决于当前所处的模块以及对当前模块所作的操作
    '''
    current_tab = bpy.context.screen.areas[0].spaces.active.context
    name = context.scene.leftWindowObj
    # 局部加厚模式下透明模式物体为作为对比的LocalThickCompare
    if (current_tab == 'OUTPUT'):
        cur_name = name + "LocalThickCompare"
    # # 铸造法模式下透明模式物体为内部的红色物体CastingCompare
    # elif(current_tab == "PARTICLES"):
    #     cur_name = name + "CastingCompare"
    #     material_name = "CastingRed"
    elif (current_tab == "MATERIAL" and get_color_mode() == 1):
        cur_name = name + "cutmouldforshow"
    else:
        cur_name = name

    obj = bpy.data.objects.get(cur_name)
    if obj:
        if name == '右耳' and context.scene.transparent3R:
            material_name = "YellowR"
            if (current_tab == "MATERIAL" and get_color_mode() == 1):
                material_name = "cutmould_yellow_r"
            type = context.scene.transparent3EnumR
            percent = 1 - float(bpy.context.scene.transparentper3EnumR)
            appendmaterial(type, cur_name, material_name, percent)
        elif name == '左耳' and context.scene.transparent3L:
            material_name = "YellowL"
            if (current_tab == "MATERIAL" and get_color_mode() == 1):
                material_name = "cutmould_yellow_l"
            type = context.scene.transparent3EnumL
            percent = 1 - float(bpy.context.scene.transparentper3EnumL)
            appendmaterial(type, cur_name, material_name, percent)


def update_transparentper3(self, context):
    current_tab = bpy.context.screen.areas[0].spaces.active.context
    name = context.scene.leftWindowObj
    # 局部加厚模式下透明模式物体为作为对比的LocalThickCompare
    if (current_tab == 'OUTPUT'):
        cur_name = name + "LocalThickCompare"
    # 铸造法模式下透明模式物体为内部的红色物体CastingCompare
    # elif (current_tab == "PARTICLES"):
    #     cur_name = name + "CastingCompare"
    #     material_name = "CastingRed"
    elif (current_tab == "MATERIAL" and get_color_mode() == 1):
        cur_name = name + "cutmouldforshow"
    else:
        cur_name = name

    obj = bpy.data.objects.get(cur_name)
    if obj:
        if name == '右耳' and context.scene.transparent3R:
            material_name = "YellowR"
            if (current_tab == "MATERIAL" and get_color_mode() == 1):
                material_name = "cutmould_yellow_r"
            percent = 1 - float(context.scene.transparentper3EnumR)
            changealpha(material_name, percent)
        elif name == '左耳' and context.scene.transparent3L:
            material_name = "YellowL"
            if (current_tab == "MATERIAL" and get_color_mode() == 1):
                material_name = "cutmould_yellow_l"
            percent = 1 - float(context.scene.transparentper3EnumL)
            changealpha(material_name, percent)


def register():
    My_Properties()
