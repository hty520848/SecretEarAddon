import bpy.props

from .damo import remember_vertex_change, get_modal_start, get_is_back, get_is_dialog
from .jiahou import *
from .create_tip.qiege import *
from .label import *
from .support import *
from .create_mould.soft_eardrum.thickness_and_fill import reset_and_refill
from .create_mould.frame_style_eardrum.frame_style_eardrum import recover_and_refill
from .create_mould.hard_eardrum.hard_eardrum_bottom_fill import smooth_initial,hard_eardrum_smooth
from .create_mould.create_mould import recover,set_is_cut_finish
from .sound_canal import initial_hornpipe, update_hornpipe_offset_location_normal, convert_soundcanal, get_object_dic_index
from .vent_canal import convert_ventcanal
from .casting import castingThicknessUpdate

import os

import datetime

font_info = {
    "font_id": 0,
    "handler": None,
}


def My_Properties():
    # 全局变量,多个模块的文件共享该全局变量,各个模式的按钮都会有一个var值,当该按钮处于其对应的值时,会运行其操作符,不再其对应值时,会自动结束该操作符
    # 默认var值为0,各个操作符都未启动
    # 打磨模块:       打磨加厚按钮: 1        打磨打薄按钮:  2      打磨平滑按钮:  3       打磨重置按钮:  4
    # 局部加厚模块:   局部加厚重置: 9        局部加厚扩大区域: 5       局部加厚缩小区域: 6        局部加厚加厚: 7    局部加厚提交: 8
    # 切割模块:由于切割模式在初始化时会自动进入切割模态,退出时自动退出切割模块,故切割模块未使用该变量
    bpy.types.Scene.var = bpy.props.IntProperty(
        name="var", default=0, description="每个模块的按钮都会对应一个var值,用于结束按钮的modal"
    )

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
        name="localLaHouDu", default=False, update=localLaHouDu)
    bpy.types.Scene.maxLaHouDuR = bpy.props.FloatProperty(
        name="maxLaHouDu", min=-1.0, max=1.0, step=1, default=0.5,
        description="最大蜡厚度的值", update=localLaHouDu)
    bpy.types.Scene.minLaHouDuR = bpy.props.FloatProperty(
        name="minLaHouDu", min=-1.0, max=1.0, step=1, default=-0.5,
        description="最小蜡厚度的值", update=localLaHouDu)
    bpy.types.Scene.localLaHouDuL = bpy.props.BoolProperty(
        name="localLaHouDuL", default=False, update=localLaHouDu)
    bpy.types.Scene.damo_circleRadius_R = bpy.props.FloatProperty(
        name="damo_circleRadius",  default=50)
    bpy.types.Scene.damo_strength_R = bpy.props.FloatProperty(
        name="damo_strength_R", default=0.5)
    bpy.types.Scene.damo_scale_strength_R = bpy.props.FloatProperty(
        name="damo_scale_strength_R", min=0.1, max=10, step=10, default=1,
        description="调整笔刷的强度", update=scale_strength)
    bpy.types.Scene.maxLaHouDuL = bpy.props.FloatProperty(
        name="maxLaHouDuL", min=-1.0, max=1.0, step=1, default=0.5,
        description="最大蜡厚度的值", update=localLaHouDu)
    bpy.types.Scene.minLaHouDuL = bpy.props.FloatProperty(
        name="minLaHouDuL", min=-1.0, max=1.0, step=1, default=-0.5,
        description="最小蜡厚度的值", update=localLaHouDu)
    bpy.types.Scene.damo_circleRadius_L = bpy.props.FloatProperty(
        name="damo_circleRadius_L",  default=50)
    bpy.types.Scene.damo_strength_L = bpy.props.FloatProperty(
        name="damo_strength_L", default=0.5)
    bpy.types.Scene.damo_scale_strength_L = bpy.props.FloatProperty(
        name="damo_scale_strength_L", min=0.1, max=10, step=10, default=1,
        description="调整笔刷的强度", update=scale_strength)

    # 局部或整体加厚    偏移值，边框宽度
    # 右耳属性
    bpy.types.Scene.localThicking_offset = bpy.props.FloatProperty(
        name="localThicking_offset", min=0, max=3.0, default=0.8, update=LocalThickeningOffsetUpdate)
    bpy.types.Scene.localThicking_borderWidth = bpy.props.FloatProperty(
        name="localThicking_borderWidth", min=0, max=8.0, default=0.8, update=LocalThickeningBorderWidthUpdate)
    bpy.types.Scene.localThicking_circleRedius = bpy.props.FloatProperty(
        name="localThicking_circleRedius",  default=50)
    bpy.types.Scene.is_thickening_completed = bpy.props.BoolProperty(
        name="is_thickening_completed")  # 防止局部加厚中的参数更新过快使得加厚参数调用的过于频繁,使得物体发生形变
    # 左耳属性
    bpy.types.Scene.localThicking_offset_L = bpy.props.FloatProperty(
        name="localThicking_offset_L", min=0, max=3.0, default=0.8, update=LocalThickeningOffsetUpdate_L)
    bpy.types.Scene.localThicking_borderWidth_L = bpy.props.FloatProperty(
        name="localThicking_borderWidth_L", min=0, max=8.0, default=0.8, update=LocalThickeningBorderWidthUpdate_L)
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
        name="sheRuPianYi", min=0.0, max=3, step=10, default=0.5, update=sheru)

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
        name="sheRuPianYi", min=0.0, max=3, step=10, default=0.5, update=sheru)

    bpy.types.Scene.qiegewaiBianYuanL = bpy.props.FloatProperty(
        name="qiegewaiBianYuanL", min=0.1, max=1,
        step=10, update=stepcutoutborder, default=0.2)
    bpy.types.Scene.qiegeneiBianYuanL = bpy.props.FloatProperty(
        name="qiegeneiBianYuanL", min=1, max=3, step=10, update=stepcutinnerborder, default=1)
    # 创建模具属性

    # 参数、模具面板切换
    bpy.types.Scene.tabEnum = bpy.props.EnumProperty(
        name="tab",
        description='参数面板和模板选择面板切换',
        items=[
            ('参数', '参数', ''),
            ('模板', '模板', '')],
        # default = '模板' 
    )

    bpy.types.Scene.showHdu = bpy.props.BoolProperty(
        name="showMenu", default=True)

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
    # 勾选右耳
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

    # sed文件
    bpy.types.Scene.expSedFile_path = bpy.props.StringProperty(name="",
                                                               description="Sed模板",
                                                               default="",
                                                               maxlen=1024,
                                                               subtype="FILE_PATH")

    # 另存为模板属性
    # 模板描述
    bpy.types.Scene.save_desc = bpy.props.StringProperty(name="",
                                                         description="模板描述",
                                                         default="",
                                                         maxlen=1024)

    # 左侧模型属性是否保存
    bpy.types.Scene.leftDamo = bpy.props.BoolProperty(
        name="leftDamo", default=True)

    bpy.types.Scene.leftQiege = bpy.props.BoolProperty(
        name="leftQiege", default=True)

    bpy.types.Scene.leftChuangjianmoju = bpy.props.BoolProperty(
        name="leftChuangjianmoju", default=False)

    bpy.types.Scene.leftChuanshengkong = bpy.props.BoolProperty(
        name="leftChuanshengkong", default=True)

    bpy.types.Scene.leftTongqikong = bpy.props.BoolProperty(
        name="leftTongqikong", default=False)

    bpy.types.Scene.leftFujian = bpy.props.BoolProperty(
        name="leftFujian", default=True)

    bpy.types.Scene.leftRuanermohoudu = bpy.props.BoolProperty(
        name="leftRuanermohoudu", default=True)

    # 右侧模型属性是否保存
    bpy.types.Scene.rightDamo = bpy.props.BoolProperty(
        name="rightDamo", default=True)

    bpy.types.Scene.rightQiege = bpy.props.BoolProperty(
        name="rightQiege", default=True)

    bpy.types.Scene.rightChuangjianmoju = bpy.props.BoolProperty(
        name="rightChuangjianmoju", default=False)

    bpy.types.Scene.rightChuanshengkong = bpy.props.BoolProperty(
        name="rightChuanshengkong", default=True)

    bpy.types.Scene.rightTongqikong = bpy.props.BoolProperty(
        name="rightTongqikong", default=False)

    bpy.types.Scene.rightFujian = bpy.props.BoolProperty(
        name="rightFujian", default=True)

    bpy.types.Scene.rightRuanermohoudu = bpy.props.BoolProperty(
        name="rightRuanermohoudu", default=True)

    bpy.types.Scene.muJuNameEnum = bpy.props.StringProperty(name="",
                                                            description="",
                                                            default="硬耳膜",
                                                            maxlen=1024)

    bpy.types.Scene.muJuTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '软耳模', '', 'RUANERMO', 1),
            ('OP2', '硬耳膜', '', 'YINGERMO', 2),
            ('OP3', '一体外壳', '', 'YITI', 3),
            ('OP4', '框架式耳膜', '', 'KUANGJIA', 4),
            ('OP5', '常规外壳', '', 'CHANGGUI', 5),
            ('OP6', '实心面板', '', 'SHIXIN', 6)],
        update=ChangeMouldType,
        default='OP2'
    )
    bpy.types.Scene.neiBianJiXian = bpy.props.BoolProperty(
        name="neiBianJiXian")
    bpy.types.Scene.waiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="waiBianYuanSheRuPianYi", min=0.0, max=3.0,default=2, update=CreateMouldOuterSmooth)
    bpy.types.Scene.neiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="neiBianYuanSheRuPianYi", min=0.0, max=3.0, default=2,update=CreateMouldInnerSmooth)

    bpy.types.Scene.zongHouDu = bpy.props.FloatProperty(
        name="zongHouDu", min=0.5, max=3.0, default=1, update=CreateMouldThicknessUpdate)
    bpy.types.Scene.zongHouDuUpdateCompleled = bpy.props.BoolProperty(
        name="zongHouDuUpdateCompleled",default = True)
    bpy.types.Scene.jiHuoBianYuanHouDu = bpy.props.BoolProperty(
        name="jiHuoBianYuanHouDu")
    bpy.types.Scene.waiBuHouDu = bpy.props.FloatProperty(
        name="waiBuHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.waiBuQuYuKuanDu = bpy.props.FloatProperty(
        name="waiBuQuYuKuanDu", min=-1.0, max=1.0)
    bpy.types.Scene.zhongJianHouDu = bpy.props.FloatProperty(
        name="zhongJianHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouShiYongNeiBu = bpy.props.BoolProperty(
        name="shiFouShiYongNeiBu")
    bpy.types.Scene.zhongJianQuYuKuanDu = bpy.props.FloatProperty(
        name="zhongJianQuYuKuanDu", min=-1.0, max=1.0)
    bpy.types.Scene.neiBuHouDu = bpy.props.FloatProperty(
        name="neiBuHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.mianBanTypeEnum = bpy.props.EnumProperty(
        name="mianBanTypeEnum",
        description='this is option',
        items=[
            ('OP1', '312空面板', '')]
    )
    bpy.types.Scene.jieShouQiTypeEnum = bpy.props.EnumProperty(
        name="jieShouQiTypeEnum",
        description='this is option',
        items=[
            ('OP1', 'REC31570', '')]
    )
    bpy.types.Scene.jieShouQiKaiGuanTypeEnum = bpy.props.EnumProperty(
        name="jieShouQiKaiGuanTypeEnum",
        description='this is option',
        items=[
            ('OP1', '外置套管', '')]
    )
    bpy.types.Scene.buJianBTypeEenu = bpy.props.EnumProperty(
        name="buJianBTypeEenu",
        description='this is option',
        items=[
            ('OP1', 'E7111', '')]
    )
    bpy.types.Scene.mianBanPianYi = bpy.props.FloatProperty(
        name="mianBanPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.xiaFangYangXianPianYi = bpy.props.FloatProperty(
        name="xiaFangYangXianPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.shangSheRuYinZi = bpy.props.FloatProperty(
        name="shangSheRuYinZi", min=-1.0, max=1.0)
    bpy.types.Scene.xiaSheRuYinZi = bpy.props.FloatProperty(
        name="xiaSheRuYinZi", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouShangBuQieGeMianBan = bpy.props.BoolProperty(
        name="shiFouShangBuQieGeMianBan")
    bpy.types.Scene.shangBuQieGeMianBanPianYi = bpy.props.FloatProperty(
        name="shangBuQieGeMianBanPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouKongQiangMianBan = bpy.props.BoolProperty(
        name="shiFouKongQiangMianBan",default=True)
    bpy.types.Scene.KongQiangMianBanSheRuPianYi = bpy.props.FloatProperty(
        name="KongQiangMianBanSheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.ShangBuQieGeBanPianYi = bpy.props.FloatProperty(
        name="ShangBuQieGeBanPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.gongXingMianBan = bpy.props.FloatProperty(
        name="gongXingMianBan", min=-1.0, max=1.0)
    bpy.types.Scene.gongKuan = bpy.props.FloatProperty(
        name="gongKuan", min=-1.0, max=1.0)
    bpy.types.Scene.gongGao = bpy.props.FloatProperty(
        name="gongGao", min=-1.0, max=1.0)
    bpy.types.Scene.yingErMoLowestZCo = bpy.props.FloatProperty(
        description='该参数主要起到共享变量的作用,使得createmould文件中能够读取到hardmould文件中的参数',
        name="yingErMoLowestZCo", min=-24.0, max=24.0)
    bpy.types.Scene.yingErMoSheRuPianYiL = bpy.props.FloatProperty(
        name="yingErMoSheRuPianYi", min=0.0, max=3.0, step=10, default=1, update=CreateMouldHardDrumSmooth)
    bpy.types.Scene.yingErMoSheRuPianYiR = bpy.props.FloatProperty(
        name="yingErMoSheRuPianYi", min=0.0, max=3.0, step=10, default=1, update=CreateMouldHardDrumSmooth)
    bpy.types.Scene.shiFouTongFengGuan = bpy.props.BoolProperty(
        name="shiFouTongFengGuan")
    bpy.types.Scene.tongFengGuanZhiJing = bpy.props.FloatProperty(
        name="tongFengGuanZhiJing", min=-1.0, max=1.0)
    bpy.types.Scene.tongFengGuanHouDu = bpy.props.FloatProperty(
        name="tongFengGuanHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.tongFengGuanWaiBuHouDu = bpy.props.FloatProperty(
        name="tongFengGuanWaiBuHouDu", min=-1.0, max=1.0)

    # 传声孔      管道平滑      传声管道直径         激活   管道形状  偏移
    # 右属性
    bpy.types.Scene.gaunDaoPinHua = bpy.props.BoolProperty(
        name="gaunDaoPinHua", default=True)
    bpy.types.Scene.chuanShenGuanDaoZhiJing = bpy.props.FloatProperty(
        name="chuanShenGuanDaoZhiJing", min=0.2, max=10, step=10,
        default=2, update=soundcanalupdate)
    bpy.types.Scene.active = bpy.props.BoolProperty(name="active")
    bpy.types.Scene.chuanShenKongOffset = bpy.props.FloatProperty(
        name="chuanShenKongOffset", min=-50.0, max=50.0,update = soundcanalHornpipeOffset)
    bpy.types.Scene.soundcancalShapeEnum = bpy.props.EnumProperty(
        name="",
        description='传声孔的形状',
        items=[
            ('OP1', '普通管道', ''),
            ('OP2', '号角管', ''),],
        update = soundcanalShape
    )
    # 左耳属性
    bpy.types.Scene.gaunDaoPinHua_L = bpy.props.BoolProperty(
        name="gaunDaoPinHua_L", default=True)
    bpy.types.Scene.chuanShenGuanDaoZhiJing_L = bpy.props.FloatProperty(
        name="chuanShenGuanDaoZhiJing_L", min=0.2, max=10, step=10,
        default=2, update=soundcanalupdate_L)
    # bpy.types.Scene.active = bpy.props.BoolProperty(name="active")
    bpy.types.Scene.chuanShenKongOffset_L = bpy.props.FloatProperty(
        name="chuanShenKongOffset_L", min=-5.0, max=5.0,update = soundcanalHornpipeOffset)
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
        name="paiQiKongOffset", min=-1.0, max=1.0,update=SprueOffsetUpdate)
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

    bpy.types.Scene.transparent1 = bpy.props.BoolProperty(
        name="transparent1", default=False, update=show_transparent1)
    bpy.types.Scene.transparent2 = bpy.props.BoolProperty(
        name="transparent2", default=False, update=show_transparent2)
    bpy.types.Scene.transparent3 = bpy.props.BoolProperty(
        name="transparent3", default=True, update=show_transparent3)
    bpy.types.Scene.transparent1Enum = bpy.props.EnumProperty(
        name="transparent1Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent1,
        default='OP3'
    )
    bpy.types.Scene.transparentper1Enum = bpy.props.EnumProperty(
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
    bpy.types.Scene.transparent2Enum = bpy.props.EnumProperty(
        name="transparent2Enum",
        description='',
        items=[
            ('OP1', "自动", ""),
            ('OP2', "不透明", ""),
            ('OP3', "透明", ""),
        ],
        update=update_transparent2,
        default='OP3'
    )
    bpy.types.Scene.transparentper2Enum = bpy.props.EnumProperty(
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
    bpy.types.Scene.transparent3Enum = bpy.props.EnumProperty(
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
    bpy.types.Scene.transparentper3Enum = bpy.props.EnumProperty(
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
        name="cutmouldpianyiR", min=0, max=4.0, step=10)
    bpy.types.Scene.cutmouldpianyiL = bpy.props.FloatProperty(
        name="cutmouldpianyiL", min=0, max=4.0, step=10)

    bpy.types.Scene.earname = bpy.props.StringProperty(
        name="earname")


def Houdu(self, context):
    bl_description = "调整蜡厚度的值"
    name = context.scene.leftWindowObj
    active_object = bpy.data.objects[name]
    ori_name = name + 'OriginForShow'
    reset_name = name + 'DamoReset'
    if name == '右耳':
        thickness = context.scene.laHouDUR
    elif name == '左耳':
        thickness = context.scene.laHouDUL

    # 复制一份用于重置的物体
    if not bpy.data.objects.get(reset_name):
        duplicate_obj = active_object.copy()
        duplicate_obj.data = active_object.data.copy()
        duplicate_obj.name = reset_name
        duplicate_obj.animation_data_clear()
        # 将复制的物体加入到场景集合中
        scene = bpy.context.scene
        scene.collection.objects.link(duplicate_obj)
        moveToRight(duplicate_obj)
        duplicate_obj.hide_set(True)

    ori_obj = bpy.data.objects[ori_name]
    reset_obj = bpy.data.objects[reset_name]
    is_back = get_is_back()
    is_dialog = get_is_dialog()
    if active_object.type == 'MESH' and bpy.data.objects.get(reset_name) != None:
        if not get_modal_start() or (get_modal_start() and is_back):
            me = active_object.data
            reset_me = reset_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            ori_me = ori_obj.data
            ori_bm = bmesh.new()
            ori_bm.from_mesh(ori_me)
            ori_bm.verts.ensure_lookup_table()

            for vert in bm.verts:
                vert.co = ori_bm.verts[vert.index].co + ori_bm.verts[vert.index].normal.normalized() * thickness
            bm.to_mesh(me)
            bm.to_mesh(reset_me)
            bm.free()
            ori_bm.free()

        elif get_modal_start() and not is_back and not get_is_dialog():
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



def localLaHouDu(self, context):
    bl_description = "记录局部蜡厚度开启前的数据"
    remember_vertex_change()


# 环切舍入偏移函数
def sheru(self, context):
    bl_description = "环切舍入偏移"
    operator_obj = context.scene.leftWindowObj
    if operator_obj == '右耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiR
    elif operator_obj == '左耳':
        pianyi = bpy.context.scene.qiegesheRuPianYiL
    override = getOverride()
    with bpy.context.temp_override(**override):
        smooth_circlecut(operator_obj, pianyi)



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
            if os.path.isfile(example_l_path) and context.scene.autoMatch and example_l_path != file_path and left_path == "":
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
            if os.path.isfile(example_l_path) and context.scene.autoMatch and example_l_path != file_path and left_path == "":
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
            if os.path.isfile(example_r_path) and context.scene.autoMatch and example_r_path != file_path and right_path == "":
                print("右耳文件匹配成功")
                context.scene.rightEar_path = example_r_path
            elif context.scene.autoMatch and right_path != "":
                print("右耳文件已存在")

    if filename.endswith('L.STL'):
        # 构造ExampleR.stl的路径
        right_filename = another_filename(filename)
        if right_filename:
            example_r_path = os.path.join(directory, right_filename)
            right_path = context.scene.rightEar_path
            # 是否存在
            if os.path.isfile(example_r_path) and context.scene.autoMatch and example_r_path != file_path and right_path == "":
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

    offset = context.scene.localThicking_offset
    borderWidth = context.scene.localThicking_borderWidth
    is_thickening_completed = context.scene.is_thickening_completed  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        if (True):                                    # TODO   当处于加厚未提交时,参数发生变化才会调用加厚函数
            context.scene.is_thickening_completed = True
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth, False)
            context.scene.is_thickening_completed = False
    else:
        pass
# 左耳
def LocalThickeningOffsetUpdate_L(self, context):
    bl_description = "更新选中区域中加厚的厚度_L"

    offset = context.scene.localThicking_offset_L
    borderWidth = context.scene.localThicking_borderWidth_L
    is_thickening_completed = context.scene.is_thickening_completed_L  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        if (True):                                       # TODO   当处于加厚未提交时,参数发生变化才会调用加厚函数
            # 根据更新后的参数重新进行加厚
            context.scene.is_thickening_completed_L = True
            # thickening_offset_borderwidth(0, 0, True)
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth, False)
            context.scene.is_thickening_completed_L = False
    else:
        pass


def LocalThickeningBorderWidthUpdate(self, context):
    bl_description = "更新选中区域中的过渡区域"

    offset = context.scene.localThicking_offset
    borderWidth = context.scene.localThicking_borderWidth
    is_thickening_completed = context.scene.is_thickening_completed  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        if (True):                                     # TODO   当处于加厚未提交时,参数发生变化才会调用加厚函数
            context.scene.is_thickening_completed = True
            # thickening_offset_borderwidth(0, 0, True)
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth, False)
            context.scene.is_thickening_completed = False
    else:
        pass

# 左耳
def LocalThickeningBorderWidthUpdate_L(self, context):
    bl_description = "更新选中区域中的过渡区域左耳"

    offset = context.scene.localThicking_offset_L
    borderWidth = context.scene.localThicking_borderWidth_L
    is_thickening_completed = context.scene.is_thickening_completed_L    # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变
    if (not is_thickening_completed):
        if (True):                                         # TODO   当处于加厚未提交时,参数发生变化才会调用加厚函数
            # 根据更新后的参数重新进行加厚
            context.scene.is_thickening_completed_L = True
            thickening_reset()
            thickening_offset_borderwidth(offset, borderWidth, False)
            context.scene.is_thickening_completed_L = False
    else:
        pass


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
# ('OP3', '一体外壳', '', 'URL', 3),
# ('OP4', '框架式耳膜', '', 'URL', 4),
# ('OP5', '常规外壳', '', 'URL', 5),
# ('OP6', '实心面板', '', 'URL', 6)
def ChangeMouldType(self, context):
    bl_description = "切换模板"
    enum = bpy.context.scene.muJuTypeEnum
    enum_name = bpy.context.scene.muJuNameEnum

    # 同步改变模型名称属性
    if enum == "OP1":
        bpy.context.scene.muJuNameEnum = '软耳模'
    if enum == "OP2":
        bpy.context.scene.muJuNameEnum = '硬耳膜'
    if enum == "OP3":
        bpy.context.scene.muJuNameEnum = '一体外壳'
    if enum == "OP4":
        bpy.context.scene.muJuNameEnum = '框架式耳膜'
    if enum == "OP5":
        bpy.context.scene.muJuNameEnum = '常规外壳'
    if enum == "OP6":
        bpy.context.scene.muJuNameEnum = '实心面板'

    # 重置回最开始
    override = getOverride()
    if override!= None:
        with bpy.context.temp_override(**override):
            recover_flag = recover()
            # 开启切割modal
            set_is_cut_finish(False)

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


def CreateMouldThicknessUpdate(self, context):
    bl_description = "更新创建模具中的总厚度"
    thickness = context.scene.zongHouDu
    enum = bpy.context.scene.muJuTypeEnum

    if enum == "OP1":
        # todo 根据不同的模具执行不同的逻辑
        override = getOverride()
        with bpy.context.temp_override(**override):
            reset_and_refill()
    elif enum == "OP4":
        override = getOverride()
        with bpy.context.temp_override(**override):
            recover_and_refill()


def CreateMouldOuterSmooth(self, context):
    bl_description = "创建模具后,平滑其外边缘"

    enum = bpy.context.scene.muJuTypeEnum

    if enum == "OP1":
        # todo 根据不同的模具执行不同的逻辑
        override = getOverride()
        with bpy.context.temp_override(**override):
            reset_and_refill()
    elif enum == "OP4":
        override = getOverride()
        with bpy.context.temp_override(**override):
            recover_and_refill()

def CreateMouldInnerSmooth(self, context):
    bl_description = "创建模具后,平滑其内边缘"

    enum = bpy.context.scene.muJuTypeEnum

    if enum == "OP1":
        # todo 根据不同的模具执行不同的逻辑
        override = getOverride()
        with bpy.context.temp_override(**override):
            reset_and_refill()
    elif enum == "OP4":
        override = getOverride()
        with bpy.context.temp_override(**override):
            recover_and_refill()


#通过面板参数调整硬耳膜底面平滑度
def CreateMouldHardDrumSmooth(self,context):
    bl_description = "创建模具中的硬耳膜,平滑其底部边缘"

    override = getOverride()
    with bpy.context.temp_override(**override):
        print("参数调整平滑开始:", datetime.datetime.now())
        # smooth_initial()
        name = bpy.context.scene.leftWindowObj
        main_obj = bpy.data.objects.get(name)
        reset_obj = bpy.data.objects.get(name + "HardEarDrumForSmooth")

        bpy.data.objects.remove(main_obj, do_unlink=True)
        reset_obj.name = name
        reset_obj.hide_set(False)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = reset_obj
        reset_obj.select_set(True)
        if bpy.context.scene.leftWindowObj == '右耳':
            pianyi = bpy.context.scene.yingErMoSheRuPianYiR
        else:
            pianyi = bpy.context.scene.yingErMoSheRuPianYiL
        if pianyi > 0.4:
            hard_eardrum_smooth()
        else:
            smooth_initial()

        print("参数调整平滑结束:", datetime.datetime.now())

    # print("参数调整平滑开始:",datetime.datetime.now())
    #
    # name = context.scene.leftWindowObj
    # # obj = bpy.data.objects.get(name)
    # hard_eardrum_smooth = 0
    # if (name == "右耳"):
    #     hard_eardrum_smooth = round(bpy.context.scene.yingErMoSheRuPianYiR, 1) * 2
    # elif (name == "左耳"):
    #     hard_eardrum_smooth = round(bpy.context.scene.yingErMoSheRuPianYiL, 1) * 2
    # override = getOverride()
    # with bpy.context.temp_override(**override):
    #     name = bpy.context.scene.leftWindowObj
    #     smooth_name = name + "HardEarDrumForSmooth"
    #     smooth_obj = bpy.data.objects.get(smooth_name)
    #
    #     # 根据HardEarDrumForSmooth复制出一份物体用于平滑操作
    #     duplicate_obj1 = smooth_obj.copy()
    #     duplicate_obj1.data = smooth_obj.data.copy()
    #     duplicate_obj1.name = smooth_obj.name + "HardEarDrumSmoothing"
    #     duplicate_obj1.animation_data_clear()
    #     bpy.context.scene.collection.objects.link(duplicate_obj1)
    #     if bpy.context.scene.leftWindowObj == '右耳':
    #         moveToRight(duplicate_obj1)
    #     else:
    #         moveToLeft(duplicate_obj1)
    #     bpy.ops.object.select_all(action='DESELECT')
    #     duplicate_obj1.hide_set(False)
    #     duplicate_obj1.select_set(True)
    #     bpy.context.view_layer.objects.active = duplicate_obj1
    #
    #     obj = duplicate_obj1
    #
    #     # 创建平滑修改器,指定硬耳膜平滑顶点组
    #     modifier_name = "HardEarDrumModifier4"
    #     target_modifier = None
    #     for modifier in obj.modifiers:
    #         if modifier.name == modifier_name:
    #             target_modifier = modifier
    #     if (target_modifier == None):
    #         modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier4", type='SMOOTH')
    #         modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex4"
    #         target_modifier = modifierHardEarDrumSmooth
    #     target_modifier.factor = 0.5
    #     target_modifier.iterations = int(hard_eardrum_smooth)
    #     bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier4")
    #
    #     # 创建平滑修改器,指定硬耳膜平滑顶点组
    #     modifier_name = "HardEarDrumModifier3"
    #     target_modifier = None
    #     for modifier in obj.modifiers:
    #         if modifier.name == modifier_name:
    #             target_modifier = modifier
    #     if (target_modifier == None):
    #         modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier3", type='SMOOTH')
    #         modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex3"
    #         target_modifier = modifierHardEarDrumSmooth
    #     target_modifier.factor = 0.5
    #     target_modifier.iterations = int(hard_eardrum_smooth * 3)
    #     bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier3")
    #
    #     # 创建平滑修改器,指定硬耳膜平滑顶点组
    #     modifier_name = "HardEarDrumModifier2"
    #     target_modifier = None
    #     for modifier in obj.modifiers:
    #         if modifier.name == modifier_name:
    #             target_modifier = modifier
    #     if (target_modifier == None):
    #         modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier2", type='SMOOTH')
    #         modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex2"
    #         target_modifier = modifierHardEarDrumSmooth
    #     target_modifier.factor = 0.5
    #     target_modifier.iterations = int(hard_eardrum_smooth * 7)
    #     bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier2")
    #
    #     # 创建平滑修改器,指定硬耳膜平滑顶点组
    #     modifier_name = "HardEarDrumModifier1"
    #     target_modifier = None
    #     for modifier in obj.modifiers:
    #         if modifier.name == modifier_name:  #
    #             target_modifier = modifier
    #     if (target_modifier == None):
    #         modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier1", type='SMOOTH')
    #         modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex1"
    #         target_modifier = modifierHardEarDrumSmooth
    #     target_modifier.factor = 0.5
    #     target_modifier.iterations = int(hard_eardrum_smooth * 10)
    #     bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier1")
    #
    #     if hard_eardrum_smooth != 0:
    #         # 创建矫正平滑修改器,指定硬耳膜平滑顶点组
    #         modifier_name = "HardEarDrumModifier5"
    #         target_modifier = None
    #         for modifier in obj.modifiers:
    #             if modifier.name == modifier_name:
    #                 target_modifier = modifier
    #         if (target_modifier == None):
    #             modifierHardEarDrumSmooth = obj.modifiers.new(name="HardEarDrumModifier5", type='CORRECTIVE_SMOOTH')
    #             modifierHardEarDrumSmooth.smooth_type = 'LENGTH_WEIGHTED'
    #             modifierHardEarDrumSmooth.vertex_group = "HardEarDrumOuterVertex5"
    #             modifierHardEarDrumSmooth.scale = 0
    #             target_modifier = modifierHardEarDrumSmooth
    #         target_modifier.factor = 0.5
    #         target_modifier.iterations = 5
    #         bpy.ops.object.modifier_apply(modifier="HardEarDrumModifier5")
    #         for i in range(7):
    #             laplacian_smooth(getIndex5(), 0.3)
    #         for i in range(5):
    #             laplacian_smooth(getIndex6(), 0.3)
    #         for i in range(2):
    #             laplacian_smooth(getIndex7(), 0.3)
    #
    #     # 平滑成功之后,用平滑后的物体替换左/右耳
    #     bpy.data.objects.remove(bpy.data.objects[bpy.context.scene.leftWindowObj], do_unlink=True)
    #     obj.name = bpy.context.scene.leftWindowObj
    #
    #     print("参数调整平滑结束:", datetime.datetime.now())


def HandleOffsetUpdate(self, context):
    bl_description = "耳膜附件的偏移值,控制耳膜附件与耳膜的距离"

    name = bpy.context.scene.leftWindowObj
    handle_offset = None
    if name == '右耳':
        handle_offset = bpy.context.scene.erMoFuJianOffset
    elif name == '左耳':
        handle_offset = bpy.context.scene.erMoFuJianOffsetL


    #更新耳膜附件到耳膜的距离
    override = getOverride()
    with bpy.context.temp_override(**override):
        name = bpy.context.scene.leftWindowObj
        handle_obj = bpy.data.objects.get(name + "Cube")
        plane_obj = bpy.data.objects.get(name + "Plane")
        handle_compare_obj = bpy.data.objects.get(name + "Cube.001")
        if(handle_obj != None and plane_obj != None and handle_compare_obj !=None):
            if handle_obj.type == 'MESH'and plane_obj.type == 'MESH' and handle_compare_obj.type == 'MESH':
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

                #获取平面法向
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
                #根据面板参数设置偏移值
                for vert in bm.verts:
                    vert.co = ori_handle_bm.verts[vert.index].co + normal.normalized() * handle_offset
                    # vert.co += normal.normalized() * handle_offset

                bm.to_mesh(me)
                bm.free()
                ori_handle_bm.free()


def LabelTextUpdate(self, context):
    bl_description = "更新标签中的文本内容"
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


def LabelSizeUpdate(self, context):
    bl_description = "更新文本中字体的大小"
    name = bpy.context.scene.leftWindowObj
    size = None
    if name == '右耳':
        size = bpy.context.scene.fontSize
    elif name == '左耳':
        size = bpy.context.scene.fontSizeL
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelSizeUpdate(size)


def LabelDepthUpdate(self, context):
    bl_description = "更新文本中字体的高度"
    name = bpy.context.scene.leftWindowObj
    depth = None
    if name == '右耳':
        depth = bpy.context.scene.deep
    elif name == '左耳':
        depth = bpy.context.scene.deepL
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelDepthUpdate(depth)


def LabelEnum(self, context):
    bl_description = "切换Label的类型风格"
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
            if(text_obj != None and text_obj != None):
                bpy.context.view_layer.objects.active = text_obj
                red_material = bpy.data.materials.new(name="Red")
                red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
                text_obj.data.materials.clear()
                text_obj.data.materials.append(red_material)
                bpy.context.view_layer.objects.active = plane_obj
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
                red_material = bpy.data.materials.new(name="Blue")
                red_material.diffuse_color = (0, 0.4, 1, 1.0)
                text_obj.data.materials.clear()
                text_obj.data.materials.append(red_material)
                bpy.context.view_layer.objects.active = plane_obj




def CastingThicknessUpdate(self, context):
    bl_description = "更新铸造法厚度"
    name = bpy.context.scene.leftWindowObj
    thickness = None
    if name == '右耳':
        thickness = bpy.context.scene.ruanErMoHouDu
    elif name == '左耳':
        thickness = bpy.context.scene.ruanErMoHouDuL
    override = getOverride()
    with bpy.context.temp_override(**override):
        castingThicknessUpdate(thickness)

def SupportEnum(self, context):
    bl_description = "切换支撑的类型"
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


def SupportOffsetUpdate(self, context):
    bl_description = "更新支撑沿法线的偏移值"
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
        if(support_enum == "OP1"):
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

def SprueOffsetUpdate(self, context):
    bl_description = "更新排气孔沿法线的偏移值"
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
        sprue_inside_offset_compare_obj = bpy.data.objects.get(name+ "CylinderInsideOffsetCompare")
        plane_obj = bpy.data.objects.get(name + "Plane")
        if (sprue_outer_obj != None  and sprue_inner_obj != None and sprue_inside_obj != None
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


def soundcanalupdate(self, context):
    bl_description = "更新传声孔的直径大小"

    diameter = bpy.context.scene.chuanShenGuanDaoZhiJing
    for obj in bpy.data.objects:
        if obj.name == 'soundcanal':
            obj.data.bevel_depth = diameter / 2
    #更新网格数据
    convert_soundcanal()

# 左耳
def soundcanalupdate_L(self, context):
    bl_description = "更新传声孔的直径大小"

    diameter = bpy.context.scene.chuanShenGuanDaoZhiJing_L
    for obj in bpy.data.objects:
        if obj.name == 'soundcanal':
            obj.data.bevel_depth = diameter / 2
    #更新网格数据
    convert_soundcanal()

def soundcanalShape(self, context):
    bl_description = "普通管道和号角管之间的切换"
    name = bpy.context.scene.leftWindowObj
    soundcanal_enum = None
    if name == '右耳':
        soundcanal_enum = bpy.context.scene.soundcancalShapeEnum
    elif name == '左耳':
        soundcanal_enum = bpy.context.scene.soundcancalShapeEnum_L
    override = getOverride()
    with bpy.context.temp_override(**override):
        hornpipe_name = name + 'Hornpipe'
        hornpipe_obj = bpy.data.objects.get(hornpipe_name)
        hornpipe_plane_name = name + 'HornpipePlane'
        hornpipe_plane_obj = bpy.data.objects.get(hornpipe_plane_name)
        hornpipe_sphere_name = name + 'soundcanalsphere' + '100'
        hornpipe_sphere_obj = bpy.data.objects.get(hornpipe_sphere_name)
        hornpipe_sphere_name1 = name + 'soundcanalsphere' + '101'
        hornpipe_sphere_obj1 = bpy.data.objects.get(hornpipe_sphere_name1)
        last_sphere_name = name + 'soundcanalsphere' + str(2)
        last_sphere_obj = bpy.data.objects.get(last_sphere_name)
        #红球数量大于2,存在传声管道的时候
        if(last_sphere_obj != None):
            if(soundcanal_enum == 'OP1'):
                #将号角管与及其控制点删除
                if(hornpipe_obj != None):
                    bpy.data.objects.remove(hornpipe_obj, do_unlink=True)
                if (hornpipe_plane_obj != None):
                    bpy.data.objects.remove(hornpipe_plane_obj, do_unlink=True)
                if (hornpipe_sphere_obj != None):
                    bpy.data.objects.remove(hornpipe_sphere_obj, do_unlink=True)
                if(hornpipe_sphere_obj1 != None):
                    bpy.data.objects.remove(hornpipe_sphere_obj1, do_unlink=True)
                #将管道末端红球显示出来
                last_sphere_obj.hide_set(False)
                #将管道末端控制点设置为末端红球位置
                object_dic_cur = get_object_dic_index()
                index = int(object_dic_cur[last_sphere_name])
                bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[0:3] = last_sphere_obj.location
                bpy.data.objects[name + 'soundcanal'].data.splines[0].points[index].co[3] = 1
                convert_soundcanal()
            elif(soundcanal_enum == 'OP2'):
                #将可能存在的号角管物体,再初始化导入号角管
                if (hornpipe_obj != None):
                    bpy.data.objects.remove(hornpipe_obj, do_unlink=True)
                if (hornpipe_plane_obj != None):
                    bpy.data.objects.remove(hornpipe_plane_obj, do_unlink=True)
                if (hornpipe_sphere_obj != None):
                    bpy.data.objects.remove(hornpipe_sphere_obj, do_unlink=True)
                if (hornpipe_sphere_obj1 != None):
                    bpy.data.objects.remove(hornpipe_sphere_obj1, do_unlink=True)
                initial_hornpipe()
                #将管道末端控制点隐藏
                last_sphere_obj.hide_set(True)
                #根据offset面板参数更新号角管和管道末端控制点的位置
                update_hornpipe_offset_location_normal()
                convert_soundcanal()

def soundcanalHornpipeOffset(self, context):
    bl_description = "号角管偏移"

    override = getOverride()
    with bpy.context.temp_override(**override):
        #先根据面板的offset参数和管道末端红球位置找到 偏移点,将号角管在偏移点出摆正对齐
        update_hornpipe_offset_location_normal()


def ventcanalupdate(self, context):
    bl_description = "更新通气孔的直径大小"
    name = bpy.context.scene.leftWindowObj
    if name == '右耳':
        diameter = bpy.context.scene.tongQiGuanDaoZhiJing
    else:
        diameter = bpy.context.scene.tongQiGuanDaoZhiJing_L
    for obj in bpy.data.objects:
        if obj.name == 'ventcanal':
            obj.data.bevel_depth = diameter / 2
    #更新网格数据
    convert_ventcanal()


def appendmaterial(type, name, material_name):
    obj = bpy.data.objects.get(name)

    if type == 'OP1':  # 自动，一般为实体
        obj.data.materials.clear()
        obj.data.materials.append(bpy.data.materials.get(material_name))
        changealpha(material_name, 1)
    elif type == 'OP2':  # 不透明
        obj.data.materials.clear()
        obj.data.materials.append(bpy.data.materials.get(material_name))
        changealpha(material_name, 1)
    elif type == "OP3":  # 透明
        percent = 1 - float(bpy.context.scene.transparentper1Enum)
        obj.data.materials.clear()
        obj.data.materials.append(bpy.data.materials.get(material_name))
        changealpha(material_name, percent)


def changealpha(material_name, alpha):
    mat = bpy.data.materials.get(material_name)
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
    if obj and context.scene.transparent1:
        obj.hide_set(False)
        type = context.scene.transparent1Enum
        appendmaterial(type, name, "tran_green")
    elif obj and not context.scene.transparent1:
        obj.hide_set(True)


def update_transparent1(self, context):
    name = context.scene.leftWindowObj + 'OriginForShow'
    obj = bpy.data.objects.get(name)
    if obj and context.scene.transparent1:
        type = context.scene.transparent1Enum
        appendmaterial(type, name, "tran_green")


def update_transparentper1(self, context):
    name = context.scene.leftWindowObj + 'OriginForShow'
    obj = bpy.data.objects.get(name)
    if obj and context.scene.transparent1:
        percent = 1 - float(context.scene.transparentper1Enum)
        changealpha("tran_green", percent)


# 完成打磨后的模型
def show_transparent2(self, context):
    name = context.scene.leftWindowObj + 'WaxForShow'
    obj = bpy.data.objects.get(name)
    if obj and context.scene.transparent2:
        obj.hide_set(False)
        type = context.scene.transparent2Enum
        appendmaterial(type, name, "tran_blue")
    elif obj and not context.scene.transparent2:
        obj.hide_set(True)


def update_transparent2(self, context):
    name = context.scene.leftWindowObj + 'WaxForShow'
    obj = bpy.data.objects.get(name)
    if obj and context.scene.transparent2:
        type = context.scene.transparent2Enum
        appendmaterial(type, name, "tran_blue")


def update_transparentper2(self, context):
    name = context.scene.leftWindowObj + 'WaxForShow'
    obj = bpy.data.objects.get(name)
    if obj and context.scene.transparent2:
        percent = 1 - float(context.scene.transparentper2Enum)
        changealpha("tran_blue", percent)


# 正在操作的模型
def show_transparent3(self, context):
    name = context.scene.leftWindowObj
    obj = bpy.data.objects.get(name)
    if obj and context.scene.transparent3:
        obj.hide_set(False)
        type = context.scene.transparent3Enum
        appendmaterial(type, name, "Yellow")
    elif obj and not context.scene.transparent3:
        obj.hide_set(True)


def update_transparent3(self, context):
    '''
        物体处于Auto状态下,是否透明取决于当前所处的模块以及对当前模块所作的操作
    '''
    current_tab = bpy.context.screen.areas[1].spaces.active.context
    name = context.scene.leftWindowObj
    cur_name = None
    material_name = None
    # 局部加厚模式下透明模式物体为作为对比的LocalThickCompare
    if (current_tab == 'OUTPUT'):
        cur_name = name + "LocalThickCompare"
        material_name = "Yellow"
    # # 铸造法模式下透明模式物体为内部的红色物体CastingCompare
    # elif(current_tab == "PARTICLES"):
    #     cur_name = name + "CastingCompare"
    #     material_name = "CastingRed"
    else:
        cur_name = name
        material_name = "Yellow"
    obj = bpy.data.objects.get(cur_name)
    if obj and context.scene.transparent3:
        type = context.scene.transparent3Enum
        appendmaterial(type, cur_name, material_name)


def update_transparentper3(self, context):
    current_tab = bpy.context.screen.areas[1].spaces.active.context
    name = context.scene.leftWindowObj
    cur_name = None
    material_name = None
    # 局部加厚模式下透明模式物体为作为对比的LocalThickCompare
    if (current_tab == 'OUTPUT'):
        cur_name = name + "LocalThickCompare"
        material_name = "Yellow"
    # 铸造法模式下透明模式物体为内部的红色物体CastingCompare
    # elif (current_tab == "PARTICLES"):
    #     cur_name = name + "CastingCompare"
    #     material_name = "CastingRed"
    else:
        cur_name = name
        material_name = "Yellow"
    obj = bpy.data.objects.get(cur_name)
    if obj and context.scene.transparent3:
        percent = 1 - float(context.scene.transparentper3Enum)
        changealpha(material_name, percent)


def register():
    My_Properties()
